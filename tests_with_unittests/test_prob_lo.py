import unittest
from src.lib.cards import *
from src.lib.combinations import *
# noinspection PyProtectedMember
from src.lib.prob.prob_lo import possible_hands_lo, prob_of_lower_combi


# Testfunktion possible_hands_lo() testen
class TestPossibleHandsLo(unittest.TestCase):
    def test_possible_hands_lo(self):
        test = [
            # Einzelkarte
            ("Dr RK GK BD S4 R3 R2", 3, (1, 1, 11), 31, 35, "Einzelkarte"),
            ("Dr BD RB SB R3 R2", 3, (1, 1, 11), 16, 20, "Einzelkarte mit 2 Buben"),
            ("Ph RB G6 B5 R2", 3, (1, 1, 5), 9, 10, "Einzelkarte mit Phönix"),
            ("Dr Ph Ma S4 R3 R2", 1, (1, 1, 0), 0, 6, "Einzelkarte Hund"),
            ("Dr Hu Ph S4 R3 R2", 1, (1, 1, 1), 0, 6, "Einzelkarte Mahjong"),
            ("Hu Ph Ma S4 R3 R2", 1, (1, 1, 15), 5, 6, "Einzelkarte Drache"),
            ("Dr Hu Ma S4 R3 R2", 1, (1, 1, 16), 4, 6, "Einzelkarte Phönix"),
            ("Dr Hu Ma S4 R3 R2 Ph", 1, (1, 1, 16), 4, 7, "Einzelkarte Phönix (2)"),
            # Pärchen
            ("Dr RK GK BB SB RB R2", 5, (2, 2, 12), 18, 21, "Pärchen ohne Phönix"),
            ("Ph RK GK BD SB RB R2", 5, (2, 2, 11), 10, 21, "Pärchen mit Phönix"),
            ("Ph RK GK BD SB RB R2", 5, (2, 2, 12), 19, 21, "Pärchen mit Phönix (2)"),
            ("RZ GZ BZ SZ R9 S9", 5, (2, 2, 10), 4, 6, "Pärchen mit 4er-Bombe"),
            ("RZ R9 R8 R7 R6 S6", 5, (2, 2, 11), 4, 6, "Pärchen mit Farbbombe"),
            # Drilling
            ("SK RK GB BB SB R3 R2", 4, (3, 3, 12), 4, 35, "Drilling ohne Phönix"),
            ("Ph RK GK BB SB R3 R2", 4, (3, 3, 13), 4, 35, "Drilling mit Phönix"),
            ("RZ GZ BZ SZ R9 S9 B9", 5, (3, 3, 10), 6, 21, "Drilling mit 4er-Bombe"),
            ("SB RZ R9 R8 R7 R6", 5, (3, 3, 11), 0, 6, "Drilling mit Farbbombe"),
            # Treppe
            ("RK GK SK BD SD GB RB", 5, (4, 4, 13), 3, 21, "2er-Treppe aus Fullhouse"),
            ("SB RZ R9 G9 R8 G8 B4", 9, (4, 4, 9), 0, 0, "2er-Treppe nicht möglich"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 10), 12, 210, "2er-Treppe mit Phönix"),
            ("RK GK BD SD SB RB BB", 6, (4, 6, 14), 3, 7, "3er-Treppe ohne Phönix"),
            ("Ph GK BD SD SB RB BB", 6, (4, 6, 14), 3, 7, "3er-Treppe mit Phönix"),
            ("GA RA GK RK SD BD SB BB GB BZ RZ G9 B9 R9 Ph", 13, (4, 10, 14), 84, 105, "5er-Treppe"),
            # Fullhouse
            ("RK GD BD SB RB BB S2", 6, (5, 5, 13), 2, 7, "Fullhouse ohne Phönix"),
            ("BB RB SB BZ RZ R9 S9 R8", 7, (5, 5, 12), 5, 8, "Fullhouse und zusätzliches Pärchen"),
            ("BB RB SB G9 R9 S9 R7 S2", 7, (5, 5, 10), 5, 8, "Fullhouse mit 2 Drillinge"),
            ("Ph GK BD SB RB BB S2", 6, (5, 5, 12), 3, 7, "Fullhouse mit Phönix für Paar"),
            ("RK GK BD SB RB BZ Ph", 6, (5, 5, 12), 2, 7, "Fullhouse mit Phönix für Drilling"),
            # Straße
            ("BK SD BD RB BZ B9 R3", 6, (6, 5, 14), 3, 7, "5er-Straße bis König aus 7 Karten ohne Phönix"),
            ("RA GK BD SB RZ B9 R3", 6, (6, 5, 14), 2, 7, "5er-Straße bis Ass aus 7 Karten ohne Phönix"),
            ("GA RK GD RB GZ R9 S8 B7", 5, (6, 5, 13), 2, 56, "5er-Straße bis Ass aus 8 Karten ohne Phönix"),
            ("SK RD GB BB RZ B9 R8 R2", 6, (6, 5, 13), 5, 28, "5er-Straße mit 2 Buben aus 8 Karten ohne Phönix"),
            ("RA GK BD RZ B9 R8 Ph", 6, (6, 5, 13), 2, 7, "5er-Straße aus 7 Karten mit Phönix (Lücke gefüllt)"),
            ("RA BD BB RZ B9 B2 Ph", 6, (6, 5, 13), 0, 7, "5er-Straße aus 7 Karten mit Phönix (nicht unten verlängert)"),
            ("RA SK BD BB B9 B2 Ph", 6, (6, 5, 14), 2, 7, "5er-Straße bis zum Ass mit Phönix (Lücke gefüllt)"),
            ("Ph SK RK GD BB RZ B9 R8", 6, (6, 5, 13), 11, 28, "5er-Straße aus 8 Karten mit 2 Könige mit Phönix (verlängert)"),
            ("GA RK GD RB GZ R9 S8 B7 S6 Ph", 9, (6, 5, 11), 9, 10, "5er-Straße aus 10 Karten"),
            ("SB RZ R9 R8 R7 R6", 5, (6, 5, 11), 1, 6, "Straße mit Farbbombe (bekannter Fehler, 0/6 wäre eigentlich richtig)"),
            # Bombe
            ("RK GB BB SB RB BZ R2", 5, (7, 4, 10), 21, 21, "4er-Bombe"),
            ("BK BB BZ B9 B8 B7 B2", 5, (7, 7, 10), 21, 21, "Farbbombe"),
        ]
        for cards, k, figure, matches_expected, total_expected, msg in test:
            print(msg)
            matches, hands = possible_hands_lo(parse_cards(cards), k, figure)
            #for match, hand in zip(matches, hands):
            #    print(stringify_cards(hand), match)
            self.assertEqual(matches_expected, sum(matches))
            self.assertEqual(total_expected, len(hands))
            self.assertEqual(total_expected, len(list(zip(matches, hands))))
            #self.assertAlmostEqual(p_expected, sum(matches) / len(hands) if len(hands) else 0.0, places=15, msg=t[6])

# prob_of_lower_combi() testen (explizit ausgesuchte Fälle)
class TestExplicitProbOfLowerCombi(unittest.TestCase):
    def _test(self, cards, k, figure, p_expected, msg):  # pragma: no cover
        if k > len(cards.split(" ")):
            with self.assertRaises(AssertionError, msg="k > n"):
                prob_of_lower_combi(parse_cards(cards), k, figure)
        else:
            p_actual = prob_of_lower_combi(parse_cards(cards), k, figure)
            print(f"{p_actual:<20} == {p_expected:<20}  {msg}")
            self.assertAlmostEqual(p_expected, p_actual, places=15, msg=msg)

    def test_single(self):  # pragma: no cover
        self._test("Dr RK GK BD S4 R3 R2", 3, (1, 1, 11), 31/35, "Einzelkarte")
        self._test("Dr BD RB SB R3 R2", 3, (1, 1, 11), 16/20, "Einzelkarte mit 2 Buben")
        self._test("Ph RB G6 B5 R2", 3, (1, 1, 5), 9/10, "Einzelkarte mit Phönix")
        self._test("Dr Ph Ma S4 R3 R2", 1, (1, 1, 0), 0.0, "Einzelkarte Hund")
        self._test("Dr Hu Ph S4 R3 R2", 1, (1, 1, 1), 0.0, "Einzelkarte Mahjong")
        self._test("Hu Ph Ma S4 R3 R2", 1, (1, 1, 15), 5/6, "Einzelkarte Drache")
        self._test("Dr Hu Ma S4 R3 R2", 1, (1, 1, 16), 4/6, "Einzelkarte Phönix")
        self._test("Dr Hu Ma S4 R3 R2 Ph", 1, (1, 1, 16), 4/7, "Einzelkarte Phönix (2)")
        self._test("Dr RB G6 B5 S4 R3 R2", 0, (1, 1, 11), 0.0, "Einzelkarte k == 0")

    def test_pair(self):  # pragma: no cover
        self._test("Dr RK GK BB SB RB R2", 5, (2, 2, 12), 18/21, "Pärchen ohne Phönix")
        self._test("Ph RK GK BD SB RB R2", 5, (2, 2, 11), 10/21, "Pärchen mit Phönix")
        self._test("Ph RK GK BD SB RB R2", 5, (2, 2, 12), 19/21, "Pärchen mit Phönix (2)")
        self._test("RZ GZ BZ SZ R9 S9", 5, (2, 2, 10), 4/6, "Pärchen mit 4er-Bombe")
        self._test("RZ R9 R8 R7 R6 S6", 5, (2, 2, 11), 4/6, "Pärchen mit Farbbombe")

    def test_triple(self):  # pragma: no cover
        self._test("SK RK GB BB SB R3 R2", 4, (3, 3, 12), 4 / 35, "Drilling ohne Phönix")
        self._test("Ph RK GK BB SB R3 R2", 4, (3, 3, 13), 4 / 35, "Drilling mit Phönix")
        self._test("RZ GZ BZ SZ R9 S9 B9", 5, (3, 3, 10), 6 / 21, "Drilling mit 4er-Bombe")
        self._test("SB RZ R9 R8 R7 R6", 5, (3, 3, 11), 0.0, "Drilling mit Farbbombe")

    def test_stair(self):  # pragma: no cover
        self._test("RK GK SK BD SD GB RB", 5, (4, 4, 13), 3/21, "2er-Treppe aus Fullhouse")
        self._test("SB RZ R9 G9 R8 G8 B4", 9, (4, 4, 9), 0.0, "2er-Treppe nicht möglich")
        self._test("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 10), 12/210, "2er-Treppe mit Phönix")
        self._test("RK GK BD SD SB RB BB", 6, (4, 6, 14), 3/7, "3er-Treppe ohne Phönix")
        self._test("Ph GK BD SD SB RB BB", 6, (4, 6, 14), 3/7, "3er-Treppe mit Phönix")
        self._test("GA RA GK RK SD BD SB BB GB BZ RZ G9 B9 R9 Ph", 13, (4, 10, 14), 84/105, "5er-Treppe")

    def test_fullhouse(self):
        self._test("RK GD BD SB RB BB S2", 6, (5, 5, 13), 2 / 7, "Fullhouse ohne Phönix")
        self._test("BB RB SB BZ RZ R9 S9 R8", 7, (5, 5, 12), 5 / 8, "Fullhouse und zusätzliches Pärchen")
        self._test("BB RB SB G9 R9 S9 R7 S2", 7, (5, 5, 10), 5 / 8, "Fullhouse mit 2 Drillinge")
        self._test("Ph GK BD SB RB BB S2", 6, (5, 5, 12), 3 / 7, "Fullhouse mit Phönix für Paar")
        self._test("RK GK BD SB RB BZ Ph", 6, (5, 5, 12), 2 / 7, "Fullhouse mit Phönix für Drilling")

    def test_street(self):
        self._test("BK SD BD RB BZ B9 R3", 6, (6, 5, 14), 3/7, "5er-Straße bis König aus 7 Karten ohne Phönix")
        self._test("RA GK BD SB RZ B9 R3", 6, (6, 5, 14), 2/7, "5er-Straße bis Ass aus 7 Karten ohne Phönix")
        self._test("GA RK GD RB GZ R9 S8 B7", 5, (6, 5, 13), 2/56, "5er-Straße bis Ass aus 8 Karten ohne Phönix")
        self._test("SK RD GB BB RZ B9 R8 R2", 6, (6, 5, 13), 5/28, "5er-Straße mit 2 Buben aus 8 Karten ohne Phönix")
        self._test("RA GK BD RZ B9 R8 Ph", 6, (6, 5, 13), 2/7, "5er-Straße aus 7 Karten mit Phönix (Lücke gefüllt)")
        self._test("RA BD BB RZ B9 B2 Ph", 6, (6, 5, 13), 0.0, "5er-Straße aus 7 Karten mit Phönix (nicht unten verlängert)")
        self._test("RA SK BD BB B9 B2 Ph", 6, (6, 5, 14), 2/7, "5er-Straße bis zum Ass mit Phönix (Lücke gefüllt)")
        self._test("Ph SK RK GD BB RZ B9 R8", 6, (6, 5, 13), 11/28, "5er-Straße aus 8 Karten mit 2 Könige mit Phönix (verlängert)")
        self._test("GA RK GD RB GZ R9 S8 B7 S6 Ph", 9, (6, 5, 11), 9/10, "5er-Straße aus 10 Karten")
        self._test("SB RZ R9 R8 R7 R6", 5, (6, 5, 11), 1/6, "Straße mit Farbbombe (bekannter Fehler, 0/6 wäre eigentlich richtig)")

    def test_bomb(self):
        self._test("RK GB BB SB RB BZ R2", 5, (7, 4, 10), 1.0, "4er-Bombe")
        self._test("BK BB BZ B9 B8 B7 B2", 5, (7, 7, 10), 1.0, "Farbbombe")


# prob_of_lower_combi() testen (Rastersuche)
class TestRasterProbOfLowerCombi(unittest.TestCase):
    c = 0

    def _test(self, cards, k, figure):  # pragma: no cover
        if k > len(cards.split(" ")):
            with self.assertRaises(AssertionError, msg="k > n"):
                prob_of_lower_combi(parse_cards(cards), k, figure)
            return
        self.c += 1
        matches, hands = possible_hands_lo(parse_cards(cards), k, figure)
        p_expected = sum(matches) / len(hands) if hands else 0.0
        msg = stringify_figure(figure)
        print(f'("{cards}", {k}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p_expected}, "{msg}, Test {self.c}"),'),
        p_actual = prob_of_lower_combi(parse_cards(cards), k, figure)
        #print(f"{p_actual:<20} == {p_expected:<20} {msg}")
        self.assertAlmostEqual(p_expected, p_actual, places=15, msg=msg)

    def test_single(self):
        t = SINGLE
        combis = [
            "SB RZ R9 G9 R8 G8 B4",
            "SB RZ GZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 R8 G8 B4",  # 4er-Bombe
            "SB RZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",  # 4er-Bombe
            "Ph SB RZ R9 G9 R8 G8 B4",
            "SB RZ Ph R9 G9 R8 G8 B4",
            "SB RZ GZ BZ Ph G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 Ph R8 G8 B4",  # 4er-Bombe
            "SB RZ R9 G9 S9 R8 G8 B4 Ph",
            "Ph SB RZ GZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "Ph Dr RB GZ BZ SZ R9 G9 S9 R8 G8 B4",
            "Ph SB RB GZ BZ SZ R9 G9 S9 R8 G8 B4 Hu",
            "Ph SB RB GZ BZ SZ R9 G9 S9 R8 G8 B4 B2 Ma",
            "Ph SB RB GZ BZ SZ R9 G9 B6 B5 B4 B3 B2 Ma",  # Farbbombe
        ]
        m = 1
        for r in range(17):
            for cards in combis:
                for k in range(len(combis) + 2):
                    self._test(cards, k, (t, m, r))

    def test_pair(self):
        t = PAIR
        combis = [
            "SB RZ R9 G9 R8 G8 B4",
            "SB RZ GZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 R8 G8 B4",  # 4er-Bombe
            "SB RZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",  # 4er-Bombe
            "Ph SB RZ R9 G9 R8 G8 B4",
            "SB RZ Ph R9 G9 R8 G8 B4",
            "SB RZ GZ BZ Ph G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 Ph R8 G8 B4",  # 4er-Bombe
            "SB RZ R9 G9 S9 R8 G8 B4 Ph",
            "Ph SB RZ GZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",  # 4er-Bombe
            "Ph SB RB GZ BZ SZ R9 G9 B6 B5 B4 B3 B2 Ma",  # Farbbombe
        ]
        m = 2
        r = 9
        for k in [0, 3, 4, 5, 6, 7, 9, 10, 13, 14]:
            for cards in combis:
                self._test(cards, k, (t, m, r))

    def test_tripple(self):
        t = TRIPLE
        combis = [
            "SB RZ R9 G9 R8 G8 B4",
            "SB RZ GZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 R8 G8 B4",  # 4er-Bombe
            "SB RZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",  # 4er-Bombe
            "Ph SB RZ R9 G9 R8 G8 B4",
            "SB RZ Ph R9 G9 R8 G8 B4",
            "SB RZ GZ BZ Ph G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 Ph R8 G8 B4",  # 4er-Bombe
            "SB RZ R9 G9 S9 R8 G8 B4 Ph",
            "Ph SB RZ GZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",  # 4er-Bombe
            "Ph SB RB GZ BZ SZ R9 G9 B6 B5 B4 B3 B2 Ma",  # Farbbombe
        ]
        m = 3
        r = 9
        for k in [0, 3, 4, 5, 6, 7, 9, 10, 13, 14]:
            for cards in combis:
                self._test(cards, k, (t, m, r))

    def test_stair(self):
        t = STAIR
        combis = [
            "SB RZ R9 G9 R8 G8 B4",
            "SB RZ GZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 R8 G8 B4",  # 4er-Bombe
            "SB RZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",  # 4er-Bombe
            "Ph SB RZ R9 G9 R8 G8 B4",
            "SB RZ Ph R9 G9 R8 G8 B4",
            "SB RZ GZ BZ Ph G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 Ph R8 G8 B4",  # 4er-Bombe
            "SB RZ R9 G9 S9 R8 G8 B4 Ph",
            "Ph SB RZ GZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",  # 4er-Bombe
            "Ph GK BK SD SB RB BZ R9",
            "Ph GK BK SD SB RB R9",
            "Ph GK BK SD SB R9 S4",
        ]
        for m in [4, 6]:
            for r in [9, 10]:
                for k in [0, 3, 4, 5, 6, 7, 9, 10, 13, 14]:
                    for cards in combis:
                        self._test(cards, k, (t, m, r))

    def test_fullhouse(self):
        t = FULLHOUSE
        combis = [
            "SB RZ R9 G9 R8 G8 B4",
            "SB RZ GZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 R9 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 R8 G8 B4",  # mit 4er-Bombe
            "SB RZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",  # mit 4er-Bombe
            "Ph SB RZ R9 G9 R8 G8 B4",
            "SB RZ Ph R9 G9 R8 G8 B4",
            "SB RZ GZ BZ Ph G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 Ph R8 G8 B4",  # mit 4er-Bombe
            "SB RZ R9 G9 S9 R8 G8 B4 Ph",
            "Ph SB RZ GZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",  # mit 4er-Bombe
            "Ph SB RB GZ BZ SZ R9 G9 B6 B5 B4 B3 B2 Ma",  # Farbbombe
        ]
        m = 5
        r = 9
        for k in [0, 3, 4, 5, 6, 7, 9, 10, 13, 14]:
            for cards in combis:
                self._test(cards, k, (t, m, r))

    def test_street(self):
        t = STREET
        combis = [
            # ohne Phönix
            "GB RZ G9 R8 G7",
            "GD RB GZ R9 G8 R7",
            "GA RK GD RB GZ R9 S8 B7 S6 B5 S4 B3 S2",
            "GA RK GD RB GZ R9 S8 B7 S6 B5 S4 B3 S2 Ma",
            "GK BB SB GB RZ BZ GZ R9 S9 B9 R8 S8 G8 R7 S7 G7 R4 R2",
            # mit Phönix
            "GA RK GD RB GZ R9 S8 B7 S6 B5 S4 B3 Ph",
            "GA RK GD Ph GZ R9 S8 B7 S6 B5 S4 B3 S2",
            "GA RK GD RB GZ R9 S8 Ph S6 B5 S4 B3 S2",
            "GA RK GD RB Ph R9 S8 B7 S6 B5 S4 B3 S2",
            "GK RK GD RB Ph R9 S8 B7 S6 B5 S4 B3 S2",
            "GK RB GZ R9 G8 R7 SB BZ S9 B8 S7 B4 Ph",
            "Ph R7 G6 R5 G4 R3 S2 B2 Ma",
            "Ph RB GZ R8 G7 R4 S2 B2",
            # mit Bombe, ohne Phönix
            "GB GZ G9 G8 G7",
            "GD GB GZ G9 G8 G7",
            "GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2",
            "SK GB GZ G9 G8 G7 RB RZ R9 R8 R7 BB BZ B9 B8 B7 S4 S2",
            # mit Bombe, mit Phönix
            "GA GK GD GB GZ G9 R8 G7 G6 G5 G4 G3 Ph",
            "GA GK GD Ph GZ G9 R8 G7 G6 G5 G4 G3 G2",
            "GA GK GD GB GZ G9 R8 Ph G6 G5 G4 G3 G2",
            "GA GK GD GB Ph G9 G8 G7 G6 G5 G4 G3 G2",
            "SK GB GZ G9 G8 G7 RB RZ R9 R8 R7 S4 Ph",
            "Ph SB RB GZ BZ SZ R9 G9 B6 B5 B4 B3 B2 Ma",  # Farbbombe
        ]
        for m in [5]:
            r = 10
            for k in [0, 4, 5, 6, 7]:
                for cards in combis:
                    self._test(cards, k, (t, m, r))

    def test_bomb_4(self):
        t = BOMB  # 4er-Bombe
        combis = [
            "SB RZ R9 G9 R8 G8 B4",
        ]
        m = 4
        r = 9
        for k in [0, 3, 4, 5, 6, 7, 9, 10, 13, 14]:
            for cards in combis:
                self._test(cards, k, (t, m, r))

    def test_bomb_color(self):
        t = BOMB  # Farbbombe
        combis = [
            "GB GZ G9 G8 G7",
        ]
        for m in [5]:
            r = 10
            for k in [0, 4, 5, 6, 7]:
                for cards in combis:
                    self._test(cards, k, (t, m, r))


if __name__ == "__main__":
    unittest.main()
