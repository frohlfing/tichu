"""
Definiert die Heuristik-Agenten.
"""

import math
from src import config
from src.common.rand import Random
from src.lib.cards import Card, Cards, CARD_DOG, CARD_MAH
from src.lib.combinations import Combination, build_action_space, remove_combinations, CombinationType
from src.lib.partitions import filter_playable_combinations, filter_playable_partitions
from src.lib.prob.statistic import calc_statistic, partition_quality
from src.players.agent import Agent
from src.private_state import PrivateState
from src.public_state import PublicState
from typing import Optional, List, Tuple


class HeuristicAgent(Agent):
    """
    Repräsentiert einen KI-gesteuerten Spieler.

    Die Entscheidungen werden aufgrund statistischer Berechnungen und Regeln aus Expertenwissen getroffen.
    """
    def __init__(self, name: Optional[str] = None, session_id: Optional[str] = None,
                 grand_quality: list[float] = config.HEURISTIC_TICHU_QUALITY, seed: int = None):
        """
        Initialisiert einen neuen Agenten.

        :param name: (Optional) Name für den Agenten. Wenn None, wird einer generiert.
        :param session_id: (Optional) Aktuelle Session des Agenten. Wenn None, wird eine Session generiert.
        :param grand_quality: (Optional) Mindestwert für die Güte bei der Tichu-Ansage (einfaches, großes).
        :param seed: (Optional) Seed für den internen Zufallsgenerator (für Tests).
        """
        super().__init__(name, session_id=session_id)
        self._quality = grand_quality
        self._random = Random(seed)  # Zufallsgenerator, geeignet für Multiprocessing
        self.__statistic: dict = {}  # Statistische Häufigkeit der Kombinationen (wird erst berechnet, wenn benötigt)
        self._statistic_key: tuple = ()  # Spieler und Anzahl von Handkarten, für die die Statistik berechnet wurde

    def reset_round(self):  # pragma: no cover
        """
        Setzt spielrundenspezifische Werte zurück.
        """
        self.__statistic = {}
        self._statistic_key = ()

    def _statistic(self, pub: PublicState, priv: PrivateState) -> dict:
        """
        Wahrscheinlichkeit, dass die Mitspieler eine bestimmte Kombination anspielen bzw. überstechen können.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Ergebnis von calc_statistic() (Package src.lib.prob.statistic)
        """
        n = pub.count_hand_cards
        key = (priv.player_index, priv.hand_cards, n)
        if self._statistic_key != key:
            self._statistic_key = key
            self.__statistic = calc_statistic(priv.player_index, priv.hand_cards, priv.combinations, n, pub.trick_combination, pub.unplayed_cards)
        return self.__statistic

    # ------------------------------------------------------
    # Entscheidungen
    # ------------------------------------------------------

    # todo u.U. die Berechnung im Thread laufen lassen, um die asynchrone Nachrichtenschleife nicht zu blockieren:
    # import asyncio
    # import time
    # from concurrent.futures import Future, ThreadPoolExecutor, ProcessPoolExecutor
    #
    # def blocking_function() -> int:
    #     # Eine blockierende Funktion, die zwei Sekunden wartet und dann 42 zurückgibt
    #     time.sleep(2)
    #     return 42
    #
    # async def combination(...):
    #   loop = asyncio.get_running_loop()
    #   with ThreadPoolExecutor() as pool:
    #       # Ausführen der blockierenden Funktion im Thread
    #       future: Future = loop.run_in_executor(pool, blocking_function)
    #       result: int = await future

    async def announce(self) -> bool:
        """
        Die Engine fragt den Spieler, ob er ein Tichu (großes oder einfaches) ansagen möchte.

        Die Engine ruft diese Methode nur auf, wenn der Spieler ein Tichu ansagen darf.
        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        :return: True, wenn ein Tichu angesagt wird, sonst False.
        """
        grand = len(self.priv.hand_cards) == 8

        if sum(self.pub.announcements) > 0:
            announcement = False  # Falls ein Mitspieler ein Tichu angesagt hat, sagen wir nichts an!
        else:
            # Mindestwert für die Güte einer guten Partition
            min_q = self._quality[int(grand)]

            # Falls wir am Zug sind, spielbare Kombinationen ermitteln (ansonsten ist der Aktionsraum leer)
            my_turn = self.pub.current_turn_index == self.priv.player_index or (self.pub.start_player_index == -1 and CARD_MAH in self.priv.hand_cards)
            action_space = build_action_space(self.priv.combinations, self.pub.trick_combination, self.pub.wish_value) if my_turn else []

            # Kürzeste Partition bewerten
            len_min = 14
            shortest_partition = []
            for partition in self.priv.partitions:
                n = len(partition)
                if len_min >= n:
                    len_min = n
                    shortest_partition = partition
            q = partition_quality(shortest_partition, action_space if my_turn else [], self._statistic(self.pub, self.priv))
            announcement = q >= min_q
        return announcement

    async def schupf(self) -> Tuple[Card, Card, Card]:
        """
        Die Engine fordert den Spieler auf, drei Karten zum Schupfen auszuwählen.

        Die Engine ruft diese Methode nur auf, wenn der Spieler noch Karten abgeben muss.
        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        :return: Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner.
        """
        schupfed: List[Optional[Card]] = [None, None, None]
        for i in [2, 1, 3]:  # erst die Karte für den Partner aussuchen, dann für die Gegner
            p = (self.priv.player_index + i) % 4  # Index in kanonischer Form
            preferred = []  # Karten, die zum Abgeben in Betracht kommen
            if i == 2:  # Partner
                if self.pub.announcements[self.priv.player_index] > self.pub.announcements[p]:
                    # Ich habe ein größeres Tichu angesagt als mein Partner.
                    # Wenn möglich kriegt der Partner den Hund zugeschoben.
                    if CARD_DOG in self.priv.hand_cards:
                        preferred = [CARD_DOG]
                    # Ansonsten kriegt der Partner eine Karte bis 10
                    max_value = 10  # Höchster Kartenwert, der zur Abgabe in Betracht kommt
                    while not preferred:
                        preferred = [(v, c) for v, c in self.priv.hand_cards if c > 0 and v <= max_value]
                        if not preferred:
                            assert max_value < 14, "Keine Schupfkarte für den Partner gefunden."
                            max_value += 1  # wir müssen wohl höherwertige Karten in Betracht ziehen
                elif self.pub.announcements[p] > self.pub.announcements[self.priv.player_index]:
                    # Mein Partner hat ein größeres Tichu angesagt als ich.
                    # Wenn möglich kriegt der Partner den Phönix, Drachen, Mah Jong oder ein As.
                    v = self.priv.hand_cards[0][0]  # die Handkarten sind absteigend sortiert; die erste ist die beste
                    if v == 1 or v >= 14:
                        preferred = [self.priv.hand_cards[0]]
                    # Ansonsten kriegt der Partner eine Karte ab Buben
                    min_value = 11  # Bube
                    while not preferred:
                        preferred = [(v, c) for v, c in self.priv.hand_cards if c > 0 and v >= min_value]
                        if not preferred:
                            assert min_value > 2, "Keine Schupfkarte für den Partner gefunden."
                            min_value -= 1  # wir müssen wohl niederwertige Karten in Betracht ziehen
                else:  # Weder ich noch mein Partner haben einen Tichu angesagt.
                    preferred = list(self.priv.hand_cards)  # Alle Handkarten werden betrachtet.
            else:  # Gegner
                # Der Gegner kriegt den Hund, sofern vorhanden (aber nur, wenn mein Partner kein Tichu angesagt hat)
                if CARD_DOG in self.priv.hand_cards and CARD_DOG not in schupfed and not self.pub.announcements[2]:
                    if self.pub.announcements[p] or (i == 3):  # bevorzugt derjenige, der ein Tichu angekündigt hat
                        preferred = [CARD_DOG]
                # Ansonsten kriegt der Gegner eine Karte bis 10
                max_value = 10  # Höchster Kartenwert, der zur Abgabe in Betracht kommt
                while not preferred:
                    preferred = [(v, c) for v, c in self.priv.hand_cards if c > 0 and v <= max_value and (v, c) not in schupfed]
                    if not preferred:
                        assert max_value < 14, "Keine Schupfkarte für den Gegner gefunden."
                        max_value += 1  # die Handkarten sind zu gut; es müssen höhere Karten in Betracht gezogen werden

            # Aus der bevorzugten Karte diejenige auswählen, die in möglichst wenig guten Kombis gespielt werden kann.
            length = len(preferred)
            if length > 1:
                # Zuerst sind die besseren Kombis aufgelistet. Wir durchlaufen die Liste bis zu den Einzelkarten.
                # Wir verwerfen dabei alle bevorzugten Karten, die in den Kombinationen benötigt werden, solange bis
                # wir nur noch eine bevorzugte Karte haben.
                for cards, (t, n, v) in self.priv.combinations:
                    #if (not pub.announcements[priv.player_index] and t == PAIR and v < 7) or t == CombinationType.SINGLE:
                    if t == CombinationType.SINGLE and v < 15:
                        break
                    if length - n >= 1:
                        for card in cards:
                            if card in preferred:
                                preferred.remove(card)
                                length -= 1
                        if length == 1:
                            break

            if i == 2:
                # Für den Partner nehmen wir die höchste Einzelkarte
                schupfed[i - 1] = preferred[0]
            else:
                # Für den Gegner entscheidet der Zufall
                schupfed[i - 1] = preferred[self._random.integer(0, length)]
        return schupfed[0], schupfed[1], schupfed[2]

    async def play(self, interruptable: bool = False) -> Tuple[Cards, Combination]:
        """
        Die Engine fordert den Spieler auf, eine gültige Kartenkombination auszuwählen oder zu passen.

        Die Engine ruft diese Methode nur auf, wenn der Spieler am Zug ist oder eine Bombe hat.
        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        :param interruptable: (Optional) Wenn True, kann die Anfrage durch ein Interrupt abgebrochen werden.
        :return: Die ausgewählte Kombination (Karten, (Typ, Länge, Rang)) oder Passen ([], (0,0,0)).
        :raises PlayerInterruptError: Wenn die Aktion durch ein Interrupt abgebrochen wurde.
        """
        if self.pub.current_turn_index != self.priv.player_index:
            # der Spieler ist nicht am Zug, daher kann er nur eine Bombe werfen
            # todo Statistik verwenden (hier wird noch durch Zufall entschieden)
            if not self._random.choice([True, False], [1, 2]):  # einmal Ja, zweimal Nein
                return [], (CombinationType.PASS, 0, 0)
            combinations = [combi for combi in self.priv.combinations if combi[1][0] == CombinationType.BOMB]
            action_space = build_action_space(combinations, self.pub.trick_combination, wish_value=0)
            return self._random.choice(action_space)

        # mögliche Kombinationen (inklusive Passen; wenn Passen erlaubt ist, steht Passen an erster Stelle)
        action_space = build_action_space(self.priv.combinations, self.pub.trick_combination, self.pub.wish_value)

        action_len = len(action_space)
        assert action_len > 0
        if action_len == 1:
            return action_space[0]  # es gibt nur diese mögliche Aktion

        can_skip = action_space[0][1][0] == CombinationType.PASS
        partner = self.priv.partner_index
        opp_right = self.priv.opponent_right_index
        opp_left = self.priv.opponent_left_index

        # Ist noch niemand fertig geworden und habe ich ein größeres Tichu angesagt als die anderen? Oder der Partner?
        a = self.pub.announcements
        has_tichu = self.pub.winner_index == -1 and a[self.priv.player_index] > max(a[partner], a[opp_right], a[opp_left])
        has_partner_tichu = self.pub.winner_index == -1 and a[partner] > max(a[self.priv.player_index], a[opp_right], a[opp_left])

        # Kann der rechte Gegner im nächsten Zug seine restlichen Karten ablegen?
        trick_len = self.pub.trick_combination[2]
        count_hand_cards = self.pub.count_hand_cards
        right_opp_can_win = 0 < count_hand_cards[opp_right] < 6 and count_hand_cards[opp_right] == trick_len

        # Können und wollen wir fertig werden?
        for cards, figure in action_space:
            if figure[1] == count_hand_cards[self.priv.player_index]:
                # Wir könnten alle restlichen Karten ablegen.
                if has_partner_tichu and not right_opp_can_win and can_skip:
                    # Der Partner hat einen Tichu angesagt und der rechte Gegner kann nicht fertig werden.
                    return action_space[0]  # Wir passen, damit der Partner eine Chance hat, als erstes fertig zu werden.
                return cards, figure  # wir legen alle Handkarten ab

        # Können und wollen wir passen, damit der Partner den Stich bekommt?
        if self.pub.trick_owner_index == partner and can_skip:
            # Der Partner hat den Stich und wir könnten passen
            if not has_tichu and not right_opp_can_win and count_hand_cards[partner] > 0:
                # Wir haben kein Tichu angesagt und der Gegner kann nicht gewinnen und der Partner hat noch Karten.
                return action_space[0]  # Wir passen (bzw. machen nichts), um den Partner nicht zu überstechen.

        # Können und wollen wir den Hund ausspielen?
        for cards, figure in action_space:
            if figure == (CombinationType.SINGLE, 1, 0):
                return cards, figure  # wir spielen den Hund so bald wie möglich

        # Wir suchen zuerst die Partitionen, die mindestens eine spielbare Kombination haben. Damit vermeiden wir das
        # Passen, neben aber in Kauf, dass evtl. eine Bombe, Straße, Fullhouse oder Treppe auseinandergerissen wird.
        partitions = filter_playable_partitions(self.priv.partitions, action_space)
        if not partitions:  # pragma: no cover
            # Anscheinend hat build_partitions() alle Partitionen abgeschnitten, die jetzt passen würden.
            # Als Fallback bilden wir für jede gültige Aktion eine neue Partition, die neben der jeweiligen Aktion
            # nur aus Einzel-Kombinationen besteht.
            for cards, figure in action_space:
                singles = [([card], (CombinationType.SINGLE, 1, card[0])) for card in self.priv.hand_cards if card not in cards]
                partitions.append([(cards, figure)] + singles)

        # Als Zweites suchen wir die kürzeste Partition, da wir mit dieser vermutlich am schnellsten fertig werden.
        # Eine Bombe bleibt meistens in der Auswahl. Eine Straße könnte aber eine kürzere Partition bilden, sodass
        # in diesem Fall die Bombe auseinandergerissen wird.
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
                q = partition_quality(partition, action_space, self._statistic(self.pub, self.priv))
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
        for cards, (t, n, v) in self.priv.combinations:
            if t == CombinationType.BOMB:
                # Können wir Schluss machen (haben wir nur noch max. 2 Kombinationen)?
                could_win = len(best_partition) <= 2
                # Hat der Gegner, der an der Reihe ist, weniger als 6 Handkarten?
                m = count_hand_cards[self.pub.current_turn_index]
                opp_could_win = self.pub.current_turn_index in (opp_right, opp_left) and m < 6
                # Würden die Gegner 40 Punkte oder mehr kriegen?
                b1 = self.pub.trick_owner_index in (self.priv.player_index, partner) and self.pub.trick_combination == (CombinationType.SINGLE, 1, 15)
                b2 = self.pub.trick_owner_index in (opp_right, opp_left) and self.pub.trick_combination != (CombinationType.SINGLE, 1, 15)
                opp_win_trick = self.pub.trick_points >= 40 and (b1 or b2)
                # Ist mindestens ein Kriterium erfüllt?
                if could_win or opp_could_win or opp_win_trick:
                    # Vermasseln wir auch nicht das Tichu des Partners, in dem wir Schluss machen?
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
        assert combis, "Zu viele Kombinationen aus der Auswahl entfernt"
        if len(combis) == 1:
            return combis[0]

        # Wir haben jetzt die Qual der Wahl. Nehmen wir eine Kombi, die wir sonst schlechter loswerden würden oder eine
        # Kombi, mit der wir vermutlich den Stich gewinnen und wieder das Anspielrecht bekommen?
        # Wir gewichten unsere Wahl anhand der Punkte, die im Stich liegen.
        if self.pub.trick_points < 0:
            trick_sum = 0.0  # 0 Punkte oder weniger werten wir mit 0 # pragma: no cover
        elif self.pub.trick_points > 40:
            trick_sum = 1.0  # und ab 40 Punkten mit 1 # pragma: no cover
        else:
            trick_sum = self.pub.trick_points / 40  # Punkte des aktuellen Stichs normiert auf den Bereich [0, 1]

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
        statistic = self._statistic(self.pub, self.priv)
        best_combi = combis[0]
        lost_min = math.inf
        for combi in combis:
            lo_opp, lo_par, hi_opp, hi_par, eq_opp, hi_par = statistic[tuple(combi[0])]
            v = trick_sum if combi[1] != (CombinationType.SINGLE, 1, 15) else -trick_sum
            lost = (lo_opp + lo_par) * (1 - v) + (hi_opp + hi_par) * v
            if lost_min > lost:
                lost_min = lost
                best_combi = combi
        return best_combi

    # Welcher Kartenwert wird gewünscht?
    # return: Der gewünschte Kartenwert (2-14).
    async def wish(self) -> int:
        """
        Die Engine fragt den Spieler nach einem Kartenwert-Wunsch (nach Ausspielen des Mah Jong).

        Die Engine ruft diese Methode nur auf, wenn der Spieler sich einen Kartenwert wünschen muss.
        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        :return: Der gewünschte Kartenwert (2-14).
        """
        values = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]

        t, n, value = self.pub.trick_combination
        if t == CombinationType.STREET:
            # Wenn eine Straße gespielt wurde, wird Junge, Dame, König oder As bevorzugt, da diese für den Gegner
            # besser als Einzelkarte, Paar oder Drilling zu verwenden wäre.
            preferred = [v for v in range(2, 15) if v > 10 and v > value]
        else:
            # Ansonsten werden Werte bevorzugt, die sich noch vollständig in den Händen der Mitspieler befinden und
            # nicht an den Partner geschoben wurden. Das verringert das Bombenrisiko etwas.
            preferred = []
            excl = self.priv.hand_cards + self.pub.played_cards + [self.priv.given_schupf_cards[1]]
            for v in range(2, 15):
                if (v, 1) not in excl and (v, 2) not in excl and (v, 3) not in excl and (v, 4) not in excl:
                    preferred.append(v)
        if preferred:
            values = preferred

        # Wert bevorzugen, der an den nachfolgenden Gegner geschoben wurde. So mobben wir unseren Partner nicht.
        value, color = self.priv.given_schupf_cards[0]
        if value in values:
            values = [value]

        wish = values[self._random.integer(0, len(values))]
        assert 2 <= wish <= 14, "Der Wunsch muss zw. 2 und 14 (As) liegen."
        return wish

    async def give_dragon_away(self) -> int:
        """
        Die Engine fragt den Spieler, welcher Gegner den Drachen bekommen soll.

        Die Engine ruft diese Methode nur auf, wenn der Spieler den Drachen verschenken muss.
        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        :return: Der Index (0-3) des Gegners, der den Stich erhält.
        """
        # Der Spieler mit den meisten Handkarten kriegt den Drachen.
        count_hand_cards = self.pub.count_hand_cards
        right = count_hand_cards[self.priv.opponent_right_index]
        left = count_hand_cards[self.priv.opponent_left_index]
        if right > left:
            opp = self.priv.opponent_right_index
        elif right < left:
            opp = self.priv.opponent_left_index
        else:
            opp = self.priv.opponent_right_index if self._random.integer(0, 2) == 1 else self.priv.opponent_left_index
        return opp
