"""
Definiert die abstrakte Basisklasse `Player` für alle Spieler im Tichu-Spiel.
"""
from src.common.logger import logger
from src.private_state2 import PrivateState
from src.public_state2 import PublicState
from typing import Optional
from uuid import uuid4


class Player:
    """
    Die Abstrakte Basisklasse für einen Spieler (Mensch oder KI).

    Definiert die grundlegenden Eigenschaften und Methoden, die jeder Spieler haben muss.

    :ivar player_index: Der Index des Spielers am Tisch (0 bis 3, None == Spieler sitzt noch nicht am Tisch).
    """

    def __init__(self, name: str, session: Optional[str] = None):
        """
        Initialisiert einen neuen Spieler.

        :param name: Der Name des Spielers. Wird bereinigt (Leerzeichen entfernt). Darf nicht leer sein.
        :param session: (Optional) Aktuelle Session des Spielers. Wenn None, wird eine Session generiert.
        :raises ValueError: Wenn der `player_name` leer ist.
        """
        #: Der Name des Spielers.
        name_stripped = name.strip() if name else ""
        if not name_stripped:
            raise ValueError("Spielername darf nicht leer sein.")
        self._name: str = name_stripped
        self._session: str = session if session else str(uuid4())
        self.player_index: Optional[int] = None  # wird von der GameEngine gesetzt
        logger.debug(f"Player '{self._name}' (Session: {self._session}) erstellt.")

    def __repr__(self) -> str:
        """
        Gibt eine repräsentative Zeichenkette für das Player-Objekt zurück.

        :return: String-Repräsentation (z.B. "Agent(name='Alice', session='...')").
        """
        return f"{self.__class__.__name__}(name='{self._name}', session='{self._session}')"

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
    # Benachrichtigung
    # ------------------------------------------------------

    async def notify(self, message_type: str, data: dict):
        """
        Verarbeitet eine Benachrichtigung vom Server (unidirektionale, z.B. Spielzustand, Fehler).

        :param message_type: Der Typ der Nachricht.
        :param data: Die Nutzdaten der Nachricht.
        """
        pass

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
    def class_name(self) -> str:
        """Gibt den Klassennamen zurück (z.B. 'Client', 'Agent')."""
        return type(self).__name__

    @property
    def name(self) -> str:
        """Der Name des Spielers."""
        return self._name

    @property
    def session(self) -> str:
        """Die aktuelle Session des Spielers."""
        return self._session

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
