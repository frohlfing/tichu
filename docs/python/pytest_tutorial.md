ich stelle meine unittest um nach pytest. Kannst du mir helfen und die Test für pytest umzuschreiben?


Ich hab bisher nur einfache Python-Tests mit unittest geschrieben. 
Erstelle ein Tutorial, das mir in kleinen Schritten das Schreiben von Tests mit pytest beibringt. 
Fange ganz einfach an, und versuche logisch aufbauend die hier verwendeten Konzepte zu erläutern. 
Nach der Einführung (Installation, erste Tests...) wären z.B. zu nennen:  
Exceptions testen, @pytest.mark.parametrize, @pytest.fixture, Mocks von Funktionen und Klassen, mocker.create_autospec, @patch, 
und zu guter Letzt @pytest.mark.asyncio

Schreibe das komplette Tutorial in eine Markdown-Datei und biete mir diese Datei zum Download an.


# Pytest Tutorial für Einsteiger

Dieses Tutorial bringt dir Schritt für Schritt das Testen mit `pytest` bei. Du solltest bereits einfache Tests mit `unittest` geschrieben haben. Wir starten mit den Grundlagen und steigern uns bis zu fortgeschrittenen Themen wie Fixtures, Mocks und asynchronem Testen.

---

## Inhalt

1. [Installation und erster Test](#1-installation-und-erster-test)
2. [Testfunktionen und Assertions](#2-testfunktionen-und-assertions)
3. [Fixtures mit `@pytest.fixture`](#3-fixtures-mit-pytestfixture)
4. [Mocks mit `unittest.mock`](#4-mocks-mit-unittestmock)
5. [Mocks mit `mocker.create_autospec`](#5-mocks-mit-mockercreate_autospec)
6. [Parameterisierte Tests mit `@pytest.mark.parametrize`](#6-parameterisierte-tests-mit-pytestmarkparametrize)
7. [Asynchrone Tests mit `@pytest.mark.asyncio`](#7-asynchrone-tests-mit-pytestmarkasyncio)

---

## 1. Installation und erster Test

```bash
pip install pytest
```

Erstelle eine Datei `test_example.py`:

```python
def add(a, b):
    return a + b

def test_add():
    assert add(2, 3) == 5
```

Ausführen mit:

```bash
pytest
```

---

## 2. Testfunktionen und Assertions

- Testfunktionen müssen mit `test_` beginnen.
- `assert` wird verwendet, um Ergebnisse zu überprüfen.

Beispiel:

```python
def subtract(a, b):
    return a - b

def test_subtract():
    result = subtract(5, 3)
    assert result == 2
```

---

## 3. Fixtures mit `@pytest.fixture`

Fixtures liefern vorbereitete Daten oder Objekte für Tests:

```python
import pytest

@pytest.fixture
def sample_list():
    return [1, 2, 3]

def test_list_length(sample_list):
    assert len(sample_list) == 3
```

Fixtures können komplexe Setups wie Datenbankverbindungen oder Konfigurationen kapseln.

---

## 4. Mocks mit `unittest.mock`

```python
from unittest.mock import Mock

def fetch_data(api):
    return api.get_data()

def test_fetch_data():
    mock_api = Mock()
    mock_api.get_data.return_value = {'name': 'Test'}

    result = fetch_data(mock_api)
    assert result['name'] == 'Test'
```

---

## 5. Mocks mit `mocker.create_autospec`

Mit dem `mocker`-Fixture von `pytest-mock`:

```bash
pip install pytest-mock
```

```python
def process(api):
    return api.compute(3)

def test_process(mocker):
    mock_api = mocker.create_autospec(spec=['compute'])
    mock_api.compute.return_value = 42

    result = process(mock_api)
    assert result == 42
```

---

## 6. Parametrisierte Tests mit `@pytest.mark.parametrize`

Damit kannst du denselben Test mit verschiedenen Daten ausführen:

```python
import pytest

@pytest.mark.parametrize("a,b,expected", [
    (1, 1, 2),
    (2, 3, 5),
    (-1, 1, 0),
])
def test_add(a, b, expected):
    assert a + b == expected
```

---

## 7. Asynchrone Tests mit `@pytest.mark.asyncio`

```bash
pip install pytest-asyncio
```

```python
import pytest
import asyncio

async def async_add(a, b):
    await asyncio.sleep(0.1)
    return a + b

@pytest.mark.asyncio
async def test_async_add():
    result = await async_add(2, 3)
    assert result == 5
```

---

## Fazit

Mit `pytest` kannst du Tests viel eleganter und flexibler schreiben als mit `unittest`. Du hast nun gelernt:

- wie man einfache Tests schreibt
- wie man Fixtures nutzt
- wie man mit Mocks arbeitet
- wie man parameterisiert testet
- wie man asynchrone Funktionen testet

Viel Spaß beim Testen! ✅
