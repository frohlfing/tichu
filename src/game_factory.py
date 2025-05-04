"""
Definiert die GameFactory-Klasse, die für die Verwaltung aller laufenden Tichu-Spiele (GameEngine-Instanzen)
und für das Handling von Verbindungsanfragen und Spieler-Disconnect-Timern zuständig ist.
"""

import asyncio
import uuid
from aiohttp import web, WSCloseCode
from src.common.logger import logger
from src.game_engine2 import GameEngine
from src.players.client import Client
from typing import Dict, Optional, Tuple


class GameFactory:
    """
    Verwaltet die Erstellung, den Zugriff und die Bereinigung von GameEngine-Instanzen.

    Diese Klasse fungiert als zentraler Einstiegspunkt für neue Spieler-Verbindungen
    und verwaltet den Lebenszyklus der einzelnen Spieltische.
    Sie ist auch verantwortlich für das Starten und Verwalten von Timern für getrennte Verbindungen,
    um ggf. eine KI-Übernahme einzuleiten und leere Tische automatisch zu entfernen.
    """
    def __init__(self):
        """
        Initialisiert die GameFactory.
        """
        #: Dictionary, das aktive Spiele über ihren Tischnamen verwaltet.
        #: Schlüssel: table_name (str), Wert: GameEngine-Instanz.
        self.games: Dict[str, GameEngine] = {}
        #: Dictionary zur Verwaltung der laufenden Disconnect-Timer.
        #: Schlüssel: player_id (str), Wert: Tupel (asyncio.TimerHandle, table_name).
        self._disconnect_timers: Dict[str, Tuple[asyncio.TimerHandle, str]] = {}
        #: Zeit in Sekunden, nach der ein getrennter Spieler durch eine KI ersetzt wird.
        self._ki_takeover_delay: float = 20.0  # TODO: Konfigurierbar machen? (z.B. über config.py)

        logger.info("GameFactory initialisiert.")

    def get_or_create_game(self, table_name: str) -> GameEngine:
        """
        Gibt die GameEngine-Instanz für einen gegebenen Tischnamen zurück.
        Erstellt eine neue Engine, falls der Tisch noch nicht existiert.

        :param table_name: Der Name des Tisches.
        :return: Die GameEngine-Instanz für diesen Tisch.
        """
        if table_name not in self.games:
            logger.info(f"Erstelle neues Spiel für Tisch: '{table_name}'")
            # Erstellt die Engine (ohne Timer-Verwaltung in der Engine selbst)
            self.games[table_name] = GameEngine(table_name)
            # Kein separater Cleanup-Task mehr benötigt, da Cleanup nach Timer-Ablauf erfolgt.
        return self.games[table_name]

    async def handle_connection_request(self, websocket: web.WebSocketResponse, params: dict, remote_addr: Optional[str]) -> Tuple[Optional[Client], Optional[GameEngine]]:
        """
        Verarbeitet eine neue WebSocket-Verbindungsanfrage.

        Orchestriert den Prozess:
        1. Validiert Parameter (Tischname).
        2. Holt/Erstellt die zuständige GameEngine.
        3. Fragt die Engine nach einem freien Slot oder prüft auf Reconnect.
        4. Erstellt/Aktualisiert das Client-Objekt.
        5. Bestätigt den Beitritt bei der Engine.
        6. Bricht ggf. einen laufenden Disconnect-Timer ab.
        7. Sendet eine Bestätigung an den Client.

        Schließt den WebSocket bei Fehlern während des Prozesses.

        :param websocket: Das WebSocketResponse-Objekt der neuen Verbindung.
        :param params: Die aus der URL extrahierten Query-Parameter.
        :param remote_addr: Die IP-Adresse des Clients (für Logging).
        :return: Ein Tupel (Client-Objekt, GameEngine-Objekt) bei Erfolg, sonst (None, None).
        """
        player_name = params.get("playerName", f"Anon_{str(uuid.uuid4())[:4]}") # Standardname, falls nicht angegeben
        table_name = params.get("tableName")
        player_id_from_params = params.get("playerId") # Für Reconnect

        remote_addr_str = str(remote_addr) if remote_addr else "Unbekannt"
        logger.info(f"Factory: Verarbeite Verbindungsanfrage von {remote_addr_str}: Spieler='{player_name}', Tisch='{table_name}', ID='{player_id_from_params}'")

        # --- Schritt 1: Parameter validieren ---
        if not table_name:
            logger.warning(f"Factory: Verbindung von {remote_addr_str} abgelehnt: Fehlender TischName.")
            error_message = 'Tischname fehlt' # Deutsche Meldung
            await websocket.close(code=WSCloseCode.POLICY_VIOLATION, message=error_message.encode('utf-8'))
            return None, None

        # --- Schritt 2: Engine holen/erstellen ---
        try:
            engine = self.get_or_create_game(table_name)
        except Exception as e:
            logger.exception(f"Factory: Kritischer Fehler beim Holen/Erstellen der Engine für Tisch '{table_name}': {e}")
            error_message = "Serverfehler beim Zugriff auf den Spieltisch"
            await websocket.close(code=WSCloseCode.INTERNAL_ERROR, message=error_message.encode('utf-8'))
            return None, None

        # --- Schritt 3: Slot prüfen / Reconnect-Info holen (Engine fragen) ---
        try:
            slot_index, existing_client, error_msg = engine.check_reconnect_or_find_slot(player_id_from_params, player_name)
        except Exception as e:
            logger.exception(f"Factory: Kritischer Fehler bei check_reconnect_or_find_slot für Tisch '{table_name}': {e}")
            error_message = 'Serverfehler bei der Slot-Prüfung'
            await websocket.close(code=WSCloseCode.INTERNAL_ERROR, message=error_message.encode('utf-8'))
            return None, None

        if error_msg: # Wenn die Engine den Beitritt ablehnt (z.B. Tisch voll)
            logger.warning(f"Factory: Beitritt für '{player_name}' zu Tisch '{table_name}' abgelehnt: {error_msg}")
            await websocket.close(code=WSCloseCode.POLICY_VIOLATION, message=error_msg.encode('utf-8'))
            return None, None

        if slot_index is None: # Sollte nicht passieren, wenn kein error_msg kam
            logger.error(f"Factory: Inkonsistenter Zustand - Kein Slot und kein Fehler von Engine für Tisch '{table_name}'.")
            error_message = 'Interner Serverfehler bei Slot-Zuweisung'
            await websocket.close(code=WSCloseCode.INTERNAL_ERROR, message=error_message.encode('utf-8'))
            return None, None

        # --- Schritt 4: Client-Objekt erstellen oder aktualisieren ---
        client_obj: Client
        if existing_client:  # Reconnect-Fall
            logger.info(f"Factory: Behandle Reconnect für {existing_client.player_name} ({existing_client.player_id}) auf Tisch '{table_name}'.")
            client_obj = existing_client
            client_obj.update_websocket(websocket) # Bestehendes Objekt mit neuem WebSocket aktualisieren
        else:  # Neuer Spieler
            logger.info(f"Factory: Erstelle neues Client-Objekt für {player_name} (ID: {player_id_from_params or 'neu'}) für Tisch '{table_name}'.")
            # Nutze übergebene ID oder generiere neue
            client_obj = Client(player_name, websocket, player_id_from_params)

        # --- Schritt 5: Beitritt bei Engine bestätigen ---
        try:
            # Engine weist den Slot zu und aktualisiert ihren internen Zustand.
            await engine.confirm_player_join(client_obj, slot_index)
        except Exception as e:
            logger.exception(f"Factory: Kritischer Fehler bei confirm_player_join für Tisch '{table_name}': {e}")
            # Zustand ist jetzt potenziell inkonsistent. Verbindung schließen.
            error_message = 'Serverfehler bei der Bestätigung des Beitritts'
            await websocket.close(code=WSCloseCode.INTERNAL_ERROR, message=error_message.encode('utf-8'))
            # TODO: Überlegen, ob hier ein Cleanup des (evtl. halb hinzugefügten) Clients in der Engine nötig ist.
            return None, None

        # --- Schritt 6: Erfolgreichen (Re)Connect melden (bricht Timer ab) ---
        # Wichtig: Nachdem der Beitritt bei der Engine erfolgreich war.
        self.notify_player_connect_or_reconnect(table_name, client_obj.player_id, client_obj.player_name)

        # --- Schritt 7: Bestätigung an Client senden ---
        try:
            # Sende alle notwendigen Informationen an den Client zurück.
            await client_obj.notify("joined_table", {
                "message": f"Erfolgreich Tisch '{table_name}' beigetreten als '{client_obj.player_name}' an Position {slot_index}.",
                "tableName": table_name,
                "playerName": client_obj.player_name,
                "playerId": client_obj.player_id, # Client muss seine ID kennen!
                "playerIndex": slot_index
            })
        except Exception as e:
            # Wenn das Senden fehlschlägt, ist die Verbindung meist eh schon weg.
            logger.warning(f"Factory: Senden der Beitrittsbestätigung an {client_obj.player_name} fehlgeschlagen: {e}. Verbindungsproblem wahrscheinlich.")
            # Keine direkte Aktion hier, der `finally` Block im Handler wird es merken.

        logger.info(f"Factory: Spieler {client_obj.player_name} ({client_obj.player_id}) erfolgreich Tisch '{table_name}' zugeordnet (von {remote_addr_str}).")
        # Gib die erstellten/gefundenen Objekte an den Handler zurück.
        return client_obj, engine

    def notify_player_connect_or_reconnect(self, table_name: str, player_id: str, player_name: str):
        """
        Bricht einen eventuell laufenden KI-Übernahme-Timer für den (wieder)verbundenen Spieler ab.

        Wird intern von `handle_connection_request` aufgerufen.

        :param table_name: Name des betroffenen Tisches.
        :param player_id: ID des Spielers.
        :param player_name: Name des Spielers (für Logging).
        """
        logger.debug(f"Factory: Empfangen (Re-)Connect für Spieler {player_name} ({player_id}) auf Tisch '{table_name}'. Prüfe Timer.")
        # Ruft die interne synchrone Methode zum Abbrechen auf.
        self._cancel_disconnect_timer(player_id)

    def notify_player_disconnect(self, table_name: str, player_id: str, player_name: str):
        """
        Startet den KI-Übernahme-Timer, wenn ein Disconnect vom Handler gemeldet wird.

        Ignoriert die Anforderung, wenn der Tisch nicht (mehr) existiert oder bereits ein Timer für diesen Spieler läuft.

        :param table_name: Name des betroffenen Tisches.
        :param player_id: ID des Spielers.
        :param player_name: Name des Spielers (für Logging).
        """
        # Prüfe, ob der Tisch (noch) existiert.
        if table_name not in self.games:
            logger.warning(f"Factory: Disconnect für Spieler {player_name} ({player_id}) auf Tisch '{table_name}' gemeldet, aber Tisch nicht gefunden.")
            return
        # Prüfe, ob bereits ein Timer läuft (verhindert doppelte Timer).
        if player_id in self._disconnect_timers:
            logger.warning(f"Factory: Disconnect für Spieler {player_name} ({player_id}) gemeldet, aber Timer läuft bereits. Ignoriere.")
            return

        logger.info(f"Factory: Starte KI Übernahme Timer ({self._ki_takeover_delay:.1f}s) für Spieler {player_name} ({player_id}) auf Tisch '{table_name}'.")
        # Hole die aktuelle Event-Loop.
        loop = asyncio.get_running_loop()
        # Plane den Callback für die Zukunft. `call_later` ist nicht blockierend.
        timer_handle = loop.call_later(self._ki_takeover_delay, self._ki_takeover_callback, player_id)
        # Speichere das TimerHandle und den Tischnamen, um den Timer später ggf. abbrechen zu können.
        self._disconnect_timers[player_id] = (timer_handle, table_name)

    def _cancel_disconnect_timer(self, player_id: str):
        """Interne Methode zum sicheren Abbrechen und Entfernen eines Timers."""
        if player_id in self._disconnect_timers:
            timer_handle, table_name = self._disconnect_timers.pop(player_id) # Entferne aus Dict
            timer_handle.cancel() # Breche den geplanten Aufruf ab
            logger.info(f"Factory: KI Übernahme Timer für Spieler ID {player_id} auf Tisch '{table_name}' abgebrochen.")

    def _ki_takeover_callback(self, player_id: str):
        """
        Synchroner Callback, der ausgeführt wird, wenn ein Disconnect-Timer abläuft.

        Dieser Callback sollte schnell sein und nur die asynchrone Verarbeitung der KI-Ersetzung
        und des potenziellen Cleanups anstoßen.

        :param player_id: Die ID des Spielers, dessen Timer abgelaufen ist.
        """
        # Prüfe, ob der Timer noch in der Verwaltung ist (könnte durch Race Condition schon weg sein).
        if player_id in self._disconnect_timers:
            _timer_handle, table_name = self._disconnect_timers.pop(player_id) # Entferne jetzt
            logger.info(f"Factory: KI Übernahme Timer für Spieler ID {player_id} auf Tisch '{table_name}' abgelaufen. Plane asynchrone Verarbeitung.")
            # Starte die eigentliche Logik (KI ersetzen, Tisch prüfen) als separaten Task.
            asyncio.create_task(self._handle_ki_takeover_and_cleanup(player_id, table_name))
        else:
            # Der Timer wurde wahrscheinlich kurz vor dem Callback durch einen Reconnect abgebrochen.
            logger.debug(f"Factory: KI Übernahme Callback für Spieler ID {player_id} ausgelöst, aber kein Timer mehr registriert (wahrscheinlich abgebrochen).")

    async def _handle_ki_takeover_and_cleanup(self, player_id: str, table_name: str):
        """
        Asynchrone Verarbeitung nach Ablauf eines Disconnect-Timers.

        1. Weist die zuständige GameEngine an, den Spieler durch eine KI zu ersetzen.
        2. Prüft, ob die Engine danach leer von menschlichen Spielern ist.
        3. Wenn ja, entfernt die Engine aus der Verwaltung (`remove_game`).

        :param player_id: ID des Spielers, der ersetzt werden soll.
        :param table_name: Name des betroffenen Tisches.
        """
        engine = self.games.get(table_name)
        if not engine:
            # Die Engine existiert nicht mehr (wurde vielleicht schon entfernt).
            logger.warning(f"Factory: KI-Ersetzung für Spieler ID {player_id} auf Tisch '{table_name}' nicht möglich, Tisch existiert nicht mehr.")
            return

        # 1. Versuche, den Spieler in der Engine durch eine KI zu ersetzen.
        logger.debug(f"Factory: Fordere Engine für Tisch '{table_name}' auf, Spieler {player_id} zu ersetzen.")
        success = await engine.replace_player_with_agent(player_id)

        if not success:
            # Die Ersetzung ist fehlgeschlagen (z.B. weil der Spieler doch wieder da war).
            logger.warning(f"Factory: KI-Ersetzung von Spieler {player_id} auf Tisch '{table_name}' wurde von der Engine abgelehnt oder ist fehlgeschlagen. Tisch wird nicht entfernt.")
            return

        # 2. Prüfe, ob der Tisch *nach erfolgreicher Ersetzung* leer ist.
        logger.debug(f"Factory: Prüfe nach KI-Ersetzung, ob Tisch '{table_name}' leer ist.")
        try:
            if engine.is_empty_of_humans():
                logger.info(f"Factory: Tisch '{table_name}' ist nach KI-Ersetzung leer. Entferne den Tisch.")
                # Entferne den Tisch aus der Verwaltung (ruft auch engine.cleanup()).
                await self.remove_game(table_name)
            else:
                logger.debug(f"Factory: Tisch '{table_name}' ist nach KI-Ersetzung nicht leer.")
        except Exception as e:
            logger.exception(f"Factory: Fehler bei Prüfung oder Entfernung des leeren Tisches '{table_name}': {e}")

    async def remove_game(self, table_name: str):
        """
        Entfernt eine GameEngine-Instanz sicher aus der Verwaltung.

        Wird aufgerufen, wenn ein Tisch nach KI-Ersetzung als leer erkannt wird.
        Ruft auch die `cleanup`-Methode der Engine auf.

        :param table_name: Der Name des zu entfernenden Tisches.
        """
        if table_name in self.games:
            logger.info(f"Factory: Entferne Spieltisch: '{table_name}'")
            game_engine = self.games.pop(table_name) # Entferne aus dem Dictionary
            try:
                await game_engine.cleanup() # Rufe die Aufräum-Methode der Engine auf
            except Exception as e:
                logger.exception(f"Factory: Fehler während des Cleanups der Engine für Tisch '{table_name}': {e}")
        else:
            # Sollte selten vorkommen, da _handle_ki_takeover prüft, bevor es aufruft
            logger.warning(f"Factory: Versuch, nicht existierenden Tisch '{table_name}' zu entfernen.")

    async def shutdown(self):
        """
        Fährt die GameFactory und alle zugehörigen Spiele und Timer sauber herunter.

        Wird normalerweise am Ende des Server-Lebenszyklus aufgerufen.
        """
        logger.info("GameFactory fährt herunter...")

        # 1. Breche alle noch laufenden Disconnect-Timer ab.
        if self._disconnect_timers:
             count = len(self._disconnect_timers)
             logger.info(f"Breche {count} laufende KI Übernahme Timer ab...")
             # Kopiere die IDs, da das Dictionary während der Iteration geändert wird.
             timer_ids = list(self._disconnect_timers.keys())
             for player_id in timer_ids:
                 self._cancel_disconnect_timer(player_id) # Bricht ab und entfernt aus Dict

        # 2. Fahre alle noch aktiven Game Engines herunter (ruft deren cleanup Methode).
        if self.games:
            logger.info(f"Fahre {len(self.games)} aktive Game Engines herunter...")
            # Starte alle cleanups parallel und warte darauf.
            await asyncio.gather(*[asyncio.create_task(e.cleanup()) for e in self.games.values()], return_exceptions=True)
        else:
            logger.info("Keine aktiven Game Engines zum Herunterfahren vorhanden.")

        # 3. Leere das Game-Dictionary.
        self.games.clear()
        logger.info("GameFactory Shutdown abgeschlossen.")
