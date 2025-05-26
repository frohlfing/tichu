import unittest
from src.players.agent import Agent
from src.players.player import Player
from src.private_state import PrivateState
from src.game_engine import GameEngine


class TestGameEngine(unittest.TestCase):
    def setUp(self):
        """Initialisiert die GameEngine für jeden Test."""
        default_agents = [
            Agent(name="Agent_1"),
            Agent(name="Agent_2"),
            Agent(name="Agent_3"),
            Agent(name="Agent_4")
        ]
        self.engine = GameEngine(table_name="TestTable", default_agents=default_agents)

    def test_name_mutability(self):
        """Testet, ob das Ändern des Namens in `_default_agents[0]` auch `_players[0]` beeinflusst."""
        # Name in _default_agents ändern
        self.engine._default_agents[0]._name = "NewAgentName"
        
        # Überprüfen, ob Name in _players auch geändert wurde
        self.assertEqual(self.engine._players[0].name, "NewAgentName", 
                         "Das Ändern des Namens in `_default_agents[0]` sollte `_players[0]` beeinflussen, da sie dieselbe Referenz teilen.")

    def test_private_state_to_default_agents_mutability(self):
        """Testet, ob das Ändern von `_private_states[0]` auch `self._default_agents[0].priv` beeinflusst."""
        # Wert in _private_states[0] ändern
        self.engine._private_states[0].hand_cards = [(2,3)]

        # Überprüfen, ob Änderung in _default_agents[0].priv sichtbar ist
        self.assertEqual(self.engine._default_agents[0].priv.hand_cards, [(2,3)],
                         "Das Ändern von `_private_states[0]` sollte `self._default_agents[0].priv` beeinflussen, wenn sie dieselbe Referenz teilen.")

        self.assertEqual(self.engine._players[0].priv.hand_cards, [(2,3)],
                         "Das Ändern von `_private_states[0]` sollte `self._players[0].priv` beeinflussen, da sie dieselbe Referenz teilen.")

    def test_swap_players(self):
        self.assertEqual(self.engine._players[0].priv.player_index, 0)
        self.assertEqual(self.engine._players[1].priv.player_index, 1)
        self.assertEqual(self.engine._players[0].name, "Agent_1")
        self.assertEqual(self.engine._players[1].name, "Agent_2")

        self.assertEqual(self.engine._default_agents[0].priv.player_index, 0)
        self.assertEqual(self.engine._default_agents[1].priv.player_index, 1)
        self.assertEqual(self.engine._default_agents[0].name, "Agent_1")
        self.assertEqual(self.engine._default_agents[1].name, "Agent_2")

        self.engine._players[1], self.engine._players[0] = self.engine._players[0], self.engine._players[1]
        self.engine._players[1].priv, self.engine._players[0].priv = self.engine._players[0].priv, self.engine._players[1].priv

        self.assertEqual(self.engine._players[0].priv.player_index, 0)
        self.assertEqual(self.engine._players[1].priv.player_index, 1)
        self.assertEqual(self.engine._players[0].name, "Agent_2")
        self.assertEqual(self.engine._players[1].name, "Agent_1")

        self.assertEqual(self.engine._default_agents[0].priv.player_index, 0)
        self.assertEqual(self.engine._default_agents[1].priv.player_index, 1)
        self.assertEqual(self.engine._default_agents[0].name, "Agent_2")
        self.assertEqual(self.engine._default_agents[1].name, "Agent_1")

if __name__ == "__main__":
    unittest.main()