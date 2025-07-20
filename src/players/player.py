"""
Definiert die abstrakte Basisklasse `Player` für alle Spieler im Tichu-Spiel.
"""

import asyncio
from src.lib.cards import Card, Cards
from src.lib.combinations import Combination
from src.lib.errors import ErrorCode
from src.private_state import PrivateState
from src.public_state import PublicState
from typing import Optional, Tuple, Dict
from uuid import uuid4


class Player:
    """
    Die Abstrakte Basisklasse für einen Spieler (Mensch oder KI).

    Definiert die grundlegenden Eigenschaften und Methoden, die jeder Spieler haben muss.

    :ivar pub: Der öffentliche Spielzustand.
    :ivar priv: Der private Spielzustand.
    :ivar interrupt_event: Das globale Interrupt-Event.
    """

    def __init__(self, name: str, session_id: Optional[str] = None):
        """
        Initialisiert einen neuen Spieler.

        :param name: Der Name des Spielers. Wird bereinigt (Leerzeichen entfernt). Darf nicht leer sein.
        :param session_id: (Optional) Aktuelle Session des Spielers. Wenn None, wird eine Session generiert.
        :raises ValueError: Wenn der `player_name` leer ist.
        """
        name_stripped = name.strip() if name else ""
        if not name_stripped:
            raise ValueError("Spielername darf nicht leer sein.")
        self._name: str = name_stripped
        self._session_id: str = session_id if session_id else str(uuid4())
        self.pub: Optional[PublicState] = None  # wird von der GameEngine gesetzt
        self.priv: Optional[PrivateState] = None  # wird von der GameEngine gesetzt
        self.interrupt_event: Optional[asyncio.Event] = None  # wird von der GameEngine gesetzt

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

    async def announce(self) -> bool:
        """
        Die Engine fragt den Spieler, ob er ein Tichu (großes oder einfaches) ansagen möchte.

        Die Engine ruft diese Methode nur auf, wenn der Spieler ein Tichu ansagen darf.

        Die Bedingung für ein großes Tichu (direkt nach dem Austeilen der ersten 8 Karten) ist::
            pub.announcements[priv.player_index] == 0 and
            pub.count_hand_cards[priv.player_index] == 8 and
            pub.start_player_index == -1

        Die Bedingung für ein einfaches Tichu ist::
            pub.announcements[priv.player_index] == 0 and
            pub.count_hand_cards[priv.player_index] == 14 and
            pub.start_player_index >= 0

        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        :return: True, wenn angesagt wird, sonst False.
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'announce_tichu' implementieren.")

    async def schupf(self) -> Tuple[Card, Card, Card]:
        """
        Die Engine fordert den Spieler auf, drei Karten zum Schupfen auszuwählen.

        Die Engine ruft diese Methode nur auf, wenn der Spieler noch Karten abgeben muss.
        Die Bedingung ist::
            pub.count_hand_cards[priv.player_index] > 8 and
            priv.given_schupf_cards is None

        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        :return: Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner.
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'schupf' implementieren.")

    async def play(self, interruptable: bool = False) -> Tuple[Cards, Combination]:
        """
        Die Engine fordert den Spieler auf, eine gültige Kartenkombination auszuwählen oder zu passen.

        Die Engine ruft diese Methode nur auf, wenn der Spieler am Zug ist oder eine Bombe hat.
        Die Bedingung ist::
            pub.current_turn_index == priv.player_index or
            priv.has_bomb

        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        :param interruptable: (Optional) Wenn True, kann die Anfrage durch ein Interrupt abgebrochen werden.
        :return: Die ausgewählte Kombination (Karten, (Typ, Länge, Rang)) oder Passen ([], (0,0,0)).
        :raises PlayerInterruptError: Wenn die Aktion durch ein Interrupt abgebrochen wurde.
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'play' implementieren.")

    async def wish(self) -> int:
        """
        Die Engine fragt den Spieler nach einem Kartenwert-Wunsch (nach Ausspielen des Mah Jong).

        Die Engine ruft diese Methode nur auf, wenn der Spieler sich einen Kartenwert wünschen muss.
        Die Bedingung ist::
            pub.current_turn_index == priv.player_index and
            pub.wish_value == 0 and
            (1,0) in pub.trick_cards

        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        :return: Der gewünschte Kartenwert (2-14).
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'wish' implementieren.")

    async def give_dragon_away(self) -> int:
        """
        Die Engine fragt den Spieler, welcher Gegner den Drachen bekommen soll.

        Die Engine ruft diese Methode nur auf, wenn der Spieler den Drachen verschenken muss.
        Die Bedingung ist::
            pub.current_turn_index == priv.player_index and
            pub.dragon_recipient == -1 and
            pub.trick_combination == (0,1,15)

        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        :return: Der Index (0-3) des Gegners, der den Stich erhält.
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'give_dragon_away' implementieren.")

    # ------------------------------------------------------
    # Benachrichtigungen
    # ------------------------------------------------------

    async def notify(self, event: str, context: Optional[dict] = None):
        """
        Der Server ruft diese Funktion auf, um dem Spieler ein Spielereignis zu melden.

        :param event: Das Spielereignis.
        :param context: (Optional) Zusätzliche Informationen zum Ereignis.
        """
        pass

    async def error(self, message: str, code: ErrorCode, context: Optional[Dict] = None):
        """
        Der Server ruft diese Funktion auf, um dem Spieler einen Fehler zu melden.

        Die Fehlermeldung wird über die WebSocket-Verbindung an den realen Spieler weitergeleitet.

        :param message: Die Fehlermeldung.
        :param code: Der Fehlercode.
        :param context: (Optional) Zusätzliche Informationen.
        """
        pass

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
