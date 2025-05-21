# tests/test_game_engine.py
"""
Tests für die GameEngine-Klasse.

Zusammenfassung der Tests für GameEngine:
- Initialisierung:
    - Korrekte Initialisierung der Engine mit Tischnamen und (Mock-)Spielern.
    - Überprüfung der korrekten Zuordnung der Spieler.
- Zustands-Reset:
    - Korrekte Funktionalität der statischen Methoden zum Zurücksetzen des PublicState (`reset_public_state_for_round`) und PrivateState (`reset_private_state_for_round`) für eine neue Runde.
- Kartenmanagement:
    - Korrektheit der Logik zum Austeilen von Karten (`deal_out`).
    - Korrektheit der Logik zum Aufnehmen von Karten durch einen Spieler (`take_cards`).
- Zustandsänderungen durch Spielaktionen (Test der statischen Methoden):
    - Korrektes Setzen von Tichu-Ansagen (`announce`).
    - Korrekte Aktualisierung des PublicState beim Ausspielen einer Kombination oder Passen (`play_pub`), inklusive Stichhistorie, gespielte Karten, Handkartenzahl, Stichbesitzer, Stichpunkte etc.
    - Korrektes Setzen eines Wunsches (`set_wish`).
    - Korrekte Logik beim Abräumen eines Stichs (`clear_trick`), inklusive Punktevergabe, Verschenken des Drachenstichs und (teilweise) Rundenende-Logik (Punkteübertrag, Score-Update - *Hinweis: Vollständige Rundenende-Punkteberechnung in `clear_trick` muss ggf. noch verfeinert werden*).
    - Korrekte Logik für den Spielerwechsel (`turn`), auch nach Ausspielen des Hundes.
- Spieler-Interaktion (mit Mocks):
    - Überprüfung, ob die Engine die Methoden der (Mock-)Spieler an den erwarteten Stellen aufruft (Beispiel: `schupf`).
"""

# Erklärungen zu Fixtures und Mocks im Code:
#
# Fixtures (@pytest.fixture):
# Das sind Funktionen, die Setup-Code ausführen (z.B. Objekte erstellen) und das Ergebnis an Testfunktionen übergeben,
# die sie als Argument anfordern. Das vermeidet Code-Wiederholung im Setup. mock_agents, initial_public_state,
# initial_private_states, game_engine, sind Beispiele.
#
# Mocks (mocker, AsyncMock):
# Das sind "Stellvertreter"-Objekte. Wir erstellen Mocks für die Player, damit die GameEngine etwas zum Interagieren hat,
# ohne dass wir echte Agentenlogik benötigen.
# AsyncMock ist wichtig für async def-Methoden der Spieler.
# Wir können das return_value eine Mock-Methode setzen (z.B. mock_player.schupf.return_value = ...), um zu steuern, was
# die Engine "zurückbekommt".
# Wir können prüfen, ob und wie eine Mock-Methode aufgerufen wurde (z.B. mock_player.schupf.assert_awaited_once_with(...)).
# Dies testet, ob die Engine die Spieler korrekt anspricht.
#
# States (initial_public_state, initial_private_states):
# Dies sind einfach Instanzen unserer Datenklassen, die über Fixtures bereitgestellt werden, damit jeder Test mit einem
# sauberen Zustand beginnt.
#
# Wichtige Hinweise:
# 1) Test für clear_trick am Rundenende: Dieser Test hat eine potenzielle Lücke in deiner clear_trick-Implementierung
# aufgedeckt, was die Punkte der Restkarten des Losers angeht. Die Testlogik muss angepasst werden, sobald die Engine-Logik
# dazu finalisiert ist. Das ist ein super Beispiel dafür, wie Tests helfen, Design-Fragen zu klären!
# 2) Async-Tests: Tests, die await verwenden (um z.B. auf gemockte async-Player-Methoden zu "warten"), sollten mit
# @pytest.mark.asyncio markiert werden, falls du pytest-asyncio verwendest. Mit neueren pytest-Versionen ist das oft nicht
# mehr strikt nötig, aber schadet auch nicht. Der wichtigste Teil ist die Verwendung von AsyncMock und await im Test selbst
# sowie assert_awaited_once_with.
# 3) Komplexität der Game Loop: Die run_game_loop direkt zu testen ist sehr aufwändig. Es ist meist effektiver, die einzelnen
# Zustandsänderung-Methoden (wie play_pub, clear_trick, announce etc.) isoliert zu testen und sicherzustellen, dass die
# Engine die Player-Methoden korrekt aufruft (wie im test_engine_calls_player_schupf-Beispiel angedeutet).

from typing import List
import pytest
from unittest.mock import AsyncMock
from src.players.agent import Agent
from src.game_engine import GameEngine
from src.public_state import PublicState
from src.private_state import PrivateState
from src.lib.cards import Cards, parse_cards, CARD_MAH, CARD_DRA, deck
from src.lib.combinations import CombinationType, FIGURE_PASS, FIGURE_DOG, FIGURE_DRA

# === Fixtures: Wiederverwendbare Test-Setups ===

# @pytest.fixture(autouse=True)
# def make_agents_real(mocker):
#     # Alle isinstance-Prüfungen gegen Agent liefern True
#     mocker.patch.object(Agent, "__instancecheck__", return_value=True)
    
@pytest.fixture
def mock_agents(mocker) -> List[AsyncMock]:
    """
    Erstellt eine Liste von 4 Mock-Objekten, die sich wie Player verhalten.

    Erklärung:
    - 'mocker': Dies ist ein spezieller Fixture von pytest-mock. Es bietet eine
      einfache Schnittstelle zum Erstellen von Mocks.
    - 'AsyncMock': Wir verwenden AsyncMock, weil die Methoden in unserer Player-Klasse
      (wie play, announce, schupf etc.) 'async def' sind. Ein normaler Mock würde
      bei 'await' einen Fehler werfen. AsyncMock simuliert dieses async-Verhalten.
    - List[AsyncMock]: Wir geben den Typ explizit an (gute Praxis).
    - return [...]: Erzeugt 4 separate AsyncMock-Instanzen. Jede kann individuell
      konfiguriert werden (z.B. was sie zurückgeben soll, wenn ihre Methoden aufgerufen werden).
      Wir setzen hier schon mal den 'name' und 'player_index' für die Mocks.
    """
    players = []
    for i in range(4):
        # Erstelle einen Mock, der vorgibt, ein Player-Objekt zu sein
        player_mock = mocker.create_autospec(Agent, instance=True)
        player_mock.__class__ = Agent
        # Wichtig: Da Player Methoden wie play async sind, ersetzen wir sie explizit durch AsyncMocks,
        # NACHDEM create_autospec die Signatur erstellt hat.
        player_mock.schupf = AsyncMock(name=f'schupf_mock_{i}')
        player_mock.announce = AsyncMock(name=f'announce_mock_{i}')
        player_mock.play = AsyncMock(name=f'play_mock_{i}') # play statt combination
        player_mock.wish = AsyncMock(name=f'wish_mock_{i}')
        player_mock.give_dragon_away = AsyncMock(name=f'gift_mock_{i}') # Umbenannt
        player_mock.cleanup = AsyncMock(name=f'cleanup_mock_{i}') # Auch cleanup mocken

        # Setze Standard-Attribute für den Mock
        player_mock.name = f"MockPlayer_{i}"
        player_mock.index = i
        player_mock.session_id = f"session_{i}"
        # Stellt sicher, dass die Index-Properties des Mocks funktionieren
        player_mock.partner_index = (i + 2) % 4
        player_mock.opponent_right_index = (i + 1) % 4
        player_mock.opponent_left_index = (i + 3) % 4

        players.append(player_mock)
    return players

@pytest.fixture
def game_engine(mock_agents) -> GameEngine:
    """
    Erstellt eine GameEngine-Instanz, die mit den Mock-Spielern initialisiert ist.

    Erklärung:
    - 'mock_agents': Pytest erkennt, dass dieser Fixture den Fixture 'mock_agents'
      benötigt. Es führt zuerst 'mock_agents' aus und übergibt das Ergebnis
      (die Liste der 4 AsyncMocks) hier als Argument.
    - return GameEngine(...): Erstellt die Engine mit diesen Mocks als "Spieler".
      So können wir das Verhalten der Engine testen, ohne echte Agenten-Logik auszuführen.
    """
    # Seed setzen (für reproduzierbare Zufälligkeit in Tests, falls nötig)
    return GameEngine(table_name="TestEngineTable", default_agents=mock_agents, seed=12345)

@pytest.fixture
def initial_public_state() -> PublicState:
    """Erstellt einen frischen PublicState für Tests."""
    return PublicState(
        table_name="TestEngineTable",
        player_names=["P0", "P1", "P2", "P3"],
        count_hand_cards=[14, 14, 14, 14],
    )


@pytest.fixture
def initial_private_states() -> List[PrivateState]:
    """Erstellt 4 frische PrivateStates für Tests."""
    return [PrivateState(player_index=i) for i in range(4)]

# === Testfälle ===

def test_game_engine_initialization(game_engine, mock_agents):
    """Testet, ob die Engine korrekt mit Mocks initialisiert wird."""
    assert game_engine.table_name == "TestEngineTable"
    assert len(game_engine.players) == 4
    # Prüfen, ob die übergebenen Mocks auch wirklich die Spieler in der Engine sind
    assert game_engine.players[0] is mock_agents[0]
    assert game_engine.players[1] is mock_agents[1]
    assert game_engine.players[2] is mock_agents[2]
    assert game_engine.players[3] is mock_agents[3]
    # Prüfen, ob die Namen im PublicState (falls schon gesetzt) passen
    # (Engine setzt die Namen eventuell erst später, je nach Implementierung).
    # assert game_engine._players[0].name == "MockPlayer_0" # Zugriff auf _players ist unschön

# --- Tests für State Resets ---

def test_reset_public_state_for_round(game_engine, initial_public_state):
    """Testet das Zurücksetzen des PublicState für eine neue Runde."""
    pub = initial_public_state
    # Zustand "verschmutzen"
    pub.current_turn_index = 1
    pub.played_cards = parse_cards("S5")
    pub.points = [10, 0, 0, 0]
    pub.winner_index = 0
    pub.tricks.append([(0, parse_cards("S5"), (CombinationType.SINGLE, 1, 5))]) # Test mit neuer tricks Struktur

    # Reset durchführen (reset_public_state_for_round ist static)
    GameEngine.reset_public_state_for_round(pub)

    # Prüfen, ob die Werte auf Defaults zurückgesetzt wurden
    assert pub.current_turn_index == -1
    assert pub.played_cards == []
    assert pub.points == [0, 0, 0, 0]
    assert pub.winner_index == -1
    assert pub.tricks == []
    assert pub.trick_combination == (CombinationType.PASS, 0, 0)
    # assert pub._current_trick_plays_internal == [] # Falls noch in PublicState

def test_reset_private_state_for_round(game_engine, initial_private_states):
    """Testet das Zurücksetzen eines PrivateState für eine neue Runde."""
    priv = initial_private_states[0]
    # Zustand "verschmutzen"
    priv.hand_cards = parse_cards("S5 G5")
    priv.given_schupf_cards = (2, 2), (2, 3), (2, 4)
    # priv.given_schupf_cards = [None, None, parse_cards("R2")[0], None] # Neue Form

    # Reset durchführen (reset_private_state_for_round ist static)
    GameEngine.reset_private_state_for_round(priv)

    # Prüfen
    assert priv.hand_cards == []
    assert priv.given_schupf_cards is None

# --- Tests für Kartenmanagement ---

def test_deal_out(game_engine):
    """Testet das Austeilen von Karten."""
    # deal_out ist static und braucht keine Engine-Instanz, aber wir nutzen die Klasse
    test_deck = list(parse_cards("S2 S3 S4 S5 S6 S7 S8 S9 SZ SB SD SK SA Ma B2 B3 B4 B5 B6 B7 B8 B9 BZ BB BD BK BA Hu G2 G3 G4 G5 G6 G7 G8 G9 GZ GB GD GK GA Dr R2 R3 R4 R5 R6 R7 R8 R9 RZ RB RD RK RA Ph"))
    assert len(test_deck) == 56

    # Teste Aushändigen von 8 Karten an Spieler 0
    cards_p0_8 = GameEngine.deal_out(test_deck, 0, 8)
    assert len(cards_p0_8) == 8
    assert cards_p0_8 == sorted(test_deck[0:8], reverse=True) # Muss sortiert sein

    # Teste Aushändigen von 14 Karten an Spieler 1
    cards_p1_14 = GameEngine.deal_out(test_deck, 1, 14)
    assert len(cards_p1_14) == 14
    assert cards_p1_14 == sorted(test_deck[14:28], reverse=True)

def test_take_cards(game_engine, initial_private_states):
    """Testet das Aufnehmen von Karten im PrivateState."""
    priv = initial_private_states[0]
    cards_to_take = parse_cards("SA RA GA SK SD RZ R8 R5")
    GameEngine.take_cards(priv, list(cards_to_take)) # Übergibt Kopie
    assert priv.hand_cards == cards_to_take # Sollte sortiert sein (falls take_cards sortiert)

# --- Tests für Spielzüge (Methoden, die den State ändern) ---
# Hier testen wir die *statischen* Methoden der GameEngine, die den Zustand ändern.
# Wir brauchen keine laufende Gameloop dafür.

def test_engine_announce(initial_public_state):
    """Testet das Setzen einer Tichu-Ansage im PublicState."""
    pub = initial_public_state
    player_index = 2
    # Annahme: Spieler 2 hat 14 Karten für kleines Tichu
    pub.count_hand_cards[player_index] = 14

    GameEngine.announce(pub, player_index, grand=False)
    assert pub.announcements == [0, 0, 1, 0] # Kleines Tichu für Spieler 2

    # Test Grand Tichu
    pub.announcements = [0, 0, 0, 0]
    pub.count_hand_cards[player_index] = 8 # 8 Karten für Grand Tichu
    GameEngine.announce(pub, player_index, grand=True)
    assert pub.announcements == [0, 0, 2, 0] # Großes Tichu

@pytest.mark.parametrize("initial_trick_owner, initial_tricks_len, expected_tricks_len, expected_last_trick_len", [
    (-1, 0, 1, 1), # Anspiel -> neuer Stich, Länge 1
    (0, 1, 1, 2), # Spieler 0 hat gelegt -> Stich wird erweitert
])
def test_engine_play_pub_add_to_trick_history(initial_public_state, initial_trick_owner, initial_tricks_len, expected_tricks_len, expected_last_trick_len):
    """Testet, wie play_pub die Stichhistorie (pub.tricks) aktualisiert."""
    pub = initial_public_state
    pub.current_turn_index = 1 # Spieler 1 ist dran
    pub.trick_owner_index = initial_trick_owner
    if initial_tricks_len > 0: # Simuliere existierenden Stich
        pub.tricks.append([(0, parse_cards("S5"), (CombinationType.SINGLE, 1, 5))])
    assert len(pub.tricks) == initial_tricks_len

    cards_to_play = parse_cards("S6")
    combination_to_play = (CombinationType.SINGLE, 1, 6)

    # Verwende die angepasste Signatur von play_pub
    GameEngine.play_pub(pub, list(cards_to_play), combination_to_play) # Kopie übergeben

    assert len(pub.tricks) == expected_tricks_len
    assert len(pub.tricks[-1]) == expected_last_trick_len # Länge des letzten/aktuellen Stichs
    # Prüfe, ob der letzte hinzugefügte Zug korrekt ist
    last_play_in_last_trick = pub.tricks[-1][-1]
    assert last_play_in_last_trick == (1, cards_to_play, combination_to_play)

def test_engine_play_pub_updates_state(initial_public_state):
    """Testet weitere State-Updates durch play_pub (nicht Passen)."""
    pub = initial_public_state
    player_index = 0
    pub.current_turn_index = player_index
    pub.count_hand_cards[player_index] = 5
    pub.played_cards = []

    cards_to_play = parse_cards("S8 G8")
    combination_to_play = (CombinationType.PAIR, 2, 8)

    GameEngine.play_pub(pub, list(cards_to_play), combination_to_play)

    assert pub.played_cards == cards_to_play
    assert pub.count_hand_cards[player_index] == 3 # 5 - 2
    assert pub.trick_owner_index == player_index
    assert pub.trick_combination == combination_to_play
    assert pub.trick_points == 0 # 8er haben keinen Wert

def test_engine_play_pub_passing(initial_public_state):
    """Testet State-Updates durch play_pub beim Passen."""
    pub = initial_public_state
    player_index = 1
    pub.current_turn_index = player_index
    pub.count_hand_cards[player_index] = 5
    pub.played_cards = parse_cards("S8 G8") # Karten von Spieler 0
    pub.tricks.append([(0, parse_cards("S5"), (CombinationType.SINGLE, 1, 5))])  # kein Anspiel
    pub.trick_owner_index = 0 # Spieler 0 hat den Stich
    pub.trick_combination = (CombinationType.PAIR, 2, 8)
    pub.trick_points = 0

    cards_to_play: Cards = [] # Leere Liste für Passen
    combination_to_play = FIGURE_PASS # (CombinationType.PASS, 0, 0)

    GameEngine.play_pub(pub, cards_to_play, combination_to_play)

    assert pub.played_cards == parse_cards("S8 G8") # Bleibt unverändert
    assert pub.count_hand_cards[player_index] == 5 # Bleibt unverändert
    assert pub.trick_owner_index == 0 # Bleibt Spieler 0
    assert pub.trick_combination == (CombinationType.PAIR, 2, 8) # Bleibt das Paar
    assert pub.trick_points == 0 # Bleibt unverändert
    # Prüfen, ob Passen zur History hinzugefügt wurde
    assert len(pub.tricks) == 1
    assert len(pub.tricks[0]) == 2
    assert pub.tricks[0][1] == (1, [], FIGURE_PASS) # Prüfe den Pass-Eintrag

def test_engine_set_wish(initial_public_state):
    """Testet das Setzen eines Wunsches."""
    pub = initial_public_state
    # Bedingung: Mah Jong muss gespielt worden sein (simulieren wir)
    pub.played_cards.append(CARD_MAH)
    GameEngine.set_wish(pub, 8)
    assert pub.wish_value == 8

def test_engine_clear_trick_normal(initial_public_state):
    """Testet das normale Abräumen eines Stichs."""
    pub = initial_public_state
    player_index = 0
    pub.current_turn_index = player_index # Spieler 0 räumt ab
    pub.trick_owner_index = player_index
    pub.trick_combination = (CombinationType.PAIR, 2, 10) # Paar 10
    pub.trick_points = 20 # Zwei 10er
    # Simuliere einen gespielten Stich in der History (für pub.tricks)
    pub.tricks.append([(0, parse_cards("SZ RZ"), (CombinationType.PAIR, 2, 10))])
    # pub._current_trick_plays_internal = [...] # Falls verwendet

    GameEngine.clear_trick(pub, opponent=-1) # Kein Verschenken

    assert pub.points[player_index] == 20
    assert pub.trick_owner_index == -1
    assert pub.trick_combination == FIGURE_PASS
    assert pub.trick_points == 0
    assert pub.trick_counter == 1
    # assert pub._current_trick_plays_internal == [] # Falls verwendet

def test_engine_clear_trick_dragon_gift(initial_public_state):
    """Testet das Abräumen und Verschenken eines Drachenstichs."""
    pub = initial_public_state
    player_index = 0 # Spieler 0 hat Drachen gewonnen
    opponent_index = 3 # Spieler 3 (linker Gegner) soll ihn bekommen
    pub.current_turn_index = player_index
    pub.trick_owner_index = player_index
    pub.trick_combination = FIGURE_DRA # Drache
    pub.trick_points = 25 + 5 # Drache + eine 5
    pub.played_cards = [CARD_DRA, (5,1)] # Wichtig für spätere Logik evtl.
    pub.tricks.append([(0, parse_cards("Dr R5"), FIGURE_DRA)]) # Simulierter Stich

    GameEngine.clear_trick(pub, opponent=opponent_index)

    assert pub.points[player_index] == 0 # Spieler 0 bekommt nichts
    assert pub.points[opponent_index] == 30 # Spieler 3 bekommt die Punkte
    assert pub.dragon_recipient == opponent_index
    assert pub.trick_owner_index == -1
    assert pub.trick_combination == FIGURE_PASS
    assert pub.trick_points == 0
    assert pub.trick_counter == 1

def test_engine_clear_trick_round_end(initial_public_state):
    """Testet das Abräumen des letzten Stichs am Rundenende (kein Doppelsieg)."""
    pub = initial_public_state

    # erste Runde

    pub.is_round_over = True # Runde ist vorbei
    pub.is_double_victory = False
    pub.winner_index = 0
    pub.loser_index = 1
    pub.current_turn_index = 2
    pub.trick_owner_index = 2
    pub.trick_combination = (CombinationType.SINGLE, 1, 5)
    # Angenommen, die gespielten Karten sind 80 Punkte, der Loser hat demnach noch 20 Punkte auf der Hand
    pub.played_cards = [c for c in list(parse_cards("S2 S3 S4 S6 S7 S8 S9 SZ SB SD SK SA Ma B2 B3 B4 B5 B6 B7 B8 B9 BZ BB BD BK BA Hu G2 G3 G4 G5 G6 G7 G8 G9 GZ GB GD GK GA Dr R2 R3 R4 R5 R6 R7 R8 R9 RZ RB RD RK RA Ph")) if c[0] != 5]
    pub.trick_points = 5
    pub.points = [45, 10, 20, 0]  # 80 Punkte - 5 Punkte

    GameEngine.clear_trick(pub, opponent=-1)

    # 1. Letzter Stich (5 Pkt) geht an den Stich-Besitzer (Spieler 2)
    # pub.points = [45, 10, 25, 0]
    # 2. Handkarten des Losers (20 Pkt) kriegt das gegnerische Team (rechten Gegner, Spieler 2)
    # pub.points = [45, 10, 45, 0]
    # 3. Looser gibt seine kassierten Punkte an den Gewinner
    # pub.points = [55, 0, 45, 0]
    assert pub.points == [55, 0, 45, 0]
    assert len(pub.game_score) == 2
    assert pub.game_score[0] == [100] and pub.game_score[1] == [0]
    assert pub.round_counter == 1

    # zweite Runde

    pub.announcements = [0, 0, 0, 1] # Keine Ansagen
    pub.is_round_over = True # Runde ist vorbei
    pub.is_double_victory = False
    pub.winner_index = 0
    pub.loser_index = 1
    pub.current_turn_index = 2
    pub.trick_owner_index = 2
    pub.trick_combination = (CombinationType.SINGLE, 1, 5)
    # Angenommen, die gespielten Karten sind 80 Punkte, der Loser hat demnach noch 20 Punkte auf der Hand
    pub.played_cards = [c for c in list(parse_cards("S2 S3 S4 S6 S7 S8 S9 SZ SB SD SK SA Ma B2 B3 B4 B5 B6 B7 B8 B9 BZ BB BD BK BA Hu G2 G3 G4 G5 G6 G7 G8 G9 GZ GB GD GK GA Dr R2 R3 R4 R5 R6 R7 R8 R9 RZ RB RD RK RA Ph")) if c[0] != 5]
    pub.trick_points = 5
    pub.points = [45, 10, 20, 0]  # 80 Punkte - 5 Punkte

    GameEngine.clear_trick(pub, opponent=-1)

    # wie erste Runde, aber Spieler 3 hatte Tichu angesagt und verloren
    assert pub.points == [55, 0, 45, -100]
    assert pub.game_score[0] == [100, 100] and pub.game_score[1] == [0, -100]
    assert pub.round_counter == 2

def test_engine_turn_normal(initial_public_state):
    """Testet den normalen Spielerwechsel."""
    pub = initial_public_state
    pub.current_turn_index = 0
    GameEngine.turn(pub)
    assert pub.current_turn_index == 1
    GameEngine.turn(pub)
    assert pub.current_turn_index == 2
    GameEngine.turn(pub)
    assert pub.current_turn_index == 3
    GameEngine.turn(pub)
    assert pub.current_turn_index == 0

def test_engine_turn_with_dog(initial_public_state):
    """Testet den Spielerwechsel nach Ausspielen des Hundes."""
    pub = initial_public_state
    dog_player = 1
    pub.current_turn_index = dog_player
    pub.trick_owner_index = dog_player # Spieler 1 hat Hund gelegt
    pub.trick_combination = FIGURE_DOG

    GameEngine.turn(pub)
    # Sollte zu Spieler 1+2 = 3 wechseln (Partner)
    assert pub.current_turn_index == 3


async def test_schupf(game_engine, initial_public_state, initial_private_states, mock_agents):
    """
    Testet die Schupf-Methode.
    """
    privs = initial_private_states
    player_index = 0
    privs[player_index].hand_cards = parse_cards("S2 B3 G4 R5 G5 B5 R6 G6 B6 R7 G7 B7 R8 G8")
    assert len(privs[player_index].hand_cards) == 14

    schupfed_cards = (2,1), (3,2), (4,3)  # S2 B3 G4
    game_engine.schupf(privs[player_index], schupfed_cards)
    assert len(privs[player_index].hand_cards) == 11
    assert privs[player_index].given_schupf_cards == schupfed_cards

    schupfed_cards = (9, 1), (9, 2), (9, 3)  # S9 B9 G9
    game_engine.take_schupfed_cards(privs[player_index], schupfed_cards)
    assert len(privs[player_index].hand_cards) == 14
    assert privs[player_index].received_schupf_cards == schupfed_cards

# -------------------------------------------------------
# Alte Tests (ursprünglich mit unittest geschrieben)
# -------------------------------------------------------

def test_shuffle_cards(game_engine):
    mixed_deck = list(deck)
    assert list(deck) == mixed_deck
    game_engine._shuffle_cards(mixed_deck)
    assert list(deck) != mixed_deck
