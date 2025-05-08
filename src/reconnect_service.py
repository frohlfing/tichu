"""
Definiert den Service, der einen Client nach einem Verbindungsabbruch verwaltet.
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



class ReconnectService:

    def __init__(self):
        pass

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
        if not (0 <= slot_index < 4):
            logger.error(f"Tisch '{self._table_name}': Ungültiger Slot-Index {slot_index} beim Bestätigen für Spieler {client.player_name}.")
            # Versuche, den Client zu informieren und die Verbindung zu schließen.
            try:
                await client.close_connection(code=WSCloseCode.INTERNAL_ERROR, message='Interner Serverfehler bei Slot-Zuweisung'.encode('utf-8'))
            except Exception as e:
                logger.exception(f"Fehler bei close_connection für '{self._table_name}': {e}.")
            return

        logger.info(f"Tisch '{self._table_name}': Bestätige Spieler {client.player_name} ({client.uuid}) an Slot {slot_index}.")

        # Prüfen, ob der Slot aktuell von jemand anderem besetzt ist.
        existing_player = self._players[slot_index]
        if existing_player and existing_player.uuid != client.uuid:
            logger.warning(f"Tisch '{self._table_name}': Slot {slot_index} aktuell belegt durch {existing_player.player_name}. Ersetze.")
            if isinstance(existing_player, Client):
                # Wenn ein anderer Client dort saß, entferne ihn aus dem Tracking und schließe seine Verbindung.
                # Dies sollte selten sein, falls check_reconnect korrekt funktioniert.
                # existing_client = self._get_client_by_id(existing_player.player_id)
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
        await self._broadcast_public_state()  # Informiere alle über die neue Spielerliste.

        # Prüfe, ob das Spiel jetzt starten kann (wenn alle Plätze belegt sind).
        await self._check_start_game()

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
        if self._public_state.current_phase not in ["lobby", "setup", "game_over", "aborted", "error"]:
            logger.warning(f"Tisch '{self.table_name}': Slot-Zuweisung in Phase '{self._public_state.current_phase}' nicht erlaubt.")
            await requesting_client.notify("error", {"message": f"Slot-Zuweisung in Phase '{self._public_state.current_phase}' nicht erlaubt."})
            return

        try:
            slot_index = int(payload.get("slot_index", -1))
            player_type = payload.get("player_type")  # Erwartet "default"

            if not (0 <= slot_index < 4):
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
            self._public_state.player_names[slot_index] = default_agent.name
            await self._broadcast_public_state()  # Alle informieren

        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"Tisch '{self.table_name}': Ungültige Daten für Slot-Zuweisung empfangen: {payload} -> {e}")
            await requesting_client.notify("error", {"message": f"Ungültige Daten für Slot-Zuweisung: {e}"})
        except Exception as e:
            logger.exception(f"Tisch '{self.table_name}': Unerwarteter Fehler bei Slot-Zuweisung: {e}")
            await requesting_client.notify("error", {"message": "Interner Fehler bei Slot-Zuweisung."})

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
        if slot_index is not None and 0 <= slot_index < 4 and \
                self._players[slot_index] == disconnected_client and \
                not disconnected_client.is_connected:  # Wichtige Prüfung!

            logger.info(f"Tisch '{self._table_name}': Ersetze disconnected Client {disconnected_client.player_name} (ID: {player_id}) an Slot {slot_index} durch Agent (von Factory ausgelöst).")

            # Erstelle eine neue Agent-Instanz.
            # todo Die Klasse des Agents aus der Konfiguration holen oder 2. Idee: den vorherigen Agent nehmen.
            agent = RandomAgent(name=f"{disconnected_client.player_name} (KI)")
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
            if slot_index is None or not (0 <= slot_index < 4):
                reason = "Ungültiger Slot-Index"
            elif self._players[slot_index] != disconnected_client:
                reason = f"Slot wird von anderem Spieler ({self._players[slot_index]}) belegt"
            elif disconnected_client.is_connected:
                reason = "Spieler hat sich inzwischen wieder verbunden"
            logger.warning(f"Tisch '{self._table_name}': KI-Ersetzung für Player ID {player_id} abgebrochen. Grund: {reason}.")
            return False  # Misserfolg signalisieren.

