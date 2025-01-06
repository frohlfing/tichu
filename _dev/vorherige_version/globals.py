from enum import Enum


class Action(Enum):
    # Aktionsraum des Spielers
    START = 0    # Spiel starten
    GRAND = 1    # Großes Tichu ansagen bzw. ablehnen
    TICHU = 2    # Tichu ansagen
    SCHUPF = 3   # Tauschkarten ablegen
    WISH = 4     # Karte wünschen
    GIFT = 5     # Drachen verschenken
    PLAY = 6     # Karten spielen
    PASS = 7     # passen
    BOMB = 8     # Zugrecht für Bombe anfordern


class Event(Enum):
    # Spielereignis
    ERROR = 0               # ein Fehler ist aufgetreten
    PLAYER_JOINED = 1       # ein Spieler hat sich an den Tisch gesetzt (oder ein Agent hat den Platz eingenommen)
    GAME_STARTED = 2        # die Partie wurde gestartet (ein Spieler hat auf Start geklickt)
    CARDS_DEALT = 3         # Karten wurden ausgeteilt
    PLAYER_DECLARED = 4     # ein Spieler hat ein großes Tichu angesagt bzw. abgelehnt oder ein normales Tichu angesagt
    PLAYER_SCHUPFED = 5     # ein Spieler hat Tauschkarten abgelegt
    SCHUPF_DISTRIBUTED = 6  # die Tauschkarten wurden verteilt
    CARD_WISHED = 7         # ein Kartenwert wurde sich gewünscht
    WISH_FULFILLED = 8      # der Wunsch wurde erfüllt
    DRAGON_GIVEN_AWAY = 9   # der Drache wurde verschenkt
    PLAYER_PLAYED = 10      # ein Spieler hat Karten ausgespielt
    PLAYER_PASSED = 11      # ein Spieler hat gepasst
    BOMB_PENDING = 12       # ausstehende Bombe
    PLAYER_TOOK = 13        # ein Spieler hat den Stich kassiert
    ROUND_OVER = 14         # die Runde ist beendet
    GAME_OVER = 15          # die Partie wurde beendet
