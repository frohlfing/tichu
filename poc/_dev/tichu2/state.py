import numpy as np
from tichu.cards import *
from tichu.combinations import *
from tichu.partitions import build_partitions, remove_partitions
from typing import List, Tuple


class PublicState:
    def __init__(self, current_player=-1, start_player=-1, number_of_cards=(0, 0, 0, 0), number_of_players=4,
                 played_cards=(), announcements=(0, 0, 0, 0), wish=0, gift=-1,
                 trick_player=-1, trick_figure=(0, 0, 0), trick_points=0, trick_counter=0,
                 points=(0, 0, 0, 0), winner=-1, loser=-1, is_done=False, double_win=False, score=(0, 0), history=(),
                 seed=None):
        self._mixed_deck = list(deck)  # gemischtes Kartendeck  # todo seed, random und mixed_deck raus?
        self._seed = seed  # Initialwert für Zufallsgenerator (Integer > 0 oder None)
        self._random = None  # wegen Multiprocessing ist ein eigener Zufallsgenerator notwendig
        # Public Observation Space:
        self._current_player: int = current_player  # Spieler der am Zug ist (-1, falls noch kein Startspieler feststeht)
        self._start_player: int = start_player  # Spieler, der den Mahjong hat oder hatte (-1 == steht noch nicht fest)
        self._number_of_cards: List[int] = list(number_of_cards)  # Anzahl der Handkarten aller Spieler
        self._number_of_players: int = number_of_players  # Anzahl Spieler, die noch im Rennen sind
        self._played_cards: List[tuple] = list(played_cards)  # bereits gespielte Karten
        self._announcements: List[int] = list(announcements)  # Ansagen (0 == keine Ansage, 1 == kleines, 2 == großes Tichu)
        self._wish: int = wish  # Unerfüllter Wunsch (0 == kein Wunsch geäußert, negativ == bereits erfüllt)
        self._gift: int = gift  # Nummer des Spielers, der den Drachen bekommen hat (-1 == noch niemand)
        self._trick_player: int = trick_player  # Besitzer des Stichs (-1 == noch nichts gelegt oder gerade Stich abgeräumt)
        self._trick_figure: tuple = trick_figure  # Typ, Länge, Wert des aktuellen Stichs ((0,0,0), falls kein Stich liegt)
        self._trick_points: int = trick_points  # Punkte des aktuellen Stichs
        self._trick_counter: int = trick_counter  # Stich-Zähler (nur für statistische Zwecke)  todo raus
        self._points: List[int] = list(points)  # Punktestand der aktuellen Runde
        self._winner: int = winner  # Spieler, der zuerst fertig wurde (-1 == alle Spieler sind noch dabei)
        self._loser: int = loser  # der letzte Spieler (-1 == Spiel läuft noch oder Doppelsieg)
        self._is_done: bool = is_done  # Runde fertig?
        self._double_win: bool = double_win  # Doppelsieg?
        self._score: List[int] = list(score)  # Gesamt-Punktestand der Episode für Team A (Spieler 0 und 2) und B (1 und 3)
        self._history: List[tuple] = list(history)  # Spielverlauf = [(player, combi), ...]

    # Alles (bis auf score) für eine neue Runde zurücksetzen
    def reset(self):  # pragma: no cover
        self._current_player = -1
        self._start_player = -1
        self._number_of_cards = [0, 0, 0, 0]
        self._number_of_players = 4
        self._played_cards = []
        self._announcements = [0, 0, 0, 0]
        self._wish = 0
        self._gift = -1
        self._trick_player = -1
        self._trick_figure = (0, 0, 0)
        self._trick_points = 0
        self._trick_counter = 0
        self._points = [0, 0, 0, 0]
        self._winner = -1
        self._loser = -1
        self._is_done = False
        self._double_win = False
        self._history = []

    # Gesamt-Punktestand für eine neue Episode zurücksetzen
    def reset_score(self):  # pragma: no cover
        self._score = [0, 0]

    def copy(self) -> 'PublicState':
        return PublicState(current_player=self._current_player,
                           start_player=self._start_player,
                           number_of_cards=self._number_of_cards,
                           number_of_players=self._number_of_players,
                           played_cards=self._played_cards,
                           announcements=self._announcements,
                           wish=self._wish,
                           gift=self._gift,
                           trick_player=self._trick_player,
                           trick_figure=self._trick_figure,
                           trick_points=self._trick_points,
                           trick_counter=self._trick_counter,
                           points=self._points,
                           winner=self._winner,
                           loser=self._loser,
                           is_done=self._is_done,
                           double_win=self._double_win,
                           history=self._history)

    def to_string(self) -> str:
        # todo immer wenn sich was ändert, sollte dieser String sich auch ändern. Sicherstellen, dass das so ist!
        return f'{self._current_player}{self._start_player}{self._number_of_cards}{self._announcements}{self._wish}{self._gift}'

    def print_board(self):
        print(f'Current Player: {self._current_player}; Start Player: {self._start_player}; Number of cards: {self._number_of_cards}; Number of players: {self._number_of_players}')
        print(f'Played cards: {stringify_cards(self._played_cards)}')
        print(f'Announcements: {self._announcements}; Wish: {self._wish}; Gift: {self._gift}')
        print(f'Trick: Player: {self._trick_player}, Figure: {stringify_figure(self._trick_figure)}, Points; {self._trick_points}, Counter: {self._trick_counter}')
        print(f'Points: {self._points}; Winner: {self._winner}; Loser: {self._loser}')
        print(f'Is done: {self._is_done}; Double win: {self._double_win}; Score: {self._score}')
        print(f'History: {self._history}')
        print()

    # Karten mischen
    def shuffle_cards(self):  # todo in die Arena
        if not self._random:
            self._random = np.random.RandomState(self._seed)
        self._random.shuffle(self._mixed_deck)

    # Karten austeilen
    # Die Karten werden absteigend sortiert zurückgegeben.
    # player: Spieler (0 bis 3)
    # n: Anzahl Karten (8 oder 14)
    def deal_out(self, player: int, n: int) -> List[tuple]:  # todo in die Arena   # todo Rückgabe als Tuple
        offset = player * 14
        return sorted(self._mixed_deck[offset:offset + n], reverse=True)

    # Startspieler bekannt geben
    def set_start_player(self, player: int):  # pragma: no cover
        assert not self._is_done
        assert 0 <= player <= 3
        assert self._start_player == -1
        self._start_player = player
        assert self._current_player == -1
        self._current_player = player

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
        assert (grand and self._number_of_cards[player] == 8 and self._start_player == -1) or (not grand and self._number_of_cards[player] == 14)
        self._announcements[player] = 2 if grand else 1

    # Kombination spielen
    # combi: Ausgewählte Kombination (Karten, (Typ, Länge, Wert))
    def play(self, combi: tuple):
        assert not self._is_done
        assert self._current_player != -1
        self._history.append((self._current_player, combi))
        if combi[1] == FIGURE_PASS:
            return

        # Gespielte Karten merken
        assert not set(combi[0]).intersection(self._played_cards)  # darf keine Schnittmenge bilden
        self._played_cards += combi[0]

        # Anzahl Handkarten aktualisieren
        assert combi[1][1] == len(combi[0])
        assert self._number_of_cards[self._current_player] >= combi[1][1]
        self._number_of_cards[self._current_player] -= combi[1][1]

        # Wunsch erfüllt?
        assert self._wish == 0 or -2 >= self._wish >= -14 or 2 <= self._wish <= 14
        if self._wish > 0 and is_wish_in(self._wish, combi[0]):
            assert CARD_MAH in self._played_cards
            self._wish = -self._wish

        # Stich aktualisieren
        self._trick_player = self._current_player
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
        if self._number_of_cards[self._current_player] == 0:
            self._number_of_players -= 1
            assert 1 <= self._number_of_players <= 3
            if self._number_of_players == 3:
                assert self._winner == -1
                self._winner = self._current_player
            elif self._number_of_players == 2:
                assert 0 <= self._winner <= 3
                if (self._current_player + 2) % 4 == self._winner:  # Doppelsieg?
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
        assert self._trick_player != -1
        assert self._trick_player == self._current_player
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
                assert opponent in ((1, 3) if self._trick_player in (0, 2) else (0, 2))
                assert CARD_DRA in self._played_cards
                assert self._gift == -1
                self._gift = opponent
                self._points[opponent] += self._trick_points
                assert -25 <= self._points[opponent] <= 125
            else:
                # Selbst kassieren
                self._points[self._trick_player] += self._trick_points
                assert -25 <= self._points[self._trick_player] <= 125

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

        self._trick_player = -1
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

    # Nächsten Spieler auswählen
    def step(self):
        assert not self._is_done
        assert 0 <= self._current_player <= 3
        if self._trick_figure == FIGURE_DOG and self._trick_player == self._current_player:
            self._current_player = (self._current_player + 2) % 4
        else:
            self._current_player = (self._current_player + 1) % 4

    # Spieler der am Zug ist (-1, falls noch kein Startspieler feststeht)
    @property
    def current_player(self) -> int:  # pragma: no cover
        return self._current_player

    # Spieler, der den Mahjong hat oder hatte (-1 == steht noch nicht fest)
    @property
    def start_player(self) -> int:  # pragma: no cover
        return self._start_player

    # Anzahl der Handkarten aller Spieler
    @property
    def number_of_cards(self) -> Tuple[int]:  # pragma: no cover
        return tuple(self._number_of_cards)

    # Anzahl Spieler, die noch im Rennen sind
    @property
    def number_of_players(self) -> int:  # pragma: no cover
        return self._number_of_players

    # bereits gespielte Karten
    @property
    def played_cards(self) -> Tuple[tuple]:  # pragma: no cover
        return tuple(self._played_cards)

    # Nicht gespielte Karten (in aufsteigender Reihenfolge)
    @property
    def unplayed_cards(self) -> Tuple[tuple]:  # pragma: no cover
        return tuple(other_cards(self._played_cards))

    # Ansagen aller Spieler (0 == keine Ansage, 1 == kleines Tichu, 2 == großes Tichu)
    @property
    def announcements(self) -> Tuple[int]:  # pragma: no cover
        return tuple(self._announcements)

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
    def trick_player(self) -> int:  # pragma: no cover
        return self._trick_player

    # Typ, Länge, Wert des aktuellen Stichs ((0,0,0), falls kein Stich liegt)
    @property
    def trick_figure(self) -> tuple:  # pragma: no cover
        return self._trick_figure

    # Punkte des aktuellen Stichs
    @property
    def trick_points(self) -> int:  # pragma: no cover
        return self._trick_points

    # Stich-Zähler (nur für statistische Zwecke)
    @property
    def trick_counter(self) -> int:  # pragma: no cover
        return self._trick_counter

    # Punktestand der aktuellen Runde
    @property
    def points(self) -> Tuple[int]:  # pragma: no cover
        return tuple(self._points)

    # Aktuelle Punkte für Team A (Spieler 0 und 2) und Team B (Spieler 1 und 3)
    @property
    def points_per_team(self) -> Tuple[int]:
        return tuple([self._points[0] + self._points[2], self._points[1] + self._points[3]])

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
    def score(self) -> Tuple[int]:  # pragma: no cover
        return tuple(self._score)

    # Spielverlauf = [(player, combi), ...]
    @property
    def history(self) -> Tuple[tuple]:  # pragma: no cover
        return tuple(self._history)


class PrivateState:
    def __init__(self, player: int, hand=(), schupfed=(), combinations=(), partitions=(), partitions_aborted=True, moves=0):
        self._player: int = player  # Nummer des Spielers (zw. 0 und 3)
        # Private Observation Space:
        self._hand: List[tuple] = list(hand)  # Handkarten, absteigend sortiert, z.B. [(8,3),(2,4),(0,1)]
        self._schupfed: List[tuple] = list(schupfed)  # Schupf-Karte für rechten Gegner, Partner und linken Gegner
        self.__combinations: List[tuple] = list(combinations)  # Kombinationsmöglichkeiten der Hand (wird erst berechnet, wenn benötigt)
        self.__partitions: List[List[tuple]] = list(partitions)  # mögliche Partitionen (wird erst berechnet, wenn benötigt)
        self._partitions_aborted: bool = partitions_aborted  # True, wenn nicht alle möglichen Partitionen berechnet worden sind
        self._moves: int = moves  # Wie oft war der Spieler am Zug?  # todo raus, damit bei Passen sich der Status nicht ändert

    # Alles für eine neue Runde zurücksetzen
    def reset(self):  # pragma: no cover
        self._hand = []
        self._schupfed = []
        self.__combinations = []
        self.__partitions = []
        self._partitions_aborted = True
        self._moves = 0

    def copy(self) -> 'PrivateState':
        return PrivateState(player=self._player,
                            hand=self._hand,
                            schupfed=self._schupfed,
                            combinations=self.__combinations,
                            partitions=self.__partitions,
                            partitions_aborted=self._partitions_aborted,
                            moves=self._moves)

    # Status als eindeutigen String
    def to_string(self) -> str:
        return f'{self._player}{self._hand}{self._schupfed}{self._moves}'

    def print_board(self):
        print(f'Player {self._player}: {stringify_cards(self._hand)}; Schupfed: {self._schupfed}; Moves: {self._moves}')
        print()

    # Handkarten für eine neue Runde aufnehmen (und Tichu sagen, wenn man möchte)
    # n: Anzahl Karten (8 oder 14)
    def take_cards(self, cards: List[tuple]):  # todo Parameter als Tuple
        n = len(cards)
        assert n == 8 or n == 14
        self._hand = cards
        self._schupfed = []
        self.__combinations = []
        self.__partitions = []

    # Karten an die Mitspieler abgeben (schweigend, d.h., Tichu darf man jetzt nicht sagen!))
    # schupfed: Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner (d.h. kanonische Anordnung)
    # return: Karten für Spieler 0 bis 3 (der eigene Spieler kriegt nichts, also None)
    def schupf(self, schupfed: Tuple[tuple]) -> List[tuple]:  # todo Parameter als Tuple
        # Karten abgeben
        assert len(schupfed) == 3
        self._schupfed = schupfed
        assert len(self._hand) == 14
        self._hand = [card for card in self._hand if card not in self._schupfed]
        self.__combinations = []
        self.__partitions = []
        assert len(self._hand) == 11
        cards = [None, None, None, None]
        for i in range(0, 3):
            cards[(self._player + i + 1) % 4] = self._schupfed[i]
        return cards

    # Schupf-Karten der Mitspieler aufnehmen (auch schweigend!)
    # cards: die Schupf-Karten der Spieler 0 bis 3 (None steht für keine Karte; eigener Spieler)
    def take_schupfed_cards(self, cards: List[tuple]):   # todo Parameter als Tuple
        assert len(self._hand) == 11
        assert not set(cards).intersection(self._hand)  # darf keine Schnittmenge bilden
        self._hand += [card for card in cards if card is not None]
        self._hand.sort(reverse=True)
        self.__combinations = []
        self.__partitions = []
        assert len(self._hand) == 14

    # Kombination ausspielen (oder passen)
    # combi: Ausgewählte Kombination (Karten, (Typ, Länge, Wert))
    def play(self, combi: tuple):
        self._moves += 1
        if combi[1] != FIGURE_PASS:
            # Handkarten aktualisieren
            self._hand = [card for card in self._hand if card not in combi[0]]
            if self.__combinations:
                # das Entfernen der Kombinationen ist im Schnitt ca. 1,25 mal schneller als neu zu berechnen
                self.__combinations = remove_combinations(self.__combinations, combi[0])
            if self.__partitions:
                if self._partitions_aborted:
                    # Die Berechnung aller Partitionen wurde abgebrochen, da es zu viele gibt. Daher kann die Liste
                    # nicht aktualisiert werden, sondern muss neu berechnet werden.
                    self.__partitions = []
                # das ist schneller, als alle Partitionen erneut zu berechnen
                self.__partitions = remove_partitions(self._partitions, combi[0])

    # Nummer des Spielers
    @property
    def player(self) -> int:  # pragma: no cover
        return self._player

    # Nummer des Partners
    @property
    def partner(self) -> int:  # pragma: no cover
        return (self._player + 2) % 4

    # Nummer des rechten Gegners
    @property
    def opponent_right(self) -> int:  # pragma: no cover
        return (self._player + 1) % 4

    # Nummer des linken Gegners
    @property
    def opponent_left(self) -> int:  # pragma: no cover
        return (self._player + 3) % 4

    # Handkarten, absteigend sortiert, z.B. [(8,3),(2,4),(0,1)]
    @property
    def hand(self) -> Tuple[tuple]:  # pragma: no cover
        return tuple(self._hand)

    # Anzahl Handkarten
    @property
    def number_of_cards(self) -> int:  # pragma: no cover
        return len(self._hand)

    # Schupf-Karte für rechten Gegner, Partner und linken Gegner
    @property
    def schupfed(self) -> Tuple[tuple]:  # pragma: no cover
        return tuple(self._schupfed)

    # Hat der Spieler den MahJong?
    @property
    def has_mahjong(self) -> bool:
        return CARD_MAH in self._hand

    # Kombinationsmöglichkeiten der Hand, also [(Karten, (Typ, Länge, Wert)), ...] (zuerst die besten)
    @property
    def _combinations(self) -> List[tuple]:
        if not self.__combinations and self._hand:
            self.__combinations = build_combinations(self._hand)
        return self.__combinations

    @property
    def combinations(self) -> Tuple[tuple]:  # pragma: no cover
        return tuple(self._combinations)

    # Mögliche Partitionen der Hand [[combi, combi, ...], ...] (zuerst die besten)
    @property
    def _partitions(self) -> List[List[tuple]]:
        if not self.__partitions and self._hand:
            self._partitions_aborted = not build_partitions(self.__partitions, combis=self._combinations, counter=len(self._hand))
            # reduce_partitions(self.__partitions)
        return self.__partitions

    @property
    def partitions(self) -> Tuple[List[tuple]]:  # pragma: no cover
        return tuple(self._partitions)

    @property
    def moves(self) -> int:
        return self._moves
