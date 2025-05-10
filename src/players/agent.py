"""
Definiert die Agent-Klasse, die einen KI-gesteuerten Spieler repräsentiert.
"""

from src.players.player import Player
from typing import Optional
from uuid import uuid4

class Agent(Player):
    """
    Die Abstrakte Basisklasse für einen KI-gesteuerten Spieler.

    Erbt von der Basisklasse `Player`.
    """

    def __init__(self, name: Optional[str] = None, session: Optional[str] = None):
        """
        Initialisiert einen neuen Agenten.

        :param name: (Optional) Name für den Agenten. Wenn None, wird einer generiert.
        :param session: (Optional) Aktuelle Session des Agenten. Wenn None, wird eine Session generiert.
        """
        # Generiere einen Namen, falls keiner angegeben ist.
        if name is None:
            name = f"{self.class_name}_{uuid4().hex[:8]}"  # Beispiel: "Agent_1a2b3c4d"

        # Rufe den Konstruktor der Basisklasse auf.
        super().__init__(name, session=session)
