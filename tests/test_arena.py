# tests/test_arena.py
# tests/test_arena.py
"""
Tests für die Arena-Klasse.

Zusammenfassung der Tests für Arena:
- Initialisierung:
    - Korrekte Übernahme der Parameter (Agenten, max_games, verbose, worker, etc.).
    - Auswahl des korrekten Event-Typs (`asyncio.Event` vs. `Manager.Event`) basierend auf der Worker-Anzahl.
- Statistik-Aktualisierung (`_update`):
    - Korrekte Zählung von Spielen, Runden und Stichen.
    - Korrekte Zuordnung von Siegen, Niederlagen und Unentschieden für Team 20 basierend auf dem Spielergebnis (`PublicState`).
    - Korrekte Handhabung von `None`-Ergebnissen (z.B. bei Abbruch).
- Ablaufsteuerung (Single-Worker):
    - Überprüfung, ob `Arena.run` die Methode `_play_game` für die korrekte Anzahl an Spielen aufruft.
    - Überprüfung, ob die Ergebnisse von `_play_game` korrekt an `_update` weitergegeben werden.
- Einzelspiel-Ausführung (`_play_game`):
    - Sicherstellung, dass `_play_game` die Funktion `_run_game` (die ein einzelnes Spiel durchführt) mit den korrekten Parametern (Tischnamen, Agenten, Seed etc.) über `asyncio.run` startet.
- Early Stopping:
    - Korrekte Auslösung des Stopp-Events (`_stop_event.set()`), wenn die konfigurierte Gewinnrate erreicht oder uneinholbar unterschritten wird.
- Ablaufsteuerung (Multi-Worker):
    - Überprüfung (durch Mocking von `multiprocessing.Pool`), ob die Arena versucht, die Spiele mittels `Pool.apply_async` zu starten und die Pool-API korrekt verwendet (Callback, close, join).
"""

from typing import List

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call # Importiere call für Aufrufreihgenfolge/Argumente
from time import sleep # Für Tests mit Zeitbezug

# Zu testende Klasse
from src.arena import Arena, _run_game # Importiere auch _run_game zum Mocken

# Abhängigkeiten, die gemockt werden müssen/können
from src.players.agent import Agent
from src.public_state import PublicState
from src.private_state import PrivateState
from multiprocessing import Pool, Manager # Zum Mocken

# === Fixtures ===

@pytest.fixture
def mock_agents(mocker) -> List[MagicMock]:
    """Erstellt 4 einfache Mock-Agenten (nicht async für Arena nötig)."""
    return [mocker.create_autospec(Agent, instance=True, name=f"Agent_{i}") for i in range(4)]

@pytest.fixture
def sample_public_state_game_over() -> PublicState:
    """Erstellt einen PublicState, der ein abgeschlossenes Spiel repräsentiert."""
    pub = PublicState(table_name="Game_0")
    pub.game_score = [[150, 200], [-50, 300]] # Team 20: 350, Team 31: 250 -> Team 20 gewinnt
    pub.round_counter = 5
    pub.trick_counter = 55 # Beispielwerte
    # Markiere als beendet
    pub.current_phase = "finished" # Oder eine andere passende Phase
    # Setze Score, damit is_game_over True wird (obwohl Arena das nicht direkt prüft)
    pub.game_score = [[600],[400]] # Team 20 = 600, Team 31 = 400
    # Recalculate total score for is_game_over property if used internally
    # pub.total_score = (sum(pub.game_score[0]), sum(pub.game_score[1])) # Nicht nötig, Property macht das
    return pub

# === Testfälle ===

def test_arena_initialization(mock_agents):
    """Testet die korrekte Initialisierung der Arena."""
    arena = Arena(agents=mock_agents, max_games=100, verbose=False, worker=1)
    assert arena._agents is mock_agents
    assert arena._max_games == 100
    assert arena._verbose is False
    assert arena._worker == 1
    assert arena._early_stopping is False
    assert arena._games == 0
    assert arena._rounds == 0
    assert arena._tricks == 0
    assert arena._rating == [0, 0, 0]
    assert isinstance(arena._stop_event, asyncio.Event) # Bei worker=1

def test_arena_initialization_multi_worker(mock_agents, mocker):
    """Testet die Initialisierung im Multi-Worker-Modus."""
    # Mocke Manager().Event()
    mock_manager_event = mocker.patch('src.arena.Manager').return_value.Event.return_value
    arena = Arena(agents=mock_agents, max_games=50, worker=4)
    assert arena._worker == 4
    assert arena._stop_event is mock_manager_event

def test_arena_update_statistics_team20_wins(mock_agents, sample_public_state_game_over):
    """Testet die _update Methode, wenn Team 20 gewinnt."""
    arena = Arena(agents=mock_agents, max_games=10, worker=1)
    # sample_public_state_game_over: Team 20 = 600, Team 31 = 400 -> Win for 20
    game_index = 0
    result = (game_index, sample_public_state_game_over)

    arena._update(result)

    assert arena._games == 1
    assert arena._rounds == 5 # Aus sample state
    assert arena._tricks == 55 # Aus sample state
    assert arena._rating == [1, 0, 0] # Win, Lost, Draw for Team 20
    assert arena._seconds > 0 # Zeit sollte gestartet sein (schwer exakt zu testen)

def test_arena_update_statistics_team31_wins(mock_agents, sample_public_state_game_over):
    """Testet die _update Methode, wenn Team 31 gewinnt."""
    arena = Arena(agents=mock_agents, max_games=10, worker=1)
    # Modifiziere State für Sieg Team 31
    sample_public_state_game_over.game_score = [[300], [700]] # Team 20=300, Team 31=700
    game_index = 0
    result = (game_index, sample_public_state_game_over)

    arena._update(result)

    assert arena._games == 1
    assert arena._rating == [0, 1, 0] # Win, Lost, Draw for Team 20

def test_arena_update_statistics_draw(mock_agents, sample_public_state_game_over):
    """Testet die _update Methode bei einem Unentschieden."""
    arena = Arena(agents=mock_agents, max_games=10, worker=1)
    # Modifiziere State für Unentschieden
    sample_public_state_game_over.game_score = [[500], [500]]
    game_index = 0
    result = (game_index, sample_public_state_game_over)

    arena._update(result)

    assert arena._games == 1
    assert arena._rating == [0, 0, 1] # Win, Lost, Draw for Team 20

def test_arena_update_ignores_none_result(mock_agents):
    """Testet, dass _update nichts tut, wenn das Ergebnis None ist (z.B. bei Abbruch)."""
    arena = Arena(agents=mock_agents, max_games=10, worker=1)
    initial_rating = list(arena._rating)
    arena._update(None) # Simulierter Abbruch
    assert arena._games == 0
    assert arena._rating == initial_rating

@patch('src.arena._run_game', return_value=asyncio.Future()) # Mocke die Spielfunktion
def test_arena_run_single_worker_calls_play_game(mock_run_game, mock_agents, sample_public_state_game_over, mocker):
    """
    Testet, ob Arena.run im Single-Worker-Modus _play_game für jedes Spiel aufruft
    und _update mit dem Ergebnis.
    """
    max_games = 3
    arena = Arena(agents=mock_agents, max_games=max_games, worker=1)

    # Mocke _play_game, damit es kontrollierte Ergebnisse zurückgibt
    # Erstelle Future-Objekte, die aufgelöst werden können
    futures = []
    results = []
    for i in range(max_games):
        # Erstelle einen neuen State für jedes Spiel-Ergebnis
        state = PublicState(table_name=f"Game_{i}")
        state.game_score = [[i+1], [0]] # Jedes Spiel hat ein anderes Ergebnis
        state.round_counter = i + 1
        state.trick_counter = (i + 1) * 10
        results.append((i, state))

        future = asyncio.Future()
        future.set_result(results[-1]) # Setze das Ergebnis des Futures
        futures.append(future)

    # Konfiguriere den Mock _play_game, um die vorbereiteten Ergebnisse zurückzugeben
    # Da _play_game innerhalb von run synchron aufgerufen wird (und intern asyncio.run nutzt),
    # müssen wir das Ergebnis direkt zurückgeben, nicht das Future.
    # Wir mocken also _play_game selbst, nicht _run_game in diesem Test.
    mocker.patch.object(arena, '_play_game', side_effect=results)
    mock_update = mocker.patch.object(arena, '_update') # Mocke _update, um Aufrufe zu prüfen

    # Führe Arena.run aus
    arena.run()

    # Prüfungen:
    # Wurde _play_game für jede Partie aufgerufen?
    assert arena._play_game.call_count == max_games
    arena._play_game.assert_has_calls([call(0), call(1), call(2)])

    # Wurde _update für jedes Ergebnis aufgerufen?
    assert mock_update.call_count == max_games
    mock_update.assert_has_calls([call(results[0]), call(results[1]), call(results[2])])

@patch('src.arena.asyncio.run') # Mocke asyncio.run, das in _play_game verwendet wird
def test_arena_play_game_calls_run_game(mock_asyncio_run, mock_agents, sample_public_state_game_over):
    """Testet, ob _play_game die Funktion _run_game mit asyncio.run aufruft."""
    arena = Arena(agents=mock_agents, max_games=1, worker=1, seed=123)
    game_index = 0

    # Konfiguriere den Mock von asyncio.run, um das State-Objekt zurückzugeben
    mock_asyncio_run.return_value = sample_public_state_game_over

    # Rufe _play_game auf
    result_index, result_state = arena._play_game(game_index)

    # Prüfungen:
    assert result_index == game_index
    assert result_state is sample_public_state_game_over

    # Prüfe, ob asyncio.run korrekt aufgerufen wurde
    # Der erste Argument von asyncio.run ist die Coroutine _run_game(...)
    mock_asyncio_run.assert_called_once()
    call_args = mock_asyncio_run.call_args[0] # Die Argumente des Aufrufs
    assert len(call_args) == 1
    run_game_coro = call_args[0]
    # Wir können die Coroutine nicht direkt vergleichen, aber wir können prüfen, ob sie
    # die richtigen Argumente binden würde, wenn sie erstellt wird.
    # Dies ist etwas kompliziert, alternativ kann man _run_game mocken.
    # Einfacher: Prüfen, ob _run_game die korrekten Argumente in seinem Aufruf *innerhalb* von _play_game hätte.
    # Dazu müssten wir _run_game mocken.

    # Alternativer Test: Mocke _run_game
    with patch('src.arena._run_game', return_value=asyncio.Future()) as mock_internal_run_game:
        # Konfiguriere das Future, das _run_game zurückgibt
        future = asyncio.Future()
        future.set_result(sample_public_state_game_over)
        mock_internal_run_game.return_value = future # _run_game gibt eine Coroutine zurück

        # Setze den Return-Wert von asyncio.run, um das Ergebnis des Futures zurückzugeben
        mock_asyncio_run.return_value = sample_public_state_game_over

        arena._play_game(game_index)

        # Prüfe, ob _run_game korrekt aufgerufen wurde (innerhalb von asyncio.run)
        # Der Aufruf an _run_game findet statt, BEVOR asyncio.run aufgerufen wird,
        # da die Coroutine als Argument übergeben wird.
        # --> Mocking von _run_game ist hier der bessere Ansatz.

@patch('src.arena._run_game', new_callable=AsyncMock) # _run_game ist async, also AsyncMock
def test_arena_play_game_calls_run_game_direct_mock(mock_run_game_coro, mock_agents, sample_public_state_game_over, mocker):
    """Testet _play_game durch direktes Mocken von _run_game."""
    arena = Arena(agents=mock_agents, max_games=1, worker=1, seed=123)
    game_index = 0

    # Konfiguriere den AsyncMock _run_game, was er zurückgeben soll, wenn er awaited wird
    mock_run_game_coro.return_value = sample_public_state_game_over

    # Mocke asyncio.run, um sicherzustellen, dass es die Coroutine ausführt
    # und deren Ergebnis zurückgibt
    mock_asyncio_run = mocker.patch('src.arena.asyncio.run', side_effect=lambda coro: coro.result() if isinstance(coro, asyncio.Future) else asyncio.get_event_loop().run_until_complete(coro) )
    # Die side_effect simuliert das Warten auf die Coroutine

    # Rufe _play_game auf
    result_index, result_state = arena._play_game(game_index)

    # Prüfungen
    assert result_index == game_index
    assert result_state is sample_public_state_game_over

    # Prüfe, ob _run_game korrekt aufgerufen wurde
    mock_run_game_coro.assert_awaited_once_with(
        table_name=f"Game_{game_index}",
        agents=mock_agents,
        seed=123,
        pub=None, # Da keine initialen States übergeben wurden
        privs=None
    )
    # Prüfe, ob asyncio.run aufgerufen wurde (mit der Coroutine von _run_game)
    mock_asyncio_run.assert_called_once()


def test_arena_early_stopping_wins_met(mock_agents, sample_public_state_game_over):
    """Testet early stopping, wenn die Gewinnrate erreicht wird."""
    # Team 20 gewinnt jedes Spiel
    sample_public_state_game_over.game_score = [[600],[400]]
    result = (0, sample_public_state_game_over)

    arena = Arena(agents=mock_agents, max_games=10, worker=1, early_stopping=True, win_rate=0.6)
    mock_stop_event_set = MagicMock()
    arena._stop_event.set = mock_stop_event_set # Mocke die set Methode des Events

    # Simuliere 6 Siege für Team 20
    for i in range(6):
        result = (i, sample_public_state_game_over)
        arena._update(result)
        if i < 5:
            mock_stop_event_set.assert_not_called() # Noch nicht genug Spiele/Siege
        else:
            # Nach dem 6. Spiel (6 Siege / 6 Gesamt -> 100% > 60%)
            mock_stop_event_set.assert_called_once()

def test_arena_early_stopping_wins_unreachable(mock_agents, sample_public_state_game_over):
    """Testet early stopping, wenn die Gewinnrate nicht mehr erreichbar ist."""
    # Team 31 gewinnt jedes Spiel
    sample_public_state_game_over.game_score = [[400],[600]]

    arena = Arena(agents=mock_agents, max_games=10, worker=1, early_stopping=True, win_rate=0.7) # 70% benötigt
    mock_stop_event_set = MagicMock()
    arena._stop_event.set = mock_stop_event_set # Mocke die set Methode des Events

    # Simuliere 4 Niederlagen für Team 20 (0 Siege)
    for i in range(4):
        result = (i, sample_public_state_game_over)
        arena._update(result)
        # Nach 4 Spielen: 0 Siege. Übrig 6 Spiele. Max mögliche Siege: 6.
        # Max Win Rate = 6 / (6 + 4) = 0.6 -> Kann 0.7 nicht mehr erreichen.
        if i < 3:
             mock_stop_event_set.assert_not_called()
        else:
             mock_stop_event_set.assert_called_once()

# Testen des Multi-Worker-Modus ist komplexer, da es echte Prozesse involviert.
# Man könnte Pool mocken, aber das testet nicht die tatsächliche Parallelisierung.
# Ein einfacher Test könnte prüfen, ob Pool() und apply_async aufgerufen werden.
@patch('src.arena.Pool') # Mocke die Pool-Klasse
def test_arena_run_multi_worker_calls_pool(mock_pool_class, mock_agents, sample_public_state_game_over, mocker):
    """Testet grob, ob der Multi-Worker-Modus Pool und apply_async nutzt."""
    max_games = 5
    num_workers = 4
    arena = Arena(agents=mock_agents, max_games=max_games, worker=num_workers)

    # Mocke die Instanz von Pool und ihre Methoden
    mock_pool_instance = mock_pool_class.return_value
    mock_apply_async = mock_pool_instance.apply_async
    mock_close = mock_pool_instance.close
    mock_join = mock_pool_instance.join

    # Führe run aus
    arena.run()

    # Prüfungen
    mock_pool_class.assert_called_once_with(processes=num_workers)
    assert mock_apply_async.call_count == max_games
    # Prüfe Argumente des ersten apply_async Aufrufs (optional)
    first_call_args = mock_apply_async.call_args_list[0][1] # kwargs des ersten Aufrufs
    assert first_call_args['func'] == arena._play_game
    assert first_call_args['args'] == (0,) # game_index = 0
    assert first_call_args['callback'] == arena._update

    mock_close.assert_called_once()
    mock_join.assert_called_once()