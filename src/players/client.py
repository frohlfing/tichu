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
from src.lib.cards import Card, Cards, stringify_cards, parse_cards, stringify_card
from src.lib.combinations import Combination, build_action_space, CombinationType
# noinspection PyUnresolvedReferences
from src.lib.errors import ClientDisconnectedError, PlayerInteractionError, PlayerInterruptError, PlayerTimeoutError, PlayerResponseError, ErrorCode
from src.players.player import Player
from src.private_state import PrivateState
from src.public_state import PublicState
from typing import Optional, Dict, List, Tuple
from uuid import uuid4


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

    def set_websocket(self, new_websocket: WebSocketResponse):
        """
        Übernimmt die WebSocket-Verbindung.

        :param new_websocket: Das neue WebSocketResponse-Objekt.
        """
        # Über die alte Verbindung noch Anfragen offen sind, diese verwerfen.
        for request_id, future in list(self._pending_requests.items()):
            if not future.done():
                logger.warning(f"Client {self._name}: Breche alte Anfrage '{request_id}' ab.")
                future.cancel()
            self._pending_requests.pop(request_id, None)

        # WebSocket übernehmen
        logger.info(f"Aktualisiere WebSocket für Client {self._name} ({self._session_id}).")
        self._websocket = new_websocket

    # ------------------------------------------------------
    # Entscheidungen
    # ------------------------------------------------------

    async def _ask(self, action: str) -> dict | None:
        """
        Sendet eine Anfrage an den Client und wartet auf dessen Antwort.

        :param action: Aktion (z.B. "play", "schupf"), die der Spieler ausführen soll.
        :return: Die Antwort des Clients (`response_data`).
        :raises ClientDisconnectedError: Wenn der Client nicht verbunden ist.
        :raises PlayerInterruptError: Wenn die Anfrage durch ein Engine-Event unterbrochen wird.
        :raises PlayerTimeoutError: Wenn der Client nicht innerhalb des Timeouts antwortet.
        :raises asyncio.CancelledError: Wenn der wartende Task extern abgebrochen wird.
        :raises PlayerInteractionError: Bei anderen Fehlern während des Sendevorgangs oder Wartens.
        """
        # sicherstellen, dass der Client noch verbunden ist
        if self._websocket.closed:
            #logger.warning(f"Client {self.name}: Aktion '{action}' nicht möglich (nicht verbunden).")
            raise ClientDisconnectedError(f"Client {self.name} ist nicht verbunden.")

        logger.debug(f"Client {self.name}: Starte Anfrage '{action}'.")

        # Future erstellen und registrieren
        loop = asyncio.get_running_loop()
        request_id = str(uuid4())
        response_future = loop.create_future()
        self._pending_requests[request_id] = response_future

        # Anfrage senden
        request_message: dict = {
            "type": "request",
            "payload": {
                "request_id": request_id,
                "action": action,
                "public_state": self.pub.to_dict(),
                "private_state": self.priv.to_dict(),
            }
        }
        try:
            logger.debug(f"Sende Anfrage an {self.name}: {request_message}")
            await self._websocket.send_json(request_message)
        except (ConnectionResetError, asyncio.CancelledError, RuntimeError, ConnectionAbortedError) as e:
            logger.warning(f"Senden der Anfrage '{action}' an {self.name} fehlgeschlagen (Verbindungsfehler): {e}. Markiere als getrennt.")
            # noinspection PyAsyncCall
            self._pending_requests.pop(request_id, None)  # Future entfernen
            raise ClientDisconnectedError(f"Senden der Anfrage '{action}' fehlgeschlagen.") from e
        except Exception as e:
            logger.exception(f"Unerwarteter Fehler beim Senden der Anfrage '{action}' an {self.name}: {e}")
            # noinspection PyAsyncCall
            self._pending_requests.pop(request_id, None)  # Future entfernen
            raise PlayerInteractionError(f"Fehler beim Senden der Anfrage '{action}': {e}") from e

        # auf Antwort warten
        interrupt_task = asyncio.create_task(self.interrupt_event.wait(), name="Interrupt")
        wait_tasks: List[asyncio.Future | asyncio.Task] = [response_future, interrupt_task]
        pending: set[asyncio.Future | asyncio.Task] = set()
        start_time = time.monotonic()
        try:
            done, pending = await asyncio.wait(wait_tasks, timeout=config.DEFAULT_REQUEST_TIMEOUT, return_when=asyncio.FIRST_COMPLETED)

            # Ergebnis auswerten
            if not done:
                # Timeout
                elapsed = time.monotonic() - start_time
                logger.warning(f"Client {self.name}: Timeout ({elapsed:.1f}s > {config.DEFAULT_REQUEST_TIMEOUT}s) beim Warten auf Antwort für '{action}'.")
                raise PlayerTimeoutError(f"Timeout bei '{action}' für Spieler {self.name}")

            if interrupt_task in done:
                # Interrupt
                self.interrupt_event.clear()  # Wichtig: Event zurücksetzen!
                elapsed = time.monotonic() - start_time
                logger.info(f"Client {self.name}: Warten auf '{action}' nach {elapsed:.1f}s unterbrochen aufgrund Interrupt-Event.")
                raise PlayerInterruptError(f"Aktion '{action}' unterbrochen.")

            # Antwort erhalten
            assert response_future in done
            response_data = response_future.result()
            logger.debug(f"Client {self.name}: Antwort für '{action}' erfolgreich empfangen: {response_data}.")
            return response_data  # Erfolg!

        except asyncio.CancelledError as e:  # Shutdown
            logger.info(f"Client {self.name}: Warten auf '{action}' extern abgebrochen.")
            raise e
        except ClientDisconnectedError as e:
            logger.info(f"Client {self.name}: Verbindungsabbruch. Warten auf '{action}' abgebrochen.")
            raise e
        except Exception as e:
            logger.exception(f"Client {self.name}: Kritischer Fehler während des Wartens auf '{action}': {e}")
            raise PlayerInteractionError(f"Unerwarteter Fehler bei '{action}': {e}") from e
        finally:
            logger.debug(f"Client {self.name}: Räume Warte-Tasks für '{action}' auf.")
            for task in pending:
                if not task.done():
                    task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=0.1)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
                except Exception as cleanup_e:
                    logger.error(f"Fehler beim Aufräumen von Task {task.get_name()}: {cleanup_e}")
            # noinspection PyAsyncCall
            self._pending_requests.pop(request_id, None)

    async def on_websocket_response(self, request_id: str, response_data: dict):
        """
        Wird aufgerufen, wenn eine Antwort vom realen Spieler empfangen wurde.

        :param request_id:  Die UUID der Anfrage.
        :param response_data: Die Daten der Antwort.
        """
        future = self._pending_requests.pop(request_id, None)  # hole und entferne die Future aus _pending_requests
        if future:
            if not future.done():  # _ask() wartet noch auf die Antwort
                future.set_result(response_data)  # dadurch erhält _ask() die Daten der Antwort und kann weitermachen
                logger.debug(f"Client {self._name}: Antwort an wartende Methode weitergeleitet (Request-ID {request_id}).")
            else:  # _ask() hat inzwischen das Warten auf diese Antwort aufgegeben (wegen Timeout, Interrupt oder Server beenden)
                logger.warning(f"Client {self._name}: Antwort ist veraltet (Request-ID {request_id}).")
                # todo Fehler an den Spieler senden
        else:  # keine wartende Anfrage für diese Antwort gefunden
            logger.warning(f"Client {self._name}: Keine wartende Anfrage für diese Antwort gefunden (Request-ID {request_id}).")
            # todo Fehler an den Spieler senden

    async def announce(self) -> bool:
        """
        Fragt den Spieler, ob er ein Tichu (normales oder großes) ansagen möchte.

        :return: True, wenn angesagt wird, sonst False.
        """
        #grand = pub.start_player_index == -1 and len(priv.hand_cards) == 8
        response_payload = await self._ask(action="announce_tichu")
        if response_payload and isinstance(response_payload.get("announced"), bool):
            return response_payload["announced"]
        else:
            logger.error(f"Client {self.name}: Ungültige Antwort für Anfrage \"announce_tichu\": {response_payload}")
            await self.error("Ungültige Antwort für Anfrage \"announce_tichu\"", ErrorCode.INVALID_MESSAGE, context=response_payload)
            return False  # Fallback

    async def schupf(self) -> Tuple[Card, Card, Card]:
        """
        Der Server fordert den Spieler auf, drei Karten zum Schupfen auszuwählen.

        Diese Aktion kann durch ein Interrupt abgebrochen werden.

        :return: Karten (Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner).
        """
        # TODO: Implementieren!
        return (13, 4), (5, 3), (2, 1)

    async def play(self) -> Tuple[Cards, Combination]:
        """
        Der Server fordert den Spieler auf, eine gültige Kartenkombination auszuwählen oder zu passen.

        Diese Aktion kann durch ein Interrupt abgebrochen werden.

        :return: Die ausgewählte Kombination (Karten, (Typ, Länge, Wert)) oder Passen ([], (0,0,0))
        """
        # TODO: Implementieren!

        # mögliche Kombinationen (inklusive Passen; wenn Passen erlaubt ist, steht Passen an erster Stelle)
        action_space = build_action_space(self.priv.combinations, self.pub.trick_combination, self.pub.wish_value)

        return action_space[self._random.integer(0, len(action_space))]

    async def bomb(self) -> Optional[Tuple[Cards, Combination]]:
        """
        Fragt den Spieler, ob er eine Bombe werfen will, und wenn ja, welche.

        Die Engine ruft diese Methode nur auf, wenn eine Bombe vorhanden ist.

        :return: Die ausgewählte Bombe (Karten, (Typ, Länge, Wert)) oder None, wenn keine Bombe geworfen wird.
        """
        # TODO: Implementieren!
        if not self._random.choice([True, False], [1, 2]):  # einmal Ja, zweimal Nein
            return None
        combinations = [combi for combi in self.priv.combinations if combi[1][0] == CombinationType.BOMB]
        action_space = build_action_space(combinations, self.pub.trick_combination, self.pub.wish_value)
        return action_space[self._random.integer(0, len(action_space))]

    async def wish(self) -> int:
        """
        Der Server fragt den Spieler nach einem Kartenwert-Wunsch (nach Ausspielen des Mah Jong).

        :return: Der gewünschte Kartenwert (2-14).
        """
        # TODO: Implementieren!
        return self._random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])

    async def give_dragon_away(self) -> int:
        """
        Der Server fragt den Spieler, welchem Gegner der mit dem Drachen gewonnene Stich gegeben werden soll.

        :return: Der Index (0-3) des Gegners, der den Stich erhält.
        """
        # TODO: Implementieren!
        return self.priv.opponent_left_index

    # ------------------------------------------------------
    # Benachrichtigungen
    # ------------------------------------------------------

    async def notify(self, event: str, context: Optional[dict] = None):
        """
        Der Server ruft diese Funktion auf, um ein Spielereignis zu melden.

        Die Nachricht wird über die WebSocket-Verbindung an den realen Spieler weitergeleitet.

        :param event: Das Spielereignis.
        :param context: (Optional) Zusätzliche Informationen zum Ereignis.
        """
        if self._websocket.closed:
            logger.debug(f"Das Ereignis {event} an {self._name} konnte nicht übermittelt werden. Keine Verbindung.")
            return

        if event == "player_joined":
            if context.get("player_index") == self.priv.player_index:
                context = {
                    "session_id": self._session_id,
                    "public_state": self.pub.to_dict(),
                    "private_state": self.priv.to_dict()
                }

        elif event == "hand_cards_dealt":
            assert context.get("count") == len(self.priv.hand_cards)
            context = {"hand_cards": stringify_cards(self.priv.hand_cards)}

        elif event == "schupf_cards_dealt":
            context = {"received_schupf_cards": stringify_cards(self.priv.received_schupf_cards)}

        notification_message = {
            "type": "notification",
            "payload": {
                "event": event,
                "context": context if context else {},
            }
        }

        try:
            logger.debug(f"Sende Nachricht an {self._name}: {notification_message}")
            await self._websocket.send_json(notification_message)
        except (ConnectionResetError, asyncio.CancelledError, RuntimeError, ConnectionAbortedError) as e:
            logger.warning(f"Melden des Ereignisses {event} an {self._name} fehlgeschlagen: {e}")
        except Exception as e:
            logger.exception(f"Unerwarteter Fehler beim Melden des Ereignisses {event} an {self._name}: {e}")

    async def error(self, message: str, code: ErrorCode, context: Optional[Dict] = None):
        """
        Der Server ruft diese Funktion auf, um einen Fehler zu melden.

        Die Fehlermeldung wird über die WebSocket-Verbindung an den realen Spieler weitergeleitet.

        :param message: Die Fehlermeldung.
        :param code: Der Fehlercode.
        :param context: (Optional) Zusätzliche Informationen.
        """
        if self._websocket.closed:
            logger.debug(f"Fehlermeldung {code} an {self._name} konnte nicht übermittelt werden. Keine Verbindung.")
            return

        error_message = {
            "type": "error",
            "payload": {
                "message": message,
                "code": code,
                "context": context if context else {},
            }
        }

        try:
            logger.debug(f"Sende Fehlermeldung an {self._name}: {error_message} ({code})")
            await self._websocket.send_json(error_message)
        except (ConnectionResetError, asyncio.CancelledError, RuntimeError, ConnectionAbortedError) as e:
            logger.warning(f"Senden der Fehlermeldung {code} an {self._name} fehlgeschlagen: {e}")
        except Exception as e:
            logger.exception(f"Unerwarteter Fehler beim Senden der Fehlermeldung {code} an {self._name}: {e}")

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
