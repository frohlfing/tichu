import pytest
from typing import Optional, List
from src.players.agent import Agent
import asyncio
from unittest.mock import patch, MagicMock, call
# noinspection PyUnresolvedReferences,PyProtectedMember
from multiprocessing.managers import EventProxy
# noinspection PyProtectedMember
from src.arena import Arena, _create_engine_and_run


# --- Dummies/Mocks für Abhängigkeiten (wie oben definiert) ---
class MockAgent:
    def __init__(self, name="TestAgent"):
        self.name = name
        self.__class__ = Agent

    # async def get_action(self, public_state: Any, private_state: Any) -> Any:
    #     return "some_action"

class MockPublicState:
    def __init__(self, game_score=([0], [0]), trick_counter=0, round_counter=0, game_over=False):
        self.game_score = game_score
        self.trick_counter = trick_counter
        self.round_counter = round_counter
        self.game_over = game_over
        self.current_player_index = 0
        self.current_round_score = ([0], [0])
        self.deck = []
        self.played_cards_in_trick = []
        self.next_player_index = 0

class MockPrivateState:
    def __init__(self):
        self.hand = []

class MockGameEngine:
    def __init__(self, table_name: str, default_agents: list, seed: Optional[int]):
        self.table_name = table_name
        self.agents = default_agents
        self.seed = seed
        # Wird im run_game_loop gesetzt oder durch Parameter pub überschrieben
        self.pub_state_to_return = MockPublicState(game_score=([100], [50]), round_counter=5, trick_counter=20, game_over=True)

    async def run_game_loop(self) -> MockPublicState:
        return self.pub_state_to_return

@pytest.fixture
def mock_agents(mocker) -> List[MagicMock]:
    """Erstellt 4 einfache Mock-Agenten (nicht async für Arena nötig)."""
    return [mocker.create_autospec(Agent, instance=True, name=f"Agent_{i}", player_index=i) for i in range(4)]

@pytest.fixture
def mock_public_state_win_team0():
    return MockPublicState(game_score=([100], [50]), round_counter=5, trick_counter=20)

@pytest.fixture
def mock_public_state_win_team1():
    return MockPublicState(game_score=([50], [100]), round_counter=6, trick_counter=22)

@pytest.fixture
def mock_public_state_draw():
    return MockPublicState(game_score=([75], [75]), round_counter=4, trick_counter=18)

@pytest.fixture
def mock_private_states():
    return [MockPrivateState() for _ in range(4)]

# --- Tests für _run_game ---
@pytest.mark.asyncio
@patch('src.arena.GameEngine', new=MockGameEngine)  # Mock GameEngine für _run_game
async def test_create_engine_and_run_success(mock_agents, mock_public_state_win_team0):
    pub_state = await _create_engine_and_run("TestTable", mock_agents, seed=123)
    assert pub_state is not None
    assert pub_state.game_score == ([100], [50])

@pytest.mark.asyncio
@patch('src.arena.GameEngine')  # Standard MagicMock
async def test_run_game_exception_in_engine(mock_game_engine_cls, mock_agents):
    mock_engine_instance = MagicMock()
    mock_engine_instance.run_game_loop.side_effect = Exception("Engine Boom!")
    mock_game_engine_cls.return_value = mock_engine_instance

    with patch('src.arena.logger.exception') as mock_logger_exception:
        pub_state = await _create_engine_and_run("TestTableError", mock_agents, seed=123)
        assert pub_state is None
        mock_logger_exception.assert_called_once()
        assert "Engine Boom!" in mock_logger_exception.call_args[0][0]

# --- Tests für Arena ---
def test_arena_initialization(mock_agents):
    arena = Arena(mock_agents, max_games=10, worker=1)
    assert len(arena._agents) == 4
    assert arena._max_games == 10
    assert arena._worker == 1
    assert isinstance(arena._stop_event, asyncio.Event) # Für worker = 1

def test_arena_initialization_multi_worker_event(mock_agents):
    # Um Manager().Event() zu testen, ohne einen echten Manager zu starten,
    # können wir den Typ des Events prüfen.
    arena = Arena(mock_agents, max_games=10, worker=2)
    assert arena._worker == 2
    # Überprüfen, ob es sich um einen Event-Typ handelt, der von multiprocessing.Manager stammt.
    # Genauer gesagt, ist es ein EventProxy.
    assert isinstance(arena._stop_event, EventProxy)

def test_arena_initialization_invalid_agents():
    with pytest.raises(AssertionError):
        # noinspection PyTypeChecker
        Arena([MockAgent()] * 3, max_games=10)  # Nur 3 Agenten

@patch('src.arena._run_game')  # Mocke die interne _run_game Funktion
def test_arena_play_game_single_run(mock_run_game_async, mock_agents, mock_public_state_win_team0):
    # Mock _run_game, um ein PublicState zurückzugeben
    async def async_mock_run_game(*_args, **_kwargs):
        return mock_public_state_win_team0

    mock_run_game_async.side_effect = async_mock_run_game

    arena = Arena(mock_agents, max_games=1, worker=1)
    game_index, pub_result = arena._play_game(0)

    assert game_index == 0
    assert pub_result == mock_public_state_win_team0
    mock_run_game_async.assert_called_once_with(
        table_name="Game_0",
        agents=mock_agents,
        seed=None,  # Default
        pub=None,
        privs=None
    )

@patch('src.arena._run_game')
def test_arena_play_game_with_initial_states(mock_run_game_async, mock_agents, mock_public_state_win_team0, mock_private_states):
    async def async_mock_run_game(*_args, **kwargs):
        # Stelle sicher, dass pub und privs korrekt durchgereicht wurden
        assert kwargs.get('pub') is mock_public_state_win_team0
        privs = kwargs.get('privs')
        assert privs is mock_private_states
        return mock_public_state_win_team0

    mock_run_game_async.side_effect = async_mock_run_game

    init_pubs = [mock_public_state_win_team0]
    init_privs = [mock_private_states]  # Liste von Listen von PrivateStates

    # noinspection PyTypeChecker
    arena = Arena(mock_agents, max_games=1, worker=1)
    arena._play_game(0)

    mock_run_game_async.assert_called_once_with(
        table_name="Game_0",
        agents=mock_agents,
        seed=None,
        pub=init_pubs[0],
        privs=init_privs[0]
    )

def test_arena_play_game_stop_event_set(mock_agents):
    arena = Arena(mock_agents, max_games=1, worker=1)
    arena._stop_event.set()
    result = arena._play_game(0)
    assert result is None

def test_arena_update_stats(mock_agents, mock_public_state_win_team0):
    arena = Arena(mock_agents, max_games=1, worker=1)
    arena._time_start = 0  # Mock time.time()

    with patch('src.arena.time', return_value=5):  # Mock time.time() für Dauerberechnung
        arena._update((0, mock_public_state_win_team0))

    assert arena.games == 1
    assert arena.rounds == 5
    assert arena.tricks == 20
    assert arena.rating == [1, 0, 0]  # Team 0 gewinnt
    assert arena.seconds == 5

def test_arena_update_stats_team1_wins(mock_agents, mock_public_state_win_team1):
    arena = Arena(mock_agents, max_games=1, worker=1)
    arena._time_start = 0
    with patch('src.arena.time', return_value=1):
        arena._update((0, mock_public_state_win_team1))
    assert arena.rating == [0, 1, 0]

def test_arena_update_stats_draw(mock_agents, mock_public_state_draw):
    arena = Arena(mock_agents, max_games=1, worker=1)
    arena._time_start = 0
    with patch('src.arena.time', return_value=1):
        arena._update((0, mock_public_state_draw))
    assert arena.rating == [0, 0, 1]

def test_arena_update_no_result(mock_agents):
    arena = Arena(mock_agents, max_games=1, worker=1)
    initial_games = arena.games
    arena._update(None)  # Sollte einfach zurückkehren
    assert arena.games == initial_games  # Keine Änderung

# --- Early Stopping Tests ---
def test_arena_early_stopping_win_rate_achieved(mock_agents, mock_public_state_win_team0):
    arena = Arena(mock_agents, max_games=10, early_stopping=True, win_rate=0.6, worker=1)
    arena._time_start = 0
    arena._rating = [5, 0, 0]

    # Spiel 1: Sieg für Team 0
    # Rating: [1,0,0], Games: 1, total_bewertet = 1, unplayed = 9
    # 1/1 = 1.0 >= 0.6 -> Stop!
    with patch('src.arena.time', return_value=1):
        arena._update((0, mock_public_state_win_team0))
    assert arena._stop_event.is_set()

def test_arena_early_stopping_win_rate_unreachable(mock_agents, mock_public_state_win_team1):
    arena = Arena(mock_agents, max_games=3, early_stopping=True, win_rate=0.5, worker=1)
    arena._time_start = 0

    # Spiel 1 (Index 0): Niederlage für Team 0 -> Rating [0,1,0], unplayed=2
    # max_possible_wins = 0 (current) + 2 (unplayed) = 2
    # total_bewertbar = 3 (max_games) - 0 (draws) = 3
    # 2/3 = 0.66 >= 0.5 -> noch erreichbar
    with patch('src.arena.time', return_value=1):
        arena._update((0, mock_public_state_win_team1))
    assert not arena._stop_event.is_set()

    # Spiel 2 (Index 1): Niederlage für Team 0 -> Rating [0,2,0], unplayed=1
    # max_possible_wins = 0 (current) + 1 (unplayed) = 1
    # total_bewertbar = 3 (max_games) - 0 (draws) = 3
    # 1/3 = 0.33 < 0.5 -> Stop!
    with patch('src.arena.time', return_value=2):
        arena._update((1, mock_public_state_win_team1))
    assert arena._stop_event.is_set()

def test_arena_early_stopping_not_met(mock_agents, mock_public_state_win_team0):
    arena = Arena(mock_agents, max_games=10, early_stopping=True, win_rate=0.9, worker=1)
    arena._time_start = 0
    with patch('src.arena.time', return_value=1):
        arena._update((0, mock_public_state_win_team0))  # 1/1 = 1.0 (noch nicht sicher, da unplayed > 0)
    assert not arena._stop_event.is_set()  # noch nicht sicher, da (1+9)/(10) = 1.0 >= 0.9

@patch('src.arena.Arena._play_game')  # Mocke _play_game
def test_arena_run_single_worker(mock_play_game, mock_agents, mock_public_state_win_team0):
    # _play_game soll (index, pub_state) zurückgeben
    mock_play_game.side_effect = lambda game_idx: (game_idx, mock_public_state_win_team0)

    max_games = 3
    arena = Arena(mock_agents, max_games=max_games, worker=1, verbose=False)

    # Mock _update, um seine Aufrufe zu überprüfen
    with patch.object(arena, '_update', wraps=arena._update) as mock_update_method:
        arena.run()
        assert mock_play_game.call_count == max_games
        assert mock_update_method.call_count == max_games
        for i in range(max_games):
            # Überprüfe, ob _play_game mit dem richtigen Index aufgerufen wurde
            assert call(i) in mock_play_game.call_args_list
            # Überprüfe, ob _update mit dem Ergebnis von _play_game aufgerufen wurde
            mock_update_method.assert_any_call((i, mock_public_state_win_team0))

    assert arena.games == max_games
    assert arena.rating == [max_games, 0, 0]

@patch('src.arena.Pool')  # Mocke multiprocessing.Pool
@patch('src.arena.Arena._play_game')  # _play_game wird im Pool-Prozess ausgeführt, mocken wir es hier nicht direkt, sondern was der Pool zurückgibt
def test_arena_run_multi_worker(_mock_arena_play_game_method_placeholder, mock_pool_cls, mock_agents, mock_public_state_win_team0):
    # Dieser Test ist etwas komplexer, da wir Pool und Callbacks mocken müssen.
    # Für einen einfacheren Test könnte man `_play_game` so mocken, dass es direkt
    # ein Ergebnis liefert, und dann prüfen, ob `_update` korrekt aufgerufen wird.

    max_games = 2
    num_workers = 2

    # Mock-Instanz für den Pool
    mock_pool_instance = MagicMock()
    mock_pool_cls.return_value = mock_pool_instance

    # Ergebnisse, die `apply_async` über den `callback` an `_update` liefern soll.
    # Der Callback wird mit dem Ergebnis von _play_game aufgerufen
    # _play_game gibt (game_index, pub_state) zurück.
    # Wir müssen also den Callback `arena._update` mit diesem Tupel aufrufen lassen.

    # Die `apply_async` Methode soll den `callback` mit dem Ergebnis von `_play_game` aufrufen.
    # Wir simulieren das, indem wir `apply_async` so mocken, dass es den Callback direkt ausführt.
    # Die `args` für `_play_game` (game_index) werden an `apply_async` übergeben.

    # Hilfsfunktion, um den apply_async-Aufruf zu simulieren, der den Callback auslöst.
    # Der Callback (arena._update) erwartet das Ergebnis von _play_game
    update_calls = []

    # noinspection GrazieInspection
    def mock_apply_async(_target_func, args, callback):
        # target_func ist arena._play_game
        # args ist (game_index,)
        # callback ist arena._update
        game_index = args[0]
        # Simuliere das Ergebnis von _play_game
        play_game_result = (game_index, mock_public_state_win_team0)
        callback(play_game_result)  # Rufe _update mit dem simulierten Ergebnis auf
        update_calls.append(play_game_result)  # Für Assertions
        return MagicMock()  # apply_async gibt ein AsyncResult-Objekt zurück

    mock_pool_instance.apply_async.side_effect = mock_apply_async

    arena = Arena(mock_agents, max_games=max_games, worker=num_workers, verbose=False)

    # Da `_update` jetzt direkt durch `mock_apply_async` aufgerufen wird,
    # brauchen wir `_update` nicht separat zu mocken, sondern können seine Seiteneffekte prüfen.
    arena.run()

    mock_pool_cls.assert_called_once_with(processes=num_workers)
    assert mock_pool_instance.apply_async.call_count == max_games

    # Überprüfe, dass _update (via Callback) mit den richtigen Argumenten aufgerufen wurde
    assert len(update_calls) == max_games
    for i in range(max_games):
        # Stelle sicher, dass für jeden Spielindex ein Update erfolgte
        assert any(res[0] == i and res[1] == mock_public_state_win_team0 for res in update_calls)

    mock_pool_instance.close.assert_called_once()
    mock_pool_instance.join.assert_called_once()

    assert arena.games == max_games
    assert arena.rating == [max_games, 0, 0]

def test_cpu_count():
    with patch('src.arena.cpu_count', return_value=4) as mock_cpu_c:
        assert Arena.cpu_count() == 4
        mock_cpu_c.assert_called_once()

def test_properties(mock_agents, mock_public_state_win_team0):
    arena = Arena(mock_agents, max_games=1)
    arena._seconds = 10
    arena._games = 1
    arena._rounds = 5
    arena._tricks = 20
    arena._rating = [1, 0, 0]

    assert arena.seconds == 10
    assert arena.games == 1
    assert arena.rounds == 5
    assert arena.tricks == 20
    assert arena.rating == [1, 0, 0]
