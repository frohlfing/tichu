from src.players.player import Player


class Agent(Player):
    # Basisklasse für eine KI

    def __init__(self, seed=None):
        super().__init__(seed)
