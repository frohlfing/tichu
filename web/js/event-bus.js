/**
 * Type-Alias für das Verzeichnis der Ereignishändler.
 *
 * @typedef {Object.<string, Array<Function>>} EventHandlers
 */

/**
 * Type-Alias für einen Eintrag der Ereigniswarteschlange.
 *
 * @typedef {Object} EventQueueItem
 * @property {string} event - Der Name des Ereignisses.
 * @property {any} data - Die zugehörigen Daten.
 */

/**
 * Zentrale Nachrichtenvermittlung zwischen den Komponenten.
 *
 * @example Anwendungsbeispiel
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
     * @type EventHandlers
     */
    const _handlers = {};

    /**
     * Die Warteschlange für auszulösende Ereignisse.
     *
     * @type {Array<EventQueueItem>}
     */
    const _eventQueue = [];

    /**
     * Flag, das anzeigt, ob die Ereigniswarteschlange gerade verarbeitet wird.
     *
     * @type {boolean}
     */
    let _isProcessing = false;

    /**
     * Flag, das gesetzt ist, wenn die Ereigniswarteschlange pausiert.
     *
     * @type {boolean}
     */
    let _isPaused = false;

    /**
     * Registriert einen Ereignishändler.
     *
     * Doppelte Registrierung derselben Funktion wird verhindert.
     *
     * @param {string} event – Das Ereignis, für das der Ereignishändler registriert werden soll.
     * @param {Function} handler - Der Ereignishändler.
     */
    function on(event, handler) {
        if (!_handlers[event]) {
            _handlers[event] = [];
        }
        if (!_handlers[event].includes(handler)) {
            _handlers[event].push(handler);
        }
    }

    /**
     * Entfernt einen registrierten Ereignishändler.
     *
     * @param {string} event - Das Ereignis, für das der Ereignishändler registriert wurde.
     * @param {Function} handler - Der Ereignishändler.
     */
    function off(event, handler) {
        if (_handlers[event]) {
            _handlers[event] = _handlers[event].filter(h => h !== handler);
        }
    }

    /**
     * Verarbeitet die Event-Queue.
     *
     * Nimmt das nächste Event aus der Queue und führt dessen Handler aus.
     * Plant sich selbst neu, solange Events in der Queue sind.
     * Die Handler werden synchron und blockierend innerhalb eines Events ausgeführt.
     */
    function _processQueue() {
        if (_isPaused || _eventQueue.length === 0) {
            _isProcessing = false;
            return;
        }

        // nächstes Ereignis aus der Queue holen (FIFO)
        const item = _eventQueue.shift();

        // alle Handler für dieses Event sequenziell ausführen
        if (_handlers[item.event]) {
            _handlers[item.event].forEach(handler => {
                try {
                    handler(item.data);
                }
                catch (error) {
                    console.error(`Error in event handler for "${item.event}":`, error, "Handler:", handler);
                }
            });
        }

        if (_eventQueue.length > 0) {
            // es sind noch weitere Ereignisse in der Ereigniswarteschlange
            setTimeout(_processQueue, 0); // Verarbeitung asynchron fortsetzen
        }
        else {
            // Ereigniswarteschlange ist jetzt leer
            _isProcessing = false; // Verarbeitung stoppen
        }
    }

    /**
     * Löst ein Ereignis aus.
     *
     * Die Funktion ist nicht-blockierend, sie kehrt sofort zurück.
     * Für ein gegebenes Event werden dessen Listener nacheinander und blockierend aufgerufen.
     * Die Reihenfolge der ausgelösten Events bleibt bei der Verarbeitung erhalten.
     *
     * @param {string} event - Der Name des auszulösenden Events.
     * @param {any} data - Die Daten, die an die Handler übergeben werden.
     */
    function emit(event, data = null) {
        if (!_handlers[event] || _handlers[event].length === 0) {
            return;
        }

        // Event und Daten zur Queue hinzufügen
        _eventQueue.push({event, data});

        // Wenn die Warteschlange nicht bereits verarbeitet wird, starte die Verarbeitung.
        if (!_isProcessing) {
            _isProcessing = true;
            setTimeout(_processQueue, 0); // starte die Verarbeitung asynchron
        }
    }

    /**
     * Pausiert die Verarbeitung der Event-Queue.
     * Neue Events werden weiterhin zur Queue hinzugefügt, aber nicht verarbeitet.
     */
    function pause() {
        console.log("EventBus: Pausiert.");
        _isPaused = true;
    }

    /**
     * Setzt die Verarbeitung der Event-Queue fort.
     */
    function resume() {
        if (!_isPaused) {
            return;
        }

        console.log("EventBus: Fortgesetzt.");

        _isPaused = false;

        // Starte die Verarbeitung der Queue neu, falls Events anstehen
        // und sie nicht bereits durch einen neuen `emit` gestartet wurde.
        if (_eventQueue.length > 0 && !_isProcessing) {
            _isProcessing = true;
            setTimeout(_processQueue, 0);
        }
    }

    // noinspection JSUnusedGlobalSymbols
    return {
        on,
        off,
        emit,
        pause,
        resume,
    };
})();