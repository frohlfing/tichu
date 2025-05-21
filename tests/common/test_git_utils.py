# tests/test_git_utils.py
"""
Tests für src.common.git_utils
"""
import subprocess
from unittest.mock import patch, MagicMock # Importiere patch und MagicMock
from src.common.git_utils import get_git_tag, get_release


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
    expected_tag_bytes = b"v1.2.3-4-foo\n" # Beispiel-Output von git describe
    mock_check_output.return_value = expected_tag_bytes

    # 2. Rufe die zu testende Funktion auf:
    actual_tag = get_git_tag()

    # 3. Überprüfe die Ergebnisse:
    #    a) Wurde der Mock korrekt aufgerufen?
    mock_check_output.assert_called_once_with(["git", "describe", "--tags"])
    #    b) Ist der zurückgegebene Tag der erwartete (gestrippt und dekodiert)?
    assert actual_tag == "v1.2.3-4-foo"

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
    assert actual_tag == ""

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
    
    
# === Testfälle für get_release ===

# Wir können die Funktion get_git_tag innerhalb des Moduls mocken,
# wenn get_release sie aufruft. Das macht die Tests für get_release
# unabhängig von der Implementierung (und den Mocks) von get_git_tag.
@patch('src.common.git_utils.get_git_tag') # Mock get_git_tag im selben Modul
def test_get_release_valid_semver_tag(mock_get_git_tag: MagicMock):
    """
    Testet get_release mit einem gültigen semver-ähnlichen Tag.
    """
    mock_get_git_tag.return_value = "v1.2.3"
    assert get_release() == "1.2.3"
    mock_get_git_tag.assert_called_once()

@patch('src.common.git_utils.get_git_tag')
def test_get_release_valid_semver_tag_with_suffix(mock_get_git_tag: MagicMock):
    """
    Testet get_release mit einem Tag, der ein Suffix hat (z.B. von 'git describe').
    Das Suffix sollte entfernt werden.
    """
    mock_get_git_tag.return_value = "v1.2.3-4-foo"
    assert get_release() == "1.2.3"
    mock_get_git_tag.assert_called_once()

@patch('src.common.git_utils.get_git_tag')
def test_get_release_tag_without_v_prefix(mock_get_git_tag: MagicMock):
    """
    Testet get_release mit einem Tag, der kein 'v' als Präfix hat.
    """
    mock_get_git_tag.return_value = "1.2.3"
    assert get_release() == "1.2.3"
    mock_get_git_tag.assert_called_once()

@patch('src.common.git_utils.get_git_tag')
def test_get_release_tag_without_v_prefix_and_suffix(mock_get_git_tag: MagicMock):
    """
    Testet get_release mit einem Tag ohne 'v'-Präfix aber mit Suffix.
    """
    mock_get_git_tag.return_value = "1.2.3-rc1"
    assert get_release() == "1.2.3"
    mock_get_git_tag.assert_called_once()

@patch('src.common.git_utils.get_git_tag')
def test_get_release_non_semver_tag_returns_default(mock_get_git_tag: MagicMock):
    """
    Testet get_release mit einem Tag, der nicht dem SemVer-Format entspricht.
    Sollte "0.0.0" zurückgeben.
    """
    mock_get_git_tag.return_value = "my-feature-branch"
    assert get_release() == "0.0.0"
    mock_get_git_tag.assert_called_once()

@patch('src.common.git_utils.get_git_tag')
def test_get_release_non_semver_tag_with_numbers_returns_default(mock_get_git_tag: MagicMock):
    """
    Testet get_release mit einem Tag, der Zahlen enthält, aber nicht SemVer ist.
    """
    mock_get_git_tag.return_value = "feature-1.2" # Nur zwei Teile
    assert get_release() == "0.0.0"
    mock_get_git_tag.assert_called_once()

@patch('src.common.git_utils.get_git_tag')
def test_get_release_non_semver_tag_with_non_digits_returns_default(mock_get_git_tag: MagicMock):
    """
    Testet get_release mit einem Tag, der SemVer-ähnlich aussieht, aber nicht-numerische Teile hat.
    """
    mock_get_git_tag.return_value = "v1.beta.3"
    assert get_release() == "0.0.0"
    mock_get_git_tag.assert_called_once()

@patch('src.common.git_utils.get_git_tag')
def test_get_release_empty_tag_from_get_git_tag_returns_default(mock_get_git_tag: MagicMock):
    """
    Testet get_release, wenn get_git_tag einen leeren String zurückgibt
    (z.B. weil kein Tag gefunden wurde und get_git_tag jetzt "" zurückgibt).
    Sollte "0.0.0" zurückgeben.
    """
    mock_get_git_tag.return_value = ""
    assert get_release() == "0.0.0"
    mock_get_git_tag.assert_called_once()

@patch('src.common.git_utils.get_git_tag')
def test_get_release_tag_is_just_v_returns_default(mock_get_git_tag: MagicMock):
    """
    Testet den Fall, dass der Tag nur "v" ist.
    """
    mock_get_git_tag.return_value = "v"
    assert get_release() == "0.0.0"
    mock_get_git_tag.assert_called_once()

@patch('src.common.git_utils.get_git_tag')
def test_get_release_complex_suffix_is_stripped(mock_get_git_tag: MagicMock):
    """
    Testet ein komplexeres Suffix, das korrekt entfernt werden sollte.
    """
    mock_get_git_tag.return_value = "v0.15.1-beta.2-15-foo01"
    assert get_release() == "0.15.1"
    mock_get_git_tag.assert_called_once()
    