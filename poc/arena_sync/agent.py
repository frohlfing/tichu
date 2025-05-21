import config
import math
from poc.arena_sync.state import PublicState, PrivateState
from src.common.rand import Random
from src.lib.cards import Card, CARD_DOG, CARD_MAH, CARD_DRA, CARD_PHO
from src.lib.combinations import Combination, build_action_space, FIGURE_PASS, FIGURE_DOG, FIGURE_DRA, remove_combinations, FIGURE_PHO
from src.lib.partitions import partition_quality, filter_playable_partitions, filter_playable_combinations
from typing import Optional, List, Tuple
from uuid import uuid4


# Figur-Typen
PASS = 0       # Passen
SINGLE = 1     # Einzelkarte
PAIR = 2       # Paar
TRIPLE = 3     # Drilling
STAIR = 4      # Treppe
FULLHOUSE = 5  # Full House
STREET = 6     # Straße
BOMB = 7       # Vierer-Bombe oder Farbbombe

class Player:
    def __init__(self, name: str, session: Optional[str] = None):
        #: Der Name des Spielers.
        name_stripped = name.strip() if name else ""
        if not name_stripped:
            raise ValueError("Spielername darf nicht leer sein.")
        self._name: str = name_stripped
        self._session: str = session if session else str(uuid4())

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self._name}', session='{self._session}')"

    def cleanup(self):
        # Bereinigt Ressourcen dieser Instanz.
        pass

    def reset_round(self):  # pragma: no cover
        # Setzt spielrundenspezifische Werte zurück.
        pass

    def schupf(self, pub: PublicState, priv: PrivateState) -> list[tuple]:
        # Fordert den Spieler auf, drei Karten zum Schupfen auszuwählen.
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'schupf' implementieren.")

    def announce(self, pub: PublicState, priv: PrivateState, grand: bool = False) -> bool:
        # Fragt den Spieler, ob er Tichu (oder Grand Tichu) ansagen möchte.
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'announce' implementieren.")

    def combination(self, pub: PublicState, priv: PrivateState, action_space: List[Tuple[List[Card], Combination]]) -> Tuple[List[Card], Combination]:
        # Fordert den Spieler auf, eine gültige Kartenkombination auszuwählen oder zu passen.
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'combination' implementieren.")

    def wish(self, pub: PublicState, priv: PrivateState) -> int:
        # Fragt den Spieler nach einem Kartenwert-Wunsch (nach Ausspielen des Mah Jong).
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'wish' implementieren.")

    def gift(self, pub: PublicState, priv: PrivateState) -> int:
        # Fragt den Spieler, welchem Gegner der mit dem Drachen gewonnene Stich gegeben werden soll.
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'gift' implementieren.")

    @property
    def class_name(self) -> str:
        # Gibt den Klassennamen zurück (z.B. 'Client', 'Agent').
        return type(self).__name__

    @property
    def name(self) -> str:
        # Der Name des Spielers.
        return self._name


class Agent(Player):
    def __init__(self, name: Optional[str] = None, session: Optional[str] = None):
        # Generiere einen Namen, falls keiner angegeben ist.
        if name is None:
            name = f"{self.class_name}_{uuid4().hex[:8]}"  # Beispiel: "Agent_1a2b3c4d"
        # Rufe den Konstruktor der Basisklasse auf.
        super().__init__(name, session=session)
        

class RandomAgent(Agent):
    def __init__(self, name: Optional[str] = None, session: Optional[str] = None, seed: int = None):
        super().__init__(name, session=session)
        self._random = Random(seed)  # Zufallsgenerator, geeignet für Multiprocessing

    def schupf(self, pub: PublicState, priv: PrivateState) -> list[tuple]:
        hand = list(priv.hand)
        return [hand.pop(self._random.integer(0, 14)), hand.pop(self._random.integer(0, 13)), hand.pop(self._random.integer(0, 12))]

    def announce(self, pub: PublicState, priv: PrivateState, grand: bool = False) -> bool:
        return self._random.choice([True, False], [1, 19] if grand else [1, 9])

    def combination(self, pub: PublicState, priv: PrivateState, action_space: List[Tuple[List[Card], Combination]]) -> Tuple[List[Card], Combination]:
        return action_space[self._random.integer(0, len(action_space))]

    def wish(self, pub: PublicState, priv: PrivateState) -> int:
        return self._random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])

    def gift(self, pub: PublicState, priv: PrivateState) -> int:
        return priv.opponent_right if self._random.boolean() else priv.opponent_left


class HeuristicAgent(Agent):
    def __init__(self, seed=None):
        super().__init__(seed)
        self.__statistic: dict = {}  # Statistische Häufigkeit der Kombinationen (wird erst berechnet, wenn benötigt)
        self._statistic_key: tuple = ()  # Spieler und Anzahl Handkarten, für die die Statistik berechnet wurde
        self._random = Random(seed)  # Zufallsgenerator, geeignet für Multiprocessing

    def reset(self):
        self.__statistic = {}
        self._statistic_key = ()

    # Return random integers from low (inclusive) to high (exclusive).
    def _rand(self, a, b):
        return self._random.integer(a, b)
    
    # Welche Karten an die Mitspieler abgeben?
    # return: Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner (d.h. kanonische Anordnung)
    def schupf(self, pub: PublicState, priv: PrivateState) -> tuple:
        schupfed = [None, None, None]
        for i in [2, 1, 3]:  # erst die Karte für den Partner aussuchen, dann für die Gegner
            p = (priv.player_index + i) % 4  # Index in kanonische Form
            preferred = []  # Karten, die zum Abgeben in Betracht kommen
            if i == 2:  # Partner
                if pub.announcements[priv.player_index] > pub.announcements[p]:
                    # Ich hab ein größeres Tichu angesagt als mein Partner.
                    # Wenn möglich kriegt der Partner den Hund zugeschoben.
                    if CARD_DOG in priv.hand:
                        preferred = [CARD_DOG]
                    # Ansonsten kriegt der Partner eine Karte bis 10
                    max_value = 10  # Höchster Kartenwert, der zur Abgabe in Betracht kommt
                    while not preferred:
                        preferred = [(v, c) for v, c in priv.hand if c > 0 and v <= max_value]
                        if not preferred:
                            assert max_value < 14, 'Keine Schupfkarte für den Partner gefunden.'
                            max_value += 1  # wir müssen wohl höherwertige Karten in Betracht ziehen
                elif pub.announcements[p] > pub.announcements[priv.player_index]:
                    # Mein Partner hat ein größeres Tichu angesagt als ich.
                    # Wenn möglich kriegt der Partner den Phönix, Drachen, Mah Jong oder ein As.
                    v = priv.hand[0][0]  # die Handkarten sind absteigend sortiert; die erste ist die beste
                    if v == 1 or v >= 14:
                        preferred = [priv.hand[0]]
                    # Ansonsten kriegt der Partner eine Karte ab Bube
                    min_value = 11  # Bube
                    while not preferred:
                        preferred = [(v, c) for v, c in priv.hand if c > 0 and v >= min_value]
                        if not preferred:
                            assert min_value > 2, 'Keine Schupfkarte für den Partner gefunden.'
                            min_value -= 1  # wir müssen wohl niederwertige Karten in Betracht ziehen
                else:  # Weder ich noch mein Partner haben ein Tichu angesagt.
                    preferred = list(priv.hand)  # Alle Handkarten werden betrachtet.
            else:  # Gegner
                # Der Gegner kriegt den Hund, sofern vorhanden (aber nur, wenn mein Partner kein Tichu angesagt hat)
                if CARD_DOG in priv.hand and CARD_DOG not in schupfed and not pub.announcements[2]:
                    if pub.announcements[p] or (i == 3):  # bevorzugt derjenige, der ein Tichu angekündigt hat
                        preferred = [CARD_DOG]
                # Ansonsten kriegt der Gegner eine Karte bis 10
                max_value = 10  # Höchster Kartenwert, der zur Abgabe in Betracht kommt
                while not preferred:
                    preferred = [(v, c) for v, c in priv.hand if c > 0 and v <= max_value and (v, c) not in schupfed]
                    if not preferred:
                        assert max_value < 14, 'Keine Schupfkarte für den Gegner gefunden.'
                        max_value += 1  # die Handkarten sind zu gut; es müssen höhere Karten in Betracht gezogen werden

            # Aus den bevorzugten Karten diejenige auswählen, die in möglichst wenig guten Kombis gespielt werden kann.
            length = len(preferred)
            if length > 1:
                # Zuerst sind die besseren Kombis aufgelistet. Wir durchlaufen die Liste bis zu den hohen Paaren (wenn
                # wir ein Tichu angesagt haben, durchlaufen wir alle Paare und halten erst bei den Einzelkarten an).
                # Wir verwerfen dabei alle bevorzugten Karten, die in den Kombinationen benötigt werden, solange bis
                # wir nur noch eine bevorzugte Karte haben.
                for cards, (t, n, v) in priv.combinations:
                    if (not pub.announcements[priv.player_index] and t == PAIR and v < 7) or t == SINGLE:
                        break
                    if length - n >= 1:
                        for card in cards:
                            if card in preferred:
                                preferred.remove(card)
                                length -= 1
                        if length == 1:
                            break

            # Falls mehrere Karten zur Auswahl stehen, entscheidet der Zufall.
            schupfed[i - 1] = preferred[self._rand(0, length)]

        return tuple(schupfed)

    # Tichu ansagen?
    def announce(self, pub: PublicState, priv: PrivateState, grand: bool = False) -> bool:
        if sum(pub.announcements) > 0:
            announcement = False  # Falls ein Mitspieler ein Tichu angesagt hat, sagen wir nichts an!
        else:
            # Mindestwert für die Güte einer guten Partition
            min_q = config.HEURISTIC_TICHU_QUALITY[int(grand)]

            # Falls wir am Zug sind, spielbare Kombinationen ermitteln (ansonsten ist der Aktionsraum leer)
            my_turn = pub.current_player_index == priv.player_index or (pub.start_player_index == -1 and CARD_MAH in priv.hand)
            # noinspection PyTypeChecker
            action_space = build_action_space(priv.combinations, pub.trick_figure, pub.wish) if my_turn else []

            # Kürzeste Partition bewerten
            len_min = 14
            shortest_partition = []
            for partition in priv.partitions:
                n = len(partition)
                if len_min >= n:
                    len_min = n
                    shortest_partition = partition
            q = partition_quality(shortest_partition, action_space if my_turn else [], self._statistic(pub, priv))
            announcement = q >= min_q
        return announcement

    # Welche Kombination soll gespielt werden?
    # action_space: Mögliche Kombinationen (inklusiv Passen; Passen steht an erster Stelle)
    # return: Ausgewählte Kombination (Karten, (Typ, Länge, Wert))
    def combination(self, pub: PublicState, priv: PrivateState, action_space: List[tuple]) -> tuple:
        action_len = len(action_space)
        assert action_len > 0
        if action_len == 1:
            return action_space[0]  # es gibt nur diese mögliche Aktion

        can_skip = action_space[0][1] == FIGURE_PASS
        partner = priv.partner
        opp_right = priv.opponent_right
        opp_left = priv.opponent_left

        # Ist noch keiner fertig geworden und hab ich ein größeres Tichu angesagt als die anderen? Oder der Partner?
        a = pub.announcements
        has_tichu = pub.winner == -1 and a[priv.player_index] > max(a[partner], a[opp_right], a[opp_left])
        has_partner_tichu = pub.winner == -1 and a[partner] > max(a[priv.player_index], a[opp_right], a[opp_left])

        # Kann der rechte Gegner im nächsten Zug seine restlichen Karten ablegen?
        trick_len = pub.trick_figure[2]
        right_opp_can_win = 0 < pub.number_of_cards[opp_right] < 6 and pub.number_of_cards[opp_right] == trick_len

        # Können und wollen wir fertig werden?
        for cards, figure in action_space:
            if figure[1] == pub.number_of_cards[priv.player_index]:
                # Wir könnten alle restlichen Karten ablegen.
                if has_partner_tichu and not right_opp_can_win and can_skip:
                    # Der Partner hat ein Tichu angesagt und der rechte Gegner kann nicht fertig werden.
                    return action_space[0]  # Wir passen, damit der Partner eine Chance hat, als erstes fertig zu werden.
                return cards, figure  # wir legen alle Handkarten ab

        # Können und wollen wir passen, damit der Partner den Stich bekommt?
        if pub.trick_player_index == partner and can_skip:
            # Der Partner hat den Stich und wir könnten passen
            if not has_tichu and not right_opp_can_win and pub.number_of_cards[partner] > 0:
                # Wir haben kein Tichu angesagt und der Gegner kann nicht gewinnen und der Partner hat noch Karten.
                return action_space[0]  # Wir passen (bzw. machen nichts), um den Partner nicht zu überstechen.

        # Können und wollen wir den Hund ausspielen?
        for cards, figure in action_space:
            if figure == FIGURE_DOG:
                return cards, figure  # wir spielen den Hund so bald wie möglich

        # Wir suchen zuerst die Partitionen, die mindestens eine spielbare Kombination haben. Damit vermeiden wir das
        # Passen, neben aber in Kauf, dass evtl. eine Bombe, Straße, Fullhouse oder Treppe auseinander gerissen wird.
        partitions = filter_playable_partitions(priv.partitions, action_space)
        if not partitions:  # pragma: no cover
            # Anscheinend hat build_partitions() alle Partitionen abgeschnitten, die jetzt passen würden.
            # Als Fallback bilden wir für jede gültige Aktion eine neue Partition, die neben der jeweiligen Aktion
            # nur aus Einzel-Kombinationen besteht.
            for cards, figure in action_space:
                singles = [([card], (SINGLE, 1, card[0])) for card in priv.hand if card not in cards]
                partitions.append([(cards, figure)] + singles)

        # Als Zweites suchen wir die kürzeste Partition, da wir mit dieser vermutlich am schnellsten fertig werden.
        # Eine Bombe bleibt meistens in der Auswahl. Eine Straße könnte aber eine kürzere Partition bilden, sodass
        # in diesem Fall die Bombe auseinander gerissen wird.
        len_min = 14
        for partition in partitions:
            len_min = min(len_min, len(partition))
        partitions = [partition for partition in partitions if len(partition) == len_min]

        # Als Drittes suchen wir die Partitionen mit der besten Güte, d.h., mit der wir statistisch gesehen am
        # schnellsten fertig werden.
        best_partition = partitions[0]
        if len(partitions) > 1:
            q_max = -math.inf
            for partition in partitions:
                q = partition_quality(partition, action_space, self._statistic(pub, priv))
                if q_max < q:
                    q_max = q
                    best_partition = partition

        # Wir haben uns für eine Partition entschieden! Jetzt schauen wir uns die spielbaren Kombinationen in dieser
        # Partition genauer an.
        combis = filter_playable_combinations(best_partition, action_space)

        # Falls wir eine Bombe haben, dann schmeißen wir die Bombe nur, wenn
        #  - wir Schluss machen können
        #  - oder der Gegner evtl. Schluss machen könnte
        #  - oder wenn die Gegner viele Punkte kriegen würden.
        #  Voraussetzung ist aber, dass wir dem Partner nicht sein Tichu versauen (sofern er ein Tichu angesagt hat).
        for cards, (t, n, v) in priv.combinations:
            if t == BOMB:
                # Können wir Schluss machen (haben wir nur noch max. 2 Kombinationen)?
                could_win = len(best_partition) <= 2
                # Hat der Gegner, der an der Reihe ist, weniger als 6 Handkarten?
                m = pub.number_of_cards[pub.current_player_index]
                opp_could_win = pub.current_player_index in (opp_right, opp_left) and m < 6
                # Würden die Gegner 40 Punkte oder mehr kriegen?
                b1 = pub.trick_player_index in (priv.player_index, partner) and pub.trick_figure == FIGURE_DRA
                b2 = pub.trick_player_index in (opp_right, opp_left) and pub.trick_figure != FIGURE_DRA
                opp_win_trick = pub.trick_points >= 40 and (b1 or b2)
                # Ist mindestens ein Kriterium erfüllt?
                if could_win or opp_could_win or opp_win_trick:
                    # Vermasseln wir auch nicht das Tichu des Partners, in dem wir schluss machen?
                    if not has_partner_tichu or not could_win:
                        return cards, (t, n, v)  # wir schmeißen die Bombe
                # Die Kriterien sind nicht erfüllt. Wir nehmen die Bombe aus unserer Wahl, falls noch andere Aktionen
                # möglich sind.
                not_bombs = remove_combinations(combis, cards)
                if not_bombs:
                    combis = not_bombs
                elif can_skip:
                    return action_space[0]  # Wir passen

        # Falls nur noch eine Kombination übrig bleibt, nehmen wir diese!
        assert combis, 'Zu viele Kombinationen aus der Auswahl entfernt'
        if len(combis) == 1:
            return combis[0]

        # Wir haben jetzt die Qual der Wahl. Nehmen wir eine Kombi, die wir sonst schlechter loswerden würden oder eine
        # Kombi, mit der wir vermutlich den Stich gewinnen und wieder das Anspielrecht bekommen?
        # Wir gewichten unsere Wahl anhand der Punkte, die im Stich liegen.
        if pub.trick_points < 0:
            trick_sum = 0.0  # 0 Punkte oder weniger werten wir mit 0  # pragma: no cover
        elif pub.trick_points > 40:
            trick_sum = 1.0  # und ab 40 Punkte mit 1  # pragma: no cover
        else:
            trick_sum = pub.trick_points / 40  # Punkte des aktuellen Stichs normiert auf den Bereich [0, 1]

        # Ein niedriger Lo-Anteil bedeutet, dass wir die Kombi schlecht abwerfen können.
        # Je weniger Punkte im Stich sind, desto eher sollten wir die Gelegenheit nutzen, diese Kombi loszuwerden.
        # weight_lo = (1 - lo_opp - lo_par) * (1 - v)
        #
        # Ein niedriger Hi-Anteil bedeutet, dass wir eher den Stich gewinnen, da die Mitspieler weniger höherwertige
        # Kombis haben. Je mehr Punkte im Stich sind, desto eher sollten wir diese Kombis einsetzen.
        # weight_hi = (1 - hi_opp - hi_par) * v
        #
        # Es gilt, die Kombi mit dem größten weight zu finden, alternativ das kleinste lost:
        # weight = weight_lo + weight_hi
        # lost = -weight = (-1 + lo_opp + lo_par) * (1 - v)        + (-1 + hi_opp + hi_par) * v
        #                = (-1 + v) + (lo_opp + lo_par) * (1 - v)  + -v + (hi_opp + hi_par) * v
        #                = (lo_opp + lo_par) * (1 - v) + (hi_opp + hi_par) * v + (-1 + v) - v
        #                = (lo_opp + lo_par) * (1 - v) + (hi_opp + hi_par) * v - 1
        #
        # Die Konstante -1 können wir für den Minimum-Vergleich ignorieren.
        statistic = self._statistic(pub, priv)
        best_combi = combis[0]
        lost_min = math.inf
        for combi in combis:
            lo_opp, lo_par, hi_opp, hi_par, eq_opp, hi_par = statistic[tuple(combi[0])]
            v = trick_sum if combi[1] != FIGURE_DRA else -trick_sum
            lost = (lo_opp + lo_par) * (1 - v) + (hi_opp + hi_par) * v
            if lost_min > lost:
                lost_min = lost
                best_combi = combi
        return best_combi

    # Welcher Kartenwert wird gewünscht?
    # return: Wert zw. 2 und 14
    def wish(self, pub: PublicState, priv: PrivateState) -> int:
        values = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]

        t, n, value = pub.trick_figure
        if t == STREET:
            # Wenn eine Straße gespielt wurde, wird Junge, Dame, König oder As bevorzugt, da diese für den Gegner
            # besser als Einzelkarte, Paar oder Drilling zu verwenden wäre.
            preferred = [v for v in range(2, 15) if v > 10 and v > value]
        else:
            # Ansonsten werden Werte bevorzugt, die sich noch vollständig in den Händen der Mitspieler befinden und
            # nicht an den Partner geschoben wurde. Das verringert das Bombenrisiko etwas.
            preferred = []
            excl = priv.hand + pub.played_cards + list(priv.schupfed[1])
            for v in range(2, 15):
                if (v, 1) not in excl and (v, 2) not in excl and (v, 3) not in excl and (v, 4) not in excl:
                    preferred.append(v)
        if preferred:
            values = preferred

        # Wert bevorzugen, der an den nachfolgenden Gegner geschoben wurde. So mobben wir unseren Partner nicht.
        value, color = priv.schupfed[0]
        if value in values:
            values = [value]

        wish = values[self._rand(0, len(values))]
        assert 2 <= wish <= 14, 'Der Wunsch muss zw. 2 und 14 (As) liegen.'
        return wish

    # Welcher Gegner soll den Drachen bekommen?
    # return: Nummer des Gegners
    def gift(self, pub: PublicState, priv: PrivateState) -> int:
        # Der Spieler mit den meisten Handkarten kriegt den Drachen.
        right = pub.number_of_cards[priv.opponent_right]
        left = pub.number_of_cards[priv.opponent_left]
        if right > left:
            opp = priv.opponent_right
        elif right < left:
            opp = priv.opponent_left
        else:
            opp = priv.opponent_right if self._rand(0, 2) == 1 else priv.opponent_left
        return opp

    # Wahrscheinlichkeit, dass die Mitspieler eine bestimmte Kombination anspielen bzw. überstechen können
    def _statistic(self, pub: PublicState, priv: PrivateState) -> dict:
        key = (priv.player_index, priv.hand, pub.number_of_cards)
        if self._statistic_key != key:
            self._statistic_key = key
            self.__statistic = calc_statistic(priv.player_index, priv.hand, priv.combinations, pub.number_of_cards, pub.trick_figure, pub.unplayed_cards)
        return self.__statistic


# Wahrscheinlichkeit berechnen, dass die Mitspieler eine bestimmte Kombination anspielen bzw. überstechen können
# Für jede eigene Kombination liefert die Funktion folgende Werte:
# lo_opp: Wahrscheinlichkeit, das der Gegner eine Kombination hat, die ich stechen kann und somit das Anspiel gewinne
# lo_par: Wahrscheinlichkeit, das der Partner eine Kombination hat, die ich stechen kann und somit das Anspiel gewinne
# hi_opp: Wahrscheinlichkeit, das der Gegner eine höherwertige Kombination hat und das Anspiel verliere
# hi_par: Wahrscheinlichkeit, das der Partner eine höherwertige Kombination hat und das Anspiel verliere
# eq_opp: Wahrscheinlichkeit, dass der Gegner eine gleichwertige Kombinationen hat
# eq_par: Wahrscheinlichkeit, dass der Partner eine gleichwertige Kombinationen hat
# Daraus folgt:
# 1 - lo_opp - hi_opp - eq_opp: Wahrscheinlichkeit, dass der Gegner nicht die die Kombi vom gleichen Typ und Länge hat
# 1 - lo_par - hi_par - eq_par: Wahrscheinlichkeit, dass der Partner nicht die die Kombi vom gleichen Typ und Länge hat
# Diese Parameter werden erwartet:
# player: Meine Spielernummer (zw. 0 und 3)
# hand: Eigene Handkarten
# combis: Zu bewertende Kombinationen (gebildet aus den Handkarten) [(Karten, (Typ, Länge, Wert)), ...]
# number_of_cards: Anzahl der Handkarten aller Spieler.
# trick_figure: Typ, Länge, Wert des aktuellen Stichs ((0,0,0), falls kein Stich liegt)
# unplayed_cards: Noch nicht gespielte Karten
def calc_statistic(player: int, hand: List[tuple], combis: List[tuple], number_of_cards: List[int], trick_figure: tuple, unplayed_cards: List[tuple]) -> dict:
    assert hand  # wir haben bereits bzw. noch Karten auf der Hand
    assert len(hand) == number_of_cards[player]

    if sum(number_of_cards) != len(unplayed_cards):
        # die Karten werden gerade verteilt bzw. es wird geschupft!
        m = len(hand)
        assert m in (0, 8, 11, 14)
        assert len(unplayed_cards) == 56
        n = int((56 - m) / 3)
        number_of_cards = [n, n, n, n]  # wir tun so, als wenn alle Karten bereits verteilt sind
        number_of_cards[player] = m

    # Anzahl der ungespielten Karten (die eigenen Handkarten werden hier nicht mitgezählt)
    #  Dog Mah 2  3  4  5  6  7  8  9 10 Bu Da Kö As Dra
    c = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # rot oder Sonderkarte
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # grün
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # blau
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]   # schwarz
    ]
    phoenix = False
    for card in unplayed_cards:
        if card not in hand:
            if card == CARD_DOG:
                c[0][0] = 1
            elif card == CARD_MAH:
                c[0][1] = 1
            elif card == CARD_DRA:
                c[0][15] = 1
            elif card == CARD_PHO:
                phoenix = True
            else:
                c[card[1]-1][card[0]] = 1

    # Anzahl der ungespielten Karten gesamt (ohne die eigenen Handkarten)
    sum_c = len(unplayed_cards) - len(hand)

    # Anzahl Kombinationen pro Typ (Single/1 bis Bombe/7)
    #           1   2   3   4   5   6   7
    d = [None, [], [], [], [], [], [], []]

    # Anzahl Einzelkarten gesamt  (d[SINGLE][1][15] == Drache, d[SINGLE][1][16] == Phönix)
    d[SINGLE] = [None, [c[0][v] + c[1][v] + c[2][v] + c[3][v] for v in range(16)] + [int(phoenix)]]

    # Paare, Drillinge und Fullhouse (zunächst ohne Phönix)
    d[PAIR] = [None, None, [6 if d[SINGLE][1][v] == 4 else 3 if d[SINGLE][1][v] == 3 else 1 if d[SINGLE][1][v] == 2 else 0 for v in range(15)]]
    d[TRIPLE] = [None, None, None, [4 if d[SINGLE][1][v] == 4 else 1 if d[SINGLE][1][v] == 3 else 0 for v in range(15)]]
    sum_pairs = sum(d[PAIR][2])
    d[FULLHOUSE] = [None, None, None, None, None, [d[TRIPLE][3][v] * (sum_pairs - d[PAIR][2][v]) for v in range(15)]]

    # Treppen   0     1     2     3    4    5    6    7    8    9   10   11   12   13   14 Karten
    d[STAIR] = [None, None, None, None, [], None, [], None, [], None, [], None, [], None, []]
    for k in range(7, 1, -1):  # Anzahl Paare in der Treppe (7 bis 2)
        n = k * 2  # Anzahl Karten in der Treppe
        # Wert         0  1  2  3  4  5  6  7  8  9 10 11 12 13 14
        d[STAIR][n] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        for v in range(k + 1, 15):  # höchstes Paar (=Wert der Kombination)
            phoenix_available = phoenix
            counter = 1
            for i in range(k):  # Anzahl Paare
                if phoenix_available and not d[PAIR][2][v - i]:
                    phoenix_available = False  # Fehlendes Paar mit Einzelkarte und Phönix ersetzen
                    counter *= d[SINGLE][1][v - i]
                else:
                    counter *= d[PAIR][2][v - i]
            if phoenix_available and counter:
                counter_without_phoenix = counter  # Anzahl Kombinationsmöglichkeiten ohne Phönix
                for i in range(k):  # jede Karte mit dem Phönix ersetzten und zu den Möglichkeiten dazuzählen
                    if d[PAIR][2][v - i]:
                        counter += int(counter_without_phoenix / d[PAIR][2][v - i]) * 2
            d[STAIR][n][v] = counter

    # Paare, Drillinge und Fullhouse mit Phönix
    if phoenix:
        counter = 0
        sum_singles = sum(d[SINGLE][1][:16])  # Anzahl Karten ohne Phönix
        for v in range(2, 15):
            # fullhouse = # Drilling + Einzelkarte + Phönix
            # Ausnahmeregel: Der Drilling darf nicht vom gleichen Wert sein wie die Einzelkarte.
            d[FULLHOUSE][5][v] += d[TRIPLE][3][v] * (sum_singles - d[SINGLE][1][v])
            # fullhouse = Paar1 + Phönix + Paar2
            # Bedingung: Paar1 ist größer als Paar2 (man würde immer den Phönix zum höherwertigen Pärchen sortieren)
            d[FULLHOUSE][5][v] += d[PAIR][2][v] * counter
            counter += d[PAIR][2][v]
            d[TRIPLE][3][v] += d[PAIR][2][v]  # Drilling mit Phönix = Paar + Phönix
            d[PAIR][2][v] += d[SINGLE][1][v]  # Paar mit Phönix = Einzelkarte + Phönix

    # Bomben     0     1     2     3    4   5   6   7   8   9  10  11  12  13 Karten
    d[BOMB] = [None, None, None, None, [], [], [], [], [], [], [], [], [], []]
    # 4er-Bomben
    d[BOMB][4] = [1 if d[SINGLE][1][v] == 4 else 0 for v in range(15)]
    # Straßenbomben
    for n in range(5, 14):  # Anzahl Karten in der Straßenbombe  (5 bis 13)
        bombs0 = [4 if v > n else 0 for v in range(15)]  # Werte 0 bis As
        for v in range(n + 1, 15):  # höchste Karte (=Wert der Kombination)
            for color in range(4):
                for i in range(n):
                    if c[color][v - i] == 0:
                        bombs0[v] -= 1
                        break
        d[BOMB][n] = bombs0

    # Straßen    0     1     2     3     4    5   6   7   8   9  10  11  12  13  14 Karten
    d[STREET] = [None, None, None, None, None, [], [], [], [], [], [], [], [], [], []]
    for n in range(14, 4, -1):  # Anzahl Karten in der Straße (14 bis 5)
        # Wert        0  1  2  3  4  5  6  7  8  9 10 11 12 13 14
        d[STREET][n] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        for v in range(n, 15):  # höchste Karte (=Wert der Kombination)
            phoenix_available = phoenix
            counter = 1
            for i in range(n):
                if phoenix_available and not d[SINGLE][1][v - i] and (i < n - 1 or v == 14):
                    phoenix_available = False  # Lücke mit Phönix ersetzten (nur nicht ganz hinten, wenn vorne noch Platz wäre)
                else:
                    counter *= d[SINGLE][1][v - i]
            if phoenix_available and counter:
                counter_without_phoenix = counter  # Anzahl Kombinationsmöglichkeiten ohne Phönix
                for i in range(n):  # jede Karte mit dem Phönix ersetzten und zu den Möglichkeiten dazuzählen
                    counter += int(counter_without_phoenix / d[SINGLE][1][v - i])
            d[STREET][n][v] = counter

    # Wir wissen nun die Anzahl Kombinationen, die mit allen Handkarten der anderen Spieler zusammen gebildet
    # werden können. Als Nächstes berechnen wir die statistische Häufigkeit der Kombinationen auf der Hand der
    # einzelnen Mitspieler.

    # Wahrscheinlichkeit, dass die Mitspieler eine Kombination mit bestimmter Länge auf der Hand haben
    # p[0][n]+p[1][n]+p[2][n]+p[3][n] ist die Wahrscheinlichkeit, dass irgendein Mitspieler eine Kombi mit n Karten hat.
    # 1 - (p[0][n]+p[1][n]+p[2][n]+p[3][n]) ist die Wahrscheinlichkeit, das kein Mitspieler eine Kombi mit n Karten hat.
    #       0  1  2  3  4  5  6  7  8  9 10 11 12 13 14  Kombi-Länge n
    p = [
        [None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Spieler 0
        [None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Spieler 1
        [None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Spieler 2
        [None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]   # Spieler 3
    ]
    if sum_c > 0:
        for i in range(4):  # Mitspieler
            if i == player:
                p[i] = None  # die Wahrscheinlichkeiten für die eigenen Handkarten werden nicht benötigt
                continue
            h = number_of_cards[i]  # Anzahl Handkarten des Mitspielers i
            p[i][1] = h / sum_c  # Wahrscheinlichkeit, dass der Spieler i eine bestimmte Einzelkarte hat
            for j in range(1, min(sum_c, 14)):
                # nachdem eine Karte gezogen wurde, gibt es noch h - 1 Handkarten und sum_c - 1 ungespielte Karten
                p[i][j + 1] = p[i][j] * (h - j) / (sum_c - j)

    # Indizes der Mitspieler
    opp_right = (player + 1) % 4
    partner = (player + 2) % 4
    opp_left = (player + 3) % 4

    # Wahrscheinlichkeit, dass ein Mitspieler eine Bombe werfen kann
    p_bomb_opp = sum([sum(d[BOMB][n]) * (p[opp_right][n] + p[opp_left][n]) for n in range(4, 14)])
    p_bomb_par = sum([sum(d[BOMB][n]) * p[partner][n] for n in range(4, 14)])

    # Anzahl der möglichen Bomben auf den Händen der Mitspieler gesamt
    sum_bombs = sum([sum(d[BOMB][n]) for n in range(4, 14)])

    # Uns interessieren nur die Kombinationen der Mitspieler, die zu den eigenen Handkarten passen...
    statistic = {}
    for cards, figure in combis:
        t, n, v = figure

        if t == BOMB:
            # Anzahl Kombis der Mitspieler insgesamt, die hier betrachtet werden (das sind alle Kombis bis auf Hund)
            sum_combis = \
                sum([sum(d[k][m]) for k in range(1, 7) for m in range(1, len(d[k])) if d[k][m] is not None]) \
                + (0 if figure == FIGURE_DOG else sum_bombs)

            # lo = normale Kombis + kürzere Bomben + niederwertige Bomben gleicher länge
            lo_opp = \
                sum([sum(d[k][m]) * (p[opp_right][m] + p[opp_left][m]) for k in range(1, 7) for m in range(1, len(d[k])) if d[k][m] is not None]) \
                + sum([sum(d[BOMB][m]) * (p[opp_right][m] + p[opp_left][m]) for m in range(4, n)]) \
                + sum(d[BOMB][n][:v]) * (p[opp_right][n] + p[opp_left][n])
            lo_par = \
                sum([sum(d[k][m]) * p[partner][m] for k in range(1, 7) for m in range(1, len(d[k])) if d[k][m] is not None]) \
                + sum([sum(d[BOMB][m]) * p[partner][m] for m in range(4, n)]) \
                + sum(d[BOMB][n][:v]) * p[partner][n]

            # hi = längere Bomben + höherwertige Bomben gleicher länge
            hi_opp = \
                sum([sum(d[BOMB][m]) * (p[opp_right][m] + p[opp_left][m]) for m in range(n + 1, 14)]) \
                + sum(d[BOMB][n][v + 1:]) * (p[opp_right][n] + p[opp_left][n])
            hi_par = \
                sum([sum(d[BOMB][m]) * p[partner][m] for m in range(n + 1, 14)]) \
                + sum(d[BOMB][n][v + 1:]) * p[partner][n]

            # eq = gleichwertige Bomben gleicher länge
            eq_opp = d[BOMB][n][v] * (p[opp_right][n] + p[opp_left][n])
            eq_par = d[BOMB][n][v] * p[partner][n]

        else:  # keine Bombe
            # Anzahl Kombis der Mitspieler, die betrachtet werden (Kombis gleicher Länge (aber kein Hund) plus Bomben)
            sum_combis = sum(d[t][n][1:]) + (0 if figure == FIGURE_DOG else sum_bombs)

            # niederwertige Kombis (ohne Hund) - wie viele Kombinationen gibt es, die ich mit combi stechen kann?
            a = 1
            b = 15 if figure == FIGURE_PHO else v
            w = sum(d[t][n][a:b]) + (d[t][n][16] if figure == FIGURE_DRA else 0)  # Anzahl niederwertige Kombinationen
            lo_opp = (p[opp_right][n] + p[opp_left][n]) * w
            lo_par = p[partner][n] * w

            # höherwertige Kombis
            a = trick_figure[2] + 1 if figure == FIGURE_PHO else v + 1
            b = 16
            w = sum(d[t][n][a:b]) + (d[t][n][16] if t == SINGLE and figure != FIGURE_DRA else 0)  # höherwertige (ohne Bomben)
            hi_opp = (p[opp_right][n] + p[opp_left][n]) * w + (0 if figure == FIGURE_DOG else p_bomb_opp)
            hi_par = p[partner][n] * w + (0 if figure == FIGURE_DOG else p_bomb_par)

            # gleichwertige Kombis
            w = d[t][n][v]  # Anzahl gleichwertige Kombinationen
            eq_opp = (p[opp_right][n] + p[opp_left][n]) * w
            eq_par = p[partner][n] * w

        # Beim Phönix wurden die spielbaren Kombination (außer Drache) doppelt gerechnet. Das liegt daran, dass der
        # Wert vom ausgelegten Stich abhängt.
        w = sum_combis + (sum(d[t][n][(trick_figure[2] + 1):15]) if figure == FIGURE_PHO else 0)
        if w:
            # normalisieren
            lo_opp /= w
            lo_par /= w
            hi_opp /= w
            hi_par /= w
            eq_opp /= w
            eq_par /= w
            # if figure == FIGURE_PHO:
            #     assert eq_opp == 0
            #     assert eq_par == 0
            #     w = lo_opp + lo_par + hi_opp + hi_par
            #     if w > 1:
            #         lo_opp /= w
            #         lo_par /= w
            #         hi_opp /= w
            #         hi_par /= w
            # assert 0 <= lo_opp + hi_opp + eq_opp <= 1
            # assert 0 <= lo_par + hi_par + eq_par <= 1
            assert 0 <= lo_opp + lo_par + hi_opp + hi_par + eq_opp + eq_par <= 1.000001, lo_opp + lo_par + hi_opp + hi_par + eq_opp + eq_par
        else:
            assert lo_opp + lo_par + hi_opp + hi_par + eq_opp + eq_par == 0

        statistic.setdefault(tuple(cards), (lo_opp, lo_par, hi_opp, hi_par, eq_opp, eq_par))
    return statistic
