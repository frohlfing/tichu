import sqlite3

def insert_or_replace():
    # Test-Datenbank in-memory, damit nichts gespeichert wird
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Tabelle anlegen mit PRIMARY KEY
    cursor.execute("""
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    """)

    # Normaler INSERT – erzeugt neue ID
    cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("Alice",))
    print("Nach erstem Insert:", cursor.lastrowid)  # z.B. 1

    # INSERT OR REPLACE mit gleicher ID → ersetzt bestehenden Datensatz
    cursor.execute("INSERT OR REPLACE INTO test_table (id, name) VALUES (?, ?)", (cursor.lastrowid, "Bob"))
    print("Nach Replace mit gleicher ID:", cursor.lastrowid)  # gleiche ID

    # INSERT OR REPLACE mit neuer ID → erzeugt neuen Datensatz
    cursor.execute("INSERT OR REPLACE INTO test_table (id, name) VALUES (?, ?)", (999, "Charlie"))
    print("Nach Replace mit neuer ID:", cursor.lastrowid)  # z.B. 999

    # Alle Zeilen anzeigen
    cursor.execute("SELECT * FROM test_table")
    rows = cursor.fetchall()
    print("Inhalt der Tabelle:", rows)

    conn.close()

# Funktion ausführen
insert_or_replace()
