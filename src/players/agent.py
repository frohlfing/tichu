import asyncio
import uuid
from src.common.logger import logger
from src.players.player import Player
from src.private_state2 import PrivateState
from src.public_state2 import PublicState
from typing import Optional


class Agent(Player):
    """Basisklasse für einen KI-gesteuerten Spieler."""

    def __init__(self, player_name: Optional[str] = None, ai_level: int = 1, player_id: Optional[str] = None):
        # Generiere einen Namen, falls keiner angegeben ist
        name = player_name or f"Agent_{ai_level}_{str(uuid.uuid4())[:4]}"  # todo eindeutigen lustigen Namen generieren
        super().__init__(name, player_id=player_id)
        self.ai_level = ai_level

    # ------------------------------------------------------
    # Notify
    # ------------------------------------------------------

    async def notify(self, message_type: str, data: dict):
        """KIs empfangen Nachrichten, tun aber meist nichts damit (oder loggen sie)."""
        logger.debug(f"Agent {self.player_name} received message: {message_type}, {data}")
        pass # Oder interne Logik ausführen

    # ------------------------------------------------------
    # Entscheidungen
    # ------------------------------------------------------

    async def get_action(self, public_state: PublicState, private_state: PrivateState) -> Optional[dict]:
        """
        Hier wird die KI ihre Entscheidung treffen.
        Gibt die Aktion als Dictionary zurück oder None, wenn keine Aktion möglich ist.
        Muss von der GameEngine aufgerufen werden, wenn die KI am Zug ist.
        """
        logger.info(f"Agent {self.player_name} is thinking...")
        await asyncio.sleep(0.5) # Simuliert Denkzeit
        # --- ECHTE KI LOGIK HIER ---
        # Beispiel: Wenn Tichu möglich ist, ansagen
        if private_state.can_announce_tichu:
             return {"action": "announce_tichu", "type": "small"}

        # Beispiel: Einfachste Aktion: Passen (wenn möglich) oder niedrigste Karte spielen
        # Diese Logik ist nur ein Platzhalter!
        if not public_state.last_played_combination and private_state.hand_cards: # Erster Zug im Stich
             return {"action": "play_cards", "cards": [private_state.hand_cards[0]]}
        else: # Passen (oder andere Karte spielen)
             return {"action": "pass_turn"}
