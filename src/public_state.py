from src.common.rand import Random
from src.lib.cards import deck, is_wish_in, sum_card_points, other_cards, CARD_MAH, CARD_DRA
from src.lib.combinations import SINGLE, FIGURE_PASS, FIGURE_MAH, FIGURE_PHO, FIGURE_DRA, FIGURE_DOG


class PublicState:
    def __init__(self,
                 current_player_index: int = -1,
                 start_player_index: int = -1,
                 number_of_cards: list[int] = None,
                 number_of_players: int = 4,
                 played_cards: list[tuple] = None,
                 announcements: list[int] = None,
                 wish: int = 0,
                 gift: int = -1,
                 trick_player_index: int = -1,
                 trick_figure: tuple[int, int, int] = (0, 0, 0),
                 trick_points: int = 0,
                 history: list[tuple] = None,
                 points: list[int] = None,
                 winner: int = -1,
                 loser: int = -1,
                 is_done: bool = False,
                 double_win: bool = False,
                 score: list[int] = None,
                 trick_counter: int = 0,
                 round_counter: int = 0,
                 seed: int = None):
        if number_of_cards:
            assert len(number_of_cards) == 4  # pragma: no cover
        if announcements:
            assert len(announcements) == 4  # pragma: no cover
        if points:
            assert len(points) == 4  # pragma: no cover
        if score:
            assert len(score) == 2  # pragma: no cover
        self._mixed_deck = list(deck)  # gemischtes Kartendeck
        self._random = Random(seed)  # Zufallsgenerator, geeignet für Multiprocessing
        # Public Observation Space:
        self._current_player_index: int = current_player_index  # Index des Spielers, der am Zug ist (-1, falls noch kein Startspieler feststeht)
        self._start_player_index: int = start_player_index  # Index des Spielers, der den Mahjong hat oder hatte (-1 == steht noch nicht fest)
        self._number_of_cards: list[int] = number_of_cards if number_of_cards else [0, 0, 0, 0]  # Anzahl der Handkarten aller Spieler
        self._number_of_players: int = number_of_players  # Anzahl Spieler, die noch im Rennen sind
        self._played_cards: list[tuple] = played_cards if played_cards else []  # bereits gespielte Karten
        self._announcements: list[int] = announcements if announcements else [0, 0, 0, 0]  # Ansagen (0 == keine Ansage, 1 == kleines, 2 == großes Tichu)
        self._wish: int = wish  # Unerfüllter Wunsch (0 == kein Wunsch geäußert, negativ == bereits erfüllt)
        self._gift: int = gift  # Nummer des Spielers, der den Drachen bekommen hat (-1 == noch niemand)
        self._trick_player_index: int = trick_player_index  # Besitzer des Stichs (-1 == noch nichts gelegt oder gerade Stich abgeräumt)
        self._trick_figure: tuple = trick_figure  # Typ, Länge, Wert des aktuellen Stichs ((0,0,0), falls kein Stich liegt)
        self._trick_points: int = trick_points  # Punkte des aktuellen Stichs
        self._history: list[tuple] = history if history else []  # Spielverlauf der Runde [(player, combi), ...]
        self._points: list[int] = points if points else [0, 0, 0, 0]  # Punktestand der aktuellen Runde
        self._winner: int = winner  # Index des Spielers, der zuerst fertig wurde (-1 == alle Spieler sind noch dabei)
        self._loser: int = loser  # Index des letzten Spielers (-1 == Spiel läuft noch oder Doppelsieg)
        self._is_done: bool = is_done  # Runde fertig?
        self._double_win: bool = double_win  # Doppelsieg?
        self._score: list[int] = score if score else [0, 0]  # Gesamt-Punktestand der Episode für Team 20 und Team 31
        self._trick_counter: int = trick_counter  # Stich-Zähler (nur für statistische Zwecke)
        self._round_counter: int = round_counter  # Anzahl beendete Runden (nur für statistische Zwecke)

    # Spielzustand für eine neue Runde zurücksetzen
    def reset(self):  # pragma: no cover
        self._current_player_index = -1
        self._start_player_index = -1
        self._number_of_cards = [0, 0, 0, 0]
        self._number_of_players = 4
        self._played_cards = []
        self._announcements = [0, 0, 0, 0]
        self._wish = 0
        self._gift = -1
        self._trick_player_index = -1
        self._trick_figure = (0, 0, 0)
        self._trick_points = 0
        self._history = []
        self._points = [0, 0, 0, 0]
        self._winner = -1
        self._loser = -1
        self._is_done = False
        self._double_win = False

    # Spielzustand für eine neue Episode zurücksetzen
    def reset_score(self):  # pragma: no cover
        self._score = [0, 0]
        self._trick_counter = 0
        self._round_counter = 0

    # def copy(self) -> 'PublicState':
    #     return PublicState(current_player=self._current_player,
    #                        start_player=self._start_player,
    #                        number_of_cards=self._number_of_cards,
    #                        number_of_players=self._number_of_players,
    #                        played_cards=self._played_cards,
    #                        announcements=self._announcements,
    #                        wish=self._wish,
    #                        gift=self._gift,
    #                        trick_player=self._trick_player,
    #                        trick_figure=self._trick_figure,
    #                        trick_points=self._trick_points,
    #                        history=self._history,
    #                        points=self._points,
    #                        winner=self._winner,
    #                        loser=self._loser,
    #                        is_done=self._is_done,
    #                        double_win=self._double_win,
    #                        score=self._score,
    #                        trick_counter=self._trick_counter,
    #                        round_counter=self._round_counter)

    # Karten mischen
    def shuffle_cards(self):
        self._random.shuffle(self._mixed_deck)

    # Karten austeilen
    # Die Karten werden absteigend sortiert zurückgegeben.
    # player: Spieler (0 bis 3)
    # n: Anzahl Karten (8 oder 14)
    def deal_out(self, player: int, n: int) -> list[tuple]:
        offset = player * 14
        return sorted(self._mixed_deck[offset:offset + n], reverse=True)

    # Startspieler bekannt geben
    def set_start_player(self, player: int):  # pragma: no cover
        assert not self._is_done
        assert 0 <= player <= 3
        assert self._start_player_index == -1
        self._start_player_index = player
        assert self._current_player_index == -1
        self._current_player_index = player

    # Anzahl der Handkarten angeben
    def set_number_of_cards(self, player: int, n: int):  # pragma: no cover
        assert not self._is_done
        assert 0 <= player <= 3
        assert (self._number_of_cards[player] == 0 and n == 8) or \
               (self._number_of_cards[player] == 8 and n == 14) or \
               (self._number_of_cards[player] == 14 and n == 11) or \
               (self._number_of_cards[player] == 11 and n == 14)
        self._number_of_cards[player] = n

    # Tichu ansagen
    def announce(self, player: int, grand: bool = False):  # pragma: no cover
        assert not self._is_done
        assert 0 <= player <= 3
        assert self._announcements[player] == 0
        assert (grand and self._number_of_cards[player] == 8 and self._start_player_index == -1) or (not grand and self._number_of_cards[player] == 14)
        self._announcements[player] = 2 if grand else 1

    # Kombination spielen
    # combi: Ausgewählte Kombination (Karten, (Typ, Länge, Wert))
    def play(self, combi: tuple):
        assert not self._is_done
        assert self._current_player_index != -1
        self._history.append((self._current_player_index, combi))
        if combi[1] == FIGURE_PASS:
            return

        # Gespielte Karten merken
        assert not set(combi[0]).intersection(self._played_cards)  # darf keine Schnittmenge bilden
        self._played_cards += combi[0]

        # Anzahl Handkarten aktualisieren
        assert combi[1][1] == len(combi[0])
        assert self._number_of_cards[self._current_player_index] >= combi[1][1]
        self._number_of_cards[self._current_player_index] -= combi[1][1]

        # Wunsch erfüllt?
        assert self._wish == 0 or -2 >= self._wish >= -14 or 2 <= self._wish <= 14
        if self._wish > 0 and is_wish_in(self._wish, combi[0]):
            assert CARD_MAH in self._played_cards
            self._wish = -self._wish

        # Stich aktualisieren
        self._trick_player_index = self._current_player_index
        if combi[1] == FIGURE_PHO:
            assert self._trick_figure == (0, 0, 0) or self._trick_figure[0] == SINGLE
            assert self._trick_figure != FIGURE_DRA  # Phönix auf Drache geht nicht
            # Der Phönix ist eigentlich um 0.5 größer als der Stich, aber gleichsetzen geht auch (Anspiel == 1).
            if self._trick_figure[2] == 0:  # Anspiel oder Hund?
                self._trick_figure = FIGURE_MAH
        else:
            self._trick_figure = combi[1]
        self._trick_points += sum_card_points(combi[0])
        assert -25 <= self._trick_points <= 125

        # Runde beendet?
        if self._number_of_cards[self._current_player_index] == 0:
            self._number_of_players -= 1
            assert 1 <= self._number_of_players <= 3
            if self._number_of_players == 3:
                assert self._winner == -1
                self._winner = self._current_player_index
            elif self._number_of_players == 2:
                assert 0 <= self._winner <= 3
                if (self._current_player_index + 2) % 4 == self._winner:  # Doppelsieg?
                    self._is_done = True
                    self._double_win = True
            elif self._number_of_players == 1:
                self._is_done = True
                for player in range(0, 4):
                    if self._number_of_cards[player] > 0:
                        assert self._loser == -1
                        self._loser = player
                        break

    # Wunsch äußern
    def set_wish(self, wish: int):  # pragma: no cover
        assert not self._is_done
        assert 2 <= wish <= 14
        assert CARD_MAH in self._played_cards
        assert self._wish == 0
        self._wish = wish

    # Stich abräumen
    # opponent: Nummer des Gegners, falls der Stich verschenkt werden muss, ansonsten -1
    def clear_trick(self, opponent: int = -1):
        # Sicherstellen, dass die Funktion nicht zweimal aufgerufen wird, sondern nur, wenn ein Stich abgeräumt werden kann.
        assert self._trick_player_index != -1
        assert self._trick_player_index == self._current_player_index
        assert self._trick_figure != (0, 0, 0)

        if self._double_win:
            # Doppelsieg! Die Karten müssen nicht gezählt werden.
            assert self._is_done
            assert 0 <= self._winner <= 3
            assert self._number_of_players == 2
            self._points = [0, 0, 0, 0]
            self._points[self._winner] = 200
        else:
            # Stich abräumen
            if opponent != -1:
                # Verschenken
                assert opponent in ((1, 3) if self._trick_player_index in (0, 2) else (0, 2))
                assert CARD_DRA in self._played_cards
                assert self._gift == -1
                self._gift = opponent
                self._points[opponent] += self._trick_points
                assert -25 <= self._points[opponent] <= 125
            else:
                # Selbst kassieren
                self._points[self._trick_player_index] += self._trick_points
                assert -25 <= self._points[self._trick_player_index] <= 125

            # Runde vorbei?
            if self._is_done:
                # Der letzte Spieler gibt seine Handkarten an das gegnerische Team.
                assert 0 <= self._loser <= 3
                leftover_points = 100 - sum_card_points(self._played_cards)
                assert leftover_points == sum_card_points(other_cards(self._played_cards))
                self._points[(self._loser + 1) % 4] += leftover_points
                # Der letzte Spieler übergibt seine Stiche an den Spieler, der zuerst fertig wurde.
                assert self._winner >= 0
                self._points[self._winner] += self._points[self._loser]
                self._points[self._loser] = 0
                assert sum(self._points) == 100
                assert -25 <= self._points[0] <= 125
                assert -25 <= self._points[1] <= 125
                assert -25 <= self._points[2] <= 125
                assert -25 <= self._points[3] <= 125

        self._trick_player_index = -1
        self._trick_figure = (0, 0, 0)
        self._trick_points = 0
        self._trick_counter += 1

        # Runde vorbei? Dann Bonus-Punkte berechnen und Gesamt-Punktestand aktualisieren
        if self._is_done:
            # Bonus für Tichu-Ansage
            for player in range(0, 4):
                if self._announcements[player]:
                    if player == self._winner:
                        self._points[player] += 100 * self._announcements[player]
                    else:
                        self._points[player] -= 100 * self._announcements[player]

            # Score (Gesamt-Punktestand der aktuellen Episode)
            self._score[0] += self.points[0] + self.points[2]
            self._score[1] += self.points[1] + self.points[3]
            self._round_counter += 1

    # Nächsten Spieler auswählen
    def step(self):
        assert not self._is_done
        assert 0 <= self._current_player_index <= 3
        if self._trick_figure == FIGURE_DOG and self._trick_player_index == self._current_player_index:
            self._current_player_index = (self._current_player_index + 2) % 4
        else:
            self._current_player_index = (self._current_player_index + 1) % 4

    # Spieler der am Zug ist (-1, falls noch kein Startspieler feststeht)
    @property
    def current_player_index(self) -> int:  # pragma: no cover
        return self._current_player_index

    # Spieler, der den Mahjong hat oder hatte (-1 == steht noch nicht fest)
    @property
    def start_player_index(self) -> int:  # pragma: no cover
        return self._start_player_index

    # Anzahl der Handkarten aller Spieler
    @property
    def number_of_cards(self) -> list[int]:  # pragma: no cover
        return self._number_of_cards

    # Anzahl Spieler, die noch im Rennen sind
    @property
    def number_of_players(self) -> int:  # pragma: no cover
        return self._number_of_players

    # bereits gespielte Karten
    @property
    def played_cards(self) -> list[tuple]:  # pragma: no cover
        return self._played_cards

    # Nicht gespielte Karten (in aufsteigender Reihenfolge)
    @property
    def unplayed_cards(self) -> list[tuple]:  # pragma: no cover
        return other_cards(self._played_cards)

    # Ansagen aller Spieler (0 == keine Ansage, 1 == kleines Tichu, 2 == großes Tichu)
    @property
    def announcements(self) -> list[int]:  # pragma: no cover
        return self._announcements

    # Unerfüllter Wunsch (0 == kein Wunsch geäußert, negativ == bereits erfüllt)
    @property
    def wish(self) -> int:  # pragma: no cover
        return self._wish

    # Nummer des Spielers, der den Drachen bekommen hat (-1 == noch niemand)
    @property
    def gift(self) -> int:  # pragma: no cover
        return self._gift

    # Besitzer des Stichs (-1 == noch nichts gelegt oder gerade Stich abgeräumt)
    @property
    def trick_player_index(self) -> int:  # pragma: no cover
        return self._trick_player_index

    # Typ, Länge, Wert des aktuellen Stichs ((0,0,0), falls kein Stich liegt)
    @property
    def trick_figure(self) -> tuple:  # pragma: no cover
        return self._trick_figure

    # Punkte des aktuellen Stichs
    @property
    def trick_points(self) -> int:  # pragma: no cover
        return self._trick_points

    # Spielverlauf der Runde [(player, combi), ...]
    @property
    def history(self) -> list[tuple]:  # pragma: no cover
        return self._history

    # Punktestand der aktuellen Runde
    @property
    def points(self) -> list[int]:  # pragma: no cover
        return self._points

    # Aktuelle Punkte für Team A (Spieler 0 und 2) und Team B (Spieler 1 und 3)
    @property
    def points_per_team(self) -> list[int]:
        return [self._points[0] + self._points[2], self._points[1] + self._points[3]]

    # Spieler, der zuerst fertig wurde (-1 == alle Spieler sind noch in der Runde)
    @property
    def winner(self) -> int:  # pragma: no cover
        return self._winner

    # Der letzte Spieler (-1 == Spiel läuft noch oder Doppelsieg)
    @property
    def loser(self) -> int:  # pragma: no cover
        return self._loser

    # Runde beendet?
    @property
    def is_done(self) -> bool:  # pragma: no cover
        return self._is_done

    # Doppelsieg?
    @property
    def double_win(self) -> bool:  # pragma: no cover
        return self._double_win

    # Gesamt-Punktestand der Episode für Team A (Spieler 0 und 2) und Team B (Spieler 1 und 3)
    @property
    def score(self) -> list[int]:  # pragma: no cover
        return self._score

    # Stich-Zähler einer Episode (nur für statistische Zwecke)
    @property
    def trick_counter(self) -> int:  # pragma: no cover
        return self._trick_counter

    # Runden-Zähler einer Episode (nur für statistische Zwecke)
    @property
    def round_counter(self) -> int:  # pragma: no cover
        return self._round_counter
