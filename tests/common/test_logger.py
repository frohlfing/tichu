import pytest
import logging
import sys
import os
from io import StringIO  # Zum Abfangen von Stream-Ausgaben
from unittest.mock import patch

# Klassen und das konfigurierte Logger-Objekt importieren
# ACHTUNG: Der Import von logger führt den Konfigurationscode aus!
# noinspection PyProtectedMember
from src.common.logger import logger, AnsiColorizer, ColorStreamHandler

# Importiere config, um es evtl. zu mocken
import config

@pytest.fixture
def mock_stream():
    """Ein StringIO-Objekt, das sich wie ein Stream verhält, um Ausgaben abzufangen."""
    return StringIO()

@patch('src.common.logger.AnsiColorizer.supported', return_value=True) # Annahme: Farben werden unterstützt
def test_ansi_colorizer_write(_mock_supported, mock_stream):
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
def test_ansi_colorizer_supported_no_tty(_mock_isatty):
    """Testet, ob supported() False zurückgibt, wenn kein TTY vorhanden ist."""
    assert AnsiColorizer.supported(sys.stdout) is False

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
        msg='Info message', args=(), exc_info=None, func=''
    )
    warning_record = logging.LogRecord(
        name='test', level=logging.WARNING, pathname='', lineno=0,
        msg='Warning message', args=(), exc_info=None, func=''
    )

    # Sende Info-Record
    color_stream_handler.emit(info_record)
    # Info -> grün (32)
    expected_output_info = "\x1b[32mInfo message\n\x1b[0m"
    assert mock_stream.getvalue() == expected_output_info

    # Sende Warning-Record
    mock_stream.seek(0)
    mock_stream.truncate()
    color_stream_handler.emit(warning_record)
    # Warning -> gelb (33)
    expected_output_warning = "\x1b[33mWarning message\n\x1b[0m"
    assert mock_stream.getvalue() == expected_output_warning

# === Tests für die globale Logger-Konfiguration (Beispielhaft) ===
# Diese Tests sind empfindlicher wegen des globalen Setups beim Import.

# ACHTUNG: Diese Tests prüfen den Zustand, NACHDEM logger.py importiert wurde.
# Sie können durch andere Tests beeinflusst werden, wenn diese logger importieren.

def test_logger_instance_created():
    """Prüft, ob das globale Logger-Objekt existiert."""
    assert isinstance(logger, logging.Logger)

def test_logger_level_set_from_config():
    """Prüft, ob das Logger-Level dem Wert aus config entspricht."""
    # Wir können nicht garantieren, was in config steht, aber wir können prüfen,
    # ob der gesetzte Level dem entspricht, was beim Import gelesen wurde.
    assert logger.level == config.LOG_LEVEL

def test_logger_has_handlers():
    """Prüft, ob der Logger die erwarteten Handler hat."""
    assert len(logger.handlers) >= 2 # Mindestens File und Console

    handler_types = [type(h) for h in logger.handlers]
    # noinspection PyUnresolvedReferences
    assert logging.handlers.TimedRotatingFileHandler in handler_types
    assert ColorStreamHandler in handler_types

def test_logger_file_handler_configured():
    """Prüft einige Konfigurationen des File Handlers (weniger robust)."""
    # noinspection PyUnresolvedReferences
    file_handler = next((h for h in logger.handlers if isinstance(h, logging.handlers.TimedRotatingFileHandler)), None)
    assert file_handler is not None
    assert file_handler.level == config.LOG_LEVEL
    # Dateiname prüfen (kann fehlschlagen, wenn Pfad sich ändert)
    expected_path_part = os.path.join("logs", "app.log")
    assert expected_path_part in file_handler.baseFilename
    assert file_handler.backupCount == config.LOG_COUNT
    assert isinstance(file_handler.formatter, logging.Formatter)

def test_logger_console_handler_configured():
    """Prüft einige Konfigurationen des Console Handlers."""
    console_handler = next((h for h in logger.handlers if isinstance(h, ColorStreamHandler)), None)
    assert console_handler is not None
    assert console_handler.level == config.LOG_LEVEL
    assert console_handler.stream is sys.stdout # Prüft den Stream
    assert isinstance(console_handler.formatter, logging.Formatter)

# Man könnte auch testen, ob eine Log-Nachricht tatsächlich geschrieben wird,
# aber das erfordert mehr Mocking oder das Abfangen der Ausgabe.
# noinspection GrazieInspection
@patch.object(logger, 'handle') # Mock die zentrale handle-Methode des Loggers
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