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
from src.lib.cards import Card, Cards, stringify_cards, deck, CARD_MAH, CardSuit
from src.lib.combinations import Combination, build_action_space, CombinationType, FIGURE_DRA
# noinspection PyUnresolvedReferences
from src.lib.errors import ClientDisconnectedError, PlayerInteractionError, PlayerInterruptError, PlayerTimeoutError, PlayerResponseError, ErrorCode
from src.players.player import Player
from typing import Optional, Dict, List, Tuple
from uuid import uuid4


class Peer(Player):
    """
    Repräsentiert den serverseitigen Endpunkt der WebSocket-Verbindung zu einem verbundenen Client.

    Dieser Client kann ein menschlicher Spieler sein (der z.B. über einen Browser interagiert) oder
    potenziell auch ein anderer Bot, der das definierte Tichu-Protokoll spricht.
    """

    def __init__(self, name: str,
                 websocket: WebSocketResponse,
                 session_id: Optional[str] = None,
                 seed: Optional[int] = None):
        """
        Initialisiert einen neuen Peer.

        :param name: Der Name des Spielers.
        :param websocket: Das WebSocketResponse-Objekt der initialen Verbindung.
        :param session_id: (Optional) Aktuelle Session des Spielers. Wenn None, wird eine Session generiert.
        :param seed: (Optional) Seed für den internen Zufallsgenerator (für Tests).
        """
        super().__init__(name, session_id=session_id)
        self._websocket = websocket
        self._random = Random(seed)  # Zufallsgenerator
        self._new_websocket_event = asyncio.Event()
        self._pending_requests: Dict[str, asyncio.Future] = {}  # die noch vom Client unbeantworteten Anfragen
        self._pending_announce: Optional[bool] = None  # die noch vom Server abzuholende Tichu-Ansage
        self._pending_bomb: Optional[Cards] = None  # die noch vom Server abzuholende Bombe todo in Type Optional[bool] ändern

    async def cleanup(self):
        """
        Bereinigt Ressourcen dieser Instanz.

        Versucht, die WebSocket-Verbindung serverseitig aktiv und sauber zu schließen.
        """
        # WebSocket schließen
        if self._websocket and not self._websocket.closed:
            logger.info(f"[{self._name}] Schließe WebSocket.")
            try:
                await self._websocket.close(code=WSCloseCode.GOING_AWAY, message="Verbindung wird geschlossen".encode('utf-8'))
            except Exception as e:
                logger.exception(f"[{self._name}] Fehler beim Schließen der WebSocket': {e}")

        self._new_websocket_event.set()

        # Offene Anfragen verwerfen.
        self._cancel_pending_requests()

    def reset_round(self):  # pragma: no cover
        """
        Setzt spielrundenspezifische Werte zurück.
        """
        #self._cancel_pending_requests()
        assert self._pending_requests == {}
        assert self._pending_announce is None
        assert self._pending_bomb is None

    def _cancel_pending_requests(self):
        """
        Offene Anfragen verwerfen.
        """
        for request_id, future in list(self._pending_requests.items()):
            if not future.done():
                future.set_result(None)
        self._pending_requests = {}
        self._pending_announce = None
        self._pending_bomb = None

    def set_websocket(self, new_websocket: WebSocketResponse):
        """
        Übernimmt die WebSocket-Verbindung.

        :param new_websocket: Das neue WebSocketResponse-Objekt.
        """
        # WebSocket übernehmen
        logger.debug(f"[{self._name}] Aktualisiere WebSocket.")
        self._websocket = new_websocket
        self._new_websocket_event.set()

    async def wait_for_reconnect(self, timeout: float):
        """
        Wartet auf eine WebSocket-Verbindung.

        :param timeout: Maximale Wartezeit in Sekunden.
        :return: True, wenn der Peer verbunden wurde.
        """
        try:
            await asyncio.wait_for(self._new_websocket_event.wait(), timeout=timeout)
            self._new_websocket_event.clear()
            return self.is_connected
        except asyncio.TimeoutError:
            return False

    # ------------------------------------------------------
    # Entscheidungen
    # ------------------------------------------------------

    async def client_announce(self):
        """
        Der WebSocket-Handler ruft diese Funktion auf, wenn der Client ein einfaches Tichu angesagt hat.
        """
        if self.pub.count_hand_cards[self.priv.player_index] != 14 or self.pub.announcements[self.priv.player_index]:
            # Spieler hat schon Karten ausgespielt oder bereits Tichu angesagt
            msg = "Tichu-Ansage abgelehnt."
            logger.warning(f"[{self._name}] {msg}")
            await self.error(msg, ErrorCode.INVALID_ANNOUNCE)
            return

        self._pending_announce = True
        self.interrupt_event.set()

    async def client_bomb(self, cards: Cards):
        """
        Der WebSocket-Handler ruft diese Funktion auf, wenn der Client außerhalb seines regulären Zuges eine Bombe geworfen hat.

        todo Der Client kündigt die Bombe nur an. Welche Bombe es ist, wird explizit gefragt, sobald er am Zug ist.

        :param cards: Die Karten, aus denen die Bombe gebildet wurde. Werden absteigend sortiert (mutable!).
        """
        # Parameter ok?
        if not isinstance(cards, list):
            msg = "Ungültige Parameter für \"bomb\""
            logger.warning(f"[{self._name}] {msg}: {cards}")
            await self.error(msg, ErrorCode.INVALID_MESSAGE, context={"cards": cards})
            return

        # Karten valide?
        if any(card not in deck for card in cards):
            msg = "Mindestens eine Karte ist unbekannt"
            logger.warning(f"[{self._name}] {msg}: {cards}")
            await self.error(msg, ErrorCode.UNKNOWN_CARD, context={"cards": cards})
            return

        # Sind die Karten unterschiedlich?
        if len(set(cards)) != len(cards):
            msg = "Mindestens zwei Karten sind identisch"
            logger.warning(f"[{self._name}] {msg}: {stringify_cards(cards)}")
            await self.error(msg, ErrorCode.NOT_UNIQUE_CARDS, context={"cards": cards})
            return

        # Sind die Karten auf der Hand?
        if any(card not in self.priv.hand_cards for card in cards):
            msg = "Mindestens eine Karte ist keine Handkarte"
            logger.warning(f"[{self._name}] {msg}: {stringify_cards(cards)}")
            await self.error(msg, ErrorCode.NOT_HAND_CARD, context={"cards": cards})
            return

        # Kombination der Bombe ermitteln. Ist sie spielbar?
        combination = None
        action_space = build_action_space(self.priv.combinations, self.pub.trick_combination, self.pub.wish_value)
        for playable_cards, playable_combination in action_space:
            if playable_combination[0] == CombinationType.BOMB and set(cards) == set(playable_cards):
                combination = playable_combination
                break
        if combination is None:
            msg = "Die Karten bilden keine spielbare Bombe"
            logger.warning(f"[{self._name}] {msg}: {stringify_cards(cards)}")
            await self.error(msg, ErrorCode.INVALID_COMBINATION, context={"cards": cards})
            return

        self._pending_bomb = cards  # todo nur True zuweisen
        self.interrupt_event.set()

    async def client_response(self, request_id: str, response_data: dict):
        """
        Der WebSocket-Handler ruft diese Funktion auf, wenn der Client eine Anfrage beantwortet hat.

        :param request_id:  Die UUID der Anfrage.
        :param response_data: Die Daten der Antwort.
        """
        future = self._pending_requests.pop(request_id, None)  # hole und entferne die Future aus _pending_requests
        if not future:  # keine wartende Anfrage für diese Antwort gefunden
            msg = "Keine wartende Anfrage für diese Antwort gefunden"
            logger.warning(f"[{self._name}] {msg}; Request-ID {request_id}.")
            await self.error(msg, ErrorCode.INVALID_RESPONSE, context={"request_id": request_id})
            return
        if future.done():  # _ask() hat inzwischen das Warten auf diese Antwort aufgegeben (wegen Timeout, Interrupt oder Server beenden)
            msg = "Anfrage ist veraltet"
            logger.warning(f"[{self._name}] {msg}; Request-ID: {request_id}.")
            await self.error(msg, ErrorCode.REQUEST_OBSOLETE, context={"request_id": request_id})
            return
        # die Daten mittels Future an _ask() übergeben
        future.set_result(response_data)
        logger.debug(f"[{self._name}] Antwort an wartende Methode übergeben; Request-ID {request_id}.")

    async def _ask(self, action: str, context: Optional[dict] = None, interruptable: bool = False) -> dict | None:
        """
        Sendet eine Anfrage an den Client und wartet auf dessen Antwort.

        :param action: Aktion (z.B. "play", "schupf"), die der Spieler ausführen soll.
        :param context: (Optional) Zusätzliche Informationen zum Ereignis.
        :param interruptable: (Optional) Wenn True, kann die Anfrage durch ein Interrupt abgebrochen werden.
        :return: Die Antwort des Clients (`response_data`), oder None nach Kick-Out.
        :raises asyncio.CancelledError: Bei Shutdown.
        :raises PlayerInterruptError: Wenn die Anfrage durch ein Interrupt-Event abgebrochen wurde.
        """
        # sicherstellen, dass der Client noch verbunden ist
        if self._websocket.closed:
            logger.warning(f"[{self._name}] Keine Verbindung. Anfrage '{action}' nicht möglich.")
            return None

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
                "context": context if context else {},
            }
        }
        try:
            logger.debug(f"[{self._name}] Sende Anfrage '{action}'.")
            #logger.debug(f"[{self._name}] Sende Anfrage: {request_message}")
            await self._websocket.send_json(request_message)
        except asyncio.CancelledError as e_cancel:  # Shutdown
            raise e_cancel
        except (ConnectionResetError, RuntimeError, ConnectionAbortedError) as e:
            logger.warning(f"[{self._name}] Verbindungsfehler. Senden der Anfrage '{action}' fehlgeschlagen: {e}.")
            # noinspection PyAsyncCall
            self._pending_requests.pop(request_id, None)  # Future entfernen
            return None
        except Exception as e:
            logger.exception(f"[{self._name}] Unerwarteter Fehler. Senden der Anfrage '{action}' fehlgeschlagen: {e}")
            # noinspection PyAsyncCall
            self._pending_requests.pop(request_id, None)  # Future entfernen
            return None

        # Warte-Tasks anlegen
        if interruptable:
            interrupt_task = asyncio.create_task(self.interrupt_event.wait(), name="Interrupt")
            wait_tasks: List[asyncio.Future | asyncio.Task] = [response_future, interrupt_task]
        else:
            interrupt_task = None
            wait_tasks: List[asyncio.Future | asyncio.Task] = [response_future]
        pending: set[asyncio.Future | asyncio.Task] = set()

        # auf Antwort warten
        start_time = time.monotonic()
        try:
            done, pending = await asyncio.wait(wait_tasks, timeout=config.DEFAULT_REQUEST_TIMEOUT, return_when=asyncio.FIRST_COMPLETED)

            # Timeout?
            if not done:
                elapsed = time.monotonic() - start_time
                logger.warning(f"[{self._name}] Timeout ({elapsed:.1f}s > {config.DEFAULT_REQUEST_TIMEOUT}s). Warten auf Antwort '{action}' abgebrochen.")
                return None

            # Interrupt?
            if interruptable and interrupt_task in done:
                self.interrupt_event.clear()  # Wichtig: Event zurücksetzen!
                logger.info(f"[{self._name}] Interrupt. Warten auf Antwort '{action}' abgebrochen.")
                raise PlayerInterruptError(f"Aktion '{action}' unterbrochen.")

            # Antwort erhalten!
            assert response_future in done
            response_data = response_future.result()
            logger.debug(f"[{self._name}] Antwort '{action}' erfolgreich empfangen: {response_data}.")
            return response_data  # Erfolg!

        except asyncio.CancelledError as e:  # Shutdown
            logger.info(f"[{self._name}] Shutdown. Warten auf Antwort '{action}' abgebrochen.")
            raise e
        except ClientDisconnectedError:
            logger.info(f"[{self._name}] Verbindungsabbruch. Warten auf Antwort '{action}' abgebrochen.")
            return None
        except Exception as e:
            logger.exception(f"[{self._name}] Unerwarteter Fehler. Wartens auf Antwort '{action}' abgebrochen: {e}")
            return None
        finally:
            logger.debug(f"[{self._name}] Räume Warte-Task für '{action}' auf.")
            for task in pending:
                if not task.done():
                    task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=0.1)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
                except Exception as cleanup_e:
                    logger.exception(f"[{self._name}] Fehler beim Aufräumen von Task {task.get_name()}: {cleanup_e}")
            # noinspection PyAsyncCall
            self._pending_requests.pop(request_id, None)

    async def announce_grand_tichu(self) -> bool:
        """
        Die Engine fragt den Spieler, ob er ein großes Tichu ansagen möchte.

        Die Engine ruft diese Methode nur auf, wenn der Spieler noch ein großes Tichu ansagen darf.
        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        :return: True, wenn angesagt wird, sonst False.
        """
        announced = None
        while announced is None:
            response_data = await self._ask("announce_grand_tichu")

            # Fallback bei Verbindungsabbruch
            if response_data is None:
                # Heuristik: Es wird niemals großes Tichu angesagt.
                logger.debug(f"[{self._name}] Fallback-Antwort")
                return False

            # Ist der Payload ok?
            if not isinstance(response_data.get("announced"), bool):
                msg = "Ungültige Antwort für Anfrage 'announce_grand_tichu'"
                logger.warning(f"[{self._name}] {msg}: {response_data}")
                await self.error(msg, ErrorCode.INVALID_MESSAGE, context=response_data)
                continue
            # Antwort übernehmen
            announced = response_data["announced"]

        # Darf der Spieler noch ein großes Tichu sagen? (stellt die Engine sicher) todo rausnehmen
        assert self.pub.announcements[self.priv.player_index] == 0 and self.pub.start_player_index == -1 and self.pub.count_hand_cards[self.priv.player_index] == 8

        return announced

    async def announce_tichu(self) -> bool:
        """
        Die Engine fragt den Spieler, ob er ein einfaches Tichu ansagen möchte.

        Die Engine ruft diese Methode nur auf, wenn der Spieler noch ein einfaches Tichu ansagen darf.
        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        # Da der Client proaktiv (also ungefragt) ein einfaches Tichu ansagt, wird die Frage nicht an den Client
        # weitergeleitet, sondern es wird im Puffer geschaut, ob eine unbearbeitete Tichu-Ansage vorliegt.

        :return: True, wenn ein Tichu angesagt wird, sonst False.
        """
        # Liegt eine Ansage vor?
        if not self._pending_announce:
            return False

        # Ansage aus dem Puffer nehmen
        announced = self._pending_announce
        self._pending_announce = None
        assert announced == True

        # Darf der Spieler noch Tichu sagen? (stellt die Engine sicher)  todo rausnehmen
        assert (self.pub.announcements[self.priv.player_index] == 0 and
                ((self.pub.start_player_index == -1 and self.pub.count_hand_cards[self.priv.player_index] > 8) or
                 (self.pub.start_player_index >= 0 and self.pub.count_hand_cards[self.priv.player_index] == 14)))

        return announced

    async def schupf(self) -> Tuple[Card, Card, Card]:
        """
        Die Engine fordert den Spieler auf, drei Karten zum Schupfen auszuwählen.

        Die Engine ruft diese Methode nur auf, wenn der Spieler noch Karten abgeben muss.
        Die Engine verlässt sich darauf, dass die Antwort valide ist.
        Diese Aktion kann durch ein Interrupt abgebrochen werden.

        :return: Karten (Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner).
        :raises PlayerInterruptError: Wenn die Anfrage durch ein Interrupt-Event abgebrochen wurde.
        """
        cards: Optional[Tuple[Card, Card, Card]] = None
        while cards is None:
            response_data = await self._ask("schupf", {"hand_cards": self.priv.hand_cards}, interruptable=True)

            # Fallback bei Verbindungsabbruch
            if response_data is None:
                # Heuristik: Die drei rangniedrigsten Karten werden geschupft, die höchste davon an den Partner.
                logger.debug(f"[{self._name}] Fallback-Antwort")
                return self.priv.hand_cards[-1], self.priv.hand_cards[-3], self.priv.hand_cards[-2]

            # Ist der Payload ok?
            if not isinstance(response_data.get("given_schupf_cards"), list) or len(response_data.get("given_schupf_cards")) != 3:
                msg = "Ungültige Antwort für Anfrage 'schupf'"
                logger.warning(f"[{self._name}] {msg}: {response_data}")
                await self.error(msg, ErrorCode.INVALID_MESSAGE, context=response_data)
                continue

            # Label der Karten valide?
            cards = ((response_data["given_schupf_cards"][0][0], CardSuit(response_data["given_schupf_cards"][0][1])),
                     (response_data["given_schupf_cards"][1][0], CardSuit(response_data["given_schupf_cards"][1][1])),
                     (response_data["given_schupf_cards"][2][0], CardSuit(response_data["given_schupf_cards"][2][1])))
            if any(card not in deck for card in cards):
                msg = "Mindestens eine Karte ist unbekannt"
                logger.warning(f"[{self._name}] {msg}: {cards}")
                await self.error(msg, ErrorCode.UNKNOWN_CARD, context={"cards": cards})
                continue

            # Sind die Karten unterschiedlich?
            if len(set(cards)) != 3:  # todo testen!
                msg = "Mindestens zwei Karten sind identisch"
                logger.warning(f"[{self._name}] {msg}: {stringify_cards(cards)}")
                await self.error(msg, ErrorCode.NOT_UNIQUE_CARDS, context={"cards": cards})
                cards = None
                continue

            # Sind die Karten auf der Hand?
            if any(card not in self.priv.hand_cards for card in cards):
                msg = "Mindestens eine Karte ist keine Handkarte"
                logger.warning(f"[{self._name}] {msg}: {stringify_cards(cards)}")
                await self.error(msg, ErrorCode.NOT_HAND_CARD, context={"cards": cards})
                cards = None
                continue

        # Wurde noch nicht geschupft? (stellt die Engine sicher) todo rausnehmen
        assert self.pub.count_hand_cards[self.priv.player_index] > 8 and self.priv.given_schupf_cards is None

        return cards

    async def play(self) -> Tuple[Cards, Combination]:
        """
        Die Engine fordert den Spieler auf, eine gültige Kartenkombination auszuwählen oder zu passen.

        Die Engine ruft diese Methode nur auf, wenn der Spieler am Zug ist.
        Die Engine verlässt sich darauf, dass die Antwort valide ist.
        Diese Aktion kann durch ein Interrupt abgebrochen werden.

        :return: Die ausgewählte Kombination (Karten, (Typ, Länge, Rang)) oder Passen ([], (0,0,0))
        :raises PlayerInterruptError: Wenn die Anfrage durch ein Interrupt-Event abgebrochen wurde.
        """
        cards = None
        combination = None
        while combination is None:
            response_data = await self._ask("play", {
                "hand_cards": self.priv.hand_cards,
                "trick_combination": self.pub.trick_combination,
                "wish_value": self.pub.wish_value,
            }, interruptable=True)

            # Fallback bei Verbindungsabbruch
            if response_data is None:
                # Heuristik: Die schwächste spielbare Kombination wird ausgewählt. Passen ist die letzte Option.
                logger.debug(f"[{self._name}] Fallback-Antwort")
                action_space = build_action_space(self.priv.combinations, self.pub.trick_combination, self.pub.wish_value)
                return action_space[-1]

            # Ist der Payload ok?
            if not isinstance(response_data.get("cards"), list):
                msg = "Ungültige Antwort für Anfrage 'play'"
                logger.warning(f"[{self._name}] {msg}: {response_data}")
                await self.error(msg, ErrorCode.INVALID_MESSAGE, context=response_data)
                continue

            # Karten valide?
            cards = [(card[0], CardSuit(card[1])) for card in response_data["cards"]]
            if any(card not in deck for card in cards):
                msg = "Mindestens eine Karte ist unbekannt"
                logger.warning(f"[{self._name}] {msg}: {cards}")
                await self.error(msg, ErrorCode.UNKNOWN_CARD, context={"cards": cards})
                continue

            # Sind die Karten unterschiedlich?
            if len(set(cards)) != len(cards):
                msg = "Mindestens zwei Karten sind identisch"
                logger.warning(f"[{self._name}] {msg}: {stringify_cards(cards)}")
                await self.error(msg, ErrorCode.NOT_UNIQUE_CARDS, context={"cards": cards})
                cards = None
                continue

            # Sind die Karten auf der Hand?
            if any(card not in self.priv.hand_cards for card in cards):
                msg = "Mindestens eine Karte ist keine Handkarte"
                logger.warning(f"[{self._name}] {msg}: {stringify_cards(cards)}")
                await self.error(msg, ErrorCode.NOT_HAND_CARD, context={"cards": cards})
                cards = None
                continue

            # Kombination ermitteln. Ist sie spielbar?
            action_space = build_action_space(self.priv.combinations, self.pub.trick_combination, self.pub.wish_value)
            for playable_cards, playable_combination in action_space:
                if set(cards) == set(playable_cards):
                    combination = playable_combination
                    break

            if combination is None:
                msg = "Die Karten bilden keine spielbare Kombination"
                logger.warning(f"[{self._name}] {msg}: {stringify_cards(cards)}")
                await self.error(msg, ErrorCode.INVALID_COMBINATION, context={"cards": cards})
                cards = None
                continue

        # Ist der Spieler am Zug? (stellt die Engine sicher) todo rausnehmen
        assert self.pub.current_turn_index == self.priv.player_index

        return cards, combination

    async def bomb(self) -> Tuple[Cards, Combination] | False:
        """
        Die Engine fragt den Spieler, ob er eine Bombe werfen will, und wenn ja, welche.

        Die Engine ruft diese Methode nur auf, wenn eine Bombe vorhanden ist.
        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        Da der Client proaktiv (also ungefragt) eine Bombe wirft, wird die Frage nicht an den Client
        weitergeleitet, sondern es wird im Puffer geschaut, ob ein Bombenwurf vorliegt.
        todo Nein, das ist falsch! Richtig ist:
        Da der Client proaktiv (also ungefragt) eine Bombe ankündigt, wird die Frage nur an den Client
        weitergeleitet, wenn er zuvor die Bombe angekündigt hat.

        :return: Die Bombe (Karten, (Typ, Länge, Rang)) oder False, wenn keine Bombe geworfen wurde.
        """
        # Liegt ein Bombenwurf vor?
        if not self._pending_bomb:
            return False

        # Bombe aus dem Puffer nehmen
        cards = self._pending_bomb
        self._pending_bomb = None

        # Sind die Karten noch auf der Hand?
        if any(card not in self.priv.hand_cards for card in cards):
            msg = "Mindestens eine Karte ist keine Handkarte"
            logger.warning(f"[{self._name}] {msg}: {stringify_cards(cards)}")
            await self.error(msg, ErrorCode.NOT_HAND_CARD, context={"cards": cards})
            return False

        # Ist die Kombination noch spielbar?
        combination = None
        action_space = build_action_space(self.priv.combinations, self.pub.trick_combination, self.pub.wish_value)
        for playable_cards, playable_combination in action_space:
            if playable_combination[0] == CombinationType.BOMB and set(cards) == set(playable_cards):
                combination = playable_combination
                break
        if combination is None:
            msg = "Die Karten bilden keine spielbare Bombe"
            logger.warning(f"[{self._name}] {msg}: {stringify_cards(cards)}")
            await self.error(msg, ErrorCode.INVALID_COMBINATION, context={"cards": cards})
            return False

        return cards, combination

    async def wish(self) -> int:
        """
        Die Engine fragt den Spieler nach einem Kartenwert-Wunsch (nach Ausspielen des Mah Jong).

        Die Engine ruft diese Methode nur auf, wenn der Spieler sich einen Kartenwert wünschen muss.
        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        :return: Der gewünschte Kartenwert (2-14).
        """
        wish_value = None
        while wish_value is None:
            response_data = await self._ask("wish")

            # Fallback bei Verbindungsabbruch
            if response_data is None:
                # Heuristik: Die Karte, die an den rechten Gegner geschupft wurde, wird sich gewünscht.
                logger.debug(f"[{self._name}] Fallback-Antwort")
                return self.priv.given_schupf_cards[0][0]

            # Ist der Payload ok?
            if not isinstance(response_data.get("wish_value"), int):
                msg = "Ungültige Antwort für Anfrage 'wish'"
                logger.warning(f"[{self._name}] {msg}: {response_data}")
                await self.error(msg, ErrorCode.INVALID_MESSAGE, context=response_data)
                continue

            # Ist der Wunsch ein Kartenwert?
            wish_value = response_data["wish_value"]
            if wish_value < 2 or wish_value > 14:
                msg = "Wunsch ist kein Kartenwert"
                logger.warning(f"[{self._name}] {msg}: {wish_value}")
                await self.error(msg, ErrorCode.INVALID_WISH, context={"wish_value": wish_value})
                wish_value = None
                continue

        # Wurde noch kein Wunsch geäußert? (stellt die Engine sicher)  todo rausnehmen
        assert (self.pub.current_turn_index == self.priv.player_index and
                self.pub.wish_value == 0 and
                CARD_MAH in self.pub.played_cards) # oder alternativ: CARD_MAH in self.pub.trick_cards

        return wish_value

    async def give_dragon_away(self) -> int:
        """
        Die Engine fragt den Spieler, welchem Gegner der mit dem Drachen gewonnene Stich gegeben werden soll.

        Die Engine ruft diese Methode nur auf, wenn der Spieler den Drachen verschenken muss.
        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        :return: Der Index (0-3) des Gegners, der den Stich erhält.
        """
        dragon_recipient = None
        while dragon_recipient is None:
            response_data = await self._ask("give_dragon_away")

            # Fallback bei Verbindungsabbruch
            if response_data is None:
                # Heuristik: Der Gegner mit den meisten Handkarten kriegt den Drachen.
                logger.debug(f"[{self._name}] Fallback-Antwort")
                return self.priv.opponent_right_index if self.pub.count_hand_cards[self.priv.opponent_right_index] > self.pub.count_hand_cards[self.priv.opponent_left_index] else self.priv.opponent_left_index

            # Ist der Payload ok?
            if not isinstance(response_data.get("dragon_recipient"), int):
                msg = "Ungültige Antwort für Anfrage 'give_dragon_away'"
                logger.warning(f"[{self._name}] {msg}: {response_data}")
                await self.error(msg, ErrorCode.INVALID_MESSAGE, context=response_data)
                continue

            # Wurde der Drache an den Gegner verschenkt?
            dragon_recipient = response_data["dragon_recipient"]
            if dragon_recipient not in [self.priv.opponent_right_index, self.priv.opponent_left_index]:
                msg = "Der gewählte Spieler ist kein Gegner"
                logger.warning(f"[{self._name}] {msg}: {dragon_recipient}")
                await self.error(msg, ErrorCode.INVALID_DRAGON_RECIPIENT, context={"dragon_recipient": dragon_recipient})
                dragon_recipient = None
                continue

        # Ist der Drache noch zu verschenken? (stellt die Engine sicher)  todo rausnehmen
        assert (self.pub.current_turn_index == self.priv.player_index and
                self.pub.dragon_recipient == -1 and
                self.pub.trick_combination == FIGURE_DRA)

        return dragon_recipient

    # ------------------------------------------------------
    # Benachrichtigungen
    # ------------------------------------------------------

    async def notify(self, event: str, context: Optional[dict] = None):
        """
        Die Engine ruft diese Funktion auf, um ein Spielereignis zu melden.

        Die Nachricht wird eventuell noch mit privaten Statusinformationen angereichert, bevor sie
        über die WebSocket-Verbindung an den Client weitergeleitet wird.

        :param event: Das Spielereignis, über das berichtet wird.
        :param context: (Optional) Zusätzliche Informationen zum Ereignis.
        """
        if self._websocket.closed:
            logger.debug(f"[{self._name}] Keine Verbindung. Ereignis '{event}' konnte nicht gesendet werden.")
            return

        if event == "player_joined":
            if context.get("player_index") == self.priv.player_index:
                context = {
                    "session_id": self._session_id,
                    "public_state": self.pub.to_dict(),
                    "private_state": self.priv.to_dict(),
                }

        elif event == "hand_cards_dealt":
            if context.get("player_index") == self.priv.player_index:
                assert context.get("count") == len(self.priv.hand_cards)
                context = {
                    "hand_cards": self.priv.hand_cards,
                }

        elif event == "player_schupfed":
            if context.get("player_index") == self.priv.player_index:
                context = {
                    "given_schupf_cards": self.priv.given_schupf_cards,
                }

        elif event == "start_playing":
            context = {
                "start_player_index": self.pub.start_player_index,
                "received_schupf_cards": self.priv.received_schupf_cards,
            }

        notification_message = {
            "type": "notification",
            "payload": {
                "event": event,
                "context": context if context else {},
            }
        }

        try:
            logger.debug(f"[{self._name}] Sende Ereignis '{event}'.")
            await self._websocket.send_json(notification_message)
        except (ConnectionResetError, asyncio.CancelledError, RuntimeError, ConnectionAbortedError) as e:
            logger.warning(f"[{self._name}] Verbindungsabbruch. Ereignis '{event}' konnte nicht gesendet werden: {e}")
        except Exception as e:
            logger.exception(f"[{self._name}] Unerwarteter Fehler. Ereignis '{event}' konnte nicht gesendet werden': {e}")

    async def error(self, message: str, code: ErrorCode, context: Optional[Dict] = None):
        """
        Die Engine ruft diese Funktion auf, um einen Fehler zu melden.

        Die Fehlermeldung wird über die WebSocket-Verbindung an den Client weitergeleitet.

        :param message: Die Fehlermeldung.
        :param code: Der Fehlercode.
        :param context: (Optional) Zusätzliche Informationen.
        """
        if self._websocket.closed:
            logger.debug(f"[{self._name}] Keine Verbindung. Fehler {code} konnte nicht gesendet werden.")
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
            logger.debug(f"[{self._name}] Sende Fehler {code}.")
            await self._websocket.send_json(error_message)
        except (ConnectionResetError, asyncio.CancelledError, RuntimeError, ConnectionAbortedError) as e:
            logger.warning(f"[{self._name}] Verbindungsabbruch. Fehler {code} konnte nicht gesendet werden: {e}")
        except Exception as e:
            logger.exception(f"[{self._name}] Unerwarteter Fehler. Fehler {code} konnte nicht gesendet werden: {e}")

    # ------------------------------------------------------
    # Eigenschaften
    # ------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        """
        Ermittelt, ob der Peer aktuell verbunden ist.

        :return: True, wenn verbunden, sonst False.
        """
        return not self._websocket.closed
