# Dieses PowerShell-Skript führt eine Code-Coverage-Analyse durch und zeigt anschließend das Ergebnis an.

# Coverage-Datei erzeugen (Default: .coverage; kann in .coveragerc bzw. pyproject.toml geändert werden)
coverage run -m pytest

# HTML-Report generieren (Ausgabeverzeichnis: ./htmlcov; kann in .coveragerc bzw. pyproject.toml geändert werden)
coverage html

# XML-Report für PyCharm generieren (Default: coverage.xml; kann in .coveragerc bzw. pyproject.toml geändert werden)
coverage xml

# Icon für die README generieren
coverage-badge -f -o docs/assets/coverage.svg

Write-Output ""
Write-Output ("Coverage Report " + (Get-Date -Format "dd.MM.yyyy HH:mm:ss"))
Write-Output "==================================="
Write-Output ""

# Report im Terminal anzeigen
coverage report
