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
    Subklassen (`Client`, `Agent`) müssen die abstrakten Methoden implementieren.
    """

    def __init__(self, player_name: str, player_id: Optional[str] = None):
        """
        Initialisiert einen neuen Spieler.

        :param player_name: Der Name des Spielers. Wird bereinigt (Leerzeichen entfernt). Darf nicht leer sein.
        :param player_id: Eine optionale, vorgegebene Spieler-ID. Wenn None, wird eine neue UUID generiert.
        :raises ValueError: Wenn der `player_name` nach Bereinigung leer ist.
        """
        # TODO: Player Name validieren/bereinigen
        name_stripped = player_name.strip() if player_name else ""
        if not name_stripped:
            raise ValueError("Spielername darf nicht leer sein.")
        #: Der (bereinigte) Name des Spielers.
        self.player_name: str = name_stripped

        #: Eindeutige Spieler-ID (UUID).
        self.player_id: str = player_id or str(uuid.uuid4())

        #: Spielerposition am Tisch (0-3), wird von der GameEngine gesetzt.
        self.player_index: Optional[int] = None

    def __repr__(self) -> str:
        """
        Gibt eine repräsentative Zeichenkette für das Player-Objekt zurück.

        :return: String-Repräsentation (z.B. "Client(name='Alice', id='...')").
        :rtype: str
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
        Sendet eine Nachricht (Spielzustand, Fehler etc.) an den Spieler.

        Diese Methode ist abstrakt und muss von konkreten Subklassen
        (`Client`, `Agent`) implementiert werden, um die Nachricht
        passend zu übermitteln (z.B. via WebSocket oder interne Verarbeitung).

        :param message_type: Der Typ der Nachricht.
        :type message_type: str
        :param data: Die Nutzdaten der Nachricht.
        :type data: dict
        :raises NotImplementedError: Wenn die Methode nicht von der Subklasse überschrieben wurde.
        """
        raise NotImplementedError

    # ------------------------------------------------------
    # Spiel-Entscheidungen
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

    async def get_action(self, public_state: PublicState, private_state: PrivateState) -> Optional[dict]:
        """
        Fordert den Spieler auf, die nächste Aktion basierend auf dem Kontext zu bestimmen.

        Diese Methode ist für ein Design gedacht, bei dem der Spieler selbst entscheidet,
        welche Art von Aktion gerade erforderlich ist. Aktuell nicht primär verwendet.

        :param public_state: Der öffentliche Spielzustand.
        :type public_state: PublicState
        :param private_state: Der private Zustand dieses Spielers.
        :type private_state: PrivateState
        :return: Ein Dictionary, das die gewählte Aktion beschreibt.
        :rtype: Optional[dict]
        :raises NotImplementedError: Wenn die Methode nicht von der Subklasse überschrieben wurde.
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'get_action' implementieren, wenn Variante (a) verwendet wird.")

    # --- Variante b) Spezifische Entscheidungen ---

    def schupf(self, pub: PublicState, priv: PrivateState) -> list[tuple]:
        """
        Fordert den Spieler auf, drei Karten zum Schupfen auszuwählen.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Zustand (enthält Handkarten).
        :return: Eine Liste mit genau einem Tupel, das die drei zu schupfenden Karten enthält
                 (Format: [(karte_an_gegner_rechts, karte_an_partner, karte_an_gegner_links)]).
                 Der genaue Typ der Karten hängt von der internen Repräsentation ab.
        :rtype: list[Tuple[Any, Any, Any]]
        :raises NotImplementedError: Wenn die Methode nicht von der Subklasse überschrieben wurde.
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'schupf' implementieren.")

    def announce(self, pub: PublicState, priv: PrivateState, grand: bool = False) -> bool:
        """
        Fragt den Spieler, ob er Tichu (oder Grand Tichu) ansagen möchte.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Zustand.
        :param grand: True, wenn nach Grand Tichu gefragt wird, False für kleines Tichu.
        :type grand: bool
        :return: True, wenn angesagt wird, sonst False.
        :rtype: bool
        :raises NotImplementedError: Wenn die Methode nicht von der Subklasse überschrieben wurde.
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'announce' implementieren.")

    def combination(self, pub: PublicState, priv: PrivateState, action_space: list[tuple]) -> tuple:
        """
        Fordert den Spieler auf, eine gültige Kartenkombination auszuwählen oder zu passen.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Zustand.
        :param action_space: Eine Liste der von der GameEngine als gültig erachteten Aktionen.
                             Jede Aktion ist ein Tupel, z.B. ('play_cards', [card_obj1, ...])
                             oder ('pass_turn', None).
        :type action_space: list[tuple]
        :return: Die vom Spieler ausgewählte Aktion als Tupel aus dem `action_space`.
        :rtype: tuple
        :raises NotImplementedError: Wenn die Methode nicht von der Subklasse überschrieben wurde.
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'combination' implementieren.")

    def wish(self, pub: PublicState, priv: PrivateState) -> int:
        """
        Fragt den Spieler nach einem Kartenwert-Wunsch (nach Ausspielen des Mah Jong).

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Zustand.
        :return: Der gewünschte Kartenwert (2-14).
        :rtype: int
        :raises NotImplementedError: Wenn die Methode nicht von der Subklasse überschrieben wurde.
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'wish' implementieren.")

    def gift(self, pub: PublicState, priv: PrivateState) -> int:
        """
        Fragt den Spieler, welchem Gegner der mit dem Drachen gewonnene Stich gegeben werden soll.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Zustand (sollte die Indizes der Gegner kennen).
        :return: Der Index (0-3) des Gegners, der den Stich erhält.
        :rtype: int
        :raises NotImplementedError: Wenn die Methode nicht von der Subklasse überschrieben wurde.
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'gift' implementieren.")

    # ------------------------------------------------------
    # Eigenschaften
    # ------------------------------------------------------

    # Diese Property gibt nur den Klassennamen zurück, könnte nützlich sein.
    @property
    def name(self) -> str:
        """Gibt den Namen der konkreten Spielerklasse zurück (z.B. 'Client', 'Agent')."""
        return type(self).__name__
