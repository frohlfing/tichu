"""
Definiert die Client-Klasse für die Interaktion mit einem menschlichen Spieler über eine WebSocket-Verbindung.
"""

import asyncio
import time
from aiohttp import WSCloseCode
from aiohttp.web import WebSocketResponse

import config
from src.lib.errors import ClientDisconnectedError, PlayerInteractionError, PlayerInterruptError, PlayerTimeoutError, PlayerResponseError
from src.common.logger import logger
from src.common.rand import Random
from src.lib.cards import Card, stringify_cards, parse_cards
from src.lib.combinations import Combination
from src.players.player import Player
from src.private_state2 import PrivateState
from src.public_state2 import PublicState
from typing import Optional, Dict, List, Tuple

# Timeout Konstante
DEFAULT_REQUEST_TIMEOUT = 30.0  # todo notwendig? wenn ja, in die config verschieben


class Client(Player):
    """
    Repräsentiert einen menschlichen Spieler, der über eine WebSocket verbunden ist.

    Erbt von der Basisklasse `Player`.
    """

    def __init__(self, name: str,
                 websocket: WebSocketResponse,
                 interrupt_event: asyncio.Event,  # todo nach Player verlager. Agent könnten auch schonmal await benutzen und dann brauchen die das interrupt_event
                 session: Optional[str] = None,
                 seed: Optional[int] = None):
        """
        Initialisiert einen neuen Client.

        :param name: Der Name des Spielers.
        :param websocket: Das WebSocketResponse-Objekt der initialen Verbindung.
        :param interrupt_event: Das globale Interrupt-Event.
        :param session: (Optional) Aktuelle Session des Spielers. Wenn None, wird eine Session generiert.
        :param seed: (Optional) Seed für den internen Zufallsgenerator (für Tests).
        """
        super().__init__(name, session=session)
        self._websocket = websocket
        self._interrupt_event = interrupt_event
        self._random = Random(seed)  # Zufallsgenerator
        # todo es wird immer nur eine Anfrage gestellt. Bevor die nicht beantwortet ist, wird keine zweite gestellt.
        #  Daher reicht es nur ein Future festzuhalten: self._pending_requests: Optional[asyncio.Future] = None
        self._pending_requests: Dict[str, asyncio.Future] = {}  # noch nicht von der Gegenstelle beantwortete Websocket-Anfragen
        #self._is_connected: bool = True  # interner Verbindungsstatus

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
        #self.mark_as_disconnected(reason="Expliziter close_connection Aufruf")

    # ------------------------------------------------------
    # Ereignis-Handler
    # ------------------------------------------------------

    async def on_notify(self, msg_type: str, payload: dict):
        """
        Wird aufgerufen, wenn eine Nachricht vom Server eingetroffen ist.

        Die Nachricht wird über die WebSocket-Verbindung an die Gegenstelle weitergeleitet.

        :param msg_type: Der Typ der Nachricht.
        :param payload: Die Nutzdaten der Nachricht als Dictionary.
        """
        #if not self._is_connected or self._websocket is None or self._websocket.closed:
        if self._websocket.closed:
            # Client nicht verbunden
            logger.debug(f"Nachricht {msg_type} an {self._name} konnte nicht übermittelt werden. Keine Verbindung.")
            return

        message = {"type": msg_type, "payload": payload}
        try:
            logger.debug(f"Sende Nachricht an {self._name}: {message}")
            await self._websocket.send_json(message)
        except (ConnectionResetError, asyncio.CancelledError, RuntimeError, ConnectionAbortedError) as e:
            logger.warning(f"Senden der Nachricht {msg_type} an {self._name} fehlgeschlagen: {e}")
            #self.mark_as_disconnected(reason=f"Sendefehler: {e}")
        except Exception as e:
            logger.exception(f"Unerwarteter Fehler beim Senden der Nachricht {msg_type} an {self._name}: {e}")
            #self.mark_as_disconnected(reason=f"Unerwarteter Sendefehler: {e}")

    async def on_websocket_message(self, msg_type: str, payload: dict):
        """
        Wird aufgerufen, wenn eine Nachricht von der Gegenstelle empfangen wurde.

        :param msg_type: Der Typ der Nachricht.
        :param payload: Die Nutzdaten der Nachricht als Dictionary.
        """
        if msg_type == "response":  # Antwort auf einer vorherigen Anfrage (die mittels _ask() gestellt wurde)
            request_type = payload.get("request_type")  # der Typ der ursprünglichen Anfrage
            response_data = payload.get("response_data")  # Die Nutzdaten der Antwort.
            if request_type in self._pending_requests:
                future = self._pending_requests[request_type]
                if not future.done():
                    future.set_result(response_data)
                    logger.debug(f"Client {self._name}: Antwort für '{request_type}' an wartende Methode weitergeleitet.")
                else:
                    # Die Future wurde bereits gesetzt (z.B. Timeout, Cancelled) oder die Antwort kam zu spät.
                    logger.warning(f"Client {self._name}: Antwort für bereits abgeschlossene/abgebrochene Anfrage '{request_type}' erhalten: {response_data}")
            else:
                # Keine wartende Anfrage für diesen Typ gefunden.
                logger.warning(f"Client {self._name}: Unerwartete Antwort für '{request_type}' erhalten (keine passende wartende Anfrage): {response_data}")

        if msg_type == "ping":
            logger.info(f"{self._name}: ping")
            await self.on_notify("pong", {"message": f"{payload}"})
        else:
            logger.warning(f"Gegenstelle von {self._name} hat invalide Daten gesendet: {payload}")
            await self.on_notify("error", {"message": "Invalide Daten."})

    # ------------------------------------------------------
    # Entscheidungen
    # todo dieser Abschnitt ist noch nicht umgesetzt.
    #  Es fehlt eine klare Definition, wie die Nachrichten aufgebaut sein müssen.
    # ------------------------------------------------------

    async def schupf(self, pub: PublicState, priv: PrivateState) -> Tuple[Card, Card, Card]:
        """
        Fordert den Spieler auf, drei Karten zum Schupfen auszuwählen.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Die Liste der Karten (Karte für rechten Gegner, Karte für Partner, Karte für linken Gegner).
        """
        # TODO: Implementieren!
        raise PlayerResponseError(f"Ungültige Antwort auf 'foo': bar")
        #return (13, 4), (5, 3), (2, 1)  # dummy-Werte ersetzen

        # request_type = "request_schupf_cards"
        # try:
        #     # Kontext ist hier nicht unbedingt nötig, Client sieht seine Hand
        #     raw_response_payload = await self._ask(request_type)
        #     # raw_response_payload ist z.B. {"to_left": "RK", "to_partner": "G5", "to_right": "S2"}
        #     logger.debug(f"Parsing schupf response: {raw_response_payload}")  # Debugging
        #
        #     # Parst und validiert die Schupf-Antwort des Clients
        #     # 1. Extrahiere die drei Karten-Labels aus raw_response_payload.
        #     # 2. Prüfe, ob genau drei Labels vorhanden sind.
        #     # 3. Parse die Labels mit parse_cards in interne Card-Tupel.
        #     # 4. Prüfe, ob alle drei geparsten Karten in der current_hand des Spielers vorkommen.
        #     # 5. Wenn alles gültig: schupf_tuple = (card_left, card_partner, card_right)
        #     if not raw_response_payload:
        #         raise PlayerResponseError(f"Ungültige Antwort auf '{request_type}': {raw_response_payload}")
        #     schupf_tuple = (13,4), (5,3), (2,1)  # dummy-Werte ersetzen
        #     logger.info(f"Client {self.name}: Schupf-Karten erfolgreich gewählt.")
        #     return schupf_tuple
        # except PlayerInteractionError as e:
        #     logger.warning(f"Client {self.name}: Interaktionsfehler bei '{request_type}': {e}")
        #     raise e

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
        return self._random.choice([True, False], [1, 19] if grand else [1, 9])

    async def combination(self, pub: PublicState, priv: PrivateState, action_space: list[tuple]) -> tuple:
        """
        Fordert den Spieler auf, eine gültige Kartenkombination auszuwählen oder zu passen.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :param action_space: Mögliche Kombinationen (inklusiv Passen; wenn Passen erlaubt ist, steht Passen an erster Stelle).
        :return: Die ausgewählte Kombination (Karten, (Typ, Länge, Wert)) oder Passen ([], (0,0,0))
        """
        # TODO: Implementieren!
        return action_space[self._random.integer(0, len(action_space))]
        # Beispielimplementierung:
        # # Eindeutiger Schlüssel für diese Anfrageart
        # request_type = "request_combination"
        # try:
        #     # Bereite Kontext vor (mögliche Aktionen serialisieren)
        #     serializable_actions = self._serialize_action_space(action_space)
        #     context = {"possible_actions": serializable_actions}
        #
        #     # Rufe _ask auf und warte auf die Rohdaten der Antwort
        #     raw_response_payload = await self._ask(request_type, context)  # Fängt Timeout/Interrupt/Disconnect ab
        #
        #     # Parse und validiere die Rohdaten
        #     action_tuple = self._parse_combination_response(raw_response_payload, action_space)
        #     if action_tuple is None:
        #         # Parsing/Validierung fehlgeschlagen
        #         raise PlayerResponseError(f"Ungültige Antwort auf '{request_type}': {raw_response_payload}")
        #
        #     logger.info(f"Client {self.name}: Kombination '{action_tuple[0]}' erfolgreich gewählt.")
        #     return action_tuple
        # except PlayerInteractionError as e:  # Fängt Timeout, Interrupt, Disconnect, ResponseError
        #     logger.warning(f"Client {self.name}: Interaktionsfehler bei '{request_type}': {e}")
        #     raise e

    def _parse_combination_response(self, response_data: dict, original_action_space: list[tuple]) -> Optional[tuple]:
        """
        Parst die Antwort des Clients, validiert sie gegen den ursprünglichen action_space
        und gibt das interne Aktions-Tupel zurück oder None bei ungültiger Antwort.
        """
        # Input z.B.: {"action": "play_cards", "payload": {"cards": ["SK", "BK"]}}
        # Output z.B.: ('play_cards', [(13,1), (13,2)], (PAIR, 2, 13)) oder ('pass_turn', None, ...)
        # TODO: Implementieren!
        # 1. Extrahiere action und payload aus response_data.
        # 2. Wenn action == "play_cards":
        #    a. Parse die card_labels im payload mit parse_cards in interne Card-Tupel.
        #    b. Finde die entsprechende Aktion im original_action_space, die genau diese Karten enthält.
        #       (Achtung: Reihenfolge der Karten könnte anders sein, Sets vergleichen?)
        #    c. Wenn gefunden -> Gib das Tupel aus original_action_space zurück.
        #    d. Wenn nicht gefunden -> Ungültig, return None.
        # 3. Wenn action == "pass_turn":
        #    a. Finde die ('pass_turn', ...) Aktion im original_action_space.
        #    b. Wenn gefunden -> Gib dieses Tupel zurück.
        #    c. Wenn nicht gefunden (sollte nicht passieren) -> Ungültig, return None.
        # 4. Andere Aktionen -> Ungültig, return None.

        client_action = response_data.get("action")
        client_payload = response_data.get("payload", {})

        if client_action == "pass_turn":
            # Finde die Pass-Aktion im Action Space
            pass_action = next((a for a in original_action_space if a[0] == "pass_turn"), None)
            if pass_action:
                return pass_action
            else:
                logger.error(f"Client {self._name} wählte 'pass_turn', aber das war nicht im Action Space: {original_action_space}")
                return None  # Ungültig

        elif client_action == "play_cards":
            card_labels = client_payload.get("cards", [])
            if not card_labels:
                logger.warning(f"Client {self._name} wählte 'play_cards' ohne Karten.")
                return None  # Ungültig
            try:
                # Konvertiere Labels zu internen Karten und sortiere für Vergleich
                played_cards_internal = sorted(parse_cards(" ".join(card_labels)), reverse=True)
            except Exception as e:
                logger.warning(f"Client {self._name} sendete ungültige Karten-Labels: {card_labels} -> {e}")
                return None  # Ungültig

            # Finde die passende Aktion im Action Space
            for action_tuple in original_action_space:
                if action_tuple[0] == "play_cards":
                    space_cards_internal = sorted(action_tuple[1], reverse=True)
                    # Vergleiche die sortierten Listen/Sets der Karten
                    if played_cards_internal == space_cards_internal:
                        return action_tuple  # Gültige Aktion gefunden!

            # Wenn keine Übereinstimmung gefunden wurde
            logger.warning(f"Client {self._name} spielte Karten {card_labels}, die nicht im Action Space waren: {original_action_space}")
            return None  # Ungültig
        else:
            logger.warning(f"Client {self._name} sendete unbekannte Aktion in Antwort: {client_action}")
            return None  # Ungültig

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

    async def gift(self, pub: PublicState, priv: PrivateState) -> int:
        """
        Fragt den Spieler, welchem Gegner der mit dem Drachen gewonnene Stich gegeben werden soll.

        Muss von Subklassen implementiert werden.

        :param pub: Der öffentliche Spielzustand.
        :param priv: Der private Spielzustand.
        :return: Der Index (0-3) des Gegners, der den Stich erhält.
        """
        # TODO: Implementieren!
        return self.opponent_right_index if self._random.boolean() else self.opponent_left_index

    # ------------------------------------------------------
    # Hilfsfunktionen
    # ------------------------------------------------------

    def set_websocket(self, new_websocket: WebSocketResponse):
        """
        Übernimmt die WebSocket-Verbindung.

        :param new_websocket: Das neue WebSocketResponse-Objekt.
        """
        logger.info(f"Aktualisiere WebSocket für Client {self._name} ({self._session}).")
        self._websocket = new_websocket
        #self._is_connected = True  # markiere als verbunden
        # Über die alte Verbindung noch Anfragen offen sind, diese verwerfen.
        for request_type, future in list(self._pending_requests.items()):
            if not future.done():
                logger.warning(f"Client {self._name}: Breche alte Anfrage '{request_type}' wegen Reconnect ab.")
                future.cancel()
            self._pending_requests.pop(request_type, None)

    # def mark_as_disconnected(self, reason: str = "Verbindung geschlossen"):
    #     """
    #     Markiert den Client intern als getrennt.
    #
    #     Wird aufgerufen, wenn die Verbindung verloren geht oder explizit
    #     geschlossen wird. Setzt das interne Flag und entfernt die WebSocket-Referenz.
    #
    #     :param reason: Der Grund für die Trennung (für Logging).
    #     """
    #     # Nur ausführen, wenn der Client aktuell als verbunden gilt.
    #     if self._is_connected:
    #         logger.info(f"Markiere Client {self._name} ({self._session}) als getrennt. Grund: {reason}")
    #         self._is_connected = False
    #         self._websocket = None # WebSocket-Referenz entfernen

    async def _ask(self, request_type: str, context_payload: Optional[dict] = None, timeout: float = config.DEFAULT_REQUEST_TIMEOUT) -> dict | None:
        """
        Sendet eine Anfrage an den Client und wartet auf dessen Antwort.

        :param request_type: Eindeutiger Bezeichner für die Art der Anfrage (z.B. "request_combination", "request_schupf").
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
        #if not self._is_connected or self._websocket is None or self._websocket.closed:
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
        request_data = {"type": "request_action", "payload": {"request": request_type, "timeout": timeout}}
        if context_payload:
            request_data["payload"]["context"] = context_payload  # Kontext in Payload verschachteln
        try:
            logger.debug(f"Sende Anfrage an {self.name}: {request_data}")
            # Direkter Aufruf von send_json hier
            await self._websocket.send_json(request_data)
        except (ConnectionResetError, asyncio.CancelledError, RuntimeError, ConnectionAbortedError) as e:
            logger.warning(f"Senden der Anfrage '{request_type}' an {self.name} fehlgeschlagen (Verbindungsfehler): {e}. Markiere als getrennt.")
            #self.mark_as_disconnected(reason=f"Sendefehler bei Anfrage: {e}")
            # noinspection PyAsyncCall
            self._pending_requests.pop(request_type, None)  # Future entfernen
            raise ClientDisconnectedError(f"Senden der Anfrage '{request_type}' fehlgeschlagen.") from e
        except Exception as e:
            logger.exception(f"Unerwarteter Fehler beim Senden der Anfrage '{request_type}' an {self.name}: {e}")
            #self.mark_as_disconnected(reason=f"Unerwarteter Sendefehler bei Anfrage: {e}")
            # noinspection PyAsyncCall
            self._pending_requests.pop(request_type, None)  # Future entfernen
            raise PlayerInteractionError(f"Fehler beim Senden der Anfrage '{request_type}': {e}") from e

        # --- 4. Auf Antwort warten ---
        loop = asyncio.get_running_loop()
        response_future = loop.create_future()
        wait_tasks = [
            asyncio.create_task(response_future, name=f"ClientResp_{self.player_index}_{request_type}"),
            asyncio.create_task(self._interrupt_event.wait(), name="Interrupt"),
        ]
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

            if self._interrupt_event in done:
                # Interrupt
                elapsed = time.monotonic() - start_time
                logger.info(f"Client {self.name}: Warten auf '{request_type}' nach {elapsed:.1f}s unterbrochen aufgrund Interrupt-Event.")
                raise PlayerInterruptError()

            # Antwort erhalten
            assert response_future in done
            response_data = response_future.result()  # Das ist das Payload-Dict von receive_response
            logger.debug(f"Client {self.name}: Antwort für '{request_type}' erfolgreich empfangen.")
            return response_data  # Erfolg! Gib rohes Payload zurück.

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

    # noinspection PyMethodMayBeStatic
    def _serialize_action_space(self, action_space: list[tuple]) -> List[Dict]:
        """Konvertiert den internen action_space in ein serialisierbares Format für den Client."""
        # Input z.B.: [('play_cards', [(13,1), (13,2)], (PAIR, 2, 13)), ('pass_turn', None, (PASS,0,0))]
        # Output z.B.: [{"action": "play_cards", "cards": ["SK", "BK"], "combo_type": "PAIR", "combo_rank": 13}, {"action": "pass_turn"}]
        serialized = []
        if not action_space:
            return []
        for action_tuple in action_space:
            action_name = action_tuple[0]
            if action_name == "play_cards":
                cards_internal: Optional[List[Card]] = action_tuple[1]
                combo_details: Optional[Combination] = action_tuple[2]
                if cards_internal and combo_details:
                    serialized.append({
                        "action": "play_cards",
                        "cards": stringify_cards(cards_internal),  # Konvertiere zu Labels
                        "combo_type": combo_details[0].name,  # Enum-Name
                        "combo_rank": combo_details[2]  # Rang
                    })
            elif action_name == "pass_turn":
                serialized.append({"action": "pass_turn"})
            # Füge hier ggf. andere Aktionen hinzu
        return serialized

    # ------------------------------------------------------
    # Eigenschaften
    # ------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        """
        Gibt zurück, ob der Client aktuell als verbunden gilt.

        :return: True, wenn verbunden, sonst False.
        """
        #return self._is_connected and self._websocket is not None and not self._websocket.closed
        return not self._websocket.closed
