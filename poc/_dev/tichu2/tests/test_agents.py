import logging

import config
from tichu.agents import *
from tichu.tichu import *
from unittest import TestCase
from web.database import init_flask_db

logger = logging.getLogger(__name__)
db = init_flask_db()
ws = WebSocket()


class TestRandomAgent(TestCase):
    def setUp(self):
        self.tichu = Tichu(logger, db, ws, seed=123)
        self.agent = RandomAgent(self.tichu, player=0, seed=123)
        self.agent.take_cards(8)

    def test_pre_play(self):
        self.assertEqual('G3 R3 S2 B2 G2 R2 Ma Hu', stringify_cards(self.agent._hand))
        self.assertEqual([8, 0, 0, 0], self.tichu.number_of_cards)
        self.assertEqual([0, 0, 0, 0], self.tichu.announcements)
        # take_cards
        for _ in range(7):
            self.agent.announce()  # Zufallsgenerator vorspulen, sa dass jetzt ein Tichu gesagt wird
        self.agent.take_cards(14)
        self.assertEqual('S4 B4 G4 R4 S3 B3 G3 R3 S2 B2 G2 R2 Ma Hu', stringify_cards(self.agent._hand))
        self.assertEqual([14, 0, 0, 0], self.tichu.number_of_cards)
        self.assertEqual([1, 0, 0, 0], self.tichu.announcements)
        # schupf
        schupfed_cards = self.agent.schupf()
        self.assertEqual([None, (4, 3), (2, 2), (4, 4)], schupfed_cards)
        self.assertEqual([11, 0, 0, 0], self.tichu.number_of_cards)
        self.assertEqual('G4 R4 S3 B3 G3 R3 S2 B2 R2 Ma Hu', stringify_cards(self.agent._hand))
        # take schupfed cards
        self.agent.take_schupfed_cards(schupfed_cards)
        self.assertEqual('S4 B4 G4 R4 S3 B3 G3 R3 S2 B2 G2 R2 Ma Hu', stringify_cards(self.agent._hand))
        self.assertEqual([14, 0, 0, 0], self.tichu.number_of_cards)

    def test_play(self):
        self.agent._hand = parse_cards('S4 B4 G4 R4 S3 B3 G3 R3 S2 B2 G2 R2 Ma')
        self.tichu._number_of_cards = [13, 14, 14, 14]
        self.tichu._trick_player = 0
        self.tichu._current_player = 0
        self.tichu._trick_figure = FIGURE_DRA
        self.tichu._played_cards.append(CARD_DRA)
        partitions = self.agent._partitions
        self.assertEqual(config.PARTITIONS_MAXLEN, len(partitions))
        self.agent.play()  # der Agent spielt hier 3erTreppe4
        self.assertEqual('S4 G4 S3 R3 B2 R2 Ma', stringify_cards(self.agent._hand))
        self.assertEqual([7, 14, 14, 14], self.tichu.number_of_cards)
        self.assertEqual(13, len(self.agent._partitions))
        self.assertEqual(1, self.tichu._current_player)

    def test_pass(self):
        self.agent._hand = parse_cards('S7 B7 G6 R6 S5 B5 G4 R4 S3 B3 G2 R2 Ma Hu')
        self.tichu._number_of_cards = [14, 14, 14, 13]
        self.tichu._trick_player = 3
        self.tichu._current_player = 0
        self.tichu._trick_figure = FIGURE_DRA
        self.tichu._played_cards.append(CARD_DRA)
        self.agent.play()
        self.assertEqual('S7 B7 G6 R6 S5 B5 G4 R4 S3 B3 G2 R2 Ma Hu', stringify_cards(self.agent._hand))
        self.assertEqual([14, 14, 14, 13], self.tichu.number_of_cards)
        self.assertEqual(1, self.tichu._current_player)

    def test_done(self):
        self.agent._hand = parse_cards('S7')
        self.tichu._number_of_cards = [1, 5, 0, 0]
        self.tichu._number_of_players = 2
        self.tichu._winner = 2
        self.tichu._current_player = 0
        self.agent.play()
        self.assertTrue(self.tichu.is_done)

    def test_wish(self):
        self.agent._hand = parse_cards('Ma')
        self.tichu._number_of_cards = [1, 14, 14, 14]
        self.tichu._current_player = 0
        self.assertEqual(0, self.tichu.wish)
        self.agent.play()
        self.assertEqual(4, self.tichu.wish)


class TestHeuristicAgent(TestCase):
    def setUp(self):
        self.tichu = Tichu(logger, db, ws, seed=123)
        self.agent = HeuristicAgent(self.tichu, player=0, seed=123)

    def testannounce(self):
        cards = parse_cards('SA GK BD GB SZ B9 G8 R7 S6 B5 G4 R3 S2 Ma')
        self.tichu._mixed_deck = cards + other_cards(cards)
        self.agent.take_cards(8)
        self.assertEqual([0, 0, 0, 0], self.tichu.announcements)
        self.agent.take_cards(14)
        self.tichu._number_of_cards = [14, 14, 14, 14]
        self.assertEqual([1, 0, 0, 0], self.tichu.announcements)
        result = self.agent.announce()
        self.assertFalse(result)

    def testschupf(self):
        # Niemand hat Tichu angesagt
        cards = parse_cards('SK SA GA BD GD SD B9 G9 R9 S6 B6 G6 R3 S2')
        self.tichu._mixed_deck = cards + other_cards(cards)
        self.agent.take_cards(8)
        self.agent.take_cards(14)
        self.tichu._number_of_cards = [14, 14, 14, 14]
        self.tichu._announcements = [0, 0, 0, 0]
        self.assertEqual([(3, 1), (13, 4), (2, 4)], self.agent.schupf())

        # Niemand hat Tichu angesagt und ich hab den Hund
        self.tichu.reset()
        cards = parse_cards('Dr BA GA RD GZ S8 R8 B8 G6 S6 G5 B5 S5 Hu')
        self.tichu._mixed_deck = cards + other_cards(cards)
        self.agent.take_cards(8)
        self.agent.take_cards(14)
        self.tichu._number_of_cards = [14, 14, 14, 14]
        self.tichu._announcements = [0, 0, 0, 0]
        self.assertEqual([(10, 2), (12, 1), (0, 0)], self.agent.schupf())

        # Ich hab Tichu angesagt
        self.tichu.reset()
        cards = parse_cards('Ph Dr BA GA RK GK SK RD BD GD SD GB BB SB')
        self.tichu._mixed_deck = cards + other_cards(cards)
        self.agent.take_cards(8)
        self.agent.take_cards(14)
        self.tichu._number_of_cards = [14, 14, 14, 14]
        self.tichu._announcements = [1, 0, 0, 0]
        self.assertEqual([(11, 4), (11, 3), (11, 2)], self.agent.schupf())

        # Ich hab Tichu angesagt und hab den Hund
        self.tichu.reset()
        cards = parse_cards('Dr BA GA RK GK SK RD BD GD SD GB BB SB Hu')
        self.tichu._mixed_deck = cards + other_cards(cards)
        self.agent.take_cards(8)
        self.agent.take_cards(14)
        self.tichu._number_of_cards = [14, 14, 14, 14]
        self.tichu._announcements = [1, 0, 0, 0]
        self.assertEqual([(11, 2), (0, 0), (11, 4)], self.agent.schupf())

        # Partner hat Tichu angesagt
        self.tichu.reset()
        cards = parse_cards('RZ GZ SZ R9 B9 G9 R8 G8 S8 G7 S7 B6 S5 Hu')
        self.tichu._mixed_deck = cards + other_cards(cards)
        self.agent.take_cards(8)
        self.agent.take_cards(14)
        self.tichu._number_of_cards = [14, 14, 14, 14]
        self.tichu._announcements = [0, 0, 1, 0]
        self.assertEqual([(8, 1), (10, 1), (7, 2)], self.agent.schupf())

        # Partner hat Tichu angesagt und ich hab den Drachen
        self.tichu.reset()
        cards = parse_cards('Dr BA GA RK GK SK RD BD GD SD GB BB SB Hu')
        self.tichu._mixed_deck = cards + other_cards(cards)
        self.agent.take_cards(8)
        self.agent.take_cards(14)
        self.tichu._number_of_cards = [14, 14, 14, 14]
        self.tichu._announcements = [0, 0, 1, 0]
        self.assertEqual([(11, 2), (15, 0), (11, 4)], self.agent.schupf())

    def testcombination_simple(self):
        # gibt nichts zu entscheiden
        cards = parse_cards('Dr RA GA BA G9 S8 R8 B8 G6 S6 G5 B5 S5 Ma')
        self.agent._hand = cards
        self.tichu._number_of_cards = [14, 14, 14, 14]
        action_space = [([CARD_DRA], FIGURE_DRA)]
        self.assertEqual(action_space[0], self.agent.combination(action_space))

        # Wir könnten und werden alle restlichen Karten ablegen.
        cards = parse_cards('RA GA BA')
        self.agent._hand = cards
        self.tichu._number_of_cards = [3, 14, 14, 14]
        action_space = [([], FIGURE_PASS), (cards, (3, 3, 14))]
        self.assertEqual(action_space[1], self.agent.combination(action_space))

        # Wie eben, aber der Partner hat Tichu gesagt. Wir machen nicht fertig.
        self.tichu._announcements = [0, 0, 1, 0]
        self.assertEqual(action_space[0], self.agent.combination(action_space))
        self.tichu._announcements = [0, 0, 0, 0]

        # Der Partner könnte den Stich bekommen. Wir passen und überstechen den Partner nicht.
        cards = parse_cards('Dr RA GA BA G9 S8 R8 B8 G6 S6 G5 B5 S5 Ma')
        self.agent._hand = cards
        self.tichu._number_of_cards = [14, 14, 10, 14]
        action_space = [([], FIGURE_PASS), (parse_cards('RA GA BA'), (3, 3, 14))]
        self.tichu._trick_player = 2
        self.assertEqual(action_space[0], self.agent.combination(action_space))
        self.tichu._trick_player = -1

        # Wir spielen den Hund
        cards = parse_cards('Dr BA Hu')
        self.agent._hand = cards
        self.tichu._number_of_cards = [3, 14, 10, 14]
        action_space =  [([CARD_DRA], FIGURE_DRA), (parse_cards('BA'), (1, 1, 14)), ([CARD_DOG], FIGURE_DOG)]
        self.assertEqual(action_space[2], self.agent.combination(action_space))

    def testcombination_one_combi(self):
        # Die beste Partition hat genau eine spielbare Kombi.
        cards = parse_cards('Dr RA GA BA')
        self.agent._hand = cards
        self.tichu._played_cards = parse_cards('G9 S8 R8 B8 G6 S6 G5 B5 S5 Ma')
        self.tichu._number_of_cards = [4, 14, 14, 14]
        action_space =  [(parse_cards('GA BA'), (1, 1, 14)), (parse_cards('RA BA'), (1, 1, 14))]
        self.assertEqual(action_space[0], self.agent.combination(action_space))

    def testcombination_more_combis(self):
        # Wir beste Partition hat mehrere spielbare Kombis.
        cards = parse_cards('RA GA GK BK')
        self.agent._hand = cards
        self.tichu._played_cards = parse_cards('Dr G9 S8 R8 B8 G6 S6 G5 B5 S5')
        self.tichu._number_of_cards = [4, 14, 14, 14]
        action_space = [(parse_cards('RA GA'), (2, 2, 14)), (parse_cards('GK BK'), (2, 2, 13))]
        self.assertEqual(action_space[1], self.agent.combination(action_space))

    def testcombination_bomb(self):
        # Wir haben eine Bombe
        cards = parse_cards('Dr RA GA BA SA')
        self.agent._hand = cards
        self.tichu._played_cards = parse_cards('G9 S8 R8 B8 G6 S6 G5 B5 S5')
        self.tichu._number_of_cards = [5, 14, 14, 14]
        action_space = [(parse_cards('RA GA BA SA'), (7, 4, 14)), ([CARD_DRA], FIGURE_DRA)]
        self.assertEqual(action_space[0], self.agent.combination(action_space))

        # Wie eben, aber der Partner hat Tichu gesagt. Wir schmeißen nicht die Bombe, sondern eine ander Kombi
        self.tichu._announcements = [0, 0, 1, 0]
        self.assertEqual(action_space[1], self.agent.combination(action_space))

        # Wie eben, aber wir könnten auch passen, was wir auch tun.
        action_space = [([], FIGURE_PASS), (parse_cards('RA GA BA SA'), (7, 4, 14))]
        self.assertEqual(action_space[0], self.agent.combination(action_space))
        self.tichu._announcements = [0, 0, 0, 0]

    def testwish(self):
        cards = parse_cards('Dr BA GA RD G9 S8 R8 B8 G6 S6 G5 B5 S5 Ma')
        self.tichu._mixed_deck = cards + other_cards(cards)
        self.agent.take_cards(8)
        self.agent.take_cards(14)
        self.agent._schupfed = parse_cards('G9 G6 S6')
        self.agent._hand = parse_cards('BA GA RD S8 R8 B8 G7 S7 G5 B5 S5 G4')
        self.tichu._played_cards = parse_cards('S4 R6 R7 Dr Ma')
        self.tichu._number_of_cards = [12, 13, 13, 13]
        self.assertEqual(9, self.agent.wish())
        # Straße wurde gespielt
        self.tichu.reset()
        cards = parse_cards('Dr BA GA RD G9 S8 R8 B7 G6 S5 G4 B3 S2 Ma')
        self.tichu._mixed_deck = cards + other_cards(cards)
        self.agent.take_cards(8)
        self.agent.take_cards(14)
        self.agent._schupfed = parse_cards('G9 RD S8')
        self.agent._hand = parse_cards('Dr BA GA RK SD R8 B7 G6 S5 G4 B3 S2 R2 Ma')
        self.tichu._trick_figure = (STREET, 8, 8)
        self.tichu._trick_vlaue = 5
        self.tichu._trick_player = 0
        self.tichu._played_cards = parse_cards('R8 B7 G6 S5 G4 B3 S2 Ma')
        self.tichu._number_of_cards = [8, 14, 14, 14]
        self.assertEqual(13, self.agent.wish())

    def testgift(self):
        cards = parse_cards('Dr BA GA RD G9 S8 R8 B8 G6 S6 G5 B5 S5 Ma')
        self.tichu._mixed_deck = cards + other_cards(cards)
        self.agent.take_cards(8)
        self.agent.take_cards(14)
        self.agent._schupfed = parse_cards('G9 G6 S6')
        self.agent._hand = parse_cards('BA GA RD S8 R8 B8 G7 S7 G5 B5 S5 G4')
        self.tichu._played_cards = parse_cards('S4 R6 R7 Dr')
        self.tichu._number_of_cards = [12, 12, 14, 14]
        self.assertEqual(3, self.agent.gift())
        self.tichu._number_of_cards = [12, 14, 14, 12]
        self.assertEqual(1, self.agent.gift())
        self.tichu._number_of_cards = [13, 13, 13, 13]
        self.assertEqual(3, self.agent.gift())
