# tests/test_random_agent.py
"""
Tests für die RandomAgent-Klasse

Zusammenfassung der Tests für RandomAgent:
- Vererbung:
    - Sicherstellung, dass `RandomAgent` korrekt von `Agent` erbt.
- Entscheidungsmethoden (`schupf`, `announce`, `play`, `wish`, `give_dragon_away`):
    - Überprüfung der korrekten Rückgabetypen für jede Methode.
    - Sicherstellung, dass die zurückgegebenen Werte innerhalb der gültigen und erwarteten Grenzen liegen (z.B. 3 Karten für `schupf`, bool für `announce`, Wert 2-14 für `wish`, gültiger Gegner-Index für `give_dragon_away`).
    - Verifizierung, dass die von `play` zurückgegebene Aktion eine aus dem übergebenen `action_space` ist.
- Randfälle:
    - Überprüfung des Verhaltens, wenn `play` mit einem leeren `action_space` aufgerufen wird (sollte `IndexError` auslösen).
- Reproduzierbarkeit (implizit durch `random_agent_seeded`):
    - Verwendung eines Agenten mit festem Seed ermöglicht prinzipiell reproduzierbare Testergebnisse für spezifische Zufallswahlen (obwohl hier primär Typen/Grenzen getestet werden).
"""
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
    return PublicState(player_names=["P0", "P1", "P2", "P3"])

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
def random_agent_seeded() -> RandomAgent:
    """Erstellt einen RandomAgent mit einem festen Seed für reproduzierbare Tests."""
    return RandomAgent(seed=42) # Fester Seed

@pytest.fixture
def random_agent_unseeded() -> RandomAgent:
    """Erstellt einen normalen RandomAgent ohne festen Seed."""
    return RandomAgent()

# === Testfälle für RandomAgent ===

def test_random_agent_inheritance():
    """Stellt sicher, dass RandomAgent von Agent erbt."""
    assert issubclass(RandomAgent, Agent)

@pytest.mark.asyncio
async def test_random_agent_schupf(random_agent_seeded, public_state_fixture, private_state_fixture):
    """Testet RandomAgent.schupf."""
    agent = random_agent_seeded
    agent.index = private_state_fixture.player_index # Agent Index setzen
    original_hand_copy = list(private_state_fixture.hand_cards)

    # Rufe schupf auf
    schupfed_cards = await agent.schupf(public_state_fixture, private_state_fixture)

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
    assert private_state_fixture.hand_cards == original_hand_copy

@pytest.mark.asyncio
@pytest.mark.parametrize("grand", [True, False], ids=["GrandTichu", "SmallTichu"])
async def test_random_agent_announce(random_agent_unseeded, public_state_fixture, private_state_fixture, grand):
    """Testet RandomAgent.announce (nur Typ und Wertbereich)."""
    agent = random_agent_unseeded
    agent.index = private_state_fixture.player_index

    result = await agent.announce(public_state_fixture, private_state_fixture)
    assert isinstance(result, bool)

@pytest.mark.asyncio
async def test_random_agent_play(random_agent_seeded, public_state_fixture, private_state_fixture):
    """Testet RandomAgent.play."""
    agent = random_agent_seeded # Seed für reproduzierbare Auswahl
    agent.index = private_state_fixture.player_index

    # Erstelle einen Beispiel-Action-Space
    combi1_cards = parse_cards("S2 B2")
    combi1_figure = (CombinationType.PAIR, 2, 2)
    combi2_cards = parse_cards("S3")
    combi2_figure = (CombinationType.SINGLE, 1, 3)
    action_space = [
        ([], FIGURE_PASS), # Passen
        (combi1_cards, combi1_figure),
        (combi2_cards, combi2_figure),
    ]

    # Setze Beispiel-Handkarten (obwohl Agent sie nicht prüft)
    private_state_fixture.hand_cards = parse_cards("S2 B2 S3 G3")

    # Rufe play auf
    chosen_action = await agent.play(public_state_fixture, private_state_fixture)

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
async def test_random_agent_play_empty_action_space_raises_error(mock_build_action_space, random_agent_seeded, public_state_fixture, private_state_fixture):
    """Testet, dass RandomAgent.play bei leerem Action Space einen Fehler wirft."""
    agent = random_agent_seeded
    agent.index = private_state_fixture.player_index
    mock_build_action_space.return_value = []
    # Erwarte einen ValueError, da random.integer(0, 0) oder random.choice([]) fehlschlägt
    with pytest.raises(ValueError):
       await agent.play(public_state_fixture, private_state_fixture)

@pytest.mark.asyncio
async def test_random_agent_wish(random_agent_unseeded, public_state_fixture, private_state_fixture):
    """Testet RandomAgent.wish."""
    agent = random_agent_unseeded
    agent.index = private_state_fixture.player_index

    wishes = set()
    for _ in range(50): # Mehrere Versuche
        wish_value = await agent.wish(public_state_fixture, private_state_fixture)
        assert isinstance(wish_value, int)
        assert 2 <= wish_value <= 14
        wishes.add(wish_value)
    assert len(wishes) > 1 # Sollte verschiedene Werte liefern

@pytest.mark.asyncio
async def test_random_agent_give_dragon_away(random_agent_unseeded, public_state_fixture, private_state_fixture):
    """Testet RandomAgent.give_dragon_away."""
    agent = random_agent_unseeded
    agent.index = private_state_fixture.player_index # Spieler 1

    possible_opponents = {
        agent.priv.opponent_left_index, # Spieler 0
        agent.priv.opponent_right_index # Spieler 2
    }

    chosen_opponents = set()
    for _ in range(20): # Mehrere Versuche
        recipient_index = await agent.give_dragon_away(public_state_fixture, private_state_fixture)
        assert isinstance(recipient_index, int)
        assert recipient_index in possible_opponents
        chosen_opponents.add(recipient_index)
    assert len(chosen_opponents) > 0 # Mindestens einer der Gegner wurde gewählt.

# -------------------------------------------------------
# Alte Tests (ursprünglich mit unittest geschrieben)
# -------------------------------------------------------

@pytest.fixture
def agent():
    agent = RandomAgent("Agent_1", seed=123)
    agent.index = 1
    return agent

@pytest.fixture
def pub():
    return PublicState()

@pytest.fixture
def priv():
    priv = PrivateState(player_index=1)
    priv.player_index = 1
    return priv

def test_name(agent):
    assert agent.name == "Agent_1"

async def test_schupf(agent, pub, priv):
    priv._hand_cards = parse_cards("S4 B4 G4 R4 S3 B3 G3 R3 S2 B2 G2 R2 Ma Hu")
    pub._number_of_cards = [14, 14, 14, 14]
    result = await agent.schupf(pub, priv)
    assert result == tuple(parse_cards("S4 B3 G4"))

async def test_announce(agent, pub, priv):
    result = await agent.announce(pub, priv)
    assert result in [True, False]

@patch("src.players.random_agent.build_action_space")
async def test_play(mock_build_action_space, agent, pub, priv):
    #List[Tuple[Cards, Combination]]
    mock_build_action_space.return_value = [([(CombinationType.SINGLE, 3, 2)], (CombinationType.SINGLE, 1, 3)), ([], (CombinationType.PASS, 0, 0))]
    result = await agent.play(pub, priv)
    assert result in mock_build_action_space.return_value

async def test_wish(agent, pub, priv):
    result = await agent.wish(pub, priv)
    assert result in range(2, 15)

async def test_give_dragon_away(agent, pub, priv):
    result = await agent.give_dragon_away(pub, priv)
    assert result in [agent.priv.opponent_right_index, agent.priv.opponent_left_index]
    assert result in [priv.priv.opponent_right_index, priv.priv.opponent_left_index]
