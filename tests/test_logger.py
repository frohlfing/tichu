# tests/test_logger.py
"""
Tests für src.common.logger.

Zusammenfassung der Tests für Logger:
- `AnsiColorizer`:
    - Korrektes Schreiben der Farbcodes in einen Stream.
    - Korrekte Handhabung von unbekannten Farben (Fallback auf Default).
    - Funktion des `supported()`-Checks (gemockt für TTY/no-TTY).
- `ColorStreamHandler`:
    - Korrekte Auswahl der Farbe basierend auf dem Log-Level des Records.
    - Korrektes Emittieren der formatierten Nachricht mit Farbcodes in den Stream.
- Globale Logger-Konfiguration (Smoke Tests):
    - Überprüfung der Existenz des globalen `logger`-Objekts nach dem Import.
    - Überprüfung, ob das Log-Level des Loggers dem aus `config` entspricht.
    - Überprüfung, ob die erwarteten Handler (File, Console) am Logger registriert sind.
- Handler-Konfiguration (Stichproben):
    - Überprüfung grundlegender Einstellungen der registrierten Handler (Level, Stream/Dateiname, Formatter, backupCount).
- Basis-Logging:
    - Sicherstellung, dass Aufrufe wie `logger.info()` die interne `handle`-Methode des Loggers mit dem korrekten LogRecord auslösen (Level-Filterung wird hierbei auch implizit geprüft).
"""

import pytest
import logging
import sys
import os
from io import StringIO # Zum Abfangen von Stream-Ausgaben
from unittest.mock import MagicMock, patch

# Klassen und das konfigurierte Logger-Objekt importieren
# ACHTUNG: Der Import von logger führt den Konfigurationscode aus!
from src.common.logger import logger, AnsiColorizer, ColorStreamHandler

# Importiere config, um es evtl. zu mocken
import src.common.config as config

# === Tests für AnsiColorizer ===

@pytest.fixture
def mock_stream():
    """Ein StringIO-Objekt, das sich wie ein Stream verhält, um Ausgaben abzufangen."""
    return StringIO()

@patch('src.common.logger.AnsiColorizer.supported', return_value=True) # Annahme: Farben werden unterstützt
def test_ansi_colorizer_write(mock_supported, mock_stream):
    """Testet, ob der Colorizer die korrekten ANSI-Codes schreibt."""
    colorizer = AnsiColorizer(mock_stream)
    colorizer.write("Hello", "red")
    # \x1b[<color_code>m<text>\x1b[0m -> Rot ist 31
    expected_output = "\x1b[31mHello\x1b[0m"
    assert mock_stream.getvalue() == expected_output

    # Teste mit unbekannter Farbe (sollte weiß/default 37 sein)
    mock_stream.seek(0)
    mock_stream.truncate()
    colorizer.write("World", "unknown_color")
    expected_output_default = "\x1b[37mWorld\x1b[0m"
    assert mock_stream.getvalue() == expected_output_default

@patch('sys.stdout.isatty', return_value=False) # Simulieren: Kein TTY
def test_ansi_colorizer_supported_no_tty(mock_isatty):
    """Testet, ob supported() False zurückgibt, wenn kein TTY vorhanden ist."""
    assert AnsiColorizer.supported(sys.stdout) is False

# Weitere Tests für supported() mit/ohne curses sind komplexer und plattformabhängig.

# === Tests für ColorStreamHandler ===

@pytest.fixture
def color_stream_handler(mock_stream):
    """Erstellt einen Handler mit einem Mock-Stream."""
    # Stelle sicher, dass der Colorizer glaubt, Farben werden unterstützt
    with patch('src.common.logger.AnsiColorizer.supported', return_value=True):
        handler = ColorStreamHandler(stream=mock_stream)
        # Setze einen einfachen Formatter für den Test
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        return handler

def test_color_stream_handler_emit(color_stream_handler, mock_stream):
    """Testet, ob der Handler die korrekte Farbe für ein Level verwendet."""
    # Erstelle LogRecords für verschiedene Level
    info_record = logging.LogRecord(
        name='test', level=logging.INFO, pathname='', lineno=0,
        msg='Info message', args=[], exc_info=None, func=''
    )
    warning_record = logging.LogRecord(
        name='test', level=logging.WARNING, pathname='', lineno=0,
        msg='Warning message', args=[], exc_info=None, func=''
    )

    # Sende Info-Record
    color_stream_handler.emit(info_record)
    # Info -> grün (32)
    expected_output_info = "\x1b[32mInfo message\x1b[0m\n"
    assert mock_stream.getvalue() == expected_output_info

    # Sende Warning-Record
    mock_stream.seek(0)
    mock_stream.truncate()
    color_stream_handler.emit(warning_record)
    # Warning -> gelb (33)
    expected_output_warning = "\x1b[33mWarning message\x1b[0m\n"
    assert mock_stream.getvalue() == expected_output_warning

# === Tests für die globale Logger-Konfiguration (Beispielhaft) ===
# Diese Tests sind empfindlicher wegen des globalen Setups beim Import.

# ACHTUNG: Diese Tests prüfen den Zustand NACHDEM logger.py importiert wurde.
# Sie können durch andere Tests beeinflusst werden, wenn diese logger importieren.

def test_logger_instance_created():
    """Prüft, ob das globale Logger-Objekt existiert."""
    assert isinstance(logger, logging.Logger)

def test_logger_level_set_from_config():
    """Prüft, ob das Logger-Level dem Wert aus config entspricht."""
    # Wir können nicht garantieren, was in config steht, aber wir können prüfen,
    # ob der gesetzte Level dem entspricht, was beim Import gelesen wurde.
    assert logger.level == logging.getLevelName(config.LOG_LEVEL)

def test_logger_has_handlers():
    """Prüft, ob der Logger die erwarteten Handler hat."""
    assert len(logger.handlers) >= 2 # Mindestens File und Console

    handler_types = [type(h) for h in logger.handlers]
    assert logging.handlers.TimedRotatingFileHandler in handler_types
    assert ColorStreamHandler in handler_types

def test_logger_file_handler_configured(mocker):
    """Prüft einige Konfigurationen des File Handlers (weniger robust)."""
    file_handler = next((h for h in logger.handlers if isinstance(h, logging.handlers.TimedRotatingFileHandler)), None)
    assert file_handler is not None
    assert file_handler.level == logging.getLevelName(config.LOG_LEVEL)
    # Dateiname prüfen (kann fehlschlagen, wenn Pfad sich ändert)
    expected_path_part = os.path.join("logs", "app.log")
    assert expected_path_part in file_handler.baseFilename
    assert file_handler.backupCount == config.LOG_COUNT
    assert isinstance(file_handler.formatter, logging.Formatter)

def test_logger_console_handler_configured():
    """Prüft einige Konfigurationen des Console Handlers."""
    console_handler = next((h for h in logger.handlers if isinstance(h, ColorStreamHandler)), None)
    assert console_handler is not None
    assert console_handler.level == logging.getLevelName(config.LOG_LEVEL)
    assert console_handler.stream is sys.stdout # Prüft den Stream
    assert isinstance(console_handler.formatter, logging.Formatter)

# Man könnte auch testen, ob eine Log-Nachricht tatsächlich geschrieben wird,
# aber das erfordert mehr Mocking oder das Abfangen der Ausgabe.
@patch.object(logger, 'handle') # Mocke die zentrale handle-Methode des Loggers
def test_logger_logs_message_at_correct_level(mock_handle):
    """Testet, ob logger.info() etc. die handle-Methode aufruft."""
    # Setze Logger-Level temporär für diesen Test, falls nötig
    original_level = logger.level
    logger.setLevel(logging.INFO)

    logger.info("Test info message")
    logger.debug("Test debug message - should be ignored") # Liegt unter INFO

    # Prüfe, ob handle für INFO aufgerufen wurde
    assert mock_handle.call_count == 1
    call_args = mock_handle.call_args[0] # Das LogRecord-Argument
    record: logging.LogRecord = call_args[0]
    assert record.levelno == logging.INFO
    assert record.getMessage() == "Test info message"

    # Setze Level zurück
    logger.setLevel(original_level)