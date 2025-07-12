/**
 * Stellt Animationen bereit.
 */
const Animations = (() => {

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
     * Tauscht die Schupfkarten aller Spieler untereinander aus.
     *
     * @param {Function} [callback] - (Optional) Callback nach Abschluss der Animation.
     */
    function schupf(callback) {
        let completed = 0;
        for (let fromRelativeIndex=0; fromRelativeIndex <= 3; fromRelativeIndex++) {
            for (let toRelativeIndex=0; toRelativeIndex <= 3; toRelativeIndex++) {
                if (fromRelativeIndex !== toRelativeIndex) {
                    _schupfCard(fromRelativeIndex, toRelativeIndex, () => {
                        completed++;
                        if (completed === 12 && typeof callback === 'function') {
                            callback();
                        }
                    });
                }
            }
        }

        // setTimeout(() => {
        //     console.log("Animation beendet, räume auf.");
        // }, 2000); // etwas länger als die Animationsdauer (die Dauer ist in der CSS-Klasse .flying-card definiert)
    }

    /**
     * Verschiebt eine Schupfkarte von einem Spieler zum anderen.
     *
     * @param {number} fromRelativeIndex - Relativer Index des Spielers, der die Tauschkarte abgibt.
     * @param {number} toRelativeIndex - Relativer Index des Spielers, der die Tauschkarte bekommt.
     * @param {Function} [callback] - (Optional) Callback nach Abschluss der Animation
     */
    function _schupfCard(fromRelativeIndex, toRelativeIndex, callback) {
        // DOM-Element, das die Tauschkarte zeigt
        const cardElement = _schupfZones[fromRelativeIndex].querySelector(`.schupf-subzone:nth-child(${(4 + fromRelativeIndex - toRelativeIndex) % 4}) .card`);
        if (!cardElement) {
            // Schupf-Subzone ist leer
            if (typeof callback === 'function') {
                callback();
            }
            return;
        }

        // Container, in der die Tauschkarte abgelegt werden soll
        const targetContainer = _schupfZones[toRelativeIndex].querySelector(`.schupf-subzone:nth-child(${(4 + toRelativeIndex - fromRelativeIndex) % 4})`);

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
        const endRect = targetContainer.getBoundingClientRect();
        const endOffset = toRelativeIndex === 1 || toRelativeIndex === 3 ? 30 : 0; // 30 = (Kartenhöhe - Kartenbreite) / 2, entsteht durch die Drehung um 90 Grad um den Kartenmittelpunkt
        const endX = (endRect.left - wrapperRect.left) / wrapperScale + endOffset;
        const endY = (endRect.top - wrapperRect.top) / wrapperScale - endOffset;
        const endDeg = [0, -90, 180, 90][toRelativeIndex];

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
        cardElement.addEventListener('transitionend', () => {
            if (typeof callback === 'function') {
                cardElement.remove();
                callback();
            }
        }, { once: true });

        // Animation im nächsten Frame starten
        //const startTime = document.timeline.currentTime;
        requestAnimationFrame(_timestamp => { // rAF sagt dem Browser: "Bevor du den nächsten Frame zeichnest, führe diese Funktion aus."
            //const elapsed = timestamp - startTime;
            cardElement.style.transform = `translate(${endX - startX}px, ${endY - startY}px) rotate(${startDeg + diffDeg}deg)`;
        });
    }

    /**
     * Wendet einen Kartenstapel (dreht ihn von Vorder- zu Rückseite oder umgekehrt).
     *
     * HINWEIS: Erfordert eine spezifische HTML-Struktur:
     * @example
     * <div class="card-flipper">
     *     <div class="card-face front"></div>
     *     <div class="card-face back"></div>
     * </div>
     *
     * @param {HTMLElement} flipperElement - Das Elternelement, das die CSS-Klasse 'card-flipper' hat.
     */
    function flipCard(flipperElement) {
        if (!flipperElement) return;
        flipperElement.classList.toggle('is-flipped');
    }

    /**
     * Entfernt einen Kartenstapel aus dem Bildschirm mit einer Animation.
     *
     * @param {Array<HTMLElement>} cardElements - Ein Array von Karten-DOM-Elementen, die entfernt werden sollen.
     */
    function removeCards(cardElements) {
        cardElements.forEach(element => {
            element.classList.add('is-removing');
            // Element nach der Animation aus dem DOM entfernen
            element.addEventListener('transitionend', () => {
                element.remove();
            }, { once: true });
        });
    }

    /**
     * Löst die Bomben-Animation aus.
     */
    function animateBomb() {
        // 1. Screen-Shake-Effekt
        const wrapper = document.getElementById('wrapper');
        wrapper.classList.add('screen-shake-effect');
        wrapper.addEventListener('animationend', () => {
            wrapper.classList.remove('screen-shake-effect');
        }, { once: true });

        // 2. "BOMBE!"-Text-Effekt
        const bombTextEl = document.createElement('div');
        bombTextEl.className = 'bomb-effect-text';
        bombTextEl.textContent = 'BOMBE!';
        document.body.appendChild(bombTextEl);

        // 3. Sound abspielen
        SoundManager.playSound('bomb'); // Annahme: Es gibt einen allgemeinen Bombensound

        // 4. Aufräumen
        bombTextEl.addEventListener('animationend', () => {
            bombTextEl.remove();
        }, { once: true });
    }

    /**
     * Lässt ein Element pulsieren.
     *
     * @param {HTMLElement} element - Das Element, das pulsieren soll.
     * @param {boolean} enable - True, um die Animation zu starten, False, um sie zu stoppen.
     */
    function pulseElement(element, enable) {
        if (!element) return;
        element.classList.toggle('is-pulsing', enable);
    }

    /**
     * Animiert die Punkteanzeige durch einen kurzen "Blitz"-Effekt.
     *
     * @param {HTMLElement} scoreElement - Das DOM-Element der Punkteanzeige.
     */
    function animateScoreUpdate(scoreElement) {
        if (!scoreElement) return;
        // Die Animation wird durch das Hinzufügen der Klasse ausgelöst.
        // Wir entfernen die Klasse nach der Animation wieder, damit sie erneut ausgelöst werden kann.
        scoreElement.classList.add('score-updated');
        scoreElement.addEventListener('animationend', () => {
            scoreElement.classList.remove('score-updated');
        }, { once: true });
    }

    // noinspection JSUnusedGlobalSymbols
    return {
        schupf,
        flipCard,
        removeCards,
        animateBomb,
        pulseElement,
        animateScoreUpdate,
    };
})();