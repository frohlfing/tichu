import asyncio
from aiohttp import web, WSCloseCode
from src.common.logger import logger
from src.common.rand import Random
from src.players.player import Player
from src.private_state2 import PrivateState
from src.public_state2 import PublicState
from typing import Optional


class Client(Player):
    """Repräsentiert einen menschlichen Spieler mit einer WebSocket-Verbindung."""

    def __init__(self, player_name: str, websocket: web.WebSocketResponse, player_id: Optional[str] = None, seed: Optional[int] = None):
        super().__init__(player_name, player_id)
        self._websocket: Optional[web.WebSocketResponse] = websocket
        self._is_connected: bool = True
        self._random = Random(seed)  # Zufallsgenerator, geeignet für Multiprocessing

    @property
    def is_connected(self) -> bool:
        """Ist der Client aktuell verbunden?"""
        return self._is_connected and self._websocket is not None and not self._websocket.closed

    def update_websocket(self, new_websocket: web.WebSocketResponse):
        """Aktualisiert die WebSocket-Verbindung bei einem Reconnect."""
        logger.debug(f"Updating websocket for {self.player_name}")
        self._websocket = new_websocket
        self._is_connected = True

    def mark_as_disconnected(self, reason: str = "Connection closed"):
        """Wird von außen (Engine oder Handler) aufgerufen, um den Client als getrennt zu markieren."""
        if self._is_connected:
            logger.info(f"Marking client {self.player_name} ({self.player_id}) as disconnected. Reason: {reason}")
            self._is_connected = False
            self._websocket = None # Referenz aufheben

    async def close_connection(self, code=WSCloseCode.GOING_AWAY, message=b'Closing connection'):
        """Versucht, die WebSocket-Verbindung sauber zu schließen."""
        if self._websocket and not self._websocket.closed:
            logger.debug(f"Closing websocket for {self.player_name}")
            try:
                 await self._websocket.close(code=code, message=message)
            except Exception as e:
                 logger.warning(f"Exception during websocket close for {self.player_name}: {e}")
        self.mark_as_disconnected(reason="Explicit close_connection call")

    # ------------------------------------------------------
    # Notify
    # ------------------------------------------------------

    async def notify(self, message_type: str, data: dict):
        """Sendet Daten als JSON über die WebSocket-Verbindung."""
        if self.is_connected and self._websocket:
            message = {"type": message_type, "payload": data}
            try:
                logger.debug(f"Sending to {self.player_name}: {message}")
                await self._websocket.send_json(message)
            except (ConnectionResetError, asyncio.CancelledError, RuntimeError, ConnectionAbortedError) as e:
                # RuntimeError kann auftreten, wenn versucht wird, auf eine geschlossene Verbindung zu senden
                logger.warning(f"Failed to send message to {self.player_name} ({self.player_id}): {e}. Marking as disconnected.")
                # Markiere als nicht verbunden. Die Engine wird beim nächsten Sendeversuch
                # oder durch den websocket_handler über den tatsächlichen Disconnect informiert.
                self._is_connected = False  # Wichtig, um weitere Sendeversuche zu stoppen
        # else:
        #    pass  # Kein Logging hier, wenn eh nicht verbunden

    # ------------------------------------------------------
    # Entscheidungen
    # ------------------------------------------------------

    # Welche Karten an die Mitspieler abgeben?
    # return: Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner
    def schupf(self, pub: PublicState, priv: PrivateState) -> list[tuple]:
        hand = list(priv.hand)
        return [hand.pop(self._random.integer(0, 14)), hand.pop(self._random.integer(0, 13)), hand.pop(self._random.integer(0, 12))]

    # Tichu ansagen?
    def announce(self, pub: PublicState, priv: PrivateState, grand: bool = False) -> bool:
        return self._random.choice([True, False], [1, 19] if grand else [1, 9])

    # Welche Kombination soll gespielt werden?
    # action_space: Mögliche Kombinationen (inklusiv Passen)
    # return: Ausgewählte Kombination (Karten, (Typ, Länge, Wert))
    def combination(self, pub: PublicState, priv: PrivateState, action_space: list[tuple]) -> tuple:
        return action_space[self._random.integer(0, len(action_space))]

    # Welcher Kartenwert wird gewünscht?
    # return: Wert zw. 2 und 14
    def wish(self, pub: PublicState, priv: PrivateState) -> int:
        return self._random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])

    # Welcher Gegner soll den Drachen bekommen?
    # return: Nummer des Gegners
    def gift(self, pub: PublicState, priv: PrivateState) -> int:
        return priv.opponent_right if self._random.boolean() else priv.opponent_left
