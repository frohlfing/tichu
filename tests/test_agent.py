# tests/test_agent.py
"""
Tests für die abstrakte Basisklasse Agent.

Zusammenfassung der Tests für Agent:
- Vererbung:
    - Sicherstellung, dass die `Agent`-Klasse korrekt von `Player` erbt.
- Initialisierung:
    - Überprüfung, dass automatisch ein Name generiert wird, falls bei der Instanziierung keiner angegeben wird (Format: "Agent_<uuid>").
    - Sicherstellung, dass ein explizit übergebener Name korrekt verwendet wird.
- Klasse:
    - Überprüfung des `class_name` Properties.
"""

# Zu testende Klasse
from src.players.agent import Agent
from src.players.player import Player # Importiere Player, um Vererbung zu prüfen

# === Testfälle für Agent (Basisklasse) ===

def test_agent_inheritance():
    """Stellt sicher, dass Agent von Player erbt."""
    assert issubclass(Agent, Player)

def test_agent_init_generates_name():
    """Testet, ob Agent einen Namen generiert, wenn keiner angegeben wird."""
    agent = Agent() # Kein Name übergeben
    assert agent.name.startswith("Agent_") # Sollte mit Klassenname beginnen
    assert len(agent.name) > len("Agent_") # Sollte einen UUID-Teil haben
    # class_name sollte weiterhin den spezifischen Klassennamen liefern (wenn nicht überschrieben)
    # Da Agent selbst keine __init__ hat, die class_name setzt, wird es von Player geerbt.
    # Wenn wir eine Subklasse hätten (z.B. MySpecificAgent(Agent)), würde deren Name kommen.
    assert agent.class_name == "Agent"

def test_agent_init_with_name():
    """Testet, ob Agent einen übergebenen Namen verwendet."""
    agent = Agent(name="MyAgent")
    assert agent.name == "MyAgent"

# Agent ist selbst eine abstrakte Klasse (da sie die Methoden von Player nicht implementiert).
# Das Testen der abstrakten Methoden von Player erfolgt in test_player.py oder
# besser noch in den *konkreten* Agent-Implementierungen (wie RandomAgent).
# Wir brauchen hier keinen separaten Test dafür.