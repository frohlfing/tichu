/**
 * Stellt Funktionen für die Unit-Tests bereit.
 *
 * Auf dem Produktiv-System werden die Tests NICHT ausgeführt!
 */
(function () {

    const _tests = [];
    let _currentGroup = null;

    /**
     * Gruppiert Tests unter einem gemeinsamen Namen.
     *
     * @param {string} name - Gruppenname.
     * @param {Function} fn - Funktion, die Tests registriert.
     */
    function describe(name, fn) {
        _currentGroup = name;
        fn();
        _currentGroup = null;
    }

    /**
     * Definiert einen Test.
     *
     * @example
     * test('Addition.', () => {
     *     assert(1 + 2, 3);
     * });
     *
     * test('Test mit Parameter', (a, b, expected) => {
     *     assert(a + b, expected);
     * }, [
     *     [1, 2, 3],
     *     [4, 5, 9],
     *     [2, 2, 5]
     * ]);
     *
     * @param {string} name - Der Name des Tests.
     * @param {Function} fn - Die Testfunktion.
     * @param {Array<Array<any>>} [cases] - Optional: Array von Argument-Arrays für parametrisierte Tests.
     */
    function test(name, fn, cases = null) {
        if (cases) {
            for (const [index, params] of cases.entries()) {
                const paramStr = params.map(p => _stringify(p)).join(', ');
                const caseName = `${name} [${index + 1}] → ${paramStr}`;
                _tests.push({group: _currentGroup, name: caseName, fn: () => fn(...params)});
            }
        }
        else {
            _tests.push({group: _currentGroup, name: name, fn: fn});
        }
    }

    /**
     * Prüft, ob zwei Werte gleich sind.
     *
     * Die Werte werden per Tiefenvergleich (Deep Comparison) geprüft, so dass auch
     * Arrays und Objekte korrekt verglichen werden.
     *
     * @param {any} actual - Der tatsächlich erhaltene Wert.
     * @param {any} expected - Der erwartete Wert.
     * @param {string|null} [message] - Optional: eigene Fehlermeldung bei Nicht-Gleichheit.
     * @throws {Error} Wenn die Werte nicht gleich sind.
     */
    function assert(actual, expected, message = null) {
        if (!_isEqual(actual, expected)) {
            throw new Error(message || `Expected ${_stringify(expected)}, but got ${_stringify(actual)}`);
        }
    }

    /**
     * Prüft, ob eine Funktion eine Exception wirft.*
     *
     * @example
     * assertThrows(() => {
     *     throw new Error('Ungültiger Zustand');
     * }, 'Ungültig');
     *
     * @param {Function} fn
     * @param {string|null} [expectedMessage]
     */
    function assertThrows(fn, expectedMessage = null) {
        let threw = false;
        try {
            fn();
        }
        catch (e) {
            threw = true;
            if (expectedMessage && !e.message.includes(expectedMessage)) {
                throw new Error(`Expected error message to include "${expectedMessage}", but got "${e.message}"`);
            }
        }
        if (!threw) {
            throw new Error('Expected function to throw, but it did not');
        }
    }

    /**
     * Erzeugt ein Vergleichsobjekt für Gleitkommazahlen mit Toleranz.
     *
     * Wird in Verbindung mit `assert()` verwendet, um numerische Werte auf „nahe genug“ zu prüfen – ähnlich wie `pytest.approx()`.
     *
     * @example
     * assert(0.1 + 0.2, approx(0.3));
     *
     * @param {number} expected - Die erwartete Gleitkommazahl.
     * @param {number} [tolerance] - Optional: Die maximale Abweichung, die noch als gleich gilt (Default: 1e-9).
     * @returns {{_approx_: true, expected: number, tolerance: number}} Das Vergleichsobjekt.
     */
    function approx(expected, tolerance = 1e-9) {
        return {_approx_: true, expected, tolerance};
    }

    /**
     * Vergleicht zwei Werte tief (rekursiv), unterstützt primitive Werte, Arrays und Objekte.
     *
     * @param {any} a - Der tatsächlich erhaltene Wert.
     * @param {any} b - Der erwartete Wert.
     * @returns {boolean} True, wenn die Werte gleich sind, sonst false.
     */
    function _isEqual(a, b) {
        if (a === b) {
            return true;
        }

        if (b && typeof b === 'object' && b._approx_ === true) {
            return typeof a === 'number' && Math.abs(a - b.expected) <= b.tolerance;
        }

        if (Array.isArray(a) && Array.isArray(b)) {
            if (a.length !== b.length) {
                return false;
            }
            return a.every((v, i) => _isEqual(v, b[i]));
        }

        if (a && b && typeof a === 'object' && typeof b === 'object') {
            const keysA = Object.keys(a);
            const keysB = Object.keys(b);
            if (keysA.length !== keysB.length) {
                return false;
            }
            return keysA.every(key => _isEqual(a[key], b[key]));
        }

        return false;
    }

    /**
     * Gibt den Wert als String aus.
     *
     * @param {any} val - Der umzuwandelnde Wert.
     * @returns {string} Der Wert als String.
     */
    function _stringify(val) {
        try {
            return JSON.stringify(val, (_key, value) =>
                value && value._approx_ === true ? `${value.expected}±${value.tolerance}` : value
            );
        }
        catch {
            return String(val);
        }
    }

    /**
     * Führt alle registrierten Tests aus und zeigt die Ergebnisse im Browser an.
     */
    async function _runTests() {
        const statusbar = document.getElementById('statusbar');
        const output = document.getElementById('output');

        let passed = 0;
        let failed = 0;

        const grouped = {};
        for (const [i, test] of _tests.entries()) {
            const group = test.group || 'Allgemein';
            if (!grouped[group]) {
                grouped[group] = [];
            }
            grouped[group].push({...test, index: i});
        }

        for (const groupName in grouped) {
            const groupContainer = document.createElement('details');
            groupContainer.open = false;
            const groupHeader = document.createElement('summary');
            groupHeader.textContent = groupName;
            groupContainer.appendChild(groupHeader);
            const ul = document.createElement('ul');
            for (const test of grouped[groupName]) {
                const li = document.createElement('li');
                try {
                    await test.fn();
                    li.textContent = `✅ ${test.name}`;
                    //li.className = 'test-pass';
                    passed++;
                }
                catch (error) {
                    li.textContent = `❌ ${test.name}`;
                    //li.className = 'test-fail';
                    failed++;
                    groupContainer.open = true;
                    const pre = document.createElement('pre');
                    pre.textContent = _getErrorDetails(error);
                    li.appendChild(pre);
                }
                ul.appendChild(li);
            }
            groupContainer.appendChild(ul);
            output.appendChild(groupContainer);
        }

        statusbar.classList.add(failed === 0 ? 'pass' : 'fail');
        output.innerHTML += `\n<span class="summary">========== summary ==========</span>\n`;
        output.innerHTML += `${passed + failed} tests collected\n`;
        output.innerHTML += `${failed} failed, ${passed} passed\n`;
    }

    /**
     * Extrahiert relevante Fehlerdetails.
     *
     * @param {Error} error - Der ausgelöste Fehler.
     * @returns {string} Fehlertext und Angaben, wo der Fehler ausgelöst wurde.
     */
    function _getErrorDetails(error) {
        const details = [];
        details.push(error.message);
        if (error.stack) {
            const stackLines = error.stack.split('\n');
            // der letzte Stack-Eintrag is test-runner.js, ich will aber tests.js
            const relevantLine = stackLines.findLast(line => line.includes('.js') && !line.includes('test-runner.js')); // at Object.fn (http://localhost:63342/tichu/web/js/tests.js:284:28)
            //const relevantLine = stackLines[relevantIndex] || ""; // at Object.fn (http://localhost:63342/tichu/web/js/tests.js:284:28)
            const start = relevantLine.lastIndexOf('/');
            const end = relevantLine.lastIndexOf(')');
            const location= relevantLine.slice(start + 1, end > start ? end : undefined); // tests.js:284:28
            const [file, line, _column] = location.split(':');
            if (file && line) {
                details.push(`${file}, Zeile ${line}`);
            }
        }
        return details.join('\n');
    }

    // Funktion `_runTests` ausführen, sobald die gesamte Seite vollständig geladen ist
    if (Config.ENVIRONMENT !== "production") {
        window.onload = _runTests;
    }

    // Funktionen `test` und `assert` global bereitstellen
    window.describe = describe;
    window.test = test;
    window.assert = assert;
    window.assertThrows = assertThrows;
    window.approx = approx;
})();