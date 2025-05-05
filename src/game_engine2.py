"""
Definiert die GameEngine-Klasse, die für einen einzelnen Tisch und für die asynchrone Interaktion mit
den Spielern an diesen Tisch zuständig ist.
"""

import asyncio
import random
from aiohttp import WSCloseCode
from src.common.logger import logger
from src.players.agent import Agent
from src.players.client import Client
from src.players.player import Player
from src.private_state2 import PrivateState
from src.public_state2 import PublicState
from typing import List, Dict, Optional, Tuple, Any, Coroutine

from src.lib.cards import Card, CardLabel, deck, stringify_cards, parse_cards
from src.lib.combinations import CombinationType, Combination, build_combinations
#from src.lib.rules import can_player_announce_tichu, can_player_bomb  # Beispiel für Regelfunktionen
#from src.lib.scoring import calculate_round_scores


class GameEngine:
    """
    Steuert den Spielablauf und verwaltet den Spielzustand eines Tichu-Tisches.

    Es wird asynchron auf eine Aktion der Spieler gewartet.
    Die Clients (Menschen) werden über eine Websocket-Verbindung asynchron über Ereignisse informiert.
    Die Agenten (KI-gesteuert) werden direkt aufgerufen, wenn diese am Zug sind.
    """

    # Konstanten
    MAX_PLAYERS = 4  #: Die maximale Anzahl von Spielern an einem Tichu-Tisch.
    DEFAULT_REQUEST_TIMEOUT = 30.0  # Sekunden Timeout für Client-Antworten

    def __init__(self, table_name: str):
        """
        Initialisiert eine neue GameEngine für einen gegebenen Tischnamen.

        :param table_name: Der Name des Tisches, eindeutiger Identifikator.
        :type table_name: str
        """
        # Der Name dieses Spieltisches.
        self.table_name: str = table_name

        # Liste der Spieler an den vier Positionen (0-3). Kann Player-Objekte oder None enthalten
        self.players: List[Optional[Player]] = [None] * self.MAX_PLAYERS

        # Dictionary zur Nachverfolgung verbundener Clients über ihre eindeutige player_id.
        # Wird für Reconnects und zum Nachschlagen von Client-Objekten verwendet.
        self._clients: Dict[str, Client] = {}

        # Der öffentliche Spielzustand, sichtbar für alle Spieler am Tisch.
        self.public_state: PublicState = PublicState(table_name=table_name)

        # Liste der privaten Spielzustände, einer für jede Spielerposition (Index 0-3).
        self.private_states: List[PrivateState] = [PrivateState(player_index=i) for i in range(self.MAX_PLAYERS)]

        # Optionaler Task für die Haupt-Spielschleife (`_run_game_loop`).
        # TODO (Frage): Wofür? Antwort: Hält die Referenz auf den asyncio Task,
        #  der den eigentlichen Spielablauf (Karten geben, Runden spielen etc.)
        #  steuert. Wird benötigt, um den Task z.B. bei `cleanup` sauber beenden zu können.
        self.game_loop_task: Optional[asyncio.Task] = None

        # Optional: Tisch direkt mit KIs füllen. Kann zum Testen nützlich sein.
        # for i in range(self.MAX_PLAYERS):
        #     agent = Agent(player_name=f"KI_{i+1}") # Beispielnamen
        #     agent.player_index = i
        #     self.players[i] = agent
        #     logger.debug(f"DEBUG: Initialen Agent {agent.player_name} an Slot {i} für Tisch '{table_name}' hinzugefügt.")

        logger.info(f"GameEngine für Tisch '{table_name}' erstellt.")

    def _get_player_names(self) -> List[Optional[str]]:
        """Hilfsmethode, um die Namen der Spieler an den Slots zu erhalten."""
        return [p.player_name if p else None for p in self.players]

    def check_reconnect_or_find_slot(self, player_id: Optional[str], player_name: str) -> Tuple[Optional[int], Optional[Client], Optional[str]]:
        """
        Prüft, ob eine `player_id` zu einem bekannten, getrennten Client gehört (Reconnect),
        oder findet einen verfügbaren Slot (leer oder von einer KI besetzt).

        Der Timer-Abbruch für einen Reconnect muss von der `GameFactory` durchgeführt werden,
        da die Timer dort verwaltet werden. Diese Methode informiert die Factory *nicht*.

        :param player_id: Die vom Client übermittelte ID (kann None sein bei neuer Verbindung).
        :type player_id: Optional[str]
        :param player_name: Der vom Client übermittelte oder generierte Name.
        :type player_name: str
        :return: Ein Tupel:
                 (Slot-Index | None, existierendes Client-Objekt bei Reconnect | None, Fehlermeldung | None).
                 Slot-Index ist None bei Fehler oder vollem Tisch.
                 Client-Objekt ist nur bei Reconnect gesetzt.
                 Fehlermeldung ist nur bei Ablehnung gesetzt.
        :rtype: Tuple[Optional[int], Optional[Client], Optional[str]]
        """
        # 1. Reconnect-Versuch prüfen: Existiert die ID und ist der zugehörige Client getrennt?
        if player_id and player_id in self._clients:
            existing_client = self._clients[player_id]
            if not existing_client.is_connected:
                # Gefunden! Erfolgreicher Reconnect-Versuch identifiziert.
                logger.info(f"Tisch '{self.table_name}': Reconnect Versuch für Spieler {existing_client.player_name} ({player_id}) an Index {existing_client.player_index} erkannt.")
                # Timer-Abbruch erfolgt in der Factory!
                return existing_client.player_index, existing_client, None
            elif existing_client.is_connected:
                # Spieler mit dieser ID ist bereits aktiv verbunden.
                logger.warning(f"Tisch '{self.table_name}': Spieler '{player_name}' ({player_id}) ist bereits verbunden.")
                return None, None, f"Spieler '{player_name}' ({player_id}) ist bereits mit diesem Tisch verbunden."

        # 2. Prüfen, ob ID (falls vorhanden) von einem *anderen* verbundenen Client genutzt wird (sollte selten sein).
        if player_id and player_id in self._clients:
            # Dieser Fall tritt ein, wenn die ID von einem *anderen*, aktuell verbundenen Client stammt.
            logger.error(f"Tisch '{self.table_name}': Spieler ID {player_id} (Name: {player_name}) wird bereits von einem anderen verbundenen Client verwendet.")
            return None, None, f"Spieler ID {player_id} wird bereits an diesem Tisch verwendet."

        # 3. Freien Slot suchen: Bevorzugt leere Slots, dann Slots mit KIs.
        available_slot = -1
        agent_slot = -1
        for i, p in enumerate(self.players):
            if p is None:
                available_slot = i
                break  # Leeren Slot gefunden, bevorzuge diesen.
            if isinstance(p, Agent):
                if agent_slot == -1: # Merke den ersten gefundenen KI-Slot.
                    agent_slot = i

        # Wenn kein leerer Slot gefunden wurde, nimm den KI-Slot (falls vorhanden).
        if available_slot == -1:
            available_slot = agent_slot

        if available_slot != -1:
            # Freien Slot (leer oder KI) gefunden.
            logger.info(f"Tisch '{self.table_name}': Freien Slot {available_slot} für neuen Spieler {player_name} (ID: {player_id or 'neu'}) gefunden.")
            return available_slot, None, None # Kein Reconnect, aber Slot gefunden.
        else:
            # Kein freier Slot verfügbar (alle Plätze von verbundenen Clients belegt).
            logger.warning(f"Tisch '{self.table_name}' ist voll für Spieler {player_name}.")
            return None, None, f"Tisch '{self.table_name}' ist voll (nur menschliche Spieler)."

    async def confirm_player_join(self, client: Client, slot_index: int):
        """
        Bestätigt den Beitritt (oder Reconnect) eines Clients an einem bestimmten Slot.

        Diese Methode wird von der `GameFactory` aufgerufen, nachdem `check_reconnect_or_find_slot`
        einen gültigen Slot zurückgegeben hat. Sie platziert den Client, aktualisiert
        interne Strukturen und sendet die notwendigen Zustandsinformationen.

        :param client: Das Client-Objekt des beitretenden Spielers.
        :type client: Client
        :param slot_index: Der zugewiesene Index (0-3) am Tisch.
        :type slot_index: int
        """
        if not (0 <= slot_index < self.MAX_PLAYERS):
            logger.error(f"Tisch '{self.table_name}': Ungültiger Slot-Index {slot_index} beim Bestätigen für Spieler {client.player_name}.")
            # Versuche, den Client zu informieren und die Verbindung zu schließen.
            try:
                await client.close_connection(code=WSCloseCode.INTERNAL_ERROR, message='Interner Serverfehler bei Slot-Zuweisung'.encode('utf-8'))
            except Exception as e:
                logger.exception(f"Fehler bei close_connection für '{self.table_name}': {e}.")
            return

        logger.info(f"Tisch '{self.table_name}': Bestätige Spieler {client.player_name} ({client.player_id}) an Slot {slot_index}.")

        # Prüfen, ob der Slot aktuell von jemand anderem besetzt ist.
        existing_player = self.players[slot_index]
        if existing_player and existing_player.player_id != client.player_id:
            logger.warning(f"Tisch '{self.table_name}': Slot {slot_index} aktuell belegt durch {existing_player.player_name}. Ersetze.")
            if isinstance(existing_player, Client):
                # Wenn ein anderer Client dort saß, entferne ihn aus dem Tracking und schließe seine Verbindung.
                # Dies sollte selten sein, falls check_reconnect korrekt funktioniert.
                if existing_player.player_id in self._clients:
                    del self._clients[existing_player.player_id]
                try:
                    await existing_player.close_connection(message='Dein Platz wurde von einer neuen Verbindung übernommen'.encode('utf-8'))
                except Exception as e:
                    logger.exception(f"Fehler bei close_connection für '{self.table_name}': {e}.")
            # Eine KI an diesem Platz wird einfach überschrieben.

        # Client am Slot platzieren und im Client-Tracking vermerken/aktualisieren.
        self.players[slot_index] = client
        self._clients[client.player_id] = client
        # Index im Client-Objekt setzen, damit der Client weiß, wo er sitzt.
        client.player_index = slot_index

        # Sende initialen/aktualisierten Zustand an die Spieler.
        await self._send_private_state(client)  # Sende Handkarten etc. an den (wieder-)verbundenen Client.
        await self._broadcast_public_state()   # Informiere alle über die neue Spielerliste.

        # Prüfe, ob das Spiel jetzt starten kann (wenn alle Plätze belegt sind).
        await self._check_start_game()

    async def _broadcast_public_state(self):
        """
        Aktualisiert den öffentlichen Spielzustand und sendet ihn an alle verbundenen Clients.
        """
        # Sicherstellen, dass die Spielerliste im State aktuell ist.
        self.public_state.player_names = self._get_player_names()
        # TODO: Weitere Felder im public_state aktualisieren, z.B.:
        # - Aktuelle Punktzahlen
        # - Wer ist am Zug? (current_turn_index)
        # - Zuletzt gespielte Kombination
        # - Angekündigte Tichu/Grand Tichu
        # - Spielstatus (läuft, beendet)

        state_dict = self.public_state.to_dict()
        # Füge optional den Verbindungsstatus hinzu (nützlich für UI)
        state_dict['player_connected_status'] = [
            isinstance(p, Client) and p.is_connected for p in self.players
        ]

        logger.debug(f"Tisch '{self.table_name}': Sende Public State Update: {state_dict}")
        tasks = []
        # Sende den Zustand parallel an alle verbundenen Clients.
        for player in self.players:
            if isinstance(player, Client) and player.is_connected:
                tasks.append(asyncio.create_task(player.notify("public_state_update", state_dict)))
        if tasks:
            # Warte auf das Senden, fange aber Fehler ab (falls Verbindung genau jetzt abbricht).
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Tisch '{self.table_name}': Fehler beim Senden des Public State an einen Client: {result}")

    async def _send_private_state(self, player: Player):
        """
        Aktualisiert und sendet den privaten Spielzustand an einen spezifischen Client.

        :param player: Der Spieler (muss ein verbundener Client sein), der den Zustand erhalten soll.
        :type player: Player
        """
        # Nur an verbundene Clients senden, die einen gültigen Index haben.
        if not isinstance(player, Client) or not player.is_connected or player.player_index is None:
            return

        player_index = player.player_index
        private_state = self.private_states[player_index]

        # TODO: Private State Felder hier aktualisieren, bevor gesendet wird.
        # Dies ist der Ort, um z.B. die Handkarten nach dem Ziehen oder Spielen zu aktualisieren.
        # Beispiel: private_state.hand_cards = self._get_current_hand(player_index)
        # Beispiel: private_state.can_announce_tichu = self._can_announce_tichu(player_index)

        state_dict = private_state.to_dict()
        logger.debug(f"Tisch '{self.table_name}': Sende Private State Update an {player.player_name}: {state_dict}")
        try:
            await player.notify("private_state_update", state_dict)
        except Exception as e:
            logger.warning(f"Tisch '{self.table_name}': Fehler beim Senden des Private State an {player.player_name}: {e}")

    async def handle_player_message(self, client: Client, message: dict):
        """
        Verarbeitet eine eingehende Nachricht (Spielaktion) von einem verbundenen Client.

        Validiert die Aktion basierend auf dem aktuellen Spielzustand (z.B. wer ist am Zug)
        und den Spielregeln. Aktualisiert den Zustand und benachrichtigt Spieler.

        :param client: Der Client, der die Nachricht gesendet hat.
        :type client: Client
        :param message: Die als Dictionary geparste JSON-Nachricht vom Client.
                        Erwartet typischerweise `{'action': '...', 'payload': {...}}`.
        :type message: dict
        """
        # Ignoriere Nachrichten von Clients, die nicht (mehr) verbunden sind oder keinen Index haben.
        if not client.is_connected or client.player_index is None:
            logger.warning(f"Tisch '{self.table_name}': Ignoriere Nachricht von nicht verbundenem/zugewiesenem Client {client.player_name}")
            return

        if not isinstance(message, dict):
            logger.error(f"Tisch '{self.table_name}': Ungültiger Nachrichtentyp von {client.player_name} empfangen. Erwartet: dict, Bekommen: {type(message)}. Nachricht: {message}")
            try:
                # Informiere den Client über das ungültige Format.
                await client.notify("error", {"message": "Ungültiges Nachrichtenformat (kein Objekt)."})
            except Exception as e:
                logger.warning(f"Tisch '{self.table_name}': Fehler beim Senden an {client.player_name}: {e}")
            return  # Verarbeitung für diese ungültige Nachricht abbrechen

        action_type = message.get("action")
        payload = message.get("payload", {})
        player_index = client.player_index # Typ-Checker weiß jetzt, dass player_index nicht None ist.

        logger.info(f"Tisch '{self.table_name}': Empfangen Aktion '{action_type}' von {client.player_name} (Index: {player_index}), Payload: {payload}")

        # --- TODO: Kern-Spiellogik hier implementieren ---
        # 1. Ist der Spieler überhaupt am Zug?
        #    if self.public_state.current_turn_index != player_index:
        #        await client.notify("error", {"message": "Du bist nicht am Zug."})
        #        return

        # 2. Aktion validieren und ausführen
        if action_type == "announce_tichu":
            # Kann Tichu jetzt angesagt werden? (Vor dem Spielen der ersten Karte)
            # Ist der Typ ('small' oder 'grand') gültig?
            # ... Logik ...
            logger.info(f"{client.player_name} sagt Tichu an (Typ: {payload.get('type')})")
            # Zustand aktualisieren (z.B. im PublicState vermerken)
            await self._broadcast_public_state()

        elif action_type == "play_cards":
            cards = payload.get("cards")
            if not cards:
                 await client.notify("error", {"message": "Keine Karten zum Spielen ausgewählt."})
                 return
            # Hat der Spieler diese Karten?
            # Ist die Kombination gültig (Straße, Paar, etc.)?
            # Ist die Kombination höher als die letzte gespielte Kombination?
            # ... Logik zur Validierung und Ausführung ...
            logger.info(f"{client.player_name} spielt Karten: {cards} (VALIDIERUNG AUSSTEHEND!)")
            # Zustand aktualisieren: Karten aus Hand entfernen, letzte Kombi setzen, nächsten Spieler bestimmen.
            # Beispiel (vereinfacht):
            # self.private_states[player_index].hand_cards = [c for c in self.private_states[player_index].hand_cards if c not in cards]
            # self.public_state.last_played_combination = cards # Detaillierter speichern!
            # self.public_state.current_turn_index = self._get_next_player_index(player_index)
            await self._send_private_state(client) # Eigene (aktualisierte) Hand senden
            await self._broadcast_public_state() # Alle informieren

        elif action_type == "pass_turn":
            # Darf der Spieler passen? (Nicht, wenn er den Stich eröffnet)
            # ... Logik zur Validierung und Ausführung ...
            logger.info(f"{client.player_name} passt (VALIDIERUNG AUSSTEHEND!).")
            # Zustand aktualisieren: Nächsten Spieler bestimmen.
            # self.public_state.current_turn_index = self._get_next_player_index(player_index)
            await self._broadcast_public_state()

        # TODO: Weitere Aktionen implementieren (Schupfen bestätigen, Wunsch äußern, Drachen abgeben)

        elif action_type == "ping":
            # Ping empfangen.
            logger.info(f"{client.player_name}: ping")
            await client.notify("pong", {"message": f"{payload}"})

        else:
            # Unbekannte Aktion empfangen.
            logger.warning(f"Tisch '{self.table_name}': Unbekannte Aktion '{action_type}' von {client.player_name}")
            await client.notify("error", {"message": f"Unbekannte Aktion: {action_type}"})

        # --- TODO: Nach jeder Aktion prüfen, ob der Stich, die Runde oder das Spiel beendet ist ---
        # if self._is_stich_over():
        #    await self._handle_stich_end()
        # if self._is_round_over():
        #    await self._handle_round_end()
        # if self._is_game_over():
        #    await self._handle_game_end()

    async def replace_player_with_agent(self, player_id: str) -> bool:
        """
        Ersetzt einen Client (identifiziert durch `player_id`) durch eine KI.

        Diese Methode wird von der `GameFactory` aufgerufen, nachdem der
        Disconnect-Timer für den Spieler abgelaufen ist. Sie prüft, ob der
        Spieler immer noch als getrennt gilt und ersetzt ihn dann durch
        eine `Agent`-Instanz.

        :param player_id: Die ID des zu ersetzenden Clients.
        :type player_id: str
        :return: True, wenn die Ersetzung erfolgreich war, andernfalls False.
        :rtype: bool
        """
        if player_id not in self._clients:
            # Der Client ist nicht (mehr) in unserer Verwaltung.
            logger.warning(f"Tisch '{self.table_name}': Ersetzung fehlgeschlagen - Player ID {player_id} nicht in _clients gefunden (vielleicht reconnected oder bereits ersetzt?).")
            return False

        # Hole das Client-Objekt.
        disconnected_client = self._clients[player_id]
        slot_index = disconnected_client.player_index

        # Überprüfe den Zustand: Ist der Slot gültig? Steht der Client dort? Ist er wirklich getrennt?
        if slot_index is not None and 0 <= slot_index < self.MAX_PLAYERS and \
           self.players[slot_index] == disconnected_client and \
           not disconnected_client.is_connected: # Wichtige Prüfung!

            logger.info(f"Tisch '{self.table_name}': Ersetze disconnected Client {disconnected_client.player_name} (ID: {player_id}) an Slot {slot_index} durch Agent (von Factory ausgelöst).")

            # Entferne den Client aus dem aktiven Client-Tracking.
            del self._clients[player_id]

            # Erstelle eine neue Agent-Instanz.
            agent = Agent(player_name=f"{disconnected_client.player_name} (KI)", ai_level=1)
            agent.player_index = slot_index
            # Setze den Agenten an den Platz des Clients.
            self.players[slot_index] = agent

            # --- TODO: WICHTIG - Zustand übertragen! ---
            # Der Agent muss den aktuellen Spielzustand des ersetzten Spielers übernehmen.
            # Das beinhaltet mindestens die Handkarten, aber potenziell auch:
            # - Bereits gewonnene Stiche/Punkte in dieser Runde.
            # - Ob Tichu angesagt wurde.
            # Überlege, wie der Agent diese Informationen erhält (z.B. über `agent.load_state(self.private_states[slot_index])`).
            logger.warning(f"Tisch '{self.table_name}': Zustandsübertragung von {disconnected_client.player_name} an Agent {agent.player_name} ist NICHT implementiert!")

            # Sende den aktualisierten Zustand (zeigt jetzt den Agenten an).
            await self._broadcast_public_state()
            return True  # Erfolg signalisieren.
        else:
            # Die Bedingungen für die Ersetzung sind nicht (mehr) erfüllt.
            reason = "Bedingungen nicht erfüllt"
            if slot_index is None or not (0 <= slot_index < self.MAX_PLAYERS):
                reason = "Ungültiger Slot-Index"
            elif self.players[slot_index] != disconnected_client:
                reason = f"Slot wird von anderem Spieler ({self.players[slot_index]}) belegt"
            elif disconnected_client.is_connected:
                reason = "Spieler hat sich inzwischen wieder verbunden"
            logger.warning(f"Tisch '{self.table_name}': KI-Ersetzung für Player ID {player_id} abgebrochen. Grund: {reason}.")
            return False # Misserfolg signalisieren.

    def is_empty_of_humans(self) -> bool:
        """
        Prüft, ob keine menschlichen Spieler (Clients) mehr am Tisch aktiv sind.

        Ein Tisch gilt als leer, wenn alle Slots entweder leer (`None`) sind
        oder von einer `Agent`-Instanz besetzt sind. Ein `Client`-Objekt,
        auch wenn es `is_connected == False` ist, zählt *nicht* als leer,
        solange es nicht durch einen Agenten ersetzt wurde.

        Diese Methode wird von der `GameFactory` verwendet, um zu entscheiden,
        ob ein Tisch aufgeräumt werden kann.

        :return: True, wenn nur Agents oder leere Slots vorhanden sind, sonst False.
        :rtype: bool
        """
        for player in self.players:
            if isinstance(player, Client):
                # Sobald ein Client-Objekt gefunden wird (egal ob verbunden), ist der Tisch nicht leer.
                return False
        # Wenn die Schleife durchläuft, ohne einen Client zu finden:
        logger.debug(f"Tisch '{self.table_name}' ist leer von menschlichen Clients.")
        return True

    async def _check_start_game(self):
       """
       Prüft, ob alle Spielerplätze belegt sind und startet ggf. die Spiel-Logik.
       """
       # Sind alle 4 Slots belegt (egal ob Client oder Agent)?
       if all(p is not None for p in self.players):
           # Ist der Spiel-Loop noch nicht gestartet oder bereits beendet?
           if self.game_loop_task is None or self.game_loop_task.done():
               logger.info(f"Tisch '{self.table_name}': Alle Spieler bereit. Starte Spiel-Loop.")
               # --- TODO: Die eigentliche Spiel-Loop-Coroutine starten ---
               # self.game_loop_task = asyncio.create_task(self._run_game_loop())
               # Beispiel: Initialen Zustand senden, nachdem alle bereit sind.
               await self._broadcast_public_state()
           else:
               # Spiel läuft bereits.
               logger.debug(f"Tisch '{self.table_name}': Alle Spieler anwesend, aber Spiel-Loop läuft bereits.")
       else:
           # Es fehlen noch Spieler.
           player_count = sum(1 for p in self.players if p is not None)
           logger.info(f"Tisch '{self.table_name}': Warte auf {self.MAX_PLAYERS - player_count} weitere Spieler.")

    async def cleanup(self):
        """
        Bereinigt Ressourcen dieser GameEngine Instanz.

        Wird von der `GameFactory` aufgerufen, bevor die Engine-Instanz
        aus dem Speicher entfernt wird. Bricht laufende Tasks ab und
        schließt verbleibende Client-Verbindungen.
        """
        logger.info(f"Räume GameEngine für Tisch '{self.table_name}' auf...")

        # 1. Breche den Haupt-Spiel-Loop Task ab, falls er läuft.
        if self.game_loop_task and not self.game_loop_task.done():
            logger.debug(f"Tisch '{self.table_name}': Breche Spiel-Loop Task ab.")
            self.game_loop_task.cancel()
            try:
                # Warte kurz darauf, dass der Task auf den Abbruch reagiert.
                await asyncio.wait_for(self.game_loop_task, timeout=1.0)
            except asyncio.CancelledError:
                logger.debug(f"Tisch '{self.table_name}': Spiel-Loop Task bestätigt abgebrochen.")
            except asyncio.TimeoutError:
                logger.warning(f"Tisch '{self.table_name}': Timeout beim Warten auf Abbruch des Spiel-Loop Tasks.")
            except Exception as e:
                 logger.error(f"Tisch '{self.table_name}': Fehler beim Warten auf abgebrochenen Spiel-Loop Task: {e}")
        self.game_loop_task = None # Referenz entfernen

        # --- Timer werden von der Factory verwaltet, hier nichts zu tun ---

        # 2. Schließe aktiv Verbindungen zu allen noch verbundenen Clients.
        logger.debug(f"Tisch '{self.table_name}': Schließe verbleibende Client-Verbindungen.")
        tasks = []
        for player in self.players:
            if isinstance(player, Client) and player.is_connected:
                 logger.debug(f"Schließe Verbindung für Client {player.player_name} auf Tisch '{self.table_name}'.")
                 tasks.append(asyncio.create_task(
                     player.close_connection(code=WSCloseCode.GOING_AWAY, message='Tisch wird geschlossen'.encode('utf-8'))
                 ))
        if tasks:
            # Warte auf das Schließen der Verbindungen.
            await asyncio.gather(*tasks, return_exceptions=True)

        # 3. Interne Datenstrukturen leeren (optional, hilft dem Garbage Collector).
        self.players = [None] * self.MAX_PLAYERS
        self._clients.clear()
        self.private_states.clear() # Liste leeren

        logger.info(f"GameEngine Cleanup für Tisch '{self.table_name}' beendet.")

    # --- Platzhalter für die eigentliche Spiel-Loop Coroutine ---
    # async def _run_game_loop(self):
    #    try:
    #        logger.info(f"[{self.table_name}] Spiel-Loop gestartet.")
    #        # --- Phase 1: Karten austeilen ---
    #        # self._deal_cards()
    #        # await self._broadcast_public_state()
    #        # for p in self.players: await self._send_private_state(p)
    #
    #        # --- Phase 2: Schupfen ---
    #        # Warten auf Schupf-Aktionen von Clients / Ausführen für Agents
    #        # Karten tauschen
    #        # await self._broadcast_public_state() # Zeigt an, dass Schupfen beendet?
    #        # for p in self.players: await self._send_private_state(p) # Neue Hand senden
    #
    #        # --- Phase 3: Tichu / Grand Tichu ansagen ---
    #        # Warten auf Ansagen / Agents fragen
    #
    #        # --- Phase 4: Runden spielen (Stiche) ---
    #        while not self.public_state.is_round_over: # Annahme: State hat so ein Flag
    #             current_player_index = self.public_state.current_turn_index
    #             current_player = self.players[current_player_index]
    #
    #             if isinstance(current_player, Client):
    #                 # Auf Aktion von Client warten (über handle_player_message)
    #                 # Hier ist eine Synchronisation nötig, z.B. mit asyncio.Event pro Spieler/Zug
    #                 # turn_event = asyncio.Event()
    #                 # self._player_turn_events[current_player_index] = turn_event
    #                 # await turn_event.wait() # Warten bis handle_player_message das Event setzt
    #                 pass # Platzhalter
    #             elif isinstance(current_player, Agent):
    #                 # Aktion von Agent holen und verarbeiten
    #                 action = await current_player.get_action(self.public_state, self.private_states[current_player_index])
    #                 # Verarbeite 'action' ähnlich wie in handle_player_message
    #                 pass # Platzhalter
    #             else: # Leerer Slot im laufenden Spiel - sollte nicht passieren
    #                 logger.error(f"[{self.table_name}] Leerer Slot bei Index {current_player_index} während Spielzug.")
    #                 # Nächsten Spieler bestimmen oder Fehler behandeln
    #                 pass # Platzhalter
    #
    #             # --- Runden-/Spielende prüfen ---
    #
    #        # --- Phase 5: Rundenende, Punkte zählen ---
    #        # self._calculate_scores()
    #        # await self._broadcast_public_state() # Punkte mitteilen
    #
    #        # --- TODO: Logik für mehrere Runden / Spielende (z.B. 1000 Punkte) ---
    #
    #    except asyncio.CancelledError:
    #        logger.info(f"[{self.table_name}] Spiel-Loop abgebrochen.")
    #    except Exception as e:
    #        logger.exception(f"[{self.table_name}] Unerwarteter Fehler im Spiel-Loop: {e}")
    #        # TODO: Fehler an Clients melden? Spiel abbrechen?
    #    finally:
    #        logger.info(f"[{self.table_name}] Spiel-Loop beendet.")
    #        # Sicherstellen, dass der State das Ende reflektiert (falls nicht schon geschehen)
    #        # self.public_state.is_game_over = True
    #        # await self._broadcast_public_state()