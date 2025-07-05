// noinspection JSUnusedGlobalSymbols // todo wenn nicht gebraucht, dann raus damit
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
    // Karten (Python-Port von lib/cards.py)
    // --------------------------------------------------------------------------------------

    /**
     * Kartendeck (56 Karten)
     *
     * @type {Cards}
     */
    const _deck = /** @type Cards */ [
        [0, CardSuit.SPECIAL],                                                                    // Hund
        [1, CardSuit.SPECIAL],                                                                    // Mahjong
        [2, CardSuit.SWORD], [2, CardSuit.PAGODA], [2, CardSuit.JADE], [2, CardSuit.STAR],  // 2
        [3, CardSuit.SWORD], [3, CardSuit.PAGODA], [3, CardSuit.JADE], [3, CardSuit.STAR],  // 3
        [4, CardSuit.SWORD], [4, CardSuit.PAGODA], [4, CardSuit.JADE], [4, CardSuit.STAR],  // 4
        [5, CardSuit.SWORD], [5, CardSuit.PAGODA], [5, CardSuit.JADE], [5, CardSuit.STAR],  // 5
        [6, CardSuit.SWORD], [6, CardSuit.PAGODA], [6, CardSuit.JADE], [6, CardSuit.STAR],  // 6
        [7, CardSuit.SWORD], [7, CardSuit.PAGODA], [7, CardSuit.JADE], [7, CardSuit.STAR],  // 7
        [8, CardSuit.SWORD], [8, CardSuit.PAGODA], [8, CardSuit.JADE], [8, CardSuit.STAR],  // 8
        [9, CardSuit.SWORD], [9, CardSuit.PAGODA], [9, CardSuit.JADE], [9, CardSuit.STAR],  // 9
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
    function isCardEqual(card1, card2) {
        return card1[0] === card2[0] && card1[1] === card2[1];
    }

    /**
     * Prüft, ob zwei Kartenstapel gleich sind.
     *
     * Es wird vorausgesetzt, dass beide Arrays absteigend sortiert sind.
     *
     * @param {Cards} cards1 - Der erste Kartenstapel.
     * @param {Cards} cards2 - Der zweite Kartenstapel.
     * @returns {boolean} True, wenn die Kartenstapel gleich sind, sonst false.
     */
    function isCardsEqual(cards1, cards2) {
        if (cards1.length !== cards2.length) {
            return false;
        }
        cards1 = [...cards1] // Kopie anlegen, damit die Sortierung die Parameter nicht ändert
        cards2 = [...cards2]
        sortCards(cards1)
        sortCards(cards2)
        return cards1.every((card, i) => isCardEqual(card, cards2[i]));
    }

    /**
     * Sortiert Karten absteigend.
     *
     * @param {Cards} cards Die Karten (mutable!).
     */
    function sortCards(cards) {
        cards.sort((a, b) => b[0] !== a[0] ? b[0] - a[0] : b[1] - a[1]);
    }

    /**
     * Prüft, ob eine bestimmte Karte in einem Kartenstapel enthalten ist.
     *
     * @param {Card} cardToFind - Die gesuchte Karte.
     * @param {Cards} cards - Der Kartenstapel.
     * @returns {boolean} True, wenn die Karte im Kartenstapel ist.
     */
    function includesCard(cardToFind, cards) {
        return cards.some(card => isCardEqual(card, cardToFind));
    }

    /**
     * Ermittelt, ob sich die beiden Kartenstapel überschneiden.
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
    // Kombinationen (Python-Port von lib/combinations.py)
    // --------------------------------------------------------------------------------------

    /**
     * Prüft, ob zwei Kombinationen gleich sind.
     *
     * @param {Combination} combi1 - Die erste Kombination.
     * @param {Combination} combi2 - Die zweite Kombination
     * @returns {boolean} True, wenn die Kartenstapel gleich sind.
     */
    function isCombinationEqual(combi1, combi2) {
        return combi1[0] === combi2[0] && combi1[1] === combi2[1] && combi1[2] === combi2[2];
    }

    /**
     * Ermittelt die Kombination der gegebenen Karten.
     *
     * Es wird vorausgesetzt, dass `cards` eine gültige Kombination darstellt.
     *
     * Wenn `shiftPhoenix` gesetzt ist, wird der Phönix der Kombi entsprechend eingereiht.
     *
     * @param {Cards} cards - Karten der Kombination; werden absteigend sortiert (mutable!).
     * @param {number} trickValue - Rang des aktuellen Stichs (0, wenn kein Stich ausgelegt ist).
     * @param {boolean} [shiftPhoenix] - Wenn True, wird der Phönix eingereiht.
     * @returns {Combination} Die Kombination (Typ, Länge, Rang).
     */
    function getCombination(cards, trickValue, shiftPhoenix = false) {
        const n = cards.length;
        if (n === 0) {
            return FIGURE_PASS;
        }

        // Karten absteigend sortieren
        sortCards(cards);

        // Typ ermitteln
        let /** @type CombinationType */ t;
        if (n === 1) {
            t = CombinationType.SINGLE;
        }
        else if (n === 2) {
            t = CombinationType.PAIR;
        }
        else if (n === 3) {
            t = CombinationType.TRIPLE;
        }
        else if (n === 4 && cards[1][0] === cards[2][0] && cards[2][0] === cards[3][0]) { // Treppe ausschließen: 2., 3. und 4. Karte gleichwertig
            t = CombinationType.BOMB; // 4er-Bombe
        }
        else if (n === 5 && (cards[1][0] === cards[2][0] || cards[2][0] === cards[3][0])) { // Straße ausschließen
            t = CombinationType.FULLHOUSE; // 22211 22111 *2211 *2221 *2111
        }
        else if (cards[1][0] === cards[2][0] || cards[2][0] === cards[3][0]) { // Straße ausschließen
            t = CombinationType.STAIR; // Treppe: 332211 *32211 *33211 *33221
        }
        else if (cards.every(card => card[1] === cards[0][1])) {
            t = CombinationType.BOMB; // Farbbombe
        }
        else {
            t = CombinationType.STREET;
        }

        // Rang ermitteln
        let /** @type number */ v;
        if (t === CombinationType.SINGLE) {
            if (isCardEqual(cards[0], CARD_PHO)) {
                v = trickValue ? trickValue : 1;  // ist um 0.5 größer als der Stich (wir runden ab, da egal)
            }
            else {
                v = cards[0][0];
            }
        }
        else if (t === CombinationType.FULLHOUSE) {
            v = cards[2][0]; // die 3. Karte gehört auf jeden Fall zum Drilling
        }
        else if (t === CombinationType.STREET || (t === CombinationType.BOMB && n > 4)) {
            if (isCardEqual(cards[0], CARD_PHO)) {
                if (cards[1][0] === 14) {
                    v = 14; // Phönix muss irgendwo anders eingereiht werden
                }
                else {
                    v = cards[1][0] + 1; // wir nehmen erstmal an, dass der Phönix vorn eingereiht werden kann
                    for (let i = 2; i < n; i++) {
                        if (v > cards[i][0] + i) {
                            // der Phönix füllt eine Lücke
                            v -= 1;
                            break;
                        }
                    }
                }
            }
            else {
                v = cards[0][0];
            }
        }
        else {
            v = cards[1][0];
        }

        if (shiftPhoenix && isCardEqual(cards[0], CARD_PHO)) {
            switch (t) {
                case CombinationType.PAIR: // Phönix ans Ende verschieben
                    [cards[0], cards[1]] = [cards[1], cards[0]];
                    break;

                case CombinationType.TRIPLE: // Phönix ans Ende verschieben
                    [cards[0], cards[1], cards[2]] = [cards[1], cards[2], cards[0]];
                    break;

                case CombinationType.STAIR: // Phönix in die Lücke verschieben *11233
                    for (let i = 1; i < n; i += 2) {
                        if (i + 1 >= n || cards[i][0] !== cards[i + 1][0]) {
                            // Lücke gefunden
                            const phoenix = cards.shift(); // Phönix entfernen
                            cards.splice(i, 0, phoenix); // an Position i einfügen
                            break;
                        }
                    }
                    break;

                case CombinationType.FULLHOUSE: // Phönix ans Ende des Drillings bzw. Pärchens verschieben
                    if (cards[1][0] === cards[2][0] && cards[2][0] === cards[3][0]) {  // Drilling vorne komplett -> Phönix ans Ende
                        const phoenix = cards.shift();
                        cards.push(phoenix);
                    }
                    else if (cards[2][0] === cards[3][0] && cards[3][0] === cards[4][0]) { // Drilling hinten komplett -> Phönix an die 2. Stelle
                        const phoenix = cards.shift();
                        cards.splice(1, 0, phoenix);
                    }
                    else { // Kein Drilling komplett -> Phönix in die Mitte verschieben
                        const phoenix = cards.shift();
                        cards.splice(2, 0, phoenix);
                    }
                    break;

                case CombinationType.STREET: // Phönix in die Lücke verschieben
                    // Phönix vorn annehmen
                    let w = cards[1][0] + 1; // wir nehmen erstmal an, dass der Phönix vorn bleiben kann
                    for (let i = 2; i < n; i++) {
                        if (w > cards[i][0] + i) {
                            // Lücke gefunden
                            const phoenix = cards.shift();
                            cards.splice(i - 1, 0, phoenix);
                            break;
                        }
                    }
                    if (isCardEqual(cards[0], CARD_PHO) && cards[1][0] === 14) { // keine Lücke gefunden - aber wegen Ass muss Phönix ans Ende
                        const phoenix = cards.shift();
                        cards.push(phoenix);
                    }
                    break;
            }
        }

        return /** @type Combination */ [t, n, v];
    }

    /**
     * Ermittelt die Kombinationsmöglichkeiten der Handkarten (die besten zuerst).
     *
     * @param {Cards} hand - Die Handkarten; werden absteigend sortiert (mutable!).
     * @returns {Array<[Cards, Combination]>} Kombinationsmöglichkeiten [(Karten, (Typ, Länge, Rang)), ...].
     */
    function buildCombinations(hand) {
        // Handkarten absteigend sortieren
        sortCards(hand);

        const hasPhoenix = includesCard(CARD_PHO, hand);
        const arr = [[], [], [], [], [], [], [], []]; // pro Typ ein Array
        const n = hand.length;

        // Einzelkarten, Paare, Drilling, 4er-Bomben
        for (let i1 = 0; i1 < n; i1++) {
            const card1 = hand[i1];
            arr[CombinationType.SINGLE].push([card1]);
            if (card1[1] === CardSuit.SPECIAL) {
                continue;
            }
            if (hasPhoenix) {
                arr[CombinationType.PAIR].push([card1, CARD_PHO]);
            }
            // Paare suchen...
            for (let i2 = i1 + 1; i2 < n; i2++) {
                const card2 = hand[i2];
                if (card1[0] !== card2[0]) {
                    break;
                }
                arr[CombinationType.PAIR].push([card1, card2]);
                if (hasPhoenix) {
                    arr[CombinationType.TRIPLE].push([card1, card2, CARD_PHO]);
                }
                // Drillinge suchen...
                for (let i3 = i2 + 1; i3 < n; i3++) {
                    const card3 = hand[i3];
                    if (card1[0] !== card3[0]) {
                        break;
                    }
                    arr[CombinationType.TRIPLE].push([card1, card2, card3]);
                    // 4er-Bomben suchen...
                    if (i3 + 1 < n) {
                        const card4 = hand[i3 + 1];
                        if (card1[0] === card4[0]) {
                            arr[CombinationType.BOMB].push([card1, card2, card3, card4]);
                        }
                    }
                }
            }
        }

        // Treppen
        const temp = [...arr[CombinationType.PAIR]]; // copy
        let m = temp.length;
        let i = 0;
        while (i < m) {
            const v = temp[i][temp[i].length - 2][0]; // Rang der vorletzten Karte in der Treppe
            for (const pair of arr[CombinationType.PAIR]) {
                if (includesCard(CARD_PHO, pair) && includesCard(CARD_PHO, temp[i])) {
                    continue;
                }
                if (v - 1 === pair[0][0]) {
                    const newStair = temp[i].concat(pair);
                    arr[CombinationType.STAIR].push(newStair);
                    temp.push(newStair);
                    m++;
                }
            }
            i++;
        }

        // Fullhouse
        for (const triple of arr[CombinationType.TRIPLE]) {
            for (const pair of arr[CombinationType.PAIR]) {
                if (triple[0][0] === pair[0][0]) {
                    // Ausnahmeregel: Der Drilling darf nicht vom gleichen Rang sein wie das Paar (wäre mit Phönix möglich).
                    continue;
                }
                if (isCardEqual(triple[2], CARD_PHO) && triple[0][0] < pair[0][0]) {
                    // Man würde immer den Phönix zum höherwertigen Pärchen sortieren.
                    continue;
                }
                if (!hasIntersection(triple, pair)) {
                    arr[CombinationType.FULLHOUSE].push(triple.concat(pair));
                }
            }
        }

        // Straßen
        for (let i1 = 0; i1 < n - 1; i1++) {
            if (hand[i1][1] === CardSuit.SPECIAL || (i1 > 0 && hand[i1 - 1][0] === hand[i1][0])) {
                continue; // Sonderkarte oder vorherige Karte gleichwertig
            }
            let v1 = hand[i1][0];
            if (v1 < (hasPhoenix ? 4 : 5)) {
                break; // eine Straße hat mindestens den Rang 5
            }
            let temp = [[hand[i1]]];
            for (let i2 = i1 + 1; i2 < n; i2++) {
                if (isCardEqual(hand[i2], CARD_DOG)) {
                    break; // Hund
                }
                const v2 = hand[i2][0];
                if (v1 === v2) {
                    // gleicher Kartenwert; die letzte Karte in der Straße kann ausgetauscht werden
                    const temp2 = [];
                    for (const cards of temp) {
                        const cards2 = cards.slice(0, -1).concat([hand[i2]]);
                        if (!temp2.some(c => stringifyCards(c) === stringifyCards(cards2))) { // todo geht das einfacher? if cards2 not in temp2:
                            temp2.push(cards2);
                        }
                    }
                    temp = temp.concat(temp2);
                }
                else if (v1 === v2 + 1) {
                    // keine Lücke zwischen den Karten
                    for (const cards of temp) {
                        cards.push(hand[i2]);
                    }
                    v1 = v2;
                }
                else if (v1 === v2 + 2 && hasPhoenix && !includesCard(CARD_PHO, temp[0])) {
                    // ein Phönix kann die Lücke schließen
                    for (const cards of temp) {
                        cards.push(CARD_PHO);
                        cards.push(hand[i2]);
                    }
                    v1 = v2;
                }
                else {
                    // zu große Lücke zwischen den Karten, um daraus eine Straße zu machen
                    break;
                }
            }

            const m = temp[0].length;
            for (const cards of temp) {
                for (let k = 4; k <= m; k++) {
                    if (isCardEqual(cards[k - 1], CARD_PHO)) {
                        continue;
                    }
                    const availablePhoenix = hasPhoenix && !includesCard(CARD_PHO, cards.slice(0, k));
                    // Straße bzw. Bombe übernehmen
                    if (k >= 5) {
                        let is_bomb = true;
                        for (let card of cards.slice(1, k)) {
                            if (card[1] !== cards[0][1]) {
                                is_bomb = false;
                                break;
                            }
                        }
                        arr[is_bomb ? CombinationType.BOMB : CombinationType.STREET].push(cards.slice(0, k));
                        // jede Karte ab der 2. bis zur vorletzten mit dem Phönix ersetzen
                        if (availablePhoenix) {
                            for (let i = 1; i < k - 1; i++) {
                                arr[CombinationType.STREET].push(cards.slice(0, i).concat([CARD_PHO], cards.slice(i + 1, k)));
                            }
                        }
                    }
                    // Straße mit Phönix verlängern
                    if (k >= 4 && availablePhoenix) {
                        if (cards[0][0] < 14) {
                            arr[CombinationType.STREET].push([CARD_PHO].concat(cards.slice(0, k)));
                        }
                        else if (cards[k - 1][0] > 2) {
                            arr[CombinationType.STREET].push(cards.slice(0, k).concat([CARD_PHO]));
                        }
                    }
                }
            }
        }

        // Kombinationen auflisten (zuerst die besten)
        const result = [];
        for (let t = 7; t >= 1; t--) { // Typ t = 7 (BOMB) .. 1 (SINGLE)
            for (const cards of arr[t]) {
                // Rang ermitteln
                let v;
                if (t === CombinationType.STREET && isCardEqual(cards[0], CARD_PHO)) {
                    v = cards[1][0] + 1; // Phönix == Rang der zweiten Karte + 1
                }
                else {
                    v = cards[0][0]; // Rang der ersten Karte
                }
                // Kombination speichern
                result.push([cards, [t, cards.length, v]]);
            }
        }

        return result;
    }

    /**
     * Entfernt Kombinationen, die eine der angegebenen Karten enthalten.
     *
     * @param {Array<[Cards, Combination]>} combis - Kombinationsmöglichkeiten [(Karten, (Typ, Länge, Rang)), ...].
     * @param {Cards} cards - Karten, die entfernt werden sollen.
     * @returns {Array<[Cards, Combination]>} Kombinationsmöglichkeiten ohne die gegebenen Karten.
     */
    function removeCombinations(combis, cards) {
        return combis.filter(combi => !hasIntersection(combi[0], cards));
    }

    /**
     * Ermittelt die spielbaren Kartenkombinationen aus einer Liste von Möglichkeiten.
     *
     * @param {Array<[Cards, Combination]>} combis - Kombinationsmöglichkeiten der Hand ([(Karten, (Typ, Länge, Rang)), ...]).
     * @param {Combination} trickCombination - Typ, Länge, Rang des aktuellen Stichs ((0,0,0) falls kein Stich liegt).
     * @param {number} unfulfilledWish - Unerfüllter Wunsch (0 == kein Wunsch geäußert, negativ == bereits erfüllt).
     * @returns {Array<[Cards, Combination]>} ([], (0,0,0)) für Passen sofern möglich + spielbare Kombinationsmöglichkeiten.
     */
    function buildActionSpace(combis, trickCombination, unfulfilledWish) {
        let result = [];
        if (trickCombination[2] > 0) {
            // kein Anspiel (Rang > 0; Stich liegt und es ist kein Hund)
            result.push([[], [CombinationType.PASS, 0, 0]]); // Passen ist eine Option
            const [t, n, v] = trickCombination;
            for (const combi of combis) {
                let [t2, n2, v2] = combi[1];
                if (combi[1][0] === CombinationType.SINGLE && combi[1][2] === 16) { // Phoenix als Einzelkarte
                    if (trickCombination[0] === CombinationType.SINGLE && trickCombination[2] === 15) {  // Drache
                        continue; // Phönix auf Drache ist nicht erlaubt
                    }
                    v2 = v > 0 ? v + 0.5 : 1.5;
                }
                if ((t === CombinationType.BOMB && t2 === t && (n2 > n || (n2 === n && v2 > v))) ||
                    (t !== CombinationType.BOMB && (t2 === CombinationType.BOMB || (t2 === t && n2 === n && v2 > v)))) {
                        result.push(combi);
                }
            }
        }
        else {
            // Anspiel! Freie Auswahl (bis auf passen).
            result = combis;
        }

        // Falls ein Wunsch offen ist, muss der Spieler diesen erfüllen, wenn er kann.
        if (unfulfilledWish > 0) {
            //const mandatory = result.filter(combi => isWishIn(unfulfilledWish, combi[0]));
            const mandatory = [];
            for (let combi of result ) {
                if (isWishIn(unfulfilledWish, combi[0])) {
                    mandatory.push(combi);
                }
            }
            if (mandatory.length > 0) {
                // Der Spieler kann und muss den Wunsch erfüllen.
                result = mandatory;
            }
        }

        return result;
    }

    // --------------------------------------------------------------------------------------
    // Zusätzliche Funktionen
    // --------------------------------------------------------------------------------------

    /**
     * Findet alle Bomben in einer Hand.
     *
     * @param {Cards} hand - Die Handkarten des Spielers (werden durch die Funktion absteigend sortiert - mutable!).
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
     * Findet alle Bomben, die aktuelle spielbar sind.
     *
     * @param {Cards} hand - Die Handkarten des Spielers (werden durch die Funktion absteigend sortiert - mutable!).
     * @param {Combination} trickCombination - Die auf dem Tisch liegende Kombination.
     * @returns {Array<[Cards, Combination]>} Ein Array aller spielbaren Bomben.
     */
    function getPlayableBombs(hand, trickCombination) {
        const allCombis = buildCombinations(hand);
        const bombsInHand = allCombis.filter(combi => combi[1][0] === CombinationType.BOMB);
        if (bombsInHand.length === 0) {
            return [];
        }

        // Wenn der aktuelle Stich keine Bombe ist, sind alle Bomben spielbar.
        if (trickCombination[0] !== CombinationType.BOMB) {
            return bombsInHand;
        }

        // Wenn der aktuelle Stich eine Bombe ist, nur höhere Bomben zurückgeben.
        const [_trickType, trickLength, trickRank] = trickCombination;
        return bombsInHand.filter(bombCombi => {
            const [_bombType, bombLength, bombRank] = bombCombi[1];
            return bombLength > trickLength || (bombLength === trickLength && bombRank > trickRank);
        });
    }

    // noinspection JSUnusedGlobalSymbols
    return {
        sum,
        getRelativePlayerIndex, getCanonicalPlayerIndex,
        isCardEqual, isCardsEqual, sortCards, includesCard, hasIntersection,
        parseCard, parseCards, stringifyCard, stringifyCards,
        isWishIn, sumCardPoints, otherCards,
        isCombinationEqual,
        getCombination, buildCombinations, removeCombinations, buildActionSpace,
        findBombs, getPlayableBombs,
    };
})();