"""
Definiert den serverseitigen Endpunkt der WebSocket-Verbindung für die Interaktion mit einem menschlichen Spieler.
"""

import asyncio
import time
from aiohttp import WSCloseCode
from aiohttp.web import WebSocketResponse
from src import config
from src.common.logger import logger
from src.common.rand import Random
from src.lib.cards import Card, Cards, stringify_cards, deck, CARD_MAH, CardSuit
from src.lib.combinations import Combination, build_action_space, CombinationType
# noinspection PyUnresolvedReferences
from src.lib.errors import ClientDisconnectedError, PlayerInteractionError, PlayerInterruptError, PlayerTimeoutError, PlayerResponseError, ErrorCode
from src.players.player import Player
from typing import Optional, Dict, List, Tuple


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
        self._new_websocket_event = asyncio.Event()  #  wait_for_reconnect() wartet auf dieses Event
        self._pending_request: Optional[Tuple[str, asyncio.Future]] = None  # die noch vom Client unbeantwortete Anfrage
        self._pending_bomb: Optional[Cards] = None  # die noch vom Server abzuholende Bombe

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

        # Die Referenz auf den Spielzustand muss für eine Fallback-Entscheidung erhalten bleiben! Nachfolgende Zeilen müssen auskommentiert bleiben!
        #peer.pub = None
        #peer.priv = None
        #peer.interrupt_event = None

        self._new_websocket_event.set()  # bewirkt, dass wait_for_reconnect() fortgesetzt wird

        # Offene Anfragen verwerfen.
        self._cancel_pending_requests()

    def reset_round(self):  # pragma: no cover
        """
        Setzt spielrundenspezifische Werte zurück.
        """
        self._cancel_pending_requests()

    def _cancel_pending_requests(self):
        """
        Offene Anfragen verwerfen.
        """
        if self._pending_request and not self._pending_request[1].done():
            self._pending_request[1].set_result(None)
        self._pending_request = None
        self._pending_bomb = None

    def set_websocket(self, new_websocket: WebSocketResponse):
        """
        Übernimmt die WebSocket-Verbindung.

        :param new_websocket: Das neue WebSocketResponse-Objekt.
        """
        # WebSocket übernehmen
        logger.debug(f"[{self._name}] Aktualisiere WebSocket.")
        self._websocket = new_websocket
        self._new_websocket_event.set()  # bewirkt, dass wait_for_reconnect() fortgesetzt wird

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

    async def client_bomb(self, cards: Cards):
        """
        Der WebSocket-Handler ruft diese Funktion auf, wenn der Client proaktiv (also unaufgefordert) eine Bombe geworfen hat.

        Die Bombe wird zwischengespeichert, bis sie von der Engine regulär im Game-Loop abgeholt wird.
        Es wird ein Interrupt ausgelöst, so dass die Engine schnellstmöglich nach der Bombe fragt.

        :param cards: Die Karten, aus denen die Bombe gebildet wurde. Werden absteigend sortiert (mutable!).
        """
        # Ist der Parameter eine Liste?
        if not isinstance(cards, list):
            msg = "Ungültiger Parameter für 'bomb'"
            logger.warning(f"[{self._name}] {msg}: {cards}")
            await self.error(msg, ErrorCode.INVALID_MESSAGE, context={"cards": cards})
            return

        # Karten valide?
        cards = [(card[0], CardSuit(card[1])) for card in cards]
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
        action_space = build_action_space(self.priv.combinations, self.pub.trick_combination, wish_value=0)
        for playable_cards, playable_combination in action_space:
            if playable_combination[0] == CombinationType.BOMB and set(cards) == set(playable_cards):
                combination = playable_combination
                break
        if combination is None:
            msg = "Die Karten bilden keine spielbare Bombe"
            logger.warning(f"[{self._name}] {msg}: {stringify_cards(cards)}")
            await self.error(msg, ErrorCode.INVALID_COMBINATION, context={"cards": cards})
            return

        self._pending_bomb = cards
        self.interrupt_event.set()

    async def client_response(self, action: str, response_data: dict):
        """
        Der WebSocket-Handler ruft diese Funktion auf, wenn der Client eine Anfrage beantwortet hat.

        :param action: Die angefragte Aktion.
        :param response_data: Die Daten der Antwort.
        """
        if not self._pending_request or self._pending_request[0] != action:
            # Die Aktion wurde nicht angefragt.
            # Das kann auch bei einem fehlerfreien Client passieren. Denn nachdem eine Anfrage durch ein Interrupt verworfen,
            # aber noch kein neues Ereignis gesendet wurde, hat der Client eine veraltete Anfrage.
            logger.warning(f"Aktion '{action}' nicht erwartet.")
            #await self.error("Aktion nicht erwartet", ErrorCode.INVALID_RESPONSE, context={"action": action, "pending_action": self._pending_request[0]})
            return

        # Future abholen
        future = self._pending_request[1]
        self._pending_request = None

        if future.done():
            # _ask() hat inzwischen das Warten auf diese Antwort aufgegeben (wegen Timeout oder Server beenden).
            msg = "Anfrage ist veraltet"
            logger.warning(f"[{self._name}] {msg}; Request: {action}.")
            await self.error(msg, ErrorCode.REQUEST_OBSOLETE, context={"action": action})
            return

        # Die Daten mittels Future an _ask() übergeben.
        future.set_result(response_data)
        logger.debug(f"[{self._name}] Antwort an wartende Methode übergeben; Request {action}.")

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
        # if self._websocket.closed:
        #     logger.warning(f"[{self._name}] Keine Verbindung. Anfrage '{action}' nicht möglich.")
        #     return None

        # Future erstellen und registrieren
        loop = asyncio.get_running_loop()
        response_future = loop.create_future()
        assert self._pending_request is None, "Eine Anfrage wurde bereits gesendet!"
        self._pending_request = action, response_future

        # Anfrage senden
        request_message: dict = {
            "type": "request",
            "payload": {
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
            logger.warning(f"[{self._name}] Verbindungsfehler. Senden der Anfrage '{action}' fehlgeschlagen: {e}. Warte auf Reconnect.")
            # Wir warten trotzdem auf das Future. Sobald der Client wieder verbunden ist, erhält er mit dem Status auch diese Anfrage.
        except Exception as e:
            logger.exception(f"[{self._name}] Unerwarteter Fehler. Senden der Anfrage '{action}' fehlgeschlagen: {e}")
            self._pending_request = None  # Future wieder entfernen
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
        except PlayerInterruptError as e:
            raise e
        except Exception as e:
            logger.exception(f"[{self._name}] Unerwarteter Fehler. Warten auf Antwort '{action}' abgebrochen: {e}")
            return None
        finally:
            logger.debug(f"[{self._name}] Räume Warte-Task für '{action}' auf.")
            for task in pending:
                if not task.done():
                    task.cancel()
                # Die noch laufenden Tasks etwas Zeit geben, dass sie sich sauber beenden können.
                try:
                    await asyncio.wait_for(task, timeout=0.1)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
                except Exception as cleanup_e:
                    logger.exception(f"[{self._name}] Fehler beim Aufräumen von Task {task.get_name()}: {cleanup_e}")
            # noinspection PyAsyncCall
            self._pending_request = None  # Future wieder entfernen

    async def announce(self) -> bool:
        """
        Die Engine fragt den Spieler, ob er ein Tichu (großes oder einfaches) ansagen möchte.

        Die Engine ruft diese Methode nur auf, wenn der Spieler ein Tichu ansagen darf.
        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        Wenn es um ein einfaches Tichu geht, wird die Anfrage einfach verneint, denn der Client sagt dies proaktiv an.
        Ansonsten wird die Anfrage an den Client gesendet.

        :return: True, wenn angesagt wird, sonst False.
        """
        grand = len(self.priv.hand_cards) == 8
        if not grand:
            # Eine einfache Tichu-Ansage entscheidet der Client proaktiv, also nicht jetzt.
            # Sollte der Client ein einfaches Tichu ansagen, leitet der Websocket-Handler dies direkt an die Engine weiter,
            # die dann die Ansage parallel zum Game-Loop speichert.
            return False

        announced = None
        while announced is None:
            response_data = await self._ask("announce_grand_tichu")

            # Fallback bei Verbindungsabbruch
            if response_data is None:
                # Heuristik: Es wird niemals großes Tichu angesagt.
                logger.debug(f"[{self._name}] Fallback-Antwort")
                return False

            # Hat die Antwort die erwartete Struktur?
            if not isinstance(response_data.get("announced"), bool):
                msg = "Ungültige Antwort für Anfrage 'announce_grand_tichu'"
                logger.warning(f"[{self._name}] {msg}: {response_data}")
                await self.error(msg, ErrorCode.INVALID_MESSAGE, context=response_data)
                continue

            # Antwort übernehmen
            announced = response_data["announced"]

        return announced

    async def schupf(self) -> Tuple[Card, Card, Card]:
        """
        Die Engine fordert den Spieler auf, drei Karten zum Schupfen auszuwählen.

        Die Engine ruft diese Methode nur auf, wenn der Spieler noch Karten abgeben muss.
        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        :return: Karten (Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner).
        """
        cards: Optional[Tuple[Card, Card, Card]] = None
        while cards is None:
            response_data = await self._ask("schupf", {"hand_cards": self.priv.hand_cards})

            # Fallback bei Verbindungsabbruch
            if response_data is None:
                # Heuristik: Die drei rangniedrigsten Karten werden geschupft, die höchste davon an den Partner.
                logger.debug(f"[{self._name}] Fallback-Antwort")
                return self.priv.hand_cards[-1], self.priv.hand_cards[-3], self.priv.hand_cards[-2]

            # Hat die Antwort die erwartete Struktur?
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
            if len(set(cards)) != 3:
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

        return cards

    async def play(self, interruptable: bool = False) -> Tuple[Cards, Combination]:
        """
        Die Engine fordert den Spieler auf, eine gültige Kartenkombination auszuwählen oder zu passen.

        Die Engine ruft diese Methode nur auf, wenn der Spieler am Zug ist oder eine Bombe hat.
        Die Engine verlässt sich darauf, dass die Antwort valide ist.

        Wenn der Client bereits eine Bombe gezündet hat (proaktiv), wird diese zurückgegeben.
        Wenn der Client nicht am Zug ist, kann er nur eine Bombe dazwischenwerfen. Wenn er das nicht bereits
        proaktiv gemacht hat, wird gepasst. Ansonsten wird die Anfrage an den Client gesendet.

        :param interruptable: (Optional) Wenn True, kann die Anfrage durch ein Interrupt abgebrochen werden.
        :return: Die ausgewählte Kombination (Karten, (Typ, Länge, Rang)) oder Passen ([], (0,0,0)).
        :raises PlayerInterruptError: Wenn die Aktion durch ein Interrupt abgebrochen wurde.
        """
        cards = None
        combination = None
        while combination is None:
            if self._pending_bomb:
                # Der Client hat bereits eine Bombe gezündet (proaktiv), jetzt ist Zeit, sie zu werfen.
                cards = self._pending_bomb
                self._pending_bomb = None
            else:
                if self.pub.current_turn_index != self.priv.player_index:
                    # Der Client ist nicht am Zug und kann daher nur eine Bombe dazwischenwerfen.
                    # Das hat er nicht getan, also passen wir.
                    return [], (CombinationType.PASS, 0, 0)  # Passen

                # Der Client ist regulär am Zug. Wir fordern ihn auf, Karten auszuwählen oder zu passen.
                response_data = await self._ask("play", {
                    "hand_cards": self.priv.hand_cards,
                    "trick_combination": self.pub.trick_combination,
                    "wish_value": self.pub.wish_value,
                }, interruptable)

                # Fallback bei Verbindungsabbruch
                if response_data is None:
                    # Heuristik: Die schwächste spielbare Kombination wird ausgewählt. Passen ist die letzte Option.
                    logger.debug(f"[{self._name}] Fallback-Antwort")
                    action_space = build_action_space(self.priv.combinations, self.pub.trick_combination, self.pub.wish_value)
                    return action_space[-1]

                # Hat die Antwort die erwartete Struktur?
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
            if self.pub.current_turn_index != self.priv.player_index:
                # Der Client ist nicht am Zug, daher kann er nur eine Bombe werfen.
                combinations = [combi for combi in self.priv.combinations if combi[1][0] == CombinationType.BOMB]
                action_space = build_action_space(combinations, self.pub.trick_combination, wish_value=0)
            else:
                # Der Client ist am Zug.
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

            # Hat die Antwort die erwartete Struktur?
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

        return wish_value

    async def give_dragon_away(self) -> int:
        """
        Die Engine fragt den Spieler, welcher Gegner den Drachen bekommen soll.

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

            # Hat die Antwort die erwartete Struktur?
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
            #logger.debug(f"[{self._name}] Keine Verbindung. Ereignis '{event}' konnte nicht gesendet werden.")
            return

        if event == "player_joined":
            if context.get("player_index") == self.priv.player_index:
                context = {
                    "session_id": self._session_id,
                    "public_state": self.pub.to_dict(),
                    "private_state": self.priv.to_dict(),
                    "pending_action": self._pending_request[0] if self._pending_request else "",
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
        except asyncio.CancelledError as e_cancel:  # Shutdown
            raise e_cancel
        except (ConnectionResetError, RuntimeError, ConnectionAbortedError) as e:
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
            #logger.debug(f"[{self._name}] Keine Verbindung. Fehler {code} konnte nicht gesendet werden.")
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
        except asyncio.CancelledError as e_cancel:  # Shutdown
            raise e_cancel
        except (ConnectionResetError, RuntimeError, ConnectionAbortedError) as e:
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
