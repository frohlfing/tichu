/**
 * Dieses Modul implementiert einen Zufallsgenerator.
 */
const Random = (() => {
    /**
     * Gibt eine zufällige Dezimalzahl zwischen low (inklusiv) und high (exklusiv) zurück.
     *
     * @param {number} low - Untere Grenze (inklusive).
     * @param {number} high - Obere Grenze (exklusive).
     * @returns {number} Eine zufällige Dezimalzahl.
     */
    function float(low, high) {
        return Math.random() * (high - low) + low;
    }

    /**
     * Gibt eine zufällige Ganzzahl zwischen low (inklusiv) und high (exklusiv) zurück.
     *
     * @param {number} low - Untere Grenze (inklusive).
     * @param {number} high - Obere Grenze (exklusive).
     * @returns {number} Eine zufällige Ganzzahl.
     */
    function integer(low, high) {
        return Math.floor(Math.random() * (high - low)) + low;
    }

    /**
     * Gibt zufällig `true` oder `false` zurück.
     *
     * @returns {boolean} Ein zufälliger Wahrheitswert.
     */
    function boolean() {
        return Math.random() < 0.5;
    }

    /**
     * Wählt ein zufälliges Element aus einer Sequenz.
     *
     * @param {Array<any>} seq - Die Eingabesequenz.
     * @param {Array<number>} [weights] - (Optional) Die Gewichtungen (für jedes Element ein Wert, z.B. [1, 3, 6] oder normiert [0.1, 0.3, 0.6]).
     * @returns {any} Ein zufällig ausgewähltes Element.
     */
    function choice(seq, weights = null) {
        if (!weights) {
            const index = Math.floor(Math.random() * seq.length);
            return seq[index];
        } else {
            const totalWeight = weights.reduce((acc, value) => acc + value, 0); // Summe bilden
            const rnd = Math.random() * totalWeight;
            let cumulative = 0
            for (let i = 0; i < seq.length; i++) {
                cumulative += weights[i];
                if (rnd < cumulative) {
                    return seq[i];
                }
            }
        }
    }

    /**
     * Gibt `k` zufällige Elemente aus einer Sequenz zurück (ohne Zurücklegen).
     *
     * @param {Array<any>} seq - Die Eingabesequenz.
     * @param {number} k - Anzahl der zu ziehenden Elemente (darf nicht größer als die Array-Länge sein).
     * @returns {Array<any>} Eine Liste zufälliger Elemente.
     */
    function sample(seq, k) {
        const clone = [...seq]; // Kopie, um Original nicht zu verändern
        const result = [];
        for (let i = 0; i < k; i++) {
            const index = Math.floor(Math.random() * clone.length);
            result.push(clone.splice(index, 1)[0]);
        }
        return result;
    }

    /**
     * Mischt eine Sequenz in-place.
     *
     * Die Funktion basiert auf den Fisher-Yates-Algorithmus.
     *
     * @param {Array} seq - Die zu mischende Sequenz (mutable).
     */
    function shuffle(seq) {
        for (let i = seq.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [seq[i], seq[j]] = [seq[j], seq[i]];
        }
    }

    // noinspection JSUnusedGlobalSymbols
    return {
        float,
        integer,
        boolean,
        choice,
        sample,
        shuffle,
    };
})();
