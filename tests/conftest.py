"""
Diese Datei wird automatisch von pytest geladen und dient dazu, gemeinsame Fixtures,
Hooks und Einstellungen für Tests bereitzustellen.
Mehr Infos zu conftest.py: https://docs.pytest.org/en/latest/explanation/fixtures.html
"""

import sys
import os

# das src-Verzeichnis zur Umgebungsvariable PYTHONPATH hinzufügen
#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
