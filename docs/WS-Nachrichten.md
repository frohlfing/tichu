1. **Client-zu-Server-Nachrichten:** Diese würden Aktionen des Spielers an den Server übermitteln.
    - Beispiele basierend auf und der Spiellogik:
        - `JOIN_TABLE`: Spieler möchte einem Tisch beitreten (ggf. mit Tischnamen und Spielernamen).
        - `PLAYER_ACTION`: Eine generische Nachricht für Spieleraktionen oder spezifische Nachrichten wie:
            - `SCHUPF_CARDS`: Enthält die vom Spieler ausgewählten Karten zum Schupfen.
            - `ANNOUNCE_TICHU`: Spieler sagt Tichu oder Grand Tichu an.
            - `PLAY_CARDS`: Spieler spielt eine Kartenkombination.
            - `WISH_VALUE`: Spieler äußert einen Kartenwert-Wunsch (nach Mahjong).
            - `GIVE_DRAGON_AWAY`: Spieler bestimmt, wer den Drachenstich erhält.

        - `LEAVE_TABLE`: Spieler möchte den Tisch verlassen.

`client.py`

2. **Server-zu-Client-Nachrichten:** Diese würden den Spielzustand aktualisieren, zu Aktionen auffordern oder andere Benachrichtigungen senden.
    - Beispiele:
        - `GAME_STATE_UPDATE`: Übermittelt den aktuellen `PublicState` (wahrscheinlich im Format, das von `PublicState.to_dict()` erzeugt wird). Dies könnte nach jeder Aktion oder jedem wichtigen Ereignis gesendet werden.
        - `PRIVATE_STATE_UPDATE`: Übermittelt den `PrivateState` an den jeweiligen Spieler (Handkarten, etc.).
        - `REQUEST_ACTION`: Fordert den Spieler auf, eine bestimmte Aktion durchzuführen (z.B. "Schupfen", "Karten spielen") und könnte den `action_space` enthalten.
        - `NOTIFICATION`: Allgemeine Benachrichtigungen (z.B. "Spieler X ist beigetreten", "Runde beendet", Fehlermeldungen).
        - `ERROR_MESSAGE`: Bei ungültigen Aktionen oder anderen Fehlern.
        - `TABLE_JOINED_CONFIRMATION`: Bestätigung, dass der Spieler dem Tisch beigetreten ist, ggf. mit seiner `player_index`.
