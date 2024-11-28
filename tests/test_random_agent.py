import unittest
from src.lib.cards import *
from src.players.random_agent import RandomAgent
from src.private_state import PrivateState
from src.public_state import PublicState


class TestRandomAgent(unittest.TestCase):
    def setUp(self):
        self.agent = RandomAgent(seed=123)
        self.pub = PublicState(seed=123)
        self.priv = PrivateState(0)

    def test_name(self):
        self.assertEqual(self.agent.name, "RandomAgent")

    def test_schupf(self):
        self.priv._hand = parse_cards("S4 B4 G4 R4 S3 B3 G3 R3 S2 B2 G2 R2 Ma Hu")
        self.pub._number_of_cards = [14, 14, 14, 14]
        result = self.agent.schupf(self.pub, self.priv)
        self.assertEqual(result, parse_cards("Hu G4 R4"))

    def test_announce(self):
        result = self.agent.announce(self.pub, self.priv)
        self.assertIn(result, [True, False])

    def test_combination(self):
        action_space = [(list(range(5)), ('type', 5, 10)), ([], ('pass', 0, 0))]
        result = self.agent.combination(self.pub, self.priv, action_space)
        self.assertIn(result, action_space)

    def test_wish(self):
        result = self.agent.wish(self.pub, self.priv)
        self.assertIn(result, range(2, 15))

    def test_gift(self):
        result = self.agent.gift(self.pub, self.priv)
        self.assertIn(result, [self.priv.opponent_right, self.priv.opponent_left])


if __name__ == '__main__':
    unittest.main()
