/**
 * Konfigurationsvariablen.
 *
 * Diese wird vom Python-Server dynamisch generiert.
 */

/**
 * Konfigurationsvariablen
 */
const Config = {
    // Maximale Wartezeit für Anfragen an den Client in Sekunden (0 == unbegrenzt)
    DEFAULT_REQUEST_TIMEOUT: 20,
    
    // WebSocket-URL
    WEBSOCKET_URL: 'ws://localhost:8765/ws'
};


// todo raus damit
/**
 * CardValueLabels - Labels für Kartenwerte 2 bis Ass.
 */
const CardValueLabels = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];

// todo raus damit
/**
 * SpecialCardValues - Numerische Werte für Sonderkarten.
 */
const SpecialCardValues = {'MAH': 1, 'DOG': 0, 'DRA': 15, 'PHO': 16};


