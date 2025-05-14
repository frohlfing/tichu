import unittest
# noinspection PyProtectedMember
from src.lib.combinations import _figures, _figures_index, _figurelabels, _figurelabels_index, validate_figure
from src.lib.combinations import *
from src.lib.cards import *


# noinspection DuplicatedCode
class TestCombinations(unittest.TestCase):
    def test_validate_figure(self):
        self.assertTrue(validate_figure((0, 0, 0)))
        self.assertTrue(validate_figure((1, 1, 6)))
        self.assertTrue(validate_figure((2, 2, 5)))
        self.assertTrue(validate_figure((3, 3, 6)))
        self.assertTrue(validate_figure((4, 14, 8)))
        self.assertTrue(validate_figure((5, 5, 2)))
        self.assertTrue(validate_figure((6, 14, 14)))
        self.assertTrue(validate_figure((7, 13, 14)))
        self.assertFalse(validate_figure((6, 11, 10)))

    def test_parse_and_stringify_figure(self):
        self.assertTrue(len(_figures) == len(_figures_index) == len(_figurelabels) == len(_figurelabels_index) == 227, "es gibt 227 Kombinationsarten (inklusiv Passen)")
        for i in range(0, 227):
            figure = _figures[i]
            lb = stringify_figure(figure)
            self.assertEqual(figure, parse_figure(lb), f"Index nicht OK: {i}, {figure}, {lb}")

    def test_stringify_type(self):
        self.assertEqual(stringify_type(0), "pass")
        self.assertEqual(stringify_type(5, 6), "fullhouse")
        self.assertEqual(stringify_type(6), "street")
        self.assertEqual(stringify_type(6, 7), "street07")
        self.assertEqual(stringify_type(7), "bomb")

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


if __name__ == "__main__":
    unittest.main()
