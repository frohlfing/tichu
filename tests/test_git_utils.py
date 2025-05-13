# tests/test_git_utils.py
"""
Tests für src.common.git_utils
"""

import pytest
from unittest.mock import patch, MagicMock # Importiere patch und MagicMock

# Importiere die zu testende Funktion
# Annahme: Deine Datei heißt z.B. src/common/git_utils.py
from src.common.git_utils import get_git_tag

# === Testfälle für get_git_tag ===

# Der Decorator @patch ersetzt 'subprocess.check_output' im Modul 'src.common.git_utils'
# während der Ausführung dieses Tests durch einen Mock.
@patch('src.common.git_utils.subprocess.check_output')
def test_get_git_tag_success(mock_check_output: MagicMock):
    """
    Testet den Erfolgsfall, wenn 'git describe --tags' einen Tag zurückgibt.

    :param mock_check_output: Der von @patch injizierte Mock für subprocess.check_output.
                              MagicMock ist flexibel und kann konfiguriert werden.
    """
    # 1. Konfiguriere den Mock:
    #    Was soll er zurückgeben, wenn er aufgerufen wird?
    #    'git describe' gibt Bytes zurück, die dann dekodiert und gestrippt werden.
    expected_tag_bytes = b"v1.2.3-4-gabcdef\n" # Beispiel-Output von git describe
    mock_check_output.return_value = expected_tag_bytes

    # 2. Rufe die zu testende Funktion auf:
    actual_tag = get_git_tag()

    # 3. Überprüfe die Ergebnisse:
    #    a) Wurde der Mock korrekt aufgerufen?
    mock_check_output.assert_called_once_with(["git", "describe", "--tags"])
    #    b) Ist der zurückgegebene Tag der erwartete (gestrippt und dekodiert)?
    assert actual_tag == "v1.2.3-4-gabcdef"

@patch('src.common.git_utils.subprocess.check_output')
def test_get_git_tag_no_tags_found(mock_check_output: MagicMock):
    """
    Testet den Fall, wenn 'git describe --tags' fehlschlägt (z.B. keine Tags vorhanden).
    In diesem Fall soll "No tag found" zurückgegeben werden.
    """
    # 1. Konfiguriere den Mock, um eine subprocess.CalledProcessError auszulösen,
    #    wenn er aufgerufen wird.
    #    'side_effect' kann eine Exception sein, die ausgelöst werden soll.
    mock_check_output.side_effect = subprocess.CalledProcessError(
        returncode=128, # Typischer Return-Code für git-Fehler
        cmd=["git", "describe", "--tags"],
        output=b"fatal: No names found, cannot describe anything." # Beispiel-Fehlermeldung
    )

    # 2. Rufe die zu testende Funktion auf:
    actual_tag = get_git_tag()

    # 3. Überprüfe die Ergebnisse:
    #    a) Wurde der Mock korrekt aufgerufen?
    mock_check_output.assert_called_once_with(["git", "describe", "--tags"])
    #    b) Ist der zurückgegebene Wert der erwartete Fallback-String?
    assert actual_tag == "No tag found"

@patch('src.common.git_utils.subprocess.check_output')
def test_get_git_tag_different_tag_format(mock_check_output: MagicMock):
    """
    Testet mit einem anderen gültigen Tag-Format von 'git describe'.
    """
    expected_tag_bytes = b"my-feature-tag\n"
    mock_check_output.return_value = expected_tag_bytes

    actual_tag = get_git_tag()

    mock_check_output.assert_called_once_with(["git", "describe", "--tags"])
    assert actual_tag == "my-feature-tag"

@patch('src.common.git_utils.subprocess.check_output')
def test_get_git_tag_empty_output_from_git(mock_check_output: MagicMock):
    """
    Testet den (unwahrscheinlichen) Fall, dass git einen leeren Output liefert,
    aber keinen Fehler wirft.
    """
    expected_tag_bytes = b"\n" # Nur ein Newline
    mock_check_output.return_value = expected_tag_bytes

    actual_tag = get_git_tag()

    mock_check_output.assert_called_once_with(["git", "describe", "--tags"])
    assert actual_tag == "" # strip() and decode() sollten einen leeren String ergeben