import unittest
# noinspection PyProtectedMember
#from src.lib.cards import _deck_index, _cardlabels, _cardlabels_index
#from src.lib.cards import *
from src.lib.probabilities import ranks_to_vector, cards_to_vector
#from src.lib.probabilities import *


class TestProbabilities(unittest.TestCase):
    # def test_cards_to_vector(self):
    #     # r= 2  3  4  5  6  7  8  9 10 Bu Da Kö As
    #     h = [
    #         [1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0],  # schwarz
    #         [0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0],  # blau
    #         [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0],  # grün
    #         [0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1],  # rot
    #     ]
    #     self.assertEqual(count_cards([(0, 0), (2, 1), (3, 2), (4, 3), (5, 4), (8, 1), (8, 2), (8, 3), (8, 4), (11, 1), (12, 2), (13, 3), (14, 4), (15, 0)]), h)

    def test_ranks_to_vector(self):
        #   Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
        h = [1, 0, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 1, 0]
        self.assertEqual(ranks_to_vector([(0, 0), (2, 1), (3, 2), (2, 3), (14, 3), (14, 4), (15, 0)]), h)

        #   Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
        h = [0, 1, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 1]
        self.assertEqual(ranks_to_vector([(1, 0), (8, 1), (8, 2), (8, 3), (8, 4), (16, 0)]), h)

    def test_cards_to_vector(self):
        # r=Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
        # i= 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55
        h = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.assertEqual(cards_to_vector([(0, 0), (14, 1), (10, 2), (5, 3), (2, 4)]), h)

        # r=Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
        # i= 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55
        h = [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1]
        self.assertEqual(cards_to_vector([(1, 0), (14, 4), (16, 0)]), h)

        # r=Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
        # i= 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55
        h = [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]
        self.assertEqual(cards_to_vector([(2, 1), (15, 0)]), h)


if __name__ == "__main__":
    unittest.main()
