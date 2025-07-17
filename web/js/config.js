/**
 * Konfigurationsvariablen.
 *
 * Dieses Modul wird vom Server dynamisch generiert.
 */
const Config = {
    // Umgebung (development, production, staging)
    // Auf dem Produktiv-System können keine Tests ausgeführt werden!
    ENVIRONMENT: "development",

    // Maximale Wartezeit für Anfragen an den Client in Sekunden (0 == unbegrenzt)
    DEFAULT_REQUEST_TIMEOUT: 20,
    
    // WebSocket-URL
    WEBSOCKET_URL: 'ws://localhost:8765/ws',

    // Automatische Wiederherstellung der Verbindung, wenn diese nicht manuell beendet wurde (in ms).
    RECONNECT_DELAY: 1500,

    // Zeit für Fehler-Pop-up (in ms)
    TOAST_TIMEOUT: 3500,

    // Verzögerung des Bots (von/bis) in ms.
    BOT_DELAY: [500, 1500],

    // Anzahl Partien, die der Bot spielt (0 für unendlich)
    BOT_MAX_GAMES: 10,
};