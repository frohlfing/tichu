/**
 * Verwaltet das Laden und Abspielen von Soundeffekten.
 */
const SoundManager = (() => {
    const sounds = {}; // Speichert die Audio-Objekte.
    let masterVolume = 0.5; // Die globale Lautstärke für alle Sounds.
    let soundsEnabled = true; // Gibt an, ob Sounds aktiviert sind.

    /**
     * @const {object} soundFiles
     * @description Mapping von Sound-Namen zu Dateipfaden. Endungen sind .ogg.
     */
    const soundFiles = {
        // todo Sound-Files hinzufügen

        // --- Notification Events ---
        // player_joined0
        // player_left0
        // players_swapped
        //game_started
        round_started: 'sounds/shuffle.ogg',
        //hand_cards_dealt
        player_grand_announced_0: 'sounds/announce0.ogg', player_grand_announced_1: 'sounds/announce1.ogg', player_grand_announced_2: 'sounds/announce2.ogg', player_grand_announced_3: 'sounds/announce3.ogg',
        player_announced_0: 'sounds/announce0.ogg', player_announced_1: 'sounds/announce1.ogg', player_announced_2: 'sounds/announce2.ogg', player_announced_3: 'sounds/announce3.ogg',
        player_schupfed_0: 'sounds/schupf0.ogg', player_schupfed_1: 'sounds/schupf1.ogg', player_schupfed_2: 'sounds/schupf2.ogg', player_schupfed_3: 'sounds/schupf3.ogg',
        schupf_cards_dealt: 'sounds/dealout.ogg',
        player_passed_0: 'sounds/pass0.ogg', player_passed_1: 'sounds/pass1.ogg', player_passed_2: 'sounds/pass2.ogg', player_passed_3: 'sounds/pass3.ogg',
        player_played_0: 'sounds/play0.ogg', player_played_1: 'sounds/play1.ogg', player_played_2: 'sounds/play2.ogg', player_played_3: 'sounds/play3.ogg',
        player_bombed_0: 'sounds/bomb0.ogg', player_bombed_1: 'sounds/bomb1.ogg', player_bombed_2: 'sounds/bomb2.ogg', player_bombed_3: 'sounds/bomb3.ogg',
        // wish_made: 'sounds/wish_made.ogg',
        // wish_fulfilled: 'sounds/wish_fulfilled.ogg',
        trick_taken_0: 'sounds/take0.ogg', trick_taken_1: 'sounds/take1.ogg', trick_taken_2: 'sounds/take2.ogg', trick_taken_3: 'sounds/take3.ogg',
        // player_turn_changed
        // round_over: 'sounds/round_over.ogg',
        // game_over: 'sounds/game_over.ogg',

        // --- UI Events ---
        // buttonClick: 'sounds/ui_click.ogg',
        // cardSelect: 'sounds/ui_tap.ogg',
        // dialogOpen: 'sounds/dialog_open.ogg' // Beispiel
    };

    /**
     * Initialisiert den SoundManager und lädt alle definierten Sound-Dateien vor.
     */
    function init() {
        for (const key in soundFiles) {
            if (soundFiles.hasOwnProperty(key)) {
                sounds[key] = new Audio(soundFiles[key]);
                sounds[key].volume = masterVolume;
            }
        }
        const storedSoundsEnabled = localStorage.getItem('tichuSoundsEnabled');
        if (storedSoundsEnabled !== null) {
            soundsEnabled = storedSoundsEnabled === 'true';
        }
        const storedVolume = localStorage.getItem('tichuMasterVolume');
        if (storedVolume !== null) {
            setVolume(parseFloat(storedVolume));
        }
    }

    /**
     * Spielt einen Soundeffekt ab, falls Sounds aktiviert sind.
     * @param {string} soundKey - Der Schlüssel des Sounds aus `soundFiles`.
     */
    function playSound(soundKey) {
        if (soundsEnabled && sounds[soundKey]) {
            sounds[soundKey].currentTime = 0;
            sounds[soundKey].play().catch(error => {
                // console.warn(`Sound ${soundKey} konnte nicht abgespielt werden:`, error.message);
            });
        }
        else if (soundsEnabled && !sounds[soundKey]) {
            // console.warn(`SoundManager: Sound-Schlüssel '${soundKey}' nicht in soundFiles gefunden.`);
        }
    }

    /**
     * Spielt einen Sound für eine Server-Notification ab.
     * Versucht zuerst einen spielerspezifischen Sound (eventuellName_relativeIndex),
     * dann einen generischen Sound (eventName).
     * @param {string} eventName - Das Event (z.B. "player_played").
     * @param {int} eventBelongsToPlayerIndex - Der Index des Spielers, auf den sich das Event bezieht (-1 == das Event bezieht sich auf niemandem).
     */
    function playNotificationSound(eventName, eventBelongsToPlayerIndex = -1) {
        if (!soundsEnabled) {
            return;
        }
        if (soundFiles.hasOwnProperty(eventName)) {
            SoundManager.playSound(eventName);
        }
        else if (eventBelongsToPlayerIndex !== -1) {
            const relativeIdx = Helpers.getRelativePlayerIndex(eventBelongsToPlayerIndex);
            let soundKey = eventName + "_" + relativeIdx
            if (soundFiles.hasOwnProperty(soundKey)) {
                SoundManager.playSound(soundKey);
            }
        }
    }

    /**
     * Schaltet Sounds an oder aus und speichert die Einstellung im LocalStorage.
     * @param {boolean} enabled - True, um Sounds zu aktivieren, false zum Deaktivieren.
     */
    function setSoundsEnabled(enabled) {
        soundsEnabled = !!enabled;
        localStorage.setItem('tichuSoundsEnabled', soundsEnabled.toString());
    }

    /**
     * Gibt zurück, ob Sounds aktuell aktiviert sind.
     * @returns {boolean} True, wenn Sounds aktiviert sind, sonst false.
     */
    function areSoundsEnabled() {
        return soundsEnabled;
    }

    /**
     * Setzt die Master-Lautstärke für alle Sounds und speichert sie im LocalStorage.
     * @param {number} volume - Lautstärke von 0.0 (stumm) bis 1.0 (volle Lautstärke).
     */
    function setVolume(volume) {
        masterVolume = Math.max(0, Math.min(1, parseFloat(volume) || 0));
        for (const key in sounds) {
            if (sounds.hasOwnProperty(key) && sounds[key]) {
                sounds[key].volume = masterVolume;
            }
        }
        localStorage.setItem('tichuMasterVolume', masterVolume.toString());
    }

    /**
     * Gibt die aktuelle Master-Lautstärke zurück.
     * @returns {number} Die aktuelle Lautstärke (0.0 - 1.0).
     */
    function getVolume() {
        return masterVolume;
    }

    return {
        init,
        playSound,
        playNotificationSound,
        setSoundsEnabled,
        areSoundsEnabled,
        setVolume,
        getVolume
    };
})();