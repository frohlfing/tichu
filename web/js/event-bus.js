/**
 * Zentrale Nachrichtenvermittlung zwischen den Komponenten.
 */
const EventBus = (() => {
    /**
     * Die registrierten Event-Handler.
     *
     * @type {Object.<string, function[]>}
     */
    let _events = {};

    /**
     * Registriert einen Handler, der aufgerufen wird, wenn das entsprechende Event eintritt.
     * Doppelte Registrierung derselben Funktion wird verhindert.
     *
     * @param {string} event – Der Name des Events, das abonniert wird.
     * @param {function} handler - Die Funktion, die beim Eintreten des Events ausgeführt wird.
     */
    function subscribe(event, handler) {
        if (!_events[event]) {
            _events[event] = [];
        }

        // Verhindert doppelte Registrierung
        if (!_events[event].includes(handler)) {
            _events[event].push(handler);
        }
    }

    /**
     * Entfernt einen registrierten Handler vom Event.
     *
     * @param {string} event - Der Name des Events.
     * @param {function} handler - Die Funktion, die entfernt werden soll.
     */
    function unsubscribe(event, handler) {
        if (_events[event]) {
            _events[event] = _events[event].filter(h => h !== handler);
        }
    }

    /**
     * Löst ein Event aus und übermittelt Daten an alle registrierten Handler.
     *
     * @param {string} event - Der Name des auszulösenden Events.
     * @param {any} data - Die Daten, die an die Handler übergeben werden.
     */
    function publish(event, data) {
        if (_events[event]) {
            _events[event].forEach(handler => handler(data));
        }
    }

    return {
        subscribe,
        unsubscribe,
        publish
    };
})();
