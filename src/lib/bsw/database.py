"""
Verwaltet eine SQLite-Datenbank mit Protokolldaten von Tichu-Spielen.
Diese Klasse agiert als Data Access Layer und Mapper zwischen den logischen
Entitäten (GameEntity, etc.) und dem normalisierten Datenbankschema.
"""

__all__ = "deserialize_cards", "deserialize_history", "update_elo", "TichuDatabase", "GameEntity", "RoundEntity", "PlayerEntity", "ETLErrorCode"

import enum
import os
import sqlite3
from dataclasses import dataclass, field
from src.lib.cards import Cards, parse_card, stringify_card
from tqdm import tqdm
from typing import List, Tuple, Generator, Optional


def serialize_cards(cards: Cards) -> str:
    """
    Serialisiert die Karten zu einem String.
    
    :param cards: Die Karten.
    :return: Kartenlabels ohne Leerzeichen.
    """
    return "".join([stringify_card(card) for card in cards])


def deserialize_cards(s: str) -> Cards:
    """
    Deserialisiert die Karten.
    
    :param s: Kartenlabels ohne Leerzeichen.
    :return: Karten.
    """
    return [parse_card(s[i:i + 2]) for i in range(0, len(s), 2)]


def serialize_history(history: List[Tuple[int, Cards, int]]) -> str:
    """
    Serialisiert die Historie.
    
    :param history: Die Historie als Liste.
    :return: Historie als String, z.B "3:R6R3Ph|2|3:R6R3Ph;0|2;3".
    """
    turns = []
    for player_index, cards, trick_collector_index in history:
        turn = f"{player_index}"
        if cards:
            turn += f":{serialize_cards(cards)}"
        if trick_collector_index != -1:
            turn += f";{trick_collector_index}"
        turns.append(turn)
    return "|".join(turns)


def deserialize_history(s) -> List[Tuple[int, Cards, int]]:
    """
    Serialisiert die Historie.

    :param s: Historie als String, z.B "3:R6R3Ph|2|3:R6R3Ph;0|2;3".
    :return: Die Historie als Liste.
    """
    history = []
    for turn in s.split("|"):
        parts = turn.split(";")
        trick_collector_index = int(parts[1]) if len(parts) == 2 else -1
        parts = parts[0].split(":")
        cards = deserialize_cards(parts[1]) if len(parts) == 2 else ""
        player_index = int(parts[0])
        history.append((player_index, cards, trick_collector_index))
    return history


def update_elo(r: Tuple[float, float, float, float], score: Tuple[float, float], k: Tuple[float, float, float, float] = (20.0, 20.0, 20.0, 20.0)) -> Tuple[float, float, float, float]:
    """
    Aktualisiert die Spielstärke der Tichu-Spieler nach einer Elo‑basierenden Berechnung.

    Grundformel zur Aktualisierung der Elo-Zahl:
        Eigene aktualisiertes Elo-Zahl = r_own + k * (s - e)
        k: K‑Faktor
        s: Tatsächliches Ergebnis der Partie
        e: Erwartetes Ergebnis der Partie = 1 / (1 + 10^((r_opp - r_own) / 400.0))
        r_own: Eigene bisherige Elo-Zahl
        r_opp: Elo-Zahl des Gegners

    :param r: Bisherige Spielstärken der 4 Spieler.
    :param score: Das Endergebnis der Partie.
    :param k: Der K‑Faktor für jeden Spieler, der festlegt, wie stark sich ein Ergebnis auswirkt (niedriger Wert == Profi, hoher Wert == Anfänger).
    :return: Neue Spielstärken der 4 Spieler
    """
    r20 = (r[2] + r[0]) / 2.0  # Mittelwert der Ratings von Team 20
    r31 = (r[3] + r[1]) / 2.0  # Mittelwert der Ratings von Team 31
    e20 = 1.0 / (1.0 + 10 ** ((r31 - r20) / 400.0))  # erwartete Gewinnwahrscheinlichkeit für Team 20 (zw. 0.0 und 1.0)
    s20 = 1 if score[0] > score[1] else 0 if score[0] < score[1] else 0.5  # tatsächlicher Gewinn für Team 20 (1 == Sieg, 0.5 == Unentschieden, 0 == Niederlage)
    diff20 = s20 - e20  # Abweichung für Team 10
    diff31 = -diff20  # Abweichung für Team 31
    return (r[0] + k[0] * diff20,
            r[1] + k[1] * diff31,
            r[2] + k[2] * diff20,
            r[3] + k[3] * diff31)


def get_k_factor(games_played: int, max_elo: float) -> float:
    """
    Bestimmt den K-Faktor basierend auf der Anzahl der gespielten Partien.

    :param games_played: Anzahl der gespielten Partien.
    :param max_elo: Die höchste Elo-Zahl, die der Spieler erreicht hat.
    :return: Der K-Faktor.
    """
    # Im Schach hat k im Regelfall den Wert 40, 20 oder 10:
    # k = 40: für Spieler, die neu in der Ratingliste sind und weniger als 30 Partien aufweisen.
    # k = 20: für alle Spieler mit mindestens dreißig gewerteten Partien und einer maximalen Elo-Zahl < 2400. Dieser k-Wert trifft für die meisten Spieler zu.
    # k = 10: für alle Top-Spieler, die eine Elo-Zahl ≥ 2400 erreicht haben, selbst wenn die Elo-Zahl wieder unter diesen Wert fällt.
    # Quelle: https://de.wikipedia.org/wiki/Elo-Zahl
    if games_played < 30:
        return 40.0  # Anfänger, Rating soll sich schnell anpassen

    if max_elo < 2400:
        return 20.0  # Standard

    return 10.0  # Top-Spieler


class ETLErrorCode(enum.IntEnum):
    """
    Fehlercodes für den ETL-Prozess: Extract, Transform, Load
    """
    NO_ERROR = 0
    """Kein Fehler"""

    # Karten

    INVALID_CARD_LABEL = 10
    """Unbekanntes Kartenlabel."""

    INVALID_CARD_COUNT = 11
    """Anzahl der Karten ist fehlerhaft."""

    DUPLICATE_CARD = 12
    """Karten mehrmals vorhanden."""

    CARD_NOT_IN_HAND = 13
    """Karte gehört nicht zu den Handkarten."""

    CARD_ALREADY_PLAYED = 14
    """Karte bereits gespielt."""

    # Spielzüge

    PASS_NOT_POSSIBLE = 20
    """Passen nicht möglich."""

    WISH_NOT_FOLLOWED = 21
    """Wunsch nicht beachtet."""

    COMBINATION_NOT_PLAYABLE = 22
    """Kombination nicht spielbar."""

    PLAYER_NOT_ON_TURN = 23
    """Der Spieler ist nicht am Zug."""

    HISTORY_TOO_SHORT = 24
    """Es fehlen Einträge in der Historie."""

    HISTORY_TOO_LONG = 25
    """Karten ausgespielt, obwohl die Runde vorbei ist (wurde korrigiert)."""

    # Drache verschenken

    DRAGON_NOT_GIVEN = 30
    """Drache hat den Stich nicht gewonnen, wurde aber nicht verschenkt."""

    DRAGON_GIVEN_TO_OWN_TEAM = 31
    """Drache an eigenes Team verschenkt."""

    DRAGON_GIVEN_WITHOUT_BEAT = 32
    "Drache verschenkt, aber niemand hat durch den Drachen ein Stich gewonnen."

    # Wunsch

    WISH_WITHOUT_MAHJONG = 40
    """Wunsch geäußert, aber kein Mahjong gespielt."""

    # Tichu-Ansage

    ANNOUNCEMENT_NOT_POSSIBLE = 50
    """Tichu-Ansage an der geloggten Position nicht möglich (wurde korrigiert)."""

    # Rundenergebnis

    SCORE_NOT_POSSIBLE = 60
    """Rechenfehler! Geloggtes Rundenergebnis ist nicht möglich (wurde korrigiert)."""

    SCORE_MISMATCH = 61
    """Geloggtes Rundenergebnis stimmt nicht mit dem berechneten Ergebnis überein (wurde korrigiert)."""

    # Endergebnis

    GAME_NOT_FINISHED  = 70
    """Partie nicht zu Ende gespielt."""

    GAME_OVERPLAYED  = 71
    """Ein oder mehrere Runden gespielt, obwohl die Partie bereits entschieden war."""

    # Runden

    ROUND_FAILED = 80
    """Mindestens eine Runde ist fehlerhaft."""


@dataclass
class PlayerEntity:
    """
    Entität für einen Spieler.

    :ivar id: ID des Spielers.
    :ivar name: Der eindeutige Name des Spielers.
    :ivar elo: Die Elo-Zahl (Spielstärke) des Spielers.
    :ivar num_games: Anzahl der gespielten Partien.
    :ivar num_rounds: Anzahl der gespielten Runden.
    :ivar grand_tichu_success_rate: Wie oft gewinnt er sein großes Tichu?
    :ivar tichu_success_rate: Wie oft gewinnt er sein einfaches Tichu?
    :ivar tichu_suicidal_rate: Wie oft hat der Spieler Tichu angesagt, obwohl bereits ein Mitspieler fertig war?
    :ivar tichu_premature_rate: Wie oft hat der Spieler Tichu angesagt, ohne direkt danach Karten auszuspielen?
    :ivar games_win_rate: Wie oft gewinnt er eine Partie?
    :ivar avg_score_diff: Durchschnittliche Punktedifferenz einer Runde.
    """
    id: int = 0  # wird beim Speichern generiert, wenn 0
    name: str = ""
    # Aggregierte Daten (werden beim Speichern automatisch berechnet)
    elo: float = 1500.0
    num_games: int = 0
    num_rounds: int = 0
    grand_tichu_success_rate: float = 0.0
    tichu_success_rate: float = 0.0
    tichu_suicidal_rate: float = 0.0
    tichu_premature_rate: float = 0.0
    games_win_rate: float = 0.0
    avg_score_diff: float = 0.0


@dataclass
class RoundEntity:
    """
    Entität für eine Runde.

    :ivar id: ID der Runde.
    :ivar game_id: ID der Partie.
    :ivar round_index: Index der Runde innerhalb der Partie.
    :ivar players: Die 4 Spieler dieser Runde.
    :ivar start_hands: Handkarten der Spieler vor dem Schupfen (zuerst die 8 Grand-Tichu-Karten, danach die restlichen).
    :ivar num_bombs: Anzahl der Bombenblätter nach dem Schupfen.
    :ivar schupf_hands: Abgegebene Tauschkarten der Spieler (an rechten Gegner, Partner, linken Gegner).
    :ivar tichu_positions: Position in der Historie, an der Tichu angesagt wurde (-3 == kein Tichu, -2 == großes Tichu, -1 == Ansage vor oder während des Schupfens).
    :ivar tichu_suicidal: Gibt an, ob ein Spieler Tichu angesagt hatte, obwohl bereits ein Mitspieler fertig war.
    :ivar tichu_premature: Gibt an, ob ein Spieler Tichu angesagt hatte, ohne direkt danach Karten auszuspielen.
    :ivar wish_value: Der gewünschte Kartenwert (2 bis 14, -1 == kein Mahjong gespielt, 0 == ohne Wunsch).
    :ivar dragon_giver: Index des Spielers, der den Drachen verschenkte (-1 == Drache wurde nicht verschenkt).
    :ivar dragon_recipient: Index des Spielers, der den Drachen bekommen hat (-1 == Drache wurde nicht verschenkt).
    :ivar gift_relative_index: Wahl des Spielers, der den Drachen verschenkte (1 == rechte Gegner, 3 == linke Gegner, -1 == keine Wahl).
    :ivar is_phoenix_low: Gibt an, ob der Phönix in einer mehrdeutigen Kombination den niedrigeren Rang mimte.
    :ivar winner_index: Index des Spielers, der zuerst in der aktuellen Runde fertig wurde (-1 == kein Spieler).
    :ivar winner_position: Position in der Historie, wo der erste Spieler fertig wurde.
    :ivar loser_index: Index des Spielers, der in der aktuellen Runde als letztes übrig blieb (-1 == kein Spieler).
    :ivar is_double_victory: Gibt an, ob die Runde durch einen Doppelsieg beendet wurde.
    :ivar score: Rundenergebnis (Team20, Team31).
    :ivar score_diff: Punktedifferenz = Team20-Team31. Dies ist die Zielvariable des Values-Netzes.
    :ivar history: Spielzüge. Jeder Spielzug ist ein Tuple: Spieler-Index + Karten + Spieler-Index, der den Stich nach dem Zug kassiert (-1 == Stich nicht kassiert).
    :ivar error_code: ETL-Fehlercode.
    :ivar error_context: Im Fehlerfall der betroffene Abschnitt aus der Quelle, sonst None.
    :ivar num_tricks: Anzahl der Stiche in dieser Runde.
    :ivar num_turns: Anzahl der Spielzüge in dieser Runde.
    """
    id: int = 0  # wird beim Speichern generiert, wenn 0
    game_id: int = 0  # wird beim Speichern ermittelt, wenn 0
    round_index: int = -1
    players: List[PlayerEntity] = field(default_factory=lambda: [PlayerEntity(), PlayerEntity(), PlayerEntity(), PlayerEntity()])
    start_hands: List[Cards] = field(default_factory=lambda: [[], [], [], []])
    num_bombs: int = 0
    schupf_hands: List[Cards] = field(default_factory=lambda: [[], [], [], []])
    tichu_positions: List[int] = field(default_factory=lambda: [-3, -3, -3, -3])
    tichu_suicidal: bool = False
    tichu_premature: bool = False
    wish_value: int = -1
    dragon_giver: int = -1
    dragon_recipient: int = -1
    gift_relative_index: int = -1
    is_phoenix_low: bool = False
    winner_index: int = -1
    winner_position: int = -1
    loser_index: int = -1
    is_double_victory: bool = False
    score: Tuple[int, int] = (0, 0)
    score_diff: int = 0
    history: List[Tuple[int, Cards, int]] = field(default_factory=list)
    error_code: ETLErrorCode = ETLErrorCode.NO_ERROR
    error_context: Optional[str] = None
    # Aggregierte Daten (werden beim Speichern automatisch berechnet)
    num_tricks: int = 0
    num_turns: int = 0

@dataclass
class GameEntity:
    """
    Entität für eine Partie.

    :ivar id: ID der Partie.
    :ivar players: Die 4 Spieler zu Beginn der Partie.
    :ivar rounds: Liste der Rundendaten dieser Partie.
    :ivar player_changed: True, wenn mindestens ein Spieler während der Partie wechselt.
    :ivar year: Jahr der Logdatei.
    :ivar month: Monat der Logdatei.
    :ivar error_code: ETL-Fehlercode (0 == kein Fehler).
    :ivar total_score: Endergebnis (Team20, Team31).
    :ivar num_rounds: Anzahl der gespielten Runden in dieser Partie.
    :ivar avg_tricks_per_round: Durchschnittliche Anzahl Stiche pro Runde.
    :ivar avg_turns_per_round: Durchschnittliche Anzahl Spielzüge pro Runde.
    """
    id: int = 0  # wird beim Speichern generiert, wenn 0
    players: List[PlayerEntity] = field(default_factory=lambda: [PlayerEntity(), PlayerEntity(), PlayerEntity(), PlayerEntity()])
    player_changed: bool = False
    rounds: List[RoundEntity] = field(default_factory=list)
    year: int = -1
    month: int = -1
    error_code: ETLErrorCode = ETLErrorCode.NO_ERROR
    # Aggregierte Daten (werden beim Speichern automatisch berechnet)
    total_score: Tuple[int, int] = (0, 0)
    num_rounds: int = 0
    avg_tricks_per_round: float = 0.0
    avg_turns_per_round: float = 0.0
    
    
class TichuDatabase:
    """
    Tichu-Datenbank.
    """
    
    def __init__(self, database: str):
        """
        Initialisiert die Datenbank.

        :param database: Die SQLite-Datenbankdatei.
        """
        self._database = database
        """Die SQLite-Datenbankdatei."""

        self._conn: Optional[sqlite3.Connection] = None
        """Die Datenbankverbindung."""

    def __del__(self):
        """
        Bereinigt Ressourcen.
        """
        self.close()

    def open(self):
        """
        Stellt eine Verbindung mit der SQLite-Datenbank her.

        Falls die DB nicht existiert, wird sie erstellt und Tabellen eingerichtet.
        """
        if self._conn:
            return

        # Datenbankverbindung herstellen
        db_exists = os.path.exists(self._database)
        os.makedirs(os.path.dirname(self._database), exist_ok=True)
        self._conn = sqlite3.connect(self._database)
        self._conn.row_factory = sqlite3.Row  # um auf die Spalten per Name zugreifen zu können

        # Tabellen einrichten
        if not db_exists:
            self._create_tables()

    def close(self):
        """
        Schließt die Datenbankverbindung, sofern sie offen ist.
        """
        if self._conn:
            self._conn.close()
            self._conn = None

    def cursor(self) -> sqlite3.Cursor:
        """
        Gibt einen Datenbank-Cursor zurück, mit dem man SQL-Statements ausführen kann.

        :return: Datenbank-Cursor.
        """
        return self._conn.cursor()

    def commit(self):
        """
        Übernimmt alle ausstehenden Transaktionen.
        """
        self._conn.commit()

    def rollback(self):
        """
        Führt ein Rollback zum Anfang einer ausstehenden Transaktion durch.
        """
        self._conn.rollback()

    def games(self) -> Generator[GameEntity]:
        """
        Liefert alle fehlerfreien Partien aus.

        :return: Ein Generator, der die Daten einer Partie liefert.
        """
        self.open()
        game_cursor = self.cursor()
        round_cursor = self.cursor()
        player_cursor = self.cursor()
        try:
            # Alle fehlerfreien Partien abfragen
            game_cursor.execute("SELECT * FROM games WHERE error_code = 0 ORDER BY id")
            for g in game_cursor:
                # Hole die Start-Spieler der Partie
                player_cursor.execute("""
                    SELECT p.* 
                    FROM players AS p
                    INNER JOIN games_players AS gp ON p.id = gp.player_id
                    WHERE gp.game_id = ? 
                    ORDER BY gp.player_index
                """, (g["id"],))
                players = []
                for p in player_cursor.fetchall():
                    players.append(PlayerEntity(
                        id=p["id"],
                        name=p["name"],
                        # Aggregierte Daten
                        elo=p["elo"],
                        num_games=p["num_games"],
                        num_rounds=p["num_rounds"],
                        grand_tichu_success_rate=p["grand_tichu_success_rate"],
                        tichu_success_rate=p["tichu_success_rate"],
                        tichu_suicidal_rate=p["tichu_suicidal_rate"],
                        tichu_premature_rate=p["tichu_premature_rate"],
                        games_win_rate=p["games_win_rate"],
                        avg_score_diff=p["avg_score_diff"],
                    ))

                game = GameEntity(
                    id=g["id"],
                    players=players,
                    player_changed=g["player_changed"],
                    year=g["log_year"],
                    month=g["log_month"],
                    error_code=g["error_code"],
                    # Aggregierte Daten
                    total_score=g["total_score"],
                    num_rounds=g["num_rounds"],
                    avg_tricks_per_round=g["avg_tricks_per_round"],
                    avg_turns_per_round=g["avg_turns_per_round"],
                )

                # Alle Rundendaten der Partie abfragen
                round_cursor.execute("SELECT * FROM rounds WHERE game_id = ? ORDER BY id", (g["id"],))
                for r in round_cursor:
                    # Hole die neuen Spieler, falls ein Spielerwechsel stattfand.
                    if g["player_changed"]:
                        player_cursor.execute("""
                            SELECT p.*, s.player_index 
                            FROM players AS p
                            INNER JOIN swaps AS s ON p.id = s.player_id
                            WHERE s.round_id = ?
                        """, (r["id"],))
                        for p in player_cursor.fetchall():
                            players[p["player_index"]] = PlayerEntity(
                                id=p["id"],
                                name=p["name"],
                                # Aggregierte Daten
                                elo=p["elo"],
                                num_games=p["num_games"],
                                num_rounds=p["num_rounds"],
                                grand_tichu_success_rate=p["grand_tichu_success_rate"],
                                tichu_success_rate=p["tichu_success_rate"],
                                tichu_suicidal_rate=p["tichu_suicidal_rate"],
                                tichu_premature_rate=p["tichu_premature_rate"],
                                games_win_rate=p["games_win_rate"],
                                avg_score_diff=p["avg_score_diff"],
                            )

                    game.rounds.append(RoundEntity(
                        game_id=r["game_id"],
                        round_index=r["round_index"],
                        players=players,
                        start_hands=[deserialize_cards(r[f"hand_cards_{player_index}"]) for player_index in range(4)],
                        num_bombs=r["num_bombs"],
                        schupf_hands=[deserialize_cards(r[f"schupf_cards_{player_index}"]) for player_index in range(4)],
                        tichu_positions=[r["tichu_pos_0"], r["tichu_pos_1"], r["tichu_pos_2"], r["tichu_pos_3"]],
                        tichu_suicidal=r["tichu_suicidal"],
                        tichu_premature=r["tichu_premature"],
                        wish_value=r["wish_value"],
                        dragon_giver=r["dragon_giver"],
                        dragon_recipient=r["dragon_recipient"],
                        gift_relative_index=r["gift_relative_index"],
                        is_phoenix_low=r["is_phoenix_low"],
                        winner_index=r["winner_index"],
                        winner_position=r["winner_position"],
                        loser_index=r["loser_index"],
                        is_double_victory=r["is_double_victory"],
                        score=(r["score_20"],r["score_31"]),
                        score_diff=r["score_diff"],
                        history=deserialize_history(r["history"]),
                        error_code=r["error_code"],
                        error_context=r["error_context"],
                        # Aggregierte Daten
                        num_tricks=r["num_tricks"],
                        num_turns=r["num_turns"],
                    ))

                # Daten der Partie ausliefern
                yield game
        finally:
            self.close()
    
    def count(self):
        """
        Zählt die in der DB gespeicherten fehlerfreien Partien.
        """
        self.open()
        cursor = self.cursor()
        try:
            cursor.execute("SELECT count(*) FROM games WHERE error_code = 0")
            row = cursor.fetchone()
            total = row[0] if row else 0
        finally:
            self.close()
        return total

    def _create_tables(self):
        """
        Erstellt die Tabellen in der SQLite-Datenbank, falls sie nicht existieren.
        """
        self.open()
        cursor = self.cursor()

        # Tabelle für Partien

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id                          INTEGER PRIMARY KEY AUTOINCREMENT,
                log_year                    INTEGER NOT NULL,   -- Jahr der Logdatei
                log_month                   INTEGER NOT NULL,   -- Monat der Logdatei
                player_changed              BOOLEAN NOT NULL,   -- True, wenn mindestens ein Spieler wechselt
                error_code                  INTEGER NOT NULL,   -- Fehlercode der Partie (0 == kein Fehler)
                -- Aggregierte Daten                  
                total_score_20              INTEGER,            -- Endergebnis Team 20
                total_score_31              INTEGER,            -- Endergebnis Team 31
                num_rounds                  INTEGER,            -- Anzahl der gespielten Runden
                avg_tricks_per_round        REAL,               -- Durchschnittliche Anzahl Stiche pro Runde
                avg_turns_per_round         REAL                -- Durchschnittliche Anzahl Spielzüge pro Runde
            );
        """)

        # Tabelle für Runden

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rounds (
                id                          INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id                     INTEGER NOT NULL,   -- ID der Partie
                round_index                 INTEGER NOT NULL,   -- Index der Runde innerhalb der Partie (0, 1, 2, ...)
                hand_cards_0                TEXT    NOT NULL,   -- Handkarten von Spieler 0 vor dem Schupfen (ohne Leerzeichen) 
                hand_cards_1                TEXT    NOT NULL,   -- Handkarten von Spieler 1 vor dem Schupfen (ohne Leerzeichen)
                hand_cards_2                TEXT    NOT NULL,   -- Handkarten von Spieler 2 vor dem Schupfen (ohne Leerzeichen)
                hand_cards_3                TEXT    NOT NULL,   -- Handkarten von Spieler 3 vor dem Schupfen (ohne Leerzeichen)
                num_bombs                   INTEGER NOT NULL,   -- Anzahl der Bombenblätter nach dem Schupfen
                schupf_cards_0              TEXT    NOT NULL,   -- Abgegebene Tauschkarten von Spieler 0 (ohne Leerzeichen)
                schupf_cards_1              TEXT    NOT NULL,   -- Abgegebene Tauschkarten von Spieler 1 (ohne Leerzeichen)
                schupf_cards_2              TEXT    NOT NULL,   -- Abgegebene Tauschkarten von Spieler 2 (ohne Leerzeichen)
                schupf_cards_3              TEXT    NOT NULL,   -- Abgegebene Tauschkarten von Spieler 3 (ohne Leerzeichen)
                tichu_pos_0                 INTEGER NOT NULL,   -- Tichu-Ansage-Position Spieler 0 (-3…-1, ≥0 = Zug-Index)
                tichu_pos_1                 INTEGER NOT NULL,   -- Tichu-Ansage-Position Spieler 1
                tichu_pos_2                 INTEGER NOT NULL,   -- Tichu-Ansage-Position Spieler 2
                tichu_pos_3                 INTEGER NOT NULL,   -- Tichu-Ansage-Position Spieler 3
                tichu_suicidal              INTEGER NOT NULL,   -- 1 == ein Spieler hat Tichu angesagt, obwohl ein Mitspieler fertig war, 0 == sonst
                tichu_premature             INTEGER NOT NULL,   -- 1 == ein Spieler hat Tichu angesagt, ohne direkt danach Karten auszuspielen, 0 == sonst
                wish_value                  INTEGER NOT NULL,   -- Gewünschter Kartenwert (2–14, -1 = kein Mahjong gespielt, 0 = ohne Wunsch)
                dragon_giver                INTEGER NOT NULL,   -- Index des Spielers, der den Drachen verschenkte (-1 == Drache wurde nicht verschenkt)
                dragon_recipient            INTEGER NOT NULL,   -- Index des Spielers, der den Drachen bekam (-1 == Drache wurde nicht verschenkt)
                gift_relative_index         INTEGER NOT NULL,   -- Wahl des Spielers, der den Drachen verschenkt (1 == rechter Gegner, 3 == linker Gegner, -1 = keine Wahl)
                is_phoenix_low              INTEGER NOT NULL,   -- 1 == Der Phönix mimt in der mehrdeutigen Kombination den niedrigeren Rang, 0 == Phönix mimt den höheren Rang (sofern er gespielt wird)
                winner_index                INTEGER NOT NULL,   -- Index des Spielers, der als Erster ausspielt (-1 = niemand)
                winner_position             INTEGER NOT NULL,   -- Position in der Historie, wo der erste Spieler fertig wurde
                loser_index                 INTEGER NOT NULL,   -- Index des Spielers, der als Letzter übrig bleibt (-1 = niemand)
                is_double_victory           INTEGER NOT NULL,   -- 1 == Doppelsieg, 0 == normales Ende
                score_20                    INTEGER NOT NULL,   -- Rundenergebnis Team 20
                score_31                    INTEGER NOT NULL,   -- Rundenergebnis Team 31
                score_diff                  INTEGER NOT NULL,   -- Punktedifferenz = Team20-Team31. Dies ist die Zielvariable des Values-Netzes
                history                     TEXT    NOT NULL,   -- Spielzüge [(Spieler, Karten, Stichnehmer), …], z.B 3:R6R3Ph|2|3:R6R3Ph;0|2;3
                error_code                  INTEGER NOT NULL,   -- Fehlercode der Runde (0 == kein Fehler)
                error_context               TEXT,               -- Betroffener Abschnitt aus der Quelle (NULL, wenn kein Fehler)
                -- Aggregierte Daten
                num_tricks                  INTEGER,            -- Anzahl der Stiche in dieser Runde
                num_turns                   INTEGER,            -- Anzahl der Spielzüge in dieser Runde
                FOREIGN KEY (game_id)       REFERENCES games(id)
            );
        """)

        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_rounds_game_id_round_index ON rounds (game_id, round_index);")

        # Tabelle für Spieler

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id                          INTEGER PRIMARY KEY AUTOINCREMENT, 
                name                        TEXT    NOT NULL,   -- Der eindeutige Name des Spielers
                -- -- Aggregierte Daten                         
                elo                         REAL,               -- Elo-Zahl des Spielers
                num_games                   INTEGER,            -- Anzahl der gespielten Partien
                num_rounds                  INTEGER,            -- Anzahl der gespielten RundenTichu an?
                grand_tichu_success_rate    REAL,               -- Wie oft gewinnt er ein großes Tichu?
                tichu_success_rate          REAL,               -- Wie oft gewinnt er ein einfaches Tichu?
                tichu_suicidal_rate         REAL,               -- Wie oft hat der Spieler Tichu angesagt, obwohl bereits ein Mitspieler fertig war?
                tichu_premature_rate        REAL,               -- Wie oft hat der Spieler Tichu angesagt, ohne direkt danach Karten auszuspielen?
                games_win_rate              REAL,               -- Wie oft gewinnt er eine Partie?
                avg_score_diff              REAL                -- Durchschnittliche Punktedifferenz einer Runde
            );
        """)

        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_players_name ON players (name);")

        # Zuordnungstabelle zw. Partien und Spieler
        # Namenskonvention: Pluralform der Tabellenname in alphabetischer Reihenfolge, mit Unterstrich getrennt
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games_players (
                id                          INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id                     INTEGER NOT NULL,
                player_id                   INTEGER NOT NULL,
                player_index                INTEGER NOT NULL,
                FOREIGN KEY (game_id)       REFERENCES games(id),
                FOREIGN KEY (player_id)     REFERENCES players(id)
            );
        """)

        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_games_players_game_id_player_index ON games_players (game_id, player_index);")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_games_players_player_id_game_id ON games_players (player_id, game_id);")

        # Tabelle für Spielerwechsel
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS swaps (
                id                          INTEGER PRIMARY KEY AUTOINCREMENT,
                round_id                    INTEGER NOT NULL,
                player_id                   INTEGER NOT NULL,
                player_index                INTEGER NOT NULL,
                old_player_id               INTEGER NOT NULL,
                FOREIGN KEY (round_id)      REFERENCES rounds(id),
                FOREIGN KEY (player_id)     REFERENCES players(id),
                FOREIGN KEY (old_player_id) REFERENCES players(id)
            );
        """)

        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_swaps_round_id_player_index ON swaps (round_id, player_index);")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_swaps_player_id_round_id ON swaps (player_id, round_id);")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_swaps_old_player_id_round_id ON swaps (old_player_id, round_id);")

        # Mapping-Tabelle für Error-Codes

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                code                        INTEGER PRIMARY KEY,
                name                        TEXT NOT NULL,
                description                 TEXT NOT NULL
            );
        """)

        self._create_error_codes()

        self.commit()

    def _create_error_codes(self):
        """
        Füllt die Mapping-Tabelle mit Fehlercodes.
        """
        descriptions = {
            0: "Kein Fehler",
            10: "Unbekanntes Kartenlabel",
            11: "Anzahl der Karten ist fehlerhaft",
            12: "Karten mehrmals vorhanden",
            13: "Karte gehört nicht zu den Handkarten",
            14: "Karte bereits gespielt",
            20: "Passen nicht möglich",
            21: "Wunsch nicht beachtet",
            22: "Kombination nicht spielbar",
            23: "Der Spieler ist nicht am Zug",
            24: "Es fehlen Einträge in der Historie",
            25: "Karten ausgespielt, obwohl die Runde vorbei ist (wurde korrigiert)",
            30: "Drache hat den Stich nicht gewonnen, wurde aber nicht verschenkt",
            31: "Drache an eigenes Team verschenkt",
            32: "Drache verschenkt, aber niemand hat durch den Drachen ein Stich gewonnen",
            40: "Wunsch geäußert, aber kein Mahjong gespielt",
            50: "Tichu-Ansage an der geloggten Position nicht möglich (wurde korrigiert)",
            60: "Rechenfehler! Geloggtes Rundenergebnis ist nicht möglich (wurde korrigiert)",
            61: "Geloggtes Rundenergebnis stimmt nicht mit dem berechneten Ergebnis überein (wurde korrigiert)",
            70: "Partie nicht zu Ende gespielt",
            71: "Ein oder mehrere Runden gespielt, obwohl die Partie bereits entschieden war",
            80: "Mindestens eine Runde ist fehlerhaft",
        }
        cursor = self.cursor()
        for code in ETLErrorCode:
            cursor.execute("SELECT code FROM errors WHERE code = ?", (code.value,))
            result = cursor.fetchone()
            if result:
                cursor.execute("UPDATE errors SET name=?, description=? WHERE code = ?", (code.name, descriptions[code.value], code.value))
            else:
                cursor.execute("INSERT INTO errors (code, name, description) VALUES (?, ?, ?)", (code.value, code.name, descriptions[code.value]))

    def create_indexes(self):
        """
        Erstellt Indizes für die Tabellen in der SQLite-Datenbank zur Beschleunigung typischer Abfragen.
        """
        self.open()
        cursor = self.cursor()

        # games
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_log_year_log_month   ON games (log_year, log_month);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_error_code           ON games (error_code);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_num_rounds           ON games (num_rounds);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_avg_tricks_per_round ON games (avg_tricks_per_round);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_avg_turns_per_round  ON games (avg_turns_per_round);")

        # rounds
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_num_bombs           ON rounds (num_bombs);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_tichu_pos_0         ON rounds (tichu_pos_0);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_tichu_pos_1         ON rounds (tichu_pos_1);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_tichu_pos_2         ON rounds (tichu_pos_2);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_tichu_pos_3         ON rounds (tichu_pos_3);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_tichu_suicidal      ON rounds (tichu_suicidal);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_tichu_premature     ON rounds (tichu_premature);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_wish_value          ON rounds (wish_value);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_gift_relative_index ON rounds (gift_relative_index);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_is_phoenix_low      ON rounds (is_phoenix_low);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_double_victory      ON rounds (is_double_victory);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_score_diff          ON rounds (score_diff);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_error_code          ON rounds (error_code);")

        # players
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_elo                ON players (elo);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_num_games          ON players (num_games);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_num_rounds         ON players (num_rounds);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_grand_tichu_success_rate ON players (grand_tichu_success_rate);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_tichu_success_rate ON players (tichu_success_rate);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_tichu_suicidal_rate ON players (tichu_suicidal_rate);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_tichu_premature_rate ON players (tichu_premature_rate);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_games_win_rate     ON players (games_win_rate);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_avg_score_diff     ON players (avg_score_diff);")

        # games_players
        # keine zusätzlichen Indizes nötig

        # swaps
        # keine zusätzlichen Indizes nötig

        self.commit()

    def save_game(self, game: GameEntity) -> int:
        """
        Speichert eine Partie in der Datenbank.

        :param game: Die Daten der Partie (mutable). Die Id's werden aktualisiert.
        :return: Die ID der Partie in der Datenbank.
        """
        # Partie speichern
        self._save_game_record(game)
        
        # Runden speichern
        for r in game.rounds:
            r.game_id = game.id
            self._save_round_record(r)

        # Spieler speichern
        if len(game.players) != 4:
            raise ValueError("Es müssen 4 Spieler angegeben werden.")
        for p in game.players:
            self._save_player_record(p)

        # Zuordnung zwischen Partie und Spieler speichern
        for player_index in range(4):
            self._save_game_player_record(game.id, game.players[player_index].id, player_index)

        # Spielerwechsel speichern
        old_players = game.players
        for r in game.rounds:
            for player_index in range(4):
                p = r.players[player_index]
                if p.name == old_players[player_index].name:
                    p.id = old_players[player_index].id
                else:
                    self._save_player_record(p)
                    self._save_swap_record(r.id, p.id, player_index, old_players[player_index].id)
            old_players = r.players

        return game.id

    def _save_game_record(self, g: GameEntity) -> int:
        """
        Speichert eine Partie in der Datenbank.

        Wenn die ID > 0 ist, wird nach dem Datensatz gesucht.
        Wenn der Datensatz gefunden wurde, wird dieser aktualisiert, ansonsten hinzugefügt.

        :param g: Die Partie.
        :return: Die ID der Partie in der Datenbank.
        """
        cursor = self.cursor()
        if g.id:
            # Prüfen, ob die ID existiert oder eingefügt werden muss.
            cursor.execute("SELECT id FROM games WHERE id = ?", (g.id,))
            row = cursor.fetchone()
        else:
            row = None  # kein Unique-Key vorhanden, über den gesucht werden könnte

        # Datensatz speichern.
        if row:
            cursor.execute("""
                UPDATE games SET
                    log_year=?, log_month=?,
                    player_changed=?,
                    error_code=?
                WHERE id = ?
                """, (
                    g.year, g.month,
                    g.player_changed,
                    g.error_code.value,
                    g.id,
            )
        )
        else:
            cursor.execute("""
                INSERT INTO games (
                    id, 
                    log_year, log_month, 
                    player_changed, 
                    error_code
                )
                VALUES (?, ?, ?, ?, ?)
                """, (
                    g.id if g.id else None,
                    g.year, g.month,
                    g.player_changed,
                    g.error_code.value,
                )
            )
            if not g.id:
                g.id = cursor.lastrowid

        return g.id

    def _save_round_record(self, r: RoundEntity) -> int:
        """
        Speichert die Runde in der Datenbank.

        Wenn die ID > 0 ist, wird nach dem Datensatz gesucht. Ansonst wird versucht, den Datensatz über den Unique-Key (`game_id`, `round_index`) zu finden.
        Wenn der Datensatz gefunden wurde, wird dieser aktualisiert, ansonsten hinzugefügt.

        :param r: Die Runde.
        :return: Die ID der Runde in der Datenbank.
        """
        # Die Felder für den Unique-Key müssen befüllt sein.
        if r.game_id is None:
            raise ValueError("`r.game_id` muss gesetzt sein.")
        if r.round_index is None:
            raise ValueError("`r.round_index` muss gesetzt sein.")
        
        # Karten und Historie serialisieren
        hands_str = [serialize_cards(r.start_hands[player_index]) for player_index in range(4)]
        schupf_str = [serialize_cards(r.schupf_hands[player_index]) for player_index in range(4)]
        history_str = serialize_history(r.history)

        cursor = self.cursor()
        if r.id:
            # Prüfen, ob die ID existiert oder eingefügt werden muss.
            cursor.execute("SELECT id FROM rounds WHERE id = ?", (r.id,))
            row = cursor.fetchone()
        else:
            # Versuchen, die Datensatz-ID anhand des Unique-Keys zu ermitteln
            cursor.execute("SELECT id FROM rounds WHERE game_id = ? AND round_index = ?", (r.game_id, r.round_index))
            row = cursor.fetchone()
            if row:
                r.id = row[0]

        # Datensatz speichern
        if row:
            cursor.execute("""
                UPDATE rounds SET
                    game_id=?, round_index=?, 
                    hand_cards_0=?, hand_cards_1=?, hand_cards_2=?, hand_cards_3=?,
                    num_bombs=?,
                    schupf_cards_0=?, schupf_cards_1=?, schupf_cards_2=?, schupf_cards_3=?,
                    tichu_pos_0=?, tichu_pos_1=?, tichu_pos_2=?, tichu_pos_3=?,
                    tichu_suicidal=?, tichu_premature=?,
                    wish_value=?, 
                    dragon_giver=?, dragon_recipient=?, gift_relative_index=?, 
                    is_phoenix_low=?,
                    winner_index=?, winner_position=?, loser_index=?, 
                    is_double_victory=?, 
                    score_20=?, score_31=?, score_diff=?,
                    history=?,
                    error_code=?, error_context=?
                WHERE id = ?
                """, (
                    r.game_id, r.round_index,
                    hands_str[0], hands_str[1], hands_str[2], hands_str[3],
                    r.num_bombs,
                    schupf_str[0], schupf_str[1], schupf_str[2], schupf_str[3],
                    r.tichu_positions[0], r.tichu_positions[1], r.tichu_positions[2], r.tichu_positions[3],
                    r.tichu_suicidal, r.tichu_premature,
                    r.wish_value,
                    r.dragon_giver, r.dragon_recipient, r.gift_relative_index,
                    r.is_phoenix_low,
                    r.winner_index, r.winner_position, r.loser_index,
                    r.is_double_victory,
                    r.score[0], r.score[1], r.score_diff,
                    history_str,
                    r.error_code.value, r.error_context,
                    r.id,
                )
            )
        else:
            cursor.execute("""
                INSERT INTO rounds (
                    id, 
                    game_id, round_index, 
                    hand_cards_0, hand_cards_1, hand_cards_2, hand_cards_3,
                    num_bombs,
                    schupf_cards_0, schupf_cards_1, schupf_cards_2, schupf_cards_3,
                    tichu_pos_0, tichu_pos_1, tichu_pos_2, tichu_pos_3,
                    tichu_suicidal, tichu_premature,
                    wish_value, 
                    dragon_giver, dragon_recipient, gift_relative_index, 
                    is_phoenix_low,
                    winner_index, winner_position, loser_index, 
                    is_double_victory, 
                    score_20, score_31, score_diff, 
                    history,
                    error_code, error_context
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r.id if r.id else None,
                    r.game_id, r.round_index,
                    hands_str[0], hands_str[1], hands_str[2], hands_str[3],
                    r.num_bombs,
                    schupf_str[0], schupf_str[1], schupf_str[2], schupf_str[3],
                    r.tichu_positions[0], r.tichu_positions[1], r.tichu_positions[2], r.tichu_positions[3],
                    r.tichu_suicidal, r.tichu_premature,
                    r.wish_value,
                    r.dragon_giver, r.dragon_recipient, r.gift_relative_index,
                    r.is_phoenix_low,
                    r.winner_index, r.winner_position, r.loser_index,
                    r.is_double_victory,
                    r.score[0], r.score[1], r.score_diff,
                    history_str,
                    r.error_code.value, r.error_context,
                )
            )
            if not r.id:
                r.id = cursor.lastrowid
        
        return r.id

    def _save_player_record(self, p: PlayerEntity) -> int:
        """
        Speichert den Spieler.

        Wenn die ID > 0 ist, wird nach dem Datensatz gesucht. Ansonst wird versucht, den Datensatz über den Unique-Key (`name`) zu finden.
        Wenn der Datensatz gefunden wurde, wird dieser aktualisiert, ansonsten hinzugefügt.

        :param p: Der Spieler.
        :return: Die ID des Spielers in der Datenbank.
        """
        # Der Name für den Unique-Key muss befüllt sein.
        if p.name.strip() == "":
            raise ValueError("`p.name` muss gesetzt sein.")

        cursor = self.cursor()
        if p.id:
            # Prüfen, ob die ID existiert oder eingefügt werden muss.
            cursor.execute("SELECT id FROM players WHERE id = ?", (p.id,))
            row = cursor.fetchone()
        else:
            # Versuchen, die ID anhand des Unique-Keys zu ermitteln.
            cursor.execute("SELECT id FROM players WHERE name = ?", (p.name,))
            row = cursor.fetchone()
            if row:
                p.id = row[0]

        # Datensatz speichern.
        if row:
            cursor.execute("""
                UPDATE players SET
                    name=?
                WHERE id = ?
                """, (
                    p.name,
                    p.id
                )
            )
        else:
            cursor.execute("""
                INSERT INTO players (
                    id,  
                    name
                ) 
                VALUES (?, ?)
                """, (
                    p.id if p.id else None,
                    p.name,
                )
            )
            if not p.id:
                p.id = cursor.lastrowid

        return p.id

    def _save_game_player_record(self, game_id: int, player_id: int, player_index: int) -> id:
        """
        Speichert die Zuordnung zwischen Partie und Spieler.

        :param game_id: Die ID der Partie.
        :param player_id: Die ID des Spielers.
        :param player_index: Der Index des Spielers in dieser Partie.
        :return: Die ID der Zuordnung.
        """
        # Die Felder für den Unique-Key müssen befüllt sein.
        if not game_id:
            raise ValueError("`r.game_id` muss gesetzt sein.")
        if not player_id:
            raise ValueError("`player_id` muss gesetzt sein.")
        if player_index == -1:
            raise ValueError("`player_index` muss gesetzt sein.")

        # Versuchen, die ID anhand des Unique-Keys zu ermitteln.
        cursor = self.cursor()
        cursor.execute("SELECT id FROM games_players WHERE game_id = ? AND player_index = ?", (game_id, player_index))
        row = cursor.fetchone()
        if not row:
            cursor.execute("SELECT id FROM games_players WHERE player_id = ? AND game_id = ?", (player_id, game_id))
            row = cursor.fetchone()

        if row:
            # Zuordnung aktualisieren.
            pivot_id = row[0]
            cursor.execute("UPDATE games_players SET game_id=?, player_id=?, player_index=? WHERE id = ?", (
                game_id,
                player_id,
                player_index,
                pivot_id,
            ))
        else:
            # Zuordnung hinzufügen.
            cursor.execute("INSERT INTO games_players (game_id, player_id, player_index) VALUES (?, ?, ?)", (
                game_id,
                player_id,
                player_index,
            ))
            pivot_id = cursor.lastrowid

        return pivot_id

    def _save_swap_record(self, round_id: int, player_id: int, player_index: int, old_player_id: int) -> int:
        """
        Speichert den Spielerwechsel.

        :param round_id: Die ID der Runde.
        :param player_id: Die ID des neuen Spielers.
        :param player_index: Der Index des Spielers.
        :param old_player_id: Die ID des bisherigen Spielers.
        :return: Die ID des Eintrags.
        """
        # Die Felder für den Unique-Key müssen befüllt sein.
        if not round_id:
            raise ValueError("`r.round_id` muss gesetzt sein.")
        if not player_id:
            raise ValueError("`player_id` muss gesetzt sein.")
        if player_index == -1:
            raise ValueError("`player_index` muss gesetzt sein.")
        if not old_player_id:
            raise ValueError("`old_player_id` muss gesetzt sein.")

        # Versuchen, die ID anhand des Unique-Keys zu ermitteln.
        cursor = self.cursor()
        cursor.execute("SELECT id FROM swaps WHERE round_id = ? AND player_index = ?", (round_id, player_index))
        row = cursor.fetchone()
        if not row:
            cursor.execute("SELECT id FROM swaps WHERE player_id = ? AND round_id = ?", (player_id, round_id))
            row = cursor.fetchone()
            if not row:
                cursor.execute("SELECT id FROM swaps WHERE old_player_id = ? AND round_id = ?", (old_player_id, round_id))
                row = cursor.fetchone()

        if row:
            # Datensatz aktualisieren.
            swap_id = row[0]
            cursor.execute("UPDATE swaps SET round_id=?, player_id=?, player_index=?, old_player_id=? WHERE id = ?",(
                round_id,
                player_id,
                player_index,
                old_player_id,
                swap_id
            ))
        else:
            # Datensatz hinzufügen.
            cursor.execute("INSERT INTO swaps (round_id, player_id, player_index, old_player_id) VALUES (?, ?, ?, ?)",(
                round_id,
                player_id,
                player_index,
                old_player_id,

            ))
            swap_id = cursor.lastrowid

        return swap_id

    def update_aggregated_fields(self):
        """
        Aktualisiert die aggregierten Felder in der Datenbank.

        Hierbei wird ein Fortschrittsbalken angezeigt.
        """
        self.open()
        loop_cursor = self.cursor()
        cursor = self.cursor()
        cursor2 = self.cursor()
        try:
            # 1) Runden und Partien aktualisieren

            # Anzahl Partien
            cursor.execute("SELECT count(*) FROM games")
            row = cursor.fetchone()
            total = row[0] if row else 0

            # Partien durchlaufen...
            loop_counter = 0
            loop_cursor.execute("SELECT * FROM games ORDER BY id")
            for loop_row in tqdm(loop_cursor, total=total, unit=" Partien", desc="Aggregiere Daten für Partien"):
                game_id = loop_row[0]

                # 1.1) Die Runden der Partie aktualisieren.
                # Das "|"-Zeichen trennt die Stiche in der History. Ein ";"-Zeichen steht vor dem Stiche-Einsammler.
                cursor.execute("""
                    UPDATE rounds SET
                        num_tricks = LENGTH(history) - LENGTH(REPLACE(history, '|', '')) + 1, -- Anzahl der Stiche
                        num_turns = LENGTH(history) - LENGTH(REPLACE(history, ';', ''))  -- Anzahl der Spielzüge
                    WHERE game_id = ?""", (game_id,)
                )

                # 1.2) Die Partie aktualisieren.
                cursor.execute("SELECT SUM(score_20), SUM(score_31), count(*), SUM(num_tricks), SUM(num_turns) FROM rounds WHERE game_id = ?", (game_id,))
                row = cursor.fetchone()
                total_score_20, total_score_31, num_rounds, num_tricks, num_turns = row
                cursor.execute("""
                    UPDATE games SET
                        total_score_20=?, total_score_31=?,
                        num_rounds=?,
                        avg_tricks_per_round=?,
                        avg_turns_per_round=?
                    WHERE id = ?""", (
                        total_score_20, total_score_31,  # Endergebnis der Partie
                        num_rounds,  # Anzahl der Runden
                        num_tricks / num_rounds if num_rounds > 0 else 0.0,  # avg_tricks_per_round
                        num_turns / num_rounds if num_rounds > 0 else 0.0,  # avg_turns_per_round
                        game_id,
                    )
                )

                # Transaktion alle 1000 Partien committen
                loop_counter += 1
                if loop_counter % 1000 == 0:
                    self.commit()

            # 2) Die Spieler aktualisieren.

            # Anzahl Spieler
            cursor.execute("SELECT count(*) FROM players")
            row = cursor.fetchone()
            total = row[0] if row else 0

            # Spieler durchlaufen...
            loop_counter = 0
            loop_cursor.execute("SELECT * FROM players ORDER BY id")
            for loop_row in tqdm(loop_cursor, total=total, unit=" Spieler", desc="Aggregiere Daten für Spieler"):
                player_id = loop_row[0]

                # Alle Partien des Spielers durchlaufen.
                # Es werden nur die fehlerfreien Partien untersucht, und nur die ohne Spielerwechsel.
                num_games = 0  # Anzahl der gespielten Partien
                num_wins = 0  # Anzahl der gewonnenen Partien
                elo = 1500.0  # Elo-Zahl

                num_rounds = 0  # Anzahl der gespielten Runden.
                num_grand_tichus_success = 0  # Wie oft gewinnt er sein großes Tichu?
                num_tichus_success = 0  # Wie oft gewinnt er sein einfaches Tichu?
                num_tichus_suicidal = 0  # Wie oft hat der Spieler Tichu angesagt, obwohl bereits ein Mitspieler fertig war?
                num_tichus_premature = 0  # Wie oft hat der Spieler Tichu angesagt, ohne direkt danach Karten auszuspielen?
                sum_score_diff = 0  # Punktedifferenz über alle Runden summiert
                cursor.execute("""
                    SELECT g.id, gp.player_index, g.player_changed, g.total_score_20, g.total_score_31
                    FROM games AS g
                    INNER JOIN games_players AS gp ON g.id = gp.game_id
                    WHERE gp.player_id = ? AND g.error_code = 0 AND g.player_changed = 0
                    ORDER BY g.id
                """, (player_id,))  # nach game_id sortiert, also chronologisch (für Elo wichtig)
                for row in cursor.fetchall():
                    game_id, player_index, player_changed, total_score_20, total_score_31 = row
                    num_games += 1
                    if (player_index in [2, 0] and total_score_20 > total_score_31) or (player_index in [3, 1] and total_score_31 > total_score_20):
                        num_wins += 1

                    # alle Runden des Spielers durchlaufen...
                    # tichus_premature ist fehlerbehaftet (wird überschätzt):
                    # Wenn mehrere Spieler in der Runde Tichu angesagt haben, und einer übereifrig war, werden hier alle Spieler schlecht bewertet.
                    cursor2.execute(f"""
                        SELECT 
                            COUNT(*) AS num_rounds,
                            SUM(CASE WHEN tichu_pos_{player_index} = -2 AND winner_index = ? THEN 1 ELSE 0 END) AS num_grand_tichus_success,
                            SUM(CASE WHEN tichu_pos_{player_index} > -2 AND winner_index = ? THEN 1 ELSE 0 END) AS num_tichus_success,
                            SUM(CASE WHEN tichu_pos_{player_index} > winner_position THEN 1 ELSE 0 END) AS num_tichus_suicidal,
                            SUM(CASE WHEN tichu_pos_{player_index} >= 0 AND tichu_premature = 1 THEN 1 ELSE 0 END) AS num_tichus_premature,
                            SUM(score_diff) AS total_score_diff
                        FROM rounds
                        WHERE game_id = ?
                    """, (player_index, player_index, game_id,))
                    row2 = cursor2.fetchone()
                    num_rounds += row2[0]
                    num_grand_tichus_success += row2[1]
                    num_tichus_success += row2[2]
                    num_tichus_suicidal += row2[3]
                    num_tichus_premature += row2[4]
                    if player_index in [2, 0]:
                        sum_score_diff += row2[5]
                    else:
                        sum_score_diff -= row2[5]

                # todo Elo muss noch berechnet werden

                cursor.execute("""
                    UPDATE players SET
                        elo=?,
                        num_games=?, 
                        num_rounds=?,
                        grand_tichu_success_rate=?,
                        tichu_success_rate=?,
                        tichu_suicidal_rate=?, 
                        tichu_premature_rate=?,
                        games_win_rate=?,
                        avg_score_diff=?
                    WHERE id = ?
                    """, (
                        elo,
                        num_games,
                        num_rounds,
                        num_grand_tichus_success / num_rounds if num_rounds > 0 else 0.0,  # grand_tichu_success_rate
                        num_tichus_success / num_rounds if num_rounds > 0 else 0.0,  # tichu_success_rate
                        num_tichus_suicidal / num_rounds if num_rounds > 0 else 0.0,  # tichu_suicidal_rate
                        num_tichus_premature / num_rounds if num_rounds > 0 else 0.0,  # tichu_premature_rate
                        num_wins / num_games if num_games > 0 else 0.0,  # games_win_rate
                        sum_score_diff / num_rounds if num_rounds > 0 else 0.0,  # avg_score_diff
                        player_id,
                    )
                )

                # Transaktion alle 1000 Spieler committen
                loop_counter += 1
                if loop_counter % 1000 == 0:
                    self.commit()

        finally:
            self.commit()