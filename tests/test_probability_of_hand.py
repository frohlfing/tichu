import unittest
# noinspection PyProtectedMember
from src.lib.combinations import *
from src.lib.cards import *
from src.lib.probabilities import prob_of_hand


# noinspection DuplicatedCode
# class TestProbabilityOfHands(unittest.TestCase):
#     c = 0
#
#     def test_stair(self):
#         t = STAIR
#         combis = [
#             "SB RZ R9 G9 R8 G8 B4",
#             "SB RZ GZ R9 G9 R8 G8 B4",
#             "SB RZ GZ BZ R9 G9 R8 G8 B4",
#             "SB RZ GZ BZ SZ R9 G9 R8 G8 B4",
#             "SB RZ R9 G9 S9 R8 G8 B4",
#             "SB RZ GZ R9 G9 S9 R8 G8 B4",
#             "SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
#             "SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",
#             "Ph SB RZ R9 G9 R8 G8 B4",
#             "SB RZ Ph R9 G9 R8 G8 B4",
#             "SB RZ GZ BZ Ph G9 R8 G8 B4",
#             "SB RZ GZ BZ SZ R9 Ph R8 G8 B4",
#             "SB RZ R9 G9 S9 R8 G8 B4 Ph",
#             "Ph SB RZ GZ R9 G9 S9 R8 G8 B4",
#             "Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
#             "Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",
#         ]
#         for m in [4, 6]:
#             r = 10
#             for k in [0, 3, 4, 5, 6, 7, 9, 10, 13, 14]:
#                 for cards in combis:
#                     self.c += 1
#                     figure = (t, m, r)
#                     matches, hands = possible_hands(parse_cards(cards), k, figure)
#                     p_expect = sum(matches) / len(hands) if hands else 0.0
#                     msg = stringify_figure(figure)
#                     print(f'("{cards}", {k}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p_expect}, "{msg}, Test {self.c}"),'),
#                     p_actual = probability_of_hand(parse_cards(cards), k, figure)
#                     self.assertAlmostEqual(p_expect, p_actual, places=15, msg=msg)
#
#     def test_fullhouse(self):
#         t = FULLHOUSE
#         combis = [
#             "SB RZ R9 G9 R8 G8 B4",
#             "SB RZ GZ R9 G9 R8 G8 B4",
#             "SB RZ GZ BZ R9 G9 R8 G8 B4",
#             "SB RZ GZ BZ R9 G9 R9 G8 B4",
#             "SB RZ GZ BZ SZ R9 G9 R8 G8 B4",
#             "SB RZ R9 G9 S9 R8 G8 B4",
#             "SB RZ GZ R9 G9 S9 R8 G8 B4",
#             "SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
#             "SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",
#             "Ph SB RZ R9 G9 R8 G8 B4",
#             "SB RZ Ph R9 G9 R8 G8 B4",
#             "SB RZ GZ BZ Ph G9 R8 G8 B4",
#             "SB RZ GZ BZ SZ R9 Ph R8 G8 B4",
#             "SB RZ R9 G9 S9 R8 G8 B4 Ph",
#             "Ph SB RZ GZ R9 G9 S9 R8 G8 B4",
#             "Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
#             "Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",
#         ]
#         m = 5
#         r = 10
#         for k in [0, 3, 4, 5, 6, 7, 9, 10, 13, 14]:
#             for cards in combis:
#                 self.c += 1
#                 figure = (t, m, r)
#                 matches, hands = possible_hands(parse_cards(cards), k, figure)
#                 p_expect = sum(matches) / len(hands) if hands else 0.0
#                 msg = stringify_figure(figure)
#                 print(f'("{cards}", {k}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p_expect}, "{msg}, Test {self.c}"),'),
#                 p_actual = probability_of_hand(parse_cards(cards), k, figure)
#                 self.assertAlmostEqual(p_expect, p_actual, places=15, msg=msg)
#
#     def test_street(self):
#         t = STREET
#         combis = [
#             "GB RZ G9 R8 G7",
#             "GD RB GZ R9 G8 R7",
#             "GA RK GD RB GZ R9 S8 B7 S6 B5 S4 B3 S2",
#             "GA RK GD RB GZ R9 S8 B7 S6 B5 S4 B3 S2 Ma",
#             "GK BB SB GB RZ BZ GZ R9 S9 B9 R8 S8 G8 R7 S7 G7 R4 R2",
#             "SK GB GZ G9 G8 G7 RB RZ R9 R8 R7 BB BZ B9 B8 B7 S4 S2",
#
#             "GA RK GD RB GZ R9 S8 B7 S6 B5 S4 B3 Ph",
#             "GA RK GD Ph GZ R9 S8 B7 S6 B5 S4 B3 S2",
#             "GA RK GD RB GZ R9 S8 Ph S6 B5 S4 B3 S2",
#             "GA RK GD RB Ph R9 S8 B7 S6 B5 S4 B3 S2",
#             "GK RK GD RB Ph R9 S8 B7 S6 B5 S4 B3 S2",
#             "GK RB GZ R9 G8 R7 SB BZ S9 B8 S7 B4 Ph",
#             "Ph R7 G6 R5 G4 R3 S2 B2 Ma",
#             "Ph RB GZ R8 G7 R4 S2 B2",
#
#             "GB GZ G9 G8 G7",
#             "GD GB GZ G9 G8 G7",
#             "GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2",
#             "SK GB GZ G9 G8 G7 RB RZ R9 R8 R7 BB BZ B9 B8 B7 S4 S2",
#
#             "GA GK GD GB GZ G9 R8 G7 G6 G5 G4 G3 Ph",
#             "GA GK GD Ph GZ G9 R8 G7 G6 G5 G4 G3 G2",
#             "GA GK GD GB GZ G9 R8 Ph G6 G5 G4 G3 G2",
#             "GA GK GD GB Ph G9 G8 G7 G6 G5 G4 G3 G2",
#             "SK GB GZ G9 G8 G7 RB RZ R9 R8 R7 S4 Ph",
#         ]
#         for m in [5, 9, 10]:
#             r = 11
#             for k in [0, 4, 5, 6, 7, 9, 10, 13, 14]:
#                 for cards in combis:
#                     self.c += 1
#                     figure = (t, m, r)
#                     matches, hands = possible_hands(parse_cards(cards), k, figure)
#                     p_expect = sum(matches) / len(hands) if hands else 0.0
#                     msg = stringify_figure(figure)
#                     print(f'("{cards}", {k}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p_expect}, "{msg}, Test {self.c}"),'),
#                     p_actual = probability_of_hand(parse_cards(cards), k, figure)
#                     self.assertAlmostEqual(p_expect, p_actual, places=15, msg=msg)
#
#     def test_bomb_color(self):
#         t = BOMB  # Farbbombe
#         combis = [
#             "GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2",
#             "GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2 B2 S2",
#             "SK GB GZ G9 G8 G7 RB RZ R9 R8 R7 BB BZ B9 B8 B7 S4 S2",
#             "Ph GB GZ G8 G7 G4 B2 S2",
#         ]
#         for m in [5, 9, 10]:
#             r = 11
#             for k in [0, 4, 5, 6, 7, 9, 10, 13, 14]:
#                 for cards in combis:
#                     self.c += 1
#                     figure = (t, m, r)
#                     matches, hands = possible_hands(parse_cards(cards), k, figure)
#                     p_expect = sum(matches) / len(hands) if hands else 0.0
#                     msg = stringify_figure(figure)
#                     print(f'("{cards}", {k}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p_expect}, "{msg}, Test {self.c}"),'),
#                     p_actual = probability_of_hand(parse_cards(cards), k, figure)
#                     self.assertAlmostEqual(p_expect, p_actual, places=15, msg=msg)
#
#     def test_bomb_4er(self):
#         t = BOMB  # 4er-Bombe
#         combis = [
#             "SB RZ R9 G9 R8 G8 B4",
#             "SB RZ GZ R9 G9 R8 G8 B4",
#             "SB RZ GZ BZ R9 G9 R8 G8 B4",
#             "SB RZ GZ BZ SZ R9 G9 R8 G8 B4",
#             "SB RZ GZ BZ SZ R9 G9 S9 B9 G8 B4",
#             "Ph SB RZ R9 G9 R8 G8 B4",
#             "SB RZ GZ BZ Ph G9 R8 G8 B4",
#             "SB RZ GZ BZ SZ R9 Ph R8 G8 B4",
#             "Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
#             "Ph SB RZ GZ BZ SZ R9 G9 S9 B9 G8 B4",
#             "SB RZ GZ BZ SZ R9 G9 S9 B9 R8 G8 S8 B8 B4 B2",
#         ]
#         m = 4
#         r = 10
#         for k in [0, 3, 4, 5, 6, 7, 9, 10, 13, 14]:
#             for cards in combis:
#                 self.c += 1
#                 figure = (t, m, r)
#                 matches, hands = possible_hands(parse_cards(cards), k, figure)
#                 p_expect = sum(matches) / len(hands) if hands else 0.0
#                 msg = stringify_figure(figure)
#                 print(f'("{cards}", {k}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p_expect}, "{msg}, Test {self.c}"),'),
#                 p_actual = probability_of_hand(parse_cards(cards), k, figure)
#                 self.assertAlmostEqual(p_expect, p_actual, places=15, msg=msg)
#
#     def test_tripple(self):
#         t = TRIPLE
#         combis = [
#             "SB RZ R9 G9 R8 G8 B4",
#             "SB RZ GZ R9 G9 R8 G8 B4",
#             "SB RZ GZ BZ R9 G9 R8 G8 B4",
#             "SB RZ GZ BZ SZ R9 G9 R8 G8 B4",
#             "SB RZ R9 G9 S9 R8 G8 B4",
#             "SB RZ GZ R9 G9 S9 R8 G8 B4",
#             "SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
#             "SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",
#             "Ph SB RZ R9 G9 R8 G8 B4",
#             "SB RZ Ph R9 G9 R8 G8 B4",
#             "SB RZ GZ BZ Ph G9 R8 G8 B4",
#             "SB RZ GZ BZ SZ R9 Ph R8 G8 B4",
#             "SB RZ R9 G9 S9 R8 G8 B4 Ph",
#             "Ph SB RZ GZ R9 G9 S9 R8 G8 B4",
#             "Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
#             "Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",
#         ]
#         m = 3
#         r = 10
#         for k in [0, 3, 4, 5, 6, 7, 9, 10, 13, 14]:
#             for cards in combis:
#                 self.c += 1
#                 figure = (t, m, r)
#                 matches, hands = possible_hands(parse_cards(cards), k, figure)
#                 p_expect = sum(matches) / len(hands) if hands else 0.0
#                 msg = stringify_figure(figure)
#                 print(f'("{cards}", {k}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p_expect}, "{msg}, Test {self.c}"),'),
#                 p_actual = probability_of_hand(parse_cards(cards), k, figure)
#                 self.assertAlmostEqual(p_expect, p_actual, places=15, msg=msg)
#
#     def test_pair(self):
#         t = PAIR
#         combis = [
#             "SB RZ R9 G9 R8 G8 B4",
#             "SB RZ GZ R9 G9 R8 G8 B4",
#             "SB RZ GZ BZ R9 G9 R8 G8 B4",
#             "SB RZ GZ BZ SZ R9 G9 R8 G8 B4",
#             "SB RZ R9 G9 S9 R8 G8 B4",
#             "SB RZ GZ R9 G9 S9 R8 G8 B4",
#             "SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
#             "SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",
#             "Ph SB RZ R9 G9 R8 G8 B4",
#             "SB RZ Ph R9 G9 R8 G8 B4",
#             "SB RZ GZ BZ Ph G9 R8 G8 B4",
#             "SB RZ GZ BZ SZ R9 Ph R8 G8 B4",
#             "SB RZ R9 G9 S9 R8 G8 B4 Ph",
#             "Ph SB RZ GZ R9 G9 S9 R8 G8 B4",
#             "Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
#             "Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",
#         ]
#         m = 2
#         r = 10
#         for k in [0, 3, 4, 5, 6, 7, 9, 10, 13, 14]:
#             for cards in combis:
#                 self.c += 1
#                 figure = (t, m, r)
#                 matches, hands = possible_hands(parse_cards(cards), k, figure)
#                 p_expect = sum(matches) / len(hands) if hands else 0.0
#                 msg = stringify_figure(figure)
#                 print(f'("{cards}", {k}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p_expect}, "{msg}, Test {self.c}"),'),
#                 p_actual = probability_of_hand(parse_cards(cards), k, figure)
#                 self.assertAlmostEqual(p_expect, p_actual, places=15, msg=msg)
#
#     def test_single(self):
#         t = SINGLE
#         combis = [
#             "SB RZ R9 G9 R8 G8 B4",
#             "SB RZ GZ R9 G9 R8 G8 B4",
#             "SB RZ GZ BZ R9 G9 R8 G8 B4",
#             "SB RZ GZ BZ SZ R9 G9 R8 G8 B4",
#             "SB RZ R9 G9 S9 R8 G8 B4",
#             "SB RZ GZ R9 G9 S9 R8 G8 B4",
#             "SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
#             "SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",
#             "Ph SB RZ R9 G9 R8 G8 B4",
#             "SB RZ Ph R9 G9 R8 G8 B4",
#             "SB RZ GZ BZ Ph G9 R8 G8 B4",
#             "SB RZ GZ BZ SZ R9 Ph R8 G8 B4",
#             "SB RZ R9 G9 S9 R8 G8 B4 Ph",
#             "Ph SB RZ GZ R9 G9 S9 R8 G8 B4",
#             "Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
#             "Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",
#         ]
#         m = 1
#         r = 10
#         for k in [0, 3, 4, 5, 6, 7, 9, 10, 13, 14]:
#             for cards in combis:
#                 self.c += 1
#                 figure = (t, m, r)
#                 matches, hands = possible_hands(parse_cards(cards), k, figure)
#                 p_expect = sum(matches) / len(hands) if hands else 0.0
#                 msg = stringify_figure(figure)
#                 print(f'("{cards}", {k}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p_expect}, "{msg}, Test {self.c}"),'),
#                 p_actual = probability_of_hand(parse_cards(cards), k, figure)
#                 self.assertAlmostEqual(p_expect, p_actual, places=15, msg=msg)


class TestProbabilityOfHandsHi(unittest.TestCase):
    c = 0

    def test_stair(self):
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
            "Ph GK BK SD SB RB BZ R9",
            "Ph GK BK SD SB RB R9",
            "Ph GK BK SD SB R9 S4",
        ]
        for m in [4, 6]:
            for r in [9, 10]:
                for k in [0, 3, 4, 5, 6, 7, 9, 10, 13, 14]:
                    for cards in combis:
                        self.c += 1
                        figure = (t, m, r)
                        matches, hands = possible_hands_hi(parse_cards(cards), k, figure)
                        p_expect = sum(matches) / len(hands) if hands else 0.0
                        msg = stringify_figure(figure)
                        print(f'("{cards}", {k}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p_expect}, "{msg}, Test {self.c}"),'),
                        p_actual = prob_of_hand(parse_cards(cards), k, figure)
                        self.assertAlmostEqual(p_expect, p_actual, places=15, msg=msg)

    def test_fullhouse(self):
        t = FULLHOUSE
        combis = [
            "SB RZ R9 G9 R8 G8 B4",
            "SB RZ GZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 R9 G8 B4",
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
        m = 5
        r = 9
        for k in [0, 3, 4, 5, 6, 7, 9, 10, 13, 14]:
            for cards in combis:
                self.c += 1
                figure = (t, m, r)
                matches, hands = possible_hands_hi(parse_cards(cards), k, figure)
                p_expect = sum(matches) / len(hands) if hands else 0.0
                msg = stringify_figure(figure)
                print(f'("{cards}", {k}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p_expect}, "{msg}, Test {self.c}"),'),
                p_actual = prob_of_hand(parse_cards(cards), k, figure)
                self.assertAlmostEqual(p_expect, p_actual, places=15, msg=msg)

    def test_street_ohne_pho_ohne_bombe(self):
        t = STREET
        combis = [
            "GB RZ G9 R8 G7",
            "GD RB GZ R9 G8 R7",
            "GA RK GD RB GZ R9 S8 B7 S6 B5 S4 B3 S2",
            "GA RK GD RB GZ R9 S8 B7 S6 B5 S4 B3 S2 Ma",
            "GK BB SB GB RZ BZ GZ R9 S9 B9 R8 S8 G8 R7 S7 G7 R4 R2",
        ]
        for m in [5]:
            r = 10
            for k in [0, 4, 5, 6, 7]:
                for cards in combis:
                    self.c += 1
                    figure = (t, m, r)
                    matches, hands = possible_hands_hi(parse_cards(cards), k, figure)
                    p_expect = sum(matches) / len(hands) if hands else 0.0
                    msg = stringify_figure(figure)
                    print(f'("{cards}", {k}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p_expect}, "{msg}, Test {self.c}"),'),
                    p_actual = prob_of_hand(parse_cards(cards), k, figure)
                    self.assertAlmostEqual(p_expect, p_actual, places=15, msg=msg)

    def test_street_mit_pho_ohne_bombe(self):
        t = STREET
        combis = [
            "GA RK GD RB GZ R9 S8 B7 S6 B5 S4 B3 Ph",
            "GA RK GD Ph GZ R9 S8 B7 S6 B5 S4 B3 S2",
            "GA RK GD RB GZ R9 S8 Ph S6 B5 S4 B3 S2",
            "GA RK GD RB Ph R9 S8 B7 S6 B5 S4 B3 S2",
            "GK RK GD RB Ph R9 S8 B7 S6 B5 S4 B3 S2",
            "GK RB GZ R9 G8 R7 SB BZ S9 B8 S7 B4 Ph",
            "Ph R7 G6 R5 G4 R3 S2 B2 Ma",
            "Ph RB GZ R8 G7 R4 S2 B2",
        ]
        for m in [5]:
            r = 10
            for k in [0, 4, 5, 6, 7]:
                for cards in combis:
                    self.c += 1
                    figure = (t, m, r)
                    matches, hands = possible_hands_hi(parse_cards(cards), k, figure)
                    p_expect = sum(matches) / len(hands) if hands else 0.0
                    msg = stringify_figure(figure)
                    print(f'("{cards}", {k}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p_expect}, "{msg}, Test {self.c}"),'),
                    p_actual = prob_of_hand(parse_cards(cards), k, figure)
                    self.assertAlmostEqual(p_expect, p_actual, places=15, msg=msg)

    def test_street_ohne_pho_mit_bombe(self):
        t = STREET
        combis = [
            "GB GZ G9 G8 G7",
            "GD GB GZ G9 G8 G7",
            "GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2",
            "SK GB GZ G9 G8 G7 RB RZ R9 R8 R7 BB BZ B9 B8 B7 S4 S2",
        ]
        for m in [5]:
            r = 10
            for k in [0, 4, 5, 6, 7]:
                for cards in combis:
                    self.c += 1
                    figure = (t, m, r)
                    matches, hands = possible_hands_hi(parse_cards(cards), k, figure)
                    p_expect = sum(matches) / len(hands) if hands else 0.0
                    msg = stringify_figure(figure)
                    print(f'("{cards}", {k}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p_expect}, "{msg}, Test {self.c}"),'),
                    p_actual = prob_of_hand(parse_cards(cards), k, figure)
                    self.assertAlmostEqual(p_expect, p_actual, places=15, msg=msg)

    def test_street_mit_pho_mit_bombe(self):
        t = STREET
        combis = [
            "GA GK GD GB GZ G9 R8 G7 G6 G5 G4 G3 Ph",
            "GA GK GD Ph GZ G9 R8 G7 G6 G5 G4 G3 G2",
            "GA GK GD GB GZ G9 R8 Ph G6 G5 G4 G3 G2",
            "GA GK GD GB Ph G9 G8 G7 G6 G5 G4 G3 G2",
            "SK GB GZ G9 G8 G7 RB RZ R9 R8 R7 S4 Ph",
        ]
        for m in [5]:
            r = 10
            for k in [0, 4, 5, 6, 7]:
                for cards in combis:
                    self.c += 1
                    figure = (t, m, r)
                    matches, hands = possible_hands_hi(parse_cards(cards), k, figure)
                    p_expect = sum(matches) / len(hands) if hands else 0.0
                    msg = stringify_figure(figure)
                    print(f'("{cards}", {k}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p_expect}, "{msg}, Test {self.c}"),'),
                    p_actual = prob_of_hand(parse_cards(cards), k, figure)
                    self.assertAlmostEqual(p_expect, p_actual, places=15, msg=msg)

    def test_bomb_color(self):
        t = BOMB  # Farbbombe
        combis = [
            "GB GZ G9 G8 G7",
            "GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2",
            "GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2 B2 S2",
            "SK GB GZ G9 G8 G7 RB RZ R9 R8 R7 BB BZ B9 B8 B7 S4 S2",
            "Ph GB GZ G8 G7 G4 B2 S2",
        ]
        for m in [5]:
            r = 10
            for k in [0, 4, 5, 6, 7]:
                for cards in combis:
                    self.c += 1
                    figure = (t, m, r)
                    matches, hands = possible_hands_hi(parse_cards(cards), k, figure)
                    p_expect = sum(matches) / len(hands) if hands else 0.0
                    msg = stringify_figure(figure)
                    print(f'("{cards}", {k}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p_expect}, "{msg}, Test {self.c}"),'),
                    p_actual = prob_of_hand(parse_cards(cards), k, figure)
                    self.assertAlmostEqual(p_expect, p_actual, places=15, msg=msg)

    def test_bomb_4er(self):
        t = BOMB  # 4er-Bombe
        combis = [
            "SB RZ R9 G9 R8 G8 B4",
            "SB RZ GZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 S9 B9 G8 B4",
            "Ph SB RZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ Ph G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 Ph R8 G8 B4",
            "Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ SZ R9 G9 S9 B9 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 S9 B9 R8 G8 S8 B8 B4 B2",
        ]
        m = 4
        r = 9
        for k in [0, 3, 4, 5, 6, 7, 9, 10, 13, 14]:
            for cards in combis:
                self.c += 1
                figure = (t, m, r)
                matches, hands = possible_hands_hi(parse_cards(cards), k, figure)
                p_expect = sum(matches) / len(hands) if hands else 0.0
                msg = stringify_figure(figure)
                print(f'("{cards}", {k}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p_expect}, "{msg}, Test {self.c}"),'),
                p_actual = prob_of_hand(parse_cards(cards), k, figure)
                self.assertAlmostEqual(p_expect, p_actual, places=15, msg=msg)

    def test_tripple(self):
        t = TRIPLE
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
        m = 3
        r = 9
        for k in [0, 3, 4, 5, 6, 7, 9, 10, 13, 14]:
            for cards in combis:
                self.c += 1
                figure = (t, m, r)
                matches, hands = possible_hands_hi(parse_cards(cards), k, figure)
                p_expect = sum(matches) / len(hands) if hands else 0.0
                msg = stringify_figure(figure)
                print(f'("{cards}", {k}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p_expect}, "{msg}, Test {self.c}"),'),
                p_actual = prob_of_hand(parse_cards(cards), k, figure)
                self.assertAlmostEqual(p_expect, p_actual, places=15, msg=msg)

    def test_pair(self):
        t = PAIR
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
        m = 2
        r = 9
        for k in [0, 3, 4, 5, 6, 7, 9, 10, 13, 14]:
            for cards in combis:
                self.c += 1
                figure = (t, m, r)
                matches, hands = possible_hands_hi(parse_cards(cards), k, figure)
                p_expect = sum(matches) / len(hands) if hands else 0.0
                msg = stringify_figure(figure)
                print(f'("{cards}", {k}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p_expect}, "{msg}, Test {self.c}"),'),
                p_actual = prob_of_hand(parse_cards(cards), k, figure)
                self.assertAlmostEqual(p_expect, p_actual, places=15, msg=msg)

    def test_single(self):
        t = SINGLE
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
        m = 1
        r = 9
        for k in [0, 3, 4, 5, 6, 7, 9, 10, 13, 14]:
            for cards in combis:
                self.c += 1
                figure = (t, m, r)
                matches, hands = possible_hands_hi(parse_cards(cards), k, figure)
                p_expect = sum(matches) / len(hands) if hands else 0.0
                msg = stringify_figure(figure)
                print(f'("{cards}", {k}, ({figure[0]}, {figure[1]}, {figure[2]}), {sum(matches)}, {len(hands)}, {p_expect}, "{msg}, Test {self.c}"),'),
                p_actual = prob_of_hand(parse_cards(cards), k, figure)
                self.assertAlmostEqual(p_expect, p_actual, places=15, msg=msg)


if __name__ == "__main__":
    unittest.main()
