/**
 * Enum für Fehlercodes.
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
 * Kartenfarben.
 */
const CardSuits = {
    SPECIAL: 0, // Hund, Mahjong, Phönix, Drache
    SWORD: 1,   // Schwert/Schwarz
    PAGODA: 2,  // Pagode/Blau
    JADE: 3,    // Jade/Grün
    STAR: 4     // Stern/Rot
};

// todo CardSuits hier verwenden. Auch in cards.py einführen. Grund: Farbe ist ein kategorialer Typ.
/**
 * Type-Alias für eine Karte mit Wert und Farbe.
 *
 * @typedef {[number, number]} Card
 * @property {number} 0 - Wert der Karte (0 = Hund, 1 = Mahjong, 2 bis 10, 11 = Bube, 12 = Dame, 13 = König, 14 = As, 15 = Drache, 16 = Phönix)
 * @property {number} 1 - Farbe der Karte (0 = Sonderkarte, 1 = Schwarz/Schwert, 2 = Blau/Pagode, 3 = Grün/Jade, 4 = Rot/Stern)
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
    // Karte
    // --------------------------------------------------------------------------------------

    /**
     * Kartendeck (56 Karten)
     *
     * @type {Cards}
     */
    const _deck = [
        // schwarz blau  grün    rot
        [0, 0],                              // Hund
        [1, 0],                              // Mahjong
        [2, 1], [2, 2], [2, 3], [2, 4],      // 2
        [3, 1], [3, 2], [3, 3], [3, 4],      // 3
        [4, 1], [4, 2], [4, 3], [4, 4],      // 4
        [5, 1], [5, 2], [5, 3], [5, 4],      // 5
        [6, 1], [6, 2], [6, 3], [6, 4],      // 6
        [7, 1], [7, 2], [7, 3], [7, 4],      // 7
        [8, 1], [8, 2], [8, 3], [8, 4],      // 8
        [9, 1], [9, 2], [9, 3], [9, 4],      // 9
        [10, 1], [10, 2], [10, 3], [10, 4],  // 10
        [11, 1], [11, 2], [11, 3], [11, 4],  // Bube
        [12, 1], [12, 2], [12, 3], [12, 4],  // Dame
        [13, 1], [13, 2], [13, 3], [13, 4],  // König
        [14, 1], [14, 2], [14, 3], [14, 4],  // As
        [15, 0],                             // Drache
        [16, 0]                              // Phönix
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
     * @returns {number} Der relative Index (0 = Benutzer, 1 = rechter Gegner, 2 = Partner, 3 = linker Gegner, -1 = der eigene Index ist noch nicht bekannt).
     */
    function getRelativePlayerIndex(canonicalPlayerIndex) {
        const ownPlayerIndex = State.getPlayerIndex(); // der eigene kanonische Index
        if (ownPlayerIndex === -1 || canonicalPlayerIndex === -1) {
            return -1;
        }
        return (canonicalPlayerIndex - ownPlayerIndex + 4) % 4;
    }

    /**
     * Konvertiert den aus Sicht des Benutzers relativen Index eines Spielers in den kanonischen (serverseitigen) Index.
     *
     * @param {number} relativePlayerIndex - Aus Sicht des Benutzers relativer Index (0 = Benutzer, 1 = rechter Gegner, 2 = Partner, 3 = linker Gegner).
     * @returns {number} Der kanonische Index des Spielers (0-3, oder -1, wenn der eigene Spielerindex noch nicht bekannt ist).
     */
    function getCanonicalPlayerIndex(relativePlayerIndex) {
        const ownPlayerIndex = State.getPlayerIndex(); // Holt den eigenen kanonischen Index
        if (ownPlayerIndex === -1) {
            return -1;
        }
        return (ownPlayerIndex + relativePlayerIndex) % 4;
    }

    // --------------------------------------------------------------------------------------
    // Kombination
    // --------------------------------------------------------------------------------------

    // todo

    return {
        parseCard,
        parseCards,
        stringifyCard,
        stringifyCards,
        getRelativePlayerIndex,
        getCanonicalPlayerIndex,
    };
})();