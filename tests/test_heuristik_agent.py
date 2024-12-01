import unittest
from src.lib.cards import *
from src.lib.combinations import *
from src.players.random_agent import RandomAgent
from src.private_state import PrivateState
from src.public_state import PublicState


class TestHeuristicAgent(unittest.TestCase):
    def setUp(self):
        self.agent = RandomAgent(seed=123)
        self.pub = PublicState(seed=123)
        self.priv = PrivateState(0)

    def test_announce(self):
        cards = parse_cards("SA GK BD GB SZ B9 G8 R7 S6 B5 G4 R3 S2 Ma")
        self.pub._mixed_deck = cards + other_cards(cards)
        cards = self.pub.deal_out(0, 8)
        self.priv.take_cards(cards)
        self.assertEqual([0, 0, 0, 0], self.pub.announcements)
        cards = self.pub.deal_out(0, 14)
        self.priv.take_cards(cards)
        self.pub._number_of_cards = [14, 14, 14, 14]
        self.assertEqual([1, 0, 0, 0], self.pub.announcements)
        result = self.agent.announce(self.pub, self.priv, False)
        self.assertFalse(result)

    def test_schupf(self):
        # Niemand hat Tichu angesagt
        cards = parse_cards("SK SA GA BD GD SD B9 G9 R9 S6 B6 G6 R3 S2")
        self.pub._mixed_deck = cards + other_cards(cards)
        cards = self.pub.deal_out(0, 8)
        self.priv.take_cards(cards)
        self.assertEqual([0, 0, 0, 0], self.pub.announcements)
        cards = self.pub.deal_out(0, 14)
        self.priv.take_cards(cards)
        self.pub._number_of_cards = [14, 14, 14, 14]
        self.pub._announcements = [0, 0, 0, 0]
        self.assertEqual([(3, 1), (13, 4), (2, 4)], self.agent.schupf())

        # Niemand hat Tichu angesagt und ich hab den Hund
        self.pub.reset()
        cards = parse_cards("Dr BA GA RD GZ S8 R8 B8 G6 S6 G5 B5 S5 Hu")
        self.pub._mixed_deck = cards + other_cards(cards)
        cards = self.pub.deal_out(0, 8)
        self.priv.take_cards(cards)
        self.assertEqual([0, 0, 0, 0], self.pub.announcements)
        cards = self.pub.deal_out(0, 14)
        self.priv.take_cards(cards)
        self.pub._number_of_cards = [14, 14, 14, 14]
        self.pub._announcements = [0, 0, 0, 0]
        self.assertEqual([(10, 2), (12, 1), (0, 0)], self.agent.schupf())

        # Ich hab Tichu angesagt
        self.pub.reset()
        cards = parse_cards("Ph Dr BA GA RK GK SK RD BD GD SD GB BB SB")
        self.pub._mixed_deck = cards + other_cards(cards)
        cards = self.pub.deal_out(0, 8)
        self.priv.take_cards(cards)
        self.assertEqual([0, 0, 0, 0], self.pub.announcements)
        cards = self.pub.deal_out(0, 14)
        self.priv.take_cards(cards)
        self.pub._number_of_cards = [14, 14, 14, 14]
        self.pub._announcements = [1, 0, 0, 0]
        self.assertEqual([(11, 4), (11, 3), (11, 2)], self.agent.schupf())

        # Ich hab Tichu angesagt und hab den Hund
        self.pub.reset()
        cards = parse_cards("Dr BA GA RK GK SK RD BD GD SD GB BB SB Hu")
        self.pub._mixed_deck = cards + other_cards(cards)
        cards = self.pub.deal_out(0, 8)
        self.priv.take_cards(cards)
        self.assertEqual([0, 0, 0, 0], self.pub.announcements)
        cards = self.pub.deal_out(0, 14)
        self.priv.take_cards(cards)
        self.pub._number_of_cards = [14, 14, 14, 14]
        self.pub._announcements = [1, 0, 0, 0]
        self.assertEqual([(11, 2), (0, 0), (11, 4)], self.agent.schupf())

        # Partner hat Tichu angesagt
        self.pub.reset()
        cards = parse_cards("RZ GZ SZ R9 B9 G9 R8 G8 S8 G7 S7 B6 S5 Hu")
        self.pub._mixed_deck = cards + other_cards(cards)
        cards = self.pub.deal_out(0, 8)
        self.priv.take_cards(cards)
        self.assertEqual([0, 0, 0, 0], self.pub.announcements)
        cards = self.pub.deal_out(0, 14)
        self.priv.take_cards(cards)
        self.pub._number_of_cards = [14, 14, 14, 14]
        self.pub._announcements = [0, 0, 1, 0]
        self.assertEqual([(8, 1), (10, 1), (7, 2)], self.agent.schupf())

        # Partner hat Tichu angesagt und ich hab den Drachen
        self.pub.reset()
        cards = parse_cards("Dr BA GA RK GK SK RD BD GD SD GB BB SB Hu")
        self.pub._mixed_deck = cards + other_cards(cards)
        cards = self.pub.deal_out(0, 8)
        self.priv.take_cards(cards)
        self.assertEqual([0, 0, 0, 0], self.pub.announcements)
        cards = self.pub.deal_out(0, 14)
        self.priv.take_cards(cards)
        self.pub._number_of_cards = [14, 14, 14, 14]
        self.pub._announcements = [0, 0, 1, 0]
        self.assertEqual([(11, 2), (15, 0), (11, 4)], self.agent.schupf())

    def test_combination_simple(self):
        # gibt nichts zu entscheiden
        cards = parse_cards("Dr RA GA BA G9 S8 R8 B8 G6 S6 G5 B5 S5 Ma")
        self.agent._hand = cards
        self.pub._number_of_cards = [14, 14, 14, 14]
        action_space = [([CARD_DRA], FIGURE_DRA)]
        self.assertEqual(action_space[0], self.agent.combination(action_space))

        # Wir könnten und werden alle restlichen Karten ablegen.
        cards = parse_cards("RA GA BA")
        self.agent._hand = cards
        self.pub._number_of_cards = [3, 14, 14, 14]
        action_space = [([], FIGURE_PASS), (cards, (3, 3, 14))]
        self.assertEqual(action_space[1], self.agent.combination(action_space))

        # Wie eben, aber der Partner hat Tichu gesagt. Wir machen nicht fertig.
        self.pub._announcements = [0, 0, 1, 0]
        self.assertEqual(action_space[0], self.agent.combination(action_space))
        self.pub._announcements = [0, 0, 0, 0]

        # Der Partner könnte den Stich bekommen. Wir passen und überstechen den Partner nicht.
        cards = parse_cards("Dr RA GA BA G9 S8 R8 B8 G6 S6 G5 B5 S5 Ma")
        self.agent._hand = cards
        self.pub._number_of_cards = [14, 14, 10, 14]
        action_space = [([], FIGURE_PASS), (parse_cards("RA GA BA"), (3, 3, 14))]
        self.pub._trick_player_index = 2
        self.assertEqual(action_space[0], self.agent.combination(action_space))
        self.pub._trick_player_index = -1

        # Wir spielen den Hund
        cards = parse_cards("Dr BA Hu")
        self.agent._hand = cards
        self.pub._number_of_cards = [3, 14, 10, 14]
        action_space =  [([CARD_DRA], FIGURE_DRA), (parse_cards("BA"), (1, 1, 14)), ([CARD_DOG], FIGURE_DOG)]
        self.assertEqual(action_space[2], self.agent.combination(action_space))

    def test_combination_one_combi(self):
        # Die beste Partition hat genau eine spielbare Kombi.
        cards = parse_cards("Dr RA GA BA")
        self.agent._hand = cards
        self.pub._played_cards = parse_cards("G9 S8 R8 B8 G6 S6 G5 B5 S5 Ma")
        self.pub._number_of_cards = [4, 14, 14, 14]
        action_space =  [(parse_cards("GA BA"), (1, 1, 14)), (parse_cards("RA BA"), (1, 1, 14))]
        self.assertEqual(action_space[0], self.agent.combination(action_space))

    def test_combination_more_combis(self):
        # Wir beste Partition hat mehrere spielbare Kombis.
        cards = parse_cards("RA GA GK BK")
        self.agent._hand = cards
        self.pub._played_cards = parse_cards("Dr G9 S8 R8 B8 G6 S6 G5 B5 S5")
        self.pub._number_of_cards = [4, 14, 14, 14]
        action_space = [(parse_cards("RA GA"), (2, 2, 14)), (parse_cards("GK BK"), (2, 2, 13))]
        self.assertEqual(action_space[1], self.agent.combination(action_space))

    def test_combination_bomb(self):
        # Wir haben eine Bombe
        cards = parse_cards("Dr RA GA BA SA")
        self.agent._hand = cards
        self.pub._played_cards = parse_cards("G9 S8 R8 B8 G6 S6 G5 B5 S5")
        self.pub._number_of_cards = [5, 14, 14, 14]
        action_space = [(parse_cards("RA GA BA SA"), (7, 4, 14)), ([CARD_DRA], FIGURE_DRA)]
        self.assertEqual(action_space[0], self.agent.combination(action_space))

        # Wie eben, aber der Partner hat Tichu gesagt. Wir schmeißen nicht die Bombe, sondern eine ander Kombi
        self.pub._announcements = [0, 0, 1, 0]
        self.assertEqual(action_space[1], self.agent.combination(action_space))

        # Wie eben, aber wir könnten auch passen, was wir auch tun.
        action_space = [([], FIGURE_PASS), (parse_cards("RA GA BA SA"), (7, 4, 14))]
        self.assertEqual(action_space[0], self.agent.combination(action_space))
        self.pub._announcements = [0, 0, 0, 0]

    def test_wish(self):
        cards = parse_cards("Dr BA GA RD G9 S8 R8 B8 G6 S6 G5 B5 S5 Ma")
        self.pub._mixed_deck = cards + other_cards(cards)
        cards = self.pub.deal_out(0, 8)
        self.priv.take_cards(cards)
        self.assertEqual([0, 0, 0, 0], self.pub.announcements)
        cards = self.pub.deal_out(0, 14)
        self.priv.take_cards(cards)
        self.agent._schupfed = parse_cards("G9 G6 S6")
        self.agent._hand = parse_cards("BA GA RD S8 R8 B8 G7 S7 G5 B5 S5 G4")
        self.pub._played_cards = parse_cards("S4 R6 R7 Dr Ma")
        self.pub._number_of_cards = [12, 13, 13, 13]
        self.assertEqual(9, self.agent.wish())
        # Straße wurde gespielt
        self.pub.reset()
        cards = parse_cards("Dr BA GA RD G9 S8 R8 B7 G6 S5 G4 B3 S2 Ma")
        self.pub._mixed_deck = cards + other_cards(cards)
        cards = self.pub.deal_out(0, 8)
        self.priv.take_cards(cards)
        self.assertEqual([0, 0, 0, 0], self.pub.announcements)
        cards = self.pub.deal_out(0, 14)
        self.priv.take_cards(cards)
        self.agent._schupfed = parse_cards("G9 RD S8")
        self.agent._hand = parse_cards("Dr BA GA RK SD R8 B7 G6 S5 G4 B3 S2 R2 Ma")
        self.pub._trick_figure = (STREET, 8, 8)
        self.pub._trick_vlaue = 5
        self.pub._trick_player_index = 0
        self.pub._played_cards = parse_cards("R8 B7 G6 S5 G4 B3 S2 Ma")
        self.pub._number_of_cards = [8, 14, 14, 14]
        self.assertEqual(13, self.agent.wish())

    def test_gift(self):
        cards = parse_cards("Dr BA GA RD G9 S8 R8 B8 G6 S6 G5 B5 S5 Ma")
        self.pub._mixed_deck = cards + other_cards(cards)
        cards = self.pub.deal_out(0, 8)
        self.priv.take_cards(cards)
        self.assertEqual([0, 0, 0, 0], self.pub.announcements)
        cards = self.pub.deal_out(0, 14)
        self.priv.take_cards(cards)
        self.agent._schupfed = parse_cards("G9 G6 S6")
        self.agent._hand = parse_cards("BA GA RD S8 R8 B8 G7 S7 G5 B5 S5 G4")
        self.pub._played_cards = parse_cards("S4 R6 R7 Dr")
        self.pub._number_of_cards = [12, 12, 14, 14]
        self.assertEqual(3, self.agent.gift())
        self.pub._number_of_cards = [12, 14, 14, 12]
        self.assertEqual(1, self.agent.gift())
        self.pub._number_of_cards = [13, 13, 13, 13]
        self.assertEqual(3, self.agent.gift())


if __name__ == "__main__":
    unittest.main()
