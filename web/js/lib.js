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
 * @typedef {Array<Card>} Cards
 */

// Sonderkarten
const CARD_DOG = /** @type Card */ [0, CardSuit.SPECIAL];
const CARD_MAH = /** @type Card */ [1, CardSuit.SPECIAL];
const CARD_DRA = /** @type Card */ [15, CardSuit.SPECIAL];
const CARD_PHO = /** @type Card */ [16, CardSuit.SPECIAL];

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

// Sonderkarten einzeln ausgespielt // todo entfernen
const FIGURE_PASS = /** @type Combination */ [CombinationType.PASS, 0, 0];
const FIGURE_DOG = /** @type Combination */ [CombinationType.SINGLE, 1, 0];
const FIGURE_MAH = /** @type Combination */ [CombinationType.SINGLE, 1, 1];
const FIGURE_DRA = /** @type Combination */ [CombinationType.SINGLE, 1, 15];
const FIGURE_PHO = /** @type Combination */ [CombinationType.SINGLE, 1, 16];

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
     * @param {Array<number>} arr - Das Array von Zahlen.
     * @returns {number} Die Summe der Zahlen im Array.
     */
    function sum(arr) {
        return arr.reduce((acc, num) => acc + num, 0);
    }

    // --------------------------------------------------------------------------------------
    // Kanonischer Index / Relativer Index
    // --------------------------------------------------------------------------------------

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
    // Karte (Python-Port)
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
     * @type {Array<string>}
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
     * Zuordnung von Kartenwert zu Punkten.
     *
     * @type {Array<number>}
     */
    const _cardPoints = [
        0,    // 0: Hund
        0,    // 1: MahJong
        0,    // 2
        0,    // 3
        0,    // 4
        5,    // 5 → 5 Punkte
        0,    // 6
        0,    // 7
        0,    // 8
        0,    // 9
        10,   // 10  → 10 Punkte
        0,    // 11: Bube
        0,    // 12: Dame
        10,   // 13: König → 10 Punkte
        0,    // 14: As
        25,   // 15: Drache → 25 Punkte
        -25   // 16: Phönix → 25 Minuspunkte
    ];

    /**
     * Prüft, ob zwei Karten gleich sind.
     *
     * @param {Card} card1
     * @param {Card} card2
     * @returns {boolean}
     */
    function areCardsEqual(card1, card2) {
        return card1[0] === card2[0] && card1[1] === card2[1];
    }

    /**
     * Prüft, ob eine Karte in einem Array von Karten enthalten ist.
     *
     * @param {Card} cardToFind - Die gesuchte Karte.
     * @param {Cards} cards - Die gegebenen Karten.
     * @returns {boolean} True, wenn die Karte unter den gegebenen ist.
     */
    function includesCard(cardToFind, cards) {
        return cards.some(card => areCardsEqual(card, cardToFind));
    }

     /**
     * Ermittelt, ob sich die beiden Karten-Arrays überschneiden.
      *
     * @param {Cards} cards1 - Das erste Karten-Array.
     * @param {Cards} cards2 - Das zweite Karten-Array.
     * @returns {boolean} - True, wenn es eine Schnittmenge gibt.
     */
    function hasIntersection(cards1, cards2) {
        for (const card1 of cards1) {
            if (includesCard(card1, cards2)) {
                return true;
            }
        }
        return false;
    }

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
     * Ermittelt, ob der gewünschte Kartenwert unter den Karten ist.
     *
     * @param {number} wish - Der gewünschte Kartenwert.
     * @param {Cards} cards - Die zu prüfenden Karten.
     * @returns {boolean} True, wenn der Kartenwert unter den Karten ist.
     */
    function isWishIn(wish, cards) {
        return cards.some(card => card[0] === wish);
    }

    /**
     * Zählt die Punkte der übergebenen Karten.
     *
     * @param {Cards} cards - Die zu zählenden Karten.
     * @returns {number} Die Summe der Punkte.
     */
    function sumCardPoints(cards) {
        if (cards.length === 0) {
            return 0;
        }
        return cards.map(card => _cardPoints[card[0]]).reduce((total, points) => total + points, 0);
    }

    /**
     * Listet die Karten auf, die nicht in der übergebenen Liste vorkommen.
     *
     * Die Reihenfolge entspricht dem Kartendeck (also aufsteigend).
     *
     * @param {Cards} cards - Die Karten, aus denen die fehlenden Karten ermittelt werden.
     * @returns {Cards} Eine Liste der Karten, die nicht in der Eingabeliste vorkommen.
     */
    function otherCards(cards) {
        if (cards.length === 0) {
            return [..._deck]; // gibt eine Kopie des gesamten Decks zurück
        }
        return _deck.filter(deckCard => !includesCard(deckCard, cards));
    }

    // --------------------------------------------------------------------------------------
    // Kombination (Python-Port)
    // --------------------------------------------------------------------------------------

    /**
     * Ermittelt die Kombination der gegebenen Karten.
     *
     * Es wird vorausgesetzt, dass `cards` eine gültige Kombination ist.
     *
     * Parameter `cards` wird absteigend sortiert (mutable Parameter).
     * Wenn `shift_phoenix` gesetzt ist, wird der Phönix der Kombi entsprechend eingereiht.
     *
     * @param {Cards} cards - Karten der Kombination.
     * @param {number} trickValue - Rang des aktuellen Stichs (0, wenn kein Stich ausgelegt ist).
     * @param {boolean} [shift_phoenix] - Wenn True, wird der Phönix eingereiht.
     * @returns {Combination} Die Kombination (Typ, Länge, Rang).
     */
    function getCombination(cards, trickValue, shift_phoenix = false) {
        const n = cards.length;
        if (n === 0) return FIGURE_PASS;

        // Karten absteigend sortieren
        cards.sort((a, b) => b[0] - a[0]);

        let t, v;

        if (n === 1) {
            t = CombinationType.SINGLE;
        } else if (n === 2) {
            t = CombinationType.PAIR;
        } else if (n === 3) {
            t = CombinationType.TRIPLE;
        } else if (n === 4 && cards[1][0] === cards[2][0] && cards[2][0] === cards[3][0]) {
            t = CombinationType.BOMB; // 4er-Bombe
        } else if (n === 5 && (cards[1][0] === cards[2][0] || cards[2][0] === cards[3][0])) {
            t = CombinationType.FULLHOUSE;
        } else if (cards.length > 1 && (cards[1][0] === cards[2][0] || (cards.length > 3 && cards[2][0] === cards[3][0]))) {
             t = CombinationType.STAIR;
        } else if (cards.every(card => card[1] === cards[0][1] && card[1] !== CardSuit.SPECIAL)) {
            t = CombinationType.BOMB; // Farbbombe
        } else {
            t = CombinationType.STREET;
        }

        // Rang ermitteln
        if (t === CombinationType.SINGLE) {
            if (areCardsEqual(cards[0], CARD_PHO)) {
                v = trickValue ? trickValue : 1; // Phoenix ist um 0.5 größer, hier gerundet
            } else {
                v = cards[0][0];
            }
        } else if (t === CombinationType.FULLHOUSE) {
            v = cards[2][0]; // Die 3. Karte gehört auf jeden Fall zum Drilling
        } else if (t === CombinationType.STREET || (t === CombinationType.BOMB && n > 4)) {
            if (areCardsEqual(cards[0], CARD_PHO)) {
                if (cards[1][0] === 14) {
                    v = 14;
                } else {
                    v = cards[1][0] + 1;
                    for (let i = 2; i < n; i++) {
                        if (v > cards[i][0] + i) {
                            v -= 1;
                            break;
                        }
                    }
                }
            } else {
                v = cards[0][0];
            }
        } else {
            v = cards.length > 1 ? cards[1][0] : cards[0][0];
        }

        if (shift_phoenix && areCardsEqual(cards[0], CARD_PHO)) {
            switch (t) {
                case CombinationType.PAIR: // Phönix ans Ende verschieben
                    [cards[0], cards[1]] = [cards[1], cards[0]];
                    break;

                case CombinationType.TRIPLE: // Phönix ans Ende verschieben
                    [cards[0], cards[1], cards[2]] = [cards[1], cards[2], cards[0]];
                    break;

                case CombinationType.STAIR: // Phönix in die Lücke verschieben
                    for (let i = 1; i < n; i += 2) {
                        if (i + 1 >= n || cards[i][0] !== cards[i + 1][0]) {
                            // Lücke gefunden. Phönix nach vorne schieben und dann an Position i einfügen.
                            const phoenix = cards.shift(); // Phönix entfernen
                            cards.splice(i, 0, phoenix); // An Position i einfügen
                            break;
                        }
                    }
                    break;

                case CombinationType.FULLHOUSE:
                    // Drilling vorne komplett -> Phönix ans Ende
                    if (cards[1][0] === cards[2][0] && cards[2][0] === cards[3][0]) {
                        const phoenix = cards.shift();
                        cards.push(phoenix);
                    }
                    // Drilling hinten komplett -> Phönix an die 2. Stelle
                    else if (cards[2][0] === cards[3][0] && cards[3][0] === cards[4][0]) {
                        const phoenix = cards.shift();
                        cards.splice(1, 0, phoenix);
                    }
                    // Kein Drilling komplett (Phönix im Drilling) -> Phönix in die Mitte
                    else {
                        const phoenix = cards.shift();
                        cards.splice(2, 0, phoenix);
                    }
                    break;

                case CombinationType.STREET:
                    let lueckeGefunden = false;
                    // Phönix vorn annehmen
                    let erwarteterWert = cards[1][0] + 1;
                    for (let i = 2; i < n; i++) {
                        if (erwarteterWert > cards[i][0] + i-1) { // i-1, weil wir bei 1 starten
                            // Lücke gefunden. Phönix nach vorne schieben und an Position i-1 einfügen.
                            const phoenix = cards.shift();
                            cards.splice(i - 1, 0, phoenix);
                            lueckeGefunden = true;
                            break;
                        }
                    }
                    // Keine Lücke, aber Ass am Anfang -> Phönix muss ans Ende
                    if (!lueckeGefunden && cards[1][0] === 14) {
                        const phoenix = cards.shift();
                        cards.push(phoenix);
                    }
                    break;
            }
        }

        return [t, n, v];
    }

    /**
     * Ermittelt die Kombinationsmöglichkeiten der Handkarten (die besten zuerst).
     *
     * @param {Cards} hand - Die Handkarten, absteigend sortiert, z.B. [(8,3),(2,4),(0,1)].
     * @returns {Array<[Cards, Combination]>} Kombinationsmöglichkeiten [(Karten, (Typ, Länge, Rang)), ...].
     */
    function buildCombinations(hand) {
        // Handkarten für die Operationen absteigend sortieren
        hand.sort((a, b) => b[0] - a[0]);

        const has_phoenix = includesCard(CARD_PHO, hand);
        const arr = [[], [], [], [], [], [], [], []]; // Index entspricht CombinationType
        const n = hand.length;

        // Einzelkarten, Paare, Drilling, 4er-Bomben
        for (let i1 = 0; i1 < n; i1++) {
            const card1 = hand[i1];
            arr[CombinationType.SINGLE].push([card1]);
            if (card1[1] === CardSuit.SPECIAL) continue;
            if (has_phoenix) {
                arr[CombinationType.PAIR].push([card1, CARD_PHO]);
            }
            for (let i2 = i1 + 1; i2 < n; i2++) {
                const card2 = hand[i2];
                if (card1[0] !== card2[0]) break;
                arr[CombinationType.PAIR].push([card1, card2]);
                if (has_phoenix) {
                    arr[CombinationType.TRIPLE].push([card1, card2, CARD_PHO]);
                }
                for (let i3 = i2 + 1; i3 < n; i3++) {
                    const card3 = hand[i3];
                    if (card1[0] !== card3[0]) break;
                    arr[CombinationType.TRIPLE].push([card1, card2, card3]);
                    for (let i4 = i3 + 1; i4 < n; i4++) {
                        const card4 = hand[i4];
                        if (card1[0] === card4[0]) {
                            arr[CombinationType.BOMB].push([card1, card2, card3, card4]);
                        }
                        break;
                    }
                }
            }
        }

        // Treppen
        const temp_stairs = [...arr[CombinationType.PAIR]];
        let m_stairs = temp_stairs.length;
        let i_stairs = 0;
        while (i_stairs < m_stairs) {
            const v = temp_stairs[i_stairs][temp_stairs[i_stairs].length - 2][0];
            for (const pair of arr[CombinationType.PAIR]) {
                if (includesCard(CARD_PHO, pair) && includesCard(CARD_PHO, temp_stairs[i_stairs])) continue;
                if (v - 1 === pair[0][0]) {
                    const newStair = temp_stairs[i_stairs].concat(pair);
                    arr[CombinationType.STAIR].push(newStair);
                    temp_stairs.push(newStair);
                    m_stairs++;
                }
            }
            i_stairs++;
        }

        // FullHouse
        for (const triple of arr[CombinationType.TRIPLE]) {
            for (const pair of arr[CombinationType.PAIR]) {
                if (triple[0][0] === pair[0][0]) continue;
                if (areCardsEqual(triple[2], CARD_PHO) && triple[0][0] < pair[0][0]) continue;
                if (!hasIntersection(triple, pair)) {
                    arr[CombinationType.FULLHOUSE].push(triple.concat(pair));
                }
            }
        }

        // Straßen
        for (let i1 = 0; i1 < n - 1; i1++) {
            if (hand[i1][1] === CardSuit.SPECIAL || (i1 > 0 && hand[i1 - 1][0] === hand[i1][0])) continue;
            let v1 = hand[i1][0];
            if (v1 < (has_phoenix ? 4 : 5)) break;

            let temp_streets = [[hand[i1]]];
            for (let i2 = i1 + 1; i2 < n; i2++) {
                if (areCardsEqual(hand[i2], CARD_DOG)) break;
                const v2 = hand[i2][0];
                if (v1 === v2) {
                    const temp2 = [];
                    for (const cards of temp_streets) {
                        const cards2 = cards.slice(0, -1).concat([hand[i2]]);
                        // Prüfen, ob cards2 schon in temp2 ist (einfache Duplikatprüfung)
                        if (!temp2.some(c => stringifyCards(c) === stringifyCards(cards2))) {
                            temp2.push(cards2);
                        }
                    }
                    temp_streets = temp_streets.concat(temp2);
                } else if (v1 === v2 + 1) {
                    for (const cards of temp_streets) {
                        cards.push(hand[i2]);
                    }
                    v1 = v2;
                } else if (v1 === v2 + 2 && has_phoenix && !includesCard(CARD_PHO, temp_streets[0])) {
                    for (const cards of temp_streets) {
                        cards.push(CARD_PHO);
                        cards.push(hand[i2]);
                    }
                    v1 = v2;
                } else {
                    break;
                }
            }

            const m_streets = temp_streets.length > 0 ? temp_streets[0].length : 0;
            for (const cards of temp_streets) {
                for (let k = 4; k <= m_streets; k++) {
                    const current_slice = cards.slice(0, k);
                    if (areCardsEqual(current_slice[k - 1], CARD_PHO)) continue;

                    const available_phoenix = has_phoenix && !includesCard(CARD_PHO, current_slice);

                    if (k >= 5) {
                        const is_bomb = current_slice.slice(1).every(card => card[1] === current_slice[0][1]);
                        arr[is_bomb ? CombinationType.BOMB : CombinationType.STREET].push(current_slice);
                        if (available_phoenix) {
                            for (let i = 1; i < k - 1; i++) {
                                arr[CombinationType.STREET].push(current_slice.slice(0, i).concat([CARD_PHO], current_slice.slice(i + 1, k)));
                            }
                        }
                    }
                    if (k >= 4 && available_phoenix) {
                        if (current_slice[0][0] < 14) {
                            arr[CombinationType.STREET].push([CARD_PHO].concat(current_slice));
                        } else if (current_slice[k - 1][0] > 2) {
                            arr[CombinationType.STREET].push(current_slice.concat([CARD_PHO]));
                        }
                    }
                }
            }
        }

        // Ergebnis formatieren: [[Karten, Kombination], ...]
        const result = [];
        for (let t = 7; t >= 1; t--) {
            for (const cards of arr[t]) {
                let v;
                if (t === CombinationType.STREET && cards.length > 0 && areCardsEqual(cards[0], CARD_PHO)) {
                    v = cards[1][0] + 1;
                } else {
                    v = cards.length > 0 ? cards[0][0] : 0;
                }
                const combination = [t, cards.length, v];
                result.push([cards, combination]);
            }
        }

        return result;
    }

    /**
     * Entfernt Kombinationen, die eine der angegebenen Karten enthalten.
     *
     * @param {Array<[Cards, Combination]>} combis - Liste der Kombinationsmöglichkeiten.
     * @param {Cards} cards_to_remove - Karten, die entfernt werden sollen.
     * @returns {Array<[Cards, Combination]>} Gefilterte Liste der Kombinationen.
     */
    function removeCombinations(combis, cards_to_remove) {
        return combis.filter(combi => !hasIntersection(combi[0], cards_to_remove));
    }

    /**
     * Ermittelt die spielbaren Kartenkombinationen aus einer Liste von Möglichkeiten.
     *
     * @param {Array<[Cards, Combination]>} combis - Alle Kombinationsmöglichkeiten der Hand.
     * @param {Combination} trick_combination - Die auf dem Tisch liegende Kombination.
     * @param {number} unfulfilled_wish - Der Wert eines unerfüllten Wunsches (oder 0).
     * @returns {Array<[Cards, Combination]>} Liste der spielbaren Aktionen.
     */
    function buildActionSpace(combis, trick_combination, unfulfilled_wish) {
        let result = [];
        const isAnspiel = areCardsEqual(trick_combination, FIGURE_PASS) || areCardsEqual(trick_combination, FIGURE_DOG);

        if (!isAnspiel) {
            result.push([[], FIGURE_PASS]); // Passen ist eine Option
            const [t, n, v] = trick_combination;

            for (const combi of combis) {
                const [cards, combi_details] = combi;
                let [t2, n2, v2] = combi_details;

                if (areCardsEqual(combi_details, FIGURE_PHO)) { // Phoenix als Einzelkarte
                    if (areCardsEqual(trick_combination, FIGURE_DRA)) continue; // Phoenix auf Drache verboten
                    v2 = v > 0 ? v + 0.5 : 1.5;
                }

                const isHigherBomb = (t === CombinationType.BOMB && t2 === t && (n2 > n || (n2 === n && v2 > v)));
                const isBombOnNormal = (t !== CombinationType.BOMB && t2 === CombinationType.BOMB);
                const isHigherNormal = (t2 === t && n2 === n && v2 > v);

                if (isHigherBomb || isBombOnNormal || isHigherNormal) {
                    result.push(combi);
                }
            }
        } else {
            result = combis; // Anspiel, alles ist erlaubt (außer Passen)
        }

        if (unfulfilled_wish > 0) {
            const mandatory = result.filter(combi => isWishIn(unfulfilled_wish, combi[0]));
            if (mandatory.length > 0) {
                // Wenn Passen möglich war und erzwungene Züge existieren, muss Passen
                // erhalten bleiben, falls der Spieler passen möchte, obwohl er erfüllen kann.
                // ACHTUNG: Die Regel besagt, der Spieler MUSS erfüllen. Passen ist keine Option,
                // wenn man erfüllen kann.
                // Wenn Anspiel ist, ist Passen sowieso nicht im `result`
                // Wenn kein Anspiel ist, ist Passen in `result`, muss aber für die
                // `mandatory`-Liste entfernt werden.
                if (!isAnspiel) {
                    // Falls der Spieler nicht erfüllen kann (mandatory leer wäre),
                    // bleibt `result` wie es ist (inklusive Passen).
                    // Da `mandatory` hier aber nicht leer ist, wird das Ergebnis
                    // auf die Züge beschränkt, die den Wunsch erfüllen.
                    return mandatory;
                } else {
                    // Bei Anspiel kann nicht gepasst werden.
                    return mandatory;
                }
            }
        }

        return result;
    }

    // --------------------------------------------------------------------------------------
    // Neue Funktionen
    // --------------------------------------------------------------------------------------

    /**
     * Prüft, ob der Spieler eine gültige Kombination (außer Passen) spielen kann.
     *
     * @param {Cards} hand - Die Handkarten des Spielers.
     * @param {Combination} trickCombination - Die auf dem Tisch liegende Kombination.
     * @param {number} unfulfilledWish - Der Wert eines unerfüllten Wunsches (oder 0).
     * @returns {boolean} - True, wenn mindestens eine spielbare Kombination existiert, sonst False.
     */
    function canPlay(hand, trickCombination, unfulfilledWish) {
        const allCombis = buildCombinations(hand);
        const actionSpace = buildActionSpace(allCombis, trickCombination, unfulfilledWish);
        
        // Wenn es ein Anspiel ist (Hund oder leerer Stich), ist `actionSpace` leer, wenn keine Karten da sind.
        // In diesem Fall wäre `canPlay` false. Wenn Karten da sind, ist actionSpace > 0.
        const isAnspiel = areCardsEqual(trickCombination, FIGURE_PASS) || areCardsEqual(trickCombination, FIGURE_DOG);
        if (isAnspiel) {
            return actionSpace.length > 0;
        }
        
        // Wenn kein Anspiel ist, enthält der `actionSpace` immer "Passen" als Option.
        // Wenn MEHR als nur "Passen" möglich ist, kann der Spieler spielen.
        return actionSpace.length > 1;
    }

    /**
     * Wählt die "beste" spielbare Kombination aus. 
     * 
     * Als "beste" gilt hier die niedrigst-mögliche Kombination, die den aktuellen Stich schlägt.
     *
     * @param {Cards} hand - Die Handkarten des Spielers.
     * @param {Combination} trickCombination - Die auf dem Tisch liegende Kombination.
     * @param {number} unfulfilledWish - Der Wert eines unerfüllten Wunsches (oder 0).
     * @returns {[Cards, Combination] | null} - Die empfohlene Kombination oder null, wenn nur Passen möglich ist.
     */
    function selectBestPlay(hand, trickCombination, unfulfilledWish) {
        const allCombis = buildCombinations(hand);
        const actionSpace = buildActionSpace(allCombis, trickCombination, unfulfilledWish);

        // Entferne die "Passen"-Option aus dem Aktionsraum, falls vorhanden.
        const playableCombinations = actionSpace.filter(
            combi => combi[1][0] !== CombinationType.PASS
        );

        if (playableCombinations.length === 0) {
            return null; // Nur Passen ist möglich
        }

        // Sortiere die spielbaren Kombinationen, um die "schwächste" zu finden.
        // Priorität:
        // 1. Keine Bombe vor einer Bombe (Bomben sind wertvoll und werden geschont).
        // 2. Niedrigster Rang.
        // 3. Kürzeste Länge (als sekundärer Tie-Breaker, selten relevant).
        playableCombinations.sort((a, b) => {
            const combiA = a[1];
            const combiB = b[1];

            const isBombA = combiA[0] === CombinationType.BOMB;
            const isBombB = combiB[0] === CombinationType.BOMB;

            // Regel 1: Bomben werden zuletzt in Betracht gezogen
            if (isBombA && !isBombB) return 1;  // a (Bombe) kommt nach b
            if (!isBombA && isBombB) return -1; // a kommt vor b (Bombe)

            // Regel 2: Sortiere nach Rang (aufsteigend)
            const rankDiff = combiA[2] - combiB[2];
            if (rankDiff !== 0) return rankDiff;

            // Regel 3: Sortiere nach Länge (aufsteigend)
            return combiA[1] - combiB[1];
        });

        // Gib die erste (schwächste) spielbare Kombination zurück
        return playableCombinations[0];
    }
    
    /**
     * Findet alle Bomben in einer Hand.
     *
     * @param {Cards} hand - Die Handkarten des Spielers.
     * @returns {Array<[Cards, Combination]>} Ein Array aller Bomben-Kombinationen, die in der Hand gefunden wurden.
     */
    function findBombs(hand) {
        if (!hand || hand.length < 4) {
            return [];
        }
        const allCombis = buildCombinations(hand);
        return allCombis.filter(combi => combi[1][0] === CombinationType.BOMB);
    }
    
    /**
     * Findet alle Bomben, die im aktuelle spielbar sind.
     *
     * @param {Cards} hand - Die Handkarten des Spielers.
     * @param {Combination} trickCombination - Die auf dem Tisch liegende Kombination.
     * @returns {Array<[Cards, Combination]>} Ein Array aller spielbaren Bomben.
     */
    function getPlayableBombs(hand, trickCombination) {
        const bombsInHand = findBombs(hand);
        if (bombsInHand.length === 0) {
            return [];
        }

        // Wenn der aktuelle Stich keine Bombe ist, sind alle Bomben spielbar.
        if (trickCombination[0] !== CombinationType.BOMB) {
            return bombsInHand;
        }

        // Wenn der aktuelle Stich eine Bombe ist, nur höhere Bomben zurückgeben.
        const [trickType, trickLength, trickRank] = trickCombination;
        return bombsInHand.filter(bombCombi => {
            const [bombType, bombLength, bombRank] = bombCombi[1];
            // Höher ist: längere Bombe ODER gleiche Länge und höherer Rang.
            return bombLength > trickLength || (bombLength === trickLength && bombRank > trickRank);
        });
    }
    
    // noinspection JSUnusedGlobalSymbols
    return {
        sum,
        getRelativePlayerIndex, getCanonicalPlayerIndex,
        areCardsEqual, includesCard, hasIntersection,
        parseCard, parseCards, stringifyCard, stringifyCards,
        isWishIn, sumCardPoints, otherCards,
        getCombination, buildCombinations, removeCombinations, buildActionSpace,
        canPlay, selectBestPlay,
        findBombs, getPlayableBombs,
    };
})();