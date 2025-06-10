/**
 * Type-Alias für einen Spielzug.
 *
 * @typedef {[number, Cards, Combination]} Turn
 * @property {number} 0 - Index des Spielers.
 * @property {Cards} 1 - Gespielte Karten.
 * @property {Combination} 2 - Kombination.
 */

/**
 * Type-Alias für einen Stich (Liste von Spielzügen).
 *
 * @typedef {Turn[]} Trick
 */

/**
 * Type-Alias für die Punktetabelle
 *
 * @typedef {[number[], number[]]} GameScore
 */

/**
 * Der öffentliche Spielzustand vom Server.
 *
 * @typedef {Object} PublicState
 * @property {string} table_name - Der Name des Tisches.
 * @property {string[]} player_names - Die eindeutigen Namen der 4 Spieler [Spieler 0-3].
 * @property {number} host_index - Index des Clients, der Host ist (-1 = kein Client).
 * @property {boolean} is_running - True, wenn eine Partie gerade läuft.
 * @property {string} current_phase - Aktuelle Spielphase (z.B. "dealing", "schupfing", "playing").
 * @property {number} current_turn_index - Index des Spielers, der am Zug ist (-1 = Startspieler steht noch nicht fest).
 * @property {number} start_player_index - Index des Spielers mit Mahjong (-1 = steht noch nicht fest).
 * @property {number[]} count_hand_cards - Anzahl der Handkarten pro Spieler [Spieler 0-3].
 * @property {Cards} played_cards - Bereits gespielte Karten in der Runde.
 * @property {number[]} announcements - Angekündigtes Tichu pro Spieler [Spieler 0-3] (0 = keine Ansage, 1 = einfaches, 2 = großes).
 * @property {number} wish_value - Gewünschter Kartenwert (2–14, 0 = kein Wunsch, negativ = erfüllt).
 * @property {number} dragon_recipient - Index des Spielers mit Drachen (-1 = noch niemand).
 * @property {number} trick_owner_index - Index des Spielers mit dem Stich (-1 = leerer Stich).
 * @property {Cards} trick_cards - Karten der letzten Kombination im Stich.
 * @property {number[]} trick_combination - Typ, Länge und Wert des aktuellen Stichs ([0,0,0] = leerer Stich).
 * @property {number} trick_points - Punkte des aktuellen Stichs.
 * @property {Trick[]} tricks - Liste der Stiche der aktuellen Runde.
 * @property {number[]} points - Bisher kassierte Punkte in der aktuellen Runde [Spieler 0-3].
 * @property {number} winner_index - Index des ersten Spielers, der fertig wurde (-1 = Runde läuft).
 * @property {number} loser_index - Index des letzten Spielers (-1 = Runde läuft oder Doppelsieg).
 * @property {boolean} isRound_over - Gibt an, ob die Runde beendet ist.
 * @property {boolean} isDouble_victory - Gibt an, ob die Runde durch einen Doppelsieg beendet wurde.
 * @property {GameScore} game_score - Punktetabelle der Partie [Team 20, Team 31].
 * @property {number} round_counter - Anzahl der abgeschlossenen Runden der Partie.
 * @property {number} trick_counter - Anzahl der abgeräumten Stiche insgesamt über alle Runden.
 */

/**
 * Der private Spielzustand vom Server.
 *
 * @typedef {Object} PrivateState
 * @property {number} player_index - Der Index des Benutzers am Tisch (zwischen 0 und 3).
 * @property {Card[]} hand_cards - Die aktuellen Handkarten des Benutzers.
 * @property {[Card, Card, Card] | null} given_schupf_cards - Die drei Karten, die der Benutzer weitergegeben hat.
 * @property {[Card, Card, Card] | null} received_schupf_cards - Die drei Karten, die der Benutzer erhalten hat.
 */

/**
 * Datencontainer für den Spielzustand.
 */
const State = (() => {

    /** Der öffentliche Spielzustand vom Server.
     *
     * @type {PublicState}
     */
    let _publicState = {
        table_name: "",
        player_names: ["", "", "", ""],
        host_index: -1,
        is_running: false,
        current_phase: "init",
        current_turn_index: -1,
        start_player_index: -1,
        count_hand_cards: [0, 0, 0, 0],
        played_cards: [],
        announcements: [0, 0, 0, 0],
        wish_value: 0,
        dragon_recipient: -1,
        trick_owner_index: -1,
        trick_cards: [],
        trick_combination: [0, 0, 0],
        trick_points: 0,
        tricks: [],
        points: [0, 0, 0, 0],
        winner_index: -1,
        loser_index: -1,
        isRound_over: false,
        isDouble_victory: false,
        game_score: [[], []],
        round_counter: 0,
        trick_counter: 0
    };

    /**
     * Der private Spielzustand vom Server.
     *
     * @type {PrivateState}
     */
    let _privateState = {
        player_index: -1,
        hand_cards: [],
        given_schupf_cards: null,
        received_schupf_cards: null
    };

    /**
     * Initialisiert den Zustand, lädt Werte aus dem LocalStorage.
     */
    function init() {
    }

    /**
     * Setzt den öffentlichen Spielzustand.
     *
     * @param {PublicState} publicState - Der öffentliche Spielzustand.
     */
    function setPublicState(publicState) {
        _publicState = publicState;
    }

    /** @returns {PublicState} Den aktuellen öffentlichen Spielzustand. */
    function getPublicState() {
        return _publicState;
    }

    /**
     * Setzt den privaten Spielzustand.
     *
     * @param {PrivateState} privateState - Der private Spielzustand.
     */
    function setPrivateState(privateState) {
        _privateState = privateState;
    }

    /** @returns {PrivateState} Den aktuellen privaten Spielzustand. */
    function getPrivateState() {
        return _privateState;
    }

    /**
     * Setzt den Index des Benutzers.
     *
     * @param {number} playerIndex - Der neue Index des Benutzers.
     */
    function setPlayerIndex(playerIndex) {
        _privateState.player_index = playerIndex;
    }

    /** @returns {number} Den Index des Benutzers. */
    function getPlayerIndex() {
        return _privateState.player_index;
    }

    /** @returns {string} Den Namen des Benutzers. */
    function getPlayerName() {
        return _privateState.player_index !== -1 ? _publicState.player_names[_privateState.player_index] : "";
    }

    /** @returns {string} Den Namen des aktuellen Tisches. */
    function getTableName() {
        return _publicState.table_name;
    }

    /** @returns {boolean} True, wenn der Benutzer der Host des Tisches ist, sonst false. */
    function isHost() {
        return _privateState.player_index !== -1 && _publicState.host_index === _privateState.player_index;
    }

    return {
        init,
        setPublicState,
        getPublicState,
        setPrivateState,
        getPrivateState,
        setPlayerIndex,
        getPlayerIndex,
        getPlayerName,
        getTableName,
        isHost: isHost,
    };
})();