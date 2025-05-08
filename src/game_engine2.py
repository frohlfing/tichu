"""
Definiert die Spiellogik.
"""

import asyncio
from aiohttp import WSCloseCode
from src.common.errors import PlayerTimeoutError, ClientDisconnectedError, PlayerResponseError
from src.common.logger import logger
from src.common.rand import Random
from src.lib.cards import Card, deck
from src.players.agent import Agent
from src.players.client import Client
from src.players.player import Player
from src.players.random_agent import RandomAgent
from src.private_state2 import PrivateState
from src.public_state2 import PublicState
from typing import List, Dict, Optional, Tuple

# todo alles überarbeiten

class GameEngine:
    """
    Steuert den Spielablauf eines Tisches.

    :ivar game_loop_task: Der asyncio Task, der die Hauptspielschleife ausführt.
    :ivar interrupt_events: Dictionary für globale Interrupts.
    """

    def __init__(self, table_name: str, default_agents: Optional[List[Agent]] = None, seed: Optional[int] = None):
        """
        Initialisiert eine neue GameEngine für einen gegebenen Tischnamen.

        :param table_name: Der Name des Spieltisches (eindeutiger Identifikator).
        :param default_agents: Optional: Liste mit 4 Agenten als Standard/Fallback.
        :param seed: (Optional) Seed für den internen Zufallsgenerator (für Tests).
        :raises ValueError: Wenn Parameter nicht ok sind.
        """
        # Name dieses Spieltisches
        name_stripped = table_name.strip() if table_name else ""
        if not name_stripped:
            raise ValueError("Name des Spieltisches darf nicht leer sein.")
        self._table_name: str = name_stripped

        # Default-Agenten initialisieren
        if default_agents:
            if len(default_agents) != 4 or any(not isinstance(player, Agent) for player in default_agents):
                raise ValueError(f"`default_agents` muss genau 4 Agenten auflisten.")
            self._default_agents: List[Agent] = list(default_agents)  # Kopie erstellen (immutable machen)
        else:
            self._default_agents: List[Agent] = [RandomAgent(name=f"RandomAgent_{i + 1}") for i in range(4)]

        # Sitzplätze der Reihe nach vergeben (0 bis 3)
        for i, default_agent in enumerate(self._default_agents):
            default_agent.player_index = i

        agent_names = ", ".join(default_agent.name for default_agent in self._default_agents)
        logger.debug(f"[{self.table_name}] Agenten initialisiert: {agent_names}.")

        # aktuelle Spielerliste
        self._players: List[Player] = list(self._default_agents)

        # öffentlicher Spielzustand, sichtbar für alle Spieler am Tisch
        self._public_state: PublicState = PublicState(
            table_name = self.table_name,
            player_names = [p.name for p in self._players],
        )

        # Liste der privaten Spielzustände, einer für jede Spielerposition (Index 0-3)
        self._private_states: List[PrivateState] = [PrivateState(player_index=i) for i in range(4)]

        # Referenz auf den Hintergrund-Task `_run_game_loop`
        self.game_loop_task: Optional[asyncio.Task] = None
        self._player_action_futures: Dict[int, asyncio.Future] = {} # Intern für Client-Warten

        # Flag für laufenden Interrupt
        self._interrupt_in_progress: bool = False
        self._interrupting_player_index: Optional[int] = None

        # Interrupt-Events
        self.interrupt_events: Dict[str, asyncio.Event] = {
            "tichu_announced": asyncio.Event(),
            "bomb_played": asyncio.Event(),
            "game_abort_request": asyncio.Event(), # Beispiel
        }

        # Zufallsgenerator, geeignet für Multiprocessing
        self._random = Random(seed)

        # Kopie des sortiertem Standarddecks - wird jede Runde neu durchgemischt
        self._mixed_deck = list(deck)

        logger.info(f"GameEngine für Tisch '{table_name}' erstellt.")

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
        self._players = [None] * 4
        self._private_states.clear() # Liste leeren

        logger.info(f"GameEngine Cleanup für Tisch '{self._table_name}' beendet.")

    # ------------------------------------------------------
    # Partie spielen
    # ------------------------------------------------------

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
           logger.info(f"Tisch '{self._table_name}': Warte auf {4 - player_count} weitere Spieler.")

    async def start_game(self):
        """
        Startet den Hintergrund-Task `_run_game_loop`
        """
        if self.game_loop_task and not self.game_loop_task.done():
            logger.warning(f"Tisch '{self.table_name}': Versuch, neue Partie zu starten, obwohl bereits eine läuft.")
            return

        logger.info(f"[{self.table_name}] Starte Hintergrund-Task für eine neue Partie.")
        self.game_loop_task = asyncio.create_task(self.run_game_loop(), name=f"Game Loop '{self.table_name}'")

    async def run_game_loop(self, pub: Optional[PublicState] = None, privs: Optional[List[PrivateState]] = None, break_time = 5) -> PublicState|None:
        """
        Steuert den Spielablauf einer Partie.

        :param pub: (Optional) Öffentlicher Spielzustand. Änderungen extern möglich, aber nicht vorgesehen.
        :param privs: (Optional) Private Spielzustände (müssen 4 sein). Änderungen extern möglich, aber nicht vorgesehen.
        :param break_time: Pause in Sekunden zwischen den Runden.
        :return: Der öffentliche Spielzustand.
        :raises ValueError: Wenn Parameter nicht ok sind.
        """
        try:
            logger.info(f"[{self.table_name}] Starte neue Partie...")

            # --- PublicState initialisieren ---
            self._public_state = PublicState(
                table_name=self.table_name,
                player_names=[p.name for p in self._players],
                current_phase="playing"
            )
            if pub:
                logger.debug(f"[{self.table_name}] Verwende übergebenen PublicState.")
                self._public_state = pub

            # --- PrivateState initialisieren ---
            self._private_states = [PrivateState(player_index=i) for i in range(4)]
            if privs:
                logger.debug(f"[{self.table_name}] Verwende übergebene PrivateStates.")
                if len(privs) != 4:
                    raise ValueError(f"Die Anzahl der Einträge in `privs` muss genau 4 sein.")
                # Sitzplätze der Reihe nach vergeben (0 bis 3)
                for i, priv in enumerate(privs):
                    priv.player_index = i
                self._private_states = privs

            # --- Partie-Schleife (analog zu alten game_engine_.play_episode) ---
            # Zugriff auf public_state über self._public_state
            while not self.is_game_over:
                # Neue Runde...

                # öffentlichen Spielzustand zurücksetzen
                pub.reset_round()

                # privaten Spielzustand zurücksetzen
                for priv in privs:
                    priv.reset_round()

                # Agents zurücksetzen
                for agent in self._agents:
                    agent.reset_round()

                # Karten mischen
                pub.shuffle_cards()

                # Karten aufnehmen, erst 8 dann alle
                first = self._random.integer(0, 4)  # wählt zufällig eine Zahl zwischen 0 und 3
                for n in (8, 14):
                    # Karten verteilen
                    for player in range(0, 4):
                        cards = pub.deal_out(player, n)
                        privs[player].take_cards(cards)
                        pub.set_number_of_cards(player, n)
                    self.broadcast("")

                    # Tichu ansagen?
                    for i in range(0, 4):
                        player = (first + i) % 4  # mit irgendeinem Spieler zufällig beginnen
                        grand = n == 8  # großes Tichu?
                        if not pub.announcements[player] and self._agents[player].announce(pub, privs[player], grand):
                            pub.announce(player, grand)
                            self.broadcast("")

                # jetzt müssen die Spieler schupfen
                schupfed = [None, None, None, None]
                for player in range(0, 4):
                    schupfed[player] = privs[player].schupf(self._agents[player].schupf(pub, privs[player]))
                    assert privs[player].number_of_cards == 11
                    pub.set_number_of_cards(player, 11)
                self.broadcast("")

                # die abgegebenen Karten der Mitspieler aufnehmen
                for player in range(0, 4):
                    privs[player].take_schupfed_cards([schupfed[giver][player] for giver in range(0, 4)])
                    assert privs[player].number_of_cards == 14
                    pub.set_number_of_cards(player, 14)
                    if privs[player].has_mahjong:
                        pub.set_start_player(player)  # Startspieler bekannt geben
                self.broadcast("")

                # los geht's - das eigentliche Spiel kann beginnen...
                assert 0 <= pub.current_player_index <= 3
                while not pub.is_done:
                    priv = privs[pub.current_player_index]
                    agent = self._agents[pub.current_player_index]
                    assert pub.number_of_cards[priv.player_index] == priv.number_of_cards
                    assert 0 <= pub.number_of_cards[priv.player_index] <= 14
                    self.broadcast("")

                    # falls alle gepasst haben, schaut der Spieler auf seinen eigenen Stich und kann diesen abräumen
                    if pub.trick_player_index == priv.player_index and pub.trick_figure != FIGURE_DOG:  # der Hund bleibt aber immer liegen
                        if not pub.double_win and pub.trick_figure == FIGURE_DRA:  # Drache kassiert? Muss verschenkt werden!
                            opponent = agent.gift(pub, priv)
                            assert opponent in ((1, 3) if priv.player_index in (0, 2) else (0, 2))
                        else:
                            opponent = -1
                        pub.clear_trick(opponent)
                        self.broadcast("")

                    # hat der Spieler noch Karten?
                    if pub.number_of_cards[priv.player_index] > 0:
                        # falls noch alle Karten auf der Hand sind und noch nichts angesagt wurde, darf Tichu angesagt werden
                        if pub.number_of_cards[priv.player_index] == 14 and not pub.announcements[priv.player_index]:
                            if agent.announce(pub, priv):
                                pub.announce(priv.player_index)
                                self.broadcast("")

                        # Kombination auswählen
                        action_space = build_action_space(priv.combinations, pub.trick_figure, pub.wish)
                        combi = agent.combination(pub, priv, action_space)
                        assert pub.number_of_cards[priv.player_index] == priv.number_of_cards
                        assert combi[1][1] <= pub.number_of_cards[priv.player_index] <= 14

                        # Kombination ausspielen
                        priv.play(combi)
                        assert priv.number_of_cards == pub.number_of_cards[priv.player_index] - combi[1][1]
                        pub.play(combi)
                        assert pub.number_of_cards[priv.player_index] == priv.number_of_cards
                        self.broadcast("")

                        if combi[1] != FIGURE_PASS:
                            # Spiel vorbei?
                            if pub.is_done:
                                # Spiel ist vorbei; letzten Stich abräumen und fertig!
                                assert pub.trick_player_index == priv.player_index
                                if not pub.double_win and pub.trick_figure == FIGURE_DRA:  # Drache kassiert? Muss verschenkt werden!
                                    opponent = agent.gift(pub, priv)
                                    assert opponent in ((1, 3) if priv.player_index in (0, 2) else (0, 2))
                                else:
                                    opponent = -1
                                pub.clear_trick(opponent)
                                self.broadcast("")
                                break

                            # falls ein MahJong ausgespielt wurde, muss ein Wunsch geäußert werden
                            if CARD_MAH in combi[0]:
                                assert pub.wish == 0
                                wish = agent.wish(pub, priv)
                                assert 2 <= wish <= 14
                                pub.set_wish(wish)
                                self.broadcast("")

                    # nächster Spieler ist an der Reihe
                    pub.step()

            logger.info(f"[{self.table_name}] Partie beendet. Endstand: Team 20: {self.total_score(0)}, Team 31: {self.total_score(1)}")
            #await self._broadcast_public_state()

            # Episode abgeschlossen
            return pub

        except asyncio.CancelledError:
            logger.info(f"[{self.table_name}] Spiel-Loop extern abgebrochen.")
            self._public_state.current_phase = "aborted"
            # noinspection PyBroadException
            try:
                await self._broadcast_public_state()
            except Exception:
                pass
        except Exception as e:
            logger.exception(f"[{self.table_name}] Kritischer Fehler im Spiel-Loop: {e}")
            self._public_state.current_phase = "error"
            # noinspection PyBroadException
            try:
                await self._broadcast_public_state()
            except Exception:
                pass
        finally:
            logger.info(f"[{self.table_name}] Spiel-Loop definitiv beendet.")
            self.game_loop_task = None  # Referenz aufheben

        return self._public_state

    # ------------------------------------------------------
    # Nachricht an Spieler senden
    # ------------------------------------------------------

    def broadcast(self, data) -> None:
        for player in self._players:
            player.notify("broadcast", data)

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

        state_dict = private_state.to_dict()
        logger.debug(f"Tisch '{self._table_name}': Sende Private State Update an {player.player_name}: {state_dict}")
        await player.notify("private_state_update", state_dict)

    async def _broadcast_public_state(self):
        """
        Aktualisiert den öffentlichen Spielzustand und sendet ihn an alle verbundenen Clients.F
        """
        #TODO: die Methode macht zwei Dinge Spiels:
        # a) Spielzustand aktualisieren und b) Spielzustand per notify senden
        # wir sollten daher daraus 2 Funktionen machen!
        # a sollte Exception werfen, wenn irgendwas schief geht, da es wichtig ist, dass das klappt
        # b sollte wie notify kein Exception werfen, wenn etwas schiefgeht.

        # Sicherstellen, dass die Spielerliste im State aktuell ist.
        self._public_state.player_names = [p.name for p in self._players]
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

    # ------------------------------------------------------
    # Nachricht vom Spieler verarbeiten
    # ------------------------------------------------------

    # todo client-spezifische hat in der Engein nichts zu suchen
    async def handle_player_message(self, client: Client, message: dict):
        """
        Verarbeitet eine eingehende Nachricht (Spielaktion) von einem Client.

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
                    if player_count == 4:
                        # Starte das Spiel (startet run_game_loop als Task)
                        await self.start_game()
                        # Sende Bestätigung oder warte auf erstes State Update?
                        # start_game sendet selbst keine Bestätigung.
                        # Der erste Broadcast aus run_game_loop signalisiert den Start.
                    else:
                        logger.warning(f"Spielstart auf Tisch '{self._table_name}' durch Host fehlgeschlagen: Nur {player_count}/{4} Spieler.")
                        await client.notify("error", {"message": f"Es müssen genau {4} Spieler am Tisch sein, um zu starten."})
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
                await client.notify("error", {"message": f"Aktion '{action}' ist in der aktuellen Phase '{self._public_state.current_phase}' nicht erlaubt."})
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

    # ------------------------------------------------------
    # Interrupt vom Spieler verarbeiten
    # ------------------------------------------------------

    # todo client-spezifische hat in der Engein nichts zu suchen
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
        if self._public_state.current_phase != "playing":
            # Ausnahme für Tichu erlauben?
            if interrupt_type == "tichu" and self._public_state.current_phase == "announcing_small_tichu":
                pass  # Erlaubt
            else:
                logger.warning(f"Tisch '{self.table_name}': Interrupt '{interrupt_type}' von Spieler {player_index} in Phase '{self._public_state.current_phase}' nicht erlaubt.")
                await client.notify("error", {"message": f"Aktion '{interrupt_type}' in Phase '{self._public_state.current_phase}' nicht erlaubt."})
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
                #priv_state = self._private_states[player_index]
                # 1. Validieren: Hat Spieler eine Bombe? Ist Bomben erlaubt?
                # TODO: Implementiere Regel-Funktion 'player_has_bomb(priv_state.hand_cards)'
                # TODO: Implementiere Regel-Funktion 'can_bomb_now(self._public_state)'
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
                    bomb_action_tuple = ()  # await client.bomb(self._public_state, priv_state, bomb_action_space)  #todo client.bomb implementieren

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

    # todo client-spezifische hat in der Engein nichts zu suchen
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

        priv_state = self._private_states[player_index]
        is_grand_attempt = self._public_state.current_phase == "announcing_grand_tichu"
        # is_small_attempt = self._public_state.current_phase in ["announcing_small_tichu", "playing"]  # Oder genauer?

        logger.info(f"Tisch '{self.table_name}': Verarbeite Tichu-Anfrage von Spieler {player_index} (Grand: {is_grand_attempt}).")

        # --- Validierung ---
        # 1. Bereits angesagt?
        if self._public_state.announcements[player_index] > 0:
            logger.warning(f"Spieler {player_index} hat bereits Tichu angesagt.")
            await client.notify("error", {"message": "Du hast bereits Tichu angesagt."})
            return False

        # 2. Richtige Phase?
        # Annahme: can_player_announce_tichu prüft Phase, Kartenanzahl etc.
        # Die Funktion muss wissen, ob es um Grand oder Small geht.
        can_announce = True  # can_player_announce_tichu(self._public_state, priv_state, grand=is_grand_attempt)  # todo can_player_announce_tichu implementieren
        if not can_announce:
            msg = "Grand Tichu kann nur nach den ersten 8 Karten angesagt werden." if is_grand_attempt else "Tichu kann nur vor deinem ersten ausgespielten Zug angesagt werden."
            logger.warning(f"Ungültiger Tichu-Versuch von Spieler {player_index}: {msg}")
            await client.notify("error", {"message": msg})
            return False

        # --- Wenn gültig: Zustand aktualisieren ---
        tichu_type = 2 if is_grand_attempt else 1
        self._public_state.announcements[player_index] = tichu_type

        type_str = "Grand Tichu" if is_grand_attempt else "Tichu"
        logger.info(f"Tisch '{self.table_name}': {type_str}-Ansage von Spieler {player_index} akzeptiert.")

        # Sende KEINEN Broadcast hier. Das macht der Aufrufer (handle_player_message),
        # nachdem das Interrupt-Event ggf. gesetzt wurde.
        return True  # Erfolg

    # ------------------------------------------------------
    # Datenaufbereitung
    # ------------------------------------------------------

    def total_score(self, team_index: int) -> int:
        """
        Berechnet den Gesamtpunktestand der Partie für das angegebene Team.
        :param team_index: 0 == Team 20 oder 1 == Team 31
        :return: Gesamtpunktestand
        """
        return sum(self._public_state.game_score[team_index])

    # ------------------------------------------------------
    # Hilfsfunktionen
    # ------------------------------------------------------

    # todo client-spezifische hat in der Engein nichts zu suchen
    def _get_client_by_id(self, uuid: str) -> Optional[Client]:
        """Gibt den Client anhand der UUID zurück."""
        for p in self._players:
            if p.uuid == uuid and isinstance(p, Client):
                return p
        return None

    def _shuffle_deck(self):
        """
        Mischt das Kartendeck.
        """
        self._random.shuffle(self._mixed_deck)

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
    def is_game_over(self) -> bool:
        """Gibt an, ob die Partie beendet ist."""
        return self.total_score(0) >= 1000 or self.total_score(1) >= 1000

    @property
    def number_of_players(self) -> int:  # todo anderen Bezeichner finden
        """Anzahl Spieler, die noch im Rennen sind."""
        return sum(1 for n in self._public_state.num_hand_cards if n > 0)

    @property
    def public_state(self) -> PublicState:
        """Öffentlicher Spielzustand. Änderungen extern möglich, aber nicht vorgesehen."""
        return self._public_state

    @property
    def private_states(self) -> List[PrivateState]:
        """Private Spielzustände. Änderungen extern möglich, aber nicht vorgesehen."""
        return self._private_states
