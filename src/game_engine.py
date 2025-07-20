"""
Definiert die Spiellogik.
"""

import asyncio
from aiohttp.web_ws import WebSocketResponse
from copy import copy
from src import config
from src.common.logger import logger
from src.common.rand import Random
from src.lib.cards import deck, is_wish_in, sum_card_points, other_cards, CARD_DRA, CARD_MAH, Cards, stringify_cards
from src.lib.combinations import CombinationType, Combination
from src.lib.errors import ErrorCode, PlayerInterruptError
from src.players.agent import Agent
from src.players.peer import Peer
from src.players.player import Player
from src.players.random_agent import RandomAgent
from src.private_state import PrivateState
from src.public_state import PublicState
from time import time
from typing import List, Optional, Dict, Tuple


class GameEngine:
    """
    Steuert den Spielablauf eines Tisches.
    """

    def __init__(self, table_name: str, default_agents: Optional[List[Agent]] = None, seed: Optional[int] = None):
        """
        Initialisiert eine neue GameEngine für einen gegebenen Tischnamen.

        :param table_name: Der Name des Spieltisches (eindeutiger Identifikator).
        :param default_agents: (Optional) Liste mit 4 Agenten als Standard/Fallback. Wenn None, werden RandomAgent-Instanzen verwendet.
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
            if len(default_agents) != 4 or any(not isinstance(agent, Agent) for agent in default_agents):
                raise ValueError(f"`default_agents` muss genau 4 Agenten auflisten.")
            self._default_agents: List[Agent] = list(default_agents)  # Kopie erstellen (immutable machen)
        else:
            self._default_agents: List[Agent] = [RandomAgent(name=f"RandomAgent_{i + 1}") for i in range(4)]

        # aktuelle Spielerliste
        self._players: List[Player] = list(self._default_agents)  # die Liste ist eine Kopie, die Einträge nicht!

        # aktueller Spielzustand
        self._public_state = PublicState(
            table_name = self._table_name,
            player_names = [p.name for p in self._players],
        )
        self._private_states = [PrivateState(player_index=i) for i in range(4)]

        # Referenz zum Hintergrund-Task `_run_game_loop`
        self._game_loop_task: Optional[asyncio.Task] = None

        # Interrupt-Event
        self._interrupt_event: asyncio.Event = asyncio.Event()
        self._interrupt_player_index: Optional[int] = None
        self._interrupt_reason: Optional[str] = None

        # Zufallsgenerator, geeignet für Multiprocessing
        self._random = Random(seed)

        # Kopie des sortierten Standarddecks
        self._mixed_deck = list(deck)
        self._random.shuffle(self._mixed_deck)  # es wird jede Runde neu gemischt, aber initial einmal mehr schadet nicht

        # jedem Spieler eine Referenz auf den Spielzustand und auf das Interrupt-Event geben
        # (Mutable - Änderungen sind durch Player möglich, aber nicht vorgesehen)
        for i, agent in enumerate(self._default_agents):
            agent.pub = self._public_state
            agent.priv = self._private_states[i]
            agent.interrupt_event = self._interrupt_event

        logger.info(f"[{self.table_name}] Initialisiert.")

    async def cleanup(self):
        """
        Bereinigt Ressourcen dieser Instanz.

        Bricht laufende Tasks ab und ruft dann die `cleanup`-Funktion aller Player-Instanzen auf.
        """
        logger.info(f"[{self.table_name}] Räume Tisch auf...")

        # bricht den Hintergrundtask für die Spielsteuerung ab, falls er läuft
        if self._game_loop_task and not self._game_loop_task.done():
            logger.debug(f"[{self.table_name}] Beende Hintergrundtask für die Spielsteuerung.")
            self._game_loop_task.cancel()
            try:
                # Warte kurz darauf, dass der Task auf den Abbruch reagiert.
                await asyncio.wait_for(self._game_loop_task, timeout=1.0)
            except asyncio.CancelledError:
                logger.debug(f"[{self.table_name}] Abbruch. Hintergrundtask unsauber beendet.")
            except asyncio.TimeoutError:
                logger.warning(f"[{self.table_name}] Timeout. Hintergrundtask unsauber beendet.")
            except Exception as e:
                 logger.exception(f"[{self.table_name}] Unerwarteter Fehler. Hintergrundtask unsauber beendet.: {e}")
        self._game_loop_task = None # Referenz entfernen

        # alle Spieler-Instanzen bereinigen (parallel)
        await asyncio.gather(*[asyncio.create_task(p.cleanup()) for p in self._players], return_exceptions=True)

        logger.info(f"[{self.table_name}] Tisch aufgeräumt.")

    # ------------------------------------------------------
    # Client anmelden / abmelden
    # ------------------------------------------------------

    def get_peer_by_session(self, session: str) -> Optional[Peer]:
        """
        Gibt den Peer anhand der Session zurück.

        :param session: Die Session des Spielers.
        :return: Der Peer, falls die Session existiert, sonst None.
        """
        for player in self._players:
            if player.session_id == session:
                return player if isinstance(player, Peer) else None
        return None

    async def join_client(self, peer: Peer) -> bool:
        """
        Lässt den Client mitspielen.

        :param peer: Der Client, der mitspielen möchte.
        :return: True, wenn der Client einen Sitzplatz bekommen hat, ansonsten False.
        """
        # Sitzplatz suchen, der von einem Agenten (KI) besetzt ist
        available_index = -1
        for i, player in enumerate(self._players):
            if not isinstance(player, Peer):
                available_index = i
                break
        if available_index == -1:
            return False

        # Sitzplatz dem Client zuordnen
        self._players[available_index] = peer
        if self._public_state.host_index == -1:
            self._public_state.host_index = available_index
        self._public_state.player_names[available_index] = peer.name
        peer.pub = self._public_state  # Mutable - Änderungen durch Player möglich, aber nicht vorgesehen
        peer.priv = self._private_states[available_index]  # Mutable - Änderungen durch PLayer möglich, aber nicht vorgesehen
        peer.interrupt_event = self._interrupt_event

        await self._broadcast("player_joined", {"player_index": available_index, "player_name": peer.name})
        return True

    async def rejoin_client(self, peer: Peer, websocket: WebSocketResponse) -> bool:
        """
        Lässt den Client weiterspielen.

        :param peer: Der Client, der weiterspielen möchte.
        :param websocket: Das neue WebSocketResponse-Objekt.
        :return: True, wenn der Client am Tisch gefunden wurde, ansonsten False.
        """
        # Sitzplatz suchen, an dem der Client (leblos) sitzt.
        index = peer.priv.player_index
        if self._players[index].session_id != peer.session_id or not isinstance(peer, Peer) or peer.is_connected:
            return False

        # neue WebSocket-Verbindung übernehmen
        peer.set_websocket(websocket)

        assert self._players[index] == peer
        assert self._public_state.player_names[index] == peer.name
        assert peer.pub == self._public_state
        assert peer.priv == self._private_states[index]
        assert peer.interrupt_event == self._interrupt_event

        await self._broadcast("player_joined", {"player_index": index, "player_name": peer.name})
        return True

    async def leave_client(self, peer: Peer) -> bool:
        """
        Lässt den Client gehen.

        :param peer: Der Client, der gehen will.
        :return: True, wenn der Client am Tisch gefunden wurde, ansonsten False.
        """
        index = peer.priv.player_index
        if self._players[index].session_id != peer.session_id:
            raise False

        # Default-Agent als Fallback nehmen
        self._players[index] = self._default_agents[index]
        self._public_state.player_names[index] = self._default_agents[index].name

        # Peer-interne Resourcen bereinigen
        await peer.cleanup()

        # wenn der Client der Host des Tisches ist, nächsten Spieler als Host ernennen
        if self._public_state.host_index == index:
            self._public_state.host_index = -1
            for p in self._players:
                if isinstance(p, Peer):
                    self._public_state.host_index = p.priv.player_index
                    break

        await self._broadcast("player_left", {"player_index": index, "player_name": self._players[index].name, "host_index": self._public_state.host_index})
        return True

    # ------------------------------------------------------
    # Lobby-Aktionen
    # ------------------------------------------------------

    # noinspection PyMethodMayBeStatic
    async def swap_players(self, index1: int, index2: int) -> bool:
        """
        Vertauscht die Position zweier Spieler.

        Der Host darf nicht verschoben werden. Das Vertauschen ist nur vor Spielstart möglich.

        :param index1: Index des ersten Spielers
        :param index2: Index des zweiten Spielers
        :return: True, wenn die Zuordnung erfolgte, sonst False.
        """
        # Parameter ok?
        if not isinstance(index1, int) or not isinstance(index2, int) or index1 < 0 or index1 > 3 or index2 < 0 or index2 > 3:
            logger.warning(f"[{self.table_name}] Ungültige Parameter für 'swap_players': {index1}, {index2}")
            return False

        if self._public_state.host_index in [index1, index2]:
            logger.warning(f"[{self.table_name}] Der Host darf nicht verschoben werden.")
            return False

        if self._public_state.is_running:
            logger.warning(f"[{self.table_name}] Vertauschen der Spieler nicht möglich. Die Partie läuft bereits.")
            return False

        self._players[index1], self._players[index2] = copy(self._players[index2]), copy(self._players[index1])
        self._players[index1].priv = self._private_states[index1]
        self._players[index2].priv = self._private_states[index2]
        # Da der Spielzustand bei Spielstart zurückgesetzt wird, müssen die Felder pub.count_hand_cards, pub.announcements und pub.points nicht gedreht werden.
        # Es muss nur pub.player_names aktualisiert werden, denn die Spielernamen bleiben beim Reset unberührt.
        self._public_state.player_names[index1] = self._players[index1].name
        self._public_state.player_names[index2] = self._players[index2].name
        await self._broadcast("players_swapped", {"player_index_1": index1, "player_index_2": index2})
        return True

    async def start_game(self) -> bool:
        """
        Startet den Hintergrundtask für die Spielsteuerung einer Partie.

        :return: True, wenn eine neue Partie gestartet werden konnte, sonst False.
        """
        if self._game_loop_task and not self._game_loop_task.done():
            logger.warning(f"[{self.table_name}] Starten der Partie nicht möglich. Die Partie läuft bereits.")
            return False

        logger.debug(f"[{self.table_name}] Starte Hintergrundtask für die Spielsteuerung.")
        self._game_loop_task = asyncio.create_task(self.run_game_loop(), name=f"Game Loop '{self.table_name}'")
        return True

    # ------------------------------------------------------
    # Partie spielen
    # ------------------------------------------------------

    # noinspection PyUnusedLocal
    async def run_game_loop(self) -> Optional[PublicState]:
        """
        Steuert den Spielablauf einer Partie.

        :return: Der öffentliche Spielzustand.
        :raises ValueError: Wenn Parameter nicht ok sind.
        """
        # Referenz auf den Spielzustand holen
        pub = self._public_state
        privs = self._private_states
        assert pub.table_name == self.table_name
        assert pub.player_names == [p.name for p in self._players]
        assert len(privs) == 4
        assert all(priv.player_index == i for i, priv in enumerate(privs))
        assert not pub.is_running
        pub.is_running = True

        # aus Performance-Gründen für die Arena wollen wir so wenig wie möglich await aufrufen, daher ermitteln wir, ob überhaupt Clients im Spiel sind
        clients_joined = any(isinstance(player, Peer) for player in self._players)

        logger.info(f"[{self.table_name}] Starte neue Partie...")
        try:
            # Spielzustand vollständig zurücksetzen
            pub.reset_game()
            for priv in privs:
                priv.reset_game()
            if clients_joined:
                await self._broadcast("game_started")

            # Partie spielen
            while not pub.is_game_over:
                # Neue Runde...

                # Spielzustand für eine neue Runde zurücksetzen
                pub.reset_round()
                for priv in privs:
                    priv.reset_round()

                # Agents zurücksetzen
                for player in self._players:
                    player.reset_round()

                if clients_joined:
                    await self._broadcast("round_started")

                # Karten mischen
                self._random.shuffle(self._mixed_deck)
                # self._mixed_deck = [(card[0], CardSuit(card[1])) for card in [
                #     (2, 1), (2, 2), (2, 3), (2, 4), (1, 0), (15, 0), (3, 4), (6, 4), (3, 1), (14, 4), (8, 1), (7, 1), (7, 3), (3, 3),
                #     (10, 2), (11, 3), (6, 1), (11, 4), (9, 1), (13, 1), (3, 2), (6, 3), (9, 2), (12, 4), (12, 2), (4, 3), (5, 1), (4, 2),
                #     (0, 0), (13, 3), (5, 2), (9, 4), (5, 4), (10, 3), (8, 3), (10, 1), (14, 1), (9, 3), (7, 4), (8, 2), (13, 4), (10, 4),
                #     (12, 3), (4, 4), (11, 1), (5, 3), (6, 2), (12, 1), (13, 2), (4, 1), (7, 2), (14, 3), (14, 2), (11, 2), (8, 4), (16, 0),
                # ]]

                # Alle Spieler erhalten gleichzeitig die ersten 8 Karten. Sobald sie ein großes Tichu angesagt oder abgelehnt haben, erhalten sie die restlichen Karten und können Tauschkarten abgeben.
                await asyncio.gather(*[self._deal_out(player_index, clients_joined) for player_index in range(4)])

                for player_index in range(4):
                    logger.debug(f"[{self.table_name}] Handkarten Spieler {player_index}: {stringify_cards(privs[player_index].hand_cards)}")
                for player_index in range(4):
                    logger.debug(f"[{self.table_name}] Tauschkarten Spieler {player_index}: {stringify_cards(privs[player_index].given_schupf_cards)}")

                # Tauscharten aufnehmen
                # Karten-Index der abgegebenen Karte:
                # Ge-| Nehmer
                # ber| 0  1  2  3
                # ---|------------
                #   0| -  1  2  3
                #   1| 3  -  1  2
                #   2| 2  3  -  1
                #   3| 1  2  3  -
                for player_index in range(4):  # Nehmer
                    priv = privs[player_index]
                    priv.received_schupf_cards = (
                        privs[(player_index + 1) % 4].given_schupf_cards[2],
                        privs[(player_index + 2) % 4].given_schupf_cards[1],
                        privs[(player_index + 3) % 4].given_schupf_cards[0],
                    )
                    assert not set(priv.received_schupf_cards).intersection(priv.hand_cards)  # darf keine Schnittmenge bilden
                    priv.hand_cards += priv.received_schupf_cards
                    assert len(priv.hand_cards) == 14
                    pub.count_hand_cards[player_index] = 14

                # Startspieler bekannt geben
                for player_index in range(4):
                    if CARD_MAH in privs[player_index].hand_cards:
                        assert pub.start_player_index == -1
                        pub.start_player_index = player_index
                        pub.current_turn_index = player_index
                        break

                if clients_joined:
                    await self._broadcast("start_playing", {"start_player_index": pub.start_player_index})  # wird nur einmal gesendet!

                for player_index in range(4):
                    logger.debug(f"[{self.table_name}] Handkarten Spieler {player_index}: {stringify_cards(privs[player_index].hand_cards)}")
                check_deck = sorted(privs[0].hand_cards + privs[1].hand_cards + privs[2].hand_cards + privs[3].hand_cards)
                assert check_deck == list(deck), f"{stringify_cards(check_deck)} != {stringify_cards(deck)}"

                # Los geht's - das eigentliche Spiel kann beginnen.
                assert 0 <= pub.current_turn_index <= 3
                while not pub.is_round_over:
                    assert 0 <= pub.count_hand_cards[pub.current_turn_index] <= 14

                    # Wenn kein Anspiel, und falls der aktuelle Spieler den Stich kassieren darf oder aktiv an der Runde beteiligt ist (noch Handkarten hat),
                    # jeden Mitspieler fragen, ob er eine Bombe werfen will.
                    bomb: Optional[Tuple[Cards, Combination]] = None
                    if pub.trick_combination[2] > 0 and (pub.trick_owner_index == pub.current_turn_index or pub.count_hand_cards[pub.current_turn_index] > 0):
                        first = self._random.integer(0, 4)  # zufällige Zahl zwischen 0 und 3
                        for i in range(4):
                            player_index = (first + i) % 4  # mit irgendeinem Spieler zufällig beginnen
                            if player_index != pub.current_turn_index and self._private_states[player_index].has_bomb:
                                bomb = await self._players[player_index].play()
                                if bomb[1][0] == CombinationType.PASS:
                                    bomb = None
                                if bomb:
                                    pub.current_turn_index = player_index
                                    break

                    assert privs[pub.current_turn_index].player_index == pub.current_turn_index
                    assert len(privs[pub.current_turn_index].hand_cards) == pub.count_hand_cards[pub.current_turn_index]

                    # Falls alle gepasst haben, schaut der Spieler auf seinen eigenen Stich und kann diesen abräumen.
                    if not bomb and pub.trick_owner_index == pub.current_turn_index and pub.trick_combination != (CombinationType.SINGLE, 1, 0):  # der Hund bleibt liegen
                        await self._take_trick(clients_joined)

                    # Hat der Spieler noch Karten?
                    if pub.count_hand_cards[pub.current_turn_index] > 0:
                        if bomb:
                            # Der Spieler hat bereits die Bombe geworfen, wir müssen nicht nochmal nach einer Kombination fragen.
                            cards, combination = bomb
                        else:
                            # Falls noch alle Karten auf der Hand sind und noch nichts angesagt wurde, darf ein einfaches Tichu angesagt werden.
                            if pub.count_hand_cards[pub.current_turn_index] == 14 and not pub.announcements[pub.current_turn_index]:
                                if await self._players[pub.current_turn_index].announce():
                                    # Spieler hat Tichu angesagt
                                    pub.announcements[pub.current_turn_index] = 1
                                    if clients_joined:
                                        await self._broadcast("player_announced", {"player_index": pub.current_turn_index, "grand": False})
                            # Spieler fragen, welche Karten er spielen will.
                            time_start = time()
                            try:
                                cards, combination = await self._players[pub.current_turn_index].play(interruptable=True)
                            except PlayerInterruptError as e:
                                # Ein Client möchte eine Bombe werfen.
                                # Wir wiederholen den aktuellen Schleifendurchlauf, so dass nochmal danach gefragt wird, bevor es hier weitergeht.
                                continue  # while not pub.is_round_over
                            if clients_joined:
                                delay = round((time() - time_start) * 1000)  # in ms
                                if delay < config.AGENT_THINKING_TIME[0]:
                                    delay = self._random.integer(config.AGENT_THINKING_TIME[0] - delay, config.AGENT_THINKING_TIME[1] - delay)
                                    await asyncio.sleep(delay / 1000)

                        assert combination[1] <= pub.count_hand_cards[pub.current_turn_index] <= 14
                        assert combination[1] == len(cards)
                        if cards:
                            logger.debug(f"[{self.table_name}] Spieler {pub.current_turn_index} spielt {stringify_cards(cards)}")
                        else:
                            logger.debug(f"[{self.table_name}] Spieler {pub.current_turn_index} passt")

                        # Entscheidung des Spielers festhalten
                        assert pub.current_turn_index != -1
                        assert pub.current_turn_index == self._players[pub.current_turn_index].priv.player_index
                        assert pub.current_turn_index == privs[pub.current_turn_index].player_index
                        if pub.trick_owner_index == -1:  # neuer Stich?
                            assert combination[0] != CombinationType.PASS  # beim Anspiel darf nicht gepasst werden, der erste Eintrag im Stich sind also Karten
                            pub.tricks.append([(pub.current_turn_index, cards, combination)])
                        else:
                            assert len(pub.tricks) > 0
                            pub.tricks[-1].append((pub.current_turn_index, cards, combination))

                        # Kombination ausspielen, falls nicht gepasst wurde
                        if combination[0] != CombinationType.PASS:
                            # Handkarten aktualisieren
                            assert pub.count_hand_cards[pub.current_turn_index] == len(privs[pub.current_turn_index].hand_cards)
                            privs[pub.current_turn_index].hand_cards = [card for card in privs[pub.current_turn_index].hand_cards if card not in cards]
                            assert pub.count_hand_cards[pub.current_turn_index] >= combination[1]
                            pub.count_hand_cards[pub.current_turn_index] -= combination[1]
                            assert pub.count_hand_cards[pub.current_turn_index] == len(privs[pub.current_turn_index].hand_cards)

                            # Stich aktualisieren
                            pub.trick_owner_index = pub.current_turn_index
                            pub.trick_cards = cards
                            if combination == (CombinationType.SINGLE, 1, 16):
                                assert pub.trick_combination[0] == CombinationType.PASS or pub.trick_combination[0] == CombinationType.SINGLE
                                assert pub.trick_combination != (CombinationType.SINGLE, 1, 15)  # Phönix auf Drachen geht nicht
                                # Der Phönix ist eigentlich um 0.5 größer als der Stich, aber gleichsetzen geht auch (Anspiel == 1).
                                if pub.trick_combination[2] == 0:  # Anspiel oder Hund?
                                    pub.trick_combination = (CombinationType.SINGLE, 1, 1)
                            else:
                                pub.trick_combination = combination
                            pub.trick_points += sum_card_points(cards)
                            assert -25 <= pub.trick_points <= 125

                            # Gespielte Karten merken
                            assert not set(cards).intersection(pub.played_cards), f"cards: {stringify_cards(cards)},  played_cards: {stringify_cards(pub.played_cards)}"  # darf keine Schnittmenge bilden
                            pub.played_cards += cards

                            # Ist der erste Spieler fertig?
                            if pub.count_hand_cards[pub.current_turn_index] == 0:
                                n = pub.count_active_players
                                assert 1 <= n <= 3
                                if n == 3:
                                    assert pub.winner_index == -1
                                    pub.winner_index = pub.current_turn_index

                            if clients_joined:
                                await self._broadcast("player_played", {"turn": [pub.current_turn_index, pub.trick_cards, pub.trick_combination], "trick_points": pub.trick_points, "winner_index": pub.winner_index})
                            bomb = None

                            # Wunsch erfüllt?
                            assert pub.wish_value == 0 or -2 >= pub.wish_value >= -14 or 2 <= pub.wish_value <= 14
                            if pub.wish_value > 0 and is_wish_in(pub.wish_value, cards):
                                assert CARD_MAH in pub.played_cards
                                pub.wish_value = -pub.wish_value
                                if clients_joined:
                                    await self._broadcast("wish_fulfilled")

                            # Ermitteln, ob die Runde beendet ist.
                            if pub.count_hand_cards[pub.current_turn_index] == 0:
                                n = pub.count_active_players
                                assert 1 <= n <= 3
                                if n == 2:
                                    assert 0 <= pub.winner_index <= 3
                                    if (pub.current_turn_index + 2) % 4 == pub.winner_index:  # Doppelsieg?
                                        pub.is_round_over = True
                                        pub.is_double_victory = True
                                elif n == 1:
                                    pub.is_round_over = True
                                    for player_index in range(4):
                                        if pub.count_hand_cards[player_index] > 0:
                                            assert pub.loser_index == -1
                                            pub.loser_index = player_index
                                            break

                            # Runde vorbei?
                            if pub.is_round_over:
                                # Runde ist vorbei; letzten Stich abräumen und die Schleife für Kartenausspielen beenden
                                await self._take_trick(clients_joined)
                                break  # while not pub.is_round_over

                            # Falls ein MahJong ausgespielt wurde, muss ein Wunsch geäußert werden.
                            if CARD_MAH in cards:
                                assert pub.wish_value == 0
                                pub.wish_value = await self._players[pub.current_turn_index].wish()
                                assert 2 <= pub.wish_value <= 14
                                if clients_joined:
                                    await self._broadcast("wish_made", {"wish_value": pub.wish_value})

                        else:  # Spieler hat gepasst
                            if clients_joined:
                                await self._broadcast("player_passed", {"player_index": pub.current_turn_index})

                    # Nächster Spieler ist an der Reihe
                    assert not pub.is_round_over
                    assert 0 <= pub.current_turn_index <= 3
                    if pub.trick_combination == (CombinationType.SINGLE, 1, 0) and pub.trick_owner_index == pub.current_turn_index:
                        pub.current_turn_index = (pub.current_turn_index + 2) % 4
                    else:
                        pub.current_turn_index = (pub.current_turn_index + 1) % 4
                    if clients_joined:
                        await self._broadcast("player_turn_changed", {"current_turn_index": pub.current_turn_index})

                # Runde ist beendet

                # Endwertung der Runde
                assert pub.is_round_over
                if pub.is_double_victory:
                    # Doppelsieg! Das Gewinnerteam kriegt 200 Punkte. Die Gegner nichts.
                    assert sum(1 for n in pub.count_hand_cards if n > 0) == 2
                    assert 0 <= pub.winner_index <= 3
                    pub.points = [0, 0, 0, 0]
                    pub.points[pub.winner_index] = 200
                else:
                    # a) Der letzte Spieler gibt seine Handkarten an das gegnerische Team.
                    assert 0 <= pub.loser_index <= 3
                    leftover_points = 100 - sum_card_points(pub.played_cards)
                    assert leftover_points == sum_card_points(other_cards(pub.played_cards))
                    pub.points[(pub.loser_index + 1) % 4] += leftover_points
                    # b) Der letzte Spieler übergibt seine Stiche an den Spieler, der zuerst fertig wurde.
                    assert pub.winner_index >= 0
                    pub.points[pub.winner_index] += pub.points[pub.loser_index]
                    pub.points[pub.loser_index] = 0
                    assert sum(pub.points) == 100, pub.points
                    assert -25 <= pub.points[0] <= 125
                    assert -25 <= pub.points[1] <= 125
                    assert -25 <= pub.points[2] <= 125
                    assert -25 <= pub.points[3] <= 125

                # Bonus für Tichu-Ansage
                for player_index in range(4):
                    if pub.announcements[player_index]:
                        if player_index == pub.winner_index:
                            pub.points[player_index] += 100 * pub.announcements[player_index]
                        else:
                            pub.points[player_index] -= 100 * pub.announcements[player_index]

                # Ergebnis der Runde in die Punktetabelle der Partie eintragen.
                pub.game_score[0].append(pub.points[2] + pub.points[0])
                pub.game_score[1].append(pub.points[3] + pub.points[1])
                pub.round_counter += 1

                if clients_joined:
                    await self._broadcast("round_over", {"points": pub.points, "loser_index": pub.loser_index, "is_double_victory": pub.is_double_victory})
                    if config.BREAK_TIME_AFTER_ROUND > 0:
                        await asyncio.sleep(config.BREAK_TIME_AFTER_ROUND / 1000)

            # Partie ist beendet
            score20, score31 = pub.total_score
            logger.info(f"[{self.table_name}] Partie beendet. Endstand: Team 20: {score20}, Team 31: {score31}")
            pub.is_running = False
            if clients_joined:
                await self._broadcast("game_over", {"game_score": pub.game_score})
            return pub

        except asyncio.CancelledError:
            msg = f"[{self.table_name}] Spiel-Loop extern abgebrochen."
            logger.info(msg)
            # noinspection PyBroadException
            try:
                if clients_joined:
                    await self._broadcast_error(msg, ErrorCode.SERVER_DOWN)
            except Exception:
                pass

        except Exception as e:
            msg = f"[{self.table_name}] Unerwarteter Fehler im Spiel-Loop: {e}"
            logger.exception(msg)
            # noinspection PyBroadException
            try:
                if clients_joined:
                    await self._broadcast_error(msg, ErrorCode.UNKNOWN_ERROR)
            except Exception:
                pass

        finally:
            logger.info(f"[{self.table_name}] Spiel-Loop beendet.")
            self._game_loop_task = None  # Referenz aufheben

        return pub


    async def set_announcement(self, player_index):
        """
        Ein Client hat Tichu angesagt.

        Diese Funktion wird direkt vom WebSocket-Handler aufgerufen, wenn ein Client die entsprechende Nachricht gesendet hat (proaktiv).

        :param player_index: Der Index des Clients, der Tichu angesagt hat.
        :return: True, wenn die Ansage erfolgreich gesetzt wurde.
        """
        pub = self.public_state
        if not pub.is_running or pub.is_round_over:
            return False  # es läuft kein Spiel oder die letzte Runde wird gerade gewertet
        if pub.start_player_index == -1:
            return False  # das Kartenausspielen hat noch nicht begonnen
        if pub.count_hand_cards[player_index] != 14 or pub.announcements[player_index]:
            return False  # der Spieler hat schon Karten ausgespielt oder bereits Tichu angesagt
        pub.announcements[player_index] = 1
        await self._broadcast("player_announced", {"player_index": player_index, "grand": False})
        return True

    # ------------------------------------------------------
    # Hilfsfunktionen
    # ------------------------------------------------------

    async def _broadcast(self, event: str, payload: Optional[dict] = None):
        """
        Sendet eine Nachricht an alle Spieler.

        :param event: Das Spielereignis, über das berichtet wird.
        :param payload: (Optional) Die Nutzdaten der Nachricht.
        """
        for player in self._players:
            if isinstance(player, Peer):
                await player.notify(event, payload)

    async def _broadcast_error(self, message: str, code: ErrorCode, context: Optional[Dict] = None):
        """
        Sendet eine Fehlermeldung an alle Spieler.

        :param message: Die Fehlermeldung.
        :param code: Der Fehlercode.
        :param context: (Optional) Zusätzliche Informationen.
        """
        for player in self._players:
            if isinstance(player, Peer):
                await player.error(message, code, context)

    async def _deal_out(self, player_index, clients_joined: bool):
        """
        a) Teilt die ersten 8 Karten an den gegebenen Spieler aus,
        b) fragt den Spieler, ob er ein großes Tichu ansagen möchte,
        c) teilt danach die restlichen Karten an den gegebenen Spieler aus und
        d) fordert als Letztes den Spieler auf zu schupfen.

        Die Spieler werden über jedes Ereignis unmittelbar benachrichtigt.

        :param player_index: Der Index des Spielers, der die Karten bekommt.
        :param clients_joined: True, wenn Clients im Spiel sind.
        """
        pub = self._public_state
        priv = self._private_states[player_index]
        player = self._players[player_index]
        time_start = time()

        # 8 Karten aufnehmen
        n = 8
        offset = player_index * 14
        priv.hand_cards = self._mixed_deck[offset:offset + n]
        pub.count_hand_cards[player_index] = n
        if clients_joined:
            await self._broadcast("hand_cards_dealt", {"player_index": player_index, "count": n})

        # Möchte ein Spieler ein großes Tichu ansagen?
        if not pub.announcements[player_index]:
            if await player.announce():
                pub.announcements[player_index] = 2
                if clients_joined:
                    await self._broadcast("player_announced", {"player_index": player_index, "grand": True})

        # die restlichen Karten aufnehmen
        n = 14
        offset = player_index * 14
        priv.hand_cards = self._mixed_deck[offset:offset + n]
        pub.count_hand_cards[player_index] = n
        if clients_joined:
            await self._broadcast("hand_cards_dealt", {"player_index": player_index, "count": n})

        # jetzt muss der Spieler schupfen (Tauschkarten abgeben)
        assert len(priv.hand_cards) == 14
        priv.given_schupf_cards = await player.schupf()
        assert len(priv.given_schupf_cards) == 3
        priv.hand_cards = [card for card in priv.hand_cards if card not in priv.given_schupf_cards]
        assert len(priv.hand_cards) == 11
        self._public_state.count_hand_cards[player_index] = 11
        if clients_joined:
            delay = round((time() - time_start) * 1000)  # in ms
            if delay < config.AGENT_THINKING_TIME[0]:
                delay = self._random.integer(config.AGENT_THINKING_TIME[0] - delay, config.AGENT_THINKING_TIME[1] - delay)
                await asyncio.sleep(delay / 1000)
            await self._broadcast("player_schupfed", {"player_index": player_index})

    async def _take_trick(self, clients_joined: bool):
        """
        Räumt den Stich ab.

        :param clients_joined: True, wenn Clients im Spiel sind.
        """
        pub = self._public_state
        assert pub.trick_combination[0] != CombinationType.PASS
        assert pub.trick_owner_index == pub.current_turn_index
        if pub.trick_combination == (CombinationType.SINGLE, 1, 15) and not pub.is_double_victory:  # Drache kassiert? Muss verschenkt werden, wenn kein Doppelsieg!
            # Stich verschenken
            recipient = await self._players[pub.current_turn_index].give_dragon_away()
            assert recipient in ((1, 3) if pub.current_turn_index in (0, 2) else (0, 2))
            assert CARD_DRA in pub.played_cards
            assert pub.dragon_recipient == -1
            pub.dragon_recipient = recipient
        else:
            # Stich selbst kassieren
            recipient = pub.trick_owner_index

        # Punkte im Stich dem Spieler Gut schreiben.
        pub.points[recipient] += pub.trick_points
        assert -25 <= pub.points[recipient] <= 125

        # Stich zurücksetzen
        pub.trick_owner_index = -1
        pub.trick_cards = []
        pub.trick_combination = (CombinationType.PASS, 0, 0)
        pub.trick_points = 0
        pub.trick_counter += 1
        if clients_joined:
            await self._broadcast("trick_taken", {"player_index": recipient, "points": pub.points[recipient], "dragon_recipient": pub.dragon_recipient})

    # ------------------------------------------------------
    # Eigenschaften
    # ------------------------------------------------------

    @property
    def table_name(self) -> str:
        """Der Name des Spieltisches (eindeutiger Identifikator)."""
        return self._table_name

    @property
    def players(self) -> List[Player]:
        return self._players  # Mutable - Änderungen extern möglich, aber nicht vorgesehen

    @property
    def public_state(self) -> PublicState:
        """Der öffentliche Spielzustand."""
        return self._public_state  # Mutable - Änderungen extern möglich, aber nicht vorgesehen

    @property
    def private_states(self) -> List[PrivateState]:
        """Die privaten Spielzustände."""
        return self._private_states  # Mutable - Änderungen extern möglich, aber nicht vorgesehen
