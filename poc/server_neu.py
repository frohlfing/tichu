# server.py

import argparse
import asyncio
import config
import json
import os
import signal
import sys
from uuid import uuid4  # Für request_id, falls serverseitig generiert

from aiohttp import WSMsgType, WSCloseCode, WSMessage
from aiohttp.web import Application, AppRunner, Request, WebSocketResponse, TCPSite

from src.common.git_utils import get_release
from src.common.logger import logger
from src.game_factory import GameFactory
from src.players.client import Client  # Wichtig!
from src.game_engine import GameEngine  # Für Typ-Annotationen
from src.public_state import PublicState  # Für to_dict
from src.private_state import PrivateState  # Für to_dict
from src.lib.errors import ClientDisconnectedError  # Serverseitige Exception


# Annahme: KICK_OUT_TIME ist in config.py definiert
# config.KICK_OUT_TIME = 20

async def websocket_handler(request: Request) -> WebSocketResponse | None:
    factory: GameFactory = request.app['game_factory']
    ws = WebSocketResponse()
    try:
        await ws.prepare(request)
    except Exception as e:
        logger.exception(f"WebSocket Handshake fehlgeschlagen für {request.remote}: {e}")
        return ws

    params = request.query
    remote_addr = request.remote if request.remote else "Unbekannt"
    logger.debug(f"WebSocket Verbindung hergestellt von {remote_addr} mit Query-Parametern: {params}")

    client_obj: Optional[Client] = None  # Umbenannt zu client_obj zur Unterscheidung von src.players.client Modul
    engine: Optional[GameEngine] = None

    query_session_id = params.get("session_id")
    query_player_name = params.get("player_name")
    query_table_name = params.get("table_name")

    # -------------------------------------------------------------------------
    # 1. Client- und Engine-Initialisierung / Reconnect (wie zuvor besprochen)
    # -------------------------------------------------------------------------
    if query_session_id:
        engine = factory.get_engine_by_session(query_session_id)
        if engine:
            candidate = engine.get_player_by_session(query_session_id)
            if isinstance(candidate, Client):
                if not candidate.is_connected:  # Erfolgreicher Reconnect-Fall
                    client_obj = candidate
                    await client_obj.set_websocket(ws)  # Wichtig: await, falls set_websocket async wird
                    logger.info(f"Client {client_obj.name} (Session {client_obj.session}) erfolgreich via session_id wiederverbunden.")
                else:  # Session schon aktiv von anderer Verbindung
                    error_message = f"Session {query_session_id} wird bereits von einer aktiven Verbindung genutzt."
                    logger.warning(f"Verbindung von {remote_addr} abgelehnt. {error_message}")
                    await ws.close(code=WSCloseCode.POLICY_VIOLATION, message=error_message.encode('utf-8'))
                    return ws
            else:  # Session nicht gefunden oder kein Client-Objekt
                error_message = "Ungültige Session-ID oder Spieler nicht gefunden."
                logger.warning(f"Verbindung von {remote_addr} abgelehnt. {error_message}")
                await ws.close(code=WSCloseCode.POLICY_VIOLATION, message=error_message.encode('utf-8'))
                return ws
        else:
            error_message = "Kein Spiel für diese Session-ID gefunden."
            logger.warning(f"Verbindung von {remote_addr} abgelehnt. {error_message}")
            await ws.close(code=WSCloseCode.POLICY_VIOLATION, message=error_message.encode('utf-8'))
            return ws
    elif query_player_name and query_table_name:
        try:
            engine = factory.get_or_create_engine(query_table_name)
            # Optional: Prüfen, ob der Spieler mit gleichem Namen schon als Client am Tisch ist
            # (Diese Logik kann auch in engine.join_client() liegen)
            # ...
            client_obj = Client(name=query_player_name, websocket=ws, interrupt_event=engine.interrupt_event)
        except ValueError as ve:
            error_message = f"Fehler bei Tisch/Spielername: {ve}"
            logger.warning(f"Verbindung von {remote_addr} abgelehnt. {error_message}")
            await ws.close(code=WSCloseCode.POLICY_VIOLATION, message=error_message.encode('utf-8'))
            return ws

        if not await engine.join_client(client_obj):  # join_client setzt client_obj.player_index
            error_message = f"Kein freier Platz am Tisch '{engine.table_name}' oder Spieler konnte nicht beitreten."
            logger.warning(f"Verbindung von {remote_addr} abgelehnt. {error_message}")
            await ws.close(code=WSCloseCode.POLICY_VIOLATION, message=error_message.encode('utf-8'))
            return ws
        logger.info(f"Client {client_obj.name} (Session {client_obj.session}) erfolgreich Tisch '{engine.table_name}' mit Sitzplatz {client_obj.player_index} beigetreten.")
    else:
        error_message = "Ungültige Verbindungsparameter. Benötigt 'session_id' oder 'player_name' & 'table_name'."
        logger.warning(f"Verbindung von {remote_addr} abgelehnt. {error_message}")
        await ws.close(code=WSCloseCode.POLICY_VIOLATION, message=error_message.encode('utf-8'))
        return ws

    # Sicherstellen, dass wir hier einen validen client_obj und engine haben
    if not client_obj or not engine:
        logger.error(f"Kritischer Fehler: Client oder Engine nicht initialisiert nach Join-Logik für {remote_addr}.")
        await ws.close(code=WSCloseCode.INTERNAL_ERROR, message="Interne Server Initialisierung fehlgeschlagen.".encode('utf-8'))
        return ws

    # -------------------------------------------------------------------------
    # 2. Sende joined_confirmation
    # -------------------------------------------------------------------------
    # TODO: Die GameEngine sollte eine Methode bereitstellen, um den aktuellen
    # PublicState und den relevanten PrivateState für einen Spieler zu bekommen.
    # Beispiel: public_state_dict = engine.get_current_public_state().to_dict()
    #           private_state_dict = engine.get_private_state_for_player(client_obj.player_index).to_dict()

    # Für den Anfang: Dummy-States oder Basis-States
    # Annahme: engine.players und client_obj.player_index sind jetzt gesetzt.
    # Die `to_dict()` Methoden in PublicState/PrivateState erzeugen snake_case Keys.

    # Erzeuge einen initialen PublicState, falls die Engine keinen liefert
    # Dieser Block sollte idealerweise durch engine.get_states() ersetzt werden
    if hasattr(engine, "public_state_instance") and engine.public_state_instance:  # Annahme: Engine hat eine property
        public_state_data = engine.public_state_instance.to_dict()
    else:
        public_state_data = PublicState(
            table_name=engine.table_name,
            player_names=[p.name for p in engine.players],
            # Weitere sinnvolle Initialwerte für einen gerade gejointen Spieler
        ).to_dict()

    if hasattr(engine, "get_private_state_for_player") and client_obj.player_index is not None:
        private_state_instance = engine.get_private_state_for_player(client_obj.player_index)
        private_state_data = private_state_instance.to_dict() if private_state_instance else PrivateState(player_index=client_obj.player_index).to_dict()
    else:
        private_state_data = PrivateState(player_index=client_obj.player_index).to_dict()

    await client_obj.send_message("joined_confirmation", {  # send_message ist eine neue Hilfsmethode in Client
        "session_id": client_obj.session,
        "public_state": public_state_data,
        "private_state": private_state_data,
    })

    # TODO: Benachrichtige andere Spieler über den Join via engine.broadcast(...)
    # Dies würde dann client.send_message("notification", {event:"player_joined", ...}) für andere auslösen.
    # await engine.broadcast_player_joined(client_obj)

    # -------------------------------------------------------------------------
    # 3. Haupt-Nachrichtenschleife
    # -------------------------------------------------------------------------
    try:
        msg_aio: WSMessage  # Typ-Annotation für msg aus aiohttp
        async for msg_aio in ws:
            if not client_obj.is_connected:  # Erneute Prüfung, falls sich Status geändert hat
                logger.warning(f"Nachricht von {client_obj.name} empfangen, obwohl intern als disconnected markiert (Schleifenbeginn).")
                break

            if msg_aio.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg_aio.data)
                    logger.debug(f"Empfangen TEXT von {client_obj.name}: {json.dumps(data)}")

                    if not isinstance(data, dict):
                        await client_obj.send_error(101, "Ungültiges Nachrichtenformat (kein dict).", {"raw_message": msg_aio.data})
                        continue

                    msg_type = data.get("type")
                    payload = data.get("payload", {})

                    if msg_type == "leave":
                        logger.info(f"Client {client_obj.name} (Session {client_obj.session}) hat 'leave' gesendet.")
                        # Hier explizit markieren, dass der Client gehen will, bevor der finally-Block greift
                        client_obj.wants_to_leave = True  # Neues Flag in Client-Klasse
                        break  # Springt zum finally Block

                    elif msg_type == "ping":
                        timestamp = payload.get("timestamp")
                        logger.info(f"{client_obj.name}: ping empfangen um {datetime.now()} mit Client-Timestamp {timestamp}")
                        await client_obj.send_message("pong", {"timestamp": timestamp})

                    elif msg_type == "interrupt_request":
                        reason = payload.get("reason")
                        logger.info(f"{client_obj.name} fordert Interrupt: '{reason}'")
                        # Die Engine validiert und sendet ggf. Notifications oder eine neue Request an den Client
                        await engine.on_interrupt(client_obj, reason)

                    elif msg_type == "response":
                        request_id = payload.get("request_id")
                        response_data = payload.get("data", {})
                        if not request_id:
                            await client_obj.send_error(300, "Antwort ohne request_id erhalten.", payload)  # INVALID_ACTION oder spezifischer
                            continue
                        logger.info(f"{client_obj.name}: response für request_id '{request_id}' mit Daten {response_data}")
                        # Die Client-Klasse hat die Logik, um die response_future zu finden und zu setzen
                        await client_obj.on_websocket_response(request_id, response_data)

                    # elif msg_type == "lobby_action":
                    #     action = payload.get("action")
                    #     action_data = payload.get("data", {})
                    #     logger.info(f"{client_obj.name} sendet lobby_action: {action} mit Daten {action_data}")
                    #     await engine.on_lobby_action(client_obj, action, action_data) # Engine validiert & broadcastet

                    else:
                        logger.warning(f"Unbekannter Nachrichtentyp '{msg_type}' von {client_obj.name}.")
                        await client_obj.send_error(101, f"Unbekannter Nachrichtentyp '{msg_type}'.")

                except json.JSONDecodeError:
                    logger.exception(f"Ungültiges JSON von {client_obj.name}: {msg_aio.data}")
                    await client_obj.send_error(101, "Ungültiges JSON-Format.", {"raw_data": msg_aio.data})
                except PlayerDisconnectedError:  # Falls send_error/send_message dies auslöst
                    logger.warning(f"Versuch, an bereits getrennten Client {client_obj.name} zu senden. Breche ab.")
                    break
                except Exception as e_inner:
                    logger.exception(f"Fehler bei Verarbeitung der Nachricht von {client_obj.name}: {e_inner}")
                    # Versuche, einen generischen Fehler zu senden, wenn die Verbindung noch steht
                    if client_obj.is_connected:
                        await client_obj.send_error(100, "Interner Fehler bei Nachrichtenverarbeitung.", {"exception_type": type(e_inner).__name__})


            elif msg_aio.type == WSMsgType.ERROR:
                logger.error(f'WebSocket-Fehler für {client_obj.name}: {ws.exception()}')
                break
            elif msg_aio.type == WSMsgType.CLOSED:  # Client hat die Verbindung aktiv geschlossen
                logger.info(f"WebSocket-CLOSE Nachricht von {client_obj.name} empfangen.")
                client_obj.wants_to_leave = True  # Markieren, dass der Client nicht unerwartet weg ist
                break

    except asyncio.CancelledError:
        logger.debug(f"WebSocket Handler für {client_obj.name if client_obj else remote_addr} abgebrochen (Server Shutdown).")
        if client_obj: client_obj.is_shutting_down = True  # Flag für Aufräumlogik
        raise
    except Exception as e:
        logger.exception(f"Unerwarteter Fehler in WebSocket-Handler für {client_obj.name if client_obj else remote_addr}: {e}")
    finally:
        # -------------------------------------------------------------------------
        # 4. Aufräumen (Kick-Out-Timer, KI-Ersetzung, Tisch schließen)
        # -------------------------------------------------------------------------
        if client_obj and engine:
            logger.info(f"Beginne Aufräumarbeiten für Client {client_obj.name} (Session {client_obj.session}) am Tisch {engine.table_name}.")

            # client_obj.is_connected prüft, ob self._websocket und nicht closed ist.
            # wants_to_leave wird gesetzt, wenn Client "leave" sendet oder WS aktiv schließt.
            # is_shutting_down wird gesetzt, wenn der Server herunterfährt.

            is_unexpected_disconnect = not client_obj.wants_to_leave and not client_obj.is_shutting_down and not client_obj.is_connected  # True, wenn Verbindung weg ohne "leave"

            if is_unexpected_disconnect:
                logger.info(f"{engine.table_name}, Spieler {client_obj.name}: Unerwarteter Verbindungsabbruch. Starte Kick-Out-Timer ({config.KICK_OUT_TIME}s)...")
                await client_obj.mark_as_temporarily_disconnected()  # Interner Status für Reconnect-Fenster

                await asyncio.sleep(config.KICK_OUT_TIME)

                if client_obj.is_connected:  # Hat sich in der Zwischenzeit wiederverbunden (set_websocket wurde gerufen)
                    logger.info(f"{engine.table_name}, Spieler {client_obj.name}: Wiederverbunden innerhalb der Kick-Out-Zeit.")
                    # Nichts weiter zu tun, die neue WS-Schleife läuft (oder wird gestartet, je nach Implementierung)
                else:
                    logger.info(f"{engine.table_name}, Spieler {client_obj.name}: Kick-Out-Zeit abgelaufen. Wird permanent entfernt.")
                    await client_obj.mark_as_permanently_disconnected()  # Setzt is_connected = False final
                    num_human_players_left = await engine.handle_player_departure(client_obj)
                    if num_human_players_left == 0:
                        await factory.remove_engine(engine.table_name)
            else:  # Geordneter Abgang (leave, quit, server shutdown) oder schon als permanent disconnected markiert
                if not client_obj.is_permanently_disconnected:  # Sicherstellen, dass es nicht doppelt passiert
                    await client_obj.mark_as_permanently_disconnected()
                    num_human_players_left = await engine.handle_player_departure(client_obj)
                    if num_human_players_left == 0 and not client_obj.is_shutting_down:  # Engine nur entfernen, wenn nicht Server-Shutdown
                        await factory.remove_engine(engine.table_name)

            # Schließe die WebSocket serverseitig, falls sie noch offen ist und nicht vom Client geschlossen wurde
            if not ws.closed:
                logger.info(f"Schließe WebSocket serverseitig für {client_obj.name} (nach Aufräumen).")
                await ws.close(code=WSCloseCode.GOING_AWAY, message="Verbindung wird nach Verarbeitung serverseitig geschlossen".encode('utf-8'))

        elif client_obj:
            logger.error(f"Aufräumen: Client {client_obj.name} vorhanden, aber keine Engine. Markiere als permanent getrennt.")
            await client_obj.mark_as_permanently_disconnected()  # Sicherstellen, dass der Status konsistent ist
            if not ws.closed: await ws.close()

        logger.debug(f"WebSocket-Handler für {client_obj.name if client_obj else remote_addr} definitiv beendet.")
    return ws


# --- Notwendige Ergänzungen / Änderungen in anderen Klassen ---

# In src/players/client.py:
class Client(Player):
    def __init__(self, name: str, websocket: WebSocketResponse, interrupt_event: asyncio.Event, ...):
        super().__init__(name, ...)
        self._websocket = websocket
        # ...
        self.wants_to_leave: bool = False  # NEU
        self.is_shutting_down: bool = False  # NEU
        self._is_temporarily_disconnected: bool = False  # NEU
        self._is_permanently_disconnected: bool = False  # NEU

    @property
    def is_connected(self) -> bool:
        # Berücksichtigt jetzt _is_permanently_disconnected
        return not self._is_permanently_disconnected and self._websocket is not None and not self._websocket.closed

    @property
    def is_permanently_disconnected(self) -> bool:  # Getter für den neuen Status
        return self._is_permanently_disconnected

    async def set_websocket(self, new_websocket: WebSocketResponse):
        logger.info(f"Aktualisiere WebSocket für Client {self._name} ({self._session}).")
        # Alte WS schließen, falls vorhanden und offen
        if self._websocket and not self._websocket.closed:
            logger.debug(f"Schließe alte WebSocket für {self.name} bei Reconnect.")
            await self._websocket.close(code=WSCloseCode.SERVICE_RESTART, message="Neuere Verbindung hergestellt".encode('utf-8'))

        self._websocket = new_websocket
        self._is_permanently_disconnected = False  # Bei neuem WS ist man nicht mehr permanent weg
        self._is_temporarily_disconnected = False
        self.wants_to_leave = False
        # self.is_shutting_down bleibt davon unberührt, da es ein Server-Event ist

        # Ggf. offene Anfragen der alten Verbindung abbrechen (deine bestehende Logik)
        # ...

    async def send_message(self, msg_type: str, payload: Optional[dict] = None):
        if not self.is_connected:
            logger.warning(f"Versuch, Nachricht {msg_type} an nicht verbundenen Client {self.name} zu senden.")
            raise ClientDisconnectedError(f"Client {self.name} ist nicht verbunden (send_message).")
        if payload is None:
            payload = {}
        message = {"type": msg_type, "payload": payload}
        try:
            logger.debug(f"Sende Nachricht an {self.name}: {json.dumps(message)}")
            await self._websocket.send_json(message)
        except (ConnectionResetError, asyncio.CancelledError, RuntimeError) as e:
            logger.warning(f"Senden der Nachricht {msg_type} an {self.name} fehlgeschlagen (Verbindungsfehler): {e}")
            # Hier den Client als getrennt markieren, wenn ein Sendefehler auftritt
            await self.mark_as_permanently_disconnected()  # Oder zumindest temporarily und die Schleife oben fängt es
            raise ClientDisconnectedError(f"Senden der Nachricht {msg_type} fehlgeschlagen.") from e
        except Exception as e:  # Andere unerwartete Fehler
            logger.exception(f"Unerwarteter Fehler beim Senden von {msg_type} an {self.name}: {e}")
            await self.mark_as_permanently_disconnected()
            raise PlayerDisconnectedError(f"Unerwarteter Sendefehler bei {msg_type}.") from e

    async def send_error(self, code: int, message_text: str, details: Optional[dict] = None, original_request_id: Optional[str] = None):
        # Stellt sicher, dass wir nur senden, wenn die Verbindung noch da ist
        if not self.is_connected:  # Prüft _is_permanently_disconnected und _websocket state
            logger.warning(f"Kann Fehler nicht an Client {self.name} senden (nicht verbunden): Code {code}, Msg: {message_text}")
            return

        error_payload = {"code": code, "message": message_text}
        if details:
            error_payload["details"] = details
        if original_request_id:
            error_payload["original_request_id"] = original_request_id

        await self.send_message("error", error_payload)

    async def mark_as_temporarily_disconnected(self):
        logger.info(f"Client {self.name} als temporär getrennt markiert.")
        self._is_temporarily_disconnected = True
        # Wichtig: _websocket hier NICHT auf None setzen, da die aiohttp-Schleife noch darüber iteriert
        # und wir sonst bei ws.closed einen Fehler bekommen könnten.
        # is_connected wird dadurch false, wenn das WebSocket-Objekt selbst closed ist.

    async def mark_as_permanently_disconnected(self):
        logger.info(f"Client {self.name} als permanent getrennt markiert.")
        self._is_permanently_disconnected = True
        self._is_temporarily_disconnected = False  # Sicherstellen
        # Wenn die WebSocket noch existiert und nicht geschlossen ist, jetzt schließen.
        if self._websocket and not self._websocket.closed:
            logger.debug(f"Schließe WebSocket für permanent getrennten Client {self.name}.")
            await self._websocket.close(code=WSCloseCode.NORMAL_CLOSURE, message="Client permanent entfernt".encode('utf-8'))
        self._websocket = None  # Referenz entfernen

    async def on_websocket_response(self, request_id: str, data: dict):  # Deine bestehende Logik
        if request_id in self._pending_requests:
            future = self._pending_requests.pop(request_id)  # Entfernen nachdem es geholt wurde
            if not future.done():
                future.set_result(data)
                logger.debug(f"Client {self.name}: Antwort für '{request_id}' an wartende Methode weitergeleitet.")
            else:
                logger.warning(f"Client {self.name}: Antwort für bereits abgeschlossene Future für '{request_id}' erhalten.")
        else:
            logger.warning(f"Client {self.name}: Unerwartete Antwort für '{request_id}' (keine wartende Anfrage).")
            await self.send_error(300, "Unerwartete Antwort erhalten (keine passende Anfrage-ID).", {"received_request_id": request_id})

    # Die _ask Methode und die Aktionsmethoden (play, announce etc.) in Client
    # müssen jetzt `self.send_message("request", ...)` verwenden und auf die Future warten.
    # Hier ein Beispiel für _ask:
    async def _ask(self, action_type: str, context_payload: Optional[dict] = None, timeout: float = config.DEFAULT_REQUEST_TIMEOUT) -> dict:
        if not self.is_connected:
            raise ClientDisconnectedError(f"Client {self.name} ist nicht verbunden (_ask).")

        request_id = str(uuid4())
        logger.debug(f"Client {self.name}: Starte Anfrage '{action_type}' mit request_id '{request_id}'.")

        loop = asyncio.get_running_loop()
        response_future = loop.create_future()
        self._pending_requests[request_id] = response_future

        # TODO: Engine sollte aktuellen PublicState und PrivateState für den Kontext bereitstellen
        # Annahme: Engine liefert die States für den Request-Kontext
        current_public_state_dict = self.engine.public_state_instance.to_dict()  # Annahme: Client hat Referenz zur Engine
        current_private_state_dict = self.engine.get_private_state_for_player(self.player_index).to_dict()

        request_payload = {
            "request_id": request_id,
            "action": action_type,
            "public_state": current_public_state_dict,
            "private_state": current_private_state_dict
        }
        if context_payload:  # z.B. action_space
            request_payload["context"] = context_payload

        try:
            await self.send_message("request", request_payload)
        except ClientDisconnectedError:  # Erneut fangen, falls send_message fehlschlägt
            self._pending_requests.pop(request_id, None)  # Future entfernen
            raise

        # Warten auf Antwort (mit Interrupt-Logik, wie in deiner Client-Klasse bereits angedacht)
        # Deine bestehende Logik für asyncio.wait mit interrupt_event und Timeout hier...
        # Beispiel verkürzt:
        done, pending = set(), set()
        try:
            done, pending = await asyncio.wait(
                [response_future, asyncio.create_task(self._interrupt_event.wait())],
                timeout=timeout,
                return_when=asyncio.FIRST_COMPLETED
            )
            # Auswertung von done/pending hier (Timeout, Interrupt, Erfolg)
            if response_future.done():
                if response_future.cancelled(): raise asyncio.CancelledError()
                return response_future.result()  # Das ist das "data" payload von der Client-Antwort
            elif self._interrupt_event.is_set():
                raise PlayerInterruptError()  # Deine Exception
            else:  # Timeout
                raise PlayerTimeoutError()  # Deine Exception
        finally:
            for task in pending: task.cancel()
            self._pending_requests.pop(request_id, None)  # Sicherstellen, dass Future entfernt wird

# In src/game_engine.py:
# async def handle_player_departure(self, departing_client: Client) -> int:
#     logger.info(f"Spieler {departing_client.name} verlässt Tisch {self.table_name}.")
#     # Hier die Logik, um den Client durch einen Default-Agenten zu ersetzen
#     # Annahme: self._default_agents[departing_client.player_index] ist der passende Agent
#     if departing_client.player_index is not None:
#         default_agent = self._default_agents[departing_client.player_index]
#         self._players[departing_client.player_index] = default_agent
#         default_agent.player_index = departing_client.player_index # Sicherstellen
#         logger.info(f"Client {departing_client.name} wurde durch Agent {default_agent.name} ersetzt.")
#         # Benachrichtige andere Spieler
#         await self.broadcast_notification("player_left", {
#             "player_index": departing_client.player_index,
#             "player_name_old": departing_client.name,
#             "replaced_by_ai_name": default_agent.name
#         }, exclude_player=default_agent) # Nicht an den neuen Agenten senden

#     human_players_left = sum(1 for p in self._players if isinstance(p, Client) and p.is_connected)
#     logger.info(f"Verbleibende menschliche Spieler an Tisch {self.table_name}: {human_players_left}")
#     return human_players_left

# async def broadcast_notification(self, event: str, data: dict, exclude_player: Optional[Player] = None):
#     # Hilfsmethode in GameEngine
#     for p in self._players:
#         if p == exclude_player:
#             continue
#         if hasattr(p, 'send_message') and callable(getattr(p, 'send_message')): # Prüft ob es Client ist
#             try:
#                 await p.send_message("notification", {"event": event, "data": data})
#             except ClientDisconnectedError:
#                 logger.warning(f"Konnte Notification '{event}' nicht an getrennten Client {p.name} senden.")