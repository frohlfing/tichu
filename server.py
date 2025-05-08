#!/usr/bin/env python

# todo alles überarbeiten

"""
Webserver für Tichu.

Startet einen aiohttp-Server, der einen WebSocket-Endpunkt bereitstellt, über den Clients (Spieler) mit dem Spiel
interagieren können. Verwaltet den Server-Lebenszyklus und Signal-Handling für sauberes Beenden.
"""

import asyncio
import config
import json
import os
import signal
import sys
from aiohttp import WSMsgType, WSCloseCode, WSMessage
from aiohttp.web import Application, AppRunner, Request, WebSocketResponse, TCPSite
from src.common.logger import logger
from src.game_factory import GameFactory
from _dev.altkram.lobby import Lobby
from src.players.client import Client


async def websocket_handler(request: Request) -> WebSocketResponse | None:
    """
    Behandelt eingehende WebSocket-Verbindungen.

    :param request: Das aiohttp Request-Objekt, das die initiale HTTP-Anfrage enthält.
    :return: Das aiohttp WebSocketResponse-Objekt, das die Verbindung repräsentiert.
    """
    lobby: Lobby = request.app['lobby']
    factory: GameFactory = request.app['game_factory']

    # WebSocket-Handshake durchführen
    ws = WebSocketResponse()
    try:
        await ws.prepare(request)
    except Exception as e:
        logger.exception(f"WebSocket Handshake fehlgeschlagen für {request.remote}: {e}")
        return ws

    # Query-String auslesen
    params = request.query  # z.B. ?playerName=Frank&tableName=Tisch1[&session=UUID]
    remote_addr = request.remote if request.remote else "Unbekannt"  # Client-Adresse
    logger.info(f"WebSocket Verbindung hergestellt von {remote_addr} mit Parametern: {params}")

    # Referenz auf die Game-Engine holen, Client anlegen und der Engine zuordnen
    session = params.get("session")
    if session:
        engine = factory.get_engine_by_session(session)
        client = engine.get_player_by_session(session) if engine else None
        if isinstance(client, Client) and not client.is_connected:
            client.set_websocket(ws)
        else:
            error_message = "Query-Parameter 'session' fehlerhaft."
            logger.warning(f"Verbindung von {remote_addr} abgelehnt. {error_message}")
            await ws.close(code=WSCloseCode.POLICY_VIOLATION, message=error_message.encode('utf-8'))
            return ws
        logger.info(f"Client {client.name} (Session {client.session}) erfolgreich wiederverbunden.")
    else:
        try:
            engine = factory.get_or_create_engine(params.get("tableName"))
            client = Client(params.get("playerName"), websocket=ws, interrupt_events=engine.interrupt_events, session=session) if engine else None
        except ValueError:
            error_message = "Query-Parameter 'playerName' oder 'tableName' fehlerhaft."
            logger.warning(f"Verbindung von {remote_addr} abgelehnt. {error_message}")
            await ws.close(code=WSCloseCode.POLICY_VIOLATION, message=error_message.encode('utf-8'))
            return ws

        # Sitzplatz suchen, der von der KI besetzt ist (diesen werden wir kapern)
        available_index = -1
        for i, p in enumerate(engine.players):
            if not isinstance(p, Client):
                available_index = i
                break
        if available_index == -1:
            error_message = f"Kein freier Platz am Tisch '{engine.table_name}'."
            logger.warning(f"Verbindung von {remote_addr} abgelehnt. {error_message}")
            await ws.close(code=WSCloseCode.POLICY_VIOLATION, message=error_message.encode('utf-8'))
            return ws

        # Sitzplatz zuordnen
        client.player_index = available_index
        await engine.replace_player(client)
        logger.info(f"Client {client.name} (Session {client.session}) erfolgreich am Tisch '{engine.table_name}' mit Sitzplatz {client.player_index} zugeordnet.")

    # Bestätigung an den Client senden
    try:
        await client.notify("joined_table", {
            "playerName": client.name,
            "tableName": engine.table_name,
            "playerIndex": client.player_index,
            "session": client.session,
        })
    except Exception as e:
        logger.warning(f"Senden der Beitrittsbestätigung an {client.name} fehlgeschlagen: {e}.")
        return ws

    # solange Nachrichten von der Websocket verarbeiten, bis die Verbindung abbricht oder der Benutzer absichtlich geht
    try:
        await client.message_loop()
    except Exception as e:
        logger.exception(f"{engine.table_name}, Spieler {client.name}: Unerwarteter Fehler in der Nachrichtenschleife: {e}")

    # bei Verbindungsabbruch etwas warten, vielleicht schlüpft der Benutzer erneut in sein altes Ich
    if not websocket.open:
        logger.debug(f"{engine.table_name}, Spieler {client.name}: Kick-Out-Timer started...")
        await asyncio.sleep(config.KICK_OUT_TIME)
        if client.websocket.id != websocket.id:
            logger.debug(f"{engine.table_name}, Spieler {client.name}: Kick-Out-Zeit abgelaufen. Der Spieler hat sich inzwischen wieder verbunden.")
            return ws  # der Client wurde inzwischen innerhalb eines anderen Aufrufs des Websocket-Händlers übernommen
        logger.debug(f"{engine.table_name}, Spieler {client.name}: Kick-Out-Zeit abgelaufen. Der Spieler hat sich nicht wieder verbunden.")

    # Gibt es noch andere Clients?
    number_of_clients = sum(1 for chair in range(4) if isinstance(engine.get_player(chair), Client))
    if number_of_clients > 1:
        # ja, es gibt weitere Clients
        agent = default_agent(client.canonical_chair, engine)
        await engine.replace_player(agent)  # client in der Engine durch die KI ersetzen, andere wollen ja weiterspielen
    else:
        # es war der letzte Client
        factory.remove_engine(engine)  # Engine entfernen


    try:
        # Haupt-Nachrichtenschleife: Warten auf und Verarbeiten von Client-Nachrichten.
        msg: WSMessage
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                # Ignoriere Nachrichten, wenn der Client intern bereits als getrennt markiert ist.
                if not client.is_connected:
                    logger.warning(f"Handler: Nachricht von {client.name} empfangen, obwohl intern als disconnected markiert.")
                    break  # Schleife verlassen -> finally wird ausgeführt.
                try:
                    # Versuche, die Textnachricht als JSON zu parsen.
                    data = json.loads(msg.data)
                    logger.debug(f"Empfangen TEXT von {client.name}: {data}") # Log nach erfolgreichem Parsen

                    # Grundlegende Typ-Prüfung
                    if not isinstance(data, dict):
                        logger.warning(f"Handler: Ungültiges Nachrichtenformat (kein dict) von {client.name}: {data}")
                        await client.notify("error", {"message": "Ungültiges Nachrichtenformat."})
                        continue  # Nächste Nachricht

                    response_to = data.get("response_to")  # Ist es eine Antwort auf eine Anfrage?
                    action = data.get("action")  # Ist es eine proaktive Aktion?
                    payload = data.get("payload", {})  # Die Nutzdaten

                    if response_to:
                        # Nachricht ist eine Antwort -> an Client.receive_response leiten
                        logger.debug(f"Handler: Leite Antwort auf '{response_to}' an Client {client.name} weiter.")
                        client.receive_response(response_to, payload)  # Annahme: payload enthält die relevanten Antwortdaten
                    elif action:
                        # Nachricht ist eine proaktive Aktion -> an Engine.handle_player_message leiten
                        # (oder an eine dedizierte Methode wie handle_proactive_action)
                        logger.debug(f"Handler: Leite proaktive Aktion '{action}' an Engine für Tisch '{engine.table_name}' weiter.")
                        # Leite die geparsten Daten zur Verarbeitung an die GameEngine weiter.
                        await engine.handle_player_message(client, data)
                    else:
                        # Nachricht hat weder 'response_to' noch 'action' -> unbekanntes Format
                        logger.warning(f"Unbekanntes Nachrichtenformat von {client.name} (weder Antwort noch Aktion): {data}")
                        await client.notify("error", {"message": "Unbekanntes Nachrichtenformat."})
                except json.JSONDecodeError:
                    # Fehler beim Parsen von JSON. Informiere Client.
                    logger.exception(f"Ungültiges JSON von {client.name}: {msg.data}")
                    await client.notify("error", {"message": "Ungültiges JSON Format"})
                except Exception as send_e:
                    logger.exception(f"Fehler bei Verarbeitung der Nachricht von {client.name}: {send_e}")
                    # Sende generische Fehlermeldung an Client.
                    await client.notify("error", {"message": "Fehler bei Verarbeitung Ihrer Anfrage."})

            elif msg.type == WSMsgType.BINARY:
                # Binäre Nachrichten werden aktuell nicht erwartet.
                logger.warning(f"Empfangen unerwartete BINARY Daten von {client.name or remote_addr}")
                # Ignorieren oder spezifische Logik hinzufügen, falls benötigt.

            elif msg.type == WSMsgType.ERROR:
                # aiohttp meldet einen internen WebSocket-Fehler.
                logger.error(f'WebSocket Fehler für {client.name or "unbekannt"}: {ws.exception()}')
                break  # Schleife verlassen -> finally wird ausgeführt.

            elif msg.type == WSMsgType.CLOSE:
                # Der Client hat die Verbindung aktiv geschlossen (normaler Vorgang).
                logger.info(f"WebSocket CLOSE Nachricht von {client.name or 'unbekannt'} empfangen.")
                break  # Schleife verlassen -> finally wird ausgeführt.

    except asyncio.CancelledError:
        # Der Server wird heruntergefahren (z.B. durch Signal).
        client_name_log = client.name if client else remote_addr
        logger.info(f"WebSocket Handler für {client_name_log} abgebrochen (Server Shutdown).")
        raise  # Wichtig: CancelledError weitergeben für sauberes Beenden.
    except Exception as e:
        # Fängt unerwartete Fehler während der Verbindung oder im Handler ab.
        client_name_log = client.name if client else "unbekannt"
        logger.exception(f"Unerwarteter Fehler im WebSocket Handler für {client_name_log} von {remote_addr}: {e}")
    finally:
        # Dieser Block wird immer ausgeführt, wenn der Handler endet
        # (durch normalen Close, Fehler, CancelledError, etc.).
        client_name_log = client.name if client else 'N/A'
        client_id_log = client.session if client else 'N/A'
        table_name_log = engine.table_name if engine else 'N/A'
        logger.info(f"WebSocket Verbindung schließt für {client_name_log} ({client_id_log}) von {remote_addr}, Tisch: '{table_name_log}'")

        # Informiere die Factory über den Disconnect, damit der Timer gestartet werden kann.
        # Dies geschieht nur, wenn Client und Engine erfolgreich initialisiert wurden.
        if client and engine:
            # Ruft die synchrone Methode in der Factory auf.
            factory.notify_player_disconnect(engine.table_name, client.session, client.name)
        # else: # Optional: Loggen, wenn Client/Engine nicht vorhanden waren
        #    if not client: logger.debug(f"Kein Client-Objekt im finally-Block für {remote_addr} vorhanden.")
        #    if not engine: logger.debug(f"Keine Engine-Referenz im finally-Block für {remote_addr} vorhanden.")

        # Sicherstellen, dass die WebSocket-Verbindung serverseitig geschlossen ist.
        if not ws.closed:
            logger.debug(f"Stelle sicher, dass WebSocket für {remote_addr} im finally Block geschlossen wird.")
            try:
                await ws.close(code=WSCloseCode.GOING_AWAY, message="Verbindung wird serverseitig beendet".encode('utf-8'))
            except Exception as close_e:
                logger.warning(f"Fehler beim expliziten Schließen des WebSockets für {remote_addr}: {close_e}")
        logger.info(f"WebSocket Verbindung definitiv geschlossen für {remote_addr}")

    return ws


async def main():
    """
    Haupt-Einstiegspunkt zum Starten des aiohttp Servers.

    Erstellt die aiohttp-Anwendung, initialisiert die GameFactory,
    richtet Routen und Signal-Handler ein und startet den Server.
    Hält den Server am Laufen, bis ein Shutdown-Signal empfangen wird.
    """
    # aiohttp Anwendung erstellen.
    app = Application()

    # GameFactory Instanz erstellen und im App-Kontext speichern.
    # Dadurch ist sie für Handler über request.app['game_factory'] zugänglich.
    lobby = Lobby()
    factory = GameFactory()
    app['lobby'] = lobby
    app['game_factory'] = factory

    # Route für den WebSocket-Endpunkt '/ws' hinzufügen und mit dem Handler verknüpfen.
    app.router.add_get('/ws', websocket_handler)

    # --- Plattformspezifisches Signal Handling ---
    # Notwendig, um auf Strg+C (SIGINT) und Terminate-Signale (SIGTERM) zu reagieren
    # und einen geordneten Shutdown einzuleiten.
    if sys.platform == 'win32':
        # Unter Windows wird signal.signal verwendet, da loop.add_signal_handler nicht unterstützt wird.
        # Nur SIGINT (Strg+C) wird zuverlässig unterstützt.
        signal.signal(signal.SIGINT, shutdown) # Registriert die shutdown Funktion als Handler
        logger.debug("Signal-Handler: Verwende signal.signal für SIGINT unter Windows.")
    else:
        # Unter POSIX-Systemen (Linux, macOS) wird loop.add_signal_handler bevorzugt.
        # Es integriert sich besser in die asyncio Event-Schleife.
        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                # Registriert die shutdown Funktion für SIGINT und SIGTERM.
                loop.add_signal_handler(sig, shutdown, sig) # Übergibt Signalnummer an shutdown
            logger.debug("Signal-Handler: Verwende loop.add_signal_handler für SIGINT und SIGTERM unter POSIX.")
        except NotImplementedError:
            # Fallback für seltene Fälle, wo add_signal_handler nicht verfügbar ist.
            logger.warning("Signal-Handler: loop.add_signal_handler nicht implementiert, falle zurück auf signal.signal für SIGINT.")
            signal.signal(signal.SIGINT, shutdown)

    # Server mit AppRunner und TCPSite starten für mehr Kontrolle.
    runner = AppRunner(app)
    await runner.setup()
    # Server an Host und Port aus der Konfiguration binden.
    site = TCPSite(runner, config.HOST, config.PORT)

    try:
        # Starte den Server und beginne, auf Verbindungen zu lauschen.
        await site.start()
        logger.info(f"aiohttp Server gestartet auf http://{config.HOST}:{config.PORT}")
        logger.info(f"WebSocket verfügbar unter ws://{config.HOST}:{config.PORT}/ws")
        # Hält den Haupt-Task am Laufen, bis ein Ereignis (z.B. CancelledError durch shutdown) eintritt.
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        # Wird ausgelöst, wenn shutdown() die Tasks abbricht.
        logger.info("Haupt-Task abgebrochen, beginne Shutdown-Sequenz.")
    finally:
        # Wird immer ausgeführt, auch bei Fehlern oder Abbruch.
        logger.info("Fahre Server herunter...")
        # Führe zuerst die Cleanup-Operationen der Factory aus (räumt Engines auf).
        await factory.cleanup()
        # Stoppe dann den aiohttp Listener (nimmt keine neuen Verbindungen mehr an).
        await site.stop()
        # Räume die aiohttp AppRunner Ressourcen auf.
        await runner.cleanup()
        logger.info("Server erfolgreich heruntergefahren.")


def shutdown(*_args):
    """
    Leitet den Server-Shutdown ein, indem laufende asyncio-Tasks abgebrochen werden.

    Diese Funktion wird durch die Signal-Handler (SIGINT/SIGTERM) aufgerufen.
    Das Abbrechen der Tasks führt dazu, dass `asyncio.Event().wait()` in `main`
    eine `CancelledError` auslöst, was den `finally`-Block für das
    geordnete Herunterfahren aktiviert.

    :param _args: Akzeptiert variable Argumente (z.B. Signalnummer), die aber nicht verwendet werden.
    """
    logger.info("Shutdown-Signal empfangen.")
    # Finde alle laufenden Tasks außer dem aktuellen Task (dem shutdown-Handler selbst).
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if tasks:
        count = len(tasks)
        logger.info(f'Breche {count} laufende Task{"s" if count > 1 else ""} ab...')
        for task in tasks:
            task.cancel() # Sendet ein CancelledError an den Task.
    else:
        logger.info("Keine laufenden Tasks zum Abbrechen gefunden.")


if __name__ == "__main__":
    # Stellt sicher, dass das Skript nur ausgeführt wird, wenn es direkt gestartet wird.
    # Prüfe, ob aiohttp installiert ist (optional, aber gute Praxis).
    logger.info(f"Starte Tichu Server (PID: {os.getpid()})...") # os importieren
    try:
       asyncio.run(main(), debug=config.DEBUG)
    except KeyboardInterrupt:
       # Fängt Strg+C ab, falls die Signal-Handler aus irgendeinem Grund nicht greifen
       # (sollte unter Windows mit signal.signal passieren).
       logger.info("KeyboardInterrupt im __main__ abgefangen.")
    except Exception as e_top:
        # Fängt alle anderen unerwarteten Fehler beim Start ab.
        logger.exception(f"Unerwarteter Fehler auf Top-Level: {e_top}")
        sys.exit(1) # Beenden mit Fehlercode
    finally:
        logger.info("Server-Prozess beendet.")