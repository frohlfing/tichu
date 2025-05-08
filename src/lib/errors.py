"""
Definiert die anwendungsspezifischen Laufzeitfehler.
"""

import asyncio

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
