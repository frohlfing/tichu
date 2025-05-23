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

# Enum für Errorcodes (Auskommentierte Codes werden noch nicht benutzt!)
class ErrorCode(enum.IntEnum):
    # Allgemeine Fehler (100-199)
    UNKNOWN_ERROR = 100  # Ein unbekannter Fehler ist aufgetreten.
    INVALID_MESSAGE = 101  # Ungültiges Nachrichtenformat empfangen.
    #UNAUTHORIZED = 102  # Aktion nicht autorisiert.
    #SERVER_BUSY = 103  # Der Server ist momentan überlastet. Bitte später versuchen.
    #MAINTENANCE_MODE = 104  # Der Server befindet sich im Wartungsmodus.

    # Verbindungs- & Session-Fehler (200-299)
    SESSION_EXPIRED = 200  # Deine Session ist abgelaufen. Bitte neu verbinden.
    SESSION_NOT_FOUND = 201  # Session nicht gefunden.
    #TABLE_NOT_FOUND = 202  # Tisch nicht gefunden.
    #TABLE_FULL = 203  # Der Tisch ist bereits voll.
    #NAME_TAKEN = 204  # Dieser Spielername ist an diesem Tisch bereits vergeben.
    #ALREADY_ON_TABLE = 205  # Du bist bereits an diesem Tisch.

    # Spiellogik-Fehler (300-399)
    #INVALID_ACTION = 300  # Ungültige Aktion.
    #INVALID_CARDS = 301  # Ausgewählte Karten sind ungültig für diese Aktion.
    #NOT_YOUR_TURN = 302  # Du bist nicht am Zug.
    #INTERRUPT_DENIED = 303  # Interrupt-Anfrage abgelehnt.
    #INVALID_WISH = 304  # Ungültiger Kartenwunsch.
    #INVALID_SCHUPF = 305  # Ungültige Karten für den Schupf-Vorgang. context: {request_id: uuid}
    #ACTION_TIMEOUT = 306  # Zeit für Aktion abgelaufen. context: {timeout: seconds, request_id: uuid}

    # Lobby-Fehler (400-499)
    #GAME_ALREADY_STARTED = 400  # Das Spiel an diesem Tisch hat bereits begonnen. context: {table_name: str}
    #NOT_LOBBY_HOST = 401  # Nur der Host kann diese Aktion ausführen. context: {action: str}
