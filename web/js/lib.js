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
 * Enum für die Spielphasen des Clients.
 */
const Phase = {
    // Login-Formular wird angezeigt. Der Benutzer gibt sein Name und den gewünschten Tisch an und loggt sich ein.
    LOGIN_DIALOG: 10,
    // Die eingeloggten Spieler sind zu sehen. Der Benutzer wartet, dass das Spiel beginnt.
    LOBBY_WAIT: 11,
    // Die eingeloggten Spieler sind zu sehen. Der Benutzer ist der Host und kann die Reihenfolge der Spieler ändern (bestimmt, wer mit wem spielt).
    LOBBY_ASSIGN_TEAM: 12,

    // Eine neue Runde ist gestartet. Der Benutzer erhält 8 Handkarten (Animation läuft).
    DEALING_INITIAL_ANIMATION: 20,
    // Der Benutzer muss sich entscheiden, ob er ein großes Tichu ansagen möchte.
    DEALING_TICHU_DECISION: 21,
    // Der Benutzer hat die restlichen Karten erhalten (Animation läuft).
    DEALING_REMAINING_ANIMATION: 22,

    // Der Benutzer hat ein Tichu angesagt (Animation läuft).
    TICHU_ANIMATION: 30,

    // Der Benutzer wählt Karten zum Tauschen.
    SCHUPFING_SELECT: 40,
    // Der Benutzer hat die Tauschkarten ausgewählt (Tauschkarten wurden umgedreht).
    SCHUPFING_CONFIRMED: 41,
    // Die Tauschkarten werden getauscht (Animation läuft).
    SCHUPFING_ANIMATION: 42,
    // Der Benutzer hat die erhaltenen Tauschkarten offen vor sich und muss sie aufnehmen.
    SCHUPFING_RECEIVE: 43,

    // Karten werden ausgespielt, der Benutzer ist aber nicht am Zug.
    PLAYING_WAIT: 50,
    // Der Benutzer ist am Zug und muss Karten ausspielen (Passen nicht erlaubt wegen Anspiel oder offener Wunsch).
    PLAYING_PLAY: 51,
    // Der Benutzer muss Karten ausspielen oder passen.
    PLAYING_PLAY_OR_PASS: 52,
    // Karten werden ausgespielt (Animation läuft).
    PLAYING_ANIMATION: 53,

    // Ein Spieler hat eine Bombe angekündigt. Der Benutzer kann jetzt selbst keine Bombe werfen.
    BOMBING_WAIT: 60,
    // Der Benutzer hat eine Bombe angekündigt und muss diese jetzt auswählen.
    BOMBING_SELECT: 61,
    // Der Benutzer hat eine Bombe geworfen (Animation läuft).
    BOMBING_ANIMATION: 62,

    // Der Stich wird kassiert (Animation läuft).
    TRICK_ANIMATION: 70,

    // Der Wish-Dialog wird angezeigt. Der Benutzer muss sich ein Kartenwert wünschen.
    WISH_DIALOG: 80,
    // Der Drachen-Dialog wird angezeigt. Der Benutzer muss den Drachen verschenken.
    DRAGON_DIALOG: 81,
    // Runde ist beendet, das Rundenergebnis wird angezeigt.
    ROUND_OVER_DIALOG: 82,
    // Partie ist beendet, die Punktetabelle wird angezeigt.
    GAME_OVER_DIALOG: 83,
    // Der Exit-Dialog wird angezeigt.
    EXIT_DIALOG: 84,
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