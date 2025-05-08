"""
Definiert den Eingangsbereich, von wo aus die Spieler ein Spiel aussuchen und beitreten.
"""

import asyncio
import config
import json
import os
import signal
import sys
import uuid
from aiohttp import web, WSMsgType, WSCloseCode, WSMessage
from aiohttp.web import Application, AppRunner, Request, WebSocketResponse, TCPSite
from src.common.errors import PlayerTimeoutError, ClientDisconnectedError, PlayerResponseError
from src.common.logger import logger
from src.common.rand import Random
from src.game_engine2 import GameEngine
from src.game_factory import GameFactory
from src.lib.cards import Card, deck
from src.players.player import Player
from src.players.agent import Agent
from src.players.random_agent import RandomAgent
from src.players.client import Client
from src.private_state2 import PrivateState
from src.public_state2 import PublicState
from typing import List, Dict, Optional, Tuple


class Lobby:
    """
    Verarbeitet die Logik für Beitritt/Reconnect
    """

    def __init__(self):
        pass

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
            logger.info(f"Factory: Behandle Reconnect für {existing_client._name} ({existing_client._uuid}) auf Tisch '{table_name}'.")
            client_obj = existing_client
            client_obj.update_websocket(websocket, engine.interrupt_events) # Bestehendes Objekt mit neuem WebSocket aktualisieren
        else:  # Neuer Spieler
            logger.info(f"Factory: Erstelle neues Client-Objekt für {player_name} (ID: {player_id_from_params or 'neu'}) für Tisch '{table_name}'.")
            # Nutze übergebene ID oder generiere neue
            client_obj = Client(player_name, websocket, engine.interrupt_events, player_id_from_params)

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
        self.notify_player_connect_or_reconnect(table_name, client_obj._uuid, client_obj._name)

        # --- Schritt 7: Bestätigung an Client senden ---
        try:
            # Sende alle notwendigen Informationen an den Client zurück.
            await client_obj.notify("joined_table", {
                "message": f"Erfolgreich Tisch '{table_name}' beigetreten als '{client_obj._name}' an Position {slot_index}.",
                "tableName": table_name,
                "playerName": client_obj._name,
                "playerId": client_obj._uuid, # Client muss seine ID kennen!
                "playerIndex": slot_index
            })
        except Exception as e:
            # Wenn das Senden fehlschlägt, ist die Verbindung meist eh schon weg.
            logger.warning(f"Factory: Senden der Beitrittsbestätigung an {client_obj._name} fehlgeschlagen: {e}. Verbindungsproblem wahrscheinlich.")
            # Keine direkte Aktion hier, der `finally` Block im Handler wird es merken.

        logger.info(f"Factory: Spieler {client_obj._name} ({client_obj._uuid}) erfolgreich Tisch '{table_name}' zugeordnet (von {remote_addr_str}).")
        # Gib die erstellten/gefundenen Objekte an den Handler zurück.
        return client_obj, engine