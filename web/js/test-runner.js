/**
 * Stellt Funktionen für die Unit-Tests bereit.
 */
(function () {

    const tests = [];

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
                const caseName = `${name} [${index + 1}] → ${params.join(', ')}`;
                tests.push({name: caseName, fn: () => fn(...params)});
            }
        }
        else {
            tests.push({name: name, fn: fn});
        }
    }

    /**
     * Einfacher Gleichheitsvergleich.
     *
     * @param {any} actual - Der tatsächlich erhaltene Wert.
     * @param {any} expected - Der erwartete Sollwert.
     * @throws {Error} Wenn `actual !== expected`
     */
    function assert(actual, expected) {
        if (actual !== expected) {
            throw new Error(`Expected "${expected}", but got "${actual}"`);
        }
    }

    /**
     * Führt alle registrierten Tests aus und zeigt die Ergebnisse im Browser an.
     */
    async function runTests() {
        const output = document.getElementById('output');
        const statusbar = document.getElementById('statusbar');
        let passed = 0;
        let failed = 0;
        for (const {name, fn} of tests) {
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

    // Funktion `runTests` ausführen, sobald die gesamte Seite vollständig geladen ist
    window.onload = runTests;

    // Funktionen `test` und `assert` global bereitstellen
    window.test = test;
    window.assert = assert;
})();