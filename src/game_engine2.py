"""
Definiert die GameEngine-Klasse, die für einen einzelnen Tisch und für die asynchrone Interaktion mit
den Spielern an diesen Tisch zuständig ist.
"""

import asyncio
from aiohttp import WSCloseCode

from src.common.errors import PlayerTimeoutError, ClientDisconnectedError, PlayerResponseError
#from src.common.errors import PlayerInteractionError, PlayerTimeoutError, PlayerInterruptError, ClientDisconnectedError, PlayerResponseError
from src.common.logger import logger
from src.common.rand import Random
from src.lib.cards import Card, deck
#from src.players import agent
#from src.lib.combinations import CombinationType, Combination, build_combinations, validate_combination, get_combination_details
#from src.lib.rules import can_player_announce_tichu, can_player_bomb # Beispiel
#from src.lib.scoring import calculate_round_scores
from src.players.agent import Agent
from src.players.client import Client
from src.players.player import Player
from src.players.random_agent import RandomAgent
from src.private_state2 import PrivateState
from src.public_state2 import PublicState
from typing import List, Dict, Optional, Tuple


# todo  Aktueller Stand:
# Ansonsten können wir weiter machen, und zwar mit der Factory.
# Wenn der Host (erster Client in der Liste) sagt, das Spiel beginnt, muss start_game aufgerufen werden.
#
# Ziel: Die GameFactory soll die start_game-Methode der GameEngine2 aufrufen, wenn der Host-Client die entsprechende Aktion sendet.
#
# Wo passiert das?
# Der Client (Host) sendet die Nachricht {"action": "start_game", "payload": {}}.
# Der websocket_handler empfängt diese Nachricht.
# Da es eine proaktive Aktion ist (kein response_to), leitet der Handler sie an engine.handle_player_message(client, data) weiter.
# Also müssen wir GameEngine2.handle_player_message anpassen, um auf action == "start_game" zu reagieren.
#
# Wichtige Annahmen/Änderungen:
# Ich gehe davon aus, dass wir einen "Host" haben (Spieler an Index 0), der bestimmte Aktionen durchführen darf.
# Ich füge ein internes Flag _interrupt_in_progress hinzu, um zu verhindern, dass mehrere Interrupts gleichzeitig bearbeitet werden.
# Ich gehe davon aus, dass die relevanten Regelfunktionen (wie can_player_announce_tichu, player_has_bomb) in src.lib.rules existieren oder implementiert werden.
# Ich nehme an, dass Player/Client/Agent eine neue Methode async def bomb(self, pub, priv, action_space) -> tuple: bekommen, ähnlich wie combination.
#
# Anpassung von GameEngine2:
# handle_player_message
# _process_assign_slot(client, payload)
# _handle_interrupt_request(client, interrupt_type)
# self._process_tichu_announcement(client, payload)


# Konstanten
MAX_PLAYERS = 4  #: Die maximale Anzahl von Spielern an einem Tichu-Tisch.
WINNING_SCORE = 1000 # Punktelimit für das Spiel


class GameEngine:
    """
    Steuert den Spielablauf und verwaltet den Spielzustand eines Tichu-Tisches.

    Es wird asynchron auf eine Aktion der Spieler gewartet.
    Die Clients (Menschen) werden über eine Websocket-Verbindung asynchron über Ereignisse informiert.
    Die Agenten (KI-gesteuert) werden direkt aufgerufen, wenn diese am Zug sind.

    :ivar game_loop_task: Der asyncio Task, der die Hauptspielschleife ausführt.
    :ivar interrupt_events: Dictionary für globale Interrupts.
    """

    def __init__(self, table_name: str, default_agents: Optional[List[Agent]] = None, seed: Optional[int] = None):
        """
        Initialisiert eine neue GameEngine für einen gegebenen Tischnamen.

        :param table_name: Der Name des Spieltisches (eindeutiger Identifikator).
        :param default_agents: Optional: Liste mit 4 Agenten als Standard/Fallback.
        :param seed: (Optional) Seed für den internen Zufallsgenerator (für Tests).
        """
        # Der Name dieses Spieltisches.
        name_stripped = table_name.strip() if table_name else ""
        if not name_stripped:
            raise ValueError("Name des Spieltisches darf nicht leer sein.")
        self._table_name: str = name_stripped

        # Default-Agenten initialisieren
        if default_agents:
            if len(default_agents) != MAX_PLAYERS or any(not isinstance(player, Agent) for player in default_agents):
                raise ValueError(f"default_agents muss genau {MAX_PLAYERS} Agenten enthalten.")
            self._default_agents: List[Agent] = list(default_agents)  # Kopie erstellen (immutable machen)
        else:
            self._default_agents: List[Agent] = [RandomAgent(player_name=f"KI {i+1}") for i in range(MAX_PLAYERS)]

        # Sitzplätze der Reihe nach vergeben (0 bis 3)
        for i, default_agent in enumerate(self._default_agents):
            default_agent.player_index = i

        agent_names = ", ".join(default_agent.name for default_agent in self._default_agents)
        logger.debug(f"[{self.table_name}] Agenten initialisiert: {agent_names}.")

        # Aktueller Spielerliste setzen
        self._players: List[Player] = list(self._default_agents)

        # Dictionary zur Nachverfolgung verbundener Clients über ihre eindeutige player_id.
        # Wird für Reconnects und zum Nachschlagen von Client-Objekten verwendet.
        #self._clients: Dict[str, Client] = {}

        # Der öffentliche Spielzustand, sichtbar für alle Spieler am Tisch.
        self._public_state: PublicState = PublicState(
            table_name = self.table_name,
            player_names = [p.player_name for p in self._players],
        )

        # Liste der privaten Spielzustände, einer für jede Spielerposition (Index 0-3).
        self._private_states: List[PrivateState] = [PrivateState(player_index=i) for i in range(MAX_PLAYERS)]

        # Task für die Haupt-Spielschleife (`_run_game_loop`).
        # Hält die Referenz auf den asyncio Task, der den eigentlichen Spielablauf (Karten geben, Runden spielen etc.) steuert.
        self.game_loop_task: Optional[asyncio.Task] = None
        self._player_action_futures: Dict[int, asyncio.Future] = {} # Intern für Client-Warten

        # Interrupt-Events (öffentlich zugänglich)
        self.interrupt_events: Dict[str, asyncio.Event] = {
            "tichu_announced": asyncio.Event(),
            "bomb_played": asyncio.Event(),
            "game_abort_request": asyncio.Event(), # Beispiel
        }

        # Zufallsgenerator, geeignet für Multiprocessing
        self._random = Random(seed)

        # Kopie des sortiertem Standarddecks - wird jede Runde neu durchgemischt
        self._mixed_deck = list(deck)

        # Flag für laufenden Interrupt
        self._interrupt_in_progress: bool = False
        self._interrupting_player_index: Optional[int] = None

        logger.info(f"GameEngine für Tisch '{table_name}' erstellt.")

    def _get_player_names(self) -> List[Optional[str]]:
        """Hilfsmethode, um die Namen der Spieler an den Slots zu erhalten."""
        return [p.player_name if p else None for p in self._players]

    def _get_client_by_id(self, player_id: str) -> Optional[Client]:
        """Gibt den Client anhand der ID zurück."""
        for p in self._players:
            if p.player_id == player_id and isinstance(p, Client):
                return p
        return None

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
        # todo das vereinfachen wir noch:
        #  wie in der alten Engine suchen wir hier nach einem freien Platz, mehr sollte hier nicht passieren.
        #  Alles andere (Logging usw) sollte die Factory machen.

        # 1. Reconnect-Versuch prüfen: Existiert die ID und ist der zugehörige Client getrennt?
        existing_client = self._get_client_by_id(player_id)
        if existing_client:
            if not existing_client.is_connected:
                # Gefunden! Erfolgreicher Reconnect-Versuch identifiziert.
                logger.info(f"Tisch '{self._table_name}': Reconnect Versuch für Spieler {existing_client.player_name} ({player_id}) an Index {existing_client.player_index} erkannt.")
                # Timer-Abbruch erfolgt in der Factory!
                return existing_client.player_index, existing_client, None
            elif existing_client.is_connected:
                # Spieler mit dieser ID ist bereits aktiv verbunden.
                logger.warning(f"Tisch '{self._table_name}': Spieler '{player_name}' ({player_id}) ist bereits verbunden.")
                return None, None, f"Spieler '{player_name}' ({player_id}) ist bereits mit diesem Tisch verbunden."

        # # 2. Prüfen, ob ID (falls vorhanden) von einem *anderen* verbundenen Client genutzt wird (sollte selten sein).
        # if player_id and player_id in self._clients:
        #     # Dieser Fall tritt ein, wenn die ID von einem *anderen*, aktuell verbundenen Client stammt.
        #     logger.error(f"Tisch '{self._table_name}': Spieler ID {player_id} (Name: {player_name}) wird bereits von einem anderen verbundenen Client verwendet.")
        #     return None, None, f"Spieler ID {player_id} wird bereits an diesem Tisch verwendet."

        # 3. Freien Slot suchen
        available_slot = -1
        for i, p in enumerate(self._players):
            if not isinstance(p, Client):
                available_slot = i
                break

        if available_slot != -1:
            # Freien Slot (leer oder KI) gefunden.
            logger.info(f"Tisch '{self._table_name}': Freien Slot {available_slot} für neuen Spieler {player_name} (ID: {player_id or 'neu'}) gefunden.")
            return available_slot, None, None  # Kein Reconnect, aber Slot gefunden.
        else:
            # Kein freier Slot verfügbar (alle Plätze von verbundenen Clients belegt).
            logger.warning(f"Tisch '{self._table_name}' ist voll für Spieler {player_name}.")
            return None, None, f"Tisch '{self._table_name}' ist voll (nur menschliche Spieler)."

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
        if not (0 <= slot_index < MAX_PLAYERS):
            logger.error(f"Tisch '{self._table_name}': Ungültiger Slot-Index {slot_index} beim Bestätigen für Spieler {client.player_name}.")
            # Versuche, den Client zu informieren und die Verbindung zu schließen.
            try:
                await client.close_connection(code=WSCloseCode.INTERNAL_ERROR, message='Interner Serverfehler bei Slot-Zuweisung'.encode('utf-8'))
            except Exception as e:
                logger.exception(f"Fehler bei close_connection für '{self._table_name}': {e}.")
            return

        logger.info(f"Tisch '{self._table_name}': Bestätige Spieler {client.player_name} ({client.player_id}) an Slot {slot_index}.")

        # Prüfen, ob der Slot aktuell von jemand anderem besetzt ist.
        existing_player = self._players[slot_index]
        if existing_player and existing_player.player_id != client.player_id:
            logger.warning(f"Tisch '{self._table_name}': Slot {slot_index} aktuell belegt durch {existing_player.player_name}. Ersetze.")
            if isinstance(existing_player, Client):
                # Wenn ein anderer Client dort saß, entferne ihn aus dem Tracking und schließe seine Verbindung.
                # Dies sollte selten sein, falls check_reconnect korrekt funktioniert.
                #existing_client = self._get_client_by_id(existing_player.player_id)
                try:
                    await existing_player.close_connection(message='Dein Platz wurde von einer neuen Verbindung übernommen'.encode('utf-8'))
                except Exception as e:
                    logger.exception(f"Fehler bei close_connection für '{self._table_name}': {e}.")
            # Eine KI an diesem Platz wird einfach überschrieben.

        # Client am Slot platzieren und im Client-Tracking vermerken/aktualisieren.
        self._players[slot_index] = client
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
        #TODO: die Methode macht zwei Dinge Spiels:
        # a) Spielzustand aktualisieren und b) Spielzustand per notify senden
        # wir sollten daher daraus 2 Funktionen machen!
        # a sollte Exception werfen, wenn irgendwas schief geht, da es wichtig ist, dass das klappt
        # b sollte wie notify kein Exception werfen, wenn etwas schiefgeht.

        # Sicherstellen, dass die Spielerliste im State aktuell ist.
        self._public_state.player_names = self._get_player_names()
        # TODO: Weitere Felder im public_state aktualisieren, z.B.:
        # - Aktuelle Punktzahlen
        # - Wer ist am Zug? (current_turn_index)
        # - Zuletzt gespielte Kombination
        # - Angekündigte Tichu/Grand Tichu
        # - Spielstatus (läuft, beendet)

        state_dict = self._public_state.to_dict()
        # Füge optional den Verbindungsstatus hinzu (nützlich für UI)
        state_dict['player_connected_status'] = [
            isinstance(p, Client) and p.is_connected for p in self._players
        ]

        logger.debug(f"Tisch '{self._table_name}': Sende Public State Update: {state_dict}")
        tasks = []
        # Sende den Zustand parallel an alle verbundenen Clients.
        for player in self._players:
            if isinstance(player, Client) and player.is_connected:
                tasks.append(asyncio.create_task(player.notify("public_state_update", state_dict)))
        if tasks:
            # Warte auf das Senden, fange aber Fehler ab (falls Verbindung genau jetzt abbricht).
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Tisch '{self._table_name}': Fehler beim Senden des Public State an einen Client: {result}")

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
        private_state = self._private_states[player_index]

        # TODO: Private State Felder hier aktualisieren, bevor gesendet wird.
        # Dies ist der Ort, um z.B. die Handkarten nach dem Ziehen oder Spielen zu aktualisieren.
        # Beispiel: private_state.hand_cards = self._get_current_hand(player_index)
        # Beispiel: private_state.can_announce_tichu = self._can_announce_tichu(player_index)

        state_dict = private_state.to_dict()
        logger.debug(f"Tisch '{self._table_name}': Sende Private State Update an {player.player_name}: {state_dict}")
        await player.notify("private_state_update", state_dict)

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
            logger.warning(f"Tisch '{self._table_name}': Ignoriere Nachricht von nicht verbundenem/zugewiesenem Client {client.player_name}")
            return

        action = message.get("action")
        payload = message.get("payload", {})
        player_index = client.player_index # Typ-Checker weiß jetzt, dass player_index nicht None ist.

        logger.debug(f"Tisch '{self._table_name}': Empfangen Aktion '{action}' von {client.player_name} (Index: {player_index}), Payload: {payload}")

        # --- Aktionen im Setup/Lobby/Game Over Modus ---
        # Spiel kann nur gestartet werden, wenn es nicht schon läuft
        # oder gerade initialisiert wird.
        if self._public_state.current_phase in ["lobby", "setup", "game_over", "aborted", "error"]:
            if action == "start_game":
                # Host-Prüfung (Beispiel: Spieler 0)
                host_index = 0
                if player_index == host_index:
                    # Prüfen, ob genügend Spieler da sind
                    player_count = sum(1 for p in self._players if p is not None)
                    if player_count == MAX_PLAYERS:
                        # Starte das Spiel (startet run_game_loop als Task)
                        await self.start_game()
                        # Sende Bestätigung oder warte auf erstes State Update?
                        # start_game sendet selbst keine Bestätigung.
                        # Der erste Broadcast aus run_game_loop signalisiert den Start.
                    else:
                        logger.warning(f"Spielstart auf Tisch '{self._table_name}' durch Host fehlgeschlagen: Nur {player_count}/{MAX_PLAYERS} Spieler.")
                        await client.notify("error", {"message": f"Es müssen genau {MAX_PLAYERS} Spieler am Tisch sein, um zu starten."})
                else:
                    logger.warning(f"Spielstart auf Tisch '{self._table_name}' durch Spieler {player_index} (nicht Host) abgelehnt.")
                    await client.notify("error", {"message": "Nur der Host (Spieler 1) kann das Spiel starten."})
                return  # Aktion behandelt

            elif action == "assign_slot":  # Nur im Setup/Lobby erlaubt?
                # TODO: Logik für Slot-Zuweisung durch Host
                await self._process_assign_slot(client, payload)
                return  # Aktion behandelt

            # Andere Aktionen sind in diesen Phasen meist ungültig
            else:
                logger.warning(f"Tisch '{self._table_name}': Ungültige Aktion '{action}' in Phase '{self._public_state.current_phase}' von Spieler {player_index}.")
                await client.notify("error", {"message": f"Aktion '{action}' ist in der aktuellen Phase '{self.public_state.current_phase}' nicht erlaubt."})
                return  # Aktion behandelt (als ungültig)

        # --- Aktionen während des Spiels ('playing', 'announcing_...') ---
        elif self._public_state.current_phase.startswith("playing") or \
                self._public_state.current_phase.startswith("announcing") or \
                self._public_state.current_phase.startswith("schupfing"):  # Ggf. Phasen genauer prüfen

            # Prüfen, ob eine Antwort auf eine Anfrage erwartet wird
            # (Diese Logik ist jetzt im Client, der Handler leitet nur weiter)
            # Wir müssen hier also nur proaktive Aktionen behandeln.

            if action == "announce_tichu":
                logger.info(f"Spieler {player_index} versucht Tichu anzusagen (proaktiv).")
                valid = await self._process_tichu_announcement(client, payload)
                if valid:
                    # Interrupt auslösen & Broadcast im Erfolgsfall
                    self.interrupt_events["tichu_announced"].set()
                    self.interrupt_events["tichu_announced"].clear()
                    await self._broadcast_public_state()
                # else: Fehler wurde in _process_... gesendet
                return  # Aktion behandelt

            elif action == "request_interrupt":  # Beispiel für explizite Interrupt-Anfrage
                interrupt_type = payload.get("type")
                logger.info(f"Spieler {player_index} fordert Interrupt an: '{interrupt_type}'")
                await self._handle_interrupt_request(client, interrupt_type)
                return  # Aktion behandelt

            # --- WICHTIG: Behandlung von normalen Spielzügen ---
            # Normale Spielzüge (play_cards, pass_turn, submit_schupf_cards etc.)
            # werden NICHT mehr hier verarbeitet. Sie kommen als *Antwort*
            # auf eine `request_action` vom Server und werden vom websocket_handler
            # an `client.receive_response()` weitergeleitet, was dann die Future
            # in der wartenden `Client`-Methode (z.B. `combination`) auflöst.
            # Daher sollten diese Actions hier nicht mehr auftauchen, wenn sie
            # nicht proaktiv gesendet wurden (was sie nicht sollten).

            elif action in ["play_cards", "pass_turn", "submit_schupf_cards", "make_wish", "gift_dragon"]:
                logger.warning(f"Tisch '{self._table_name}': Empfing Spielzug-Aktion '{action}' von Spieler {player_index} außerhalb einer Anfrage. Ignoriere.")
                # Optional: Fehler an Client senden
                # await client.notify("error", {"message": "Aktion nur als Antwort auf eine Anfrage möglich."})
                return  # Ignorieren

            elif action == "ping":
                # Ping empfangen.
                logger.info(f"{client.player_name}: ping")
                await client.notify("pong", {"message": f"{payload}"})

            else:
                # Unbekannte Aktion während des Spiels
                logger.warning(f"Tisch '{self._table_name}': Unbekannte proaktive Aktion '{action}' während des Spiels von Spieler {player_index}.")
                await client.notify("error", {"message": f"Unbekannte Aktion: {action}"})
                return  # Aktion behandelt (als unbekannt)
        else:
            # Unerwartete Phase
            logger.error(f"Tisch '{self._table_name}': handle_player_message aufgerufen in unerwarteter Phase '{self._public_state.current_phase}'.")
            await client.notify("error", {"message": "Interner Serverfehler (ungültige Phase)."})

    async def _process_assign_slot(self, requesting_client: Client, payload: dict):
        """
        Verarbeitet eine Slot-Zuweisungsanfrage vom Host-Client.
        Ermöglicht das Zurücksetzen eines Slots auf den Default-Agenten.

        :param requesting_client: Der Client, der die Anfrage stellt.
        :param payload: Die Daten der Anfrage, erwartet z.B.
                        {"slot_index": <int>, "player_type": "default"}.
        """
        host_index = 0  # Beispiel: Spieler 0 ist Host
        if requesting_client.player_index != host_index:
            logger.warning(f"Tisch '{self.table_name}': Spieler {requesting_client.player_index} (nicht Host) versucht Slot zuzuweisen.")
            await requesting_client.notify("error", {"message": "Nur der Host (Spieler 1) kann Slots zuweisen."})
            return

        # Nur im Setup/Lobby/Game Over erlauben?
        if self.public_state.current_phase not in ["lobby", "setup", "game_over", "aborted", "error"]:
            logger.warning(f"Tisch '{self.table_name}': Slot-Zuweisung in Phase '{self.public_state.current_phase}' nicht erlaubt.")
            await requesting_client.notify("error", {"message": f"Slot-Zuweisung in Phase '{self.public_state.current_phase}' nicht erlaubt."})
            return

        try:
            slot_index = int(payload.get("slot_index", -1))
            player_type = payload.get("player_type")  # Erwartet "default"

            if not (0 <= slot_index < MAX_PLAYERS):
                raise ValueError("Ungültiger Slot-Index.")
            if player_type != "default":
                # Andere Typen wie "ai" mit Level oder "human" sind aktuell nicht unterstützt
                # für die *Zuweisung* durch den Host. Menschen joinen selbst.
                raise ValueError("Ungültiger player_type (nur 'default' erlaubt).")

            # Hole den aktuellen Spieler an diesem Slot
            current_player = self._players[slot_index]
            default_agent = self._default_agents[slot_index]  # Hole den ursprünglichen Agenten für diesen Slot

            # Prüfe, ob sich etwas ändert
            if current_player == default_agent:
                logger.info(f"Tisch '{self.table_name}': Slot {slot_index} ist bereits mit Default Agent {default_agent.player_name} besetzt.")
                # Ggf. Bestätigung an Host? Vorerst nicht.
                return

            logger.info(f"Tisch '{self.table_name}': Host setzt Slot {slot_index} auf Default Agent '{default_agent.player_name}'.")

            # Wenn ein Client an dem Slot saß, muss dieser getrennt werden.
            if isinstance(current_player, Client):
                logger.warning(f"Tisch '{self.table_name}': Entferne Client {current_player.player_name} von Slot {slot_index} auf Host-Anweisung.")
                # Client über Kick informieren und Verbindung schließen
                try:
                    await current_player.notify("kicked", {"message": "Der Host hat dich vom Tisch entfernt."})
                    await current_player.close_connection(message="Vom Host entfernt".encode('utf-8'))
                except Exception as e:
                    logger.warning(f"Fehler beim Benachrichtigen/Schließen von Client {current_player.player_name}: {e}")
                # Referenz im (nicht mehr vorhandenen) _clients dict ist nicht nötig

            # Setze den Default Agent (wieder) an den Slot
            default_agent.player_index = slot_index  # Index sicherstellen
            self._players[slot_index] = default_agent

            # Public State aktualisieren
            self._public_state.player_names[slot_index] = default_agent.player_name
            await self._broadcast_public_state()  # Alle informieren

        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"Tisch '{self.table_name}': Ungültige Daten für Slot-Zuweisung empfangen: {payload} -> {e}")
            await requesting_client.notify("error", {"message": f"Ungültige Daten für Slot-Zuweisung: {e}"})
        except Exception as e:
            logger.exception(f"Tisch '{self.table_name}': Unerwarteter Fehler bei Slot-Zuweisung: {e}")
            await requesting_client.notify("error", {"message": "Interner Fehler bei Slot-Zuweisung."})

    async def _handle_interrupt_request(self, client: Client, interrupt_type: Optional[str]):
        """
        Bearbeitet eine Interrupt-Anfrage (Bombe/Tichu) von einem Client.

        :param client: Der anfragende Client.
        :param interrupt_type: Der Typ des gewünschten Interrupts ("bomb" oder "tichu").
        """
        player_index = client.player_index
        if player_index is None: return  # Sollte nicht passieren

        logger.info(f"Tisch '{self.table_name}': Spieler {player_index} fordert Interrupt an: '{interrupt_type}'")

        # --- Prüfungen ---
        if self._interrupt_in_progress:
            logger.warning(f"Tisch '{self.table_name}': Interrupt von Spieler {player_index} ignoriert (anderer Interrupt läuft bereits).")
            await client.notify("error", {"message": "Ein anderer Interrupt wird gerade bearbeitet. Bitte warte."})
            return

        # Nur während der Spielphase erlaubt? (Tichu evtl. auch vorher?)
        if self.public_state.current_phase != "playing":
            # Ausnahme für Tichu erlauben?
            if interrupt_type == "tichu" and self.public_state.current_phase == "announcing_small_tichu":
                pass  # Erlaubt
            else:
                logger.warning(f"Tisch '{self.table_name}': Interrupt '{interrupt_type}' von Spieler {player_index} in Phase '{self.public_state.current_phase}' nicht erlaubt.")
                await client.notify("error", {"message": f"Aktion '{interrupt_type}' in Phase '{self.public_state.current_phase}' nicht erlaubt."})
                return

        # --- Interrupt-spezifische Logik ---
        self._interrupt_in_progress = True  # Sperre setzen
        self._interrupting_player_index = player_index
        #interrupted_player_task_future: Optional[asyncio.Future] = None

        try:
            if interrupt_type == "tichu":
                # Tichu-Ansage direkt validieren und verarbeiten
                success = await self._process_tichu_announcement(client, {})  # Payload hier leer
                if success:
                    # Signalisiere den wartenden Tasks, dass Tichu angesagt wurde
                    self.interrupt_events["tichu_announced"].set()
                    # Sende Update an alle Clients
                    await self._broadcast_public_state()
                # Fehler wurde in _process_tichu_announcement behandelt
                # Tichu unterbricht nicht unbedingt den *Zug*, nur das Warten

            elif interrupt_type == "bomb":
                # --- Bomben-Logik ---
                #priv_state = self.private_states[player_index]
                # 1. Validieren: Hat Spieler eine Bombe? Ist Bomben erlaubt?
                # TODO: Implementiere Regel-Funktion 'player_has_bomb(priv_state.hand_cards)'
                # TODO: Implementiere Regel-Funktion 'can_bomb_now(self.public_state)'
                has_bomb = True  # Platzhalter
                can_bomb = True  # Platzhalter
                if not has_bomb or not can_bomb:
                    logger.warning(f"Tisch '{self.table_name}': Spieler {player_index} kann keine Bombe spielen.")
                    await client.notify("error", {"message": "Du kannst jetzt keine Bombe spielen."})
                    # Sperre muss wieder aufgehoben werden!
                    self._interrupt_in_progress = False
                    self._interrupting_player_index = None
                    return

                # 2. Alten Zug ggf. unterbrechen: Signalisiere anderen wartenden Tasks
                logger.info(f"Tisch '{self.table_name}': Spieler {player_index} initiiert Bomben-Interrupt.")
                self.interrupt_events["bomb_played"].set()  # Signalisiere Interrupt

                # 3. Bomben-Auswahl vom Client anfordern
                try:
                    # TODO: Erstelle action_space nur mit Bomben des Spielers
                    #bomb_action_space = []  # Platzhalter
                    # Fordere Client zur Auswahl auf
                    # Annahme: Client hat Methode 'bomb', die ähnlich wie 'combination' funktioniert
                    bomb_action_tuple = ()  # await client.bomb(self.public_state, priv_state, bomb_action_space)  #todo client.bomb implementieren

                    # TODO: Verarbeite bomb_action_tuple
                    #       - Validiere die gewählte Bombe erneut
                    #       - Rufe _process_stich_action auf (oder eine spezielle _process_bomb_action)
                    #         Diese aktualisiert State, History, Punkte etc.
                    #       - Setze current_turn_index auf den Bomber
                    #       - Lösche den Interrupt-Status des Stichs
                    logger.info(f"Bombe {bomb_action_tuple} von Spieler {player_index} verarbeitet (PLATZHALTER).")
                    await self._broadcast_public_state()  # Sende neuen Zustand

                except (PlayerTimeoutError, ClientDisconnectedError, PlayerResponseError, asyncio.CancelledError) as e:
                    logger.error(f"Tisch '{self.table_name}': Fehler/Timeout bei Bomben-Auswahl von Spieler {player_index}: {e}")
                    # TODO: Was tun? Interrupt abbrechen? Spieler bestrafen?
                    # Vorerst: Interrupt abbrechen, ursprünglicher Spieler ist weiter dran?
                    await client.notify("error", {"message": "Fehler bei Bomben-Auswahl."})
                except Exception as e:
                    logger.exception(f"Unerwarteter Fehler bei Bomben-Auswahl von Spieler {player_index}: {e}")
                    await client.notify("error", {"message": "Interner Fehler bei Bomben-Auswahl."})

                # Interrupt ist beendet, Event zurücksetzen
                self.interrupt_events["bomb_played"].clear()

            else:
                logger.warning(f"Tisch '{self.table_name}': Unbekannter Interrupt-Typ angefordert: '{interrupt_type}'")
                await client.notify("error", {"message": f"Unbekannter Interrupt-Typ: {interrupt_type}"})

        except Exception as e:
            # Fange allgemeine Fehler während der Interrupt-Verarbeitung ab
            logger.exception(f"Tisch '{self.table_name}': Kritischer Fehler bei Interrupt-Verarbeitung ({interrupt_type}) für Spieler {player_index}: {e}")
            # noinspection PyBroadException
            try:
                await client.notify("error", {"message": "Interner Fehler bei Interrupt-Verarbeitung."})
            except Exception:
                pass
        finally:
            # Stelle sicher, dass die Sperre immer aufgehoben wird
            self._interrupt_in_progress = False
            self._interrupting_player_index = None
            logger.debug(f"Interrupt-Verarbeitung für Spieler {player_index} beendet.")

    async def _process_tichu_announcement(self, client: Client, _payload: dict) -> bool:
        """
        Validiert und verarbeitet eine Tichu-Ansage (klein oder groß).
        Wird von handle_player_message oder _handle_interrupt_request aufgerufen.

        :param client: Der Client, der Tichu ansagen möchte.
        :param _payload: Die Daten aus der Client-Nachricht (kann leer sein).
        :return: True bei Erfolg, False bei Fehler (Fehlermeldung wird an Client gesendet).
        """
        player_index = client.player_index
        if player_index is None: return False  # Client nicht korrekt zugewiesen

        priv_state = self.private_states[player_index]
        is_grand_attempt = self.public_state.current_phase == "announcing_grand_tichu"
        #is_small_attempt = self.public_state.current_phase in ["announcing_small_tichu", "playing"]  # Oder genauer?

        logger.info(f"Tisch '{self.table_name}': Verarbeite Tichu-Anfrage von Spieler {player_index} (Grand: {is_grand_attempt}).")

        # --- Validierung ---
        # 1. Bereits angesagt?
        if self.public_state.round_announcements[player_index] > 0:
            logger.warning(f"Spieler {player_index} hat bereits Tichu angesagt.")
            await client.notify("error", {"message": "Du hast bereits Tichu angesagt."})
            return False

        # 2. Richtige Phase?
        # Annahme: can_player_announce_tichu prüft Phase, Kartenanzahl etc.
        # Die Funktion muss wissen, ob es um Grand oder Small geht.
        can_announce = True  # can_player_announce_tichu(self.public_state, priv_state, grand=is_grand_attempt)  # todo can_player_announce_tichu implementieren
        if not can_announce:
            msg = "Grand Tichu kann nur nach den ersten 8 Karten angesagt werden." if is_grand_attempt else "Tichu kann nur vor deinem ersten ausgespielten Zug angesagt werden."
            logger.warning(f"Ungültiger Tichu-Versuch von Spieler {player_index}: {msg}")
            await client.notify("error", {"message": msg})
            return False

        # --- Wenn gültig: Zustand aktualisieren ---
        tichu_type = 2 if is_grand_attempt else 1
        self.public_state.round_announcements[player_index] = tichu_type
        priv_state.can_announce_tichu = False  # Kann nicht erneut ansagen in dieser Runde

        type_str = "Grand Tichu" if is_grand_attempt else "Tichu"
        logger.info(f"Tisch '{self.table_name}': {type_str}-Ansage von Spieler {player_index} akzeptiert.")

        # Sende KEINEN Broadcast hier. Das macht der Aufrufer (handle_player_message),
        # nachdem das Interrupt-Event ggf. gesetzt wurde.
        return True  # Erfolg

    async def replace_player_with_agent(self, player_id: str) -> bool:
        """
        Ersetzt einen Client (identifiziert durch `player_id`) durch eine KI.

        Diese Methode wird von der `GameFactory` aufgerufen, nachdem der Disconnect-Timer für den Spieler abgelaufen ist.
        Sie prüft, ob der Spieler immer noch als getrennt gilt und ersetzt ihn dann durch eine `Agent`-Instanz.

        :param player_id: Die ID des zu ersetzenden Clients.
        :type player_id: str
        :return: True, wenn die Ersetzung erfolgreich war, andernfalls False.
        :rtype: bool
        """
        disconnected_client = self._get_client_by_id(player_id)
        if not disconnected_client:
            # Der Client ist nicht (mehr) in unserer Verwaltung.
            logger.warning(f"Tisch '{self._table_name}': Ersetzung fehlgeschlagen - Player ID {player_id} nicht in _clients gefunden (vielleicht reconnected oder bereits ersetzt?).")
            return False

        slot_index = disconnected_client.player_index

        # Überprüfe den Zustand: Ist der Slot gültig? Steht der Client dort? Ist er wirklich getrennt?
        if slot_index is not None and 0 <= slot_index < MAX_PLAYERS and \
           self._players[slot_index] == disconnected_client and \
           not disconnected_client.is_connected: # Wichtige Prüfung!

            logger.info(f"Tisch '{self._table_name}': Ersetze disconnected Client {disconnected_client.player_name} (ID: {player_id}) an Slot {slot_index} durch Agent (von Factory ausgelöst).")

            # Erstelle eine neue Agent-Instanz.
            # todo Die Klasse des Agents aus der Konfiguration holen oder 2. Idee: den vorherigen Agent nehmen.
            agent = RandomAgent(player_name=f"{disconnected_client.player_name} (KI)")
            agent.player_index = slot_index
            # Setze den Agenten an den Platz des Clients.
            self._players[slot_index] = agent

            # --- TODO: WICHTIG - Zustand übertragen! ---
            # Der Agent muss den aktuellen Spielzustand des ersetzten Spielers übernehmen.
            # Das beinhaltet mindestens die Handkarten, aber potenziell auch:
            # - Bereits gewonnene Stiche/Punkte in dieser Runde.
            # - Ob Tichu angesagt wurde.
            # Überlege, wie der Agent diese Informationen erhält (z.B. über `agent.load_state(self._private_states[slot_index])`).
            logger.warning(f"Tisch '{self._table_name}': Zustandsübertragung von {disconnected_client.player_name} an Agent {agent.player_name} ist NICHT implementiert!")

            # Sende den aktualisierten Zustand (zeigt jetzt den Agenten an).
            await self._broadcast_public_state()
            return True  # Erfolg signalisieren.
        else:
            # Die Bedingungen für die Ersetzung sind nicht (mehr) erfüllt.
            reason = "Bedingungen nicht erfüllt"
            if slot_index is None or not (0 <= slot_index < MAX_PLAYERS):
                reason = "Ungültiger Slot-Index"
            elif self._players[slot_index] != disconnected_client:
                reason = f"Slot wird von anderem Spieler ({self._players[slot_index]}) belegt"
            elif disconnected_client.is_connected:
                reason = "Spieler hat sich inzwischen wieder verbunden"
            logger.warning(f"Tisch '{self._table_name}': KI-Ersetzung für Player ID {player_id} abgebrochen. Grund: {reason}.")
            return False # Misserfolg signalisieren.

    def is_empty_of_humans(self) -> bool:
        """
        Prüft, ob keine menschlichen Spieler (Clients) mehr am Tisch aktiv sind.

        Ein Tisch gilt als leer, wenn alle Slots entweder leer (`None`) sind oder von einer `Agent`-Instanz besetzt sind.
        Ein `Client`-Objekt, auch wenn es `is_connected == False` ist, zählt *nicht* als leer, solange es nicht durch
        einen Agenten ersetzt wurde.

        Diese Methode wird von der `GameFactory` verwendet, um zu entscheiden, ob ein Tisch aufgeräumt werden kann.

        :return: True, wenn nur Agents oder leere Slots vorhanden sind, sonst False.
        :rtype: bool
        """
        for player in self._players:
            if isinstance(player, Client):
                # Sobald ein Client-Objekt gefunden wird (egal ob verbunden), ist der Tisch nicht leer.
                return False
        # Wenn die Schleife durchläuft, ohne einen Client zu finden:
        logger.debug(f"Tisch '{self._table_name}' ist leer von menschlichen Clients.")
        return True

    async def _check_start_game(self):
       """
       Prüft, ob alle Spielerplätze belegt sind und startet ggf. die Spiel-Logik.
       """
       # Sind alle 4 Slots belegt (egal ob Client oder Agent)?
       if all(p is not None for p in self._players):
           # Ist der Spiel-Loop noch nicht gestartet oder bereits beendet?
           if self.game_loop_task is None or self.game_loop_task.done():
               logger.info(f"Tisch '{self._table_name}': Alle Spieler bereit. Starte Spiel-Loop.")
               # --- TODO: Die eigentliche Spiel-Loop-Coroutine starten ---
               # self.game_loop_task = asyncio.create_task(self._run_game_loop())
               # Beispiel: Initialen Zustand senden, nachdem alle bereit sind.
               await self._broadcast_public_state()
           else:
               # Spiel läuft bereits.
               logger.debug(f"Tisch '{self._table_name}': Alle Spieler anwesend, aber Spiel-Loop läuft bereits.")
       else:  # todo darf nicht mehr vorkommen,initial werden 4 Agenten gesetzt
           # Es fehlen noch Spieler.
           player_count = sum(1 for p in self._players if p is not None)
           logger.info(f"Tisch '{self._table_name}': Warte auf {MAX_PLAYERS - player_count} weitere Spieler.")

    async def cleanup(self):
        """
        Bereinigt Ressourcen dieser GameEngine Instanz.

        Wird von der `GameFactory` aufgerufen, bevor die Engine-Instanz aus dem Speicher entfernt wird.
        Bricht laufende Tasks ab und schließt verbleibende Client-Verbindungen.
        """
        logger.info(f"Räume GameEngine für Tisch '{self._table_name}' auf...")

        # 1. Breche den Haupt-Spiel-Loop Task ab, falls er läuft.
        if self.game_loop_task and not self.game_loop_task.done():
            logger.debug(f"Tisch '{self._table_name}': Breche Spiel-Loop Task ab.")
            self.game_loop_task.cancel()
            try:
                # Warte kurz darauf, dass der Task auf den Abbruch reagiert.
                await asyncio.wait_for(self.game_loop_task, timeout=1.0)
            except asyncio.CancelledError:
                logger.debug(f"Tisch '{self._table_name}': Spiel-Loop Task bestätigt abgebrochen.")
            except asyncio.TimeoutError:
                logger.warning(f"Tisch '{self._table_name}': Timeout beim Warten auf Abbruch des Spiel-Loop Tasks.")
            except Exception as e:
                 logger.error(f"Tisch '{self._table_name}': Fehler beim Warten auf abgebrochenen Spiel-Loop Task: {e}")
        self.game_loop_task = None # Referenz entfernen

        # --- Timer werden von der Factory verwaltet, hier nichts zu tun ---

        # 2. Schließe aktiv Verbindungen zu allen noch verbundenen Clients.
        logger.debug(f"Tisch '{self._table_name}': Schließe verbleibende Client-Verbindungen.")
        tasks = []
        for player in self._players:
            if isinstance(player, Client) and player.is_connected:
                 logger.debug(f"Schließe Verbindung für Client {player.player_name} auf Tisch '{self._table_name}'.")
                 tasks.append(asyncio.create_task(
                     player.close_connection(code=WSCloseCode.GOING_AWAY, message='Tisch wird geschlossen'.encode('utf-8'))
                 ))
        if tasks:
            # Warte auf das Schließen der Verbindungen.
            await asyncio.gather(*tasks, return_exceptions=True)

        # 3. Interne Datenstrukturen leeren (optional, hilft dem Garbage Collector).
        self._players = [None] * MAX_PLAYERS
        self._private_states.clear() # Liste leeren

        logger.info(f"GameEngine Cleanup für Tisch '{self._table_name}' beendet.")

    def _shuffle_deck(self):
        """
        Mischt das Kartendeck.
        """
        self._random.shuffle(self._mixed_deck)

    # --------------------------------------------------------------------------
    # Spielstart
    # --------------------------------------------------------------------------

    async def start_game(self):
        """
        Startet eine neue Partie als Hintergrund-Task
        """
        if self.game_loop_task and not self.game_loop_task.done():
            logger.warning(f"Tisch '{self.table_name}': Versuch, neue Partie zu starten, obwohl bereits eine läuft.")
            return

        logger.info(f"[{self.table_name}] Starte Hintergrund-Task für eine neue Partie.")
        self.game_loop_task = asyncio.create_task(
            self.run_game_loop(), name=f"GameLoop_{self.table_name}"
        )

    async def run_game_loop(self, pub: Optional[PublicState] = None, privs: Optional[List[PrivateState]] = None, break_time = 5):
        """
        Die Haupt-Coroutine, die den Spielablauf einer Partie steuert.

        Akzeptiert optionale Start-States, die direkt verwendet werden.
        Wenn keine States übergeben werden, wird der aktuelle Zustand der Engine genutzt.

        :param pub: (Optional) öffentlicher Spielzustand. Änderungen extern möglich, aber nicht vorgesehen.
        :param privs: (Optional) Private Spielzustände (müssen 4 sein). Änderungen extern möglich, aber nicht vorgesehen.
        :param break_time: Pause in Sekunden zwischen den Runden.
        """
        try:
            logger.info(f"[{self.table_name}] Starte neue Partie...")

            # --- PublicState initialisieren ---
            self._public_state = PublicState(
                table_name=self.table_name,
                player_names=[p.player_name for p in self._players],
                current_phase="playing"
            )
            if pub:
                logger.debug(f"[{self.table_name}] Verwende übergebenen PublicState.")
                self._public_state = pub

            # --- PrivateState initialisieren ---
            self._private_states = [PrivateState(player_index=i) for i in range(MAX_PLAYERS)]
            if privs:
                logger.debug(f"[{self.table_name}] Verwende übergebene PrivateStates.")
                assert len(privs) == MAX_PLAYERS and all(i == priv.player_index for i, priv in enumerate(privs))
                self._private_states = privs

            # --- Partie-Schleife (analog zu altem game_engine_.play_episode) ---
            # Zugriff auf public_state über self._public_state
            while not self._public_state.is_game_over and \
                    self._public_state.total_scores[0] < WINNING_SCORE and \
                    self._public_state.total_scores[1] < WINNING_SCORE:

                self._public_state.round_counter += 1
                round_num = self._public_state.round_counter
                logger.info(f"[{self.table_name}] Starte Runde {round_num}")

                # Führe eine einzelne Runde aus
                await self._run_round()

                # Prüfung auf Spielende nach der Runde
                if self._public_state.total_scores[0] >= WINNING_SCORE or \
                        self._public_state.total_scores[1] >= WINNING_SCORE:
                    self._public_state.is_game_over = True
                    logger.info(f"[{self.table_name}] Punktelimit ({WINNING_SCORE}) erreicht nach Runde {round_num}.")
                    break  # Verlasse Partie-Schleife

                # Fehlerprüfung nach Runde
                if self._public_state.current_phase == "error" or self._public_state.current_phase == "aborted":
                    logger.warning(f"[{self.table_name}] Runde {round_num} wurde wegen Fehlers/Abbruchs beendet. Stoppe Partie.")
                    self._public_state.is_game_over = True
                    break  # Verlasse Partie-Schleife

                # Pause zwischen den Runden
                if not self._public_state.is_game_over:
                    logger.info(f"[{self.table_name}] Runde {round_num} beendet. Nächste Runde beginnt in Kürze...")
                    await self._broadcast_public_state()  # Rundenergebnis anzeigen
                    await asyncio.sleep(break_time)

            # --- Spielende Verarbeitung ---
            if not self.public_state.current_phase.startswith("game"):  # Nur setzen, wenn normal beendet
                self.public_state.current_phase = "game_over"
            winner_team_idx = -1
            if self.public_state.total_scores[0] > self.public_state.total_scores[1]:
                winner_team_idx = 0
            elif self.public_state.total_scores[1] > self.public_state.total_scores[0]:
                winner_team_idx = 1
            logger.info(
                f"[{self.table_name}] Spiel beendet! {'Team ' + str(winner_team_idx) + ' gewinnt' if winner_team_idx != -1 else 'Unentschieden'}. Endstand: Team 0: {self.public_state.total_scores[0]}, Team 1: {self.public_state.total_scores[1]}")
            await self._broadcast_public_state()

        except asyncio.CancelledError:
            logger.info(f"[{self.table_name}] Spiel-Loop extern abgebrochen.")
            self._public_state.is_game_over = True
            self._public_state.current_phase = "aborted"
            # noinspection PyBroadException
            try:
                await self._broadcast_public_state()
            except Exception:
                pass
        except Exception as e:
            logger.exception(f"[{self.table_name}] Kritischer Fehler im Spiel-Loop: {e}")
            self._public_state.is_game_over = True
            self._public_state.current_phase = "error"
            # noinspection PyBroadException
            try:
                await self._broadcast_public_state()
            except Exception:
                pass
        finally:
            logger.info(f"[{self.table_name}] Spiel-Loop definitiv beendet.")
            self.game_loop_task = None  # Referenz aufheben

    # --------------------------------------------------------------------------
    # Platzhalter für Runden- und Stichlogik (Nächste Schritte)
    # --------------------------------------------------------------------------

    async def _run_round(self):
        """
        Führt die Logik für eine einzelne Spielrunde aus:
        Austeilen, Ansagen, Schupfen, Stiche spielen, Rundenende.
        """
        logger.debug(f"[{self.table_name}] Runde {self.public_state.round_counter}: Beginn.")
        self._reset_round_state()  # Setzt Runden-States zurück
        self.public_state.current_phase = "dealing"
        await self._broadcast_public_state()  # Zeige Start der Runde
        await asyncio.sleep(0.1)
        logger.warning(f"Rundenlogik für Runde {self.public_state.round_counter} NICHT implementiert.")
        self._public_state.is_round_over = True  # Runde künstlich beenden

    def _reset_round_state(self, _keep_total_scores=True, _increment_round_counter=True):
        """Setzt runden-spezifische Zustände zurück."""
        logger.debug(f"[{self._table_name}] Setze Runden-Zustand zurück...")
        # # Behalte Gesamtscore und Rundenzähler bei, wenn gewünscht
        # current_total_scores = self.public_state.total_scores if keep_total_scores else [0, 0]
        # current_round_counter = self.public_state.round_counter + 1 if increment_round_counter else self.public_state.round_counter

    async def _handle_announce_phase(self, grand: bool):
        pass

    async def _deal_remaining_cards(self, remaining_deck: List[Card]):
        pass

    async def _handle_schupf_phase(self) -> bool:
        pass

    async def _play_stich(self):
        pass

    async def _process_stich_action(self, player_index: int, action_data: Optional[dict]) -> bool:
        pass

    async def _handle_stich_end(self, winner_index: int):
        pass

    # ------------------------------------------------------
    # Eigenschaften
    # ------------------------------------------------------

    @property
    def table_name(self) -> str:
        """Der Name des Spieltisches (eindeutiger Identifikator)."""
        return self._table_name

    @property
    def players(self) -> List[Optional[Player]]:
        return self._players # Rückgabe der Liste (Änderungen extern möglich, aber nicht vorgesehen)

    @property
    def public_state(self) -> PublicState:
        return self._public_state

    @property
    def private_states(self) -> List[PrivateState]:
        return self._private_states
