/**
 * Fehlercodes und Konfigurationsvariablen.
 *
 * Diese wird vom Python-Server dynamisch generiert.
 */

/**
 * Enum für Fehlercodes
 */
const ErrorCode = { // Singular
    UNKNOWN_ERROR: 100,
    INVALID_MESSAGE: 101,
    UNKNOWN_CARD: 102,
    NOT_HAND_CARD: 103,
    SERVER_DOWN: 106,
    SESSION_EXPIRED: 200,
    SESSION_NOT_FOUND: 201,
    // Ungültige Aktion
    INVALID_ACTION: 300,
    INVALID_RESPONSE: 301,
    NOT_UNIQUE_CARDS: 302,
    INVALID_COMBINATION: 303,
    INVALID_WISH: 306,
    INVALID_ANNOUNCE: 307,
    INVALID_DRAGON_RECIPIENT: 308,
    REQUEST_OBSOLETE: 310
};

/**
 * Konfigurationsvariablen
 */
const Config = {
    // Maximale Wartezeit für Anfragen an den Client in Sekunden (0 == unbegrenzt)
    DEFAULT_REQUEST_TIMEOUT: 20,
    
    // WebSocket-URL
    WEBSOCKET_URL: 'ws://localhost:8765/ws'
};

/**
 * CardValueLabels - Labels für Kartenwerte 2 bis Ass.
 */
const CardValueLabels = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];

/**
 * SpecialCardValues - Numerische Werte für Sonderkarten.
 */
const SpecialCardValues = {'MAH': 1, 'DOG': 0, 'DRA': 15, 'PHO': 16};

/**
 * Numerische Werte für Kartenfarben.
 */
const CardSuits = {
    SPECIAL: 0, // Dog, Mahjong, Phoenix, Dragon
    SWORD: 1,   // Schwert/Schwarz
    PAGODA: 2,  // Pagode/Blau
    JADE: 3,    // Jade/Grün
    STAR: 4     // Stern/Rot
};
