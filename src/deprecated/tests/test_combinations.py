import unittest

from src.deprecated.combinations import possible_hands
# noinspection PyProtectedMember
from src.lib.cards import *


# noinspection DuplicatedCode
class TestCombinations(unittest.TestCase):
    def test_possible_hands(self):
        test = [
            # unplayed cards, k, figure, sum(matches), len(hands), p, msg
            ("Dr RB G6 B5 S4 R3 R2", 4, (1, 1, 11), 20, 35, 0.5714285714285714, "Einzelkarte"),
            ("Dr RK GK BD SB RB R2", 5, (1, 1, 11), 20, 21, 0.9523809523809523, "Einzelkarte mit 2 Buben"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 3, (1, 1, 10), 100, 120, 0.8333333333333334, "Einzelkarte aus einer 4er-Bombe"),
            ("Dr Hu Ph Ma S4 R3 R2", 1, (1, 1, 0), 1, 7, 0.14285714285714285, "Einzelkarte Hund"),
            ("Dr Hu Ph Ma S4 R3 R2", 1, (1, 1, 1), 1, 7, 0.14285714285714285, "Einzelkarte Mahjong"),
            ("Dr Hu Ph Ma S4 R3 R2", 1, (1, 1, 15), 1, 7, 0.14285714285714285, "Einzelkarte Drache"),
            ("Dr Hu Ph Ma S4 R3 R2", 1, (1, 1, 16), 1, 7, 0.14285714285714285, "Einzelkarte Phönix"),
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
            matches, hands = possible_hands(parse_cards(t[0]), t[1], t[2])
            #for match, hand in zip(matches, hands):
            #    print(stringify_cards(hand), match)
            self.assertEqual(t[3], sum(matches))
            self.assertEqual(t[4], len(hands))
            self.assertEqual(t[4], len(list(zip(matches, hands))))
            self.assertAlmostEqual(t[5], sum(matches) / len(hands) if len(hands) else 0.0, places=15, msg=t[6])


if __name__ == "__main__":
    unittest.main()
