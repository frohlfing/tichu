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


if __name__ == "__main__":
    unittest.main()
