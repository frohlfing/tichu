"""
Dieses Modul stellt Funktionen zur Interaktion mit Git bereit.

Aktuell enthält es nur eine Funktion, um den neuesten Git-Tag aus dem aktuellen Repository zu ermitteln.
"""

__all__ = "get_git_tag",

import subprocess

def get_git_tag():
    """
    Ermittelt den neuesten Git-Tag aus dem aktuellen Repository von Github.

    Die Versionsnummer wird gemäß dem Semantic Versioning-Schema(https://semver.org/) vergeben.

    Das bedeutet, wir erhöhen bei gegebener Versionsnummer MAJOR.MINOR.PATCH die:
    - MAJOR-Version, wenn wir inkompatible API-Änderungen vornehmen
    - MINOR-Version, wenn wir Funktionen abwärtskompatibel hinzufügen
    - PATCH-Version, wenn wir abwärtskompatible Fehlerbehebungen vornehmen

    :return: Die aktuelle Versionsnummer
    """
    try:
        tag = subprocess.check_output(["git", "describe", "--tags"]).strip().decode("utf-8").split("-", 1)
        return tag[0]
    except subprocess.CalledProcessError:
        return "0.0.0"
