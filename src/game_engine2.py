import asyncio
from aiohttp import WSCloseCode
from src.common.logger import logger
from src.players.agent import Agent
from src.players.client import Client
from src.players.player import Player
from src.private_state2 import PrivateState
from src.public_state2 import PublicState
from typing import List, Dict, Optional, Tuple


class GameEngine:
    """Verwaltet die Logik und den Zustand eines einzelnen Tichu-Tisches."""
    MAX_PLAYERS = 4

    def __init__(self, table_name: str):
        self.table_name: str = table_name

        # Slots für Spieler initial leer oder mit KIs
        self.players: List[Optional[Player]] = [None] * self.MAX_PLAYERS

        # Clients speichern, um sie bei reconnect zu finden über player_id
        self._clients: Dict[str, Client] = {}
        self.public_state: PublicState = PublicState(table_name=table_name)

        # Jeder Spieler hat seinen eigenen privaten Zustand
        self.private_states: List[PrivateState] = [PrivateState(player_index=i) for i in range(self.MAX_PLAYERS)]

        # todo wofür?
        self.game_loop_task: Optional[asyncio.Task] = None

        # Optional: Tisch direkt mit KIs füllen
        # for i in range(self.MAX_PLAYERS):
        #     self.players[i] = Agent(ai_level=1)
        #     self.players[i].assign_game(self, i)

        logger.info(f"GameEngine created for table: {table_name}")

    def _get_player_names(self) -> List[Optional[str]]:
        """Hilfsmethode, um die Namen der Spieler in der Liste zu erhalten."""
        return [p.player_name if p else None for p in self.players]

    #  Wird vom websocket_handler aufgerufen
    def check_reconnect_or_find_slot(self, player_id: Optional[str], player_name: str) -> Tuple[Optional[int], Optional[Client], Optional[str]]:
        """Prüft Reconnect oder findet neuen Slot. Timer-Abbruch erfolgt in der Factory!"""
        # 1. Reconnect-Versuch?
        if player_id and player_id in self._clients:
            existing_client = self._clients[player_id]
            if not existing_client.is_connected:
                # Ja, ist ein Reconnect-Versuch für einen bekannten, getrennten Client
                logger.info(f"Tisch '{self.table_name}': Reconnect Versuch für bekannten Spieler {existing_client.player_name} ({player_id}) an Index {existing_client.player_index}.")
                return existing_client.player_index, existing_client, None
            elif existing_client.is_connected:
                # Spieler ist bereits verbunden (vielleicht alter Tab offen?)
                logger.warning(f"Table {self.table_name}: Player '{player_name}' ({player_id}) is already connected.")
                return None, None, f"Player '{player_name}' ({player_id}) is already connected to this table."
            # else: # Sollte nicht passieren, Client ist in _clients aber weder connected noch disconnected?
            #    logger.error(f"Inconsistent state for player {player_id}")
            #    del self._clients[player_id] # Bereinigen

        # 2. Neuen Platz suchen (prüft nur, ob ID schon vergeben ist, falls eine kam)
        if player_id and player_id in self._clients:
            # Ein anderer Spieler (aber verbunden) hat diese ID bereits - unwahrscheinlich mit UUIDs
            logger.error(f"Table {self.table_name}: Player ID {player_id} (Name: {player_name}) already in use by a connected player.")
            return None, None, f"Player ID {player_id} is already in use at this table."

        # 3. Freien Slot suchen (leer oder KI)
        available_slot = -1
        for i, p in enumerate(self.players):
            if p is None:  # Leerer Slot ist bevorzugt
                available_slot = i
                break
            if isinstance(p, Agent):  # KI-Slot als zweite Wahl
                if available_slot == -1:  # Nur nehmen, wenn noch kein leerer Slot gefunden wurde
                    available_slot = i

        if available_slot != -1:
            logger.info(f"Table {self.table_name}: Found available slot {available_slot} for new player {player_name} (ID: {player_id or 'new'})")
            return available_slot, None, None  # Slot gefunden, kein Reconnect
        else:
            logger.warning(f"Table {self.table_name} is full for player {player_name}")
            return None, None, f"Table '{self.table_name}' is full."

    # Wird vom websocket_handler aufgerufen
    async def confirm_player_join(self, client: Client, slot_index: int):
        """
        Bestätigt das Hinzufügen oder Aktualisieren eines Clients an einem bestimmten Slot.
        Wird vom websocket_handler aufgerufen, nachdem check_reconnect_or_find_slot erfolgreich war.
        Ersetzt ggf. vorhandene Spieler/Agenten an diesem Slot.
        Aktualisiert den Spielzustand und benachrichtigt die Spieler.
        """
        if not (0 <= slot_index < self.MAX_PLAYERS):
            logger.error(f"Tisch '{self.table_name}': Ungültiger Slot-Index {slot_index} für Spieler {client.player_name}.")
            await client.close_connection(code=WSCloseCode.INTERNAL_ERROR, message=b'Interner Fehler bei der Slot-Zuweisung')
            return

        logger.info(f"Tisch '{self.table_name}': Bestätige Spieler {client.player_name} ({client.player_id}) an Slot {slot_index}.")

        # Alten Spieler/KI an diesem Platz ggf. entfernen/informieren
        existing_player = self.players[slot_index]
        if existing_player and existing_player.player_id != client.player_id:
            logger.warning(f"Tisch '{self.table_name}': Slot {slot_index} aktuell belegt durch {existing_player.player_name}. Ersetze.")
            if isinstance(existing_player, Client):
                # Anderen Client entfernen (sollte durch check_reconnect_or_find_slot verhindert werden, aber sicher ist sicher)
                if existing_player.player_id in self._clients:
                    del self._clients[existing_player.player_id]
                await existing_player.close_connection(message=b'Slot taken by new player')  # Alten Client informieren & trennen
            # Agent oder None braucht keine spezielle Behandlung hier

        # Spieler am Slot platzieren und im Tracking vermerken
        self.players[slot_index] = client
        self._clients[client.player_id] = client # Client im Dictionary hinzufügen/aktualisieren
        client.player_index = slot_index

        # Relevanten Spielzustand senden
        await self._send_private_state(client) # Privaten Zustand an den beitretenden Spieler senden
        await self._broadcast_public_state() # Alle über die aktualisierte Spielerliste informieren

        # Prüfen, ob das Spiel starten/fortgesetzt werden kann
        await self._check_start_game()

    async def _broadcast_public_state(self):
        """Sendet den aktuellen öffentlichen Zustand an alle verbundenen Clients."""
        self.public_state.player_names = self._get_player_names()
        # ... andere public_state Felder aktualisieren ...
        state_dict = self.public_state.to_dict()
        for player in self.players:
            # Nur an verbundene Clients senden
            if isinstance(player, Client) and player.is_connected:
                await player.notify("public_state_update", state_dict)

    async def _send_private_state(self, player: Player):
        """Sendet den privaten Zustand an einen spezifischen Spieler."""
        if player.player_index is not None:
            private_state = self.private_states[player.player_index]
            # ... private_state Felder aktualisieren (z.B. Handkarten) ...
            if isinstance(player, Client) and player.is_connected:
                await player.notify("private_state_update", private_state.to_dict())

    def find_slot_for_human(self, player_name: str, player_id: str) -> Tuple[Optional[int], Optional[Client], Optional[str]]:
        """
        Sucht einen Platz für einen menschlichen Spieler.
        Prüft, ob der Spieler (via ID) schon am Tisch war und disconnected ist.
        Prüft, ob ein Platz frei ist oder von einer KI besetzt ist.
        Gibt (slot_index, reconnected_client, error_message) zurück.
        """
        # 1. Reconnect-Versuch?
        if player_id in self._clients:
            existing_client = self._clients[player_id]
            if not existing_client.is_connected and existing_client.player_index is not None:
                 logger.info(f"Found disconnected client {player_name} ({player_id}) at index {existing_client.player_index}. Reconnecting.")
                 # Timer abbrechen passiert in update_websocket
                 return existing_client.player_index, existing_client, None # Slot gefunden, Client-Objekt für Update zurückgeben
            elif existing_client.is_connected:
                 return None, None, f"Player '{player_name}' ({player_id}) is already connected to this table."
            else: # Sollte nicht passieren, aber sicherheitshalber
                 del self._clients[player_id] # Aus der Liste entfernen, wenn inkonsistent

        # 2. Neuen Platz suchen (leerer Slot oder KI-Slot)
        available_slot = -1
        for i, p in enumerate(self.players):
            if p is None:
                available_slot = i
                break
            if isinstance(p, Agent):
                available_slot = i
                break # Nimm den ersten freien/KI-Slot

        if available_slot != -1:
            logger.info(f"Found available slot {available_slot} for new player {player_name}")
            return available_slot, None, None # Slot gefunden, kein Reconnect
        else:
            logger.info(f"Table {self.table_name} is full for player {player_name}")
            return None, None, f"Table '{self.table_name}' is full (only human players)."

    async def add_player(self, client: Client, slot_index: int):
        """Fügt einen Client an einem bestimmten Slot hinzu (ersetzt ggf. KI/None)."""
        if 0 <= slot_index < self.MAX_PLAYERS:
            logger.info(f"Adding player {client.player_name} to slot {slot_index} in table {self.table_name}")
            existing_player = self.players[slot_index]
            if isinstance(existing_player, Client) and existing_player.player_id != client.player_id:
                 # Sollte durch find_slot_for_human verhindert werden, aber sicher ist sicher
                 logger.info(f"WARNUNG: Slot {slot_index} wird von anderem Client {existing_player.player_name} belegt.")
                 # await existing_player.close_connection() # Alten Client rauswerfen? Oder Fehler?
                 return # Vorerst nicht hinzufügen

            self.players[slot_index] = client
            self._clients[client.player_id] = client # Für Reconnect speichern
            client.player_index = slot_index

            # Zustand aktualisieren und senden
            await self._send_private_state(client)
            await self._broadcast_public_state()

            # Prüfen, ob das Spiel starten kann (z.B. wenn 4 Spieler da sind)
            await self._check_start_game()
        else:
            logger.error(f"Error: Invalid slot index {slot_index} for table {self.table_name}")

    async def handle_player_message(self, client: Client, message: dict):
        """Verarbeitet eine Nachricht (Aktion) von einem verbundenen Client."""
        if not client.is_connected:
            logger.warning(f"Ignoring message from disconnected client {client.player_name}")
            return

        action_type = message.get("action")
        payload = message.get("payload", {})
        logger.info(f"Table {self.table_name}: Received action '{action_type}' from {client.player_name}")

        # --- HIER DIE SPIELLOGIK IMPLEMENTIEREN ---
        # z.B. prüfen, ob der Spieler am Zug ist, ob die Aktion gültig ist etc.
        # Beispiel: Tichu ansagen
        if action_type == "announce_tichu":
            # ... Logik zum Tichu ansagen ...
            logger.info(f"{client.player_name} announced Tichu (type: {payload.get('type')})")
            # Zustand aktualisieren und senden
            # self.public_state.xyz = ...
            await self._broadcast_public_state()

        # Beispiel: Karten spielen
        elif action_type == "play_cards":
            cards = payload.get("cards")
            # ... Logik zum Karten spielen (Validierung!) ...
            logger.info(f"{client.player_name} played cards: {cards}")
            # self.public_state.last_played_combination = ...
            # self.private_states[client.player_index].hand_cards = ...
            await self._send_private_state(client) # Eigene Hand aktualisieren
            await self._broadcast_public_state() # Alle über gespielte Karten informieren

        # Beispiel: Passen
        elif action_type == "pass_turn":
            # ... Logik zum Passen ...
            logger.info(f"{client.player_name} passed.")
            # self.public_state.current_turn_index = ...
            await self._broadcast_public_state()

        else:
            logger.warning(f"Unknown action type: {action_type}")
            await client.notify("error", {"message": f"Unknown action: {action_type}"})

        # --- SPIELENDE PRÜFEN ---
        # if game_is_over:
        #    await self._handle_game_end()

    async def notify_player_disconnected(self, client: Client):
        """Wird vom Client aufgerufen, wenn die Verbindung abbricht."""
        logger.info(f"Table {self.table_name}: Player {client.player_name} disconnected.")
        # Informiere andere Spieler (optional)
        await self._broadcast_public_state() # Aktualisiert Spielerliste/Status
        # Der KI-Takeover-Timer wird im Client selbst gestartet

    async def replace_player_with_agent(self, player_id: str) -> bool:
        """
        Ersetzt einen Client durch eine KI. Wird von der GameFactory aufgerufen.
        Gibt True zurück, wenn die Ersetzung erfolgreich war, sonst False.
        """
        if player_id not in self._clients:
            logger.warning(f"Tisch '{self.table_name}': Ersetzung fehlgeschlagen - Player ID {player_id} nicht gefunden (vielleicht reconnected?).")
            return False

        disconnected_client = self._clients[player_id]
        slot_index = disconnected_client.player_index

        # Prüfen: Ist der Spieler wirklich noch disconnected? Und am richtigen Platz?
        if slot_index is not None and 0 <= slot_index < self.MAX_PLAYERS and \
           self.players[slot_index] == disconnected_client and \
           not disconnected_client.is_connected:

            logger.info(f"Tisch '{self.table_name}': Ersetze disconnected {disconnected_client.player_name} (ID: {player_id}) an Slot {slot_index} durch Agent (von Factory ausgelöst).")

            del self._clients[player_id] # Aus Client-Tracking entfernen

            agent = Agent(player_name=f"{disconnected_client.player_name} (AI)", ai_level=1)
            agent.player_index = slot_index
            self.players[slot_index] = agent

            # TODO: State Transfer implementieren!
            logger.warning(f"Tisch '{self.table_name}': Zustandsübertragung an Agent {agent.player_name} fehlt!")

            await self._broadcast_public_state() # Zustand mit neuem Agenten senden
            return True # Erfolg signalisieren
        else:
            logger.warning(f"Tisch '{self.table_name}': Ersetzung für Player ID {player_id} abgebrochen. Bedingungen nicht erfüllt (reconnected, anderer Slot, inkonsistenter Zustand?).")
            return False # Misserfolg signalisieren

    def is_empty_of_humans(self) -> bool:
        """Prüft, ob nur noch KIs (oder leere Slots) am Tisch sind."""
        # Wichtig: Prüft auf Client-Instanzen, auch wenn sie disconnected sind!
        # Ein Tisch mit einem disconnected Client ist nicht leer!
        for player in self.players:
            if isinstance(player, Client):
                return False
        logger.debug(f"Table {self.table_name} is empty of humans.")
        return True

    async def _check_start_game(self):
       """Prüft, ob alle Plätze belegt sind und startet ggf. den Game-Loop."""
       if all(p is not None for p in self.players):
           if self.game_loop_task is None or self.game_loop_task.done():
               logger.info(f"Table {self.table_name}: All players ready. Starting game loop.")
               # self.game_loop_task = asyncio.create_task(self._run_game()) # Startet die Spiellogik
               # Hier muss die Logik für den eigentlichen Spielablauf hin
               await self._broadcast_public_state() # Sicherstellen, dass alle den finalen Zustand haben
           else:
               logger.info(f"Table {self.table_name}: All players present, but game loop already running.")
       else:
           logger.info(f"Table {self.table_name}: Waiting for more players.")

    async def cleanup(self):
        """Bereinigt Ressourcen der GameEngine (Tasks, Client-Verbindungen)."""
        logger.info(f"Räume GameEngine für Tisch auf: '{self.table_name}'")

        # 1. Game loop task abbrechen
        if self.game_loop_task and not self.game_loop_task.done():
            self.game_loop_task.cancel()
            try:
                await self.game_loop_task
            except asyncio.CancelledError:
                pass  # Erwartet
        self.game_loop_task = None

        # 2. Client-Verbindungen schließen
        tasks = []
        for player in self.players:
            if isinstance(player, Client) and player.is_connected:
                 tasks.append(asyncio.create_task(player.close_connection()))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # 3. Interne Zustände leeren (optional)
        self.players = [None] * self.MAX_PLAYERS
        self._clients.clear()
        logger.info(f"GameEngine Cleanup beendet für Tisch: '{self.table_name}'")

    # --- Platzhalter für die eigentliche Spiellogik ---
    # async def _run_game(self):
    #    try:
    #        logger.info(f"[{self.table_name}] Game loop started.")
    #        # ... Kartenausgabe ...
    #        # ... Schupfen ...
    #        # ... Tichu ansagen ...
    #        # ... Runden-Loop (Stiche spielen) ...
    #           # Spieler am Zug ermitteln
    #           # Wenn Client: auf Aktion warten (kommt über handle_player_message)
    #           # Wenn Agent: agent.get_action() aufrufen
    #           # Aktion validieren & ausführen
    #           # Zustand aktualisieren & senden
    #           # Runden-/Spielende prüfen
    #        # ... Spielende, Punkte zählen ...
    #        await self._handle_game_end()
    #    except asyncio.CancelledError:
    #        logger.exception(f"[{self.table_name}] Game loop cancelled.")
    #    except Exception as e:
    #        logger.exception(f"[{self.table_name}] Error in game loop: {e}")
    #        # Ggf. Fehler an Clients senden
    #    finally:
    #        logger.info(f"[{self.table_name}] Game loop finished.")
