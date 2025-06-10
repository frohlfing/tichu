/**
 * Enthält allgemeine Hilfsfunktionen für die Tichu-Anwendung.
 */
const Helpers = (() => {
    // Interne Mapping-Tabelle für die Konvertierung von [value, suit] zu Label und zurück.
    // Dies ist eine Nachbildung der Logik aus `cards.py` (`_deck` und `_cardlabels`).
    // Es ist wichtig, dass dies synchron mit dem Backend bleibt.
    const _cardDeck = [ // value, suit, label
        [ 0, 0, 'Hu'],                                              // Hund
        [ 1, 0, 'Ma'],                                              // Mahjong
        [ 2, 1, 'S2'], [ 2, 2, 'B2'], [ 2, 3, 'G2'], [ 2, 4, 'R2'], // 2
        [ 3, 1, 'S3'], [ 3, 2, 'B3'], [ 3, 3, 'G3'], [ 3, 4, 'R3'], // 3
        [ 4, 1, 'S4'], [ 4, 2, 'B4'], [ 4, 3, 'G4'], [ 4, 4, 'R4'], // 4
        [ 5, 1, 'S5'], [ 5, 2, 'B5'], [ 5, 3, 'G5'], [ 5, 4, 'R5'], // 5
        [ 6, 1, 'S6'], [ 6, 2, 'B6'], [ 6, 3, 'G6'], [ 6, 4, 'R6'], // 6
        [ 7, 1, 'S7'], [ 7, 2, 'B7'], [ 7, 3, 'G7'], [ 7, 4, 'R7'], // 7
        [ 8, 1, 'S8'], [ 8, 2, 'B8'], [ 8, 3, 'G8'], [ 8, 4, 'R8'], // 8
        [ 9, 1, 'S9'], [ 9, 2, 'B9'], [ 9, 3, 'G9'], [ 9, 4, 'R9'], // 9
        [10, 1, 'SZ'], [10, 2, 'BZ'], [10, 3, 'GZ'], [10, 4, 'RZ'], // 10
        [11, 1, 'SB'], [11, 2, 'BB'], [11, 3, 'GB'], [11, 4, 'RB'], // Bube
        [12, 1, 'SD'], [12, 2, 'BD'], [12, 3, 'GD'], [12, 4, 'RD'], // Dame
        [13, 1, 'SK'], [13, 2, 'BK'], [13, 3, 'GK'], [13, 4, 'RK'], // König
        [14, 1, 'SA'], [14, 2, 'BA'], [14, 3, 'GA'], [14, 4, 'RA'], // Ass
        [15, 0, 'Dr'],                                              // Drache
        [16, 0, 'Ph'],                                              // Phönix
    ];

    const _valueSuitToLabelMap = new Map();
    const _labelToValueSuitMap = new Map();
    _cardDeck.forEach(cardDef => {
        _valueSuitToLabelMap.set(`${cardDef[0]}-${cardDef[1]}`, cardDef[2]);
        _labelToValueSuitMap.set(cardDef[2], [cardDef[0], cardDef[1]]);
    });

    /**
     * Parst ein Array von Karten-Tupeln `[value, suit]` vom Server
     * in ein Array von clientseitigen Kartenobjekten.
     * Jedes Objekt enthält `{ value, suit, label }`.
     * @param {Array<Array<number>>} serverCardsArray - Array von Karten-Tupeln, z.B. `[[2,1], [0,0]]`.
     * @returns {Array<object>} Ein Array von Kartenobjekten für das Frontend.
     */
    function parseCards(serverCardsArray) {
        if (!serverCardsArray || !Array.isArray(serverCardsArray)) {
            return [];
        }
        return serverCardsArray.map(cardTuple => {
            if (!Array.isArray(cardTuple) || cardTuple.length !== 2) {
                console.warn('Ungültiges Kartenformat vom Server:', cardTuple);
                return null; // oder Fehler werfen
            }
            const value = cardTuple[0];
            const suit = cardTuple[1];
            const label = _valueSuitToLabelMap.get(`${value}-${suit}`) || 'UNBEKANNT';
            if (label === 'UNBEKANNT') {
                console.warn(`Kein Label gefunden für Karte: [${value}, ${suit}]`);
            }
            return {value, suit, label};
        }).filter(card => card !== null); // Ungültige Karten herausfiltern
    }

    /**
     * Formatiert ein Array von clientseitigen Kartenobjekten
     * in das vom Server erwartete Format (Array von Tupeln `[value, suit]`).
     * @param {Array<object>} clientCardObjects - Array von Kartenobjekten `{ value, suit, label }`.
     * @returns {Array<Array<number>>} Array von Karten-Tupeln für den Server.
     */
    function formatCardsForServer(clientCardObjects) {
        if (!clientCardObjects || !Array.isArray(clientCardObjects)) {
            return [];
        }
        return clientCardObjects.map(cardObj => [cardObj.value, cardObj.suit]);
    }

    /**
     * Konvertiert ein Array von clientseitigen Kartenobjekten in einen lesbaren String mit Labels.
     * Nützlich für Debugging oder Fehlermeldungen.
     * @param {Array<object>} clientCardObjects - Array von Kartenobjekten `{ value, suit, label }`.
     * @returns {string} Ein String mit Kartenlabels, getrennt durch Leerzeichen.
     */
    function stringifyCardObjectsToLabels(clientCardObjects) {
        if (!clientCardObjects || clientCardObjects.length === 0) {
            return "";
        }
        return clientCardObjects.map(card => card.label).join(' ');
    }

    /**
     * Konvertiert den (kanonischen; serverseitigen) Index eines Spielers
     * in den aus Sicht des Benutzers relativen Index.
     * @param {number} canonicalPlayerIndex - Der (kanonische) Index des Spielers (0-3).
     * @returns {number} Der relative Index (0=eigener Spieler (unten), 1=rechter Gegner, 2=Partner (oben), 3=linker Gegner).
     *                   Gibt -1 zurück, wenn der eigene Spielerindex noch nicht bekannt ist.
     */
    function getRelativePlayerIndex(canonicalPlayerIndex) {
        const ownPlayerIndex = State.getPlayerIndex(); // Holt den eigenen kanonischen Index
        if (ownPlayerIndex === -1 || canonicalPlayerIndex === -1) {
            // console.warn("Eigener Spielerindex oder Ziel-Spielerindex unbekannt für getRelativePlayerIndex");
            return canonicalPlayerIndex; // Fallback oder Fehlerbehandlung
        }
        return (canonicalPlayerIndex - ownPlayerIndex + 4) % 4;
    }

    /**
     * Konvertiert den aus Sicht des Benutzers relativen Index eines Spielers
     * in den kanonischen (serverseitigen) Index.
     * @param {number} relativePlayerIndex - Aus Sicht des Benutzers relativer Index (0=ich, 1=rechts, ...).
     * @returns {number} Der kanonische Index des Spielers.
     *                   Gibt -1 zurück, wenn der eigene Spielerindex noch nicht bekannt ist.
     */
    function getCanonicalPlayerIndex(relativePlayerIndex) {
        const ownPlayerIndex = State.getPlayerIndex(); // Holt den eigenen kanonischen Index
        if (ownPlayerIndex === -1) {
            // console.warn("Eigener Spielerindex unbekannt für getCanonicalPlayerIndex");
            return relativePlayerIndex; // Fallback oder Fehlerbehandlung
        }
        return (ownPlayerIndex + relativePlayerIndex) % 4;
    }

    return {
        parseCards,
        formatCardsForServer,
        stringifyCardObjectsToLabels,
        getRelativePlayerIndex,
        getCanonicalPlayerIndex
    };
})();