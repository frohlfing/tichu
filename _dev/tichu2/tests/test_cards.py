# noinspection PyProtectedMember
from tichu.cards import deck_index, cardlabels, cardlabels_index, HASH_ALL
from tichu.cards import *
from unittest import TestCase


class TestCards(TestCase):
    def test_parse_and_stringify_cards(self):
        self.assertTrue(len(deck) == len(deck_index) == len(cardlabels) == len(cardlabels_index) == 56, 'es gibt 56 Karten')
        self.assertEqual(list(deck), parse_cards(stringify_cards(deck)), 'Index nicht OK')

    def test_is_wish_in(self):
        self.assertTrue(is_wish_in(10, parse_cards('RA Ph BZ BZ RB SB')), 'eine 10 ist unter den Karten')
        self.assertFalse(is_wish_in(13, parse_cards('RA Ph BZ BZ RB SB')), 'eine 10 ist nicht unter den Karten')

    def test_sum_card_points(self):
        self.assertEqual(5, sum_card_points(parse_cards('Ph GK BD RB RZ R9 R8 R7 R6 B5 G5 G3 B2 Ma')), 'die Karten sind 5 Punkte wert')
        self.assertEqual(55, sum_card_points(parse_cards('Dr GK BD RB RZ R9 R8 R7 R6 B5 G5 G3 B2 Ma')), 'die Karten sind 55 Punkte wert')
        self.assertEqual(30, sum_card_points(parse_cards('GK BD RB RZ R9 R8 R7 R6 B5 G5 G3 B2 Ma')), 'die Karten sind 30 Punkte wert')

    def test_other_cards(self):
        self.assertEqual([(14, 1), (14, 2), (14, 3), (14, 4)], other_cards([card for card in deck if card[0] != 14]))

    def test_hash(self):
        self.assertEqual(HASH_ALL, cards_to_hash(deck))
        cards = parse_cards('Hu B2 R7 BD SK Ph')
        self.assertEqual(cards, hash_to_cards(cards_to_hash(cards)))
