# tests/test_player.py

"""
Tests für die abstrakte Basisklasse Player.

Zusammenfassung der Tests für Player:
- Initialisierung:
    - Korrekte Verarbeitung und Bereinigung des Spielernamens.
    - Korrekte Generierung einer Session-UUID, wenn keine angegeben ist.
    - Korrekte Übernahme einer explizit angegebenen Session.
    - Sicherstellung, dass `player_index` initial `None` ist.
- Properties:
    - Korrekte Rückgabe des Namens (`name`).
    - Korrekte Rückgabe des Klassennamens (`class_name`).
    - Korrekte Berechnung der Indizes für Partner und Gegner (`partner_index`, `opponent_right_index`, `opponent_left_index`).
- Abstrakte Natur:
    - Verifizierung durch eine Dummy-Subklasse, dass der Aufruf der nicht implementierten, abstrakten Entscheidungsmethoden (`schupf`, `announce`, `play`, `wish`, `give_dragon_away`) einen `NotImplementedError` auslöst.
"""

import pytest
from uuid import UUID

# Zu testende Klasse
from src.players.player import Player

# Benötigte Klassen/Daten für den Test der abstrakten Methoden
from src.public_state import PublicState
from src.private_state import PrivateState
from src.lib.combinations import FIGURE_PASS # CombinationType.PASS wäre besser

# === Testfälle für Player (Basisklasse) ===

def test_player_init_valid_name():
    """Testet die Initialisierung mit gültigem Namen."""
    player = Player(name=" Alice ") # Mit Leerzeichen
    assert player.name == "Alice" # Name sollte gestrippt sein
    assert player.player_index is None # Initial kein Index
    # Session sollte eine gültige UUID sein
    assert isinstance(UUID(player.session_id, version=4), UUID)

def test_player_init_empty_name_raises_error():
    """Testet, ob ein leerer Name einen ValueError auslöst."""
    with pytest.raises(ValueError, match="Spielername darf nicht leer sein."):
        Player(name="")
    with pytest.raises(ValueError, match="Spielername darf nicht leer sein."):
        Player(name="   ")

def test_player_init_with_session():
    """Testet die Initialisierung mit einer vorgegebenen Session."""
    custom_session = "my-test-session-123"
    player = Player(name="Bob", session_id=custom_session)
    assert player.session_id == custom_session

def test_player_properties():
    """Testet die Standard-Properties eines Players."""
    player = Player(name="Charlie")
    player.player_index = 2 # Index manuell setzen für Test

    assert player.name == "Charlie"
    assert player.class_name == "Player" # Gibt den Klassennamen zurück
    assert player.partner_index == 0 # (2 + 2) % 4
    assert player.opponent_right_index == 3 # (2 + 1) % 4
    assert player.opponent_left_index == 1 # (2 + 3) % 4

# Testen der abstrakten Methoden ist schwierig, da man Player nicht instanziieren sollte,
# aber wir können prüfen, ob eine Subklasse, die sie NICHT implementiert, Fehler wirft.
# Erstellen wir eine minimale Dummy-Subklasse nur für diesen Test:
class IncompletePlayer(Player):
    """Eine Dummy-Klasse, die Player erbt, aber keine abstrakten Methoden implementiert."""
    # Implementiert keine der abstrakten Methoden wie schupf, play etc.
    pass

@pytest.mark.asyncio
async def test_player_abstract_methods_raise_not_implemented():
    """
    Testet, ob der Aufruf der abstrakten Methoden in einer unvollständigen
    Subklasse NotImplementedError auslöst.
    """
    # Erzeuge eine Instanz der unvollständigen Klasse.
    # Hinweis: Dies dient nur zur Veranschaulichung der abstrakten Natur.
    player = IncompletePlayer(name="Dummy")
    pub_state = PublicState() # Leere States für den Aufruf
    priv_state = PrivateState()
    # Beispiel Action Space (nur für den play-Aufruf benötigt)
    action_space = [([], FIGURE_PASS)]

    # Prüfe jede abstrakte Methode
    with pytest.raises(NotImplementedError):
        await player.schupf(pub_state, priv_state)
    with pytest.raises(NotImplementedError):
        await player.announce(pub_state, priv_state)
    with pytest.raises(NotImplementedError):
        await player.play(pub_state, priv_state, action_space) # play statt combination
    with pytest.raises(NotImplementedError):
        await player.wish(pub_state, priv_state)
    with pytest.raises(NotImplementedError):
        await player.give_dragon_away(pub_state, priv_state) # Umbenannt