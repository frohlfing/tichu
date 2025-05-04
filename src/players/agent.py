"""
Definiert die Agent-Klasse, die einen KI-gesteuerten Spieler repräsentiert.
"""

import asyncio
import random  # Standard-Random für Namensgenerierung ausreichend
#import uuid
from src.common.logger import logger
from src.players.player import Player
from src.private_state2 import PrivateState
from src.public_state2 import PublicState
from typing import Optional


class Agent(Player):
    """
    Repräsentiert einen KI-gesteuerten Spieler.

    Erbt von der Basisklasse `Player` und implementiert die Logik für automatische Spielentscheidungen (`get_action`)
    und das Empfangen von Benachrichtigungen (`notify`).
    """

    def __init__(self, player_name: Optional[str] = None, ai_level: int = 1, player_id: Optional[str] = None):
        """
        Initialisiert einen neuen Agenten.

        :param player_name: Optionaler Name für den Agenten. Wenn None, wird einer generiert.
        :param ai_level: Das Level der KI (aktuell nur zur Info).
        :param player_id: Optionale, feste ID für den Agenten. Wenn None, wird eine UUID generiert.
        """
        # Generiere einen Namen, falls keiner angegeben ist.
        # TODO: Eindeutigen/lustigeren Namen generieren. Ideen:
        # - Bibliotheken wie 'names' oder 'faker' verwenden.
        # - Vordefinierte Listen mit Adjektiven/Nomen kombinieren.
        # - Einfacher Zähler pro Tisch? (`f"KI-{slot_index+1}"`)
        if player_name is None:
            # Einfache Variante mit Zufallszahl
            name = f"KI_{ai_level}-{random.randint(100, 999)}"
        else:
            name = player_name

        # Rufe den Konstruktor der Basisklasse auf.
        super().__init__(name, player_id=player_id)
        #: Das Level oder die Komplexität der KI.
        self.ai_level = ai_level
        logger.debug(f"Agent '{self.player_name}' (ID: {self.player_id}, Level: {self.ai_level}) erstellt.")

    async def notify(self, message_type: str, data: dict):
        """
        Empfängt Benachrichtigungen vom Server (z.B. Zustands-Updates).

        Standardmäßig loggt der Agent die Nachrichten nur auf Debug-Level.
        Dies könnte erweitert werden, um interne Zustände der KI zu aktualisieren.

        :param message_type: Der Typ der Nachricht (z.B. "public_state_update").
        :param data: Die Nutzdaten der Nachricht als Dictionary.
        """
        # Loggen auf Debug-Level, um Logs nicht zu überfluten.
        logger.debug(f"Agent {self.player_name} hat Nachricht empfangen: Typ='{message_type}', Daten='{data}'")
        # Hier könnte die KI die Informationen verarbeiten, z.B. um gegnerische Karten zu lernen.
        pass

    async def get_action(self, public_state: PublicState, private_state: PrivateState) -> Optional[dict]:
        """
        Trifft die nächste Spielentscheidung basierend auf dem aktuellen Zustand.

        Diese Methode wird von der `GameEngine` aufgerufen, wenn der Agent am Zug ist.
        Sie muss eine gültige Aktion im erwarteten Format zurückgeben.

        **Aktuelle Implementierung ist ein einfacher Platzhalter!**

        :param public_state: Der aktuelle öffentliche Spielzustand.
        :param private_state: Der private Zustand dieses Agenten (inkl. Handkarten).
        :return: Ein Dictionary, das die Aktion beschreibt (z.B. {'action': 'pass_turn'}), oder None, wenn keine Aktion möglich ist (sollte nicht vorkommen).
        """
        logger.info(f"Agent {self.player_name} (Level {self.ai_level}) ist am Zug und überlegt...")
        # Simuliert Denkzeit für die KI.
        await asyncio.sleep(0.5) # TODO: Denkzeit anpassen/entfernen?

        # --- PLATZHALTER-LOGIK ---
        # TODO: Diese Logik durch eine echte KI-Strategie ersetzen!

        # 1. Tichu ansagen? (Sehr einfache Bedingung)
        if private_state.can_announce_tichu: # Annahme: private_state hat dieses Flag
             logger.info(f"Agent {self.player_name} sagt (kleines) Tichu an.")
             return {"action": "announce_tichu", "type": "small"}

        # 2. Aktion wählen: Spielen oder passen?
        # Gibt es überhaupt Karten auf der Hand?
        if not private_state.hand_cards:
            logger.warning(f"Agent {self.player_name} ist am Zug, hat aber keine Karten mehr? Passe.")
            # Sollte idealerweise nicht passieren, wenn die Rundelogik stimmt.
            return {"action": "pass_turn"}

        # Ist der Stich leer (erster Spieler im Stich)?
        if not public_state.last_played_combination: # Annahme: public_state hat dieses Feld
            # Spiele die erste Karte auf der Hand (einfachste mögliche Aktion).
            card_to_play = private_state.hand_cards[0]
            logger.info(f"Agent {self.player_name} eröffnet Stich mit: {card_to_play}")
            # TODO: Hier müsste die Kombination validiert/korrekt formatiert werden!
            return {"action": "play_cards", "cards": [card_to_play]}
        else:
            # Der Stich ist nicht leer. Einfachste Aktion: Passen.
            # TODO: Implementiere Logik zum Bedienen (Finden einer höheren Kombination).
            logger.info(f"Agent {self.player_name} passt.")
            return {"action": "pass_turn"}

        # --- ENDE PLATZHALTER-LOGIK ---