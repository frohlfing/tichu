/**
 * Stellt Animationen bereit.
 */
const Animations = (() => {

    /**
     * Lässt einen Kartenstapel von einem Start- zu einem Endelement fliegen.
     *
     * @param {Cards} cardsData - Die Daten der Karten, die fliegen sollen (für die Bildanzeige).
     * @param {HTMLElement} fromElement - Das DOM-Element, von dem die Animation startet.
     * @param {HTMLElement} toElement - Das DOM-Element, bei dem die Animation endet.
     * @param {object} [options] - Zusätzliche Optionen.
     * @param {number} [options.stagger=50] - Zeitlicher Versatz zwischen den Karten in ms für einen Kaskadeneffekt.
     * @param {boolean} [options.rotate=false] - Ob die Karte während des Flugs um 90 Grad gedreht werden soll.
     * @param {string} [options.targetWidth='5em'] - Die Zielbreite der Karte.
     * @param {string} [options.targetHeight='7em'] - Die Zielhöhe der Karte.
     * @param {number} [options.duration=600] - Dauer der Animation in ms.
     */
    function flyCards(cardsData, fromElement, toElement, options = {}) {
        const {
            stagger = 50,
            rotate = false,
            targetWidth = '120px',
            targetHeight = '180px',
            duration = 600
        } = options;

        const gameWrapper = document.getElementById('game-wrapper');
        if (!gameWrapper || !fromElement || !toElement) {
            console.error("flyCards: Start- oder Endelement oder Wrapper nicht gefunden.");
            return;
        }

        const wrapperRect = gameWrapper.getBoundingClientRect();
        const startRect = fromElement.getBoundingClientRect();
        const endRect = toElement.getBoundingClientRect();

        cardsData.forEach((card, index) => {
            setTimeout(() => {
                const flyingCard = document.createElement('div');
                flyingCard.className = 'card flying-card';
                flyingCard.style.backgroundImage = `url('images/cards/${Lib.stringifyCard(card)}.png')`;

                // Setze die Transition-Dauer
                flyingCard.style.transition = `transform ${duration}ms ease-in-out, width ${duration}ms ease-in-out, height ${duration}ms ease-in-out`;

                // Startposition relativ zum Wrapper berechnen (zentriert im Start-Element)
                const startX = startRect.left - wrapperRect.left + (startRect.width / 2);
                const startY = startRect.top - wrapperRect.top + (startRect.height / 2);
                flyingCard.style.left = `${startX}px`;
                flyingCard.style.top = `${startY}px`;

                // Setze auch die Startgröße, um einen sauberen Übergang zu gewährleisten
                flyingCard.style.width = `${startRect.width}px`;
                flyingCard.style.height = `${startRect.height}px`;

                // Füge die Karte zum Wrapper hinzu, um die Skalierung zu erben
                gameWrapper.appendChild(flyingCard);

                // Nächsten Frame abwarten, um sicherzustellen, dass die Transition getriggert wird
                requestAnimationFrame(() => {
                    // Zielposition relativ zum Wrapper berechnen (zentriert im Ziel-Element)
                    const endX = endRect.left - wrapperRect.left + (endRect.width / 2);
                    const endY = endRect.top - wrapperRect.top + (endRect.height / 2);

                    const rotation = rotate ? 'rotate(90deg)' : 'rotate(0deg)';
                    flyingCard.style.width = targetWidth;
                    flyingCard.style.height = targetHeight;
                    // Transformation relativ zur Startposition innerhalb des Wrappers
                    //flyingCard.style.transform = `translate(${endX - startX}px, ${endY - startY}px) ${rotation}`;
                });

                // Element nach der Animation aufräumen
                setTimeout(() => {
                    //flyingCard.remove();
                }, duration + 50); // Ein kleiner Puffer nach der Animation

            }, index * stagger);
        });
    }


    // PoC-Code zum Testen in der Konsole
    function testFlyAnimation() {
        console.log("Starte Test-Animation...");

        // 1. Hole die DOM-Elemente
        const cardToAnimate = document.querySelector('#schupf-zone-top .schupf-subzone:nth-child(2) .card');
        const toContainer = document.querySelector('#schupf-zone-bottom .schupf-subzone:nth-child(2)');
        const gameWrapper = document.getElementById('game-wrapper');

        if (!cardToAnimate || !toContainer || !gameWrapper) {
            console.error("Konnte Start-, Ziel- oder Wrapper-Container nicht finden.");
            return;
        }

        // 2. Erstelle die fliegende Kopie
        const flyingCard = cardToAnimate; //.cloneNode(true);
        flyingCard.classList.add('flying-card'); // Füge die Animations-Styling-Klasse hinzu
        //flyingCard.style.transition = 'all 800ms ease-in-out'; // "all" für einfache Fehlersuche
        //flyingCard.style.transformOrigin = 'center center'; // Oft stabiler für Skalierung und Rotation

        // 3. Berechne Start- und Endpositionen RELATIV ZUM WRAPPER
        //const wrapperRect = gameWrapper.getBoundingClientRect();
        const startRect = cardToAnimate.getBoundingClientRect();
        const endRect = toContainer.getBoundingClientRect();

        // // Startposition der fliegenden Karte (obere linke Ecke)
        // const startX = startRect.left - wrapperRect.left;
        // const startY = startRect.top - wrapperRect.top;
        //
        // // Zielposition der fliegenden Karte (zentriert im Zielcontainer)
        // const endX = (endRect.left - wrapperRect.left) + (endRect.width / 2) - (startRect.width / 2);
        // const endY = (endRect.top - wrapperRect.top) + (endRect.height / 2) - (startRect.height / 2);

        // Startposition der fliegenden Karte (obere linke Ecke)
        const startX = startRect.left;
        const startY = startRect.top;

        // Zielposition der fliegenden Karte (zentriert im Zielcontainer)
        const endX = endRect.left; // + (endRect.width / 2) - (startRect.width / 2);
        const endY = endRect.top; // + (endRect.height / 2) - (startRect.height / 2);


        // 4. Initialisiere die fliegende Karte
        // Setze die absolute Position und die Größe der Karte
        flyingCard.style.left = `${startX}px`;
        flyingCard.style.top = `${startY}px`;
        flyingCard.style.width = `${startRect.width}px`;
        flyingCard.style.height = `${startRect.height}px`;
        flyingCard.style.transform = 'scale(1) rotate(0deg)'; // Expliziter Start-Transform

        // Füge die fliegende Karte zum Wrapper hinzu
        gameWrapper.appendChild(flyingCard);

        // 5. Starte die Animation im nächsten Frame
        requestAnimationFrame(() => {
            // Berechne die Skalierung, damit die Karte in den Zielcontainer passt
            const scaleX = endRect.width / startRect.width;
            const scaleY = endRect.height / startRect.height;
            const scale = Math.min(scaleX, scaleY); // Nimm die kleinere Skalierung, um das Seitenverhältnis zu wahren

            // Setze die Transformation für die Endposition
            // Wir verwenden transform für ALLES: Position, Skalierung, Rotation
            flyingCard.style.transform = `translate(${endX - startX}px, ${endY - startY}px) scale(${scale}) rotate(0deg)`;
        });

        // 6. Räume nach der Animation auf
        setTimeout(() => {
            console.log("Animation beendet, räume auf.");
            flyingCard.remove();
            // Optional: Entferne auch die temporäre Testkarte
            if (cardToAnimate.parentElement === fromContainer) {
               // fromContainer.innerHTML = ''; // Sicherster Weg, alle Kinder zu entfernen
            }
        }, 900); // Etwas länger als die Animationsdauer
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
        const gameWrapper = document.getElementById('game-wrapper');
        gameWrapper.classList.add('screen-shake-effect');
        gameWrapper.addEventListener('animationend', () => {
            gameWrapper.classList.remove('screen-shake-effect');
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
        flyCards,
        flipCard,
        removeCards,
        animateBomb,
        pulseElement,
        animateScoreUpdate,
        testFlyAnimation,
    };
})();