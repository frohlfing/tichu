/**
 * Zentrale Nachrichtenvermittlung zwischen den Komponenten.
 *
 * Anwendungsbeispiel:
 *
 * EventBus.on('user:login', (data) => {
 *   console.log(`User logged in: ${data.name}`);
 * });
 *
 * EventBus.emit('user:login', { name: 'Bob' });
 */
const EventBus = (() => {
    /**
     * Die registrierten Ereignishändler.
     *
     * @type {Object.<string, function[]>}
     */
    const _events = {};

    /**
     * Registriert einen Ereignishändler.
     * Doppelte Registrierung derselben Funktion wird verhindert.
     *
     * @param {string} event – Das Ereignis, für das der Ereignishändler registriert werden soll.
     * @param {function} handler - Der Ereignishändler.
     */
    function on(event, handler) { // on(event, listener)
        if (!_events[event]) {
            _events[event] = [];
        }

        // Verhindert doppelte Registrierung
        if (!_events[event].includes(handler)) {
            _events[event].push(handler);
        }
    }

    /**
     * Entfernt einen registrierten Ereignishändler.
     *
     * @param {string} event - Das Ereignis, für das der Ereignishändler registriert wurde.
     * @param {function} handler - Der Ereignishändler.
     */
    function off(event, handler) {
        if (_events[event]) {
            _events[event] = _events[event].filter(h => h !== handler);
        }
    }

    /**
     * Löst ein Ereignis aus und übermittelt Daten an alle registrierten Ereignishändler.
     *
     * @param {string} event - Der Name des auszulösenden Events.
     * @param {any} data - Die Daten, die an die Handler übergeben werden.
     */
    function emit(event, data) {
        if (_events[event]) {
            _events[event].forEach(handler => handler(data));
        }
    }

    // noinspection JSUnusedGlobalSymbols
    return {
        on,
        off,
        emit,
    };
})();