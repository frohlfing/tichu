import uuid
from src.private_state2 import PrivateState
from src.public_state2 import PublicState
from typing import Optional


class Player:
    # Basisklasse für einen Spieler

    """Basisklasse für alle Spieler (Menschen und KIs)."""
    def __init__(self, player_name: str, player_id: Optional[str] = None):
        self.player_name: str = player_name  # todo trimmen, und sicherstellen, dass Name nicht leer ist

        # Eindeutige ID, wichtig für Reconnects
        self.player_id: str = player_id or str(uuid.uuid4())

        # Wird gesetzt, wenn der Spieler einem Spiel beitritt
        self.player_index: Optional[int] = None # Position am Tisch (0-3)

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.player_name}', id='{self.player_id}')"

    # todo von Gemini generieren lassen
    def reset_round(self):  # pragma: no cover
        """Werte zurücksetzen für eine neue Runde"""
        pass  # todo NotImplementedError auslösen?

    # ------------------------------------------------------
    # Notify
    # ------------------------------------------------------

    async def notify(self, message_type: str, data: dict):
        """
        Sendet eine Nachricht (Spielstatus, Fehler etc.) an den Spieler.
        Muss von Unterklassen implementiert werden.
        """
        raise NotImplementedError

    # ------------------------------------------------------
    # Entscheidungen
    # ------------------------------------------------------

    # todo überlegen, ob welche Variante besser ist:
    #  a) get_action: Player muss wissen, was zu tun ist und entscheidet
    #  b) schupf(), announce(), ...: die Game-Engine fragt explizit

    # Variante a) Player muss wissen, was zu tun ist und entscheidet

    async def get_action(self, public_state: PublicState, private_state: PrivateState) -> Optional[dict]:
        """
        Hier wird der Spieler seine Entscheidung treffen.
        Gibt die Aktion als Dictionary zurück oder None, wenn keine Aktion möglich ist.
        Muss von der GameEngine aufgerufen werden, wenn die KI am Zug ist.
        Muss von Unterklassen implementiert werden.
        """
        pass  # todo NotImplementedError auslösen?

    # Variante b) die Game-Engine fragt explizit

    # Welche Karten an die Mitspieler abgeben?
    # return: Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner
    def schupf(self, pub: PublicState, priv: PrivateState) -> list[tuple]:  # pragma: no cover
        pass

    # Tichu ansagen?
    def announce(self, pub: PublicState, priv: PrivateState, grand: bool = False) -> bool:  # pragma: no cover
        pass

    # Welche Kombination soll gespielt werden?
    # action_space: Mögliche Kombinationen (inklusiv Passen)
    # return: Ausgewählte Kombination (Karten, (Typ, Länge, Wert))
    def combination(self, pub: PublicState, priv: PrivateState, action_space: list[tuple]) -> tuple:  # pragma: no cover
        pass

    # Welcher Kartenwert wird gewünscht?
    # return: Wert zw. 2 und 14
    def wish(self, pub: PublicState, priv: PrivateState) -> int:  # pragma: no cover
        pass

    # Welcher Gegner soll den Drachen bekommen?
    # return: Nummer des Gegners
    def gift(self, pub: PublicState, priv: PrivateState) -> int:  # pragma: no cover
        pass

    # ------------------------------------------------------
    # Eigenschaften
    # ------------------------------------------------------

    @property
    def name(self) -> str:
        return type(self).__name__
