"""
Definiert den serverseitigen Endpunkt der WebSocket-Verbindung für die Interaktion mit einem menschlichen Spieler.
"""

import asyncio
import config
import time
from aiohttp import WSCloseCode
from aiohttp.web import WebSocketResponse
from src.common.logger import logger
from src.common.rand import Random
# noinspection PyUnresolvedReferences
from src.lib.cards import Card, Cards, stringify_cards, parse_cards
from src.lib.combinations import Combination
# noinspection PyUnresolvedReferences
from src.lib.errors import ClientDisconnectedError, PlayerInteractionError, PlayerInterruptError, PlayerTimeoutError, PlayerResponseError
from src.players.player import Player
from src.private_state import PrivateState
from src.public_state import PublicState
from typing import Optional, Dict, List, Tuple


class Client(Player):
    """
    Repräsentiert einen menschlichen Spieler, der über eine WebSocket verbunden ist.

    Erbt von der Basisklasse `Player`.
    """

    def __init__(self, name: str,
                 websocket: WebSocketResponse,
                 session_id: Optional[str] = None,
                 seed: Optional[int] = None):
        """
        Initialisiert einen neuen Client.

        :param name: Der Name des Spielers.
        :param websocket: Das WebSocketResponse-Objekt der initialen Verbindung.
        :param session_id: (Optional) Aktuelle Session des Spielers. Wenn None, wird eine Session generiert.
        :param seed: (Optional) Seed für den internen Zufallsgenerator (für Tests).
        """
        super().__init__(name, session_id=session_id)
        self._websocket = websocket
        self._random = Random(seed)  # Zufallsgenerator
        # todo es wird immer nur eine Anfrage gestellt. Bevor die nicht beantwortet ist, wird keine zweite gestellt.
        #  Daher reicht es, nur ein Future festzuhalten: self._pending_requests: Optional[asyncio.Future] = None
        self._pending_requests: Dict[str, asyncio.Future] = {}  # die noch unbeantworteten Websocket-Anfragen

    async def cleanup(self):
        """
        Bereinigt Ressourcen dieser Instanz.

        Versucht, die WebSocket-Verbindung serverseitig aktiv und sauber zu schließen.
        """
        if self._websocket and not self._websocket.closed:
            logger.debug(f"Schließe WebSocket für Client {self._name}.")
            try:
                await self._websocket.close(code=WSCloseCode.GOING_AWAY, message="Verbindung wird geschlossen".encode('utf-8'))
            except Exception as e:
                logger.exception(f"Fehler beim Schließen der WebSocket-Verbindung für {self._name}: {e}")

    # ------------------------------------------------------
    # WebSocket
    # ------------------------------------------------------

    async def on_websocket_response(self, action: str, data: dict):
        """
        Wird aufgerufen, wenn eine Antwort vom realen Spieler empfangen wurde.

        :param action: Die Aktion der ursprünglichen Anfrage.
        :param data: Die Daten der Antwort als Dictionary.
        """
        if action in self._pending_requests:
            future = self._pending_requests[action]
            if not future.done():
                future.set_result(data)
                logger.debug(f"Client {self._name}: Antwort für '{action}' an wartende Methode weitergeleitet.")
            else:
                # Die Future wurde bereits gesetzt (z.B. Timeout, Cancelled) oder die Antwort kam zu spät.
                logger.warning(f"Client {self._name}: Antwort für bereits abgeschlossene Aktion '{action}' erhalten: {data}")
        else:
            # Keine wartende Anfrage für diesen Typ gefunden.
            logger.warning(f"Client {self._name}: Unerwartete Antwort für '{action}' erhalten: {data}")

    async def on_notify(self, msg_type: str, payload: Optional[dict]=None):
        """
        Der Server ruft diese Funktion auf, um ein Spielereignis zu melden.

        Die Nachricht wird über die WebSocket-Verbindung an den realen Spieler weitergeleitet.

        :param msg_type: Der Typ der Nachricht.
        :param payload: Die Nutzdaten der Nachricht als Dictionary.
        """
        if payload is None:
            payload = {}

        if self._websocket.closed:
            logger.debug(f"Nachricht {msg_type} an {self._name} konnte nicht übermittelt werden. Keine Verbindung.")
            return

        message = {"type": msg_type, "payload": payload}
        try:
            logger.debug(f"Sende Nachricht an {self._name}: {message}")
            await self._websocket.send_json(message)
        except (ConnectionResetError, asyncio.CancelledError, RuntimeError, ConnectionAbortedError) as e:
            logger.warning(f"Senden der Nachricht {msg_type} an {self._name} fehlgeschlagen: {e}")
        except Exception as e:
            logger.exception(f"Unerwarteter Fehler beim Senden der Nachricht {msg_type} an {self._name}: {e}")

    async def _ask(self, request_type: str, context_payload: Optional[dict] = None, timeout: float = config.DEFAULT_REQUEST_TIMEOUT) -> dict | None:
        """
        Sendet eine Anfrage an den Client und wartet auf dessen Antwort.

        :param request_type: Eindeutiger Bezeichner für die Art der Anfrage (z.B. "play", "schupf").
        :param context_payload: Zusätzliche Daten, die mit der Anfrage an den Client gesendet werden (z.B. mögliche Aktionen).
        :param timeout: Maximale Wartezeit in Sekunden (0 == unbegrenzt).
        :return: Das 'payload'-Dictionary aus der Antwort des Clients bei Erfolg.
        :raises ClientDisconnectedError: Wenn der Client nicht verbunden ist.
        :raises PlayerInterruptError: Wenn die Anfrage durch ein Engine-Event unterbrochen wird.
        :raises PlayerTimeoutError: Wenn der Client nicht innerhalb des Timeouts antwortet.
        :raises asyncio.CancelledError: Wenn der wartende Task extern abgebrochen wird.
        :raises PlayerInteractionError: Bei anderen Fehlern während des Sendevorgangs oder Wartens.
        """
        # --- 1. Prüfen, ob Client verbunden ist ---
        if self._websocket.closed:
            logger.warning(f"Client {self.name}: Aktion '{request_type}' nicht möglich (nicht verbunden).")
            raise ClientDisconnectedError(f"Client {self.name} ist nicht verbunden.")

        logger.debug(f"Client {self.name}: Starte Anfrage '{request_type}'.")

        # --- 2. Future erstellen und registrieren ---
        if request_type in self._pending_requests:
            logger.warning(f"Client {self.name}: Überschreibe bereits laufende Anfrage für '{request_type}'.")
            old_future = self._pending_requests[request_type]
            if not old_future.done():
                old_future.cancel("Neue Anfrage ersetzt alte")
        loop = asyncio.get_running_loop()
        response_future = loop.create_future()
        self._pending_requests[request_type] = response_future

        # --- 3. Anfrage senden ---
        request_data: dict = {"type": "request_action", "payload": {"request": request_type, "timeout": timeout}}
        if context_payload:
            request_data["payload"]["context"] = context_payload  # Kontext in Payload verschachteln
        try:
            logger.debug(f"Sende Anfrage an {self.name}: {request_data}")
            await self._websocket.send_json(request_data)
        except (ConnectionResetError, asyncio.CancelledError, RuntimeError, ConnectionAbortedError) as e:
            logger.warning(f"Senden der Anfrage '{request_type}' an {self.name} fehlgeschlagen (Verbindungsfehler): {e}. Markiere als getrennt.")
            # noinspection PyAsyncCall
            self._pending_requests.pop(request_type, None)  # Future entfernen
            raise ClientDisconnectedError(f"Senden der Anfrage '{request_type}' fehlgeschlagen.") from e
        except Exception as e:
            logger.exception(f"Unerwarteter Fehler beim Senden der Anfrage '{request_type}' an {self.name}: {e}")
            # noinspection PyAsyncCall
            self._pending_requests.pop(request_type, None)  # Future entfernen
            raise PlayerInteractionError(f"Fehler beim Senden der Anfrage '{request_type}': {e}") from e

        # --- 4. Auf Antwort warten ---
        #loop = asyncio.get_running_loop()
        #response_future = loop.create_future()
        #response_future_task = asyncio.create_task(response_future, name=f"ClientResp_{self.index}_{request_type}")
        #interrupt_task = asyncio.create_task(self.interrupt_event.wait(), name="Interrupt")
        #wait_tasks = [response_future_task, interrupt_task]

        interrupt_task = asyncio.create_task(self.interrupt_event.wait(), name="Interrupt")
        wait_tasks = [response_future, interrupt_task]

        pending: set[asyncio.Task] = set()
        start_time = time.monotonic()
        try:
            done, pending = await asyncio.wait(wait_tasks, timeout=timeout, return_when=asyncio.FIRST_COMPLETED)

            # --- 5. Ergebnis auswerten ---
            if not done:
                # Timeout
                elapsed = time.monotonic() - start_time
                logger.warning(f"Client {self.name}: Timeout ({elapsed:.1f}s > {timeout}s) beim Warten auf Antwort für '{request_type}'.")
                raise PlayerTimeoutError(f"Timeout bei '{request_type}' für Spieler {self.name}")

            if self.interrupt_event in done:
                # Interrupt
                elapsed = time.monotonic() - start_time
                logger.info(f"Client {self.name}: Warten auf '{request_type}' nach {elapsed:.1f}s unterbrochen aufgrund Interrupt-Event.")
                raise PlayerInterruptError()

            # Antwort erhalten
            assert response_future in done
            response_data = response_future.result()  # Das ist das Payload-Dict von receive_response
            logger.debug(f"Client {self.name}: Antwort für '{request_type}' erfolgreich empfangen.")
            return response_data  # Erfolg! Gib rohen Payload zurück.

        except asyncio.CancelledError as e:  # Shutdown
            logger.info(f"Client {self.name}: Warten auf '{request_type}' extern abgebrochen.")
            raise e
        except ClientDisconnectedError as e:
            logger.info(f"Client {self.name}: Verbindungsabbruch. Warten auf '{request_type}' abgebrochen.")
            raise e
        except Exception as e:
            logger.exception(f"Client {self.name}: Kritischer Fehler während des Wartens auf '{request_type}': {e}")
            raise PlayerInteractionError(f"Unerwarteter Fehler bei '{request_type}': {e}") from e
        finally:
            # --- 6. Aufräumen ---
            logger.debug(f"Client {self.name}: Räume Warte-Tasks für '{request_type}' auf.")
            for task in pending:
                if not task.done():
                    task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=0.1)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
                except Exception as cleanup_e:
                    logger.error(f"Fehler beim Aufräumen von Task {task.get_name()}: {cleanup_e}")
            # Entferne die Future für diese Anfrage aus dem Tracking
            # noinspection PyAsyncCall
            self._pending_requests.pop(request_type, None)

    # ------------------------------------------------------
    # Entscheidungen
    # ------------------------------------------------------

    async def schupf(self, pub: PublicState, priv: PrivateState) -> Tuple[Card, Card, Card]:
        """
        Fordert den Spieler auf, drei Karten zum Schupfen auszuwählen.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Karten (Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner).
        """
        # TODO: Implementieren!
        return (13, 4), (5, 3), (2, 1)

    # todo grand? Steht nicht in der Dokumentation!
    async def announce(self, pub: PublicState, priv: PrivateState, grand: bool = False) -> bool:
        """
        Fragt den Spieler, ob er Tichu (oder Grand Tichu) ansagen möchte.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :param grand: True, wenn nach Grand Tichu gefragt wird, False für kleines Tichu.
        :return: True, wenn angesagt wird, sonst False.
        """
        # TODO: Implementieren!
        return False

    # TODO todo action_space? Steht nicht in der Dokumentation!
    async def play(self, pub: PublicState, priv: PrivateState, action_space: List[Tuple[Cards, Combination]]) -> Tuple[Cards, Combination]:
        """
        Fordert den Spieler auf, eine gültige Kartenkombination auszuwählen oder zu passen.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :param action_space: Mögliche Kombinationen (inklusive Passen; wenn Passen erlaubt ist, steht Passen an erster Stelle).
        :return: Die ausgewählte Kombination (Karten, (Typ, Länge, Wert)) oder Passen ([], (0,0,0))
        """
        # TODO: Implementieren!
        return action_space[self._random.integer(0, len(action_space))]

    async def wish(self, pub: PublicState, priv: PrivateState) -> int:
        """
        Fragt den Spieler nach einem Kartenwert-Wunsch (nach Ausspielen des Mah Jong).

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Der gewünschte Kartenwert (2-14).
        """
        # TODO: Implementieren!
        return self._random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])

    async def give_dragon_away(self, pub: PublicState, priv: PrivateState) -> int:
        """
        Fragt den Spieler, welchem Gegner der mit dem Drachen gewonnene Stich gegeben werden soll.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Der Index (0-3) des Gegners, der den Stich erhält.
        """
        # TODO: Implementieren!
        return self.opponent_left_index

    # ------------------------------------------------------
    # Hilfsfunktionen
    # ------------------------------------------------------

    def set_websocket(self, new_websocket: WebSocketResponse):
        """
        Übernimmt die WebSocket-Verbindung.

        :param new_websocket: Das neue WebSocketResponse-Objekt.
        """
        # Über die alte Verbindung noch Anfragen offen sind, diese verwerfen.
        for request_type, future in list(self._pending_requests.items()):
            if not future.done():
                logger.warning(f"Client {self._name}: Breche alte Anfrage '{request_type}' ab.")
                future.cancel()
            self._pending_requests.pop(request_type, None)

        # WEbSocket übernehmen
        logger.info(f"Aktualisiere WebSocket für Client {self._name} ({self._session_id}).")
        self._websocket = new_websocket

    # ------------------------------------------------------
    # Eigenschaften
    # ------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        """
        Gibt zurück, ob der Client aktuell verbunden ist.

        :return: True, wenn verbunden, sonst False.
        """
        return not self._websocket.closed
