from src.common.rand import Random
from src.lib.cards import CARD_MAH
from src.lib.combinations import build_action_space, CombinationType
from poc.arena_sync.agent import Agent
from poc.arena_sync.state import PublicState, PrivateState

FIGURE_PASS = (CombinationType.PASS, 0, 0)
FIGURE_DOG = (CombinationType.SINGLE, 1, 0)
FIGURE_MAH = (CombinationType.SINGLE, 1, 1)
FIGURE_DRA = (CombinationType.SINGLE, 1, 15)
FIGURE_PHO = (CombinationType.SINGLE, 1, 16)

class GameEngine:
    # Spiellogik

    # seed: Initialwert für Zufallsgenerator (Integer > 0 oder None)
    def __init__(self, agents: list[Agent], seed: int = None):
        assert len(agents) == 4
        self._agents = agents  # Agent 0 bis Agent 3
        self._number_of_clients = 0
        self._random = Random(seed)  # Zufallsgenerator, geeignet für Multiprocessing

    def play_episode(self, pub: PublicState = None, privs: list[PrivateState] = None) -> PublicState:
        # Spielt eine Episode
        # pub:  wenn gesetzt, wird dieser öffentliche Spielzustand genommen
        # privs: wenn gesetzt, werden diese privaten Spielzustände genommen

        if not pub:
            pub = PublicState()

        if not privs:
            privs = PrivateState(0), PrivateState(1), PrivateState(2), PrivateState(3)
        else:
            assert len(privs) == 4

        while pub.score[0] < 1000 and pub.score[1] < 1000:
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
                self.notify_clients("")

                # Tichu ansagen?
                for i in range(0, 4):
                    player = (first + i) % 4  # mit irgendeinem Spieler zufällig beginnen
                    grand = n == 8  # großes Tichu?
                    if not pub.announcements[player] and self._agents[player].announce(pub, privs[player], grand):
                        pub.announce(player, grand)
                        self.notify_clients("")

            # jetzt müssen die Spieler schupfen
            schupfed = [None, None, None, None]
            for player in range(0, 4):
                schupfed[player] = privs[player].schupf(self._agents[player].schupf(pub, privs[player]))
                assert privs[player].number_of_cards == 11
                pub.set_number_of_cards(player, 11)
            self.notify_clients("")

            # die abgegebenen Karten der Mitspieler aufnehmen
            for player in range(0, 4):
                privs[player].take_schupfed_cards([schupfed[giver][player] for giver in range(0, 4)])
                assert privs[player].number_of_cards == 14
                pub.set_number_of_cards(player, 14)
                if privs[player].has_mahjong:
                    pub.set_start_player(player)  # Startspieler bekannt geben
            self.notify_clients("")

            # los geht's - das eigentliche Spiel kann beginnen...
            assert 0 <= pub.current_player_index <= 3
            while not pub.is_done:
                priv = privs[pub.current_player_index]
                agent = self._agents[pub.current_player_index]
                assert pub.number_of_cards[priv.player_index] == priv.number_of_cards
                assert 0 <= pub.number_of_cards[priv.player_index] <= 14
                self.notify_clients("")

                # falls alle gepasst haben, schaut der Spieler auf seinen eigenen Stich und kann diesen abräumen
                if pub.trick_player_index == priv.player_index and pub.trick_figure != FIGURE_DOG:  # der Hund bleibt aber immer liegen
                    if not pub.double_win and pub.trick_figure == FIGURE_DRA:  # Drache kassiert? Muss verschenkt werden!
                        opponent = agent.gift(pub, priv)
                        assert opponent in ((1, 3) if priv.player_index in (0, 2) else (0, 2))
                    else:
                        opponent = -1
                    pub.clear_trick(opponent)
                    self.notify_clients("")

                # hat der Spieler noch Karten?
                if pub.number_of_cards[priv.player_index] > 0:
                    # falls noch alle Karten auf der Hand sind und noch nichts angesagt wurde, darf Tichu angesagt werden
                    if pub.number_of_cards[priv.player_index] == 14 and not pub.announcements[priv.player_index]:
                        if agent.announce(pub, priv):
                            pub.announce(priv.player_index)
                            self.notify_clients("")

                    # Kombination auswählen
                    # noinspection PyTypeChecker
                    action_space = build_action_space(priv.combinations, pub.trick_figure, pub.wish)
                    combi = agent.combination(pub, priv, action_space)
                    assert pub.number_of_cards[priv.player_index] == priv.number_of_cards
                    assert combi[1][1] <= pub.number_of_cards[priv.player_index] <= 14

                    # Kombination ausspielen
                    priv.play(combi)
                    assert priv.number_of_cards == pub.number_of_cards[priv.player_index] - combi[1][1]
                    pub.play(combi)
                    assert pub.number_of_cards[priv.player_index] == priv.number_of_cards
                    self.notify_clients("")

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
                            self.notify_clients("")
                            break

                        # falls ein MahJong ausgespielt wurde, muss ein Wunsch geäußert werden
                        if CARD_MAH in combi[0]:
                            assert pub.wish == 0
                            wish = agent.wish(pub, priv)
                            assert 2 <= wish <= 14
                            pub.set_wish(wish)
                            self.notify_clients("")

                # nächster Spieler ist an der Reihe
                pub.step()

        # Episode abgeschlossen
        return pub

    def notify_clients(self, _data) -> None:
        if not self._number_of_clients:
            return
        for _player in self._agents:
            pass

    # Zufallszahlgenerator
    @property
    def random(self) -> Random:  # pragma: no cover
        return self._random
