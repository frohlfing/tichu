"""
Definiert die abstrakte Basisklasse `Player` für alle Spieler im Tichu-Spiel.
"""

import asyncio
from src.common.logger import logger
from src.lib.cards import Card, Cards
from src.lib.combinations import Combination
from src.private_state import PrivateState
from src.public_state import PublicState
from typing import Optional, Tuple, List
from uuid import uuid4


class Player:
    """
    Die Abstrakte Basisklasse für einen Spieler (Mensch oder KI).

    Definiert die grundlegenden Eigenschaften und Methoden, die jeder Spieler haben muss.

    :ivar player_index: Der Index des Spielers am Tisch (0 bis 3, None == Spieler sitzt noch nicht am Tisch).
    :ivar interrupt_event: Das globale Interrupt-Event.
    """

    def __init__(self, name: str, session_id: Optional[str] = None):
        """
        Initialisiert einen neuen Spieler.

        :param name: Der Name des Spielers. Wird bereinigt (Leerzeichen entfernt). Darf nicht leer sein.
        :param session_id: (Optional) Aktuelle Session des Spielers. Wenn None, wird eine Session generiert.
        :raises ValueError: Wenn der `player_name` leer ist.
        """
        #: Der Name des Spielers.
        name_stripped = name.strip() if name else ""
        if not name_stripped:
            raise ValueError("Spielername darf nicht leer sein.")
        self._name: str = name_stripped
        self._session_id: str = session_id if session_id else str(uuid4())
        self.player_index: Optional[int] = None  # wird von der GameEngine gesetzt  todo in index umbenennen
        self.interrupt_event: Optional[asyncio.Event] = None  # wird von der Engine gesetzt
        logger.debug(f"Player '{self._name}' (Session: {self._session_id}) erstellt.")

    def __repr__(self) -> str:
        """
        Gibt eine repräsentative Zeichenkette für das Player-Objekt zurück.

        :return: String-Repräsentation (z.B. "Agent(name='Alice', session_id='...')").
        """
        return f"{self.__class__.__name__}(name='{self._name}', session_id='{self._session_id}')"

    async def cleanup(self):
        """
        Bereinigt Ressourcen dieser Instanz.
        """
        pass

    def reset_round(self):  # pragma: no cover
        """
        Setzt spielrundenspezifische Werte zurück.
        """
        pass

    # ------------------------------------------------------
    # Entscheidungen
    # ------------------------------------------------------

    async def schupf(self, pub: PublicState, priv: PrivateState) -> Tuple[Card, Card, Card]:
        """
        Fordert den Spieler auf, drei Karten zum Schupfen auszuwählen.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner.
        :raises PlayerInteractionError: Wenn die Aktion fehlschlägt.
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'schupf' implementieren.")

    async def announce(self, pub: PublicState, priv: PrivateState, grand: bool = False) -> bool:
        """
        Fragt den Spieler, ob er Tichu (oder Grand Tichu) ansagen möchte.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :param grand: True, wenn nach Grand Tichu gefragt wird, False für kleines Tichu.
        :return: True, wenn angesagt wird, sonst False.
        :raises PlayerInteractionError: Wenn die Aktion fehlschlägt.
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'announce' implementieren.")

    async def play(self, pub: PublicState, priv: PrivateState, action_space: List[Tuple[Cards, Combination]]) -> Tuple[Cards, Combination]:
        """
        Fordert den Spieler auf, eine gültige Kartenkombination auszuwählen oder zu passen.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :param action_space: Mögliche Kombinationen (inklusive Passen; wenn Passen erlaubt ist, steht Passen an erster Stelle).
        :return: Die ausgewählte Kombination (Karten, (Typ, Länge, Wert)) oder Passen ([], (0,0,0)).
        :raises PlayerInteractionError: Wenn die Aktion fehlschlägt.
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'combination' implementieren.")

    async def wish(self, pub: PublicState, priv: PrivateState) -> int:
        """
        Fragt den Spieler nach einem Kartenwert-Wunsch (nach Ausspielen des Mah Jong).

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Der gewünschte Kartenwert (2-14).
        :raises PlayerInteractionError: Wenn die Aktion fehlschlägt.
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'wish' implementieren.")

    async def give_dragon_away(self, pub: PublicState, priv: PrivateState) -> int:  # todo besseren Namen finden
        """
        Fragt den Spieler, welchem Gegner der mit dem Drachen gewonnene Stich gegeben werden soll.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Der Index (0-3) des Gegners, der den Stich erhält.
        :raises PlayerInteractionError: Wenn die Aktion fehlschlägt.
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'give_dragon_away' implementieren.")

    # ------------------------------------------------------
    # Eigenschaften
    # ------------------------------------------------------

    @property
    def class_name(self) -> str:
        """Gibt den Klassennamen zurück (z.B. 'Client', 'Agent')."""
        return type(self).__name__

    @property
    def name(self) -> str:
        """Der Name des Spielers."""
        return self._name

    @property
    def session_id(self) -> str:
        """Die aktuelle Session-ID des Spielers."""
        return self._session_id

    @property
    def partner_index(self) -> int:
        """Der Index des Partners (0-3)."""
        return (self.player_index + 2) % 4

    @property
    def opponent_right_index(self) -> int:
        """Der Index des rechten Gegners (0-3)."""
        return (self.player_index + 1) % 4

    @property
    def opponent_left_index(self) -> int:
        """Der Index des linken Gegners (0-3)."""
        return (self.player_index + 3) % 4
