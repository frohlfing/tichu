from src.lib.cards import stringify_cards, CARD_MAH
from src.lib.combinations import build_combinations, remove_combinations, FIGURE_PASS
from src.lib.partitions import build_partitions, remove_partitions


class PrivateState:
    def __init__(self, player: int, hand=(), schupfed=(), combinations=(), partitions=(), partitions_aborted=True, moves=0):
        self._player: int = player  # Nummer des Spielers (zw. 0 und 3)
        # Private Observation Space:
        self._hand: list[tuple] = list(hand)  # Handkarten, absteigend sortiert, z.B. [(8,3),(2,4),(0,1)]
        self._schupfed: list[tuple] = list(schupfed)  # Schupf-Karte für rechten Gegner, Partner und linken Gegner
        self.__combinations: list[tuple] = list(combinations)  # Kombinationsmöglichkeiten der Hand (wird erst berechnet, wenn benötigt)
        self.__partitions: list[list[tuple]] = list(partitions)  # mögliche Partitionen (wird erst berechnet, wenn benötigt)
        self._partitions_aborted: bool = partitions_aborted  # True, wenn nicht alle möglichen Partitionen berechnet worden sind
        self._moves: int = moves  # Wie oft war der Spieler am Zug?

    # Alles für eine neue Runde zurücksetzen
    def reset(self):  # pragma: no cover
        self._hand = []
        self._schupfed = []
        self.__combinations = []
        self.__partitions = []
        self._partitions_aborted = True
        self._moves = 0

    # def copy(self) -> 'PrivateState':
    #     return PrivateState(player=self._player,
    #                         hand=self._hand,
    #                         schupfed=self._schupfed,
    #                         combinations=self.__combinations,
    #                         partitions=self.__partitions,
    #                         partitions_aborted=self._partitions_aborted,
    #                         moves=self._moves)

    # Status als eindeutigen String
    def to_string(self) -> str:
        return f'{self._player}{self._hand}{self._schupfed}{self._moves}'

    def print_board(self):
        print(f'Player {self._player}: {stringify_cards(self._hand)}; Schupfed: {self._schupfed}; Moves: {self._moves}')
        print()

    # Handkarten für eine neue Runde aufnehmen (und Tichu sagen, wenn man möchte)
    # n: Anzahl Karten (8 oder 14)
    def take_cards(self, cards: list[tuple]):
        n = len(cards)
        assert n == 8 or n == 14
        self._hand = cards
        self._schupfed = []
        self.__combinations = []
        self.__partitions = []

    # Tauschkarten an die Mitspieler abgeben
    # schupfed: Tauschkarte für rechten Gegner, Karte für Partner, Karte für linken Gegner
    # return: Tauschkarten für Spieler 0 bis 3, kanonische Form (der eigene Spieler kriegt nichts, also None)
    def schupf(self, schupfed: list[tuple]) -> list[tuple]:
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

    # Tauschkarten der Mitspieler aufnehmen
    # cards: Tauschkarten der Spieler 0 bis 3 (None steht für keine Karte; eigener Spieler)
    def take_schupfed_cards(self, cards: list[tuple]):
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
                # das Entfernen der Kombinationen ist im Schnitt ca. 1.25-mal schneller als neu zu berechnen
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
    def hand(self) -> list[tuple]:  # pragma: no cover
        return self._hand

    # Anzahl Handkarten
    @property
    def number_of_cards(self) -> int:  # pragma: no cover
        return len(self._hand)

    # Schupf-Karte für rechten Gegner, Partner und linken Gegner
    @property
    def schupfed(self) -> list[tuple]:  # pragma: no cover
        return self._schupfed

    # Hat der Spieler den MahJong?
    @property
    def has_mahjong(self) -> bool:
        return CARD_MAH in self._hand

    # Kombinationsmöglichkeiten der Hand, also [(Karten, (Typ, Länge, Wert)), ...] (zuerst die besten)
    @property
    def _combinations(self) -> list[tuple]:
        if not self.__combinations and self._hand:
            self.__combinations = build_combinations(self._hand)
        return self.__combinations

    @property
    def combinations(self) -> list[tuple]:  # pragma: no cover
        return self._combinations

    # Mögliche Partitionen der Hand [[combi, combi, ...], ...] (zuerst die besten)
    @property
    def _partitions(self) -> list[list[tuple]]:
        if not self.__partitions and self._hand:
            self._partitions_aborted = not build_partitions(self.__partitions, combis=self._combinations, counter=len(self._hand))
            # reduce_partitions(self.__partitions)
        return self.__partitions

    @property
    def partitions(self) -> list[list[tuple]]:  # pragma: no cover
        return self._partitions

    @property
    def moves(self) -> int:
        return self._moves
