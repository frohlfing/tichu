"""
Definiert die abstrakte Basisklasse `Player` für alle Spieler im Tichu-Spiel.
"""

import uuid
from src.private_state2 import PrivateState
from src.public_state2 import PublicState
from typing import Optional


class Player:
    """
    Abstrakte Basisklasse für einen Spieler (Mensch oder KI).

    Definiert die grundlegenden Eigenschaften und Methoden, die jeder Spieler haben muss.

    :ivar player_index: Der Index des Spielers am Tisch (0-3) oder None. Dieser Wert wird von der GameEngine gesetzt.
    """

    def __init__(self, player_name: str, player_id: Optional[str] = None):
        """
        Initialisiert einen neuen Spieler.

        :param player_name: Der Name des Spielers. Wird bereinigt (Leerzeichen entfernt). Darf nicht leer sein.
        :param player_id: Eine optionale, vorgegebene Spieler-ID. Wenn None, wird eine neue UUID generiert.
        :raises ValueError: Wenn der `player_name` leer ist.
        """
        #: Der Name des Spielers.
        name_stripped = player_name.strip() if player_name else ""
        if not name_stripped:
            raise ValueError("Spielername darf nicht leer sein.")
        self._player_name: str = name_stripped

        #: Eindeutige Spieler-ID (UUID).
        self._player_id: str = player_id or str(uuid.uuid4())

        #: Spielerposition am Tisch (0-3), wird von der GameEngine gesetzt.
        self.player_index: Optional[int] = None

    def __repr__(self) -> str:
        """
        Gibt eine repräsentative Zeichenkette für das Player-Objekt zurück.

        :return: String-Repräsentation (z.B. "Client(name='Alice', id='...')").
        """
        return f"{self.__class__.__name__}(name='{self.player_name}', id='{self.player_id}')"

    # Entfernen oder Zweck klären. Falls benötigt, sollte sie wahrscheinlich abstrakt sein.
    def reset_round(self):  # pragma: no cover
        """
        Setzt spielrundenspezifische Werte zurück. (Aktuell nicht implementiert)
        """
        # raise NotImplementedError
        pass # Vorerst keine Aktion

    # ------------------------------------------------------
    # Benachrichtigungen (Abstrakt)
    # ------------------------------------------------------

    async def notify(self, message_type: str, data: dict):
        """
        Verarbeitet eine Benachrichtigung vom Server (unidirektionale, z.B. Spielzustand, Fehler).

        Muss von Subklassen implementiert werden.

        :param message_type: Der Typ der Nachricht.
        :param data: Die Nutzdaten der Nachricht.
        """
        raise NotImplementedError

    # ------------------------------------------------------
    # Entscheidungen
    # ------------------------------------------------------

    # TODO: Überlegung zu Aktions-Varianten:
    # Variante a) Eine einzige `get_action`-Methode: Der Spieler (insbesondere Agent) muss
    #              selbst anhand des Spielzustands erkennen, welche Art von Entscheidung
    #              gerade ansteht (Schupfen, Tichu, Kombi spielen, Wunsch, Drachen).
    #              Flexibler für komplexe KIs, aber erfordert mehr Logik im Spieler.
    # Variante b) Spezifische Methoden (`schupf`, `announce`, etc.): Die GameEngine
    #              ruft explizit die passende Methode auf, wenn eine bestimmte
    #              Entscheidung benötigt wird. Einfacher für die Spielerimplementierung,
    #              aber die Engine muss den Spielablauf detaillierter steuern.
    # Aktuelles Design: Variante b) wird von Client/Agent implementiert (als Platzhalter).
    # Die Signaturen sind hier definiert, Subklassen müssen sie implementieren.

    # Variante a) Player muss wissen, was zu tun ist und entscheidet

    # async def get_action(self, public_state: PublicState, private_state: PrivateState) -> Optional[dict]:
    #     """
    #     Fordert den Spieler auf, die nächste Aktion basierend auf dem Kontext zu bestimmen.
    #
    #     Diese Methode ist für ein Design gedacht, bei dem der Spieler selbst entscheidet,
    #     welche Art von Aktion gerade erforderlich ist. Aktuell nicht primär verwendet.
    #
    #     :param public_state: Der öffentliche Spielzustand.
    #     :type public_state: PublicState
    #     :param private_state: Der private Zustand dieses Spielers.
    #     :type private_state: PrivateState
    #     :return: Ein Dictionary, das die gewählte Aktion beschreibt.
    #     :rtype: Optional[dict]
    #     :raises NotImplementedError: Wenn die Methode nicht von der Subklasse überschrieben wurde.
    #     """
    #     raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'get_action' implementieren, wenn Variante (a) verwendet wird.")

    # --- Variante b) Spezifische Entscheidungen ---

    async def schupf(self, pub: PublicState, priv: PrivateState) -> list[tuple]:
        """
        Fordert den Spieler auf, drei Karten zum Schupfen auszuwählen.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Die Liste der Karten (Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner).
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

    async def combination(self, pub: PublicState, priv: PrivateState, action_space: list[tuple]) -> tuple:
        """
        Fordert den Spieler auf, eine gültige Kartenkombination auszuwählen oder zu passen.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :param action_space: Mögliche Kombinationen (inklusiv Passen; wenn Passen erlaubt ist, steht Passen an erster Stelle).
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

    async def gift(self, pub: PublicState, priv: PrivateState) -> int:
        """
        Fragt den Spieler, welchem Gegner der mit dem Drachen gewonnene Stich gegeben werden soll.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Der Index (0-3) des Gegners, der den Stich erhält.
        :raises PlayerInteractionError: Wenn die Aktion fehlschlägt.
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'gift' implementieren.")

    # ------------------------------------------------------
    # Eigenschaften
    # ------------------------------------------------------

    @property
    def name(self) -> str:
        """Gibt den Klassennamen zurück (z.B. 'Client', 'Agent')."""
        return type(self).__name__

    @property
    def player_name(self) -> str:
        """Der Name des Spielers."""
        return self._player_name

    @property
    def player_id(self) -> str:
        """Die eindeutige ID des Spielers (UUID)."""
        return self._player_id

    # Index des Partners
    @property
    def partner_index(self) -> int:
        """Der Index des Partners (0-3)."""
        return (self.player_index + 2) % 4

    # Index des rechten Gegners
    @property
    def opponent_right_index(self) -> int:
        """Der Index des rechten Gegners (0-3)."""
        return (self.player_index + 1) % 4

    # Index des linken Gegners
    @property
    def opponent_left_index(self) -> int:
        """Der Index des linken Gegners (0-3)."""
        return (self.player_index + 3) % 4
