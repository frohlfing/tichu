import unittest
# noinspection PyProtectedMember
from src.lib.combinations import figures, figurelabels_index, possible_hands_hi
from src.lib.combinations import *
from src.lib.cards import *


# noinspection DuplicatedCode
class TestCombinations(unittest.TestCase):
    def test_parse_and_stringify_figure(self):
        self.assertTrue(len(figures) == len(figures_index) == len(figurelabels) == len(figurelabels_index) == 227, "es gibt 227 Kombinationsarten (inklusiv Passen)")
        for i in range(0, 227):
            figure = figures[i]
            lb = stringify_figure(figure)
            self.assertEqual(figure, parse_figure(lb), f"Index nicht OK: {i}, {figure}, {lb}")

    def test_get_figure(self):
        # Passen
        self.assertEqual((PASS, 0, 0), get_figure([], 10), "Passen")

        # Einzelkarte
        self.assertEqual((SINGLE, 1, 14), get_figure(parse_cards("SA"), 10), "As")
        self.assertEqual((SINGLE, 1, 1),  get_figure([CARD_MAH], 10), "MahJong")
        self.assertEqual((SINGLE, 1, 15), get_figure([CARD_DRA], 10), "Drache")
        self.assertEqual((SINGLE, 1, 0),  get_figure([CARD_DOG], 10), "Hund")
        self.assertEqual((SINGLE, 1, 10), get_figure([CARD_PHO], 10), "Phönix mit Wert 10.5")
        self.assertEqual((SINGLE, 1, 1),  get_figure([CARD_PHO], 0),  "Phönix mit Wert 1.5")

        # Paare
        self.assertEqual((PAIR, 2, 14), get_figure(parse_cards("RA GA"), 10), "Paar mit Asse")
        self.assertEqual((PAIR, 2, 14), get_figure(parse_cards("RA Ph"), 10), "Paar mit As und Phönix")

        # Drilling
        self.assertEqual((TRIPLE, 3, 14), get_figure(parse_cards("RA GA BA"), 10), "Drilling")
        self.assertEqual((TRIPLE, 3, 14), get_figure(parse_cards("RA Ph BA"), 10), "Drilling")

        # 2er-Treppe
        self.assertEqual((STAIR, 4, 14), get_figure(parse_cards("RK GK BA SA"), 10), "2er-Treppe")
        self.assertEqual((STAIR, 4, 14), get_figure(parse_cards("RK Ph BA SA"), 10), "2er-Treppe")
        self.assertEqual((STAIR, 4, 14), get_figure(parse_cards("RK GK Ph SA"), 10), "2er-Treppe")

        # 4er-Bombe
        self.assertEqual((BOMB, 4, 14), get_figure(parse_cards("RA GA BA SA"), 10), "4er-Bombe")

        # Fullhouse
        self.assertEqual((FULLHOUSE, 5, 13), get_figure(parse_cards("RK GK BK BA SA"), 10), "Fullhouse")
        self.assertEqual((FULLHOUSE, 5, 14), get_figure(parse_cards("RK GK GA BA SA"), 10), "Fullhouse")
        self.assertEqual((FULLHOUSE, 5, 14), get_figure(parse_cards("RK Ph RA BA SA"), 10), "Fullhouse")
        self.assertEqual((FULLHOUSE, 5, 14), get_figure(parse_cards("RK GK Ph BA SA"), 10), "Fullhouse")
        self.assertEqual((FULLHOUSE, 5, 13), get_figure(parse_cards("RK GK BK Ph SA"), 10), "Fullhouse")

        # 5er-Straße
        self.assertEqual((STREET, 5, 13), get_figure(parse_cards("R9 GZ BB BD SK"), 10), "5er-Straße")
        self.assertEqual((STREET, 5, 13), get_figure(parse_cards("R9 GZ BB BD Ph"), 10), "5er-Straße")
        self.assertEqual((STREET, 5, 13), get_figure(parse_cards("R9 GZ BB Ph SK"), 10), "5er-Straße")
        self.assertEqual((STREET, 5, 13), get_figure(parse_cards("R9 GZ Ph BD SK"), 10), "5er-Straße")
        self.assertEqual((STREET, 5, 13), get_figure(parse_cards("R9 Ph BB BD SK"), 10), "5er-Straße")
        self.assertEqual((STREET, 5, 14), get_figure(parse_cards("Ph GZ BB BD SK"), 10), "5er-Straße")
        self.assertEqual((STREET, 5, 14), get_figure(parse_cards("Ph BB BD SK GA"), 10), "5er-Straße")

        # 5er-Bombe
        self.assertEqual(get_figure(parse_cards("R9 RZ RB RD RK"), 10), (BOMB, 5, 13), "5er-Bombe")

        # 6er-Treppe
        self.assertEqual((STAIR, 6, 11), get_figure(parse_cards("R9 G9 BZ BZ RB SB"), 10), "6er-Treppe")
        self.assertEqual((STAIR, 6, 11), get_figure(parse_cards("R9 G9 BZ BZ Ph SB"), 10), "6er-Treppe")
        self.assertEqual((STAIR, 6, 11), get_figure(parse_cards("R9 G9 Ph BZ RB SB"), 10), "6er-Treppe")
        self.assertEqual((STAIR, 6, 11), get_figure(parse_cards("R9 Ph BZ BZ RB SB"), 10), "6er-Treppe")

        # 6er-Straße
        self.assertEqual((STREET, 6, 13), get_figure(parse_cards("R8 R9 BZ RB RD RK"), 10), "6er-Straße")

        # 6er-Bombe
        self.assertEqual((BOMB, 6, 13), get_figure(parse_cards("R8 R9 RZ RB RD RK"), 10), "6er-Bombe")

        # Phönix einordnen
        cards = parse_cards("Ph SA")
        get_figure(cards, 10, shift_phoenix=True)
        self.assertEqual("SA Ph", stringify_cards(cards), "Paar - Phönix am Ende")

        cards = parse_cards("Ph SA RA")
        get_figure(cards, 10, shift_phoenix=True)
        self.assertEqual("SA RA Ph", stringify_cards(cards), "Drilling - Phönix am Ende")

        cards = parse_cards("Ph RK GK BA SA RD")
        get_figure(cards, 10, shift_phoenix=True)
        self.assertEqual("SA BA GK RK RD Ph", stringify_cards(cards), "Treppe - Phönix am Ende")

        cards = parse_cards("Ph RK BA SA GD RD")
        get_figure(cards, 10, shift_phoenix=True)
        self.assertEqual("SA BA RK Ph GD RD", stringify_cards(cards), "Treppe - Phönix Phönix an 4. Stelle")

        cards = parse_cards("RK GK BA Ph GD RD")
        get_figure(cards, 10, shift_phoenix=True)
        self.assertEqual("BA Ph GK RK GD RD", stringify_cards(cards), "Treppe - Phönix Phönix an 2. Stelle")

        cards = parse_cards("RK GA BA Ph SA")
        get_figure(cards, 10, shift_phoenix=True)
        self.assertEqual("SA BA GA RK Ph", stringify_cards(cards), "Fullhouse - Phönix am Ende")

        cards = parse_cards("RK GK BK Ph SA")
        get_figure(cards, 10, shift_phoenix=True)
        self.assertEqual("SA Ph BK GK RK", stringify_cards(cards), "Fullhouse - Phönix an 2. Stelle")

        cards = parse_cards("RK GK BA Ph SA")
        get_figure(cards, 10, shift_phoenix=True)
        self.assertEqual("SA BA Ph GK RK", stringify_cards(cards), "Fullhouse - Phönix in der Mitte")

        cards = parse_cards("GK BB SZ Ph BD")
        get_figure(cards, 10, shift_phoenix=True)
        self.assertEqual("Ph GK BD BB SZ", stringify_cards(cards), "Straße - Phönix am Anfang")

        cards = parse_cards("BD GK R9 SZ Ph")
        get_figure(cards, 10, shift_phoenix=True)
        self.assertEqual("GK BD Ph SZ R9", stringify_cards(cards), "Straße - Phönix in der Mitte")

        cards = parse_cards("GK BB GA Ph BD")
        get_figure(cards, 10, shift_phoenix=True)
        self.assertEqual("GA GK BD BB Ph", stringify_cards(cards), "Straße - Phönix am Ende")

    def test_build_combinations(self):
        # Straßen zählen
        combis = build_combinations(parse_cards("Ph GK BD RB RZ R9 R8 R7 R6 B5 G4 G3 B2 Ma"))
        self.assertEqual(381, len(combis), "381 Kombinationen sind möglich")
        self.assertEqual(352, len([1 for combi, figure in combis if figure[0] == STREET]), "352 Straßen sind möglich")

        # Drillinge, Straßen und Bomben zählen
        # Superblatt (3 Bomben + Phönix): 1576 Kombis = 3 Bomben, 360 Fullhouse, 64 5erStraßen, 174 2erTreppen,
        #                                   684 3erTreppen, 216 4erTreppen, 30 Drillinge, 31 Paare, 14 Einzelkarten
        combis = build_combinations(parse_cards("Ph R5 S4 B4 G4 R4 S3 B3 G3 R3 S2 B2 G2 R2"))  # Superblatt
        self.assertEqual(1576, len(combis), "1576 Kombinationen sind möglich")
        self.assertEqual(30, len([1 for combi, figure in combis if figure[0] == TRIPLE]), "30 Drillinge sind möglich")
        self.assertEqual(64, len([1 for combi, figure in combis if figure[0] == STREET]), "64 Straßen sind möglich")
        self.assertEqual(3, len([1 for combi, figure in combis if figure[0] == BOMB]), "3 Bomben sind möglich")
        expected = ["4erBombe4", "4erBombe3", "4erBombe2", "5erStraße6", "5erStraße6"]  # Reihenfolge testen
        for (s, combi) in zip(expected, combis[:5]):
            self.assertEqual(s, stringify_figure(combi[1]))

        # Treppen und FullHouses zählen
        combis = build_combinations(parse_cards("G4 R4 B3 G3 R3 B2 G2 R2"))
        self.assertEqual(46, len(combis), "46 Kombinationen sind möglich")
        self.assertEqual(7, len([1 for combi, figure in combis if figure[0] == PAIR]), "7 Paare sind möglich")
        self.assertEqual(2, len([1 for combi, figure in combis if figure[0] == TRIPLE]), "2 Drillinge sind möglich")
        self.assertEqual(21, len([1 for combi, figure in combis if figure[0] == STAIR]), "21 Treppen sind möglich")
        self.assertEqual(8, len([1 for combi, figure in combis if figure[0] == FULLHOUSE]), "8 FullHouses sind möglich")

        # Konkrete Beispiele prüfen
        combis = build_combinations(parse_cards("BD GD RD BZ RZ"))
        expected = ("BD GD RD BZ RZ", "BD GD RD", "BD GD", "BD RD", "GD RD", "BZ RZ", "BD", "GD", "RD", "BZ", "RZ")
        expected2 = ("FullHouseD", "DrillingD",   "PaarD", "PaarD", "PaarD", "PaarZ", "Dame", "Dame", "Dame", "Zehn", "Zehn")
        self.assertEqual(len(expected), len(combis))
        for i, (combi, figure) in enumerate(combis):
            self.assertEqual(expected[i], stringify_cards(combi), f"Kombination nicht ok: {combi}")
            self.assertEqual(expected2[i], stringify_figure(figure), f"Kombination nicht ok: {figure}")

        combis = build_combinations(parse_cards("Ph G9 B8 B7 R6 R4 Hu"))  # Straße mit Phönix für die 5 Und Hund
        expected = ("Ph G9 B8 B7 R6", "G9 B8 B7 R6 Ph R4", "B8 B7 R6 Ph R4", "G9 Ph", "B8 Ph", "B7 Ph", "R6 Ph", "R4 Ph", "Ph", "G9", "B8", "B7", "R6", "R4", "Hu")
        expected2 = ("5erStraßeZ", "6erStraße9", "5erStraße8", "Paar9", "Paar8", "Paar7", "Paar6", "Paar4", "Phönix", "Neun", "Acht", "Sieben", "Sechs", "Vier", "Hund")
        self.assertEqual(len(expected), len(combis))
        for i, (combi, figure) in enumerate(combis):
            self.assertEqual(expected[i], stringify_cards(combi), f"Kombination nicht ok: {combi}")
            self.assertEqual(expected2[i], stringify_figure(figure), f"Kombination nicht ok: {figure}")

        combis = build_combinations(parse_cards("Ph GA BK BD RB"))  # Straße mit Phönix am Ende
        expected = ("GA BK BD RB Ph", "GA Ph", "BK Ph", "BD Ph", "RB Ph", "Ph", "GA", "BK", "BD", "RB")
        expected2 = ("5erStraßeA", "PaarA", "PaarK", "PaarD", "PaarB", "Phönix", "As", "König", "Dame", "Bube")
        self.assertEqual(len(expected), len(combis))
        for i, (combi, figure) in enumerate(combis):
            self.assertEqual(expected[i], stringify_cards(combi), f"Kombination nicht ok: {combi}")
            self.assertEqual(expected2[i], stringify_figure(figure), f"Kombination nicht ok: {figure}")

        combis = build_combinations(parse_cards("Ph BK BD RB GZ"))  # Straße mit Phönix am Anfang
        expected = ("Ph BK BD RB GZ", "BK Ph", "BD Ph", "RB Ph", "GZ Ph", "Ph", "BK", "BD", "RB", "GZ")
        expected2 = ("5erStraßeA", "PaarK", "PaarD", "PaarB", "PaarZ", "Phönix", "König", "Dame", "Bube", "Zehn")
        self.assertEqual(len(expected), len(combis))
        for i, (combi, figure) in enumerate(combis):
            self.assertEqual(expected[i], stringify_cards(combi), f"Kombination nicht ok: {combi}")
            self.assertEqual(expected2[i], stringify_figure(figure), f"Kombination nicht ok: {figure}")

    def test_remove_combinations(self):
        combis = remove_combinations(build_combinations(parse_cards("BD GD RD BZ RZ")), parse_cards("GD"))
        expected = ("BD RD", "BZ RZ", "BD", "RD", "BZ", "RZ")
        expected2 = ("PaarD", "PaarZ", "Dame", "Dame", "Zehn", "Zehn")
        self.assertEqual(len(expected), len(combis))
        for i, (combi, figure) in enumerate(combis):
            self.assertEqual(expected[i], stringify_cards(combi), f"Kombination nicht ok: {combi}")
            self.assertEqual(expected2[i], stringify_figure(figure), f"Kombination nicht ok: {figure}")

    def test_build_action_space(self):
        # Passen und 4 Paare
        combis = build_action_space(build_combinations(parse_cards("RA Ph SZ BZ RB SB")), (PAIR, 2, 10), 0)
        expected = ('', "RA Ph", "RB Ph", "RB SB", "SB Ph")
        expected2 = ("Passen", "PaarA", "PaarB", "PaarB", "PaarB")
        self.assertEqual(len(expected), len(combis))
        for i, (combi, figure) in enumerate(combis):
            # print(stringify_cards(combi))
            self.assertEqual(expected[i], stringify_cards(combi), f"Kombination nicht ok: {combi}")
            self.assertEqual(expected2[i], stringify_figure(figure), f"Kombination nicht ok: {figure}")

        # Bombe
        combis = build_action_space(build_combinations(parse_cards("SA SB GB BB RB")), (STREET, 5, 10), 0)
        expected = ('', "SB GB BB RB")
        expected2 = ("Passen", "4erBombeB")
        self.assertEqual(len(expected), len(combis))
        for i, (combi, figure) in enumerate(combis):
            self.assertEqual(expected[i], stringify_cards(combi), f"Kombination nicht ok: {combi}")
            self.assertEqual(expected2[i], stringify_figure(figure), f"Kombination nicht ok: {figure}")

        # Phönix auf Drache
        combis = build_action_space(build_combinations(parse_cards("Ph SA")), (SINGLE, 1, 15), 0)
        expected = ('',)
        expected2 = ("Passen",)
        self.assertEqual(len(expected), len(combis))
        for i, (combi, figure) in enumerate(combis):
            # print(stringify_cards(combi))
            self.assertEqual(expected[i], stringify_cards(combi), f"Kombination nicht ok: {combi}")
            self.assertEqual(expected2[i], stringify_figure(figure), f"Kombination nicht ok: {figure}")

        # Wunsch 10
        combis = build_action_space(build_combinations(parse_cards("SA BD GZ R9")), (SINGLE, 1, 8), 10)
        expected = ("GZ",)
        expected2 = ("Zehn",)
        self.assertEqual(len(expected), len(combis))
        for i, (combi, figure) in enumerate(combis):
            self.assertEqual(expected[i], stringify_cards(combi), f"Kombination nicht ok: {combi}")
            self.assertEqual(expected2[i], stringify_figure(figure), f"Kombination nicht ok: {figure}")

        # Anspiel
        combis = build_action_space(build_combinations(parse_cards("SA BD GZ R9")), (0, 0, 0), 0)
        expected = ("SA", "BD", "GZ", "R9")
        expected2 = ("As", "Dame", "Zehn", "Neun")
        self.assertEqual(len(expected), len(combis))
        for i, (combi, figure) in enumerate(combis):
            self.assertEqual(expected[i], stringify_cards(combi), f"Kombination nicht ok: {combi}")
            self.assertEqual(expected2[i], stringify_figure(figure), f"Kombination nicht ok: {figure}")

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
                self.assertAlmostEqual(f1, f2, 6, f"Statistik für Beispiel 1.{k} nicht ok")

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
        expected.setdefault(tuple(parse_cards("B8")), (0.2, 0.0, 0.6, 0.0, 0.2, 0))
        statistic = calc_statistic(0, hand, build_combinations(hand), number_of_cards, trick_figure, hand + hidden)
        for combi in expected:
            result = statistic[combi]
            for k, (f1, f2) in enumerate(zip(expected[combi], result)):
                self.assertAlmostEqual(f1, f2, 6, f"Statistik für Beispiel 2.{k} nicht ok")

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
        expected.setdefault(tuple(parse_cards("G9 S9")), (0.102564102564103, 0.102564102564103, 0.102564102564103, 0.102564102564103, 0.017094017094017, 0.017094017094017))
        expected.setdefault(tuple(parse_cards("B8 G8")), (0.051282051282051, 0.051282051282051, 0.119658119658120, 0.119658119658120, 0.051282051282051, 0.051282051282051))
        expected.setdefault(tuple(parse_cards("RZ")), (0.25, 0.25, 0.15, 0.15, 0.1, 0.1))
        expected.setdefault(tuple(parse_cards("B8")), (0.1, 0.1, 0.3, 0.3, 0.1, 0.1))
        statistic = calc_statistic(0, hand, build_combinations(hand), number_of_cards, trick_figure, hand + hidden)
        for combi in expected:
            result = statistic[combi]
            for k, (f1, f2) in enumerate(zip(expected[combi], result)):
                self.assertAlmostEqual(f1, f2, 6, f"Statistik für Beispiel 3.{k} nicht ok")

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
                self.assertAlmostEqual(f1, f2, 6, f"Statistik für Beispiel 4.{k} nicht ok")

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
                self.assertAlmostEqual(f1, f2, 6, f"Statistik für Beispiel 5.{k} nicht ok")

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
                self.assertAlmostEqual(f1, f2, 6, f"Statistik für Beispiel 6.{k} nicht ok")

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
                self.assertAlmostEqual(f1, f2, 6, f"Statistik für Beispiel 7.{k} nicht ok")

    # todo Test schlägt fehl. Vermutlich wird nicht berücksichtigt, dass der Gegner spielen kann was auch immer, die Bombe ist besser.
    # def test_calc_statistic_2(self):
    #     # die Karten werden gerade verteilt
    #     hand = parse_cards("RA RK RD RB RZ R9 R8 R7 R6 R5 R4 R3 R2 Ma")
    #     combis = build_combinations(hand)
    #     number_of_cards = [len(hand), 8, 8, 8]
    #     trick_figure = (0, 0, 0)
    #     unplayed_cards = deck
    #     statistic = calc_statistic(0, hand, combis, number_of_cards, trick_figure, unplayed_cards)
    #     bomb = tuple(parse_cards("RA RK RD RB RZ R9 R8 R7 R6 R5 R4 R3 R2"))
    #     result = statistic[bomb]
    #     expected = 1.0, 1.0, 0, 0, 0, 0
    #     for k, (f1, f2) in enumerate(zip(expected, result)):
    #         self.assertAlmostEqual(f1, f2, 6, f"Statistik für Wert {k} nicht ok")

    def test_probability_of_possible_hands(self):
        test = [
            # unplayed cards, k, figure, sum(matches), len(hands), p, msg
            ("Dr RB G6 B5 S4 R3 R2", 4, (1, 1, 11), 20, 35, 0.5714285714285714, "Einzelkarte"),
            ("Dr RK GK BD SB RB R2", 5, (1, 1, 11), 20, 21, 0.9523809523809523, "Einzelkarte mit 2 Buben"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 3, (1, 1, 10), 100, 120, 0.8333333333333334, "Einzelkarte aus einer 4er-Bombe"),
            ("Dr RK GK BB SB RB R2", 5, (2, 2, 11), 18, 21, 0.8571428571428571, "Pärchen ohne Phönix"),
            ("Ph RK GK BD SB RB R2", 5, (2, 2, 11), 18, 21, 0.8571428571428571, "Pärchen mit Phönix"),
            ("SK RK GB BB SB R3 R2", 4, (3, 3, 11), 4, 35, 0.11428571428571428, "Drilling ohne Phönix"),
            ("Ph RK GB BB SB R3 R2", 4, (3, 3, 11), 13, 35, 0.37142857142857144, "Drilling mit Phönix"),
            ("RK GK BD SD SB RB BB", 6, (4, 6, 13), 3, 7, 0.42857142857142855, "3er-Treppe ohne Phönix"),
            ("Ph GK BD SD SB RB BB", 6, (4, 6, 13), 3, 7, 0.42857142857142855, "3er-Treppe mit Phönix"),
            ("SB RZ R9 G9 R8 G8 B4", 9, (4, 4, 10), 0, 0, 0.0, "2er-Treppe nicht möglich"),
            ("RK GK BD SD GD R9 B2", 6, (4, 4, 13), 5, 7, 0.7142857142857143, "2er-Treppe aus Fullhouse"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 10), 12, 210, 0.05714285714285714, "2er-Treppe, Phönix übrig"),
            ("RK GK BD SB RB BB S2", 6, (5, 5, 11), 2, 7, 0.2857142857142857, "Fullhouse ohne Phönix"),
            ("Ph GK BD SB RB BB S2", 6, (5, 5, 11), 3, 7, 0.42857142857142855, "Fullhouse mit Phönix für Paar"),
            ("RK GK BD SB RB BZ Ph", 6, (5, 5, 11), 2, 7, 0.2857142857142857, "Fullhouse mit Phönix für Drilling"),
            ("BK RK SK BZ RZ R9 S9 RB", 7, (5, 5, 13), 5, 8, 0.625, "Fullhouse und zusätzliches Pärchen"),
            ("BK RK SK GK R9 S9 RB S2", 7, (5, 5, 13), 6, 8, 0.75, "Fullhouse aus Bombe"),
            ("BK RK SK G9 R9 S9 RB S2", 7, (5, 5, 13), 5, 8, 0.625, "Fullhouse aus 2 Drillinge"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 5, (5, 5, 10), 9, 126, 0.07142857142857142, "FullHouseZ, Test 63"),
            ("Ph RZ GZ BZ B4 R8 G8", 6, (5, 5, 10), 7, 7, 1.0, "FullHouseZ, Test 80, vereinfacht"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 6, (5, 5, 10), 22, 84, 0.2619047619047619, "FullHouseZ, Test 80"),
            ("RA GK BD SB RZ B9 R3", 6, (6, 5, 13), 2, 7, 0.2857142857142857, "Straße ohne Phönix"),
            ("RA GK BD RZ B9 R3 Ph", 6, (6, 5, 13), 2, 7, 0.2857142857142857, "Straße mit Phönix (Lücke gefüllt)"),
            ("SK RK GD BB RZ B9 R8 R2", 6, (6, 5, 13), 5, 28, 0.17857142857142858, "Straße ohne Phönix (aus 8 Karten)"),
            ("Ph RK GD BB RZ B9 R8 R2", 6, (6, 5, 13), 13, 28, 0.4642857142857143, "Straße mit Phönix 2 (aus 8 Karten)"),
            ("SK RK GD BB RZ B9 R8 Ph", 6, (6, 5, 13), 18, 28, 0.6428571428571429, "Straße mit Phönix (verlängert)"),
            ("SA RK GD BB RZ B9 R8 Ph", 6, (6, 5, 13), 13, 28, 0.4642857142857143, "Straße mit Phönix (verlängert, 2)"),
            ("BK SD BD RB BZ B9 R3", 6, (6, 5, 13), 3, 7, 0.42857142857142855, "Straße, keine Bombe"),
            ("BK SD BD BB BZ B9 R3", 6, (6, 5, 13), 2, 7, 0.2857142857142857, "Straße, mit Farbbombe"),
            ("BK BD BB BZ B9 RK RD RB RZ R9 G2 G3 G4", 11, (6, 5, 13), 73, 78, 0.9358974358974359, "Straße, mit 2 Farbbomben (1)"),
            ("BK SD BD BB BZ B9 RK RD RB RZ R9 G2 G3", 11, (6, 5, 13), 74, 78, 0.9487179487179487, "Straße, mit 2 Farbbomben (2)"),
            ("BK SD BD BB BZ B9 RK RD RB SB RZ R9 G2", 11, (6, 5, 13), 75, 78, 0.9615384615384616, "Straße, mit 2 Farbbomben (3)"),
            ("GA GK GD GB GZ G9 R8 G7 G6 G5 G4 G3 Ph", 5, (6, 5, 11), 6, 1287, 0.004662004662004662, "5erStraßeB, Test 20"),
            ("SK GB GZ G9 G8 G7 RB RZ R9 R8 R7 S4 Ph", 6, (6, 5, 11), 492, 1716, 0.2867132867132867, "5erStraßeB, Test 35"),
            ("RK GB BB SB RB BZ R2", 5, (7, 4, 11), 3, 21, 0.14285714285714285, "4er-Bombe"),
            ("BK BB BZ B9 B8 B7 B2", 5, (7, 5, 11), 1, 21, 0.047619047619047616, "Farbbombe"),
            ("BK BD BB BZ B9 RK RD RB RZ R9 S2 S3", 11, (7, 5, 13), 12, 12, 1.0, "2 Farbbomben in 12 Karten"),
            ("BK BD BB BZ B9 RK RD RB RZ R9 S2 S3 G7", 11, (7, 5, 13), 53, 78, 0.6794871794871795, "2 Farbbomben in 13 Karten"),
        ]
        for t in test:
            print(t[6])

            # possible_hands
            matches, hands = possible_hands(parse_cards(t[0]), t[1], t[2])
            #for match, hand in zip(matches, hands):
            #    print(stringify_cards(hand), match)
            self.assertEqual(t[3], sum(matches))
            self.assertEqual(t[4], len(hands))
            self.assertEqual(t[4], len(list(zip(matches, hands))))
            self.assertAlmostEqual(t[5], sum(matches) / len(hands) if len(hands) else 0.0, places=15, msg=t[6])

            # probability_of_hands
            p = probability_of_hand(parse_cards(t[0]), t[1], t[2])
            self.assertAlmostEqual(t[5], p, places=15, msg=t[6])

    def test_probability_of_possible_hands_hi(self):
        test = [
            # unplayed cards, k, figure, sum(matches), len(hands), p, msg
            ("Dr RB G6 B5 S4 R3 R2", 4, (1, 1, 11), 20, 35, 0.5714285714285714, "Einzelkarte"),
            ("Dr RB SB B5 S4 R3 R2", 5, (1, 1, 11), 15, 21, 0.7142857142857143, "Einzelkarte mit 2 Buben"),
            ("Ph RB G6 B5 S4 R3 R2", 5, (1, 1, 11), 15, 21, 0.7142857142857143, "Einzelkarte mit Phönix"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 3, (1, 1, 9), 110, 120, 0.9166666666666666, "Einzelkarte aus einer 4er-Bombe"),
            ("Dr RK GK BB SB RB R2", 5, (2, 2, 11), 10, 21, 0.47619047619047616, "Pärchen ohne Phönix"),
            ("Ph RK GK BD SB RB R2", 5, (2, 2, 11), 19, 21, 0.9047619047619048, "Pärchen mit Phönix"),
            ("SK RK GB BB SB R3 R2", 4, (3, 3, 10), 4, 35, 0.11428571428571428, "Drilling ohne Phönix"),
            ("Ph RK GB BB SB R3 R2", 4, (3, 3, 10), 13, 35, 0.37142857142857144, "Drilling mit Phönix"),
            ("RK GK BD SD SB RB BB", 6, (4, 6, 12), 3, 7, 0.42857142857142855, "3er-Treppe ohne Phönix"),
            ("Ph GK BD SD SB RB BB", 6, (4, 6, 12), 3, 7, 0.42857142857142855, "3er-Treppe mit Phönix"),
            ("SB RZ R9 G9 R8 G8 B4", 9, (4, 4, 9), 0, 0, 0.0, "2er-Treppe nicht möglich"),
            ("RK GK BD SD GD R9 B2", 6, (4, 4, 12), 5, 7, 0.7142857142857143, "2er-Treppe aus Fullhouse"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 9), 13, 210, 0.06190476190476191, "2er-Treppe, Phönix übrig"),
            ("RK GK BD SB RB BB S2", 6, (5, 5, 10), 2, 7, 0.2857142857142857, "Fullhouse ohne Phönix"),
            ("Ph GK BD SB RB BB S2", 6, (5, 5, 10), 3, 7, 0.42857142857142855, "Fullhouse mit Phönix für Paar"),
            ("RK GK BD SB RB BZ Ph", 6, (5, 5, 10), 2, 7, 0.2857142857142857, "Fullhouse mit Phönix für Drilling"),
            ("BK RK SK BZ RZ R9 S9 RB", 7, (5, 5, 12), 5, 8, 0.625, "Fullhouse und zusätzliches Pärchen"),
            ("BK RK SK GK R9 S9 RB S2", 7, (5, 5, 12), 6, 8, 0.75, "Fullhouse aus Bombe"),
            ("BK RK SK G9 R9 S9 RB S2", 7, (5, 5, 12), 5, 8, 0.625, "Fullhouse aus 2 Drillinge"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 5, (5, 5, 9), 9, 126, 0.07142857142857142, "FullHouseZ, Test 63"),
            ("Ph RZ GZ BZ B4 R8 G8", 6, (5, 5, 9), 7, 7, 1.0, "FullHouseZ, Test 80, vereinfacht"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 6, (5, 5, 9), 22, 84, 0.2619047619047619, "FullHouseZ, Test 80"),
            ("RA GK BD SB RZ B9 R3", 6, (6, 5, 12), 3, 7, 0.42857142857142855, "Straße ohne Phönix"),
            ("RA GK BD RZ B9 R3 Ph", 6, (6, 5, 12), 3, 7, 0.42857142857142855, "Straße mit Phönix (Lücke gefüllt)"),
            ("SK RK GD BB RZ B9 R8 R2", 6, (6, 5, 12), 5, 28, 0.17857142857142858, "Straße ohne Phönix (aus 8 Karten)"),
            ("Ph RK GD BB RZ B9 R8 R2", 6, (6, 5, 12), 13, 28, 0.4642857142857143, "Straße mit Phönix 2 (aus 8 Karten)"),
            ("SK RK GD BB RZ B9 R8 Ph", 6, (6, 5, 12), 18, 28, 0.6428571428571429, "Straße mit Phönix (verlängert)"),
            ("SA RK GD BB RZ B9 R8 Ph", 6, (6, 5, 12), 18, 28, 0.6428571428571429, "Straße mit Phönix (verlängert, 2)"),
            ("BK SD BD RB BZ B9 R3", 6, (6, 5, 12), 3, 7, 0.42857142857142855, "Straße, keine Bombe"),
            ("BK SD BD BB BZ B9 R3", 6, (6, 5, 12), 2, 7, 0.2857142857142857, "Straße, mit Farbbombe"),
            ("BK BD BB BZ B9 RK RD RB RZ R9 G2 G3 G4", 11, (6, 5, 12), 73, 78, 0.9358974358974359, "Straße, mit 2 Farbbomben (1)"),
            ("BK SD BD BB BZ B9 RK RD RB RZ R9 G2 G3", 11, (6, 5, 12), 74, 78, 0.9487179487179487, "Straße, mit 2 Farbbomben (2)"),
            ("BK SD BD BB BZ B9 RK RD RB SB RZ R9 G2", 11, (6, 5, 12), 75, 78, 0.9615384615384616, "Straße, mit 2 Farbbomben (3)"),
            ("GA GK GD GB GZ G9 R8 G7 G6 G5 G4 G3 Ph", 5, (6, 5, 10), 19, 1287, 0.014763014763014764, "5erStraßeB, Test 20"),
            ("SK GB GZ G9 G8 G7 RB RZ R9 R8 R7 S4 Ph", 6, (6, 5, 10), 512, 1716, 0.29836829836829837, "5erStraßeB, Test 35"),
            ("RK GB BB SB RB BZ R2", 5, (7, 4, 10), 3, 21, 0.14285714285714285, "4er-Bombe"),
            ("BK BB BZ B9 B8 B7 B2", 5, (7, 5, 10), 1, 21, 0.047619047619047616, "Farbbombe"),
            ("BK BD BB BZ B9 RK RD RB RZ R9 S2 S3", 11, (7, 5, 12), 12, 12, 1.0, "2 Farbbomben in 12 Karten"),
            ("BK BD BB BZ B9 RK RD RB RZ R9 S2 S3 G7", 11, (7, 5, 12), 53, 78, 0.6794871794871795, "2 Farbbomben in 13 Karten"),
        ]
        for t in test:
            print(t[6])

            # possible_hands
            matches, hands = possible_hands_hi(parse_cards(t[0]), t[1], t[2])
            #for match, hand in zip(matches, hands):
            #    print(stringify_cards(hand), match)
            self.assertEqual(t[3], sum(matches))
            self.assertEqual(t[4], len(hands))
            self.assertEqual(t[4], len(list(zip(matches, hands))))
            self.assertAlmostEqual(t[5], sum(matches) / len(hands) if len(hands) else 0.0, places=15, msg=t[6])

            # probability_of_hands
            #p = probability_of_hand_hi(parse_cards(t[0]), t[1], t[2])
            #self.assertAlmostEqual(t[5], p, places=15, msg=t[6])


if __name__ == "__main__":
    unittest.main()
