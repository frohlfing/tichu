import asyncio
import uuid
from aiohttp import web, WSCloseCode
from src.common.logger import logger
from src.game_engine2 import GameEngine
from src.players.client import Client
from typing import Dict, Optional, Tuple


class GameFactory:
    """Verwaltet alle laufenden Spiele (Tische)."""
    def __init__(self):
        self.games: Dict[str, GameEngine] = {}  # table_name -> GameEngine
        self._disconnect_timers: Dict[str, Tuple[asyncio.TimerHandle, str]] = {}
        self._ki_takeover_delay: float = 20.0 # Sekunden
        logger.debug("GameFactory initialisiert.")

    def get_or_create_game(self, table_name: str) -> GameEngine:
        """Holt ein Spiel anhand des Namens oder erstellt ein neues."""
        if table_name not in self.games:
            logger.info(f"Creating new game for table: {table_name}")
            self.games[table_name] = GameEngine(table_name)
        return self.games[table_name]

    async def handle_connection_request(self, websocket: web.WebSocketResponse, params: dict, remote_addr: Optional[str]) -> Tuple[Optional[Client], Optional[GameEngine]]:
        """
        Verarbeitet eine neue WebSocket-Verbindung und versucht, den Spieler einem Tisch zuzuordnen.
        Gibt (Client-Objekt, GameEngine-Objekt) bei Erfolg zurück.
        Gibt (None, None) bei Fehler zurück und schließt den WebSocket.
        """
        player_name = params.get("playerName", f"Anon_{str(uuid.uuid4())[:4]}")
        table_name = params.get("tableName")
        player_id_from_params = params.get("playerId")  # Für Reconnect

        remote_addr_str = str(remote_addr) if remote_addr else "Unbekannt"
        logger.info(f"Factory: Verarbeite Verbindungsanfrage von {remote_addr_str}: Spieler='{player_name}', Tisch='{table_name}', ID='{player_id_from_params}'")

        # --- Schritt 1: Parameter validieren ---
        if not table_name:
            logger.warning(f"Factory: Verbindung von {remote_addr_str} abgelehnt: Fehlender TischName.")
            error_message = 'Missing tableName parameter'
            await websocket.close(code=WSCloseCode.POLICY_VIOLATION, message=error_message.encode('utf-8'))
            return None, None

        # --- Schritt 2: Engine holen/erstellen ---
        try:
            # Stellt sicher, dass die Engine existiert
            engine = self.get_or_create_game(table_name)
        except Exception as e:
            error_message = "Serverfehler beim Zugriff auf den Spieltisch"
            await websocket.close(code=WSCloseCode.INTERNAL_ERROR, message=error_message.encode('utf-8'))
            return None, None

        # --- Schritt 3: Slot prüfen / Reconnect-Info holen (Engine fragen) ---
        try:
            slot_index, existing_client, error_msg = engine.check_reconnect_or_find_slot(player_id_from_params, player_name)
        except Exception as e:
            logger.exception(f"Factory: Fehler bei check_reconnect_or_find_slot für Tisch '{table_name}': {e}")
            error_message = 'Serverfehler bei der Slot-Prüfung'
            await websocket.close(code=WSCloseCode.INTERNAL_ERROR, message=error_message.encode('utf-8'))
            return None, None

        if error_msg:
            logger.warning(f"Factory: Beitritt für '{player_name}' zu Tisch '{table_name}' abgelehnt: {error_msg}")
            await websocket.close(code=WSCloseCode.POLICY_VIOLATION, message=error_msg.encode('utf-8'))
            return None, None

        if slot_index is None:
            logger.error(f"Factory: Inkonsistenter Zustand - Kein Slot und kein Fehler von Engine für Tisch '{table_name}'.")
            error_message = 'Interner Serverfehler bei Slot-Zuweisung'
            await websocket.close(code=WSCloseCode.INTERNAL_ERROR, message=error_message.encode('utf-8'))
            return None, None

        # --- Schritt 4: Client-Objekt erstellen oder aktualisieren ---
        client_obj: Client
        if existing_client:  # Reconnect
            logger.info(f"Factory: Behandle Reconnect für {existing_client.player_name} ({existing_client.player_id}) auf Tisch '{table_name}'.")
            client_obj = existing_client
            client_obj.update_websocket(websocket)  # Wichtig: WS aktualisieren
        else:  # Neuer Spieler
            logger.info(f"Factory: Erstelle neues Client-Objekt für {player_name} (ID: {player_id_from_params or 'neu'}) für Tisch '{table_name}'.")
            client_obj = Client(player_name, websocket, player_id_from_params)

        # --- Schritt 5: Beitritt bei Engine bestätigen ---
        try:
            await engine.confirm_player_join(client_obj, slot_index)
        except Exception as e:
            logger.exception(f"Factory: Fehler bei confirm_player_join für Tisch '{table_name}': {e}")
            # Client-Objekt evtl. schon in Engine? Cleanup schwierig. Verbindung schließen.
            error_message = 'Serverfehler bei der Bestätigung des Beitritts'
            await websocket.close(code=WSCloseCode.INTERNAL_ERROR, message=error_message.encode('utf-8'))
            # Hier müssten wir evtl. den Client wieder aus der Engine entfernen, falls schon hinzugefügt. Komplex.
            return None, None

        # --- Schritt 6: Erfolgreichen (Re)Connect melden (bricht Timer ab) ---
        # Verwende die definitive ID des Client-Objekts
        self.notify_player_connect_or_reconnect(table_name, client_obj.player_id, client_obj.player_name)

        # --- Schritt 7: Bestätigung an Client senden ---
        try:
            await client_obj.notify("joined_table", {
                "message": f"Erfolgreich Tisch '{table_name}' beigetreten als '{client_obj.player_name}' an Position {slot_index}.",
                "tableName": table_name,
                "playerName": client_obj.player_name,
                "playerId": client_obj.player_id,
                "playerIndex": slot_index
            })
        except Exception as e:
            # Wenn das Senden der Bestätigung fehlschlägt, ist die Verbindung wahrscheinlich schon wieder weg.
            logger.warning(f"Factory: Senden der Beitrittsbestätigung an {client_obj.player_name} fehlgeschlagen: {e}. Verbindung wird wahrscheinlich bald getrennt.")
            # Wir lassen die Verbindung aber erstmal offen, der Handler merkt den Disconnect dann.

        # Am Ende erfolgreich:
        logger.info(f"Factory: Spieler {client_obj.player_name} ({client_obj.player_id}) erfolgreich Tisch '{table_name}' zugeordnet (von {remote_addr_str}).")

        # Gib Client und Engine an den Handler zurück
        return client_obj, engine

    # Wird vom websocket_handler aufgerufen, wenn Client connected
    def notify_player_connect_or_reconnect(self, table_name: str, player_id: str, player_name: str):
        """
        Informiert die Factory über einen Connect/Reconnect.
        Wird genutzt, um einen evtl. laufenden KI-Übernahme-Timer abzubrechen.
        """
        logger.debug(f"Factory: Empfangen (Re-)Connect für Spieler {player_name} ({player_id}) auf Tisch '{table_name}'.")
        # Bricht Timer ab, falls vorhanden
        self._cancel_disconnect_timer(player_id)

    # Wird vom websocket_handler bei Disconnect aufgerufen
    def notify_player_disconnect(self, table_name: str, player_id: str, player_name: str):
        """
        Nimmt Disconnect-Meldung entgegen und startet den KI-Übernahme-Timer.
        """
        # Prüfen, ob der Tisch überhaupt (noch) existiert
        if table_name not in self.games:
            logger.warning(f"Factory: Disconnect für Spieler {player_name} ({player_id}) auf Tisch '{table_name}' gemeldet, aber Tisch nicht gefunden.")
            return
        # Prüfen, ob nicht schon ein Timer für diesen Spieler läuft (Sicherheit)
        if player_id in self._disconnect_timers:
            logger.warning(f"Factory: Disconnect für Spieler {player_name} ({player_id}) gemeldet, aber Timer läuft bereits. Ignoriere.")
            return

        logger.info(f"Factory: Starte KI Übernahme Timer ({self._ki_takeover_delay}s) für Spieler {player_name} ({player_id}) auf Tisch '{table_name}'.")
        loop = asyncio.get_running_loop()
        timer_handle = loop.call_later(self._ki_takeover_delay, self._ki_takeover_callback, player_id)
        self._disconnect_timers[player_id] = (timer_handle, table_name)

    def _cancel_disconnect_timer(self, player_id: str):
        """Bricht den KI-Übernahme-Timer für einen Spieler ab (falls vorhanden)."""
        if player_id in self._disconnect_timers:
            timer_handle, table_name = self._disconnect_timers.pop(player_id)
            timer_handle.cancel()
            logger.info(f"Factory: KI Übernahme Timer für Player ID {player_id} auf Tisch '{table_name}' abgebrochen (z.B. wegen Reconnect).")

    def _ki_takeover_callback(self, player_id: str):
        """
        Callback, der ausgeführt wird, wenn der Timer abläuft. Läuft synchron.
        Plant die asynchrone Ersetzung und das Aufräumen.
        """
        # Timer aus Verwaltung entfernen, da er abgelaufen ist
        if player_id in self._disconnect_timers:
            _timer_handle, table_name = self._disconnect_timers.pop(player_id)
            logger.info(f"Factory: KI Übernahme Timer für Player ID {player_id} auf Tisch '{table_name}' abgelaufen. Plane Ersetzung/Cleanup.")
            # Asynchrone Logik als Task starten
            asyncio.create_task(self._handle_ki_takeover_and_cleanup(player_id, table_name))
        else:
            # Kann passieren, wenn cancel und callback sich überschneiden
            logger.debug(f"Factory: KI takeover callback für Player ID {player_id} ausgelöst, aber kein Timer mehr registriert (vermutlich bereits abgebrochen).")

    async def _handle_ki_takeover_and_cleanup(self, player_id: str, table_name: str):
        """
        Führt die KI-Ersetzung in der Engine aus und prüft danach,
        ob die Engine entfernt werden soll.
        """
        engine = self.games.get(table_name)
        if not engine:
            logger.warning(f"Factory: KI-Ersetzung für Player ID {player_id} auf Tisch '{table_name}' nicht möglich, Tisch existiert nicht mehr.")
            return

        # 1. Führe Ersetzung in der Engine durch
        logger.debug(f"Factory: Fordere Engine für Tisch '{table_name}' auf, Spieler {player_id} zu ersetzen.")
        success = await engine.replace_player_with_agent(player_id)

        if not success:
            logger.warning(f"Factory: KI-Ersetzung von Spieler {player_id} auf Tisch '{table_name}' wurde von der Engine abgelehnt oder ist fehlgeschlagen.")
            # Tisch nicht entfernen, da der Zustand unklar ist oder der Spieler evtl. doch reconnected hat
            return

        if engine.is_empty_of_humans():
            logger.info(f"Factory: Tisch '{table_name}' ist nach KI-Ersetzung leer. Entferne den Tisch.")
            await self.remove_game(table_name)

        # 2. Prüfe, ob die Engine jetzt leer ist
        logger.debug(f"Factory: Prüfe nach KI-Ersetzung, ob Tisch '{table_name}' leer ist.")
        if engine.is_empty_of_humans():
            logger.info(f"Factory: Tisch '{table_name}' ist nach KI-Ersetzung leer. Entferne den Tisch.")
            # Hier entfernt die Factory den Tisch direkt
            await self.remove_game(table_name)
        else:
            logger.debug(f"Factory: Tisch '{table_name}' ist nach KI-Ersetzung nicht leer.")

    async def remove_game(self, table_name: str):
        """Entfernt ein Spiel aus der Verwaltung (wenn es leer ist)."""
        if table_name in self.games:
            logger.info(f"Factory: Removing game table: {table_name}")
            game_engine = self.games.pop(table_name)
            await game_engine.cleanup() # Ressourcen der Engine freigeben
        else:
            logger.warning(f"Factory: Attempted to remove non-existent game: {table_name}")

    async def shutdown(self):
        """Fährt alle Spiele herunter und bricht laufende Timer ab."""
        logger.info("GameFactory fährt herunter...")

        # 1. Alle laufenden KI-Übernahme-Timer abbrechen
        logger.info(f"Breche {len(self._disconnect_timers)} laufende KI Übernahme Timer ab.")
        timer_ids = list(self._disconnect_timers.keys())
        for player_id in timer_ids:
            self._cancel_disconnect_timer(player_id)  # Bricht ab und entfernt aus Dict

        # 2. Alle verbleibenden Spiele herunterfahren
        logger.info("Fahre alle aktiven Game Engines herunter...")
        await asyncio.gather(*[asyncio.create_task(e.cleanup()) for e in self.games.values()], return_exceptions=True)

        self.games.clear()
        logger.info("GameFactory Shutdown abgeschlossen.")
