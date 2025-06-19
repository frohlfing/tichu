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
 * @property {number} host_index - Index des Clients, der Host ist (-1 = kein Client).
 * @property {string[]} player_names - Die eindeutigen Namen der 4 Spieler.
 * @property {boolean} is_running - Gibt an, ob eine Partie gerade läuft.
 * @property {number} current_turn_index - Index des Spielers, der am Zug ist (-1 = Startspieler steht noch nicht fest).
 * @property {number} start_player_index - Index des Spielers mit Mahjong (-1 = steht noch nicht fest).
 * @property {number[]} count_hand_cards - Anzahl der Handkarten pro Spieler.
 * @property {Cards} played_cards - Bereits gespielte Karten in der Runde.
 * @property {number[]} announcements - Angekündigtes Tichu pro Spieler (0 = keine Ansage, 1 = einfaches, 2 = großes).
 * @property {number} wish_value - Gewünschter Kartenwert (2–14, 0 = kein Wunsch, negativ = erfüllt).
 * @property {number} dragon_recipient - Index des Spielers, der den Drachen geschenkt bekommen hat (-1 = noch niemand).
 * @property {number} trick_owner_index - Index des Spielers, der den Stich besitzt (-1 = leerer Stich).
 * @property {Cards} trick_cards - Karten der letzten Kombination im Stich.
 * @property {Combination} trick_combination - Typ, Länge und Wert des aktuellen Stichs ([0,0,0] = leerer Stich).
 * @property {number} trick_points - Punkte des aktuellen Stichs.
 * @property {Trick[]} tricks - Liste der Stiche der aktuellen Runde. Der letzte Eintrag ist u.U. noch offen.
 * @property {number[]} points - Bisher kassierte Punkte in der aktuellen Runde pro Spieler.
 * @property {number} winner_index - Index des ersten Spielers, der fertig wurde (-1 = Runde läuft).
 * @property {number} loser_index - Index des letzten Spielers (-1 = Runde läuft oder Doppelsieg).
 * @property {boolean} is_round_over - Gibt an, ob die Runde beendet ist.
 * @property {boolean} is_double_victory - Gibt an, ob die Runde durch einen Doppelsieg beendet wurde.
 * @property {GameScore} game_score - Punktetabelle der Partie für Team 20 und Team 31.
 * @property {number} round_counter - Anzahl der abgeschlossenen Runden der Partie.
 * @property {number} trick_counter - Anzahl der abgeräumten Stiche insgesamt über alle Runden.
 */

/**
 * Der private Spielzustand vom Server.
 *
 * @typedef {Object} PrivateState
 * @property {number} player_index - Der Index des Benutzers am Tisch (zwischen 0 und 3).
 * @property {Cards} hand_cards - Die aktuellen Handkarten des Benutzers.
 * @property {[Card, Card, Card] | null} given_schupf_cards - Die drei Karten (für rechten Gegner, Partner, linken Gegner), die der Benutzer weitergegeben hat.
 * @property {[Card, Card, Card] | null} received_schupf_cards - Die drei Karten (vom rechten Gegner, Partner, linken Gegner), die der Benutzer erhalten hat.
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
        host_index: -1,
        player_names: ["", "", "", ""],
        is_running: false,
        current_turn_index: -1,
        start_player_index: -1,
        count_hand_cards: [0, 0, 0, 0],
        played_cards: /** @type Cards */ [],
        announcements: [0, 0, 0, 0],
        wish_value: 0,
        dragon_recipient: -1,
        trick_owner_index: -1,
        trick_cards: /** @type Cards */ [],
        trick_combination: /** @type Combination */ [0, 0, 0],
        trick_points: 0,
        tricks: /** @type Trick[] */ [],
        points: [0, 0, 0, 0],
        winner_index: -1,
        loser_index: -1,
        is_round_over: false,
        is_double_victory: false,
        game_score: /** @type GameScore */ [[], []],
        round_counter: 0,
        trick_counter: 0
    };

    /**
     * Der private Spielzustand vom Server.
     *
     * @type {PrivateState}
     */
    let _privateState = {
        player_index: 0,
        hand_cards: [],
        given_schupf_cards: null,
        received_schupf_cards: null
    };

    // /**
    //  * Initialisiert den Spielzustand.
    //  *
    //  * @param {PublicState|null} publicState - Der öffentliche Spielzustand.
    //  * @param {PrivateState|null} privateState - Der private Spielzustand.
    //  */
    // function init(publicState = null, privateState = null) {
    //     if (publicState) {
    //         _publicState = publicState;
    //     }
    //     if (privateState) {
    //         _privateState = privateState;
    //     }
    // }

    // /**
    //  * Initialisiert den Spielzustand.
    //  */
    // function init() {
    // }

    /**
     * Übernimmt den serverseitigen Spielzustand.
     *
     * @param {PublicState} publicState - Der öffentliche Spielzustand.
     * @param {PrivateState} privateState - Der private Spielzustand.
     */
    function set(publicState, privateState) {
        _publicState = publicState;
        _privateState = privateState;
    }

    // öffentlicher Spielzustand

    /** @returns {string} Den Namen des aktuellen Tisches. */
    function getTableName() {
        return _publicState.table_name;
    }

    /** @returns {number} Index des Clients, der Host ist (-1 = kein Client). */
    function getHostIndex() {
        return _publicState.host_index;
    }

    /** @param {number} index - Index des Clients, der Host ist (-1 = kein Client). */
    function setHostIndex(index) {
        _publicState.host_index = index;
    }

    /** @returns {boolean} True, wenn der Benutzer der Host des Tisches ist, sonst false. */
    function isHost() {
        return _privateState.player_index !== -1 && _publicState.host_index === _privateState.player_index;
    }

    /**
     * @param {number|null} playerIndex - Der Index des Spielers. Wenn nicht angegeben, wird der Index des Benutzers genommen.
     * @returns {string} Der Namen des Spielers.
     */
    function getPlayerName(playerIndex = null){
        if (playerIndex == null) {
           playerIndex = _privateState.player_index;
        }
        return playerIndex !== -1 ? _publicState.player_names[playerIndex] : "";
    }

    /**
     * @param {number} playerIndex - Der Index des Spielers.
     * @param {string} name - Der neue Name des Spielers.
     */
    function setPlayerName(playerIndex, name) {
        _publicState.player_names[playerIndex] = name;
    }
    
    /** @returns {boolean} Gibt an, ob eine Partie gerade läuft. */
    function isRunning(){
        return _publicState.is_running;
    }

    /** @param {boolean} flag - Gibt an, ob eine Partie gerade läuft. */
    function setRunning(flag) {
        _publicState.is_running = flag;
    }
    
    /** @returns {number} Der Index des Spielers, der am Zug ist (-1 = Startspieler steht noch nicht fest). */
    function getCurrentTurnIndex(){
        return _publicState.current_turn_index;
    }

    /** @param {number} index - Der Index des Spielers, der am Zug ist (-1 = Startspieler steht noch nicht fest). */
    function setCurrentTurnIndex(index) {
        _publicState.current_turn_index = index;
    }

    /** @returns {boolean} Gibt an, ob der Benutzer am Zug ist. */
    function isCurrentPlayer() {  // todo umbenennen in "isTurn"
        return _privateState.player_index !== -1 && _publicState.current_turn_index === _privateState.player_index;
    }

    /** @returns {number} Der Index des Spielers mit Mahjong (-1 = steht noch nicht fest). */
    function getStartPlayerIndex(){
        return _publicState.start_player_index;
    }

    /** @param {number} index - Der Index des Spielers mit Mahjong (-1 = steht noch nicht fest). */
    function setStartPlayerIndex(index) {
        _publicState.start_player_index = index;
    }
    
    /**
     * @param {number|null} playerIndex - Der Index des Spielers. Wenn nicht angegeben, wird der Index des Benutzers genommen.
     * @returns {number} Die Anzahl der Handkarten des Spielers. 
     */
    function getCountHandCards(playerIndex = null){
        if (playerIndex == null) {
           playerIndex = _privateState.player_index;
        }
        return playerIndex !== -1 ? _publicState.count_hand_cards[playerIndex] : 0;
    }

    /**
     * Setzt die Anzahl der Handkarten eines Spielers.
     *
     * Ist der Spieler der Benutzer, sollte die angegebene Anzahl mit getHandCards() übereinstimmten.
     * Es findet keine Validierung statt!
     *
     * @param {number} playerIndex - Der Index des Spielers.
     * @param {number} count - Die Anzahl der Handkarten des angebenden Spielers.
     */
    function setCountHandCards(playerIndex, count) {
        _publicState.count_hand_cards[playerIndex] = count;
    }
    
    /** @returns {Cards} Bereits gespielte Karten in der Runde. */
    function getPlayedCards(){
        return _publicState.played_cards;
    }

    /** @param {Cards} cards - Bereits gespielte Karten in der Runde. */
    function setPlayedCards(cards) {
        _publicState.played_cards = cards;
    }
    
    /**
     * @param {number|null} playerIndex - Der Index des Spielers. Wenn nicht angegeben, wird der Index des Benutzers genommen.
     * @returns {number} Tichu-Ansage des Spielers (0 = keine Ansage, 1 = einfaches, 2 = großes).
     */
    function getAnnouncement(playerIndex = null){
        if (playerIndex == null) {
           playerIndex = _privateState.player_index;
        }
        return playerIndex !== -1 ? _publicState.announcements[playerIndex] : 0;
    }

    /**
     * @param {number} playerIndex - Der Index des Spielers.
     * @param {number} announcement - Tichu-Ansage des Spielers (0 = keine Ansage, 1 = einfaches, 2 = großes).
     */
    function setAnnouncement(playerIndex, announcement) {
        _publicState.announcements[playerIndex] = announcement;
    }
    
    /** @returns {number} wish_value - Gewünschter Kartenwert (2–14, 0 = kein Wunsch, negativ = erfüllt). */
    function getWishValue(){
        return _publicState.wish_value;
    }

    /** @param {number} value - Gewünschter Kartenwert (2–14, 0 = kein Wunsch, negativ = erfüllt). */
    function setWishValue(value) {
        _publicState.wish_value = value;
    }
    
    /** @returns {number} dragon_recipient - Index des Spielers, der den Drachen geschenkt bekommen hat (-1 = noch niemand). */
    function getDragonRecipient(){
        return _publicState.dragon_recipient;
    }

    /** @param {number} index - Index des Spielers, der den Drachen geschenkt bekommen hat(-1 = noch niemand). */
    function setDragonRecipient(index) {
        _publicState.dragon_recipient = index;
    }
        
    /** @returns {number} trick_owner_index - Index des Spielers, der den Stich besitzt (-1 = leerer Stich). */
    function getTrickOwnerIndex(){
        return _publicState.trick_owner_index;
    }

    /** @param {number} index - Index des Spielers, der den Stich besitzt (-1 = leerer Stich). */
    function setTrickOwnerIndex(index) {
        _publicState.trick_owner_index = index;
    }
    
    /** @returns {Cards} trick_cards - Karten der letzten Kombination im Stich. */
    function getTrickCards(){
        return _publicState.trick_cards;
    }

    /** @param {Cards} cards - Karten der letzten Kombination im Stich. */
    function setTrickCards(cards) {
        _publicState.trick_cards = cards;
    }
    
    /** @returns {Combination} Typ, Länge und Wert des aktuellen Stichs ([0,0,0] = leerer Stich). */
    function getTrickCombination(){
        return _publicState.trick_combination;
    }

    /** @param {Combination} combination - Typ, Länge und Wert des aktuellen Stichs ([0,0,0] = leerer Stich). */
    function setTrickCombination(combination) {
        _publicState.trick_combination = combination;
    }
    
    /** @returns {number} trick_points - Punkte des aktuellen Stichs. */
    function getTrickPoints(){
        return _publicState.trick_points;
    }

    /** @param {number} points - Punkte des aktuellen Stichs. */
    function setTrickPoints(points) {
        _publicState.trick_points = points;
    }
    
    /** @returns {Trick[]} Liste der Stiche der aktuellen Runde. */
    function getTricks(){
        return _publicState.tricks;
    }

    /** @param {Trick[]} tricks - Liste der Stiche der aktuellen Runde. */
    function setTricks(tricks) {
        _publicState.tricks = tricks;
    }

    /** @returns {Trick|null} Der letzte Stich der aktuellen Runde. */
    function getLastTrick(){
        return _publicState.tricks.length ? _publicState.tricks[_publicState.tricks.length - 1] : null;
    }

    /**
     * @param {number|null} playerIndex - Der Index des Spielers. Wenn nicht angegeben, wird der Index des Benutzers genommen.
     * @returns {number} Bisher kassierte Punkte des Spielers in der aktuellen Runde.
     */
    function getPoints(playerIndex = null){
        if (playerIndex == null) {
           playerIndex = _privateState.player_index;
        }
        return playerIndex !== -1 ? _publicState.points[playerIndex] : 0;
    }

    /**
     * @param {number} playerIndex - Der Index des Spielers.
     * @param {number} points - Bisher kassierte Punkte des Spielers in der aktuellen Runde.
     */
    function setPoints(playerIndex, points) {
        _publicState.points[playerIndex] = points;
    }
    
    /** @returns {number} Der Index des ersten Spielers, der zuerst fertig wurde (-1 = Runde läuft). */
    function getWinnerIndex(){
        return _publicState.winner_index;
    }

    /** @param {number} index - Der Index des ersten Spielers, der zuerst fertig wurde (-1 = Runde läuft). */
    function setWinnerIndex(index) {
        _publicState.winner_index = index;
    }
    
    /** @returns {number} Der Index des letzten Spielers (-1 = Runde läuft oder Doppelsieg). */
    function getLoserIndex(){
        return _publicState.loser_index;
    }

    /** @param {number} index - Der Index des letzten Spielers (-1 = Runde läuft oder Doppelsieg). */
    function setLoserIndex(index) {
        _publicState.loser_index = index;
    }
    
    /** @returns {boolean} Gibt an, ob die Runde beendet ist. */
    function isRoundOver(){
        return _publicState.is_round_over;
    }

    /** @param {boolean} flag - Gibt an, ob die Runde beendet ist (default: true). */
    function setRoundOver(flag = true) {
        _publicState.is_round_over = flag;
    }
    
    /** @returns {boolean} Gibt an, ob die Runde durch einen Doppelsieg beendet wurde. */
    function isDoubleVictory(){
        return _publicState.is_double_victory;
    }

    /** @param {boolean} flag - Gibt an, ob die Runde durch einen Doppelsieg beendet wurde. */
    function setDoubleVictory(flag = true) {
        _publicState.is_double_victory = flag;
    }
    
    /** @returns {GameScore} Punktetabelle der Partie für Team 20 und Team 31. */
    function getGameScore(){
        return _publicState.game_score;
    }

    /**
     * @param {[number, number]} score - Ergebnis einer Partie (Punkte für Team 20 und für Team 31).
     */
    function addGameScoreEntry(score) {
        _publicState.game_score[0].push(score[0]);
        _publicState.game_score[1].push(score[1]);
    }

    /**
     * Setzt die Punktetabelle zurück (löscht alle Einträge).
     */
    function resetGameScore() {
        _publicState.game_score[0] = [];
        _publicState.game_score[1] = [];
    }

    /** @returns {[number, number]} Gesamtpunktestand der Partie für Team 20 und Team 31. */
    function getTotalScore(){
        return [Lib.sum(_publicState.game_score[0]), Lib.sum(_publicState.game_score[1])];
    }

    /** @returns {boolean} Gibt an, ob die Partie beendet ist. */
    function isGameOver(){
        const score = getTotalScore();
        return score[0] >= 1000 || score[1] >= 1000;
    }

    // /** @returns {boolean} Aktuelle Spielphase (z.B. "dealing", "schupfing", "playing"). */
    // function getPhase() {
    //     // todo!
    // }

    // privater Spielzustand

    /** @returns {number} Den Index des Benutzers (zwischen 0 und 3). */
    function getPlayerIndex() {
        return _privateState.player_index;
    }

    /** @param {number} playerIndex - Der neue Index des Benutzers. */
    function setPlayerIndex(playerIndex) {
        _privateState.player_index = playerIndex;
    }

    /** @returns {Cards} Die aktuellen Handkarten des Benutzers. */
    function getHandCards() {
        return _privateState.hand_cards;
    }

    /** @param {Cards} cards - Die aktuellen Handkarten des Benutzers. */
    function setHandCards(cards) {
        _privateState.hand_cards = cards;
        if (_privateState.player_index) {
            _publicState.count_hand_cards[_privateState.player_index] = cards.length;
        }
    }

    /** @returns {[Card, Card, Card] | null} Die drei Karten (für rechten Gegner, Partner, linken Gegner), die der Benutzer weitergegeben hat. */
    function getGivenSchupfCards() {
        return _privateState.given_schupf_cards;
    }

    /** @param {[Card, Card, Card] | null} cards - Die drei Karten (für rechten Gegner, Partner, linken Gegner), die der Benutzer weitergegeben hat. */
    function setGivenSchupfCards(cards) {
        _privateState.given_schupf_cards = cards;
    }

    /** @returns {[Card, Card, Card] | null} Die drei Karten (vom rechten Gegner, Partner, linken Gegner), die der Benutzer erhalten hat. */
    function getReceivedSchupfCards() {
        return _privateState.received_schupf_cards;
    }

    /** @param {[Card, Card, Card] | null} cards - Die drei Karten (vom rechten Gegner, Partner, linken Gegner), die der Benutzer erhalten hat. */
    function setReceivedSchupfCards(cards) {
        _privateState.received_schupf_cards = cards;
    }

    // noinspection JSUnusedGlobalSymbols
    return {
        set,

        // öffentlicher Spielzustand
        getTableName,
        getHostIndex, setHostIndex, isHost,
        getPlayerName, setPlayerName,
        isRunning, setRunning,
        getCurrentTurnIndex, setCurrentTurnIndex, isCurrentPlayer,
        getStartPlayerIndex, setStartPlayerIndex,
        getCountHandCards, setCountHandCards,
        getPlayedCards, setPlayedCards,
        getAnnouncement, setAnnouncement,
        getWishValue, setWishValue,
        getDragonRecipient, setDragonRecipient,
        getTrickOwnerIndex, setTrickOwnerIndex,
        getTrickCards, setTrickCards,
        getTrickCombination, setTrickCombination,
        getTrickPoints, setTrickPoints,
        getTricks, setTricks, getLastTrick,
        getPoints, setPoints,
        getWinnerIndex, setWinnerIndex,
        getLoserIndex, setLoserIndex,
        isRoundOver, setRoundOver,
        isDoubleVictory, setDoubleVictory,
        getGameScore, addGameScoreEntry, resetGameScore,
        getTotalScore,
        isGameOver,
        //getPhase,

        // privater Spielzustand
        getPlayerIndex, setPlayerIndex,
        getHandCards, setHandCards,
        getGivenSchupfCards, setGivenSchupfCards,
        getReceivedSchupfCards, setReceivedSchupfCards,
    };
})();