"""
Verwaltet eine SQLite-Datenbank mit Protokolldaten von Tichu-Spielen.
Diese Klasse agiert als Data Access Layer und Mapper zwischen den logischen
Entitäten (GameEntity, etc.) und dem normalisierten Datenbankschema.
"""

__all__ = "deserialize_cards", "deserialize_history", \
    "update_elo", "get_k_factor", \
    "ETLErrorCode", "get_error_descriptions", \
    "TichuDatabase", "GameEntity", "RoundEntity", "PlayerRoundEntity", "PlayerEntity",

import enum
import inspect
import os
import re
import sqlite3
from dataclasses import dataclass, field

from traitlets import Union

from src.lib.cards import Cards, parse_card, stringify_card
from tqdm import tqdm
from typing import List, Tuple, Generator, Optional, Dict, Iterable


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


def update_elo(elo_values: List[float], k_factors: List[float], winner_team: int) -> Tuple[float, float, float, float]:
    """
    Aktualisiert die Spielstärke der Tichu-Spieler nach einer Elo‑basierenden Berechnung.

    Grundformel zur Aktualisierung der Elo-Zahl:
        Eigene aktualisierte Elo-Zahl = r_own + k * (s - e)
        k: K‑Faktor
        s: Tatsächliches Ergebnis der Partie
        e: Erwartetes Ergebnis der Partie = 1 / (1 + 10^((r_opp - r_own) / 400.0))
        r_own: Eigene bisherige Elo-Zahl
        r_opp: Elo-Zahl des Gegners

    :param elo_values: Bisherige Spielstärken der 4 Spieler.
    :param k_factors: Der K‑Faktor für jeden der 4 Spieler, der festlegt, wie stark sich ein Ergebnis auswirkt (niedriger Wert == Profi, hoher Wert == Anfänger).
    :param winner_team: Das Gewinner-Team (20 == Team20, 31 == Team31, 0 == Unentschieden, -1 == Partie nicht beendet).
    :return: Neue Spielstärken der 4 Spieler
    """
    if len(elo_values) != 4:
        raise ValueError("Die Anzahl der Elo-Zahlen muss 4 sein.")
    if len(k_factors) != 4:
        raise ValueError("Die Anzahl der k-Faktoren muss 4 sein.")
    r20 = (elo_values[2] + elo_values[0]) / 2.0  # Mittelwert der Ratings von Team 20
    r31 = (elo_values[3] + elo_values[1]) / 2.0  # Mittelwert der Ratings von Team 31
    e20 = 1.0 / (1.0 + 10 ** ((r31 - r20) / 400.0))  # erwartete Gewinnwahrscheinlichkeit für Team 20 (zw. 0.0 und 1.0)
    s20 = 1.0 if winner_team == 20 else 0.0 if winner_team == 31 else 0.5  # tatsächlicher Gewinn für Team 20 (1 == Sieg, 0.5 == Unentschieden, 0 == Niederlage)
    diff20 = s20 - e20  # Abweichung für Team 10
    diff31 = -diff20  # Abweichung für Team 31
    return (elo_values[0] + k_factors[0] * diff20,
            elo_values[1] + k_factors[1] * diff31,
            elo_values[2] + k_factors[2] * diff20,
            elo_values[3] + k_factors[3] * diff31)


def get_k_factor(num_games: int, max_elo: float) -> float:
    """
    Bestimmt den K-Faktor basierend auf der Anzahl der gespielten Partien.

    :param num_games: Anzahl der gespielten Partien.
    :param max_elo: Die höchste Elo-Zahl, die der Spieler erreicht hat.
    :return: Der K-Faktor.
    """
    # Im Schach hat k im Regelfall den Wert 40, 20 oder 10:
    # k = 40: für Spieler, die neu in der Ratingliste sind und weniger als 30 Partien aufweisen.
    # k = 20: für alle Spieler mit mindestens dreißig gewerteten Partien und einer maximalen Elo-Zahl < 2400. Dieser k-Wert trifft für die meisten Spieler zu.
    # k = 10: für alle Top-Spieler, die eine Elo-Zahl ≥ 2400 erreicht haben, selbst wenn die Elo-Zahl wieder unter diesen Wert fällt.
    # Quelle: https://de.wikipedia.org/wiki/Elo-Zahl
    if num_games < 30:
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
    """Drache verschenkt, aber niemand hat durch den Drachen ein Stich gewonnen."""

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


def get_error_descriptions() -> Dict[int, str]:
    """
    Liest die Attribute und zugehörigen Kommentare von ETLErrorCode aus.

    :return: Ein Dictionary mit Error-Code und Beschreibung.
    """
    descriptions = {}
    source = inspect.getsource(ETLErrorCode)
    for item in ETLErrorCode:
        pattern = re.compile(rf'^\s*{item.name}\s*=\s*\d+\s*$\s*\n\s*"""\s*(.*?)\s*"""', re.MULTILINE)
        match = pattern.search(source)
        descriptions[item.value] = " ".join(match.group(1).strip().split()) if match else ""
        #print(f"{item.value}: {descriptions[item.value]}")
    return descriptions


@dataclass
class PlayerEntity:
    """
    Entität für einen Spieler.

    :ivar id: ID des Spielers.
    :ivar name: Der eindeutige Name des Spielers.
    :ivar elo: Die Elo-Zahl (Spielstärke) des Spielers.
    :ivar num_games: Anzahl der gespielten Partien.
    :ivar win_rate: Wie oft gewann er eine Partie?
    :ivar num_rounds: Anzahl der gespielten Runden.
    :ivar avg_score_diff: Durchschnittliche Punktedifferenz einer Runde.
    :ivar num_grand_tichus: Wie oft hat eir ein großes Tichu angesagt?
    :ivar grand_tichu_success_rate: Wie oft gewann er ein großes Tichu?
    :ivar num_tichus: Wie oft hat eir ein einfaches Tichu angesagt?
    :ivar tichu_success_rate: Wie oft gewann er ein einfaches Tichu?
    :ivar tichu_suicidal_rate: Wie oft hat der Spieler Tichu angesagt, obwohl bereits ein Mitspieler fertig war?
    :ivar tichu_premature_rate: Wie oft hat der Spieler Tichu angesagt, ohne direkt danach Karten auszuspielen?
    """
    id: int = 0  # wird beim Speichern generiert, wenn 0
    name: str = ""
    elo: Optional[float] = None  # wird durch den Aufruf von update_elo() aktualisiert
    # Aggregierte Daten (werden durch den Aufruf von update_patient_stats aktualisiert):
    num_games: Optional[int] = None
    win_rate: Optional[float] = None
    num_rounds: Optional[int] = None
    avg_score_diff: Optional[float] = None
    num_grand_tichus: Optional[int] = None
    grand_tichu_success_rate: Optional[float] = None
    num_tichus: Optional[int] = None
    tichu_success_rate: Optional[float] = None
    tichu_suicidal_rate: Optional[float] = None
    tichu_premature_rate: Optional[float] = None


@dataclass
class PlayerRoundEntity:
    """
    Entität für eine Zuordnung zwischen Spieler und Runde.

    :ivar id: Die ID der Zuordnung.
    :ivar round_id: ID der Runde.
    :ivar player_index: Der Index des Spielers innerhalb der Runde.
    :ivar player: Die Daten des Spielers.
    :ivar start_cards: Handkarten des Spielers vor dem Schupfen (zuerst die 8 Grand-Tichu-Karten, danach die restlichen).
    :ivar schupf_cards: Abgegebene Tauschkarten (an rechten Gegner, Partner, linken Gegner).
    :ivar has_bomb: Gibt an, ob der Spieler nach dem Schupfen mindestens eine Bombe auf der Hand hat.
    :ivar tichu_position: Position in der Historie, an der der Spieler Tichu ansagt (-3 == kein Tichu, -2 == großes Tichu, -1 == Ansage vor oder während des Schupfens).
    :ivar is_tichu_suicidal: Gibt an, ob der Spieler Tichu ansagt, obwohl ein Mitspieler fertig ist.
    :ivar is_tichu_premature: Gibt an, ob der Spieler Tichu ansagt, ohne direkt danach Karten auszuspielen.
    """
    id: int = 0  # wird beim Speichern generiert, wenn 0
    round_id: int = 0  # wird beim Speichern generiert, wenn 0
    player_index: int = -1  # wird beim Speichern gesetzt
    player: PlayerEntity = field(default_factory=lambda: PlayerEntity())
    start_cards: Cards = field(default_factory=list)
    schupf_cards: Cards = field(default_factory=list)
    has_bomb: bool = False
    tichu_position: int = -3
    is_tichu_suicidal: bool = False  # wird beim Speichern berechnet
    is_tichu_premature: bool = False  # wird beim Speichern berechnet


@dataclass
class RoundEntity:
    """
    Entität für eine Runde.

    :ivar id: ID der Runde.
    :ivar game_id: ID der Partie.
    :ivar round_index: Index der Runde innerhalb der Partie.
    :ivar players: Die 4 Spieler dieser Runde.
    :ivar score_cum: Rundenergebnis (Team20, Team31) zu Beginn der Runde.
    :ivar wish_value: Der gewünschte Kartenwert (2 bis 14, -1 == kein Mahjong gespielt, 0 == ohne Wunsch).
    :ivar dragon_giver: Index des Spielers, der den Drachen verschenkt (-1 == Drache wird nicht verschenkt).
    :ivar dragon_recipient: Index des Spielers, der den Drachen bekommt (-1 == Drache wird nicht verschenkt).
    :ivar gift_relative_index: Wahl des Spielers, der den Drachen verschenkt (1 == rechte Gegner, 3 == linke Gegner, -1 == keine Wahl).
    :ivar is_phoenix_low: Gibt an, ob der Phönix in einer mehrdeutigen Kombination den niedrigeren Rang mimt.
    :ivar winner_index: Index des Spielers, der zuerst in der aktuellen Runde fertig wird (-1 == kein Spieler).
    :ivar winner_position: Position in der Historie, wo der erste Spieler fertig wird.
    :ivar loser_index: Index des Spielers, der in der aktuellen Runde als letztes übrig bleibt (-1 == kein Spieler).
    :ivar is_double_victory: Gibt an, ob die Runde durch einen Doppelsieg beendet wird.
    :ivar score: Rundenergebnis (Team20, Team31).
    :ivar score_diff: Punktedifferenz = Team20-Team31. Dies ist die Zielvariable des Values-Netzes.
    :ivar history: Spielzüge. Jeder Spielzug ist ein Tuple: Spieler-Index + Karten + Spieler-Index, der den Stich nach dem Zug kassiert (-1 == Stich nicht kassiert).
    :ivar error_code: ETL-Fehlercode.
    :ivar error_context: Im Fehlerfall der betroffene Abschnitt aus der Quelle, sonst None.
    """
    id: int = 0  # wird beim Speichern generiert, wenn 0
    game_id: int = 0  # wird beim Speichern generiert, wenn 0
    round_index: int = -1  # wird beim Speichern gesetzt
    players: List[PlayerRoundEntity] = field(default_factory=lambda: [PlayerRoundEntity(), PlayerRoundEntity(), PlayerRoundEntity(), PlayerRoundEntity()])
    score_cum: Tuple[int, int] = (0, 0)  # wird beim Speichern ermittelt
    wish_value: int = -1
    dragon_giver: int = -1
    dragon_recipient: int = -1
    gift_relative_index: int = -1  # wird beim Speichern ermittelt
    is_phoenix_low: bool = False
    winner_index: int = -1
    winner_position: int = -1
    loser_index: int = -1
    is_double_victory: bool = False
    score: Tuple[int, int] = (0, 0)
    score_diff: int = 0  # wird beim Speichern berechnet
    history: List[Tuple[int, Cards, int]] = field(default_factory=list)
    error_code: ETLErrorCode = ETLErrorCode.NO_ERROR
    error_context: Optional[str] = None

@dataclass
class GameEntity:
    """
    Entität für eine Partie.

    :ivar id: ID der Partie.
    :ivar rounds: Liste der Rundendaten dieser Partie.
    :ivar player_changed: True, wenn mindestens ein Spieler während der Partie wechselt.
    :ivar year: Jahr der Logdatei.
    :ivar month: Monat der Logdatei.
    :ivar error_code: ETL-Fehlercode (0 == kein Fehler).
    :ivar total_score: Endergebnis (Team20, Team31).
    :ivar winner_team: Das Gewinner-Team (20 == Team20, 31 == Team31, 0 == Unentschieden, -1 == Partie nicht beendet).
    :ivar num_rounds: Anzahl der gespielten Runden in dieser Partie.
    :ivar avg_tricks_per_round: Durchschnittliche Anzahl Stiche pro Runde.
    :ivar avg_turns_per_round: Durchschnittliche Anzahl Spielzüge pro Runde.
    """
    id: int = 0  # wird beim Speichern generiert, wenn 0
    rounds: List[RoundEntity] = field(default_factory=list)
    player_changed: bool = False  # wird beim Speichern ermittelt
    year: int = -1
    month: int = -1
    error_code: ETLErrorCode = ETLErrorCode.NO_ERROR
    # Aggregierte Daten (werden beim Speichern berechnet)
    total_score: Tuple[int, int] = (0, 0)
    winner_team: int = -1
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
            self.create_tables()

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
                game = GameEntity(
                    id=g["id"],
                    player_changed=g["player_changed"],
                    year=g["log_year"],
                    month=g["log_month"],
                    error_code=g["error_code"],
                    total_score=g["total_score"],
                    winner_team=g["winner_team"],
                    num_rounds=g["num_rounds"],
                    avg_tricks_per_round=g["avg_tricks_per_round"],
                    avg_turns_per_round=g["avg_turns_per_round"],
                )
                
                # ALle Runden der Partie abfragen
                round_cursor.execute("SELECT * FROM rounds WHERE game_id = ? ORDER BY id")
                for r in round_cursor:
                    round_entity = RoundEntity(
                        id=r["id"],
                        game_id=r["game_id"],
                        round_index=r["round_index"],
                        score_cum=(r["score_cum_20"], r["score_cum_31"]),
                        wish_value=r["wish_value"],
                        dragon_giver=r["dragon_giver"],
                        dragon_recipient=r["dragon_recipient"],
                        gift_relative_index=r["gift_relative_index"],
                        is_phoenix_low=r["is_phoenix_low"],
                        winner_index=r["winner_index"],
                        winner_position=r["winner_position"],
                        loser_index=r["loser_index"],
                        is_double_victory=r["is_double_victory"],
                        score=(r["score_20"], r["score_31"]),
                        score_diff=r["score_diff"],
                        history=deserialize_history(r["history"]),
                        error_code=r["error_code"],
                        error_context=r["error_context"],
                    )
                    game.rounds.append(round_entity)
                    
                    # Die Spieler der Runde abfragen
                    player_cursor.execute("""
                        SELECT pr.*, p.name AS player_name, p.elo, 
                            p.num_games, p.win_rate, 
                            p.num_rounds, p.avg_score_diff,
                            p.num_grand_tichus, p.grand_tichu_success_rate, 
                            p.num_tichus, p.tichu_success_rate, 
                            p.tichu_suicidal_rate, p.tichu_premature_rate
                        FROM players_rounds AS pr
                        INNER JOIN players AS p ON pr.player_id = p.id
                        WHERE pr.round_id = ?
                        ORDER BY pr.player_index
                    """, (r["id"],))
                    for p in player_cursor:
                        round_entity.players.append(PlayerRoundEntity(
                            id=p["id"],
                            round_id=r["round_id"],
                            player_index=p["player_index"],
                            player=PlayerEntity(
                                id=p["player_id"],
                                name=p["player_name"],
                                elo=p["elo"],
                                num_games=p["num_games"],
                                win_rate=p["win_rate"],
                                num_rounds=p["num_rounds"],
                                avg_score_diff=p["avg_score_diff"],
                                num_grand_tichus=p["num_grand_tichus"],
                                grand_tichu_success_rate=p["grand_tichu_success_rate"],
                                num_tichus=p["num_tichus"],
                                tichu_success_rate=p["tichu_success_rate"],
                                tichu_suicidal_rate=p["tichu_suicidal_rate"],
                                tichu_premature_rate=p["tichu_premature_rate"],
                            ),
                            start_cards=p["start_cards"],
                            schupf_cards=p["schupf_cards"],
                            has_bomb=p["has_bomb"],
                            tichu_position=p["tichu_postion"],
                            is_tichu_suicidal=p["is_tichu_suicidal"],
                            is_tichu_premature=p["is_tichu_premature"],
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

    def create_tables(self):
        """
        Erstellt die Tabellen in der SQLite-Datenbank, falls sie nicht existieren.
        """
        self.open()
        cursor = self.cursor()

        # Tabelle für Spieler

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id                          INTEGER PRIMARY KEY AUTOINCREMENT, 
                name                        TEXT    NOT NULL,   -- Der eindeutige Name des Spielers
                elo                         REAL,               -- Elo-Zahl des Spielers
                -- Aggregierte Daten                         
                num_games                   INTEGER,            -- Anzahl der gespielten Partien
                win_rate              REAL,               -- Wie oft gewann er eine Partie?
                num_rounds                  INTEGER,            -- Anzahl der gespielten Runden
                avg_score_diff              REAL,               -- Durchschnittliche Punktedifferenz einer Runde
                num_grand_tichus            INTEGER,            -- Wie oft hat eir ein großes Tichu angesagt?
                grand_tichu_success_rate    REAL,               -- Wie oft gewann er ein großes Tichu?
                num_tichus                  INTEGER,            -- Wie oft hat er ein einfaches Tichu angesagt?
                tichu_success_rate          REAL,               -- Wie oft gewann er ein einfaches Tichu?
                tichu_suicidal_rate         REAL,               -- Wie oft hat der Spieler Tichu angesagt, obwohl bereits ein Mitspieler fertig war?
                tichu_premature_rate        REAL                -- Wie oft hat der Spieler Tichu angesagt, ohne direkt danach Karten auszuspielen?
            );
        """)

        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_players_name ON players (name);")

        # Zuordnungstabelle zwischen Spielern und Runden
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players_rounds (
                id                          INTEGER PRIMARY KEY AUTOINCREMENT,
                round_id                    INTEGER NOT NULL,   -- ID der Runde
                player_index                INTEGER NOT NULL,   -- Index des Spielers innerhalb der Runde (0, 1, 2, 3)
                player_id                   INTEGER NOT NULL,   -- ID des Spielers
                start_cards                 TEXT    NOT NULL,   -- Handkarten vor dem Schupfen (ohne Leerzeichen) 
                schupf_cards                TEXT    NOT NULL,   -- Abgegebene Tauschkarten (ohne Leerzeichen)
                has_bomb                    INTEGER NOT NULL,   -- 1 == Bombenblatt, 0 == keine Bombe auf der Hand
                tichu_position              INTEGER NOT NULL,   -- Tichu-Ansage-Position in der History (-3 == kein Tichu, -2 == großes Tichu, -1 == während des Schupfens)
                is_tichu_suicidal           INTEGER NOT NULL,   -- 1 == Tichu angesagt, obwohl ein Mitspieler fertig war, 0 == sonst
                is_tichu_premature          INTEGER NOT NULL,   -- 1 == Tichu angesagt, ohne direkt danach Karten auszuspielen, 0 == sonst
                FOREIGN KEY (round_id)      REFERENCES rounds(id),
                FOREIGN KEY (player_id)     REFERENCES players(id)
            );
        """)

        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_players_rounds_round_id_player_index ON players_rounds (round_id, player_index);")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_players_rounds_player_id_round_id ON players_rounds (player_id, round_id);")

        # Tabelle für Runden

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rounds (
                id                          INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id                     INTEGER NOT NULL,   -- ID der Partie
                round_index                 INTEGER NOT NULL,   -- Index der Runde innerhalb der Partie (0, 1, 2, ...)
                score_cum_20                INTEGER NOT NULL,   -- Rundenergebnis Team 20 zu Beginn der Runde
                score_cum_31                INTEGER NOT NULL,   -- Rundenergebnis Team 31 zu Beginn der Runde
                wish_value                  INTEGER NOT NULL,   -- Gewünschter Kartenwert (2–14, -1 = kein Mahjong gespielt, 0 = ohne Wunsch)
                dragon_giver                INTEGER NOT NULL,   -- Index des Spielers, der den Drachen verschenkt (-1 == Drache wurde nicht verschenkt)
                dragon_recipient            INTEGER NOT NULL,   -- Index des Spielers, der den Drachen bekommt (-1 == Drache wurde nicht verschenkt)
                gift_relative_index         INTEGER NOT NULL,   -- Wahl des Spielers, der den Drachen verschenkt (1 == rechter Gegner, 3 == linker Gegner, -1 = keine Wahl)
                is_phoenix_low              INTEGER NOT NULL,   -- 1 == Der Phönix mimt in der mehrdeutigen Kombination den niedrigeren Rang, 0 == Phönix mimt den höheren Rang (sofern er gespielt wird)
                winner_index                INTEGER NOT NULL,   -- Index des Spielers, der als Erster ausspielt (-1 = niemand)
                winner_position             INTEGER NOT NULL,   -- Position in der Historie, wo der erste Spieler fertig wird
                loser_index                 INTEGER NOT NULL,   -- Index des Spielers, der als Letzter übrig bleibt (-1 = niemand)
                is_double_victory           INTEGER NOT NULL,   -- 1 == Doppelsieg, 0 == normales Ende
                score_20                    INTEGER NOT NULL,   -- Rundenergebnis Team 20
                score_31                    INTEGER NOT NULL,   -- Rundenergebnis Team 31
                score_diff                  INTEGER NOT NULL,   -- Punktedifferenz = Team20-Team31. Dies ist die Zielvariable des Values-Netzes
                history                     TEXT    NOT NULL,   -- Spielzüge [(Spieler, Karten, Stichnehmer), …], z.B 3:R6R3Ph|2|3:R6R3Ph;0|2;3
                error_code                  INTEGER NOT NULL,   -- Fehlercode der Runde (0 == kein Fehler)
                error_context               TEXT,               -- Betroffener Abschnitt aus der Quelle (NULL, wenn kein Fehler)
                FOREIGN KEY (game_id)       REFERENCES games(id)
            );
        """)

        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_rounds_game_id_round_index ON rounds (game_id, round_index);")

        # Tabelle für Partien

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id                          INTEGER PRIMARY KEY AUTOINCREMENT,
                player_changed              BOOLEAN NOT NULL,   -- True, wenn mindestens ein Spieler wechselt
                log_year                    INTEGER NOT NULL,   -- Jahr der Logdatei
                log_month                   INTEGER NOT NULL,   -- Monat der Logdatei
                error_code                  INTEGER NOT NULL,   -- Fehlercode der Partie (0 == kein Fehler)
                -- Aggregierte Daten                  
                total_score_20              INTEGER NOT NULL,   -- Endergebnis Team 20
                total_score_31              INTEGER NOT NULL,   -- Endergebnis Team 31
                winner_team                 INTEGER NOT NULL,   -- Gewinner-Team (20 == Team 20, 31 == Team 31, 0 == Unentschieden, -1 == Partie nicht beendet) 
                num_rounds                  INTEGER NOT NULL,   -- Anzahl der gespielten Runden
                avg_tricks_per_round        REAL NOT NULL,      -- Durchschnittliche Anzahl Stiche pro Runde
                avg_turns_per_round         REAL NOT NULL       -- Durchschnittliche Anzahl Spielzüge pro Runde
            );
        """)

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
        descriptions = get_error_descriptions()
        cursor = self.cursor()
        for code in ETLErrorCode:
            cursor.execute("SELECT code FROM errors WHERE code = ?", (code.value,))
            result = cursor.fetchone()
            if result:
                cursor.execute("UPDATE errors SET name=?, description=? WHERE code = ?", (code.name, descriptions[code], code.value))
            else:
                cursor.execute("INSERT INTO errors (code, name, description) VALUES (?, ?, ?)", (code.value, code.name, descriptions[code]))

    def create_indexes(self):
        """
        Erstellt Indizes für die Tabellen in der SQLite-Datenbank zur Beschleunigung typischer Abfragen.
        """
        self.open()
        cursor = self.cursor()

        # players
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_elo ON players (elo);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_num_games ON players (num_games);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_win_rate ON players (win_rate);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_num_rounds ON players (num_rounds);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_avg_score_diff ON players (avg_score_diff);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_grand_tichu_success_rate ON players (grand_tichu_success_rate);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_tichu_success_rate ON players (tichu_success_rate);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_tichu_suicidal_rate ON players (tichu_suicidal_rate);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_tichu_premature_rate ON players (tichu_premature_rate);")

        # players_rounds
        # cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_rounds_has__bomb ON players_rounds (has_bomb);")
        # cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_rounds_tichu_position ON players_rounds (tichu_position);")
        # cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_rounds_is_tichu_suicidal ON players_rounds (is_tichu_suicidal);")
        # cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_rounds_is_tichu_premature ON players_rounds (is_tichu_premature);")

        # rounds
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_wish_value ON rounds (wish_value);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_gift_relative_index ON rounds (gift_relative_index);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_is_phoenix_low ON rounds (is_phoenix_low);")
        #cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_double_victory ON rounds (is_double_victory);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_score_diff ON rounds (score_diff);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_error_code ON rounds (error_code);")

        # games
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_log_year_log_month ON games (log_year, log_month);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_error_code ON games (error_code);")
        #cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_num_rounds ON games (num_rounds);")
        #cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_avg_tricks_per_round ON games (avg_tricks_per_round);")
        #cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_avg_turns_per_round ON games (avg_turns_per_round);")

        self.commit()

    def save_game(self, game: GameEntity) -> int:
        """
        Speichert eine Partie in der Datenbank.

        :param game: Die Daten der Partie (mutable). Die Id's werden aktualisiert.
        :return: Die ID der Partie in der Datenbank.
        """
        if len (game.rounds) == 0:
            raise ValueError(f"Die Partie {game.id} hat keine Runden.")

        # Spieler dieser Partie speichern
        players: List[PlayerEntity] = []
        for round_index, r in enumerate(game.rounds):  # alle Runden durchlaufen...
            if len(r.players) != 4:
                raise ValueError(f"Die Runde {r.id} hat keine 4 Spieler.")
            for player_index, pr in enumerate(r.players):  # alle Spieler dieser Runde durchlaufen...
                if round_index == 0:
                    # initiale Runde
                    self._save_player_record(pr.player)
                    players.append(pr.player)
                elif pr.player.name != players[player_index].name:
                    # es gab einen Spielerwechsel
                    self._save_player_record(pr.player)
                    players[player_index] = pr.player
                    game.player_changed = True
                else:
                    # derselbe Spieler wie in der Vorrunde
                    pr.player.id = players[player_index].id

        # Kumulative Scores berechnen
        score_cum = 0, 0
        for r in game.rounds:
            r.score_cum = score_cum
            score_cum = score_cum[0] + r.score[0], score_cum[1] + r.score[1]

        # Endergebnis übernehmen
        game.total_score = score_cum

        #  Gewinner-Team ermitteln
        if game.total_score[0] >= 1000 or game.total_score[1] >= 1000:
            game.winner_team = 20 if game.total_score[0] > game.total_score[1] else 31 if game.total_score[0] < game.total_score[1] else 0
        else:
            game.winner_team = -1

        # Fehlercode für die Partie bestimmen
        if game.total_score[0] < 1000 and game.total_score[1] < 1000:
            game.error_code = ETLErrorCode.GAME_NOT_FINISHED
        elif any(r.score_cum[0] >= 1000 or r.score_cum[1] >= 1000 for r in game.rounds):
            game.error_code = ETLErrorCode.GAME_OVERPLAYED
        elif any(r.error_code != ETLErrorCode.NO_ERROR for r in game.rounds):
            game.error_code = ETLErrorCode.ROUND_FAILED

        # Weitere Analyse-Daten aggregieren
        game.num_rounds = len(game.rounds)
        game.avg_tricks_per_round = sum(sum(1 for turn in r.history if turn[2] != -1) for r in game.rounds) / game.num_rounds if game.num_rounds > 0 else 0.0
        game.avg_turns_per_round = sum(len(r.history) for r in game.rounds) / game.num_rounds if game.num_rounds > 0 else 0.0

        # Partie speichern
        self._save_game_record(game)
        
        # Runden dieser Partie speichern
        for round_index, r in enumerate(game.rounds):
            r.game_id = game.id
            r.round_index = round_index
            r.gift_relative_index = (r.dragon_recipient - r.dragon_giver + 4) % 4
            r.score_diff = r.score[0] - r.score[1]
            self._save_round_record(r)

        # Zuordnungen zwischen Spielern und Runden speichern
        for round_index, r in enumerate(game.rounds):  # alle Runden durchlaufen...
            for player_index, pr in enumerate(r.players):  # alle Spieler dieser Runde durchlaufen...
                pr.round_id = r.id
                pr.player_index = player_index

                # Flags, ob jemand ein dummes Tichu angesagt hat
                if pr.tichu_position >= 0:
                    pr.is_tichu_suicidal = pr.tichu_position > r.winner_position >= 0
                    turn_player_index, turn_cards, _ = r.history[pr.tichu_position]
                    pr.is_tichu_premature = turn_player_index != player_index or not turn_cards
                else:
                    pr.is_tichu_suicidal = False
                    pr.is_tichu_premature = False

                self._save_players_rounds_record(pr)

        return game.id

    def _save_game_record(self, g: GameEntity) -> int:
        """
        Speichert eine Partie in der Datenbank.

        Wenn die ID > 0 ist, wird nach dem Datensatz dieser ID gesucht.
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
                    player_changed=?,
                    log_year=?, log_month=?,
                    error_code=?,
                    total_score_20=?, total_score_31=?, winner_team=?,
                    num_rounds=?,
                    avg_tricks_per_round=?,
                    avg_turns_per_round=?
                WHERE id = ?
                """, (
                    g.player_changed,
                    g.year, g.month,
                    g.error_code.value,
                    g.total_score[0], g.total_score[1], g.winner_team,
                    g.num_rounds,
                    g.avg_tricks_per_round,
                    g.avg_turns_per_round,
                    g.id,
            )
        )
        else:
            cursor.execute("""
                INSERT INTO games (
                    id, 
                    player_changed, 
                    log_year, log_month, 
                    error_code,
                    total_score_20, total_score_31, winner_team,
                    num_rounds,
                    avg_tricks_per_round,
                    avg_turns_per_round
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    g.id if g.id else None,
                    g.player_changed,
                    g.year, g.month,
                    g.error_code.value,
                    g.total_score[0], g.total_score[1], g.winner_team,
                    g.num_rounds,
                    g.avg_tricks_per_round,
                    g.avg_turns_per_round,
                )
            )
            if not g.id:
                g.id = cursor.lastrowid

        return g.id

    def _save_round_record(self, r: RoundEntity) -> int:
        """
        Speichert die Runde in der Datenbank.

        Wenn die ID > 0 ist, wird nach dem Datensatz dieser ID gesucht.
        Ansonst wird versucht, den Datensatz über den Unique-Key (`game_id`, `round_index`) zu finden.
        Wenn der Datensatz gefunden wurde, wird dieser aktualisiert, ansonsten hinzugefügt.

        :param r: Die Runde.
        :return: Die ID der Runde in der Datenbank.
        """
        # Die Felder für den Unique-Key müssen befüllt sein.
        if r.game_id is None:
            raise ValueError("`r.game_id` muss gesetzt sein.")
        if r.round_index is None:
            raise ValueError("`r.round_index` muss gesetzt sein.")
        
        # Historie serialisieren
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
                    score_cum_20=?, score_cum_31=?,
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
                    r.score_cum[0], r.score_cum[1],
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
                    score_cum_20, score_cum_31,
                    wish_value, 
                    dragon_giver, dragon_recipient, gift_relative_index, 
                    is_phoenix_low,
                    winner_index, winner_position, loser_index, 
                    is_double_victory, 
                    score_20, score_31, score_diff, 
                    history,
                    error_code, error_context
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r.id if r.id else None,
                    r.game_id, r.round_index,
                    r.score_cum[0], r.score_cum[1],
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

        Wenn die ID > 0 ist, wird nach dem Datensatz dieser ID gesucht.
        Ansonst wird versucht, den Datensatz über den Unique-Key (`name`) zu finden.
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

    def _save_players_rounds_record(self, pr: PlayerRoundEntity) -> id:
        """
        Speichert die Zuordnung zwischen Spieler und Runde.

         Wenn die ID > 0 ist, wird nach dem Datensatz dieser ID gesucht.
         Ansonst wird versucht, den Datensatz über die Unique-Keys (`round_id`, `player_index`) und (`player_id`, `round_id`)  zu finden.
         Wenn der Datensatz gefunden wurde, wird dieser aktualisiert, ansonsten hinzugefügt.

        :param pr: Die Zuordnung.
        :return: Die ID der Zuordnung.
        """
        # Die Felder für den Unique-Key müssen befüllt sein.
        if not pr.round_id:
            raise ValueError("`pr.round_id` muss gesetzt sein.")
        if pr.player_index == -1:
            raise ValueError("`pr.player_index` muss gesetzt sein.")
        if not pr.player.id:
            raise ValueError("`pr.player.id` muss gesetzt sein.")

        # Karten serialisieren
        start_cards_str = serialize_cards(pr.start_cards)
        schupf_cards_str = serialize_cards(pr.schupf_cards)

        cursor = self.cursor()
        if pr.id:
            # Prüfen, ob die ID existiert oder eingefügt werden muss.
            cursor.execute("SELECT id FROM players_rounds WHERE id = ?", (pr.id,))
            row = cursor.fetchone()
        else:
            # Versuchen, die ID anhand des Unique-Keys zu ermitteln.
            cursor.execute("SELECT id FROM players_rounds WHERE round_id = ? AND player_index = ?", (pr.round_id, pr.player_index))
            row = cursor.fetchone()
            if not row:
                cursor.execute("SELECT id FROM players_rounds WHERE player_id = ? AND round_id = ?", (pr.player.id, pr.round_id))
                row = cursor.fetchone()
            if row:
                pr.id = row[0]

        # Datensatz speichern
        if row:
            cursor.execute("""
                UPDATE players_rounds SET
                    round_id=?, player_index=?,
                    player_id=?, 
                    start_cards=?, 
                    schupf_cards=?,
                    has_bomb=?, 
                    tichu_position=?, 
                    is_tichu_suicidal=?, 
                    is_tichu_premature=?
                WHERE id = ?
                """, (
                    pr.round_id, pr.player_index,
                    pr.player.id,
                    start_cards_str,
                    schupf_cards_str,
                    pr.has_bomb,
                    pr.tichu_position,
                    pr.is_tichu_suicidal,
                    pr.is_tichu_premature,
                    pr.id,
                )
            )
        else:
            cursor.execute("""
                INSERT INTO players_rounds (
                    id, 
                    round_id, player_index, 
                    player_id,
                    start_cards, 
                    schupf_cards,
                    has_bomb,
                    tichu_position, 
                    is_tichu_suicidal, 
                    is_tichu_premature
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pr.id if pr.id else None,
                    pr.round_id, pr.player_index,
                    pr.player.id,
                    start_cards_str,
                    schupf_cards_str,
                    pr.has_bomb,
                    pr.tichu_position,
                    pr.is_tichu_suicidal,
                    pr.is_tichu_premature,
                )
            )
            if not pr.id:
                pr.id = cursor.lastrowid

        return pr.id

    def update_patient_stats(self):
        """
        Aktualisiert die aggregierten Felder der Spieler.

        Es werden nur die fehlerfreien Partien berücksichtigt, und nur die ohne Spielerwechsel.
        Hierbei wird ein Fortschrittsbalken angezeigt.
        """
        self.open()
        loop_cursor = self.cursor()
        cursor = self.cursor()
        try:
            # Anzahl Spieler ermitteln
            cursor.execute("SELECT count(*) FROM players")
            row = cursor.fetchone()
            total = row[0] if row else 0

            # Spieler durchlaufen...
            loop_counter = 0
            loop_cursor.execute("SELECT id FROM players ORDER BY id")
            for loop_row in tqdm(loop_cursor, total=total, unit=" Spieler", desc="Aggregiere Daten für Spieler"):
                player_id = loop_row[0]

                elo = 1500.0  # Elo-Zahl   # todo Elo muss noch berechnet werden

                # Werte ermitteln
                cursor.execute("""
                    SELECT
                        COUNT(DISTINCT g.id) AS num_games,
                        SUM(CASE WHEN (pr.player_index in (0, 2) AND g.total_score_20 > g.total_score_31) OR (pr.player_index in (1, 3) AND g.total_score_20 < g.total_score_31) THEN 1 ELSE 0 END) AS num_wins,
                        SUM(CASE WHEN (pr.player_index in (0, 2) AND g.winner_team = 20) OR (pr.player_index in (1, 3) AND g.winner_team = 31) THEN 1 ELSE 0 END) AS num_wins,
                        COUNT(DISTINCT r.id) AS num_rounds,
                        SUM(CASE WHEN pr.player_index in (0, 2) THEN r.score_diff ELSE -r.score_diff END) AS sum_score_diff,
                        SUM(CASE WHEN pr.tichu_position = -2 THEN 1 ELSE 0 END) AS num_grand_tichus,
                        SUM(CASE WHEN pr.tichu_position = -2 AND r.winner_index = pr.player_index THEN 1 ELSE 0 END) AS num_grand_tichus_success,
                        SUM(CASE WHEN pr.tichu_position > -2 THEN 1 ELSE 0 END) AS num_tichus,
                        SUM(CASE WHEN pr.tichu_position > -2 AND r.winner_index = pr.player_index THEN 1 ELSE 0 END) AS num_tichus_success,
                        SUM(pr.is_tichu_suicidal) AS num_tichus_suicidal,
                        SUM(pr.is_tichu_premature) AS num_tichus_premature
                    FROM games AS g
                    INNER JOIN rounds AS r ON g.id = r.game_id
                    INNER JOIN players_rounds AS pr ON r.id = pr.round_id
                    INNER JOIN players AS p ON pr.player_id = p.id
                    WHERE p.id = ? AND g.error_code = 0 AND g.player_changed = 0
                    ORDER BY r.id
                    """, (player_id,))
                row = cursor.fetchone()
                num_games = row["num_games"]
                win_rate = row["num_wins"] / num_games if num_games > 0 else 0.0
                num_rounds = row["num_rounds"]
                avg_score_diff = row["sum_score_diff"] / num_rounds if num_rounds > 0 else 0.0
                num_grand_tichus = row["num_grand_tichus"] if num_rounds > 0 else 0  #  ist None ohne Runden
                grand_tichu_success_rate = row["num_grand_tichus_success"] / num_grand_tichus if num_grand_tichus > 0 else 0.0
                num_tichus = row["num_tichus"] if num_rounds > 0 else 0  #  ist None ohne Runden
                tichu_success_rate = row["num_tichus_success"] / num_tichus if num_tichus > 0 else 0.0
                tichu_suicidal_rate = row["num_tichus_suicidal"] / num_tichus if num_tichus > 0 else 0.0
                tichu_premature_rate = row["num_tichus_premature"] / num_tichus if num_tichus > 0 else 0.0

                # Werte speichern
                cursor.execute("""
                    UPDATE players SET
                        elo=?,
                        num_games=?, 
                        win_rate=?,
                        num_rounds=?,
                        avg_score_diff=?,
                        num_grand_tichus=?,
                        grand_tichu_success_rate=?,
                        num_tichus=?,                        
                        tichu_success_rate=?,
                        tichu_suicidal_rate=?, 
                        tichu_premature_rate=?
                    WHERE id = ?
                    """, (
                        elo,
                        num_games,
                        win_rate,
                        num_rounds,
                        avg_score_diff,
                        num_grand_tichus,
                        grand_tichu_success_rate,
                        num_tichus,
                        tichu_success_rate,
                        tichu_suicidal_rate,
                        tichu_premature_rate,
                        player_id,
                    )
                )

                # Transaktion alle 1000 Spieler committen
                loop_counter += 1
                if loop_counter % 1000 == 0:
                    self.commit()

        finally:
            self.commit()


    # def update_patient_elo(self):
    #     """
    #     Aktualisiert die Elo-Zahl der Spieler.
    #
    #     Es werden nur die fehlerfreien Partien berücksichtigt, und nur die ohne Spielerwechsel.
    #     Hierbei wird ein Fortschrittsbalken angezeigt.
    #     """
    #     self.open()
    #     loop_cursor = self.cursor()
    #     player_cursor = self.cursor()
    #     cursor = self.cursor()
    #     try:
    #         # Anzahl Partien ermitteln
    #         cursor.execute("SELECT count(*) FROM games WHERE error_code = 0 AND player_changed = 0")
    #         row = cursor.fetchone()
    #         total = row[0] if row else 0
    #
    #         # Partien durchlaufen...
    #         loop_counter = 0
    #         loop_cursor.execute("SELECT id, total_score_20, total_score_31 FROM games WHERE error_code = 0 AND player_changed = 0 ORDER BY id")
    #         for loop_row in tqdm(loop_cursor, total=total, unit=" Spieler", desc="Aggregiere Daten für Spieler"):
    #             game_id = loop_row["id"]
    #             total_score = loop_row["total_score_20"], loop_row["total_score_31"]
    #
    #             # Werte ermitteln
    #             player_cursor.execute("""
    #                 SELECT pr.player_index, pr.player_id, p.elo
    #                 FROM players AS p
    #                 INNER JOIN players_rounds AS pr ON p.id = pr.player_id
    #                 INNER JOIN rounds AS r ON pr.round_id = r.id
    #                 WHERE r.game_id = ? AND r.round_index = 0
    #                 ORDER BY pr.player_index
    #                 """, (game_id,))
    #             for p in cursor.fetchall():
    #                 # todo elo berechnen
    #                 elo = 1500.0
    #
    #             # Werte speichern
    #             cursor.execute("""
    #                 UPDATE players SET
    #                     elo=?,
    #                 WHERE id = ?
    #                 """, (
    #                     elo,
    #                     p["player_id"],
    #                 )
    #             )
    #
    #             # Transaktion alle 1000 Spieler committen
    #             loop_counter += 1
    #             if loop_counter % 1000 == 0:
    #                 self.commit()
    #
    #     finally:
    #         self.commit()

    def clone(self, database: str):
        """
        Übernimmt alle Daten der gegebenen DB.

        :param database: SQLite-Datenbankdatei.
        """
        cursor = self.cursor()
        cursor.execute(f"ATTACH DATABASE '{database}' AS db")
        for table in ["players", "games", "rounds", "players_rounds"]:
            cursor.execute(f"INSERT INTO {table} SELECT * FROM db.{table}")
        self.commit()
        cursor.execute("DETACH DATABASE db")