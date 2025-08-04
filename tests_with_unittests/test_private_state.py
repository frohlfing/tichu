import unittest
from src import config
from src.lib.cards import *
from src.lib.combinations import *
from src.private_state import PrivateState
from src.public_state import PublicState


# noinspection DuplicatedCode
class TestPrivateState(unittest.TestCase):
    def setUp(self):
        self.pub = PublicState()
        self.priv = PrivateState(player_index=0)

    def test_pre_play(self):
        cards = self.pub.deal_out(0, 8)
        self.priv.take_cards(cards)
        self.pub.set_number_of_cards(0, 8)
        self.assertEqual("G3 R3 S2 B2 G2 R2 Ma Hu", stringify_cards(self.priv._hand))
        self.assertEqual([8, 0, 0, 0], self.pub.count_hand_cards)
        self.assertEqual([0, 0, 0, 0], self.pub.announcements)
        self.assertTrue(CARD_MAH in self.priv.hand_cards)

        # take_cards
        cards = self.pub.deal_out(0, 14)
        self.priv.take_cards(cards)
        self.pub.set_number_of_cards(0, 14)
        self.pub.announce(0, False)
        self.assertEqual("S4 B4 G4 R4 S3 B3 G3 R3 S2 B2 G2 R2 Ma Hu", stringify_cards(self.priv._hand))
        self.assertEqual([14, 0, 0, 0], self.pub.count_hand_cards)
        self.assertEqual([1, 0, 0, 0], self.pub.announcements)

        # schupf
        schupfed_cards = self.priv.schupf(parse_cards("B4 G2 S4"))
        self.pub.set_number_of_cards(0, 11)
        self.assertEqual([None, (4, 3), (2, 2), (4, 4)], schupfed_cards)
        self.assertEqual("G4 R4 S3 B3 G3 R3 S2 B2 R2 Ma Hu", stringify_cards(self.priv._hand))
        self.assertEqual([11, 0, 0, 0], self.pub.count_hand_cards)

        # take schupfed cards
        self.priv.take_schupfed_cards(schupfed_cards)
        self.pub.set_number_of_cards(0, 14)
        self.assertEqual("S4 B4 G4 R4 S3 B3 G3 R3 S2 B2 G2 R2 Ma Hu", stringify_cards(self.priv._hand))
        self.assertEqual([14, 0, 0, 0], self.pub.count_hand_cards)

    def test_play(self):
        self.priv._hand = parse_cards("S4 B4 G4 R4 S3 B3 G3 R3 S2 B2 G2 R2 Ma")
        self.pub._number_of_cards = [13, 14, 14, 14]
        self.pub._trick_player_index = 0
        self.pub.current_turn_index = 0
        self.pub._trick_figure = (CombinationType.SINGLE, 1, 15)
        self.pub.played_cards.append(CARD_DRA)
        # Partitionen
        partitions = self.priv.partitions
        self.assertEqual(config.PARTITIONS_MAXLEN, len(partitions))
        # der Agent spielt 3erTreppe4
        cards = parse_cards("B4 R4 B3 G3 S2 G2")
        combi = cards, get_trick_combination(cards, 0)
        self.priv.play(combi)
        self.pub.play(combi)
        self.pub.turn()
        self.assertEqual("S4 G4 S3 R3 B2 R2 Ma", stringify_cards(self.priv._hand))
        self.assertEqual(13, len(self.priv.partitions))
        self.assertEqual([7, 14, 14, 14], self.pub.count_hand_cards)
        self.assertEqual(1, self.pub.current_turn_index)

    def test_pass(self):
        combi = [], (0,0,0)  # passen
        self.priv._hand = parse_cards("S7 B7 G6 R6 S5 B5 G4 R4 S3 B3 G2 R2 Ma Hu")
        self.pub._number_of_cards = [14, 14, 14, 13]
        self.pub._trick_player_index = 3
        self.pub.current_turn_index = 0
        self.pub._trick_figure = (CombinationType.SINGLE, 1, 15)
        self.pub.played_cards.append(CARD_DRA)
        self.priv.play(combi)
        self.pub.play(combi)
        self.pub.turn()
        self.assertEqual("S7 B7 G6 R6 S5 B5 G4 R4 S3 B3 G2 R2 Ma Hu", stringify_cards(self.priv._hand))
        self.assertEqual([14, 14, 14, 13], self.pub.count_hand_cards)
        self.assertEqual(1, self.pub.current_turn_index)

    def test_done(self):
        cards = parse_cards("S7")
        combi = cards, get_trick_combination(cards, 0)
        self.priv._hand = cards
        self.pub._number_of_cards = [1, 5, 0, 0]
        self.pub._number_of_players = 2
        self.pub._winner = 2
        self.pub.current_turn_index = 0
        self.priv.play(combi)
        self.pub.play(combi)
        self.assertTrue(self.pub.is_round_over)

    def test_wish(self):
        cards = parse_cards("Ma")
        combi = cards, get_trick_combination(cards, 0)
        self.priv._hand = cards
        self.pub._number_of_cards = [1, 14, 14, 14]
        self.pub.current_turn_index = 0
        self.assertEqual(0, self.pub.wish_value)
        self.priv.play(combi)
        self.pub.play(combi)
        self.pub.set_wish(4)
        self.assertEqual(4, self.pub.wish_value)


if __name__ == "__main__":
    unittest.main()
