from typing import List
import pytest
from unittest.mock import AsyncMock
from src.players.agent import Agent
from src.game_engine import GameEngine
from src.players.peer import Peer
from src.players.random_agent import RandomAgent
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
        player_mock.cleanup = AsyncMock(name=f'cleanup_mock_{i}')
        player_mock.reset_round = AsyncMock(name=f'reset_round_mock_{i}')
        player_mock.announce = AsyncMock(name=f'announce_mock_{i}')
        player_mock.schupf = AsyncMock(name=f'schupf_mock_{i}')
        player_mock.play = AsyncMock(name=f'play_mock_{i}')
        player_mock.wish = AsyncMock(name=f'wish_mock_{i}')
        player_mock.give_dragon_away = AsyncMock(name=f'gift_mock_{i}')
        player_mock.notify = AsyncMock(name=f'notify_mock_{i}')
        player_mock.error = AsyncMock(name=f'error_mock_{i}')
        # Setze Standard-Attribute für den Mock
        player_mock.name = f"P{i}"
        player_mock.session_id = f"session_{i}"
        player_mock.pub = pub
        player_mock.priv = PrivateState(player_index=i)
        players.append(player_mock)
    return players

def test_init_with_default_agents(mock_agents, mocker):
    """
    Testet, dass bei der Initialisierung mit `default_agents` Kopien der Listen
    erstellt werden, aber die Agent-Objekte selbst Referenzen bleiben.
    """
    original_agents_list = list(mock_agents)
    engine = GameEngine(table_name="TestTable", default_agents=original_agents_list)
    assert engine.table_name == "TestTable"
    assert len(engine.players) == 4

    # Prüfe, ob _default_agents eine *Kopie der Liste* ist
    assert engine._default_agents is not original_agents_list
    assert engine._default_agents == original_agents_list

    # Prüfe, ob _players eine *Kopie der Liste* ist
    assert engine._players is not engine._default_agents
    assert engine._players == engine._default_agents

    # Prüfe, ob die *Elemente* in den Listen dieselben Objekte sind
    for i in range(4):
        assert engine._players[i] is original_agents_list[i]
        assert engine._default_agents[i] is original_agents_list[i]
        assert engine._players[i].pub is engine.public_state
        assert engine._players[i].priv is engine.private_states[i]


async def test_swap_players(mock_agents, mocker):
    """
    Testet das Vertauschen der Position von zwei Spielern.
    """
    original_agents_list = list(mock_agents)
    engine = GameEngine(table_name="TestTable", default_agents=original_agents_list)
    assert engine.table_name == "TestTable"
    assert len(engine.players) == 4

    # Prüfe, ob die Anordnung der Spieler korrekt ist
    for i in range(4):
        assert engine._players[i].name == f"P{i}"
        assert engine._players[i].priv.player_index == i
        assert engine._default_agents[i].name == f"P{i}"
        assert engine._default_agents[i].priv.player_index == i
        assert engine.public_state.player_names[i] == f"P{i}"

    # Vertausche zwei Spieler in der _players-Liste
    mocker.patch.object(engine, '_broadcast', new_callable=AsyncMock)
    ok = await engine.swap_players(0, 1)
    assert ok is True

    # Prüfe die neuen Positionen der Spieler
    assert engine._players[0] is not original_agents_list[1]  # Spieler 0 ist jetzt eine Kopie
    assert engine._players[0].pub is engine.public_state
    assert engine._players[0].priv is engine.private_states[0]
    assert engine._players[0].name == f"P1"
    assert engine._players[0].priv.player_index == 0

    assert engine._players[1] is not original_agents_list[0]  # Spieler 1 ist jetzt eine Kopie
    assert engine._players[1].pub is engine.public_state
    assert engine._players[1].priv is engine.private_states[1]
    assert engine._players[1].name == f"P0"
    assert engine._players[1].priv.player_index == 1

    # Spieler 2 und 3 sind weiterhin eine Referenz
    assert engine._players[2] is original_agents_list[2]
    assert engine._players[3] is original_agents_list[3]

    # Die _default_agents-Liste sollte UNVERÄNDERT bleiben, da sie eine separate Liste ist.
    for i in range(4):
        assert engine._default_agents[i] is original_agents_list[i]
        assert engine._default_agents[i].name == f"P{i}"
        assert engine._default_agents[i].priv.player_index == i

    # Die Namen in PublicState sind angepasst
    assert engine.public_state.player_names == ["P1", "P0", "P2", "P3"]


def test_init_no_agents_creates_random_agents():
    """Testet, ob RandomAgents erstellt werden, wenn keine Agents übergeben werden."""
    engine = GameEngine(table_name="TestTable", default_agents=None)
    assert len(engine._default_agents) == 4
    assert all(isinstance(agent, RandomAgent) for agent in engine._default_agents)

def test_init_invalid_agent_list_raises_error(mock_agents):
    """Testet, ob eine falsche Anzahl oder ein falscher Typ von Agent einen Fehler auslöst."""
    # Zu wenige Agenten
    with pytest.raises(ValueError, match="`default_agents` muss genau 4 Agenten auflisten."):
        GameEngine(table_name="TestTable", default_agents=mock_agents[:3])

    # Falscher Objekttyp in der Liste
    invalid_list = list(mock_agents)
    # noinspection PyTypeChecker
    invalid_list[2] = "not_an_agent"
    with pytest.raises(ValueError, match="`default_agents` muss genau 4 Agenten auflisten."):
        GameEngine(table_name="TestTable", default_agents=invalid_list)


@pytest.mark.asyncio
async def test_join_client_finds_first_available_spot(mock_agents, mocker):
    """Testet, dass der Client den ersten freien (von KI besetzten) Platz bekommt."""
    #engine = GameEngine(table_name="TestTable", default_agents=None)
    #engine._players = [mocker.create_autospec(Agent if i == 2 else Peer, instance=True, name=f"OtherPlayer_{i}") for i in range(4)]

    engine = GameEngine(table_name="TestTable", default_agents=mock_agents)
    # Ersetze die ersten beiden Spieler durch deb Peer
    engine._players[0] = mocker.create_autospec(Peer, instance=True, name=f"OtherPeer_0")
    engine._players[1] = mocker.create_autospec(Peer, instance=True, name=f"OtherPeer_0")
    mocker.patch.object(engine, '_broadcast', new_callable=AsyncMock)

    # Der nächste freie Platz sollte Index 2 sein
    peer_mock = mocker.create_autospec(Peer, instance=True, name="MockPeer")
    peer_mock.name = "HumanPlayer"
    success = await engine.join_client(peer_mock)

    assert success is True
    assert engine._players[2] is peer_mock  # Sollte an Index 2 sitzen

    assert engine._players[2].priv.player_index == 2
    assert engine._players[2].pub.player_names[2] == peer_mock.name

    # Prüfe, ob der Host-Index korrekt gesetzt wird
    assert engine._public_state.host_index == 2  # Da peer1 und peer2 den Host-Index nicht gesetzt haben


@pytest.mark.asyncio
async def test_join_client_no_spot_available(mock_agents, mocker):
    """Testet, dass join_client False zurückgibt, wenn alle Plätze von Peers besetzt sind."""
    # Erstelle die Engine ohne default_agents und setze die Spieler manuell
    engine = GameEngine(table_name="TestTable", default_agents=None)
    engine._players = [mocker.create_autospec(Peer, instance=True, name=f"OtherPeer_{i}") for i in range(4)]

    peer_mock = mocker.create_autospec(Peer, instance=True, name="MockPeer")
    peer_mock.name = "HumanPlayer"
    success = await engine.join_client(peer_mock)

    assert success is False

# -------------------------------------------------------
# Alte Tests (ursprünglich mit unittest geschrieben)
# -------------------------------------------------------
