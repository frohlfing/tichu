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
from src.lib.combinations import Combination
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

    async def _ask(self, action: str, pub: PublicState, priv: PrivateState) -> dict | None:
        """
        Sendet eine Anfrage an den Client und wartet auf dessen Antwort.

        :param action: Aktion (z.B. "play", "schupf"), die der Spieler ausführen soll.
        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
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
                "public_state": pub.to_dict(),
                "private_state": priv.to_dict(),
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

    # ------------------------------------------------------
    # Proaktive Nachrichten vom Server an den Spieler
    # ------------------------------------------------------

    async def welcome(self, pub: PublicState, priv: PrivateState) -> bool:
        """
        Der Server ruft diese Funktion auf, nachdem der Spieler sich angemeldet und einen Sitzplatz erhalten hat (auch nach einem Reconnect).

        Die Nachricht wird über die WebSocket-Verbindung an den realen Spieler weitergeleitet.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :result: True, wenn der Spieler erfolgreich begrüßt wurde, sonst False.
        """
        if self._websocket.closed:
            logger.debug(f"Die Begrüßungsnachricht konnte nicht an {self._name} übermittelt werden. Keine Verbindung.")
            return False

        welcome_message = {
            "type": "welcome",
            "payload": {
                "session_id": self._session_id,
                "public_state": pub.to_dict(),
                "private_state": priv.to_dict()
            }
        }

        try:
            logger.debug(f"Sende Begrüßungsnachricht an {self._name}: {welcome_message}")
            await self._websocket.send_json(welcome_message)
        except (ConnectionResetError, asyncio.CancelledError, RuntimeError, ConnectionAbortedError) as e:
            logger.warning(f"Senden der Begrüßungsnachricht an {self._name} fehlgeschlagen: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unerwarteter Fehler beim Senden der Begrüßungsnachricht an {self._name}: {e}")
            return False

        return True

    async def deal_cards(self, hand_cards: Cards):
        """
        Der Server ruft diese Funktion auf, wenn die Handkarten ausgeteilt wurden.

        Die Nachricht wird über die WebSocket-Verbindung an den realen Spieler weitergeleitet.

        :param hand_cards: Die Handkarten des Spielers.
        """
        if self._websocket.closed:
            logger.debug(f"Die aufzunehmenden Tauschkarten konnten nicht an {self._name} übermittelt werden. Keine Verbindung.")
            return

        deal_cards_message = {
            "type": "deal_cards",
            "payload": {
                "hand_cards": stringify_cards(hand_cards),
            }
        }

        try:
            logger.debug(f"Sende Handkarten an {self._name}: {deal_cards_message}")
            await self._websocket.send_json(deal_cards_message)
        except (ConnectionResetError, asyncio.CancelledError, RuntimeError, ConnectionAbortedError) as e:
            logger.warning(f"Senden der Handkarten an {self._name} fehlgeschlagen: {e}")
        except Exception as e:
            logger.exception(f"Unerwarteter Fehler beim Senden der Handkarten an {self._name}: {e}")

    async def deal_schupf_cards(self, from_opponent_right: Card, from_partner: Card, from_opponent_left: Card):
        """
        Der Server ruft diese Funktion auf, wenn die Schupfkarten ausgetauscht wurden.

        Die Nachricht wird über die WebSocket-Verbindung an den realen Spieler weitergeleitet.

        :param from_opponent_right: Die Karte für den rechten Gegner.
        :param from_partner: Die Karte für den Partner.
        :param from_opponent_left: Die Karte für den linken Gegner.
        """
        if self._websocket.closed:
            logger.debug(f"Die aufzunehmenden Tauschkarten konnten nicht an {self._name} übermittelt werden. Keine Verbindung.")
            return

        deal_schupf_message = {
            "type": "deal_schupf_cards",
            "payload": {
                "from_opponent_right": stringify_card(from_opponent_right),
                "from_partner": stringify_card(from_partner),
                "from_opponent_left": stringify_card(from_opponent_left),
            }
        }

        try:
            logger.debug(f"Sende Tauschkarten an {self._name}: {deal_schupf_message}")
            await self._websocket.send_json(deal_schupf_message)
        except (ConnectionResetError, asyncio.CancelledError, RuntimeError, ConnectionAbortedError) as e:
            logger.warning(f"Senden der Tauschkarten an {self._name} fehlgeschlagen: {e}")
        except Exception as e:
            logger.exception(f"Unerwarteter Fehler beim Senden der Tauschkarten an {self._name}: {e}")

    # --- Anfragen (diese Nachrichten erwarten eine Antwort vom Spieler ---

    async def schupf(self, pub: PublicState, priv: PrivateState) -> Tuple[Card, Card, Card]:
        """
        Der Server fordert den Spieler auf, drei Karten zum Schupfen auszuwählen.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Karten (Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner).
        """
        # TODO: Implementieren!
        return (13, 4), (5, 3), (2, 1)

    async def announce(self, pub: PublicState, priv: PrivateState) -> bool:
        """
        Der Server fragt den Spieler, ob er Tichu (oder Grand Tichu) ansagen möchte.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: True, wenn angesagt wird, sonst False.
        """
        #grand = pub.current_phase == "dealing" and len(priv.hand_cards) == 8
        response_payload = await self._ask(action="announce", pub=pub, priv=priv)
        if response_payload and isinstance(response_payload.get("announced"), bool):
            return response_payload["announced"]
        else:
            logger.error(f"Client {self.name}: Ungültige Antwort für Anfrage \"announce\": {response_payload}")
            await self.error("Ungültige Antwort für Anfrage \"announce\"", ErrorCode.INVALID_MESSAGE, context=response_payload)
            return False  # Fallback

    # TODO todo action_space? Steht nicht in der Dokumentation!
    async def play(self, pub: PublicState, priv: PrivateState, action_space: List[Tuple[Cards, Combination]]) -> Tuple[Cards, Combination]:
        """
        Der Server fordert den Spieler auf, eine gültige Kartenkombination auszuwählen oder zu passen.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :param action_space: Mögliche Kombinationen (inklusive Passen; wenn Passen erlaubt ist, steht Passen an erster Stelle).
        :return: Die ausgewählte Kombination (Karten, (Typ, Länge, Wert)) oder Passen ([], (0,0,0))
        """
        # TODO: Implementieren!
        return action_space[self._random.integer(0, len(action_space))]

    async def wish(self, pub: PublicState, priv: PrivateState) -> int:
        """
        Der Server fragt den Spieler nach einem Kartenwert-Wunsch (nach Ausspielen des Mah Jong).

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Der gewünschte Kartenwert (2-14).
        """
        # TODO: Implementieren!
        return self._random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])

    async def give_dragon_away(self, pub: PublicState, priv: PrivateState) -> int:
        """
        Der Server fragt den Spieler, welchem Gegner der mit dem Drachen gewonnene Stich gegeben werden soll.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Der Index (0-3) des Gegners, der den Stich erhält.
        """
        # TODO: Implementieren!
        return self.opponent_left_index

    # --- Broadcast-Nachricht (diese Nachricht wird an jeden Spieler gesendet) ----

    async def notify(self, event: str, context: Optional[dict]=None):
        """
        Der Server ruft diese Funktion auf, um ein Spielereignis zu melden.

        Die Nachricht wird über die WebSocket-Verbindung an den realen Spieler weitergeleitet.

        :param event: Das Spielereignis.
        :param context: (Optional) Zusätzliche Informationen zum Ereignis.
        """
        if self._websocket.closed:
            logger.debug(f"Das Ereignis {event} an {self._name} konnte nicht übermittelt werden. Keine Verbindung.")
            return

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

    # --- Fehlermeldung ---

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
    # Hilfsfunktionen
    # ------------------------------------------------------

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
    # Eigenschaften
    # ------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        """
        Gibt zurück, ob der Client aktuell verbunden ist.

        :return: True, wenn verbunden, sonst False.
        """
        return not self._websocket.closed
