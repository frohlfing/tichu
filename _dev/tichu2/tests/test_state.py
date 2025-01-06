import logging
import config
from tichu.agents import *
from tichu.state import PublicState, PrivateState
from unittest import TestCase
from web.database import init_flask_db

logger = logging.getLogger(__name__)
db = init_flask_db()
ws = WebSocket()


# todo
class TestPrivateState(TestCase):
    def setUp(self):
        self.tichu = Tichu(logger, db, ws, seed=123)
        self.priv = PrivateState(self.tichu, player=0)
        self.priv.take_cards(8)

    def test_pre_play(self):
        self.assertEqual('G3 R3 S2 B2 G2 R2 Ma Hu', stringify_cards(self.priv._hand))
        self.assertEqual([8, 0, 0, 0], self.tichu.number_of_cards)
        self.assertEqual([0, 0, 0, 0], self.tichu.announcements)
        # take_cards
        for _ in range(7):
            self.priv._compute_announce()  # Zufallsgenerator vorspulen, sa dass jetzt ein Tichu gesagt wird
        self.priv.take_cards(14)
        self.assertEqual('S4 B4 G4 R4 S3 B3 G3 R3 S2 B2 G2 R2 Ma Hu', stringify_cards(self.priv._hand))
        self.assertEqual([14, 0, 0, 0], self.tichu.number_of_cards)
        self.assertEqual([1, 0, 0, 0], self.tichu.announcements)
        # schupf
        schupfed_cards = self.priv.schupf()
        self.assertEqual([None, (4, 3), (2, 2), (4, 4)], schupfed_cards)
        self.assertEqual([11, 0, 0, 0], self.tichu.number_of_cards)
        self.assertEqual('G4 R4 S3 B3 G3 R3 S2 B2 R2 Ma Hu', stringify_cards(self.priv._hand))
        # take schupfed cards
        self.priv.take_schupfed_cards(schupfed_cards)
        self.assertEqual('S4 B4 G4 R4 S3 B3 G3 R3 S2 B2 G2 R2 Ma Hu', stringify_cards(self.priv._hand))
        self.assertEqual([14, 0, 0, 0], self.tichu.number_of_cards)

    def test_play(self):
        self.priv._hand = parse_cards('S4 B4 G4 R4 S3 B3 G3 R3 S2 B2 G2 R2 Ma')
        self.tichu._number_of_cards = [13, 14, 14, 14]
        self.tichu._trick_player = 0
        self.tichu._current_player = 0
        self.tichu._trick_figure = FIGURE_DRA
        self.tichu._played_cards.append(CARD_DRA)
        partitions = self.priv._partitions
        self.assertEqual(config.PARTITIONS_MAXLEN, len(partitions))
        self.priv.play()  # der Agent spielt hier 3erTreppe4
        self.assertEqual('S4 G4 S3 R3 B2 R2 Ma', stringify_cards(self.priv._hand))
        self.assertEqual([7, 14, 14, 14], self.tichu.number_of_cards)
        self.assertEqual(13, len(self.priv._partitions))
        self.assertEqual(1, self.tichu._current_player)

    def test_pass(self):
        self.priv._hand = parse_cards('S7 B7 G6 R6 S5 B5 G4 R4 S3 B3 G2 R2 Ma Hu')
        self.tichu._number_of_cards = [14, 14, 14, 13]
        self.tichu._trick_player = 3
        self.tichu._current_player = 0
        self.tichu._trick_figure = FIGURE_DRA
        self.tichu._played_cards.append(CARD_DRA)
        self.priv.play()
        self.assertEqual('S7 B7 G6 R6 S5 B5 G4 R4 S3 B3 G2 R2 Ma Hu', stringify_cards(self.priv._hand))
        self.assertEqual([14, 14, 14, 13], self.tichu.number_of_cards)
        self.assertEqual(1, self.tichu._current_player)

    def test_done(self):
        self.priv._hand = parse_cards('S7')
        self.tichu._number_of_cards = [1, 5, 0, 0]
        self.tichu._number_of_players = 2
        self.tichu._winner = 2
        self.tichu._current_player = 0
        self.priv.play()
        self.assertTrue(self.tichu.is_done)

    def test_wish(self):
        self.priv._hand = parse_cards('Ma')
        self.tichu._number_of_cards = [1, 14, 14, 14]
        self.tichu._current_player = 0
        self.assertEqual(0, self.tichu.wish)
        self.priv.play()
        self.assertEqual(4, self.tichu.wish)
