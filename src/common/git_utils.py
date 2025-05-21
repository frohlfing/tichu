"""
Dieses Modul stellt Funktionen zur Interaktion mit Git bereit.
"""

__all__ = "get_git_tag", "get_release",

import subprocess

def get_git_tag() -> str:
    """
    Ermittelt den neuesten Git-Tag aus dem Repository von GitHub.

    :return: Den neuesten Git-Tag.
    """
    try:
        tag = subprocess.check_output(["git", "describe", "--tags"]).strip().decode("utf-8")
        return tag
    except subprocess.CalledProcessError:
        return ""


def get_release() -> str:
    """
    Ermittelt die aktuelle Versionsnummer des Repositories von GitHub.

    Es wird vorausgesetzt, dass die Versionsnummer im Git-Tag als v<MAJOR>.<MINOR>.<PATCH> angegeben ist.

    :return: Die aktuelle Versionsnummer (MAJOR.MINOR.PATCH).
    """
    version = get_git_tag().lstrip("v").split("-", 1)[0]
    parts = version.split(".")
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        return version
    else:
        return "0.0.0"
