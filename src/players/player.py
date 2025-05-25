"""
Definiert die abstrakte Basisklasse `Player` für alle Spieler im Tichu-Spiel.
"""

import asyncio
from src.common.logger import logger
from src.lib.cards import Card, Cards
from src.lib.combinations import Combination
from src.lib.errors import ErrorCode
from src.private_state import PrivateState
from src.public_state import PublicState
from typing import Optional, Tuple, List, Dict
from uuid import uuid4


class Player:
    """
    Die Abstrakte Basisklasse für einen Spieler (Mensch oder KI).

    Definiert die grundlegenden Eigenschaften und Methoden, die jeder Spieler haben muss.

    :ivar index: Der Index des Spielers am Tisch (0 bis 3, None == Spieler sitzt noch nicht am Tisch).
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
        self.index: Optional[int] = None  # wird von der GameEngine gesetzt
        self.interrupt_event: Optional[asyncio.Event] = None  # wird von der GameEngine gesetzt
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

        ### Broadcast-Nachricht (diese wird an jeden Spieler gesendet) ###

    # ------------------------------------------------------
    # Benachrichtigungen
    # ------------------------------------------------------

    # async def welcome(self, pub: PublicState, priv: PrivateState) -> bool:
    #     """
    #     Der Server ruft diese Funktion auf, nachdem der Spieler sich angemeldet und einen Sitzplatz erhalten hat (auch nach einem Reconnect).
    #
    #     :param pub: Der öffentliche Spielzustand.
    #     :param priv: Der private Spielzustand.
    #     :result: True, wenn der Spieler erfolgreich begrüßt wurde, sonst False.
    #     """
    #     return True

    async def deal_cards(self, hand_cards: Cards):
        """
        Der Server ruft diese Funktion auf, wenn die Handkarten ausgeteilt wurden.

        :param hand_cards: Die Handkarten des Spielers.
        """
        pass

    async def deal_schupf_cards(self, from_opponent_right: Card, from_partner: Card, from_opponent_left: Card):
        """
        Der Server ruft diese Funktion auf, wenn die Schupfkarten ausgetauscht wurden.

        :param from_opponent_right: Die Karte für den rechten Gegner.
        :param from_partner: Die Karte für den Partner.
        :param from_opponent_left: Die Karte für den linken Gegner.
        """
        pass

    async def notify(self, event: str, context: Optional[dict] = None):
        """
        Der Server ruft diese Funktion auf, um ein Spielereignis zu melden.

        :param event: Das Spielereignis.
        :param context: (Optional) Zusätzliche Informationen zum Ereignis.
        """
        pass

    async def error(self, message: str, code: ErrorCode, context: Optional[Dict] = None):
        """
        Der Server ruft diese Funktion auf, um einen Fehler zu melden.

        Die Fehlermeldung wird über die WebSocket-Verbindung an den realen Spieler weitergeleitet.

        :param message: Die Fehlermeldung.
        :param code: Der Fehlercode.
        :param context: (Optional) Zusätzliche Informationen.
        """
        pass

    # ------------------------------------------------------
    # Entscheidungen
    # ------------------------------------------------------

    ### Anfragen (diese erwarten eine Antwort vom Spieler) ###

    async def announce(self, pub: PublicState, priv: PrivateState) -> bool:
        """
        Fragt den Spieler, ob er ein Tichu (normales oder großes) ansagen möchte.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: True, wenn angesagt wird, sonst False.
        """
        grand = pub.start_player_index == -1 and len(priv.hand_cards) == 8
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'announce' implementieren.")

    async def schupf(self, pub: PublicState, priv: PrivateState) -> Tuple[Card, Card, Card]:
        """
        Fordert den Spieler auf, drei Karten zum Schupfen auszuwählen.

        Diese Aktion kann durch ein Interrupt abgebrochen werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner.
        :raises PlayerInterruptError: Wenn die Aktion durch ein Interrupt abgebrochen wurde.  # todo oder False zurückgeben?
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'schupf' implementieren.")

    async def play(self, pub: PublicState, priv: PrivateState) -> Tuple[Cards, Combination]:
        """
        Fordert den Spieler auf, eine gültige Kartenkombination auszuwählen oder zu passen.

        Diese Aktion kann durch ein Interrupt abgebrochen werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Die ausgewählte Kombination (Karten, (Typ, Länge, Wert)) oder Passen ([], (0,0,0)).
        :raises PlayerInterruptError: Wenn die Aktion durch ein Interrupt abgebrochen wurde.  # todo oder False zurückgeben?
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'play' implementieren.")

    async def bomb(self, pub: PublicState, priv: PrivateState) -> Optional[Tuple[Cards, Combination]]:
        """
        Fragt den Spieler, ob er eine Bombe werfen will, und wenn ja, welche.

        Die Engine ruft diese Methode nur auf, wenn eine Bombe vorhanden ist.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Die ausgewählte Bombe (Karten, (Typ, Länge, Wert)) oder None, wenn keine Bombe geworfen wird.
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'bomb' implementieren.")

    async def wish(self, pub: PublicState, priv: PrivateState) -> int:
        """
        Fragt den Spieler nach einem Kartenwert-Wunsch (nach Ausspielen des Mah Jong).

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Der gewünschte Kartenwert (2-14).
        """
        raise NotImplementedError(f"{self.__class__.__name__} muss die Methode 'wish' implementieren.")

    async def give_dragon_away(self, pub: PublicState, priv: PrivateState) -> int:
        """
        Fragt den Spieler, welchem Gegner der mit dem Drachen gewonnene Stich gegeben werden soll.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Der Index (0-3) des Gegners, der den Stich erhält.
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
        return (self.index + 2) % 4

    @property
    def opponent_right_index(self) -> int:
        """Der Index des rechten Gegners (0-3)."""
        return (self.index + 1) % 4

    @property
    def opponent_left_index(self) -> int:
        """Der Index des linken Gegners (0-3)."""
        return (self.index + 3) % 4
