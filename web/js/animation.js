/**
 * Visuelle Effekte & Animationen
 */
const Animation = (() => {

    /**
     * Der Hauptcontainer, der mit einer Ausgangsgröße von 1080x1920 in den Viewport des Browsers skaliert wird.
     *
     * @type {HTMLElement}
     */
    const _wrapper = document.getElementById('wrapper');

    /**
     * Die Ablage-Zonen für die Tauschkarten.
     *
     * @type {Array<HTMLElement>}
     */
    const _schupfZones = [
        document.getElementById('schupf-zone-bottom'),
        document.getElementById('schupf-zone-right'),
        document.getElementById('schupf-zone-top'),
        document.getElementById('schupf-zone-left'),
    ];

    /**
     * Die Ablage-Zonen für den aktuellen Stich.
     *
     * @type {Array<HTMLElement>}
     */
    const _trickZones = [
        document.getElementById('trick-zone-bottom'),
        document.getElementById('trick-zone-right'),
        document.getElementById('trick-zone-top'),
        document.getElementById('trick-zone-left'),
    ];

    /**
     * Die Anzeige des Punktestandes.
     *
     * @type {HTMLDivElement}
     */
    const _scoreDisplay = document.getElementById('score-display');

    /**
     * Hält eine Liste der Callbacks aller aktuell laufenden Animationen.
     *
     * @type {Set<Function>}
     */
    const _runningAnimationCallbacks = new Set();

    /**
     * Initialisiert den Page-Visibility-Handler.
     */
    function init() {
        // Ereignis abfangen, wenn die Seite unsichtbar bzw. sichtbar wird.
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'hidden') {
                // Die Seite ist unsichtbar geworden
                console.warn("Seite wurde unsichtbar. Beende alle laufenden Animationen sofort.");
                const callbacksToExecute = Array.from(_runningAnimationCallbacks); // konvertiere das Set in ein Array, da das Set durch die Events modifiziert wird
                _runningAnimationCallbacks.clear(); // leere das Set sofort, um Race Conditions zu vermeiden.
                callbacksToExecute.forEach(callback => { // rufe die Callback-Funktion manuell auf, da 'transitioncancel'- bzw 'animationcancel'-Event in diesem Fall nicht ausgelöst wird.
                    callback();
                });
            }
            else if (document.visibilityState === 'visible') {
                // Die Seite ist sichtbar geworden.
                console.warn("Seite wurde sichtbar.");
            }
        });
    }

    /**
     * Wrapper für addEventListener, der das Element registriert.
     *
     * @param {HTMLElement} element
     * @param {string} eventType - 'transitionend' oder 'animationend'
     * @param {Function} callback - Callback nach Abschluss der Animation.
     * @param {Function} [rAF] - (Optional) Callback für requestAnimationFrame().
     */
    function _addAnimationListener(element, eventType, callback, rAF) {
        _runningAnimationCallbacks.add(callback);

        element.addEventListener(`${eventType}end`, () => {
            // Nur ausführen, wenn der Callback noch im Set ist (verhindert doppelte Ausführung,
            // wenn `visibilitychange` und `transitionend` fast gleichzeitig feuern).
            if (_runningAnimationCallbacks.has(callback)) {
                _runningAnimationCallbacks.delete(callback);
                callback();
            }
        }, { once: true });

        element.addEventListener(`${eventType}cancel`, () => {
            // Nur ausführen, wenn der Callback noch im Set ist (verhindert doppelte Ausführung,
            // wenn `visibilitychange` und `transitionend` fast gleichzeitig feuern).
            if (_runningAnimationCallbacks.has(callback)) {
                _runningAnimationCallbacks.delete(callback);
                callback();
            }
        }, { once: true });

        if (rAF) {
            // rAF 1: Stellt sicher, dass der Startzustand (Position, Rotation) im DOM committed ist.
            requestAnimationFrame(() => {
                // rAF 2: Im *nächsten* Frame, wende die Ziel-Transformation an.
                // Dies gibt dem Browser garantiert die Chance, den Startzustand zu "sehen" und die Transition korrekt auszulösen.
                requestAnimationFrame(() => {
                    rAF();
                });
            });
        }
    }

    /**
     * Tauscht die Schupfkarten aller Spieler untereinander aus.
     *
     * @param {Function} [callback] - (Optional) Callback nach Abschluss der Animation.
     */
    function schupfCards(callback) {
        let completed = 0;
        for (let fromRelativeIndex= 0; fromRelativeIndex <= 3; fromRelativeIndex++) {
            for (let toRelativeIndex= 0; toRelativeIndex <= 3; toRelativeIndex++) {
                if (fromRelativeIndex !== toRelativeIndex) {
                    _schupfCard(fromRelativeIndex, toRelativeIndex, () => {
                        completed++;
                        if (completed === 12) {
                            if (typeof callback === 'function') {
                                callback();
                            }
                        }
                    });
                }
            }
        }
    }

    /**
     * Verschiebt eine Schupfkarte von einem Spieler zum anderen.
     *
     * @param {number} fromRelativeIndex - Relativer Index des Spielers, der die Tauschkarte abgibt.
     * @param {number} toRelativeIndex - Relativer Index des Spielers, der die Tauschkarte bekommt.
     * @param {Function} [callback] - (Optional) Callback nach Abschluss der Animation
     */
    function _schupfCard(fromRelativeIndex, toRelativeIndex, callback) {
        if (document.visibilityState !== 'visible' || _schupfZones[fromRelativeIndex].classList.contains("hidden") || _schupfZones[toRelativeIndex].classList.contains("hidden")) {
            // Schupf-Subzone ist nicht sichtbar
            if (typeof callback === 'function') {
                callback();
            }
            return;
        }

        // DOM-Element, das die Tauschkarte zeigt
        const cardElement = _schupfZones[fromRelativeIndex].querySelector(`.schupf-subzone:nth-child(${(4 + fromRelativeIndex - toRelativeIndex) % 4}) .card`);
        if (!cardElement) {
            // Schupf-Subzone ist leer
            if (typeof callback === 'function') {
                callback();
            }
            return;
        }

        // Position und aktuellen Skalierungsfaktor des Wrappers
        const wrapperRect = _wrapper.getBoundingClientRect(); // die Werte von getBoundingClientRect() sind skaliert!
        const wrapperScale = _wrapper.offsetWidth ? wrapperRect.width / _wrapper.offsetWidth : 1;

        // Startposition (relativ zum Wrapper)
        const startRect = cardElement.getBoundingClientRect();
        const startOffset = fromRelativeIndex === 1 || fromRelativeIndex === 3 ? 30 : 0; // 30 = (Kartenhöhe - Kartenbreite) / 2, entsteht durch die Drehung um 90 Grad um den Kartenmittelpunkt
        const startX = (startRect.left - wrapperRect.left) / wrapperScale + startOffset;
        const startY = (startRect.top - wrapperRect.top) / wrapperScale - startOffset;
        const startDeg = [0, -90, 180, 90][fromRelativeIndex];

        // Endpositionen (relativ zum Wrapper)
        // const targetContainer = _schupfZones[toRelativeIndex].querySelector(`.schupf-subzone:nth-child(${(4 + toRelativeIndex - fromRelativeIndex) % 4})`);
        // const endRect = targetContainer.getBoundingClientRect();
        // const endOffset = toRelativeIndex === 1 || toRelativeIndex === 3 ? 30 : 0; // 30 = (Kartenhöhe - Kartenbreite) / 2, entsteht durch die Drehung um 90 Grad um den Kartenmittelpunkt
        // const endX = (endRect.left - wrapperRect.left) / wrapperScale + endOffset;
        // const endY = (endRect.top - wrapperRect.top) / wrapperScale - endOffset;
        let endX = [540, 1170, 540, -90][toRelativeIndex]; // [1080/2, 1080+Kartenhöhe/2, 1080/2, -Kartenhöhe/2]
        let endY = [1920, 810, -180, 810][toRelativeIndex]; // [1920, 1920/2, -Kartenhöhe, 1920/2]
        const endDeg = [0, -90, 180, 90][toRelativeIndex];
        if (toRelativeIndex === 0) {
            const endRect = _schupfZones[0].querySelector(`.schupf-subzone:nth-child(${4 - fromRelativeIndex})`).getBoundingClientRect();
            endX = (endRect.left - wrapperRect.left) / wrapperScale;
            endY = (endRect.top - wrapperRect.top) / wrapperScale;
        }

        // Die Karte direkt in den Hauptcontainer legen, damit sie über allem fliegen kann.
        cardElement.classList.add('flying-card');
        cardElement.style.left = `${startX}px`;
        cardElement.style.top = `${startY}px`;
        cardElement.style.transform = `rotate(${startDeg}deg)`;
        _wrapper.appendChild(cardElement);

        let diffDeg = endDeg - startDeg;
        if (diffDeg === 270) {
            diffDeg = -90
        }
        else if (diffDeg === -270) {
            diffDeg = 90
        }

        // Event-Listener für das Ende der Transition
        _addAnimationListener(cardElement, 'transition', () => {
            cardElement.remove();
            console.log('cardElement.remove()', fromRelativeIndex, toRelativeIndex);
            if (typeof callback === 'function') {
                callback();
            }
        }, () => {
            cardElement.style.transform = `translate(${endX - startX}px, ${endY - startY}px) rotate(${startDeg + diffDeg}deg)`;
        });
    }

    /**
     * Nimmt den Stich vom Tisch.
     *
     * @param {number} toRelativeIndex - Relativer Index des Spielers, der die Karten bekommt.
     * @param {Function} [callback] - (Optional) Callback nach Abschluss der Animation.
     */
    function takeTrick(toRelativeIndex, callback) {
        let completed = 0;
        for (let fromRelativeIndex= 0; fromRelativeIndex <= 3; fromRelativeIndex++) {
            _takeTurns(fromRelativeIndex, toRelativeIndex, () => {
                completed++;
                console.log(`takeTrick: completed ${fromRelativeIndex} -> ${toRelativeIndex} (${completed}/${4})`);
                if (completed === 4) {
                    if (typeof callback === 'function') {
                        callback();
                    }
                }
            });
        }
    }

     /**
     * Nimmt die Spielzüge eines Spielers vom Tisch.
     *
     * @param {number} fromRelativeIndex - Relativer Index des Spielers, der die Karten abgibt.
     * @param {number} toRelativeIndex - Relativer Index des Spielers, der die Karten bekommt.
     * @param {Function} [callback] - (Optional) Callback nach Abschluss der Animation.
     */
    function _takeTurns(fromRelativeIndex, toRelativeIndex, callback) {
        if (document.visibilityState !== 'visible') {
            // die Seite ist nicht sichtbar
            if (typeof callback === 'function') {
                callback();
            }
            return;
        }

        const turnElements = _trickZones[fromRelativeIndex].querySelectorAll(".turn");
        if (!turnElements.length) {
            if (typeof callback === 'function') {
                console.log(`takeTrick: kein Stich von ${fromRelativeIndex}`);
                callback();
            }
            return;
        }

        console.log(`takeTrick: ${turnElements.length} Stiche von ${fromRelativeIndex}`);

        let completed = 0;

        // Alle Spielzüge des Spielers durchlaufen.
        turnElements.forEach(turnElement => {

            // Position und aktuellen Skalierungsfaktor des Wrappers
            const wrapperRect = _wrapper.getBoundingClientRect(); // die Werte von getBoundingClientRect() sind skaliert!
            const wrapperScale = _wrapper.offsetWidth ? wrapperRect.width / _wrapper.offsetWidth : 1;

            // Startposition (relativ zum Wrapper)
            const startRect = turnElement.getBoundingClientRect();
            const startOffset = fromRelativeIndex === 1 || fromRelativeIndex === 3 ? 90 : 0; // 30 = (Kartenhöhe - Kartenbreite) / 2, entsteht durch die Drehung um 90 Grad um den Kartenmittelpunkt
            const startX = (startRect.left - wrapperRect.left) / wrapperScale + startOffset;
            const startY = (startRect.top - wrapperRect.top) / wrapperScale - startOffset;
            const startDeg = [0, -90, 180, 90][fromRelativeIndex];

            // Endpositionen (relativ zum Wrapper)
            const endX = [540, 1170, 540, -90][toRelativeIndex]; // [1080/2, 1080+Kartenhöhe/2, 1080/2, -Kartenhöhe/2]
            const endY = [1920, 810, -180, 810][toRelativeIndex]; // [1920, 1920/2, -Kartenhöhe, 1920/2]
            const endDeg = [0, -90, 180, 90][toRelativeIndex];

            // Die Karte direkt in den Hauptcontainer legen, damit sie über allem fliegen kann.
            //turnElement = turnElement.cloneNode(true);
            turnElement.classList.add('flying-turn');
            turnElement.classList.remove('last');
            turnElement.style.left = `${startX}px`;
            turnElement.style.top = `${startY}px`;
            turnElement.style.transform = `rotate(${startDeg}deg)`;
            _wrapper.appendChild(turnElement);

            let diffDeg = endDeg - startDeg;
            if (diffDeg === 270) {
                diffDeg = -90
            }
            else if (diffDeg === -270) {
                diffDeg = 90
            }

            // Event-Listener für das Ende der Transition
            _addAnimationListener(turnElement, 'transition', () => {
                turnElement.remove();
                completed++;
                console.log(`takeTrick: ${completed} Stiche von ${fromRelativeIndex} an ${toRelativeIndex} fertig`);
                if (completed === turnElements.length) {
                    if (typeof callback === 'function') {
                        callback();
                    }
                }
            }, () => {
                turnElement.style.transform = `translate(${endX - startX}px, ${endY - startY}px) rotate(${startDeg + diffDeg}deg)`;
            });
        });
    }

    /**
     * Löst die Bomben-Animation aus.
     *
     * @param {Function} [callback] - (Optional) Callback nach Abschluss der Animation
     */
    function explodeBomb(callback) {
        if (document.visibilityState !== 'visible') {
            // die Seite ist nicht sichtbar
            if (typeof callback === 'function') {
                callback();
            }
            return;
        }
        const bombTextEl = document.createElement('div');
        bombTextEl.className = 'bomb-effect-text';
        bombTextEl.textContent = 'BOMBE!';
        _wrapper.appendChild(bombTextEl);
        _addAnimationListener(bombTextEl, 'animation', () => {
            bombTextEl.remove();
            if (typeof callback === 'function') {
                callback();
            }
        });
    }

    /**
     * Animiert die Punkteanzeige durch ein kurzes Aufblinken.
     *
     * @param {Function} [callback] - (Optional) Callback nach Abschluss der Animation
     *
     */
    function flashScoreDisplay(callback) {
        if (document.visibilityState !== 'visible') {
            // die Seite ist nicht sichtbar
            if (typeof callback === 'function') {
                callback();
            }
            return;
        }
        _scoreDisplay.classList.add('score-updated'); // die Animation wird durch das Hinzufügen der Klasse ausgelöst
        _addAnimationListener(_scoreDisplay, 'animation', () => {
            _scoreDisplay.classList.remove('score-updated');
            if (typeof callback === 'function') {
                callback();
            }
        });
    }

    // /**
    //  * Lässt ein Element pulsieren.
    //  *
    //  * @param {HTMLElement} element - Das Element, das pulsieren soll.
    //  * @param {boolean} enable - True, um die Animation zu starten, False, um sie zu stoppen.
    //  */
    // function pulseElement(element, enable) {
    //     if (!element) return;
    //     element.classList.toggle('is-pulsing', enable);
    // }

    // /**
    //  * Wendet einen Kartenstapel (dreht ihn von Vorder- zu Rückseite oder umgekehrt).
    //  *
    //  * HINWEIS: Erfordert eine spezifische HTML-Struktur:
    //  * @example
    //  * <div class="card-flipper">
    //  *     <div class="card-face front"></div>
    //  *     <div class="card-face back"></div>
    //  * </div>
    //  *
    //  * @param {HTMLElement} flipperElement - Das Elternelement, das die CSS-Klasse 'card-flipper' hat.
    //  */
    // function flipCard(flipperElement) {
    //     if (!flipperElement) return;
    //     flipperElement.classList.toggle('is-flipped');
    // }

    // /**
    //  * Entfernt eine Karte aus dem Bildschirm mit einer Animation.
    //  *
    //  * @param {HTMLElement} cardElement - Die Karte, die entfernt werden soll.
    //  * @param {Function} [callback] - (Optional) Callback nach Abschluss der Animation
    //  */
    // function removeCard(cardElement, callback) {
    //     cardElement.classList.add('is-removing');
    //     cardElement.addEventListener('transitionend', () => {
    //         cardElement.remove();
    //         if (typeof callback === 'function') {
    //             callback();
    //         }
    //     }, { once: true });
    // }

    // /**
    //  * Entfernt einen Kartenstapel aus dem Bildschirm mit einer Animation.
    //  *
    //  * @param {Array<HTMLElement>} cardElements - Ein Array von Karten, die entfernt werden sollen.
    //  * @param {Function} [callback] - (Optional) Callback nach Abschluss der Animation
    //  */
    // function removeCards(cardElements, callback) {
    //     let completed = 0;
    //     let n = cardElements.length;
    //     cardElements.forEach(cardElement => {
    //         removeCard(cardElement, () => {
    //             completed++;
    //             if (completed === n && typeof callback === 'function') {
    //                 callback();
    //             }
    //         });
    //     });
    // }

    // noinspection JSUnusedGlobalSymbols
    return {
        init,
        schupfCards,
        takeTrick,
        explodeBomb,
        flashScoreDisplay,
        //pulseElement,
        //flipCard,
        //removeCard,
        //removeCards,
    };
})();