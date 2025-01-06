from src.game_engine import GameEngine
from src.player.agent import Agent
from src.player.heuristik_agent import HeuristikAgent
from src.player.player import Player
from src.player.random_agent import RandomAgent


class GameFactory:
    # Erstellt und verwaltet die GameEngine basierend auf der Welt, die vom Spieler angegeben wird.

    def __init__(self):
        # Constructor

        # Game-Engines
        self._engines = {}

    def get_or_create_engine(self, world_name: str, agent_classes: list[type], **kwargs) -> GameEngine:
        # Erzeugt die Engine (falls sie nicht existiert) und gibt eine Referenz darauf zurück
        # agent_classes: 4 Agent-Klassen (oder davon abgeleitet)
        # **kwargs: dict: keyword arguments, dadurch können beliebig viele benannte Argumente übergeben werden
        if world_name not in self._engines:
            assert len(agent_classes) == 4
            assert all(issubclass(agent_class, Agent) for agent_class in agent_classes)
            engine = GameEngine(world_name, lambda engine_: self._create_agents(agent_classes, engine_, **kwargs))
            self._engines[world_name] = engine
        return self._engines[world_name]

    def remove_engine(self, engine: GameEngine) -> None:
        # Engine aus der Liste entfernen
        if engine.world_name in self._engines:
            del self._engines[engine.world_name]

    @staticmethod
    def _create_agents(agent_classes: list[type], engine: GameEngine, **_kwargs) -> list[Agent]:
        # Erzeugt 4 Agenten der gegebenen Klasse und gibt eine Referenz auf die Liste zurück
        # Diese Funktion wird von der Game-Engine während der Erstellung aufgerufen.
        assert len(agent_classes) == 4
        agents = []
        for chair in range(4):
            agent_class = agent_classes[chair]
            # if agent_class == RandomAgent:
            #     agent = RandomAgent(chair, engine)
            # elif agent_class == HeuristikAgent:
            #     agent = HeuristikAgent(chair, engine)
            # else:
            agent = agent_class(chair, engine)
            agents.append(agent)
        return agents
