"""
Dieses Modul stellt den Websocket-Handler für den Server bereit.
"""

__all__ = "websocket_handler",

import asyncio
import json
from aiohttp import WSMsgType, WSCloseCode, WSMessage
from aiohttp.web import Request, WebSocketResponse
from src import config
from src.common.logger import logger
from src.game_factory import GameFactory
from src.lib.errors import ErrorCode
from src.players.peer import Peer


async def websocket_handler(request: Request) -> WebSocketResponse | None:
    """
    Behandelt eingehende WebSocket-Verbindungen.

    :param request: Das aiohttp Request-Objekt, das die initiale HTTP-Anfrage enthält.
    :return: Das aiohttp WebSocketResponse-Objekt, das die Verbindung repräsentiert.
    """
    factory: GameFactory = request.app['game_factory']

    # --- 1) WebSocket-Handshake durchführen. ---
    ws = WebSocketResponse()
    try:
        await ws.prepare(request)
    except Exception as e:
        logger.exception(f"[{request.remote}] WebSocket-Handshake fehlgeschlagen: {e}")
        return ws

    # --- 2) Query-String auslesen. ---
    params = request.query  # z.B. ?player_name=Frank&table_name=Tisch1 oder ?session_id=UUID
    remote_addr = request.remote if request.remote else "Unbekannt"  # Client-Adresse
    logger.debug(f"[{remote_addr}] Client verbunden: session_id='{params.get('session_id')}', player_name='{params.get('player_name')}', table_name='{params.get('table_name')}'.")

    # --- 3) Referenz auf die Game-Engine holen, Peer anlegen und der Engine zuordnen. ---
    session_id = params.get("session_id")
    if session_id:
        engine = factory.get_engine_by_session(session_id)
        peer = engine.get_peer_by_session(session_id) if engine else None
        if not peer or not await engine.rejoin_client(peer, websocket=ws):
            error_message = "Session unbekannt."
            logger.warning(f"[{remote_addr}] Verbindung abgelehnt: {error_message} ")
            await ws.close(code=WSCloseCode.POLICY_VIOLATION, message=error_message.encode('utf-8'))
            return ws
        logger.info(f"[{remote_addr}] '{peer.name}' erfolgreich wiederverbunden.")
    else:
        try:
            engine = factory.get_or_create_engine(params.get("table_name"))
            peer = Peer(params.get("player_name"), websocket=ws)
        except ValueError:
            error_message = "Query-Parameter 'player_name' oder 'table_name' fehlerhaft."
            logger.warning(f"[{remote_addr}] Verbindung abgelehnt: {error_message}")
            await ws.close(code=WSCloseCode.POLICY_VIOLATION, message=error_message.encode('utf-8'))
            return ws
        if not await engine.join_client(peer):
            message = f"Kein freier Platz am Tisch '{engine.table_name}'."
            logger.warning(f"[{remote_addr}] Verbindung abgelehnt: {message}")
            await ws.close(code=WSCloseCode.OK, message=message.encode('utf-8'))
            return ws
        logger.info(f"[{remote_addr}] '{peer.name}' am Tisch '{engine.table_name}' beigetreten.")

    # 4) So lange Nachrichten von der WebSocket verarbeiten, bis die Verbindung abbricht oder der Client absichtlich geht.
    try:
        msg: WSMessage
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    if not isinstance(data, dict):
                        logger.warning(f"[{remote_addr}] Ungültiges Nachrichtenformat empfangen: {msg.data}")
                        await peer.error("Ungültiges Nachrichtenformat", ErrorCode.INVALID_MESSAGE, context=msg.data)
                        continue
                    msg_type = data.get("type")  # Nachrichtentyp
                    payload = data.get("payload", {})  # die Nutzdaten
                    logger.debug(f"[{remote_addr}] Nachricht '{msg_type}' empfangen.")

                    if msg_type == "leave":  # der Client verlässt den Tisch.
                        break  # aus der Message-Loop springen

                    elif msg_type == "swap_players":  # der Client möchte die Plätze zweier Spieler vertauschen).
                        if not await engine.swap_players(payload.get("player_index_1"), payload.get("player_index_2")):
                            await peer.error("Die Spieler konnten nicht vertauscht werden.", ErrorCode.INVALID_MESSAGE, context=payload)

                    elif msg_type == "start_game":
                        if not await engine.start_game():
                            await peer.error("Es konnte keine neue Partie gestartet werden. Es läuft bereits eine.", ErrorCode.INVALID_MESSAGE, context=payload)

                    elif msg_type == "announce":  # proaktive Tichu-Ansage vom Client
                        if not await engine.set_announcement(peer.priv.player_index):
                            await peer.error("Tichu-Ansage abgelehnt.", ErrorCode.INVALID_ANNOUNCE)

                    elif msg_type == "bomb":  # proaktiver Bombenwurf vom Client
                        await peer.client_bomb(payload.get("cards"))

                    elif msg_type == "response":  # Antwort auf eine vorherige Anfrage
                        await peer.client_response(payload.get("action"), payload.get("response_data", {}))

                    else:  # Nachrichtentyp unbekannt
                        logger.error(f"[{remote_addr}] Message-Type '{msg_type}' unbekannt.")
                        await peer.error("Message-Type unbekannt.", ErrorCode.INVALID_MESSAGE, context=msg.data)

                except json.JSONDecodeError:
                    logger.exception(f"[{remote_addr}] Ungültiges JSON: {msg.data}")
                    await peer.error("Ungültiges JSON-Format.", ErrorCode.INVALID_MESSAGE, context=msg.data)

                except Exception as send_e:
                    logger.exception(f"[{remote_addr}] Unerwarteter Fehler. Verarbeitung der Nachricht fehlgeschlagen: {send_e}")
                    await peer.error("Fehler bei der Verarbeitung der Nachricht.", ErrorCode.UNKNOWN_ERROR, context=msg.data)

            elif msg.type == WSMsgType.BINARY:
                logger.warning(f"[{remote_addr}] Unerwartete Binary-Daten empfangen.")

            elif msg.type == WSMsgType.ERROR:
                logger.error(f"[{remote_addr}] WebSocket-Fehler: {ws.exception()}.")
                break  # Message-Loop verlassen, da die Verbindung gestört ist

            elif msg.type == WSMsgType.CLOSE:  # der Client hat die Verbindung aktiv geschlossen (normaler Vorgang)
                logger.debug(f"[{remote_addr}] '{peer.name}' hat die Verbindung geschlossen.")
                break  # Message-Loop verlassen

    except asyncio.CancelledError:  # der Server wird heruntergefahren (z.B. durch Signal)
        logger.debug(f"[{remote_addr}] Server Shutdown. WebSocket-Handler abgebrochen.")
        raise  # Wichtig: CancelledError weitergeben für sauberes Beenden.

    # except ConnectionResetError as e:
    #     # Dies fängt den "[WinError 10054] Eine vorhandene Verbindung wurde vom Remotehost geschlossen" sauber ab!
    #     logger.info(f"[{remote_addr}] Verbindung von '{peer.name}' abrupt zurückgesetzt. Client hat wahrscheinlich den Browser geschlossen.")

    # except ClientConnectorError as e:
    #     # aiohttp kann auch andere, höherlevelige Verbindungsfehler werfen.
    #     logger.info(f"[{remote_addr}] aiohttp-Verbindungsfehler bei '{peer.name}': {e}")

    except Exception as e:  # fängt unerwartete Fehler während der Verbindung oder im Handler ab
        logger.exception(f"[{remote_addr}] Unerwarteter Fehler. WebSocket-Handler abgebrochen: {e}")

    # 5) Bei Verbindungsabbruch etwas warten, vielleicht schlüpft der Client erneut in sein altes Ich. Ansonsten WebSocket-Verbindung serverseitig schließen.
    if ws.closed:  # not peer.is_connected:
        # Verbindungsabbruch
        logger.info(f"[{remote_addr}] Verbindungsabbruch für Spieler '{peer.name}'. Starte Kick-Out-Timer...")
        # await asyncio.sleep(config.KICK_OUT_TIME)
        if await peer.wait_for_reconnect(config.KICK_OUT_TIME):
            logger.info(f"[{remote_addr}] Kick-Out-Timer gestoppt. Spieler '{peer.name}' hat sich wieder verbunden.")
            return ws  # keine weiteren Aufräumarbeiten erforderlich
        else:
            logger.info(f"[{remote_addr}] Kick-Out-Zeit abgelaufen. Spieler '{peer.name}' hat sich nicht wieder verbunden.")
    else:
        # Client will gehen
        try:
            await ws.close(code=WSCloseCode.GOING_AWAY, message="Verbindung wird serverseitig beendet".encode('utf-8'))
        except Exception as close_e:
            logger.exception(f"[{remote_addr}] Unerwarteter Fehler. Verbindung serverseitig unsauber beendet: {close_e}")

    # 6) Wenn es noch menschliche Mitspieler gibt, einen Fallback-Agent einsetzen, ansonst Tisch schließen.
    client_exists = any(isinstance(p, Peer) for p in engine.players if p.session_id != peer.session_id)
    if client_exists:
        if not await engine.leave_client(peer):  # der Fallback-Agent spielt jetzt weiter
            logger.error(f"[{remote_addr}] '{peer.name}' am Tisch `{engine.table_name}` nicht gefunden, verlässt ihn aber.")
    else:
        await factory.remove_engine(engine.table_name)
    return ws
