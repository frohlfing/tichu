import unittest
from src.lib.prob.calc_statistic import calc_statistic
# noinspection PyProtectedMember
from src.lib.combinations import *
from src.lib.cards import *


# noinspection DuplicatedCode
class TestProbCalcStatistic(unittest.TestCase):
    def test_calc_statistic(self):
        # 1) Ich hab Fullhouse und Sonderkarten, Gegner hat Straße und Phönix
        hand = parse_cards("Dr BD GD RD BZ RZ Ma Hu")
        hidden = parse_cards("Ph GA BK SD RB SZ")
        number_of_cards = [len(hand), len(hidden), 0, 0]
        trick_figure = (0, 0, 0)
        expected = {}
        expected.setdefault(tuple(parse_cards("Dr")), (1.0, 0, 0, 0, 0, 0))
        expected.setdefault(tuple(parse_cards("BD GD RD BZ RZ")), (0.0, 0, 0, 0, 0, 0))
        expected.setdefault(tuple(parse_cards("BD GD RD")), (0.0, 0, 0, 0, 0, 0))
        expected.setdefault(tuple(parse_cards("BD GD")), (0.4, 0, 0.4, 0, 0.2, 0))
        expected.setdefault(tuple(parse_cards("BZ RZ")), (0, 0, 0.8, 0, 0.2, 0))
        expected.setdefault(tuple(parse_cards("BD")), (2/6, 0, 3/6, 0, 1/6, 0))
        expected.setdefault(tuple(parse_cards("BZ")), (0, 0, 5/6, 0, 1/6, 0))
        expected.setdefault(tuple(parse_cards("Ma")), (0, 0, 1.0, 0, 0, 0))
        expected.setdefault(tuple(parse_cards("Hu")), (0, 0, 1.0, 0, 0, 0))
        statistic = calc_statistic(0, hand, build_combinations(hand), number_of_cards, trick_figure, hand + hidden)
        for combi in expected:
            result = statistic[combi]
            for k, (f1, f2) in enumerate(zip(expected[combi], result)):
                self.assertAlmostEqual(f1, f2, 6, f"Statistik für Beispiel 1.{k} nicht ok: {stringify_cards(combi)}, {result}")

        # 2) Ich hab Treppe, Gegner hat auch eine Treppe und Phönix
        hand = parse_cards("RZ GZ G9 S9 B8 G8")
        hidden = parse_cards("Ph RB BB BZ SZ B9 R8 S8 R7 G7")
        number_of_cards = [len(hand), len(hidden), 0, 0]
        trick_figure = (0, 0, 0)
        expected = {}
        expected.setdefault(tuple(parse_cards("RZ GZ G9 S9 B8 G8")), (1/3, 0, 1/3, 0, 1/3, 0))
        expected.setdefault(tuple(parse_cards("RZ GZ G9 S9")), (6/12, 0, 5/12, 0, 1/12, 0))
        expected.setdefault(tuple(parse_cards("G9 S9 B8 G8")), (5/12, 0, 6/12, 0, 1/12, 0))
        expected.setdefault(tuple(parse_cards("RZ GZ")), (7/13, 0, 3/13, 0, 3/13, 0))
        expected.setdefault(tuple(parse_cards("G9 S9")), (6/13, 0, 6/13, 0, 1/13, 0))
        expected.setdefault(tuple(parse_cards("B8 G8")), (3/13, 0, 7/13, 0, 3/13, 0))
        expected.setdefault(tuple(parse_cards("RZ")), (0.5, 0.0, 0.3, 0.0, 0.2, 0))
        expected.setdefault(tuple(parse_cards("G9")), (0.4, 0.0, 0.5, 0.0, 0.1, 0))
        expected.setdefault(tuple(parse_cards("B8")), (0.2, 0.0, 0.6, 0.0, 0.2, 0.0))
        statistic = calc_statistic(0, hand, build_combinations(hand), number_of_cards, trick_figure, hand + hidden)
        for combi in expected:
            result = statistic[combi]
            #print(stringify_cards(combi), result)
            for k, (f1, f2) in enumerate(zip(expected[combi], result)):
                self.assertAlmostEqual(f1, f2, 6, f"Statistik für Beispiel 2.{k} nicht ok: {stringify_cards(combi)}, {result}")

        # 3) Wie 2, aber mit mehreren Mitspielern
        hand = parse_cards("RZ GZ G9 S9 B8 G8")
        hidden = parse_cards("Ph RB BB BZ SZ B9 R8 S8 R7 G7")
        number_of_cards = [len(hand), 5, 5, 0]
        trick_figure = (0, 0, 0)
        expected = {}
        expected.setdefault(tuple(parse_cards("RZ GZ G9 S9 B8 G8")), (0, 0, 0, 0, 0, 0))
        expected.setdefault(tuple(parse_cards("RZ GZ G9 S9")), (0.011904761904762, 0.011904761904762, 0.009920634920635, 0.009920634920635, 0.001984126984127, 0.001984126984127))
        expected.setdefault(tuple(parse_cards("G9 S9 B8 G8")), (0.009920634920635, 0.009920634920635, 0.011904761904762, 0.011904761904762, 0.001984126984127, 0.001984126984127))
        expected.setdefault(tuple(parse_cards("RZ GZ")), (0.119658119658120, 0.119658119658120, 0.051282051282051, 0.051282051282051, 0.051282051282051, 0.051282051282051))
        expected.setdefault(tuple(parse_cards("G9 S9")), (0.10256410256410256, 0.10256410256410256, 0.10256410256410256, 0.10256410256410256, 0.017094017094017092, 0.017094017094017092))
        expected.setdefault(tuple(parse_cards("B8")), (0.1, 0.1, 0.3, 0.3, 0.1, 0.1))
        expected.setdefault(tuple(parse_cards("B8 G8")), (0.051282051282051, 0.051282051282051, 0.119658119658120, 0.119658119658120, 0.051282051282051, 0.051282051282051))
        expected.setdefault(tuple(parse_cards("RZ")), (0.25, 0.25, 0.15, 0.15, 0.1, 0.1))
        statistic = calc_statistic(0, hand, build_combinations(hand), number_of_cards, trick_figure, hand + hidden)
        for combi in expected:
            result = statistic[combi]
            for k, (f1, f2) in enumerate(zip(expected[combi], result)):
                self.assertAlmostEqual(f1, f2, 6, f"Statistik für Beispiel 3.{k} nicht ok: {stringify_cards(combi)}, {result}")

        # 4) Ich hab eine Straße, Gegner hat Hu Ma Dr und eine Bombe
        hand = parse_cards("RZ G9 G8 B7 G6")
        hidden = parse_cards("RB GB BB SB Hu Ma Dr")
        number_of_cards = [len(hand), len(hidden), 0, 0]
        trick_figure = (0, 0, 0)
        expected = {}
        expected.setdefault(tuple(parse_cards("RZ G9 G8 B7 G6")), (0, 0, 1, 0, 0, 0))
        expected.setdefault(tuple(parse_cards("RZ")), (1/7, 0, 6/7, 0, 0, 0))  # 7 = 6 Einzelkarten ohne Hund + 1 Bombe
        statistic = calc_statistic(0, hand, build_combinations(hand), number_of_cards, trick_figure, hand + hidden)
        for combi in expected:
            result = statistic[combi]
            for k, (f1, f2) in enumerate(zip(expected[combi], result)):
                self.assertAlmostEqual(f1, f2, 6, f"Statistik für Beispiel 4.{k} nicht ok: {stringify_cards(combi)}, {result}")

        # 5) Ich hab eine Bombe, Gegner hat auch eine Bombe
        hand = parse_cards("RD GD BD SD")
        hidden = parse_cards("RB GB BB SB")
        number_of_cards = [len(hand), len(hidden), 0, 0]
        trick_figure = (0, 0, 0)
        expected = {}
        expected.setdefault(tuple(parse_cards("RD GD BD SD")), (1, 0, 0, 0, 0, 0))
        expected.setdefault(tuple(parse_cards("RD")), (4/5, 0, 1/5, 0, 0, 0))
        statistic = calc_statistic(0, hand, build_combinations(hand), number_of_cards, trick_figure, hand + hidden)
        for combi in expected:
            result = statistic[combi]
            for k, (f1, f2) in enumerate(zip(expected[combi], result)):
                self.assertAlmostEqual(f1, f2, 6, f"Statistik für Beispiel 5.{k} nicht ok: {stringify_cards(combi)}, {result}")

        # 6) Ich hab den Phönix und den Hund, der Gegner eine Bombe
        hand = parse_cards("Ph BD Hu")
        hidden = parse_cards("RB GB BB SB")
        number_of_cards = [len(hand), len(hidden), 0, 0]
        trick_figure = (1, 1, 11)
        expected = {}
        expected.setdefault(tuple(parse_cards("Ph")), (4/5, 0, 1/5, 0, 0, 0))
        expected.setdefault(tuple(parse_cards("BD")), (4/5, 0, 1/5, 0, 0, 0))
        expected.setdefault(tuple(parse_cards("Hu")), (0, 0, 1, 0, 0, 0))
        statistic = calc_statistic(0, hand, build_combinations(hand), number_of_cards, trick_figure, hand + hidden)
        for combi in expected:
            result = statistic[combi]
            for k, (f1, f2) in enumerate(zip(expected[combi], result)):
                self.assertAlmostEqual(f1, f2, 6, f"Statistik für Beispiel 6.{k} nicht ok: {stringify_cards(combi)}, {result}")

        # 7) Ich hab den Phönix, der Gegner hat den Drachen
        hand = parse_cards("Ph BD SD")
        hidden = parse_cards("Dr RK GK BB SB")
        number_of_cards = [len(hand), len(hidden), 0, 0]
        trick_figure = (1, 1, 11)
        expected = {}
        expected.setdefault(tuple(parse_cards("Ph")), (4/5*5/7, 0, 3/5*5/7, 0, 0, 0))
        statistic = calc_statistic(0, hand, build_combinations(hand), number_of_cards, trick_figure, hand + hidden)
        for combi in expected:
            result = statistic[combi]
            for k, (f1, f2) in enumerate(zip(expected[combi], result)):
                self.assertAlmostEqual(f1, f2, 6, f"Statistik für Beispiel 7.{k} nicht ok: {stringify_cards(combi)}, {result}")

    #  Test schlägt fehl. Vermutlich wird nicht berücksichtigt, dass der Gegner spielen kann was auch immer, die Bombe ist besser.
    def test_calc_statistic_2(self):
        # die Karten werden gerade verteilt
        hand = parse_cards("RA RK RD RB RZ R9 R8 R7 R6 R5 R4 R3 R2 Ma")
        combis = build_combinations(hand)
        number_of_cards = [len(hand), 8, 8, 8]
        trick_figure = (0, 0, 0)
        unplayed_cards = deck
        statistic = calc_statistic(0, hand, combis, number_of_cards, trick_figure, unplayed_cards)
        bomb = tuple(parse_cards("RA RK RD RB RZ R9 R8 R7 R6 R5 R4 R3 R2"))
        result = statistic[bomb]
        expected = 0.0, 0.0, 0, 0, 0, 0
        for k, (f1, f2) in enumerate(zip(expected, result)):
            self.assertAlmostEqual(f1, f2, 4, f"Statistik für Wert {k} nicht ok: {result}")


if __name__ == "__main__":
    unittest.main()
