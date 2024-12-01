from src.lib.cards import CARD_MAH
from src.lib.combinations import build_combinations, remove_combinations, FIGURE_PASS
from src.lib.partitions import build_partitions, remove_partitions


class PrivateState:
    def __init__(self, player_index: int, hand=(), schupfed=(), combinations=(), partitions=(), partitions_aborted=True):
        self._player_index: int = player_index  # Index des Spielers (zw. 0 und 3)
        # Private Observation Space:
        self._hand: list[tuple] = list(hand)  # Handkarten, absteigend sortiert, z.B. [(8,3),(2,4),(0,1)]
        self._schupfed: list[tuple] = list(schupfed)  # abgegebene Tauschkarten (für rechten Gegner, Partner und linken Gegner)
        self._combination_cache: list[tuple] = list(combinations)  # Kombinationsmöglichkeiten der Hand (wird erst berechnet, wenn benötigt)
        self._partition_cache: list[list[tuple]] = list(partitions)  # mögliche Partitionen (wird erst berechnet, wenn benötigt)
        self._partitions_aborted: bool = partitions_aborted  # True, wenn nicht alle möglichen Partitionen berechnet worden sind

    # Alles für eine neue Runde zurücksetzen
    def reset(self):  # pragma: no cover
        self._hand = []
        self._schupfed = []
        self._combination_cache = []
        self._partition_cache = []
        self._partitions_aborted = True

    # def copy(self) -> 'PrivateState':
    #     return PrivateState(player=self._player,
    #                         hand=self._hand,
    #                         schupfed=self._schupfed,
    #                         combinations=self.__combinations,
    #                         partitions=self.__partitions,
    #                         partitions_aborted=self._partitions_aborted)

    # Handkarten für eine neue Runde aufnehmen (und Tichu sagen, wenn man möchte)
    # n: Anzahl Karten (8 oder 14)
    def take_cards(self, cards: list[tuple]):
        n = len(cards)
        assert n == 8 or n == 14
        self._hand = cards
        self._schupfed = []
        self._combination_cache = []
        self._partition_cache = []

    # Tauschkarten an die Mitspieler abgeben
    # schupfed: Tauschkarte für rechten Gegner, Karte für Partner, Karte für linken Gegner
    # return: Tauschkarten für Spieler 0 bis 3, kanonische Form (der eigene Spieler kriegt nichts, also None)
    def schupf(self, schupfed: list[tuple]) -> list[tuple]:
        # Karten abgeben
        assert len(schupfed) == 3
        self._schupfed = schupfed
        assert len(self._hand) == 14
        self._hand = [card for card in self._hand if card not in self._schupfed]
        self._combination_cache = []
        self._partition_cache = []
        assert len(self._hand) == 11
        cards = [None, None, None, None]
        for i in range(0, 3):
            cards[(self._player_index + i + 1) % 4] = self._schupfed[i]
        return cards

    # Tauschkarten der Mitspieler aufnehmen
    # cards: Tauschkarten der Spieler 0 bis 3 (None steht für keine Karte; eigener Spieler)
    def take_schupfed_cards(self, cards: list[tuple]):
        assert len(self._hand) == 11
        assert not set(cards).intersection(self._hand)  # darf keine Schnittmenge bilden
        self._hand += [card for card in cards if card is not None]
        self._hand.sort(reverse=True)
        self._combination_cache = []
        self._partition_cache = []
        assert len(self._hand) == 14

    # Kombination ausspielen (oder passen)
    # combi: Ausgewählte Kombination (Karten, (Typ, Länge, Wert))
    def play(self, combi: tuple):
        if combi[1] != FIGURE_PASS:
            # Handkarten aktualisieren
            self._hand = [card for card in self._hand if card not in combi[0]]
            if self._combination_cache:
                # das Entfernen der Kombinationen ist im Schnitt ca. 1.25-mal schneller als neu zu berechnen
                self._combination_cache = remove_combinations(self._combination_cache, combi[0])
            if self._partition_cache:
                if self._partitions_aborted:
                    # Die Berechnung aller Partitionen wurde abgebrochen, da es zu viele gibt. Daher kann die Liste
                    # nicht aktualisiert werden, sondern muss neu berechnet werden.
                    self._partition_cache = []
                # das ist schneller, als alle Partitionen erneut zu berechnen
                self._partition_cache = remove_partitions(self.partitions, combi[0])

    # Nummer des Spielers
    @property
    def player_index(self) -> int:  # pragma: no cover
        return self._player_index

    # Nummer des Partners
    @property
    def partner(self) -> int:  # pragma: no cover
        return (self._player_index + 2) % 4

    # Nummer des rechten Gegners
    @property
    def opponent_right(self) -> int:  # pragma: no cover
        return (self._player_index + 1) % 4

    # Nummer des linken Gegners
    @property
    def opponent_left(self) -> int:  # pragma: no cover
        return (self._player_index + 3) % 4

    # Handkarten, absteigend sortiert, z.B. [(8,3),(2,4),(0,1)]
    @property
    def hand(self) -> list[tuple]:  # pragma: no cover
        return self._hand

    # Anzahl Handkarten
    @property
    def number_of_cards(self) -> int:  # pragma: no cover
        return len(self._hand)

    # Abgegebene Tauschkarten (für rechten Gegner, Partner und linken Gegner)
    @property
    def schupfed(self) -> list[tuple]:  # pragma: no cover
        return self._schupfed

    # Hat der Spieler den MahJong?
    @property
    def has_mahjong(self) -> bool:
        return CARD_MAH in self._hand

    # Kombinationsmöglichkeiten der Hand, also [(Karten, (Typ, Länge, Wert)), ...] (zuerst die besten)
    @property
    def combinations(self) -> list[tuple]:
        if not self._combination_cache and self._hand:
            self._combination_cache = build_combinations(self._hand)
        return self._combination_cache

    # Mögliche Partitionen der Hand [[combi, combi, ...], ...] (zuerst die besten)
    @property
    def partitions(self) -> list[list[tuple]]:
        if not self._partition_cache and self._hand:
            self._partitions_aborted = not build_partitions(self._partition_cache, combis=self.combinations, counter=len(self._hand))
            # reduce_partitions(self.__partitions)
        return self._partition_cache
