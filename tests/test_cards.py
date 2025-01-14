import unittest
# noinspection PyProtectedMember
from src.lib.cards import _deck_index, _cardlabels, _cardlabels_index
from src.lib.cards import *


class TestCards(unittest.TestCase):
    def test_parse_and_stringify_cards(self):
        self.assertTrue(len(deck) == len(_deck_index) == len(_cardlabels) == len(_cardlabels_index) == 56, "es gibt 56 Karten")
        self.assertEqual(list(deck), parse_cards(stringify_cards(deck)), "Index nicht OK")

    def test_is_wish_in(self):
        self.assertTrue(is_wish_in(10, parse_cards("RA Ph BZ BZ RB SB")), "eine 10 ist unter den Karten")
        self.assertFalse(is_wish_in(13, parse_cards("RA Ph BZ BZ RB SB")), "eine 10 ist nicht unter den Karten")

    def test_sum_card_points(self):
        self.assertEqual(5, sum_card_points(parse_cards("Ph GK BD RB RZ R9 R8 R7 R6 B5 G5 G3 B2 Ma")), "die Karten sind 5 Punkte wert")
        self.assertEqual(55, sum_card_points(parse_cards("Dr GK BD RB RZ R9 R8 R7 R6 B5 G5 G3 B2 Ma")), "die Karten sind 55 Punkte wert")
        self.assertEqual(30, sum_card_points(parse_cards("GK BD RB RZ R9 R8 R7 R6 B5 G5 G3 B2 Ma")), "die Karten sind 30 Punkte wert")

    def test_other_cards(self):
        self.assertEqual([(14, 1), (14, 2), (14, 3), (14, 4)], other_cards([card for card in deck if card[0] != 14]))

    def test_cards_to_vector(self):
        h = [
        #   Hu Ma 2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As
        # i=0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
            1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0,
        #   2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
        #  28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55
            0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        ]
        self.assertEqual(cards_to_vector([(0, 0), (14, 1), (10, 2), (5, 3), (2, 4)]), h)

        h = [
        #   Hu Ma 2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As
        # i=0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
            0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        #   2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
        #  28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1,
        ]
        self.assertEqual(cards_to_vector([(1, 0), (14, 4), (16, 0)]), h)

        h = [
        #   Hu Ma 2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As
        # i=0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
            0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        #   2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
        #  28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0,
        ]
        self.assertEqual(cards_to_vector([(2, 1), (15, 0)]), h)

    def test_ranks_to_vector(self):
        #   Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
        h = [1, 0, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 1, 0]
        self.assertEqual(ranks_to_vector([(0, 0), (2, 1), (3, 2), (2, 3), (14, 3), (14, 4), (15, 0)]), h)

        #   Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
        h = [0, 1, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 1]
        self.assertEqual(ranks_to_vector([(1, 0), (8, 1), (8, 2), (8, 3), (8, 4), (16, 0)]), h)


if __name__ == "__main__":
    unittest.main()
