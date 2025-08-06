from src.players.agent import Agent
from src.players.player import Player

def test_agent_inheritance():
    """Stellt sicher, dass Agent von Player erbt."""
    assert issubclass(Agent, Player)

def test_agent_init_generates_name():
    """Testet, ob Agent einen Namen generiert, wenn keiner angegeben wird."""
    agent = Agent() # Kein Name übergeben
    assert agent.name.startswith("Agent_") # Sollte mit Klassennamen beginnen
    assert len(agent.name) > len("Agent_") # Sollte einen UUID-Teil haben
    # class_name sollte weiterhin den spezifischen Klassennamen liefern (wenn nicht überschrieben)
    # Da Agent selbst keine __init__ hat, die class_name setzt, wird es von Player geerbt.
    # Wenn ich eine Subklasse hätte (z.B. MySpecificAgent(Agent)), würde deren Name kommen.
    assert agent.class_name == "Agent"

def test_agent_init_with_name():
    """Testet, ob Agent einen übergebenen Namen verwendet."""
    agent = Agent(name="MyAgent")
    assert agent.name == "MyAgent"
