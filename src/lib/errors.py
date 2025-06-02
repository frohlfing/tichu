"""
Definiert die anwendungsspezifischen Laufzeitfehler.
"""

__all__ = "PlayerInteractionError", \
    "ClientDisconnectedError", "PlayerInterruptError", "PlayerTimeoutError", "PlayerResponseError", \
    "ErrorCode",

import asyncio
import enum

# class ImmutableError(Exception):
#     # Ausnahme für unveränderliche Objekte.
#
#     def __init__(self, message="This object is immutable"):
#         self.message = message
#         super().__init__(self.message)


class PlayerInteractionError(Exception):
    """
    Basisklasse für Fehler, die während der Interaktion mit einem Spieler auftreten können.
    """
    pass


class ClientDisconnectedError(PlayerInteractionError):
    """
    Wird ausgelöst, wenn versucht wird, eine Aktion mit einem Client auszuführen, der nicht (mehr) verbunden ist.
    """
    def __init__(self, message="Client ist nicht verbunden", *args):
        super().__init__(message, *args)


class PlayerInterruptError(PlayerInteractionError):
    """
    Wird ausgelöst, wenn eine wartende Spieleraktion durch ein Engine-internes Ereignis (z.B. Tichu-Ansage, Bombe) unterbrochen wird.
    """
    def __init__(self, message: str = "Spieleraktion unterbrochen", *args):
        super().__init__(message, *args)


class PlayerTimeoutError(PlayerInteractionError, asyncio.TimeoutError):
    """
    Wird ausgelöst, wenn ein Spieler nicht innerhalb des vorgegebenen Zeitlimits auf eine Anfrage reagiert hat.
    Erbt auch von asyncio.TimeoutError für Kompatibilität.

    :param message: Eine beschreibende Fehlermeldung.
    """
    def __init__(self, message="Zeitlimit für Spieleraktion überschritten", *args):
        super().__init__(message, *args)


class PlayerResponseError(PlayerInteractionError):
    """
    Wird ausgelöst, wenn ein Spieler (Client) eine ungültige, unerwartete oder nicht zum Kontext passende Antwort auf eine Anfrage sendet.

    :param message: Eine beschreibende Fehlermeldung.
    """
    def __init__(self, message="Ungültige oder unerwartete Spielerantwort", *args):
        super().__init__(message, *args)

# todo die ErrorCodes sollten sich nicht mit den WSCloseCode von aiohttp überlappen:
# class WSCloseCode(IntEnum):
#     OK = 1000                   # Kein Fehler
#     GOING_AWAY = 1001           # Server Shutdown oder ein Client hat die Seite verlassen
#     PROTOCOL_ERROR = 1002       # Protokollfehler
#     UNSUPPORTED_DATA = 1003     # Typ der Daten in einer Nachricht nicht akzeptiert (z.B. binär statt Text)
#     ABNORMAL_CLOSURE = 1006     # Verbindung nicht ordnungsgemäß geschlossen
#     INVALID_TEXT = 1007         # Daten in einer Nachricht nicht konsistent mit dem Typ der Nachricht (z.B. nicht-UTF-8 RFC 3629-Daten in einer Textnachricht)
#     POLICY_VIOLATION = 1008     # generell gegen eine Richtlinie verstoßen (kein anderer Statuscode passt).
#     MESSAGE_TOO_BIG = 1009      # Nachricht zu groß
#     MANDATORY_EXTENSION = 1010  # Client hat Verbindung geschlossen wegen Handshake-Fehler (der Server verwendet diesen Code nicht)
#     INTERNAL_ERROR = 1011       # Server hat einen internen Fehler
#     SERVICE_RESTART = 1012      # Server wird neu gestartet
#     TRY_AGAIN_LATER = 1013      # Server ist überlastet
#     BAD_GATEWAY = 1014          # Server empfing eine ungültige Antwort vom Upstream-Server (wie HTTP-Statuscode 502)

# Enum für Errorcodes (Auskommentierte Codes werden noch nicht benutzt!)
class ErrorCode(enum.IntEnum):
    # Allgemeine Fehler (100-199)
    UNKNOWN_ERROR = 100  # Ein unbekannter Fehler ist aufgetreten.
    INVALID_MESSAGE = 101  # Ungültiges Nachrichtenformat empfangen.
    UNKNOWN_CARD = 102  # Mindestens eine Karte ist unbekannt.
    NOT_HAND_CARD = 103  # Mindestens eine Karte ist unbekannt.
    #UNAUTHORIZED = 104  # Aktion nicht autorisiert.
    #SERVER_BUSY = 105  # Der Server ist momentan überlastet. Bitte später versuchen.
    SERVER_DOWN = 106  # Der Server wurde heruntergefahren.
    #MAINTENANCE_MODE = 107  # Der Server befindet sich im Wartungsmodus.

    # Verbindungs- & Session-Fehler (200-299)
    SESSION_EXPIRED = 200  # Deine Session ist abgelaufen. Bitte neu verbinden.
    SESSION_NOT_FOUND = 201  # Session nicht gefunden.
    #TABLE_NOT_FOUND = 202  # Tisch nicht gefunden.
    #TABLE_FULL = 203  # Der Tisch ist bereits voll.
    #NAME_TAKEN = 204  # Dieser Spielername ist an diesem Tisch bereits vergeben.
    #ALREADY_ON_TABLE = 205  # Du bist bereits an diesem Tisch.

    # Spiellogik-Fehler (300-399)
    INVALID_ACTION = 300  # Ungültige Aktion.
    INVALID_RESPONSE = 301 # Keine wartende Anfrage für die Antwort gefunden.
    NOT_UNIQUE_CARDS = 302  # Mindestens zwei Karten sind identisch.
    INVALID_COMBINATION = 303  # Die Karten bilden keine spielbare Kombination.
    #NOT_YOUR_TURN = 304  # Du bist nicht am Zug.
    #INTERRUPT_DENIED = 305  # Interrupt-Anfrage abgelehnt.
    INVALID_WISH = 306  # Ungültiger Kartenwunsch.
    INVALID_ANNOUNCE = 307  # Tichu-Ansage nicht möglich.
    INVALID_DRAGON_RECIPIENT = 308  # Ungültige Wahl für Drachen verschenken.
    #ACTION_TIMEOUT = 309  # Zeit für Aktion abgelaufen.
    REQUEST_OBSOLETE = 310  # Anfrage ist veraltet.

    # Lobby-Fehler (400-499)
    GAME_ALREADY_STARTED = 400  # Das Spiel an diesem Tisch hat bereits begonnen.
    #NOT_LOBBY_HOST = 401  # Nur der Host kann diese Aktion ausführen.
