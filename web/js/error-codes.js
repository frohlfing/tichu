const ErrorCodes = (() => {
    // Auskommentierte Codes werden noch nicht benutzt!)

    // Allgemeine Fehler (100-199)
    const UNKNOWN_ERROR = 100; // Ein unbekannter Fehler ist aufgetreten.
    const INVALID_MESSAGE = 101; // Ungültiges Nachrichtenformat empfangen.
    const UNKNOWN_CARD = 102; // Mindestens eine Karte ist unbekannt.
    const NOT_HAND_CARD = 103; // Mindestens eine Karte ist unbekannt.
    //const UNAUTHORIZED = 104; // Aktion nicht autorisiert.
    //const SERVER_BUSY = 105; // Der Server ist momentan überlastet. Bitte später versuchen.
    const SERVER_DOWN = 106; // Der Server wurde heruntergefahren.
    //const MAINTENANCE_MODE = 107; // Der Server befindet sich im Wartungsmodus.

    // Verbindungs- & Session-Fehler (200-299)
    const SESSION_EXPIRED = 200; // Deine Session ist abgelaufen. Bitte neu verbinden.
    const SESSION_NOT_FOUND = 201; // Session nicht gefunden.
    //const TABLE_NOT_FOUND = 202; // Tisch nicht gefunden.
    //const TABLE_FULL = 203; // Der Tisch ist bereits voll.
    //const NAME_TAKEN = 204; // Dieser Spielername ist an diesem Tisch bereits vergeben.
    //const ALREADY_ON_TABLE = 205; // Du bist bereits an diesem Tisch.

    // Spiellogik-Fehler (300-399)
    const INVALID_ACTION = 300; // Ungültige Aktion.
    const INVALID_RESPONSE = 301; // Keine wartende Anfrage für die Antwort gefunden.
    const NOT_UNIQUE_CARDS = 302; // Mindestens zwei Karten sind identisch.
    const INVALID_COMBINATION = 303; // Die Karten bilden keine spielbare Kombination.
    //const NOT_YOUR_TURN = 304; // Du bist nicht am Zug.
    //const INTERRUPT_DENIED = 305; // Interrupt-Anfrage abgelehnt.
    const INVALID_WISH = 306; // Ungültiger Kartenwunsch.
    const INVALID_ANNOUNCE = 307; // Tichu-Ansage nicht möglich.
    const INVALID_DRAGON_RECIPIENT = 308; // Ungültige Wahl für Drachen verschenken.
    //const ACTION_TIMEOUT = 309; // Zeit für Aktion abgelaufen.
    const REQUEST_OBSOLETE = 310; // Anfrage ist veraltet.

    // Lobby-Fehler (400-499)
    //const GAME_ALREADY_STARTED = 400; // Das Spiel an diesem Tisch hat bereits begonnen.
    //const NOT_LOBBY_HOST = 401; // Nur der Host kann diese Aktion ausführen.

    return {
        // Allgemeine Fehler (100-199)
        UNKNOWN_ERROR,
        INVALID_MESSAGE,
        UNKNOWN_CARD,
        NOT_HAND_CARD,
        //UNAUTHORIZED,
        //SERVER_BUSY,
        SERVER_DOWN,
        //MAINTENANCE_MODE,

        // Verbindungs- & Session-Fehler (200-299)
        SESSION_EXPIRED,
        SESSION_NOT_FOUND,
        //TABLE_NOT_FOUND,
        //TABLE_FULL,
        //NAME_TAKEN,
        //ALREADY_ON_TABLE,

        // Spiellogik-Fehler (300-399)
        INVALID_ACTION,
        INVALID_RESPONSE,
        NOT_UNIQUE_CARDS,
        INVALID_COMBINATION,
        //NOT_YOUR_TURN,
        //INTERRUPT_DENIED,
        INVALID_WISH,
        INVALID_ANNOUNCE,
        INVALID_DRAGON_RECIPIENT,
        //ACTION_TIMEOUT,
        REQUEST_OBSOLETE,

        // Lobby-Fehler (400-499)
        //GAME_ALREADY_STARTED,
        //NOT_LOBBY_HOST,
    };
})();