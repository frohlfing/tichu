import unittest
# noinspection PyProtectedMember
from src.lib.combinations import *
from src.lib.cards import *


class TestGenerateTestData(unittest.TestCase):
    c = 0

    # cardlabels = (
    #     # rt   gr    bl    sw
    #     "Hu",  # Hund
    #     "Ma",  # MahJong
    #     "R2", "G2", "B2", "S2",  # 2
    #     "R3", "G3", "B3", "S3",  # 3
    #     "R4", "G4", "B4", "S4",  # 4
    #     "R5", "G5", "B5", "S5",  # 5
    #     "R6", "G6", "B6", "S6",  # 6
    #     "R7", "G7", "B7", "S7",  # 7
    #     "R8", "G8", "B8", "S8",  # 8
    #     "R9", "G9", "B9", "S9",  # 9
    #     "RZ", "GZ", "BZ", "SZ",  # 10
    #     "RB", "GB", "BB", "SB",  # Bube
    #     "RD", "GD", "BD", "SD",  # Dame
    #     "RK", "GK", "BK", "SK",  # König
    #     "RA", "GA", "BA", "SA",  # As
    #     "Dr",  # Drache
    #     "Ph",  # Phönix
    # )

    def _test_generate_test_data(self):
        def run(cards_, k_, figure):
            self.c += 1
            matches, hands = possible_hands(parse_cards(cards_), k_, figure)
            p = sum(matches)/len(hands) if hands else 0.0
            msg = stringify_figure(figure)
            print(f'("{cards_}", {k_}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p}, "{msg}, Test {self.c}"),'),

        t = STAIR
        combis = [
            "SB RZ R9 G9 R8 G8 B4",
            "SB RZ GZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 R8 G8 B4",
            "SB RZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ R9 G9 R8 G8 B4",
            "SB RZ Ph R9 G9 R8 G8 B4",
            "SB RZ GZ BZ Ph G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 Ph R8 G8 B4",
            "SB RZ R9 G9 S9 R8 G8 B4 Ph",
            "Ph SB RZ GZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",
        ]
        for m in [4, 6]:
            r = 10
            for k in [0, 3, 4, 5, 6, 7, 9, 10, 13, 14]:
                for cards in combis:
                    run(cards, k, (t, m, r))

        # t = FULLHOUSE
        # m = 5
        # for r in [0, 2, 10, 14, 15]:
        #     pass
        #
        # t = STREET
        # for m in [0, 4, 5, 6, 10, 13, 14, 15]:
        #     for r in [0, 4, 5, 10, 14, 15]:
        #         pass
        #
        # t = BOMB
        # for m in [0, 3, 4, 5, 10, 14, 15]:
        #     for r in [0, 2, 10, 14, 15]:
        #         pass
        #
        # t = TRIPLE
        # m = 3
        # for r in [0, 2, 10, 14, 15]:
        #     pass
        #
        # t = PAIR
        # m = 2
        # for r in [0, 2, 10, 14, 15]:
        #     pass
        #
        # t = SINGLE
        # m = 1
        # for r in [0, 1, 2, 10, 14, 15, 16]:
        #     "Ph SK RK GD BB RZ B9 R8"
        #     pass


# noinspection DuplicatedCode
class TestProbabilityOfHands(unittest.TestCase):

    def test_stair(self):
        test = [
            # unplayed cards, k, figure, sum(matches), len(hands), p, msg
            ("RK GK BD SD SB RB BB", 6, (4, 6, 13), 3, 7, 0.42857142857142855, "3er-Treppe ohne Phönix"),
            ("Ph GK BD SD SB RB BB", 6, (4, 6, 13), 3, 7, 0.42857142857142855, "3er-Treppe mit Phönix"),
            ("RK GK BD SD GD R9 B2", 6, (4, 4, 13), 5, 7, 0.7142857142857143, "2er-Treppe aus Fullhouse"),
            ("SB RZ R9 G9 R8 G8 B4", 0, (4, 4, 10), 0, 1, 0.0, "2erTreppeZ, Test 1"),
            ("SB RZ GZ R9 G9 R8 G8 B4", 0, (4, 4, 10), 0, 1, 0.0, "2erTreppeZ, Test 2"),
            ("SB RZ GZ BZ R9 G9 R8 G8 B4", 0, (4, 4, 10), 0, 1, 0.0, "2erTreppeZ, Test 3"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 0, (4, 4, 10), 0, 1, 0.0, "2erTreppeZ, Test 4"),
            ("SB RZ R9 G9 S9 R8 G8 B4", 0, (4, 4, 10), 0, 1, 0.0, "2erTreppeZ, Test 5"),
            ("SB RZ GZ R9 G9 S9 R8 G8 B4", 0, (4, 4, 10), 0, 1, 0.0, "2erTreppeZ, Test 6"),
            ("SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 0, (4, 4, 10), 0, 1, 0.0, "2erTreppeZ, Test 7"),
            ("SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 0, (4, 4, 10), 0, 1, 0.0, "2erTreppeZ, Test 8"),
            ("Ph SB RZ R9 G9 R8 G8 B4", 0, (4, 4, 10), 0, 1, 0.0, "2erTreppeZ, Test 9"),
            ("SB RZ Ph R9 G9 R8 G8 B4", 0, (4, 4, 10), 0, 1, 0.0, "2erTreppeZ, Test 10"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 0, (4, 4, 10), 0, 1, 0.0, "2erTreppeZ, Test 11"),
            ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 0, (4, 4, 10), 0, 1, 0.0, "2erTreppeZ, Test 12"),
            ("SB RZ R9 G9 S9 R8 G8 B4 Ph", 0, (4, 4, 10), 0, 1, 0.0, "2erTreppeZ, Test 13"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 0, (4, 4, 10), 0, 1, 0.0, "2erTreppeZ, Test 14"),
            ("Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 0, (4, 4, 10), 0, 1, 0.0, "2erTreppeZ, Test 15"),
            ("Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 0, (4, 4, 10), 0, 1, 0.0, "2erTreppeZ, Test 16"),
            ("SB RZ R9 G9 R8 G8 B4", 3, (4, 4, 10), 0, 35, 0.0, "2erTreppeZ, Test 17"),
            ("SB RZ GZ R9 G9 R8 G8 B4", 3, (4, 4, 10), 0, 56, 0.0, "2erTreppeZ, Test 18"),
            ("SB RZ GZ BZ R9 G9 R8 G8 B4", 3, (4, 4, 10), 0, 84, 0.0, "2erTreppeZ, Test 19"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 3, (4, 4, 10), 0, 120, 0.0, "2erTreppeZ, Test 20"),
            ("SB RZ R9 G9 S9 R8 G8 B4", 3, (4, 4, 10), 0, 56, 0.0, "2erTreppeZ, Test 21"),
            ("SB RZ GZ R9 G9 S9 R8 G8 B4", 3, (4, 4, 10), 0, 84, 0.0, "2erTreppeZ, Test 22"),
            ("SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 3, (4, 4, 10), 0, 120, 0.0, "2erTreppeZ, Test 23"),
            ("SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 3, (4, 4, 10), 0, 165, 0.0, "2erTreppeZ, Test 24"),
            ("Ph SB RZ R9 G9 R8 G8 B4", 3, (4, 4, 10), 0, 56, 0.0, "2erTreppeZ, Test 25"),
            ("SB RZ Ph R9 G9 R8 G8 B4", 3, (4, 4, 10), 0, 56, 0.0, "2erTreppeZ, Test 26"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 3, (4, 4, 10), 0, 84, 0.0, "2erTreppeZ, Test 27"),
            ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 3, (4, 4, 10), 0, 120, 0.0, "2erTreppeZ, Test 28"),
            ("SB RZ R9 G9 S9 R8 G8 B4 Ph", 3, (4, 4, 10), 0, 84, 0.0, "2erTreppeZ, Test 29"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 3, (4, 4, 10), 0, 120, 0.0, "2erTreppeZ, Test 30"),
            ("Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 3, (4, 4, 10), 0, 165, 0.0, "2erTreppeZ, Test 31"),
            ("Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 3, (4, 4, 10), 0, 220, 0.0, "2erTreppeZ, Test 32"),
            ("SB RZ R9 G9 R8 G8 B4", 4, (4, 4, 10), 0, 35, 0.0, "2erTreppeZ, Test 33"),
            ("SB RZ GZ R9 G9 R8 G8 B4", 4, (4, 4, 10), 1, 70, 0.014285714285714285, "2erTreppeZ, Test 34"),
            ("SB RZ GZ BZ R9 G9 R8 G8 B4", 4, (4, 4, 10), 3, 126, 0.023809523809523808, "2erTreppeZ, Test 35"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 4, (4, 4, 10), 6, 210, 0.02857142857142857, "2erTreppeZ, Test 36"),
            ("SB RZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 10), 0, 70, 0.0, "2erTreppeZ, Test 37"),
            ("SB RZ GZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 10), 3, 126, 0.023809523809523808, "2erTreppeZ, Test 38"),
            ("SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 10), 9, 210, 0.04285714285714286, "2erTreppeZ, Test 39"),
            ("SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 10), 18, 330, 0.05454545454545454, "2erTreppeZ, Test 40"),
            ("Ph SB RZ R9 G9 R8 G8 B4", 4, (4, 4, 10), 1, 70, 0.014285714285714285, "2erTreppeZ, Test 41"),
            ("SB RZ Ph R9 G9 R8 G8 B4", 4, (4, 4, 10), 1, 70, 0.014285714285714285, "2erTreppeZ, Test 42"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 4, (4, 4, 10), 3, 126, 0.023809523809523808, "2erTreppeZ, Test 43"),
            ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 4, (4, 4, 10), 6, 210, 0.02857142857142857, "2erTreppeZ, Test 44"),
            ("SB RZ R9 G9 S9 R8 G8 B4 Ph", 4, (4, 4, 10), 3, 126, 0.023809523809523808, "2erTreppeZ, Test 45"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 10), 12, 210, 0.05714285714285714, "2erTreppeZ, Test 46"),
            ("Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 10), 27, 330, 0.08181818181818182, "2erTreppeZ, Test 47"),
            ("Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 10), 48, 495, 0.09696969696969697, "2erTreppeZ, Test 48"),
            ("SB RZ R9 G9 R8 G8 B4", 5, (4, 4, 10), 0, 21, 0.0, "2erTreppeZ, Test 49"),
            ("SB RZ GZ R9 G9 R8 G8 B4", 5, (4, 4, 10), 4, 56, 0.07142857142857142, "2erTreppeZ, Test 50"),
            ("SB RZ GZ BZ R9 G9 R8 G8 B4", 5, (4, 4, 10), 13, 126, 0.10317460317460317, "2erTreppeZ, Test 51"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 5, (4, 4, 10), 28, 252, 0.1111111111111111, "2erTreppeZ, Test 52"),
            ("SB RZ R9 G9 S9 R8 G8 B4", 5, (4, 4, 10), 0, 56, 0.0, "2erTreppeZ, Test 53"),
            ("SB RZ GZ R9 G9 S9 R8 G8 B4", 5, (4, 4, 10), 13, 126, 0.10317460317460317, "2erTreppeZ, Test 54"),
            ("SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 5, (4, 4, 10), 42, 252, 0.16666666666666666, "2erTreppeZ, Test 55"),
            ("SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 5, (4, 4, 10), 90, 462, 0.19480519480519481, "2erTreppeZ, Test 56"),
            ("Ph SB RZ R9 G9 R8 G8 B4", 5, (4, 4, 10), 4, 56, 0.07142857142857142, "2erTreppeZ, Test 57"),
            ("SB RZ Ph R9 G9 R8 G8 B4", 5, (4, 4, 10), 4, 56, 0.07142857142857142, "2erTreppeZ, Test 58"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 5, (4, 4, 10), 13, 126, 0.10317460317460317, "2erTreppeZ, Test 59"),
            ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 5, (4, 4, 10), 28, 252, 0.1111111111111111, "2erTreppeZ, Test 60"),
            ("SB RZ R9 G9 S9 R8 G8 B4 Ph", 5, (4, 4, 10), 13, 126, 0.10317460317460317, "2erTreppeZ, Test 61"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 5, (4, 4, 10), 54, 252, 0.21428571428571427, "2erTreppeZ, Test 62"),
            ("Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 5, (4, 4, 10), 129, 462, 0.2792207792207792, "2erTreppeZ, Test 63"),
            ("Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 5, (4, 4, 10), 244, 792, 0.30808080808080807, "2erTreppeZ, Test 64"),
            ("SB RZ R9 G9 R8 G8 B4", 6, (4, 4, 10), 0, 7, 0.0, "2erTreppeZ, Test 65"),
            ("SB RZ GZ R9 G9 R8 G8 B4", 6, (4, 4, 10), 6, 28, 0.21428571428571427, "2erTreppeZ, Test 66"),
            ("SB RZ GZ BZ R9 G9 R8 G8 B4", 6, (4, 4, 10), 22, 84, 0.2619047619047619, "2erTreppeZ, Test 67"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 6, (4, 4, 10), 53, 210, 0.2523809523809524, "2erTreppeZ, Test 68"),
            ("SB RZ R9 G9 S9 R8 G8 B4", 6, (4, 4, 10), 0, 28, 0.0, "2erTreppeZ, Test 69"),
            ("SB RZ GZ R9 G9 S9 R8 G8 B4", 6, (4, 4, 10), 22, 84, 0.2619047619047619, "2erTreppeZ, Test 70"),
            ("SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 6, (4, 4, 10), 79, 210, 0.3761904761904762, "2erTreppeZ, Test 71"),
            ("SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 6, (4, 4, 10), 187, 462, 0.40476190476190477, "2erTreppeZ, Test 72"),
            ("Ph SB RZ R9 G9 R8 G8 B4", 6, (4, 4, 10), 6, 28, 0.21428571428571427, "2erTreppeZ, Test 73"),
            ("SB RZ Ph R9 G9 R8 G8 B4", 6, (4, 4, 10), 6, 28, 0.21428571428571427, "2erTreppeZ, Test 74"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 6, (4, 4, 10), 22, 84, 0.2619047619047619, "2erTreppeZ, Test 75"),
            ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 6, (4, 4, 10), 53, 210, 0.2523809523809524, "2erTreppeZ, Test 76"),
            ("SB RZ R9 G9 S9 R8 G8 B4 Ph", 6, (4, 4, 10), 22, 84, 0.2619047619047619, "2erTreppeZ, Test 77"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 6, (4, 4, 10), 97, 210, 0.46190476190476193, "2erTreppeZ, Test 78"),
            ("Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 6, (4, 4, 10), 253, 462, 0.5476190476190477, "2erTreppeZ, Test 79"),
            ("Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 6, (4, 4, 10), 524, 924, 0.5670995670995671, "2erTreppeZ, Test 80"),
            ("SB RZ R9 G9 R8 G8 B4", 7, (4, 4, 10), 0, 1, 0.0, "2erTreppeZ, Test 81"),
            ("SB RZ GZ R9 G9 R8 G8 B4", 7, (4, 4, 10), 4, 8, 0.5, "2erTreppeZ, Test 82"),
            ("SB RZ GZ BZ R9 G9 R8 G8 B4", 7, (4, 4, 10), 18, 36, 0.5, "2erTreppeZ, Test 83"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 7, (4, 4, 10), 52, 120, 0.43333333333333335, "2erTreppeZ, Test 84"),
            ("SB RZ R9 G9 S9 R8 G8 B4", 7, (4, 4, 10), 0, 8, 0.0, "2erTreppeZ, Test 85"),
            ("SB RZ GZ R9 G9 S9 R8 G8 B4", 7, (4, 4, 10), 18, 36, 0.5, "2erTreppeZ, Test 86"),
            ("SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 7, (4, 4, 10), 76, 120, 0.6333333333333333, "2erTreppeZ, Test 87"),
            ("SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 7, (4, 4, 10), 209, 330, 0.6333333333333333, "2erTreppeZ, Test 88"),
            ("Ph SB RZ R9 G9 R8 G8 B4", 7, (4, 4, 10), 4, 8, 0.5, "2erTreppeZ, Test 89"),
            ("SB RZ Ph R9 G9 R8 G8 B4", 7, (4, 4, 10), 4, 8, 0.5, "2erTreppeZ, Test 90"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 7, (4, 4, 10), 18, 36, 0.5, "2erTreppeZ, Test 91"),
            ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 7, (4, 4, 10), 52, 120, 0.43333333333333335, "2erTreppeZ, Test 92"),
            ("SB RZ R9 G9 S9 R8 G8 B4 Ph", 7, (4, 4, 10), 18, 36, 0.5, "2erTreppeZ, Test 93"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 7, (4, 4, 10), 88, 120, 0.7333333333333333, "2erTreppeZ, Test 94"),
            ("Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 7, (4, 4, 10), 263, 330, 0.796969696969697, "2erTreppeZ, Test 95"),
            ("Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 7, (4, 4, 10), 624, 792, 0.7878787878787878, "2erTreppeZ, Test 96"),
            ("SB RZ R9 G9 R8 G8 B4", 9, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 97"),
            ("SB RZ GZ R9 G9 R8 G8 B4", 9, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 98"),
            ("SB RZ GZ BZ R9 G9 R8 G8 B4", 9, (4, 4, 10), 1, 1, 1.0, "2erTreppeZ, Test 99"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 9, (4, 4, 10), 8, 10, 0.8, "2erTreppeZ, Test 100"),
            ("SB RZ R9 G9 S9 R8 G8 B4", 9, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 101"),
            ("SB RZ GZ R9 G9 S9 R8 G8 B4", 9, (4, 4, 10), 1, 1, 1.0, "2erTreppeZ, Test 102"),
            ("SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 9, (4, 4, 10), 10, 10, 1.0, "2erTreppeZ, Test 103"),
            ("SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 9, (4, 4, 10), 52, 55, 0.9454545454545454, "2erTreppeZ, Test 104"),
            ("Ph SB RZ R9 G9 R8 G8 B4", 9, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 105"),
            ("SB RZ Ph R9 G9 R8 G8 B4", 9, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 106"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 9, (4, 4, 10), 1, 1, 1.0, "2erTreppeZ, Test 107"),
            ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 9, (4, 4, 10), 8, 10, 0.8, "2erTreppeZ, Test 108"),
            ("SB RZ R9 G9 S9 R8 G8 B4 Ph", 9, (4, 4, 10), 1, 1, 1.0, "2erTreppeZ, Test 109"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 9, (4, 4, 10), 10, 10, 1.0, "2erTreppeZ, Test 110"),
            ("Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 9, (4, 4, 10), 55, 55, 1.0, "2erTreppeZ, Test 111"),
            ("Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 9, (4, 4, 10), 216, 220, 0.9818181818181818, "2erTreppeZ, Test 112"),
            ("SB RZ R9 G9 R8 G8 B4", 10, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 113"),
            ("SB RZ GZ R9 G9 R8 G8 B4", 10, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 114"),
            ("SB RZ GZ BZ R9 G9 R8 G8 B4", 10, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 115"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 10, (4, 4, 10), 1, 1, 1.0, "2erTreppeZ, Test 116"),
            ("SB RZ R9 G9 S9 R8 G8 B4", 10, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 117"),
            ("SB RZ GZ R9 G9 S9 R8 G8 B4", 10, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 118"),
            ("SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 10, (4, 4, 10), 1, 1, 1.0, "2erTreppeZ, Test 119"),
            ("SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 10, (4, 4, 10), 11, 11, 1.0, "2erTreppeZ, Test 120"),
            ("Ph SB RZ R9 G9 R8 G8 B4", 10, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 121"),
            ("SB RZ Ph R9 G9 R8 G8 B4", 10, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 122"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 10, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 123"),
            ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 10, (4, 4, 10), 1, 1, 1.0, "2erTreppeZ, Test 124"),
            ("SB RZ R9 G9 S9 R8 G8 B4 Ph", 10, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 125"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 10, (4, 4, 10), 1, 1, 1.0, "2erTreppeZ, Test 126"),
            ("Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 10, (4, 4, 10), 11, 11, 1.0, "2erTreppeZ, Test 127"),
            ("Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 10, (4, 4, 10), 66, 66, 1.0, "2erTreppeZ, Test 128"),
            ("SB RZ R9 G9 R8 G8 B4", 13, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 129"),
            ("SB RZ GZ R9 G9 R8 G8 B4", 13, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 130"),
            ("SB RZ GZ BZ R9 G9 R8 G8 B4", 13, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 131"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 13, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 132"),
            ("SB RZ R9 G9 S9 R8 G8 B4", 13, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 133"),
            ("SB RZ GZ R9 G9 S9 R8 G8 B4", 13, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 134"),
            ("SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 13, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 135"),
            ("SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 13, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 136"),
            ("Ph SB RZ R9 G9 R8 G8 B4", 13, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 137"),
            ("SB RZ Ph R9 G9 R8 G8 B4", 13, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 138"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 13, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 139"),
            ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 13, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 140"),
            ("SB RZ R9 G9 S9 R8 G8 B4 Ph", 13, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 141"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 13, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 142"),
            ("Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 13, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 143"),
            ("Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 13, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 144"),
            ("SB RZ R9 G9 R8 G8 B4", 14, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 145"),
            ("SB RZ GZ R9 G9 R8 G8 B4", 14, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 146"),
            ("SB RZ GZ BZ R9 G9 R8 G8 B4", 14, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 147"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 14, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 148"),
            ("SB RZ R9 G9 S9 R8 G8 B4", 14, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 149"),
            ("SB RZ GZ R9 G9 S9 R8 G8 B4", 14, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 150"),
            ("SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 14, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 151"),
            ("SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 14, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 152"),
            ("Ph SB RZ R9 G9 R8 G8 B4", 14, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 153"),
            ("SB RZ Ph R9 G9 R8 G8 B4", 14, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 154"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 14, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 155"),
            ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 14, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 156"),
            ("SB RZ R9 G9 S9 R8 G8 B4 Ph", 14, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 157"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 14, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 158"),
            ("Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 14, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 159"),
            ("Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 14, (4, 4, 10), 0, 0, 0.0, "2erTreppeZ, Test 160"),
            ("SB RZ R9 G9 R8 G8 B4", 0, (4, 6, 10), 0, 1, 0.0, "3erTreppeZ, Test 161"),
            ("SB RZ GZ R9 G9 R8 G8 B4", 0, (4, 6, 10), 0, 1, 0.0, "3erTreppeZ, Test 162"),
            ("SB RZ GZ BZ R9 G9 R8 G8 B4", 0, (4, 6, 10), 0, 1, 0.0, "3erTreppeZ, Test 163"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 0, (4, 6, 10), 0, 1, 0.0, "3erTreppeZ, Test 164"),
            ("SB RZ R9 G9 S9 R8 G8 B4", 0, (4, 6, 10), 0, 1, 0.0, "3erTreppeZ, Test 165"),
            ("SB RZ GZ R9 G9 S9 R8 G8 B4", 0, (4, 6, 10), 0, 1, 0.0, "3erTreppeZ, Test 166"),
            ("SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 0, (4, 6, 10), 0, 1, 0.0, "3erTreppeZ, Test 167"),
            ("SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 0, (4, 6, 10), 0, 1, 0.0, "3erTreppeZ, Test 168"),
            ("Ph SB RZ R9 G9 R8 G8 B4", 0, (4, 6, 10), 0, 1, 0.0, "3erTreppeZ, Test 169"),
            ("SB RZ Ph R9 G9 R8 G8 B4", 0, (4, 6, 10), 0, 1, 0.0, "3erTreppeZ, Test 170"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 0, (4, 6, 10), 0, 1, 0.0, "3erTreppeZ, Test 171"),
            ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 0, (4, 6, 10), 0, 1, 0.0, "3erTreppeZ, Test 172"),
            ("SB RZ R9 G9 S9 R8 G8 B4 Ph", 0, (4, 6, 10), 0, 1, 0.0, "3erTreppeZ, Test 173"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 0, (4, 6, 10), 0, 1, 0.0, "3erTreppeZ, Test 174"),
            ("Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 0, (4, 6, 10), 0, 1, 0.0, "3erTreppeZ, Test 175"),
            ("Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 0, (4, 6, 10), 0, 1, 0.0, "3erTreppeZ, Test 176"),
            ("SB RZ R9 G9 R8 G8 B4", 3, (4, 6, 10), 0, 35, 0.0, "3erTreppeZ, Test 177"),
            ("SB RZ GZ R9 G9 R8 G8 B4", 3, (4, 6, 10), 0, 56, 0.0, "3erTreppeZ, Test 178"),
            ("SB RZ GZ BZ R9 G9 R8 G8 B4", 3, (4, 6, 10), 0, 84, 0.0, "3erTreppeZ, Test 179"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 3, (4, 6, 10), 0, 120, 0.0, "3erTreppeZ, Test 180"),
            ("SB RZ R9 G9 S9 R8 G8 B4", 3, (4, 6, 10), 0, 56, 0.0, "3erTreppeZ, Test 181"),
            ("SB RZ GZ R9 G9 S9 R8 G8 B4", 3, (4, 6, 10), 0, 84, 0.0, "3erTreppeZ, Test 182"),
            ("SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 3, (4, 6, 10), 0, 120, 0.0, "3erTreppeZ, Test 183"),
            ("SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 3, (4, 6, 10), 0, 165, 0.0, "3erTreppeZ, Test 184"),
            ("Ph SB RZ R9 G9 R8 G8 B4", 3, (4, 6, 10), 0, 56, 0.0, "3erTreppeZ, Test 185"),
            ("SB RZ Ph R9 G9 R8 G8 B4", 3, (4, 6, 10), 0, 56, 0.0, "3erTreppeZ, Test 186"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 3, (4, 6, 10), 0, 84, 0.0, "3erTreppeZ, Test 187"),
            ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 3, (4, 6, 10), 0, 120, 0.0, "3erTreppeZ, Test 188"),
            ("SB RZ R9 G9 S9 R8 G8 B4 Ph", 3, (4, 6, 10), 0, 84, 0.0, "3erTreppeZ, Test 189"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 3, (4, 6, 10), 0, 120, 0.0, "3erTreppeZ, Test 190"),
            ("Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 3, (4, 6, 10), 0, 165, 0.0, "3erTreppeZ, Test 191"),
            ("Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 3, (4, 6, 10), 0, 220, 0.0, "3erTreppeZ, Test 192"),
            ("SB RZ R9 G9 R8 G8 B4", 4, (4, 6, 10), 0, 35, 0.0, "3erTreppeZ, Test 193"),
            ("SB RZ GZ R9 G9 R8 G8 B4", 4, (4, 6, 10), 0, 70, 0.0, "3erTreppeZ, Test 194"),
            ("SB RZ GZ BZ R9 G9 R8 G8 B4", 4, (4, 6, 10), 0, 126, 0.0, "3erTreppeZ, Test 195"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 4, (4, 6, 10), 0, 210, 0.0, "3erTreppeZ, Test 196"),
            ("SB RZ R9 G9 S9 R8 G8 B4", 4, (4, 6, 10), 0, 70, 0.0, "3erTreppeZ, Test 197"),
            ("SB RZ GZ R9 G9 S9 R8 G8 B4", 4, (4, 6, 10), 0, 126, 0.0, "3erTreppeZ, Test 198"),
            ("SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 4, (4, 6, 10), 0, 210, 0.0, "3erTreppeZ, Test 199"),
            ("SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 4, (4, 6, 10), 0, 330, 0.0, "3erTreppeZ, Test 200"),
            ("Ph SB RZ R9 G9 R8 G8 B4", 4, (4, 6, 10), 0, 70, 0.0, "3erTreppeZ, Test 201"),
            ("SB RZ Ph R9 G9 R8 G8 B4", 4, (4, 6, 10), 0, 70, 0.0, "3erTreppeZ, Test 202"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 4, (4, 6, 10), 0, 126, 0.0, "3erTreppeZ, Test 203"),
            ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 4, (4, 6, 10), 0, 210, 0.0, "3erTreppeZ, Test 204"),
            ("SB RZ R9 G9 S9 R8 G8 B4 Ph", 4, (4, 6, 10), 0, 126, 0.0, "3erTreppeZ, Test 205"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 4, (4, 6, 10), 0, 210, 0.0, "3erTreppeZ, Test 206"),
            ("Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 4, (4, 6, 10), 0, 330, 0.0, "3erTreppeZ, Test 207"),
            ("Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 4, (4, 6, 10), 0, 495, 0.0, "3erTreppeZ, Test 208"),
            ("SB RZ R9 G9 R8 G8 B4", 5, (4, 6, 10), 0, 21, 0.0, "3erTreppeZ, Test 209"),
            ("SB RZ GZ R9 G9 R8 G8 B4", 5, (4, 6, 10), 0, 56, 0.0, "3erTreppeZ, Test 210"),
            ("SB RZ GZ BZ R9 G9 R8 G8 B4", 5, (4, 6, 10), 0, 126, 0.0, "3erTreppeZ, Test 211"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 5, (4, 6, 10), 0, 252, 0.0, "3erTreppeZ, Test 212"),
            ("SB RZ R9 G9 S9 R8 G8 B4", 5, (4, 6, 10), 0, 56, 0.0, "3erTreppeZ, Test 213"),
            ("SB RZ GZ R9 G9 S9 R8 G8 B4", 5, (4, 6, 10), 0, 126, 0.0, "3erTreppeZ, Test 214"),
            ("SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 5, (4, 6, 10), 0, 252, 0.0, "3erTreppeZ, Test 215"),
            ("SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 5, (4, 6, 10), 0, 462, 0.0, "3erTreppeZ, Test 216"),
            ("Ph SB RZ R9 G9 R8 G8 B4", 5, (4, 6, 10), 0, 56, 0.0, "3erTreppeZ, Test 217"),
            ("SB RZ Ph R9 G9 R8 G8 B4", 5, (4, 6, 10), 0, 56, 0.0, "3erTreppeZ, Test 218"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 5, (4, 6, 10), 0, 126, 0.0, "3erTreppeZ, Test 219"),
            ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 5, (4, 6, 10), 0, 252, 0.0, "3erTreppeZ, Test 220"),
            ("SB RZ R9 G9 S9 R8 G8 B4 Ph", 5, (4, 6, 10), 0, 126, 0.0, "3erTreppeZ, Test 221"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 5, (4, 6, 10), 0, 252, 0.0, "3erTreppeZ, Test 222"),
            ("Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 5, (4, 6, 10), 0, 462, 0.0, "3erTreppeZ, Test 223"),
            ("Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 5, (4, 6, 10), 0, 792, 0.0, "3erTreppeZ, Test 224"),
            ("SB RZ R9 G9 R8 G8 B4", 6, (4, 6, 10), 0, 7, 0.0, "3erTreppeZ, Test 225"),
            ("SB RZ GZ R9 G9 R8 G8 B4", 6, (4, 6, 10), 1, 28, 0.03571428571428571, "3erTreppeZ, Test 226"),
            ("SB RZ GZ BZ R9 G9 R8 G8 B4", 6, (4, 6, 10), 3, 84, 0.03571428571428571, "3erTreppeZ, Test 227"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 6, (4, 6, 10), 6, 210, 0.02857142857142857, "3erTreppeZ, Test 228"),
            ("SB RZ R9 G9 S9 R8 G8 B4", 6, (4, 6, 10), 0, 28, 0.0, "3erTreppeZ, Test 229"),
            ("SB RZ GZ R9 G9 S9 R8 G8 B4", 6, (4, 6, 10), 3, 84, 0.03571428571428571, "3erTreppeZ, Test 230"),
            ("SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 6, (4, 6, 10), 9, 210, 0.04285714285714286, "3erTreppeZ, Test 231"),
            ("SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 6, (4, 6, 10), 18, 462, 0.03896103896103896, "3erTreppeZ, Test 232"),
            ("Ph SB RZ R9 G9 R8 G8 B4", 6, (4, 6, 10), 1, 28, 0.03571428571428571, "3erTreppeZ, Test 233"),
            ("SB RZ Ph R9 G9 R8 G8 B4", 6, (4, 6, 10), 1, 28, 0.03571428571428571, "3erTreppeZ, Test 234"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 6, (4, 6, 10), 3, 84, 0.03571428571428571, "3erTreppeZ, Test 235"),
            ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 6, (4, 6, 10), 6, 210, 0.02857142857142857, "3erTreppeZ, Test 236"),
            ("SB RZ R9 G9 S9 R8 G8 B4 Ph", 6, (4, 6, 10), 3, 84, 0.03571428571428571, "3erTreppeZ, Test 237"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 6, (4, 6, 10), 18, 210, 0.08571428571428572, "3erTreppeZ, Test 238"),
            ("Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 6, (4, 6, 10), 45, 462, 0.09740259740259741, "3erTreppeZ, Test 239"),
            ("Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 6, (4, 6, 10), 84, 924, 0.09090909090909091, "3erTreppeZ, Test 240"),
            ("SB RZ R9 G9 R8 G8 B4", 7, (4, 6, 10), 0, 1, 0.0, "3erTreppeZ, Test 241"),
            ("SB RZ GZ R9 G9 R8 G8 B4", 7, (4, 6, 10), 2, 8, 0.25, "3erTreppeZ, Test 242"),
            ("SB RZ GZ BZ R9 G9 R8 G8 B4", 7, (4, 6, 10), 7, 36, 0.19444444444444445, "3erTreppeZ, Test 243"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 7, (4, 6, 10), 16, 120, 0.13333333333333333, "3erTreppeZ, Test 244"),
            ("SB RZ R9 G9 S9 R8 G8 B4", 7, (4, 6, 10), 0, 8, 0.0, "3erTreppeZ, Test 245"),
            ("SB RZ GZ R9 G9 S9 R8 G8 B4", 7, (4, 6, 10), 7, 36, 0.19444444444444445, "3erTreppeZ, Test 246"),
            ("SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 7, (4, 6, 10), 24, 120, 0.2, "3erTreppeZ, Test 247"),
            ("SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 7, (4, 6, 10), 54, 330, 0.16363636363636364, "3erTreppeZ, Test 248"),
            ("Ph SB RZ R9 G9 R8 G8 B4", 7, (4, 6, 10), 2, 8, 0.25, "3erTreppeZ, Test 249"),
            ("SB RZ Ph R9 G9 R8 G8 B4", 7, (4, 6, 10), 2, 8, 0.25, "3erTreppeZ, Test 250"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 7, (4, 6, 10), 7, 36, 0.19444444444444445, "3erTreppeZ, Test 251"),
            ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 7, (4, 6, 10), 16, 120, 0.13333333333333333, "3erTreppeZ, Test 252"),
            ("SB RZ R9 G9 S9 R8 G8 B4 Ph", 7, (4, 6, 10), 7, 36, 0.19444444444444445, "3erTreppeZ, Test 253"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 7, (4, 6, 10), 44, 120, 0.36666666666666664, "3erTreppeZ, Test 254"),
            ("Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 7, (4, 6, 10), 123, 330, 0.37272727272727274, "3erTreppeZ, Test 255"),
            ("Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 7, (4, 6, 10), 256, 792, 0.32323232323232326, "3erTreppeZ, Test 256"),
            ("SB RZ R9 G9 R8 G8 B4", 9, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 257"),
            ("SB RZ GZ R9 G9 R8 G8 B4", 9, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 258"),
            ("SB RZ GZ BZ R9 G9 R8 G8 B4", 9, (4, 6, 10), 1, 1, 1.0, "3erTreppeZ, Test 259"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 9, (4, 6, 10), 6, 10, 0.6, "3erTreppeZ, Test 260"),
            ("SB RZ R9 G9 S9 R8 G8 B4", 9, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 261"),
            ("SB RZ GZ R9 G9 S9 R8 G8 B4", 9, (4, 6, 10), 1, 1, 1.0, "3erTreppeZ, Test 262"),
            ("SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 9, (4, 6, 10), 8, 10, 0.8, "3erTreppeZ, Test 263"),
            ("SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 9, (4, 6, 10), 33, 55, 0.6, "3erTreppeZ, Test 264"),
            ("Ph SB RZ R9 G9 R8 G8 B4", 9, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 265"),
            ("SB RZ Ph R9 G9 R8 G8 B4", 9, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 266"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 9, (4, 6, 10), 1, 1, 1.0, "3erTreppeZ, Test 267"),
            ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 9, (4, 6, 10), 6, 10, 0.6, "3erTreppeZ, Test 268"),
            ("SB RZ R9 G9 S9 R8 G8 B4 Ph", 9, (4, 6, 10), 1, 1, 1.0, "3erTreppeZ, Test 269"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 9, (4, 6, 10), 10, 10, 1.0, "3erTreppeZ, Test 270"),
            ("Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 9, (4, 6, 10), 52, 55, 0.9454545454545454, "3erTreppeZ, Test 271"),
            ("Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 9, (4, 6, 10), 182, 220, 0.8272727272727273, "3erTreppeZ, Test 272"),
            ("SB RZ R9 G9 R8 G8 B4", 10, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 273"),
            ("SB RZ GZ R9 G9 R8 G8 B4", 10, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 274"),
            ("SB RZ GZ BZ R9 G9 R8 G8 B4", 10, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 275"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 10, (4, 6, 10), 1, 1, 1.0, "3erTreppeZ, Test 276"),
            ("SB RZ R9 G9 S9 R8 G8 B4", 10, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 277"),
            ("SB RZ GZ R9 G9 S9 R8 G8 B4", 10, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 278"),
            ("SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 10, (4, 6, 10), 1, 1, 1.0, "3erTreppeZ, Test 279"),
            ("SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 10, (4, 6, 10), 9, 11, 0.8181818181818182, "3erTreppeZ, Test 280"),
            ("Ph SB RZ R9 G9 R8 G8 B4", 10, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 281"),
            ("SB RZ Ph R9 G9 R8 G8 B4", 10, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 282"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 10, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 283"),
            ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 10, (4, 6, 10), 1, 1, 1.0, "3erTreppeZ, Test 284"),
            ("SB RZ R9 G9 S9 R8 G8 B4 Ph", 10, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 285"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 10, (4, 6, 10), 1, 1, 1.0, "3erTreppeZ, Test 286"),
            ("Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 10, (4, 6, 10), 11, 11, 1.0, "3erTreppeZ, Test 287"),
            ("Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 10, (4, 6, 10), 63, 66, 0.9545454545454546, "3erTreppeZ, Test 288"),
            ("SB RZ R9 G9 R8 G8 B4", 13, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 289"),
            ("SB RZ GZ R9 G9 R8 G8 B4", 13, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 290"),
            ("SB RZ GZ BZ R9 G9 R8 G8 B4", 13, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 291"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 13, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 292"),
            ("SB RZ R9 G9 S9 R8 G8 B4", 13, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 293"),
            ("SB RZ GZ R9 G9 S9 R8 G8 B4", 13, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 294"),
            ("SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 13, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 295"),
            ("SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 13, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 296"),
            ("Ph SB RZ R9 G9 R8 G8 B4", 13, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 297"),
            ("SB RZ Ph R9 G9 R8 G8 B4", 13, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 298"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 13, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 299"),
            ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 13, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 300"),
            ("SB RZ R9 G9 S9 R8 G8 B4 Ph", 13, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 301"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 13, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 302"),
            ("Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 13, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 303"),
            ("Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 13, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 304"),
            ("SB RZ R9 G9 R8 G8 B4", 14, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 305"),
            ("SB RZ GZ R9 G9 R8 G8 B4", 14, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 306"),
            ("SB RZ GZ BZ R9 G9 R8 G8 B4", 14, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 307"),
            ("SB RZ GZ BZ SZ R9 G9 R8 G8 B4", 14, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 308"),
            ("SB RZ R9 G9 S9 R8 G8 B4", 14, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 309"),
            ("SB RZ GZ R9 G9 S9 R8 G8 B4", 14, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 310"),
            ("SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 14, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 311"),
            ("SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 14, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 312"),
            ("Ph SB RZ R9 G9 R8 G8 B4", 14, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 313"),
            ("SB RZ Ph R9 G9 R8 G8 B4", 14, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 314"),
            ("SB RZ GZ BZ Ph G9 R8 G8 B4", 14, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 315"),
            ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 14, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 316"),
            ("SB RZ R9 G9 S9 R8 G8 B4 Ph", 14, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 317"),
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 14, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 318"),
            ("Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4", 14, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 319"),
            ("Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4", 14, (4, 6, 10), 0, 0, 0.0, "3erTreppeZ, Test 320"),
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
            self.assertAlmostEqual(t[5], sum(matches) / len(hands), places=15, msg=t[6])
            # probability_of_hands
            p = probability_of_hand(parse_cards(t[0]), t[1], t[2])
            self.assertAlmostEqual(t[5], p, places=15, msg=t[6])


    def test_fullhouse(self):
        test = [
            # unplayed cards, k, figure, sum(matches), len(hands), p, msg
            ("RK GK BD SB RB BB S2", 6, (5, 5, 11), 2, 7, 0.2857142857142857, "Fullhouse ohne Phönix"),
            ("Ph GK BD SB RB BB S2", 6, (5, 5, 11), 3, 7, 0.42857142857142855, "Fullhouse mit Phönix für Paar"),
            ("RK GK BD SB RB BZ Ph", 6, (5, 5, 11), 2, 7, 0.2857142857142857, "Fullhouse mit Phönix für Drilling"),
            ("BK RK SK BZ RZ R9 S9 RB", 7, (5, 5, 13), 5, 8, 0.625, "Fullhouse und zusätzliches Pärchen"),
            ("BK RK SK GK R9 S9 RB S2", 7, (5, 5, 13), 6, 8, 0.75, "Fullhouse aus Bombe"),
            ("BK RK SK G9 R9 S9 RB S2", 7, (5, 5, 13), 5, 8, 0.625, "Fullhouse aus 2 Drillinge"),
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
            self.assertAlmostEqual(t[5], sum(matches) / len(hands), places=15, msg=t[6])
            # probability_of_hands
            p = probability_of_hand(parse_cards(t[0]), t[1], t[2])
            self.assertAlmostEqual(t[5], p, places=15, msg=t[6])

    def test_street(self):
        test = [
            # unplayed cards, k, figure, sum(matches), len(hands), p, msg
            ("RA GK BD SB RZ B9 R3", 6, (6, 5, 13), 2, 7, 0.2857142857142857, "Straße ohne Phönix"),
            ("RA GK BD RZ B9 R3 Ph", 6, (6, 5, 13), 2, 7, 0.2857142857142857, "Straße mit Phönix (Lücke gefüllt)"),
            ("SK RK GD BB RZ B9 R8 R2", 6, (6, 5, 13), 5, 28, 0.17857142857142858, "Straße ohne Phönix (aus 8 Karten)"),
            ("Ph RK GD BB RZ B9 R8 R2", 6, (6, 5, 13), 13, 28, 0.4642857142857143, "Straße mit Phönix 2 (aus 8 Karten)"),
            ("SK RK GD BB RZ B9 R8 Ph", 6, (6, 5, 13), 18, 28, 0.6428571428571429, "Straße mit Phönix (verlängert)"),
            ("SA RK GD BB RZ B9 R8 Ph", 6, (6, 5, 13), 13, 28, 0.4642857142857143, "Straße mit Phönix (verlängert, 2)"),
            ("BK SD BD RB BZ B9 R3", 6, (6, 5, 13), 3, 7, 0.42857142857142855, "Straße, keine Bombe"),
            ("BK SD BD BB BZ B9 R3", 6, (6, 5, 13), 3, 7, 0.42857142857142855, "Straße, mit Bombe"),
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
            self.assertAlmostEqual(t[5], sum(matches) / len(hands), places=15, msg=t[6])
            # probability_of_hands
            p = probability_of_hand(parse_cards(t[0]), t[1], t[2])
            self.assertAlmostEqual(t[5], p, places=15, msg=t[6])

    def test_bomb(self):
        test = [
            # unplayed cards, k, figure, sum(matches), len(hands), p, msg
            ("RK GB BB SB RB BZ R2", 5, (7, 4, 11), 3, 21, 0.14285714285714285, "4er-Bombe"),
            ("BK BB BZ B9 B8 B7 B2", 5, (7, 5, 11), 1, 21, 0.047619047619047616, "Straßenbombe"),
            ("BK BD BB BZ B9 RK RD RB RZ R9 S2 S3", 11, (7, 5, 13), 12, 12, 1.0, "2 Straßenbomben in 12 Karten"),
            ("BK BD BB BZ B9 RK RD RB RZ R9 S2 S3 G7", 11, (7, 5, 13), 53, 78, 0.6794871794871795, "2 Straßenbomben in 13 Karten"),
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
            self.assertAlmostEqual(t[5], sum(matches) / len(hands), places=15, msg=t[6])
            # probability_of_hands
            p = probability_of_hand(parse_cards(t[0]), t[1], t[2])
            self.assertAlmostEqual(t[5], p, places=15, msg=t[6])


    def test_tripple(self):
        test = [
            # unplayed cards, k, figure, sum(matches), len(hands), p, msg
            ("SK RK GB BB SB R3 R2", 4, (3, 3, 11), 4, 35, 0.11428571428571428, "Drilling ohne Phönix"),
            ("Ph RK GB BB SB R3 R2", 4, (3, 3, 11), 13, 35, 0.37142857142857144, "Drilling mit Phönix"),
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
            self.assertAlmostEqual(t[5], sum(matches) / len(hands), places=15, msg=t[6])
            # probability_of_hands
            p = probability_of_hand(parse_cards(t[0]), t[1], t[2])
            self.assertAlmostEqual(t[5], p, places=15, msg=t[6])

    def test_pair(self):
        test = [
            # unplayed cards, k, figure, sum(matches), len(hands), p, msg
            ("Dr RK GK BB SB RB R2", 5, (2, 2, 11), 18, 21, 0.8571428571428571, "Pärchen ohne Phönix"),
            ("Ph RK GK BD SB RB R2", 5, (2, 2, 11), 18, 21, 0.8571428571428571, "Pärchen mit Phönix"),
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
            self.assertAlmostEqual(t[5], sum(matches) / len(hands), places=15, msg=t[6])
            # probability_of_hands
            p = probability_of_hand(parse_cards(t[0]), t[1], t[2])
            self.assertAlmostEqual(t[5], p, places=15, msg=t[6])

    def test_single(self):
        test = [
            # unplayed cards, k, figure, sum(matches), len(hands), p, msg
            ("Dr RK GK BD SB R3 R2", 4, (1, 1, 11), 20, 35, 0.5714285714285714, "Einzelkarte"),
            ("Dr RK GK BD SB RB R2", 5, (1, 1, 11), 20, 21, 0.9523809523809523, "Einzelkarte mit 2 Buben"),
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
            self.assertAlmostEqual(t[5], sum(matches) / len(hands), places=15, msg=t[6])
            # probability_of_hands
            p = probability_of_hand(parse_cards(t[0]), t[1], t[2])
            self.assertAlmostEqual(t[5], p, places=15, msg=t[6])


    def test_fails(self):
        test = [
            ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 10), 12, 210, 0.05714285714285714, "2erTreppeZ, Test 46"),
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
            self.assertAlmostEqual(t[5], sum(matches) / len(hands), places=15, msg=t[6])
            # probability_of_hands
            p = probability_of_hand(parse_cards(t[0]), t[1], t[2])
            self.assertAlmostEqual(t[5], p, places=15, msg=t[6])


if __name__ == "__main__":
    unittest.main()
