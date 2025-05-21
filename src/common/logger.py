"""
Diese Datei definiert eine zentrale Logger-Instanz zur Protokollierung von Ereignissen und Ausgaben im System.
Sie unterstützt die Protokollierung in eine Datei sowie die farbliche Ausgabe im Terminal.
"""

__all__ = "logger",

import config
import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from typing import TextIO, Optional

# https://xsnippet.org/359377/

class AnsiColorizer:
    """
    A colorizer is an object that loosely wraps around a stream, allowing
    callers to write text to the stream in a particular color.
    Colorizer classes must implement C{supported()} and C{write(text, color)}.
    """

    _colors = dict(black=30, red=31, green=32, yellow=33, blue=34, magenta=35, cyan=36, white=37)

    def __init__(self, stream: TextIO):
        self.stream = stream

    @classmethod
    def supported(cls, stream: TextIO = sys.stdout) -> bool:
        """
        A class method that returns True if the current platform supports
        coloring terminal output using this method. Returns False otherwise.
        """
        if not stream.isatty():
            return False  # auto color only on TTYs
        try:
            import curses
        except ImportError:
            return False
        else:
            try:
                try:
                    return curses.tigetnum("colors") > 2
                except curses.error:
                    curses.setupterm()
                    return curses.tigetnum("colors") > 2
            except curses.error:
                return False

    def write(self, text: str, color: str) -> None:
        """
        Write the given text to the stream in the given color.

        @param text: Text to be written to the stream.
        @param color: A string label for a color. e.g. "red", "white".
        """
        color_code = self._colors.get(color, 37)  # Default to white if color not found
        self.stream.write(f"\x1b[{color_code}m{text}\x1b[0m")


class ColorStreamHandler(logging.StreamHandler):
    def __init__(self, stream: Optional[TextIO] = sys.stderr):
        super().__init__(stream)
        self.colorizer = AnsiColorizer(stream)

    def emit(self, record: logging.LogRecord) -> None:
        msg_colors = {
            logging.DEBUG: "blue",
            logging.INFO: "green",
            logging.WARNING: "yellow",
            logging.ERROR: "red",
            logging.CRITICAL: "red",
        }

        try:
            msg = self.format(record)
            color = msg_colors.get(record.levelno, "white")
            self.colorizer.write(msg + "\n", color)
            self.flush()
        except (OSError, ValueError):
            self.handleError(record)


# https://docs.python.org/3.7/library/logging.html#logging.info
# https://www.pylenin.com/blogs/python-logging-guide/

# Erstelle einen Logger
logger = logging.getLogger(__name__)
logger.setLevel(config.LOG_LEVEL)

# Erstelle einen Handler für das Schreiben in eine Datei
file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs", "app.log"))
file_handler = TimedRotatingFileHandler(file_path, when="midnight", interval=1, backupCount=config.LOG_COUNT)
file_handler.setLevel(config.LOG_LEVEL)

# Erstelle einen Handler für die Ausgabe in die Konsole
console_handler = ColorStreamHandler(stream=sys.stdout)
console_handler.setLevel(config.LOG_LEVEL)

# Definiere das Format für die Log-Nachrichten
formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s (%(module)s, line %(lineno)d)")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Füge die Handler dem Logger hinzu
logger.addHandler(file_handler)
logger.addHandler(console_handler)


# class Logger:
#     @staticmethod
#     def debug(msg: str):
#         #print(msg)
#         pass
#
#     @staticmethod
#     def info(msg: str):
#         print(msg)
#
#     @staticmethod
#     def warning(msg: str):
#         print(msg)
#
#     @staticmethod
#     def error(msg: str):
#         print(msg)
#
#     @staticmethod
#     def critical(msg: str):
#         print(msg)
#
# logger = Logger()


if __name__ == "__main__":
    logger.debug("Some debugging output")
    logger.info("Some info output")
    logger.warning("Some warning output")
    logger.error("Some error output")
    logger.critical("Some critical output")
