from unittest.mock import patch

import pytest
from src.public_state import PublicState
from src.private_state import PrivateState
from src.players.random_agent import RandomAgent
from src.players.agent import Agent
from src.lib.cards import parse_cards
from src.lib.combinations import CombinationType, FIGURE_PASS

# === Fixtures (spezifisch für RandomAgent-Tests) ===

@pytest.fixture
def public_state_fixture() -> PublicState:
    """Erstellt einen leeren PublicState für RandomAgent-Tests."""
    return PublicState(table_name="test", player_names=["P0", "P1", "P2", "P3"])

@pytest.fixture
def private_state_fixture() -> PrivateState:
    """
    Erstellt einen PrivateState mit Beispielhand für RandomAgent-Tests.
    Wird von jedem Test neu erstellt, Modifikationen in einem Test beeinflussen
    andere Tests nicht.
    """
    priv = PrivateState(player_index=1) # Spieler 1 als Beispiel
    # Beispielhand mit 14 Karten für Schupf-Test
    priv.hand_cards = parse_cards("S2 B2 G2 R2 S3 B3 G3 R3 S4 B4 G4 R4 S5 B5")
    assert len(priv.hand_cards) == 14
    return priv

@pytest.fixture
def random_agent_seeded(public_state_fixture, private_state_fixture) -> RandomAgent:
    """Erstellt einen RandomAgent mit einem festen Seed für reproduzierbare Tests."""
    agent = RandomAgent(seed=42) # Fester Seed
    agent.pub =public_state_fixture
    agent.priv =private_state_fixture
    return agent # Fester Seed

@pytest.fixture
def random_agent_unseeded(public_state_fixture, private_state_fixture) -> RandomAgent:
    """Erstellt einen normalen RandomAgent ohne festen Seed."""
    agent = RandomAgent() # Fester Seed
    agent.pub =public_state_fixture
    agent.priv =private_state_fixture
    return agent # Fester Seed

# === Testfälle für RandomAgent ===

def test_random_agent_inheritance():
    """Stellt sicher, dass RandomAgent von Agent erbt."""
    assert issubclass(RandomAgent, Agent)

@pytest.mark.asyncio
async def test_random_agent_schupf(random_agent_seeded):
    """Testet RandomAgent.schupf."""
    agent = random_agent_seeded
    original_hand_copy = list(agent.priv.hand_cards)

    # Rufe schupf auf
    schupfed_cards = await agent.schupf()

    # Prüfungen:
    # 1. Korrekter Typ und Länge?
    assert isinstance(schupfed_cards, tuple)
    assert len(schupfed_cards) == 3
    assert all(isinstance(card, tuple) for card in schupfed_cards)

    # 2. Sind die Karten aus der Originalhand?
    hand_set = set(original_hand_copy)
    schupfed_set = set(schupfed_cards)
    assert schupfed_set.issubset(hand_set)

    # 3. Sind die geschupften Karten einzigartig (keine Duplikate)?
    assert len(schupfed_set) == 3

    # 4. Wurde der PrivateState vom Agenten modifiziert? (Sollte nicht)
    assert agent.priv.hand_cards == original_hand_copy

@pytest.mark.asyncio
async def test_random_agent_announce_grand_tichu(random_agent_unseeded):
    """Testet RandomAgent.announce_grand_tichu (nur Typ und Wertbereich)."""
    agent = random_agent_unseeded
    result = await agent.announce_grand_tichu()
    assert isinstance(result, bool)

@pytest.mark.asyncio
async def test_random_agent_announce_tichu(random_agent_unseeded):
    """Testet RandomAgent.announce_tichu (nur Typ und Wertbereich)."""
    agent = random_agent_unseeded
    result = await agent.announce_tichu()
    assert isinstance(result, bool)

@pytest.mark.asyncio
async def test_random_agent_play(random_agent_seeded):
    """Testet RandomAgent.play."""
    agent = random_agent_seeded # Seed für reproduzierbare Auswahl

    # Erstelle einen Beispiel-Action-Space
    action_space = [
        ([], FIGURE_PASS), # Passen
        (parse_cards("B2 S2 G3 S3"), (CombinationType.STAIR, 4, 3)),
        (parse_cards("B2 S2"), (CombinationType.PAIR, 2, 2)),
        (parse_cards("G3 S3"), (CombinationType.PAIR, 2, 3)),
        (parse_cards("S3"), (CombinationType.SINGLE, 1, 3)),
        (parse_cards("G3"), (CombinationType.SINGLE, 1, 3)),
        (parse_cards("B2"), (CombinationType.SINGLE, 1, 2)),
        (parse_cards("S2"), (CombinationType.SINGLE, 1, 2)),
    ]

    # Setze Beispiel-Handkarten (obwohl Agent sie nicht prüft)
    agent.priv.hand_cards = parse_cards("B2 S2 G3 S3")

    # Rufe play auf
    chosen_action = await agent.play()

    # Prüfungen:
    # 1. Korrekter Typ?
    assert isinstance(chosen_action, tuple)
    assert len(chosen_action) == 2
    assert isinstance(chosen_action[0], list) # Cards
    assert isinstance(chosen_action[1], tuple) # Combination
    assert len(chosen_action[1]) == 3
    assert isinstance(chosen_action[1][0], CombinationType)

    # 2. Wurde eine Aktion aus dem action_space gewählt?
    assert chosen_action in action_space

@pytest.mark.asyncio
@patch("src.players.random_agent.build_action_space")
async def test_random_agent_play_empty_action_space_raises_error(mock_build_action_space, random_agent_seeded):
    """Testet, dass RandomAgent.play bei leerem Action Space einen Fehler wirft."""
    agent = random_agent_seeded
    mock_build_action_space.return_value = []
    # Erwarte einen ValueError, da random.integer(0, 0) oder random.choice([]) fehlschlägt
    with pytest.raises(ValueError):
       await agent.play()

@pytest.mark.asyncio
async def test_random_agent_wish(random_agent_unseeded):
    """Testet RandomAgent.wish."""
    agent = random_agent_unseeded

    wishes = set()
    for _ in range(50): # Mehrere Versuche
        wish_value = await agent.wish()
        assert isinstance(wish_value, int)
        assert 2 <= wish_value <= 14
        wishes.add(wish_value)
    assert len(wishes) > 1 # Sollte verschiedene Werte liefern

@pytest.mark.asyncio
async def test_random_agent_give_dragon_away(random_agent_unseeded):
    """Testet RandomAgent.give_dragon_away."""
    agent = random_agent_unseeded

    possible_opponents = {
        agent.priv.opponent_left_index, # Spieler 0
        agent.priv.opponent_right_index # Spieler 2
    }

    chosen_opponents = set()
    for _ in range(20): # Mehrere Versuche
        recipient_index = await agent.give_dragon_away()
        assert isinstance(recipient_index, int)
        assert recipient_index in possible_opponents
        chosen_opponents.add(recipient_index)
    assert len(chosen_opponents) > 0 # Mindestens einer der Gegner wurde gewählt.

# -------------------------------------------------------
# Alte Tests (ursprünglich mit unittest geschrieben)
# -------------------------------------------------------

@pytest.fixture
def agent(pub, priv):
    agent = RandomAgent("Agent_1", seed=123)
    agent.pub = pub
    agent.priv = priv
    return agent

@pytest.fixture
def pub():
    return PublicState(table_name="Test", player_names=["A", "B", "C", "D"])

@pytest.fixture
def priv():
    priv = PrivateState(player_index=1)
    priv.player_index = 1
    return priv

def test_name(agent):
    assert agent.name == "Agent_1"

async def test_schupf(agent):
    agent.priv._hand_cards = parse_cards("S4 B4 G4 R4 S3 B3 G3 R3 S2 B2 G2 R2 Ma Hu")
    agent.pub._number_of_cards = [14, 14, 14, 14]
    result = await agent.schupf()
    assert result == tuple(parse_cards("S4 B3 G4"))

async def test_announce_grand_tichu(agent):
    result = await agent.announce_grand_tichu()
    assert result in [True, False]

async def test_announce_tichu(agent):
    result = await agent.announce_tichu()
    assert result in [True, False]

@patch("src.players.random_agent.build_action_space")
async def test_play(mock_build_action_space, agent):
    #List[Tuple[Cards, Combination]]
    mock_build_action_space.return_value = [([(CombinationType.SINGLE, 3, 2)], (CombinationType.SINGLE, 1, 3)), ([], (CombinationType.PASS, 0, 0))]
    result = await agent.play()
    assert result in mock_build_action_space.return_value

async def test_wish(agent):
    result = await agent.wish()
    assert result in range(2, 15)

async def test_give_dragon_away(agent):
    result = await agent.give_dragon_away()
    assert result in [agent.priv.opponent_right_index, agent.priv.opponent_left_index]
    assert result in [agent.priv.opponent_right_index, agent.priv.opponent_left_index]
