from typing import List
import pytest
from unittest.mock import AsyncMock
from src.players.agent import Agent
from src.game_engine import GameEngine
from src.public_state import PublicState
from src.private_state import PrivateState

@pytest.fixture
def mock_agents(mocker) -> List[AsyncMock]:
    """Erstellt eine Liste von 4 Mock-Objekten, die sich wie Player verhalten."""
    players = []
    pub = PublicState(table_name="TestEngineTable", player_names=["P0", "P1", "P2", "P3"])
    for i in range(4):
        # Erstelle einen Mock, der vorgibt, ein Player-Objekt zu sein
        player_mock = mocker.create_autospec(Agent, instance=True)
        player_mock.__class__ = Agent
        # Wichtig: Da Player Methoden wie play async sind, ersetzen wir sie explizit durch AsyncMocks,
        # NACHDEM create_autospec die Signatur erstellt hat.
        player_mock.schupf = AsyncMock(name=f'schupf_mock_{i}')
        player_mock.announce_grand_tichu = AsyncMock(name=f'announce_mock_{i}')
        player_mock.play = AsyncMock(name=f'play_mock_{i}') # play statt combination
        player_mock.wish = AsyncMock(name=f'wish_mock_{i}')
        player_mock.give_dragon_away = AsyncMock(name=f'gift_mock_{i}') # Umbenannt
        player_mock.cleanup = AsyncMock(name=f'cleanup_mock_{i}') # Auch cleanup mocken

        # Setze Standard-Attribute für den Mock
        player_mock.name = f"P{i}"
        player_mock.pub = pub
        player_mock.priv = PrivateState(player_index=i)
        player_mock.session_id = f"session_{i}"

        players.append(player_mock)
    return players

@pytest.fixture
def game_engine(mock_agents) -> GameEngine:
    """Erstellt eine GameEngine-Instanz, die mit den Mock-Spielern initialisiert ist."""
    # Seed setzen (für reproduzierbare Zufälligkeit in Tests, falls nötig)
    return GameEngine(table_name="TestEngineTable", default_agents=mock_agents, seed=12345)

@pytest.fixture
def initial_public_state() -> PublicState:
    """Erstellt einen frischen PublicState für Tests."""
    return PublicState(
        table_name="TestEngineTable",
        player_names=["P0", "P1", "P2", "P3"],
        count_hand_cards=[14, 14, 14, 14],
    )

@pytest.fixture
def initial_private_states() -> List[PrivateState]:
    """Erstellt 4 frische PrivateStates für Tests."""
    return [PrivateState(player_index=i) for i in range(4)]

def test_game_engine_initialization(game_engine, mock_agents):
    """Testet, ob die Engine korrekt mit Mocks initialisiert wird."""
    assert game_engine.table_name == "TestEngineTable"
    assert len(game_engine.players) == 4
    # Prüfen, ob die übergebenen Mocks auch wirklich die Spieler in der Engine sind
    assert game_engine.players[0] is mock_agents[0]
    assert game_engine.players[1] is mock_agents[1]
    assert game_engine.players[2] is mock_agents[2]
    assert game_engine.players[3] is mock_agents[3]

# -------------------------------------------------------
# Alte Tests (ursprünglich mit unittest geschrieben)
# -------------------------------------------------------
