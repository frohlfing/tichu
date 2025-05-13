import re

def get_version_from_readme():
    """
    Liest die Versionsnummer aus der README.md-Datei.

    Die Versionsnummer wird gemäß dem Semantic Versioning-Schema(https://semver.org/) vergeben.

    Das bedeutet, wir erhöhen bei gegebener Versionsnummer MAJOR.MINOR.PATCH die:
    - MAJOR-Version, wenn wir inkompatible API-Änderungen vornehmen
    - MINOR-Version, wenn wir Funktionen abwärtskompatibel hinzufügen
    - PATCH-Version, wenn wir abwärtskompatible Fehlerbehebungen vornehmen

    :return: Die aktuelle Versionsnummer
    """
    with open("README.md", "r", encoding="utf-8") as file:
        content = file.read()
    match = re.search(r"Version\-(\d+\.\d+\.\d+)", content)
    return match.group(1) if match else "Version nicht gefunden"


print(f"Aktuelle Version: {get_version_from_readme()}")
