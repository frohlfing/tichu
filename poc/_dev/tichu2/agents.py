import config
import math
import numpy as np
from tichu.cards import *
from tichu.combinations import *
# from tichu.nnet import load_model_without_gpu
from tichu.partitions import filter_playable_partitions, filter_playable_combinations, partition_quality
from tichu.state import PublicState, PrivateState
from time import sleep
from typing import List


class Agent:
    def __init__(self, seed=None):
        self._seed = seed  # Initialwert für Zufallsgenerator (Integer > 0 oder None)
        self._random = None  # wegen Multiprocessing ist ein eigener Zufallsgenerator notwendig

    @property
    def name(self) -> str:
        return type(self).__name__

    def reset(self):
        pass

    # Welche Karten an die Mitspieler abgeben?
    # return: Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner (d.h. kanonische Anordnung)
    def schupf(self, pub: PublicState, priv: PrivateState) -> tuple:  # pragma: no cover
        pass

    # Tichu ansagen?
    def announce(self, pub: PublicState, priv: PrivateState, grand: bool = False) -> bool:  # pragma: no cover
        pass

    # Welche Kombination soll gespielt werden?
    # action_space: Mögliche Kombinationen (inklusiv Passen)
    # return: Ausgewählte Kombination (Karten, (Typ, Länge, Wert))
    def combination(self, pub: PublicState, priv: PrivateState, action_space: List[tuple]) -> tuple:  # pragma: no cover  #  todo Parameter als Tuple
        pass

    # Welcher Kartenwert wird gewünscht?
    # return: Wert zw. 2 und 14
    def wish(self, pub: PublicState, priv: PrivateState) -> int:  # pragma: no cover
        pass

    # Welcher Gegner soll den Drachen bekommen?
    # return: Nummer des Gegners
    def gift(self, pub: PublicState, priv: PrivateState) -> int:  # pragma: no cover
        pass

    # Return random integers from low (inclusive) to high (exclusive).
    def _rand(self, a, b):
        if not self._random:
            self._random = np.random.RandomState(seed=self._seed)
        return self._random.randint(a, b)


class RandomAgent(Agent):
    def __init__(self, delay=0., seed=None):
        super().__init__(seed=seed) 
        self._delay = delay  # eg 0.1 = 100ms

    # Welche Karten an die Mitspieler abgeben?
    # return: Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner (d.h. kanonische Anordnung)
    def schupf(self, pub: PublicState, priv: PrivateState) -> tuple:
        if self._delay:
            sleep(self._delay)
        hand = list(priv.hand)
        return tuple([hand.pop(self._rand(0, 14)), hand.pop(self._rand(0, 13)), hand.pop(self._rand(0, 12))])

    # Tichu ansagen?
    def announce(self, pub: PublicState, priv: PrivateState, grand: bool = False) -> bool:
        if self._delay:
            sleep(self._delay)
        return self._rand(0, 20 if grand else 10) == 0

    # Welche Kombination soll gespielt werden?
    # action_space: Mögliche Kombinationen (inklusiv Passen)
    # return: Ausgewählte Kombination (Karten, (Typ, Länge, Wert))
    def combination(self, pub: PublicState, priv: PrivateState, action_space: List[tuple]) -> tuple:
        if self._delay:
            sleep(self._delay)
        return action_space[self._rand(0, len(action_space))]

    # Welcher Kartenwert wird gewünscht?
    # return: Wert zw. 2 und 14
    def wish(self, pub: PublicState, priv: PrivateState) -> int:
        if self._delay:
            sleep(self._delay)
        return self._rand(2, 15)

    # Welcher Gegner soll den Drachen bekommen?
    # return: Nummer des Gegners
    def gift(self, pub: PublicState, priv: PrivateState) -> int:
        if self._delay:
            sleep(self._delay)
        return priv.opponent_right if self._rand(0, 2) == 1 else priv.opponent_left


class HeuristicAgent(Agent):
    def __init__(self, seed=None):
        super().__init__(seed)
        self.__statistic: dict = {}  # Statistische Häufigkeit der Kombinationen (wird erst berechnet, wenn benötigt)
        self._statistic_key: tuple = ()  # Spieler und Anzahl Handkarten, für die die Statistik berechnet wurde

    def reset(self):
        self.__statistic = {}
        self._statistic_key = ()

    # Welche Karten an die Mitspieler abgeben?
    # return: Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner (d.h. kanonische Anordnung)
    def schupf(self, pub: PublicState, priv: PrivateState) -> tuple:
        schupfed = [None, None, None]
        for i in [2, 1, 3]:  # erst die Karte für den Partner aussuchen, dann für die Gegner
            p = (priv.player + i) % 4  # Index in kanonische Form
            preferred = []  # Karten, die zum Abgeben in Betracht kommen
            if i == 2:  # Partner
                if pub.announcements[priv.player] > pub.announcements[p]:
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
                elif pub.announcements[p] > pub.announcements[priv.player]:
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
                    if (not pub.announcements[priv.player] and t == PAIR and v < 7) or t == SINGLE:
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
            min_q = config.TICHU_QUALITY[int(grand)]

            # Falls wir am Zug sind, spielbare Kombinationen ermitteln (ansonsten ist der Aktionsraum leer)
            my_turn = pub.current_player == priv.player or (pub.start_player == -1 and CARD_MAH in priv.hand)
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
        has_tichu = pub.winner == -1 and a[priv.player] > max(a[partner], a[opp_right], a[opp_left])
        has_partner_tichu = pub.winner == -1 and a[partner] > max(a[priv.player], a[opp_right], a[opp_left])

        # Kann der rechte Gegner im nächsten Zug seine restlichen Karten ablegen?
        trick_len = pub.trick_figure[2]
        right_opp_can_win = 0 < pub.number_of_cards[opp_right] < 6 and pub.number_of_cards[opp_right] == trick_len

        # Können und wollen wir fertig werden?
        for cards, figure in action_space:
            if figure[1] == pub.number_of_cards[priv.player]:
                # Wir könnten alle restlichen Karten ablegen.
                if has_partner_tichu and not right_opp_can_win and can_skip:
                    # Der Partner hat ein Tichu angesagt und der rechte Gegner kann nicht fertig werden.
                    return action_space[0]  # Wir passen, damit der Partner eine Chance hat, als erstes fertig zu werden.
                return cards, figure  # wir legen alle Handkarten ab

        # Können und wollen wir passen, damit der Partner den Stich bekommt?
        if pub.trick_player == partner and can_skip:
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
                m = pub.number_of_cards[pub.current_player]
                opp_could_win = pub.current_player in (opp_right, opp_left) and m < 6
                # Würden die Gegner 40 Punkte oder mehr kriegen?
                b1 = pub.trick_player in (priv.player, partner) and pub.trick_figure == FIGURE_DRA
                b2 = pub.trick_player in (opp_right, opp_left) and pub.trick_figure != FIGURE_DRA
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
            excl = priv.hand + pub.played_cards + (priv.schupfed[1])
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
        key = (priv.player, priv.hand, pub.number_of_cards)
        if self._statistic_key != key:
            self._statistic_key = key
            self.__statistic = calc_statistic(priv.player, priv.hand, priv.combinations, pub.number_of_cards, pub.trick_figure, pub.unplayed_cards)
        return self.__statistic


# # Neuronales Netz mit zwei Ausgänge, so wie es MCTS verwendet:
# # - Wahrscheinlichkeitsverteilung p (Vektor; für jede mögliche Aktion ein Wert, Summe aller Werte ist 1)
# # - Zustandswert v (== Belohnung r)
# class NNetAgent(Agent):
#     def __init__(self, hdf5: str, tau=0):  # tau == 0 (exploit/ausnutzen) bis math.inf (explore/erkunden)
#         super().__init__(tau=tau)
#         if not hdf5.startswith('/'):
#             hdf5 = path.join(config.DATA_PATH, hdf5)
#         if not hdf5.endswith('.h5'):
#             hdf5 = path.join(hdf5, 'model.h5')
#         self._hdf5 = hdf5
#         self._model = None
#
#     def _probability(self, state: State) -> np.array:
#         p, _ = self._nnet_predict(state)  # v wird nicht ausgewertet
#         return self._mask(p, state.valid_actions(), state)  # ungültige Aktionen herausfiltern
#
#     def _nnet_predict(self, state: State):
#         if not self._model:
#             # Die GPU wird bereits für das Training benutzt und steht hier nicht zur Verfügung.
#             self._model = load_model_without_gpu(self._hdf5)
#         # Das Netz ist für Agent 0 (Spielstein-Symbol 'O') trainiert. Falls Agent 1 ('X') an der Reihe ist, müssen die
#         # Spielsteine auf dem Spielbrett vertauscht werden, als wenn Agent 0 an der Reihe wäre.
#         canonical_state = state.canonical()
#         # predict() schmeißt in selten Fällen "WARNING:tensorflow:5 out of the last 13 calls to
#         # <function Model.make_predict_function.<locals>.predict_function at 0x7f7fc79a8160> triggered tf.function retracing."
#         # s.a. https://www.py4u.net/discuss/246141
#         # p, v = self._model.predict(canonical_state.board[np.newaxis, :, :])
#         p, v = self._model(canonical_state.board[np.newaxis, :, :])
#         p, v = p[0], v[0][0]
#         p = np.array(p)
#         return p, v  # v == Wert des Spielzustands aus Sicht des aktuellen Spielers
#
#     @staticmethod
#     def _mask(p: np.array, valid_actions, state) -> np.array:  # todo state wird rausnehmen
#         if sum(p * valid_actions) == 0:
#             pass
#             # All valid moves may be masked if either your NNet architecture is insufficient or you've get overfitting.
#             # If you have got dozens of these messages you should pay attention to your NNet and/or training process.
#             # print()
#             # print('WARNING! NNet hat keine gültigen Aktionen vorgeschlagen.')
#             # print(f'Probability: {p}; Valid Actions: {valid_actions}')
#             # print(f'Board: {state.board}; Player: {state.player}')
#             #  p = valid_actions  # jede gültige Aktion erhält die gleiche Wahrscheinlichkeit
#         else:
#             p *= valid_actions  # ungültige Aktionen herausfiltern
#         p /= p.sum()  # normalisieren
#         return p
#
#     @property
#     def name(self) -> str:
#         return f'{super().name}, {path.basename(path.dirname(self._hdf5))}'
