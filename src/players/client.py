"""
Definiert die Client-Klasse, die einen menschlichen Spieler repräsentiert,
der über eine WebSocket-Verbindung interagiert.
"""

import asyncio
from aiohttp import web, WSCloseCode
from src.common.logger import logger
from src.common.rand import Random
from src.players.player import Player
from src.private_state2 import PrivateState
from src.public_state2 import PublicState
from typing import Optional


class Client(Player):
    """
    Repräsentiert einen menschlichen Spieler, der über WebSocket verbunden ist.

    Verwaltet die WebSocket-Verbindung und den Verbindungsstatus.
    Implementiert `notify`, um Nachrichten an den Browser des Spielers zu senden.
    Enthält Platzhalter-Methoden für Spielentscheidungen, die aktuell zufällig sind
    und später durch Nachrichten vom Client ersetzt werden müssen.
    """

    def __init__(self, player_name: str, websocket: web.WebSocketResponse, player_id: Optional[str] = None, seed: Optional[int] = None):
        """
        Initialisiert einen neuen Client-Spieler.

        :param player_name: Der Name des Spielers.
        :param websocket: Das WebSocketResponse-Objekt der initialen Verbindung.
        :param player_id: Optionale, feste ID für den Spieler (für Reconnects). Wenn None, wird eine UUID generiert.
        :param seed: Optionaler Seed für den internen Zufallsgenerator (für Tests).
        """
        # Rufe Konstruktor der Basisklasse auf (validiert auch Namen).
        super().__init__(player_name, player_id=player_id)
        #: Das aktive WebSocket-Objekt.
        self._websocket: Optional[web.WebSocketResponse] = websocket
        #: Interner Verbindungsstatus.
        self._is_connected: bool = True
        #: Zufallsgenerator-Instanz.
        self._random = Random(seed)

        logger.debug(f"Client '{self.player_name}' (ID: {self.player_id}) erstellt und initial verbunden.")

    @property
    def is_connected(self) -> bool:
        """
        Gibt zurück, ob der Client aktuell als verbunden gilt.

        Prüft sowohl das interne Flag als auch den Zustand des WebSocket-Objekts.

        :return: True, wenn verbunden, sonst False.
        """
        return self._is_connected and self._websocket is not None and not self._websocket.closed

    def update_websocket(self, new_websocket: web.WebSocketResponse):
        """
        Aktualisiert die WebSocket-Verbindung bei einem Reconnect.

        Wird von der `GameFactory` aufgerufen, wenn ein bekannter Spieler
        sich erneut verbindet.

        :param new_websocket: Das neue WebSocketResponse-Objekt.
        """
        logger.info(f"Aktualisiere WebSocket für Client {self.player_name} ({self.player_id}).")
        self._websocket = new_websocket
        self._is_connected = True # Markiere wieder als verbunden

    def mark_as_disconnected(self, reason: str = "Verbindung geschlossen"):
        """
        Markiert den Client intern als getrennt.

        Wird aufgerufen, wenn die Verbindung verloren geht oder explizit
        geschlossen wird. Setzt das interne Flag und entfernt die WebSocket-Referenz.

        :param reason: Der Grund für die Trennung (für Logging).
        """
        # Nur ausführen, wenn der Client aktuell als verbunden gilt.
        if self._is_connected:
            logger.info(f"Markiere Client {self.player_name} ({self.player_id}) als getrennt. Grund: {reason}")
            self._is_connected = False
            self._websocket = None # WebSocket-Referenz entfernen

    async def close_connection(self, code: int = WSCloseCode.GOING_AWAY, message: bytes = b'Verbindung wird geschlossen'):
        """
        Versucht, die WebSocket-Verbindung serverseitig aktiv und sauber zu schließen.

        Markiert den Client danach intern als getrennt.

        :param code: Der WebSocket Close Code (siehe RFC 6455).
        :param message: Eine optionale Nachricht (als Bytes), die mit dem Close Frame gesendet wird.
        """
        # Nur versuchen, wenn ein aktives, nicht geschlossenes WebSocket vorhanden ist.
        if self._websocket and not self._websocket.closed:
            logger.debug(f"Schließe WebSocket für Client {self.player_name} aktiv.")
            try:
                # Sende Close Frame an den Client.
                await self._websocket.close(code=code, message=message)
            except Exception as e:
                # Fehler beim Senden des Close Frames (z.B. Verbindung bereits tot).
                logger.warning(f"Ausnahme beim aktiven Schließen des WebSockets für {self.player_name}: {e}")
        # Markiere den Client auf jeden Fall intern als getrennt.
        self.mark_as_disconnected(reason="Expliziter close_connection Aufruf")

    # ------------------------------------------------------
    # Benachrichtigungen senden (Implementierung von Player.notify)
    # ------------------------------------------------------

    async def notify(self, message_type: str, data: dict):
        """
        Sendet eine Nachricht (typischerweise Spielzustand oder Fehler)
        als JSON über die WebSocket-Verbindung an den Client.

        Implementiert die abstrakte Methode der `Player`-Basisklasse.

        :param message_type: Der Typ der Nachricht (z.B. "public_state_update").
        :param data: Die Nutzdaten der Nachricht als Dictionary.
        """
        # Nur senden, wenn der Client als verbunden gilt.
        if self.is_connected and self._websocket:
            # Standardisiertes Nachrichtenformat {type: ..., payload: ...}
            message = {"type": message_type, "payload": data}
            try:
                # Sende die Nachricht als JSON. aiohttp kümmert sich um die Serialisierung.
                logger.debug(f"Sende an {self.player_name}: {message}")
                await self._websocket.send_json(message)
            except (ConnectionResetError, asyncio.CancelledError, RuntimeError, ConnectionAbortedError) as e:
                # Fehler beim Senden deuten meist auf eine unterbrochene Verbindung hin.
                logger.warning(f"Senden der Nachricht an {self.player_name} ({self.player_id}) fehlgeschlagen: {e}. Markiere als getrennt.")
                # Markiere den Client intern als getrennt, damit keine weiteren Sendeversuche erfolgen.
                self.mark_as_disconnected(reason=f"Sendefehler: {e}")
            except Exception as e:
                 # Andere unerwartete Fehler beim Senden.
                 logger.exception(f"Unerwarteter Fehler beim Senden an {self.player_name}: {e}")
                 self.mark_as_disconnected(reason=f"Unerwarteter Sendefehler: {e}")
        # else: Wenn nicht verbunden, tue nichts (kein Logging nötig, um Spam zu vermeiden).
        #    pass

    # ------------------------------------------------------
    # Entscheidungen
    # ------------------------------------------------------
    # Die folgenden Methoden repräsentieren die Entscheidungen, die ein Spieler
    # treffen muss. In der `Client`-Implementierung sind sie aktuell Platzhalter,
    # die zufällige Aktionen ausführen.
    # Im echten Spielbetrieb muss die `GameEngine` stattdessen auf eine Nachricht
    # vom WebSocket warten, die die Entscheidung des menschlichen Spielers enthält.
    # Diese Methoden könnten dann entfernt oder für Testzwecke beibehalten werden.

    # Welche Karten an die Mitspieler abgeben? (Schupfen)
    # return: Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner
    def schupf(self, pub: PublicState, priv: PrivateState) -> list[tuple]:
        """
        PLATZHALTER: Wählt zufällige Karten zum Schupfen aus.

        Im echten Spiel muss die Engine auf eine 'schupf_cards'-Nachricht vom Client warten.

        :param pub: Öffentlicher Spielzustand.
        :param priv: Privater Spielzustand (enthält Handkarten).
        :return: Eine Liste mit drei Karten (Platzhalter-Typ Any).
        """
        hand = list(priv.hand)  # Kopie der Handkarten
        return [hand.pop(self._random.integer(0, 14)), hand.pop(self._random.integer(0, 13)), hand.pop(self._random.integer(0, 12))]

    # Tichu ansagen?
    def announce(self, pub: PublicState, priv: PrivateState, grand: bool = False) -> bool:
        """
        PLATZHALTER: Entscheidet zufällig, ob Tichu angesagt wird.

        Im echten Spiel muss die Engine auf eine 'announce_tichu'-Nachricht warten (oder Timeout).

        :param pub: Öffentlicher Spielzustand.
        :param priv: Privater Spielzustand.
        :param grand: True, wenn es um Grand Tichu geht.
        :return: True, wenn Tichu angesagt wird, sonst False.
        """
        return self._random.choice([True, False], [1, 19] if grand else [1, 9])

    # Welche Kombination soll gespielt werden?
    # action_space: Mögliche Kombinationen (inklusiv Passen)
    # return: Ausgewählte Kombination (Karten, (Typ, Länge, Wert))
    def combination(self, pub: PublicState, priv: PrivateState, action_space: list[tuple]) -> tuple:
        """
        PLATZHALTER: Wählt eine zufällige, gültige Aktion aus dem action_space.

        Im echten Spiel muss die Engine auf eine 'play_cards' oder 'pass_turn' Nachricht warten.

        :param pub: Öffentlicher Spielzustand.
        :param priv: Privater Spielzustand.
        :param action_space: Liste der möglichen Aktionen (Kombinationen oder Passen), die von der Engine als gültig erachtet werden.
        :return: Die zufällig ausgewählte Aktion.
        """
        return action_space[self._random.integer(0, len(action_space))]

    # Welcher Kartenwert wird gewünscht?
    # return: Wert zw. 2 und 14
    def wish(self, pub: PublicState, priv: PrivateState) -> int:
        """
        PLATZHALTER: Wählt einen zufälligen Kartenwert als Wunsch.

        Im echten Spiel muss die Engine auf eine 'make_wish'-Nachricht warten.

        :param pub: Öffentlicher Spielzustand.
        :param priv: Privater Spielzustand.
        :return: Ein zufälliger Kartenwert zwischen 2 und 14 (Ass).
        """
        return self._random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])

    # Welcher Gegner soll den Drachen bekommen?
    # return: Nummer des Gegners
    def gift(self, pub: PublicState, priv: PrivateState) -> int:
        """
        PLATZHALTER: Wählt zufällig einen Gegner aus, der den Drachen erhält.

        Im echten Spiel muss die Engine auf eine 'give_dragon'-Nachricht warten.

        :param pub: Öffentlicher Spielzustand.
        :param priv: Privater Spielzustand (enthält Infos über Gegner-Indizes).
        :return: Der Index des Gegners (0-3), der den Stich erhält.
        """
        return priv.opponent_right if self._random.boolean() else priv.opponent_left
