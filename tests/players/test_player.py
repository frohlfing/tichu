import pytest
from uuid import UUID

# Zu testende Klasse
from src.players.player import Player


def test_player_init_valid_name():
    """Testet die Initialisierung mit gültigem Namen."""
    player = Player(name=" Alice ") # Mit Leerzeichen
    assert player.name == "Alice" # Name sollte gestrippt sein
    assert player.pub is None # Initial kein Zustand
    assert player.priv is None # Initial kein Zustand
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
    custom_session_id = "my-test-session-123"
    player = Player(name="Bob", session_id=custom_session_id)
    assert player.session_id == custom_session_id

def test_player_properties():
    """Testet die Standard-Properties eines Players."""
    player = Player(name="Charlie")
    player.index = 2 # Index manuell setzen für Test
    assert player.name == "Charlie"
    assert player.class_name == "Player" # Gibt den Klassennamen zurück

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

    # Prüfe jede abstrakte Methode
    with pytest.raises(NotImplementedError):
        await player.schupf()
    with pytest.raises(NotImplementedError):
        await player.announce()
    with pytest.raises(NotImplementedError):
        await player.play() # play statt combination
    with pytest.raises(NotImplementedError):
        await player.wish()
    with pytest.raises(NotImplementedError):
        await player.give_dragon_away() # Umbenannt