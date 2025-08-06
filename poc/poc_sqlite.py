import sqlite3


def update_player(cursor: sqlite3.Cursor, player_name: str) -> int:
    cursor.execute("SELECT id FROM players WHERE name = ?", (player_name,))
    result = cursor.fetchone()
    #int(cursor.fetchone()[0])
    if result:
        player_id = result[0]
    else:
        cursor.execute("INSERT INTO players (name) VALUES (?)", (player_name,))
        player_id = cursor.lastrowid
    return player_id

def insert_or_replace():
    # Test-Datenbank in-memory, damit nichts gespeichert wird
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Tabelle anlegen mit PRIMARY KEY
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS players
    (
        id   INTEGER PRIMARY KEY AUTOINCREMENT, -- ID des Spielers
        name TEXT NOT NULL                      -- Name des Spielers
    );
    """)
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_players_name ON players (name);")
    conn.commit()

    player_id = update_player(cursor, "ALice")
    print("ID für Alice:", player_id)  # 1

    player_id = update_player(cursor, "Bob")
    print("ID für Bob:", player_id)  # 2

    player_id = update_player(cursor, "ALice")
    print("ID für Alice:", player_id)  # ID=3!!! Erwartet hätte ich 0 oder bestenfalls 1

    cursor.execute("SELECT count(*) FROM players ORDER BY id")
    total = cursor.fetchone()[0]
    print(total)

    conn.commit()

    # Alle Zeilen anzeigen
    cursor.execute("SELECT * FROM players")
    rows = cursor.fetchall()
    print("Inhalt der Tabelle:", rows)

    conn.close()

# Funktion ausführen
insert_or_replace()
