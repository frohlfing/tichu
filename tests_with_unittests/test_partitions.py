import unittest
# noinspection PyProtectedMember
from src.lib.cards import *
from src.lib.combinations import *
from src.lib.partitions import *
from src.lib.prob.statistic import calc_statistic, partition_quality

FIGURE_PASS = (CombinationType.PASS, 0, 0)
FIGURE_DOG = (CombinationType.SINGLE, 1, 0)
FIGURE_MAH = (CombinationType.SINGLE, 1, 1)
FIGURE_DRA = (CombinationType.SINGLE, 1, 15)
FIGURE_PHO = (CombinationType.SINGLE, 1, 16)


class TestPartitions(unittest.TestCase):
    def test_build_partitions(self):
        # Abbruch
        hand = parse_cards("Ph R5 S4 B4 G4 R4 S3 B3 G3 R3 S2 B2 G2 R2")  # Superblatt (3 Bomben + Phönix) = 1576 Kombis
        expected = ["4erBombe4 4erBombe3 4erBombe2 Paar5",
                    "4erBombe4 4erBombe3 4erBombe2 Phönix Fünf",
                    "4erBombe4 4erBombe3 FullHouse2 Zwei",
                    "4erBombe4 4erBombe3 FullHouse2 Zwei",
                    "4erBombe4 4erBombe3 FullHouse2 Zwei",
                    "4erBombe4 4erBombe3 FullHouse2 Zwei",
                    "4erBombe4 4erBombe3 Drilling2 Paar2 Fünf"]
        combis = build_combinations(hand)
        self.assertEqual(1576, len(combis))
        partitions = []
        partitions_aborted = not build_partitions(partitions, combis, counter=len(hand), maxlen=len(expected))
        self.assertTrue(partitions_aborted)
        self.assertEqual(len(expected), len(partitions))
        for (s, partition) in zip(expected, partitions):
            self.assertEqual(s, stringify_partition(partition))
        # kein Abbruch
        hand = parse_cards("RB BB BZ SZ")
        expected = ["2erTreppeB", "PaarB PaarZ", "PaarB Zehn Zehn", "PaarZ Bube Bube", "Bube Bube Zehn Zehn"]
        combis = build_combinations(hand)
        partitions = []
        partitions_aborted = not build_partitions(partitions, combis, counter=len(hand), maxlen=2000)
        self.assertFalse(partitions_aborted)
        self.assertEqual(len(expected), len(partitions))
        for (s, partition) in zip(expected, partitions):
            self.assertEqual(s, stringify_partition(partition))

    def test_remove_partitions(self):
        partitions = []
        build_partitions(partitions, build_combinations(parse_cards("RB BB BZ SZ")), counter=4, maxlen=2000)
        partitions = remove_partitions(partitions, parse_cards("BZ"))
        expected = ["PaarB Zehn", "Bube Bube Zehn"]
        self.assertEqual(len(expected), len(partitions))
        for (s, partition) in zip(expected, partitions):
            self.assertEqual(s, stringify_partition(partition))

    def test_filter_playable_partitions(self):
        partitions = []
        build_partitions(partitions, build_combinations(parse_cards("RB BB BZ SZ")), counter=4, maxlen=2000)
        action_space = [([], FIGURE_PASS), ([(11,4)], (CombinationType.SINGLE, 1, 11)), ([(11,2)], (CombinationType.SINGLE, 1, 11))]  # Passen, RB, BB
        partitions = filter_playable_partitions(partitions, action_space)
        expected = ["PaarZ Bube Bube", "Bube Bube Zehn Zehn"]
        self.assertEqual(len(expected), len(partitions))
        for (s, partition) in zip(expected, partitions):
            self.assertEqual(s, stringify_partition(partition))

    def test_filter_playable_combinations(self):
        partition = [([(10, 3), (10, 4)], (2, 2, 10)), ([(11, 1)], (1, 1, 11)), ([(11, 3)], (1, 1, 11))]  # PaarZ Bube Bube
        action_space = [([], FIGURE_PASS), ([(11, 1)], (CombinationType.SINGLE, 1, 11)), ([(11, 3)], (CombinationType.SINGLE, 1, 11))]  # Passen, RB, BB
        # noinspection PyTypeChecker
        combis = filter_playable_combinations(partition, action_space)
        expected = [([(11, 1)], (1, 1, 11)), ([(11, 3)], (1, 1, 11))]  # RB, BB
        self.assertEqual(len(expected), len(combis))
        for (s, combi) in zip(expected, combis):
            self.assertEqual(s, combi)

    def test_stringify_partition(self):
        partition = [([(10, 3), (10, 4)], (2, 2, 10)), ([(11, 1)], (1, 1, 11)), ([(11, 3)], (1, 1, 11))]  # PaarZ Bube Bube
        expected = "PaarZ Bube Bube"
        # noinspection PyTypeChecker
        self.assertEqual(expected, stringify_partition(partition))

    def test_partition_quality(self):  # Gleiche Beispiele wie in TestProbCalcStatistic.test_calc_statistic!
        def _test(c, expected, hand, hidden, number_of_cards, trick_figure=(0, 0, 0), action_space=None):
            if action_space is None:
                action_space = []
            hand = parse_cards(hand)
            hidden = parse_cards(hidden)
            combis = build_combinations(hand)
            partitions = []
            build_partitions(partitions, combis, len(hand), 1)
            statistic = calc_statistic(0, hand, combis, number_of_cards, trick_figure, hand + hidden)
            q = partition_quality(partitions[0], action_space, statistic)
            self.assertAlmostEqual(expected, q, 6, f"Gütefunktion für Beispiel {c} nicht ok")

        # 1) Ich habe Fullhouse und Sonderkarten, Gegner hat Straße und Phönix
        _test(1, expected=-0.083333, hand="BD GD RD BZ RZ Hu Ma Dr", hidden="Ph GA BK SD RB SZ", number_of_cards=[8, 6, 0, 0])

        # 2) Ich habe eine Treppe, der Gegner hat auch eine Treppe und Phönix
        _test(2, expected=-0.051282, hand="RZ GZ G9 S9 B8 G8", hidden="Ph RB BB BZ SZ B9 R8 S8 R7 G7", number_of_cards=[6, 10, 0, 0])

        # 3) Wie 2, aber mit mehreren Mitspielern
        _test(3, expected=0.043346, hand="RZ GZ G9 S9 B8 G8", hidden="Ph RB BB BZ SZ B9 R8 S8 R7 G7", number_of_cards=[6, 5, 5, 0])

        # 4) Ich habe eine Straße, der Gegner hat Hu Ma Dr und eine Bombe
        _test(4, expected=0., hand="RZ G9 G8 B7 G6", hidden="RB GB BB SB Hu Ma Dr", number_of_cards=[5, 7, 0, 0])

        # 5) Ich habe eine Bombe, der Gegner hat auch eine Bombe
        _test(5, expected=1., hand="RD GD BD SD", hidden="RB GB BB SB", number_of_cards=[4, 4, 0, 0])

        # 6) Ich habe den Phönix und den Hund, der Gegner eine Bombe
        _test(6, expected=0.285714, hand="Ph BD Hu", hidden="RB GB BB SB", number_of_cards=[3, 4, 0, 0], trick_figure=(1, 1, 11))

        # 7) Ich habe den Phönix, der Gegner hat den Drachen
        _test(7, expected=0., hand="Ph BD SD", hidden="Dr RK GK BB SB", number_of_cards=[3, 5, 0, 0], trick_figure=(1, 1, 11))

        # 7) Kein Mitspieler hat bessere Karten
        _test(8, expected=1., hand="RA RK RD", hidden="BB SZ B9 S8 S4 G3", number_of_cards=[3, 2, 2, 2], trick_figure=(1, 1, 11))

        # 8) Wie 4, aber mit Anspielrecht
        _test(9, expected=1., hand="RZ G9 G8 B7 G6", hidden="RB GB BB SB Hu Ma Dr", number_of_cards=[5, 7, 0, 0], trick_figure=(1, 1, 11),
              action_space=[(parse_cards("RZ G9 G8 B7 G6"), (CombinationType.STREET, 5, 10)),])


if __name__ == "__main__":
    unittest.main()
