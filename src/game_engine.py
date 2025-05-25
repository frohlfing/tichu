"""
Definiert die Spiellogik.
"""

import asyncio
from src.common.logger import logger
from src.common.rand import Random
from src.lib.cards import deck, is_wish_in, sum_card_points, other_cards, CARD_DRA, CARD_MAH, Cards
from src.lib.combinations import CombinationType, FIGURE_DRA, FIGURE_DOG, FIGURE_PASS, FIGURE_PHO, FIGURE_MAH, Combination
from src.lib.errors import ErrorCode
from src.players.agent import Agent
from src.players.client import Client
from src.players.player import Player
from src.players.random_agent import RandomAgent
from src.private_state import PrivateState
from src.public_state import PublicState
from typing import List, Optional, Dict, Tuple


class GameEngine:
    """
    Steuert den Spielablauf eines Tisches.

    :ivar game_loop_task: Der asyncio Task, der die Hauptspielschleife ausführt.
    :ivar interrupt_event: Globales Interrupt.
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
        self._players: List[Player] = list(self._default_agents)

        # aktueller Spielzustand
        self._public_state = PublicState(
            table_name = self._table_name,
            player_names = [p.name for p in self._players],
            current_phase = "init",  # todo die Spielphasen sind noch nicht definiert
        )
        self._private_states = [PrivateState(player_index=i) for i in range(4)]

        # Referenz auf den Hintergrund-Task `_run_game_loop`
        self.game_loop_task: Optional[asyncio.Task] = None

        # Interrupt-Event
        self.interrupt_event: asyncio.Event = asyncio.Event()
        self._interrupt_player_index: Optional[int] = None
        self._interrupt_reason: Optional[str] = None

        # Zufallsgenerator, geeignet für Multiprocessing
        self._random = Random(seed)

        # Sitzplätze der Reihe nach vergeben (0 bis 3) und Interrupt-Event durchreichen
        for i, default_agent in enumerate(self._default_agents):
            default_agent.index = i
            default_agent.interrupt_event = self.interrupt_event  # Todo Test für diese Zuweisung hinzufügen

        agent_names = ", ".join(default_agent.name for default_agent in self._default_agents)
        logger.debug(f"[{self.table_name}] Agenten initialisiert: {agent_names}.")

        logger.info(f"GameEngine für Tisch '{table_name}' erstellt.")

    async def cleanup(self):
        """
        Bereinigt Ressourcen dieser Instanz.

        Bricht laufende Tasks ab und ruft dann die `cleanup`-Funktion aller Player-Instanzen auf.
        """
        logger.info(f"Bereinige Tisch '{self._table_name}'...")

        # bricht den Haupt-Spiel-Loop Task ab, falls er läuft
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

        # alle Spieler-Instanzen bereinigen (parallel)
        await asyncio.gather(*[asyncio.create_task(p.cleanup()) for p in self._players], return_exceptions=True)

        logger.info(f"Bereinigung des Tisches '{self._table_name}' beendet.")

    # ------------------------------------------------------
    # Client anmelden / abmelden
    # ------------------------------------------------------

    def get_player_by_session(self, session: str) -> Optional[Player]:
        """
        Gibt den Spieler anhand der Session zurück.

        :param session: Die Session des Spielers.
        :return: Die Player-Instanz, falls die Session existiert, sonst None.
        """
        for p in self._players:
            if p.session_id == session:
                return p
        return None

    async def join_client(self, client: Client) -> bool:
        """
        Lässt den Client mitspielen.
        :param client: Der Client, der mitspielen möchte.
        :return: True, wenn der Client einen Sitzplatz bekommen hat, ansonsten False.
        """
        # Sitzplatz suchen, der von der KI besetzt ist
        available_index = -1
        for i, p in enumerate(self._players):
            if not isinstance(p, Client):
                available_index = i
                break
        if available_index == -1:
            return False
        self._players[available_index] = client
        client.index = available_index
        client.interrupt_event = self.interrupt_event   # Todo Test für diese Zuweisung hinzufügen
        return True

    async def leave_client(self, client: Client) -> None:
        """
        Lässt den Client gehen.
        :param client: Der Client, der gehen will.
        :raise ValueError: Wenn der Client nicht gefunden werden kann.
        """
        index = client.index
        if index < 0 or index > 3:
            raise ValueError(f"Der Index des Spielers {client.name} ist nicht korrekt: {index}")
        if self._players[index].session_id != client.session_id:
            raise ValueError(f"Der Spielers {client.name} kann den Tisch {self._table_name} nicht verlassen, er sitz dort nicht.")
        self._players[index] = self._default_agents[index]
        client.index = -1

    # ------------------------------------------------------
    # Lobby-Aktionen
    # ------------------------------------------------------

    # noinspection PyMethodMayBeStatic
    def assign_team(self, player_new_indexes: List[int]) -> bool:
        """
        Stellt das Team zusammen.
        :param player_new_indexes: Liste mit den neuen Indizes der Spieler.
        :return: True, wenn die Zuordnung erfolgte, sonst False.
        """
        if len(player_new_indexes) != 4:
            return False

        # todo prüfen, ob jeder Spieler einen neuen Index zw. 0 und 3 erhalten hat
        #  prüfen, jeder Spieler einen eindeutigen Index erhalten hat
        #  self._players und self._default_agents umsortieren
        #  self._players[i].index = i setzen, ebenso für default_agents.
        #  UnitTest schreiben

        return True

    async def start_game(self):
        """
        Startet den Hintergrund-Task `_run_game_loop`
        """
        if self.game_loop_task and not self.game_loop_task.done():
            logger.warning(f"Tisch '{self.table_name}': Versuch, neue Partie zu starten, obwohl bereits eine läuft.")
            return

        logger.info(f"[{self.table_name}] Starte Hintergrund-Task für eine neue Partie.")
        self.game_loop_task = asyncio.create_task(self.run_game_loop(), name=f"Game Loop '{self.table_name}'")

    # ------------------------------------------------------
    # Partie spielen
    # ------------------------------------------------------

    # noinspection PyUnusedLocal
    async def run_game_loop(self, break_time = 5) -> Optional[PublicState]:
        """
        Steuert den Spielablauf einer Partie.

        :param break_time: Pause in Sekunden zwischen den Runden.
        :return: Der öffentliche Spielzustand.
        :raises ValueError: Wenn Parameter nicht ok sind.
        """
        # Referenz auf den Spielzustand holen
        pub = self._public_state
        privs = self._private_states
        assert pub.table_name == self.table_name
        assert pub.player_names == [p.name for p in self._players]
        assert len(privs) == 4
        for i, priv in enumerate(privs):
            assert priv.player_index == i

        # aus Performance-Gründen für die Arena wollen wir so wenig wie möglich await aufrufen, daher ermitteln wir, ob überhaupt Clients im Spiel sind
        clients_joined = any(isinstance(p, Client) for p in self._players)

        # Kopie des sortierten Standarddecks - wird jede Runde neu durchgemischt
        mixed_deck = list(deck)

        logger.info(f"[{self.table_name}] Starte neue Partie...")
        try:
            # Partie spielen
            while not pub.is_game_over:
                # Neue Runde...
                #logger.debug(f"Runde {pub.round_counter}")

                # Spielzustand zurücksetzen
                pub.reset_round()
                for priv in privs:
                    priv.reset_round()

                # Agents zurücksetzen
                for player in self._players:
                    player.reset_round()

                # Spielphase aktualisieren
                pub.current_phase = "playing"  # todo Spielphasen müssen noch definiert werden

                # Karten mischen
                self._random.shuffle(mixed_deck)

                # Karten aufnehmen, erst 8 dann alle
                first = self._random.integer(0, 4)  # wählt zufällig eine Zahl zwischen 0 und 3
                for n in (8, 14):
                    # Karten verteilen (deal out)
                    for player_index in range(0, 4):
                        offset = player_index * 14
                        privs[player_index].hand_cards = sorted(mixed_deck[offset:offset + n], reverse=True)  # absteigend sortiert!
                        pub.count_hand_cards[player_index] = n
                        await self._players[player_index].deal_cards(privs[player_index].hand_cards)

                    # möchte ein Spieler ein Tichu ansagen?
                    # todo alle Spieler gleichzeitig ansprechen
                    for i in range(0, 4):
                        player_index = (first + i) % 4  # mit irgendeinem Spieler zufällig beginnen
                        grand = n == 8  # großes Tichu?
                        announced = not pub.announcements[player_index] and await self._players[player_index].announce(pub, privs[player_index])
                        if announced:
                            pub.announcements[player_index] = 2 if grand else 1  # Spieler hat Tichu angesagt
                        if clients_joined:
                            if grand:
                                await self._broadcast("grand_tichu_announced", {"player_index": player_index, "announced": announced})
                            elif announced:
                                await self._broadcast("tichu_announced", {"player_index": player_index})

                # jetzt müssen die Spieler schupfen

                # a) Tauschkarten abgeben
                # todo alle Spieler gleichzeitig ansprechen
                for i in range(0, 4):  # Geber
                    player_index = (first + i) % 4  # mit irgendeinem Spieler zufällig beginnen
                    priv = privs[player_index]
                    assert len(priv.hand_cards) == 14
                    priv.given_schupf_cards = await self._players[player_index].schupf(pub, priv)
                    assert len(priv.given_schupf_cards) == 3
                    priv.hand_cards = [card for card in priv.hand_cards if card not in priv.given_schupf_cards]
                    assert len(priv.hand_cards) == 11
                    pub.count_hand_cards[player_index] = 11
                    if clients_joined:
                        await self._broadcast("player_schupfed", {"player_index": player_index})

                # b) Tauscharten aufnehmen
                # Karten-Index der abgegebenen Karte:
                # Ge-| Nehmer
                # ber| 0  1  2  3
                # ---|------------
                #   0| -  1  2  3
                #   1| 3  -  1  2
                #   2| 2  3  -  1
                #   3| 1  2  3  -
                # todo alle Spieler gleichzeitig ansprechen
                for player_index in range(0, 4):  # Nehmer
                    priv = privs[player_index]
                    priv.received_schupf_cards = (
                        privs[(player_index + 1) % 4].given_schupf_cards[2],
                        privs[(player_index + 2) % 4].given_schupf_cards[1],
                        privs[(player_index + 3) % 4].given_schupf_cards[0],
                    )
                    assert not set(priv.received_schupf_cards).intersection(priv.hand_cards)  # darf keine Schnittmenge bilden
                    priv.hand_cards += priv.received_schupf_cards
                    priv.hand_cards.sort(reverse=True)
                    assert len(priv.hand_cards) == 14
                    pub.count_hand_cards[player_index] = 14
                    await self._players[player_index].deal_schupf_cards(*priv.received_schupf_cards)

                # Startspieler bekannt geben
                for player_index in range(0, 4):
                    if CARD_MAH in privs[player_index].hand_cards:
                        assert pub.start_player_index == -1
                        pub.start_player_index = player_index
                        pub.current_turn_index = player_index
                        break
                if clients_joined:
                    await self._broadcast("player_turn_changed", {"current_turn_index": pub.current_turn_index})

                # los geht's - das eigentliche Spiel kann beginnen...
                assert 0 <= pub.current_turn_index <= 3
                while not pub.is_round_over:
                    assert 0 <= pub.count_hand_cards[pub.current_turn_index] <= 14

                    # falls der aktuelle Spieler den Stich kassieren darf oder den Stich evtl. bedienen könnte (kein Anspiel), jeden Mitspieler fragen, ob er eine Bombe werfen will
                    bomb: Optional[Tuple[Cards, Combination]] = None
                    if ((pub.trick_owner_index == pub.current_turn_index and pub.trick_combination != FIGURE_DOG)  # der Stich kann kassiert werden
                        or (pub.count_hand_cards[pub.current_turn_index] > 0 and pub.trick_owner_index >= 0)):  # der Spieler könnte evtl. den Stich bedienen (kein Anspiel)
                        # todo alle Spieler gleichzeitig ansprechen
                        for i in range(0, 4):
                            player_index = (first + i) % 4  # mit irgendeinem Spieler zufällig beginnen
                            if player_index != pub.current_turn_index and self._private_states[player_index].has_bomb:
                                bomb = await self._players[player_index].bomb(pub, self._private_states[player_index])
                                if bomb:
                                    pub.current_turn_index = player_index
                                    break

                    priv = privs[pub.current_turn_index]
                    assert priv.player_index == pub.current_turn_index
                    assert len(priv.hand_cards) == pub.count_hand_cards[pub.current_turn_index]
                    player = self._players[pub.current_turn_index]

                    # falls alle gepasst haben, schaut der Spieler auf seinen eigenen Stich und kann diesen abräumen
                    if not bomb and pub.trick_owner_index == pub.current_turn_index and pub.trick_combination != FIGURE_DOG:  # der Hund bleibt liegen
                        assert pub.trick_combination != FIGURE_PASS
                        if pub.trick_combination == FIGURE_DRA:  # Drache kassiert? Muss verschenkt werden!
                            # Stich verschenken
                            opponent = await player.give_dragon_away(pub, priv)
                            assert opponent in ((1, 3) if pub.current_turn_index in (0, 2) else (0, 2))
                            assert CARD_DRA in pub.played_cards
                            assert pub.dragon_recipient == -1
                            pub.dragon_recipient = opponent
                            pub.points[opponent] += pub.trick_points
                            assert -25 <= pub.points[opponent] <= 125
                            if clients_joined:
                                await self._broadcast("trick_taken", {"player_index": opponent})
                        else:
                            # Stich selbst kassieren
                            pub.points[pub.trick_owner_index] += pub.trick_points
                            assert -25 <= pub.points[pub.trick_owner_index] <= 125
                            if clients_joined:
                                await self._broadcast("trick_taken", {"player_index": pub.trick_owner_index})
                        # Stich zurücksetzen
                        pub.trick_owner_index = -1
                        pub.trick_combination = (CombinationType.PASS, 0, 0)
                        pub.trick_points = 0
                        pub.trick_counter += 1

                    # hat der Spieler noch Karten?
                    if pub.count_hand_cards[pub.current_turn_index] > 0:
                        if bomb:
                            # der Spieler hat bereits die Bombe geworfen, wir müssen nicht nochmal nach einer Kombination fragen
                            cards, combination = bomb
                            bomb = None
                        else:
                            # falls noch alle Karten auf der Hand sind und noch nichts angesagt wurde, darf ein normales Tichu angesagt werden
                            if pub.count_hand_cards[pub.current_turn_index] == 14 and not pub.announcements[pub.current_turn_index]:
                                if await player.announce(pub, priv):
                                    # Spieler hat Tichu angesagt
                                    pub.announcements[pub.current_turn_index] = 1
                                    if clients_joined:
                                        await self._broadcast("tichu_announced", {"player_index": pub.current_turn_index})
                            cards, combination = await player.play(pub, priv)

                        assert combination[1] <= pub.count_hand_cards[pub.current_turn_index] <= 14
                        assert combination[1] == len(cards)

                        # Entscheidung des Spielers festhalten
                        assert pub.current_turn_index != -1
                        if pub.trick_owner_index == -1:  # neuer Stich?
                            assert combination != FIGURE_PASS  # beim Anspiel darf nicht gepasst werden, der erste Eintrag im Stich sind also Karten
                            pub.tricks.append([(player.index, cards, combination)])
                        else:
                            assert len(pub.tricks) > 0
                            pub.tricks[-1].append((player.index, cards, combination))

                        # Kombination ausspielen, falls nicht gepasst wurde
                        if combination != FIGURE_PASS:
                            # Handkarten aktualisieren
                            assert pub.count_hand_cards[pub.current_turn_index] == len(priv.hand_cards)
                            priv.hand_cards = [card for card in priv.hand_cards if card not in cards]
                            assert pub.count_hand_cards[pub.current_turn_index] >= combination[1]
                            pub.count_hand_cards[pub.current_turn_index] -= combination[1]
                            #assert len(priv.hand_cards) == pub.count_hand_cards[pub.current_turn_index] - combination[1]
                            assert pub.count_hand_cards[pub.current_turn_index] == len(priv.hand_cards)

                            # Stich aktualisieren
                            pub.trick_owner_index = pub.current_turn_index
                            if combination == FIGURE_PHO:
                                assert pub.trick_combination == FIGURE_PASS or pub.trick_combination[0] == CombinationType.SINGLE
                                assert pub.trick_combination != FIGURE_DRA  # Phönix auf Drachen geht nicht
                                # Der Phönix ist eigentlich um 0.5 größer als der Stich, aber gleichsetzen geht auch (Anspiel == 1).
                                if pub.trick_combination[2] == 0:  # Anspiel oder Hund?
                                    pub.trick_combination = FIGURE_MAH
                            else:
                                pub.trick_combination = combination
                            pub.trick_points += sum_card_points(cards)
                            assert -25 <= pub.trick_points <= 125

                            # Gespielte Karten merken
                            assert not set(cards).intersection(pub.played_cards)  # darf keine Schnittmenge bilden
                            pub.played_cards += cards
                            if clients_joined:
                                await self._broadcast("played", {"player_index": player.index, "cards": cards})

                            # Wunsch erfüllt?
                            assert pub.wish_value == 0 or -2 >= pub.wish_value >= -14 or 2 <= pub.wish_value <= 14
                            if pub.wish_value > 0 and is_wish_in(pub.wish_value, cards):
                                assert CARD_MAH in pub.played_cards
                                pub.wish_value = -pub.wish_value
                                if clients_joined:
                                    await self._broadcast("wish_fulfilled")

                            # ermitteln, ob die Runde beendet ist
                            if pub.count_hand_cards[pub.current_turn_index] == 0:
                                n = pub.count_active_players
                                assert 1 <= n <= 3
                                if n == 3:
                                    assert pub.winner_index == -1
                                    pub.winner_index = pub.current_turn_index
                                elif n == 2:
                                    assert 0 <= pub.winner_index <= 3
                                    if (pub.current_turn_index + 2) % 4 == pub.winner_index:  # Doppelsieg?
                                        pub.is_round_over = True
                                        pub.is_double_victory = True
                                elif n == 1:
                                    pub.is_round_over = True
                                    for player_index in range(0, 4):
                                        if pub.count_hand_cards[player_index] > 0:
                                            assert pub.loser_index == -1
                                            pub.loser_index = player_index
                                            break

                            # Runde vorbei?
                            if pub.is_round_over:
                                # Runde ist vorbei; letzten Stich abräumen
                                assert pub.trick_combination != FIGURE_PASS
                                assert pub.trick_owner_index == pub.current_turn_index
                                if pub.is_double_victory:
                                    # Doppelsieg! Die Karten müssen nicht gezählt werden.
                                    assert pub.is_round_over
                                    assert 0 <= pub.winner_index <= 3
                                    assert sum(1 for n in pub.count_hand_cards if n > 0) == 2
                                    pub.points = [0, 0, 0, 0]
                                    pub.points[pub.winner_index] = 200
                                else:
                                    # Punkte im Stich zählen
                                    if pub.trick_combination == FIGURE_DRA:  # Drache kassiert? Muss verschenkt werden!
                                        # Stich verschenken
                                        opponent = await player.give_dragon_away(pub, priv)
                                        assert opponent in ((1, 3) if pub.current_turn_index in (0, 2) else (0, 2))
                                        assert CARD_DRA in pub.played_cards
                                        assert pub.dragon_recipient == -1
                                        pub.dragon_recipient = opponent
                                        pub.points[opponent] += pub.trick_points
                                        assert -25 <= pub.points[opponent] <= 125
                                    else:
                                        # Stich selbst kassieren
                                        pub.points[pub.trick_owner_index] += pub.trick_points
                                        assert -25 <= pub.points[pub.trick_owner_index] <= 125

                                    # Endwertung der Runde:
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

                                # Stich zurücksetzen
                                pub.trick_owner_index = -1
                                pub.trick_combination = (CombinationType.PASS, 0, 0)
                                pub.trick_points = 0
                                pub.trick_counter += 1

                                # Bonus für Tichu-Ansage
                                for player_index in range(0, 4):
                                    if pub.announcements[player_index]:
                                        if player_index == pub.winner_index:
                                            pub.points[player_index] += 100 * pub.announcements[player_index]
                                        else:
                                            pub.points[player_index] -= 100 * pub.announcements[player_index]

                                # Ergebnis der Runde in die Punktetabelle der Partie eintragen
                                pub.game_score[0].append(pub.points[2] + pub.points[0])
                                pub.game_score[1].append(pub.points[3] + pub.points[1])
                                pub.round_counter += 1
                                break  # while not pub.is_round_over

                            # falls ein MahJong ausgespielt wurde, muss ein Wunsch geäußert werden
                            if CARD_MAH in cards:
                                assert pub.wish_value == 0
                                pub.wish_value = await player.wish(pub, priv)
                                assert 2 <= pub.wish_value <= 14
                                if clients_joined:
                                    await self._broadcast("wish_made", {"wish_value": pub.wish_value})

                        else:  # Spieler hat gepasst
                            if clients_joined:
                                await self._broadcast("passed", {"player_index": player.index})

                    # nächster Spieler ist an der Reihe
                    assert not pub.is_round_over
                    assert 0 <= pub.current_turn_index <= 3
                    if pub.trick_combination == FIGURE_DOG and pub.trick_owner_index == pub.current_turn_index:
                        pub.current_turn_index = (pub.current_turn_index + 2) % 4
                    else:
                        pub.current_turn_index = (pub.current_turn_index + 1) % 4
                    if clients_joined:
                        await self._broadcast("player_turn_changed", {"current_turn_index": pub.current_turn_index})

                # Runde ist beendet
                if break_time:
                    await asyncio.sleep(break_time)
                if clients_joined:
                    await self._broadcast("round_over", {"game_score": pub.game_score, "is_double_victory": pub.is_double_victory})

            # Partie ist beendet
            score20, score31 = pub.total_score
            logger.info(f"[{self.table_name}] Partie beendet. Endstand: Team 20: {score20}, Team 31: {score31}")
            if clients_joined:
                await self._broadcast("game_over", {"game_score": pub.game_score, "is_double_victory": pub.is_double_victory})
            return pub

        except asyncio.CancelledError:
            msg = f"[{self.table_name}] Spiel-Loop extern abgebrochen."
            logger.info(msg)
            pub.current_phase = "aborted"
            # noinspection PyBroadException
            try:
                if clients_joined:
                    await self._broadcast_error(msg, ErrorCode.SERVER_DOWN)
            except Exception:
                pass

        except Exception as e:
            msg = f"[{self.table_name}] Kritischer Fehler im Spiel-Loop: {e}"
            logger.exception(msg)
            pub.current_phase = "error"
            # noinspection PyBroadException
            try:
                if clients_joined:
                    await self._broadcast_error(msg, ErrorCode.UNKNOWN_ERROR)
            except Exception:
                pass

        finally:
            logger.info(f"[{self.table_name}] Spiel-Loop definitiv beendet.")
            self.game_loop_task = None  # Referenz aufheben

        return pub

    # ------------------------------------------------------
    # Hilfsfunktionen
    # ------------------------------------------------------

    async def _broadcast(self, message_type: str, payload: Optional[dict] = None):
        """
        Sendet eine Nachricht an alle Clients.

        :param message_type: Der Typ der Nachricht.
        :param payload: (Optional) Die Nutzdaten der Nachricht.
        """
        for player in self._players:
            if isinstance(player, Client):
                await player.notify(message_type, payload)

    async def _broadcast_error(self, message: str, code: ErrorCode, context: Optional[Dict] = None):
        """
        Sendet eine Fehlermeldung an alle Clients.

        :param message: Die Fehlermeldung.
        :param code: Der Fehlercode.
        :param context: (Optional) Zusätzliche Informationen.
        """
        for player in self._players:
            if isinstance(player, Client):
                await player.error(message, code, context)

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
