/**
 * Enum für Fehlercodes.
 */
const ErrorCode = {
    // Ein unbekannter Fehler ist aufgetreten.
    UNKNOWN_ERROR: 100,
    // Ungültiges Nachrichtenformat empfangen.
    INVALID_MESSAGE: 101,
    // Mindestens eine Karte ist unbekannt.
    UNKNOWN_CARD: 102,
    // Mindestens eine Karte ist keine Handkarte.
    NOT_HAND_CARD: 103,
    // Server wurde heruntergefahren.
    SERVER_DOWN: 106,
    // Deine Session ist abgelaufen. Bitte neu verbinden.
    SESSION_EXPIRED: 200,
    // Session nicht gefunden.
    SESSION_NOT_FOUND: 201,
    // Ungültige Aktion
    INVALID_ACTION: 300,
    // Keine wartende Anfrage für die Antwort gefunden.
    INVALID_RESPONSE: 301,
    // Mindestens zwei Karten sind identisch.
    NOT_UNIQUE_CARDS: 302,
    // Die Karten bilden keine spielbare Kombination.
    INVALID_COMBINATION: 303,
    // Ungültiger Kartenwunsch.
    INVALID_WISH: 306,
    // Tichu-Ansage nicht möglich.
    INVALID_ANNOUNCE: 307,
    // Wahl des Spielers, der den Drachen bekommt, ist ungültig.
    INVALID_DRAGON_RECIPIENT: 308,
    // Zeit für Aktion abgelaufen.
    REQUEST_OBSOLETE: 310
};

/**
 * Kartenfarben.
 */
const CardSuit = {
    // Sonderkarte (0)
    SPECIAL: 0, 
    // Schwarz/Schwert (1)
    SWORD: 1,   
    // Blau/Pagode (2)
    PAGODA: 2,  
    // Grün/Jade (3)
    JADE: 3,    
    // Rot/Stern (4)
    STAR: 4
};

/**
 * Type-Alias für eine Karte mit Wert und Farbe.
 *
 * @typedef {[number, CardSuit]} Card
 * @property {number} 0 - Wert der Karte (0 = Hund, 1 = Mahjong, 2 bis 10, 11 = Bube, 12 = Dame, 13 = König, 14 = As, 15 = Drache, 16 = Phönix)
 * @property {CardSuit} 1 - Farbe der Karte (0 = Sonderkarte, 1 = Schwarz/Schwert, 2 = Blau/Pagode, 3 = Grün/Jade, 4 = Rot/Stern)
 */

/**
 * Type-Alias für eine Liste von Karten.
 *
 * @typedef {Card[]} Cards
 */

/**
 * Enum für Kombinationstypen.
 */
const CombinationType = {
    // Passen (0)
    PASS: 0,
    // Einzelkarte (1)
    SINGLE: 1,
    // Paar (2)
    PAIR: 2,
    // Drilling (3)
    TRIPLE: 3,
    // Treppe (4)
    STAIR: 4,
    // Fullhouse (5)
    FULLHOUSE: 5,
    // Straße (6)
    STREET: 6,
    // Vierer-Bombe oder Farbbombe (7)
    BOMB: 7
};

/**
 * Type-Alias für eine Kombination.
 *
 * @typedef {[CombinationType, number, number]} Combination
 * @property {CombinationType} 0 - Typ der Kombination.
 * @property {number} 1 - Länge der Kombination.
 * @property {number} 2 - Rang der Kombination.
 */

/**
 * Tichu-Library
 */
const Lib = (() => {

    // --------------------------------------------------------------------------------------
    // Allgemeine mathematische Funktionen
    // --------------------------------------------------------------------------------------

    /**
     * Berechnet die Summe aller Zahlen in einem Array.
     *
     * @param {number[]} arr - Das Array von Zahlen.
     * @returns {number} Die Summe der Zahlen im Array.
     */
    function sum(arr) {
        return arr.reduce((acc, num) => acc + num, 0);
    }

    // --------------------------------------------------------------------------------------
    // Karte
    // --------------------------------------------------------------------------------------

    /**
     * Kartendeck (56 Karten)
     *
     * @type {Cards}
     */
    const _deck = /** @type Cards */ [
        [0, CardSuit.SPECIAL],                                                                    // Hund
        [1, CardSuit.SPECIAL],                                                                    // Mahjong
        [2, CardSuit.SWORD],  [2, CardSuit.PAGODA],  [2, CardSuit.JADE],  [2, CardSuit.STAR],  // 2
        [3, CardSuit.SWORD],  [3, CardSuit.PAGODA],  [3, CardSuit.JADE],  [3, CardSuit.STAR],  // 3
        [4, CardSuit.SWORD],  [4, CardSuit.PAGODA],  [4, CardSuit.JADE],  [4, CardSuit.STAR],  // 4
        [5, CardSuit.SWORD],  [5, CardSuit.PAGODA],  [5, CardSuit.JADE],  [5, CardSuit.STAR],  // 5
        [6, CardSuit.SWORD],  [6, CardSuit.PAGODA],  [6, CardSuit.JADE],  [6, CardSuit.STAR],  // 6
        [7, CardSuit.SWORD],  [7, CardSuit.PAGODA],  [7, CardSuit.JADE],  [7, CardSuit.STAR],  // 7
        [8, CardSuit.SWORD],  [8, CardSuit.PAGODA],  [8, CardSuit.JADE],  [8, CardSuit.STAR],  // 8
        [9, CardSuit.SWORD],  [9, CardSuit.PAGODA],  [9, CardSuit.JADE],  [9, CardSuit.STAR],  // 9
        [10, CardSuit.SWORD], [10, CardSuit.PAGODA], [10, CardSuit.JADE], [10, CardSuit.STAR], // 10
        [11, CardSuit.SWORD], [11, CardSuit.PAGODA], [11, CardSuit.JADE], [11, CardSuit.STAR], // Bube
        [12, CardSuit.SWORD], [12, CardSuit.PAGODA], [12, CardSuit.JADE], [12, CardSuit.STAR], // Dame
        [13, CardSuit.SWORD], [13, CardSuit.PAGODA], [13, CardSuit.JADE], [13, CardSuit.STAR], // König
        [14, CardSuit.SWORD], [14, CardSuit.PAGODA], [14, CardSuit.JADE], [14, CardSuit.STAR], // As
        [15, CardSuit.SPECIAL],                                                                   // Drache
        [16, CardSuit.SPECIAL]                                                                    // Phönix
    ];

    /**
     * Kartenlabel
     *
     * @type {string[]}
     */
    const _cardLabels = [
        "Hu", "Ma",
        "S2", "B2", "G2", "R2",
        "S3", "B3", "G3", "R3",
        "S4", "B4", "G4", "R4",
        "S5", "B5", "G5", "R5",
        "S6", "B6", "G6", "R6",
        "S7", "B7", "G7", "R7",
        "S8", "B8", "G8", "R8",
        "S9", "B9", "G9", "R9",
        "SZ", "BZ", "GZ", "RZ",
        "SB", "BB", "GB", "RB",
        "SD", "BD", "GD", "RD",
        "SK", "BK", "GK", "RK",
        "SA", "BA", "GA", "RA",
        "Dr", "Ph"
    ];

    /**
     * Parst die Karte aus dem String.
     *
     * @param {string} label - Das Label der Karte, z.B. "R6".
     * @returns {Card} Die geparste Karte (mit Wert und Farbe).
     */
    function parseCard(label) {
        return _deck[_cardLabels.indexOf(label)];
    }

    /**
     * Parst die Karten aus dem String.
     *
     *
     * @param {string} label - Die Labels der Karten mit Leerzeichen getrennt, z.B. "R6 B5 G4".
     * @returns {Cards} Liste der Karten.
     */
    function parseCards(label) {
        return label ? label.split(" ").map(card => _deck[_cardLabels.indexOf(card)]) : [];
    }

    /**
     * Formatiert die Karte als lesbaren String.
     *
     * @param {Card} card - Die Karte (Wert und Farbe), z.B. [8,3].
     * @returns {string} Das Label der Karte.
     */
    function stringifyCard(card) {
        return _cardLabels[_deck.findIndex(entry => entry[0] === card[0] && entry[1] === card[1])];
    }

    /**
     * Formatiert die Karte als lesbaren String.
     *
     * @param {Cards} cards - Die Karten , z.B. [[8,3], [2,4], [0,1]].
     * @returns {string} Die Labels der Karte mit Leerzeichen getrennt.
     */
    function stringifyCards(cards) {
        return cards.map(card => stringifyCard(card)).join(" ");
    }

    /**
     * Konvertiert den kanonischen (serverseitigen) Index eines Spielers in den aus Sicht des Benutzers relativen Index.
     *
     * @param {number} canonicalPlayerIndex - Der kanonische Index des Spielers (0-3).
     * @returns {number} Der relative Index (0 = Benutzer, 1 = rechter Gegner, 2 = Partner, 3 = linker Gegner, -1 = kein Spieler).
     */
    function getRelativePlayerIndex(canonicalPlayerIndex) {
        const ownPlayerIndex = State.getPlayerIndex(); // der eigene kanonische Index
        return canonicalPlayerIndex !== -1 ? (canonicalPlayerIndex - ownPlayerIndex + 4) % 4 : -1;
    }

    /**
     * Konvertiert den aus Sicht des Benutzers relativen Index eines Spielers in den kanonischen (serverseitigen) Index.
     *
     * @param {number} relativePlayerIndex - Aus Sicht des Benutzers relativer Index (0 = Benutzer, 1 = rechter Gegner, 2 = Partner, 3 = linker Gegner, -1 = kein Spieler).
     * @returns {number} Der kanonische Index des Spielers (0-3, oder -1, wenn der eigene Spielerindex noch nicht bekannt ist).
     */
    function getCanonicalPlayerIndex(relativePlayerIndex) {
        const ownPlayerIndex = State.getPlayerIndex(); // Holt den eigenen kanonischen Index
        return relativePlayerIndex !== -1 ? (ownPlayerIndex + relativePlayerIndex) % 4 : -1;
    }

    // --------------------------------------------------------------------------------------
    // Kombination
    // --------------------------------------------------------------------------------------

    // todo

    // noinspection JSUnusedGlobalSymbols
    return {
        sum,
        parseCard,
        parseCards,
        stringifyCard,
        stringifyCards,
        getRelativePlayerIndex,
        getCanonicalPlayerIndex,
    };
})();