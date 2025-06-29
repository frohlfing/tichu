/**
 * Stellt Funktionen für die Unit-Tests bereit.
 *
 * Auf dem Produktiv-System werden die Tests NICHT ausgeführt!
 */
(function () {

    const _tests = [];

    /**
     * Definiert einen Test.
     *
     * Anwendungsbeispiel:
     * ```
     *      test('Addition.', () => {
     *          assert(1 + 2, 3);
     *      });
     *
     *      test('Test mit Parameter', (a, b, expected) => {
     *          assert(a + b, expected);
     *      }, [
     *          [1, 2, 3],
     *          [4, 5, 9],
     *          [2, 2, 5],
     *      ]);
     * ```
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
                _tests.push({name: caseName, fn: () => fn(...params)});
            }
        }
        else {
            _tests.push({name: name, fn: fn});
        }
    }

    /**
     * Prüft, ob zwei Werte gleich sind.
     *
     * Die Werte werden mit per Tiefenvergleich (Deep Comparison) geprüft, so dass auch
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
     * Erzeugt ein Vergleichsobjekt für Gleitkommazahlen mit Toleranz.
     *
     * Wird in Verbindung mit `assert()` verwendet, um numerische Werte auf „nahe genug“ zu prüfen – ähnlich wie `pytest.approx()`.
     *
     * Anwendungsbeispiel:
     * ```
     *      assert(0.1 + 0.2, approx(0.3));
     * ```
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
        const output = document.getElementById('output');
        const statusbar = document.getElementById('statusbar');
        let passed = 0;
        let failed = 0;
        for (const {name, fn} of _tests) {
            try {
                await fn();
                output.innerHTML += `✅ ${name}\n`;
                passed++;
            }
            catch (e) {
                output.innerHTML += `❌ ${name}\n    ${e.message}\n`;
                failed++;
            }
        }

        statusbar.classList.add(failed === 0 ? 'pass' : 'fail');
        output.innerHTML += `\n<span class="summary">========== summary ==========</span>\n`;
        output.innerHTML += `${passed + failed} tests collected\n`;
        output.innerHTML += `${failed} failed, ${passed} passed\n`;
    }

    // Funktion `_runTests` ausführen, sobald die gesamte Seite vollständig geladen ist
    if (Config.ENVIRONMENT !== "production") {
        window.onload = _runTests;
    }

    // Funktionen `test` und `assert` global bereitstellen
    window.test = test;
    window.assert = assert;
    window.approx = approx;
})();