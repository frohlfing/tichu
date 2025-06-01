// js/sound-manager.js

/**
 * @module SoundManager
 * Verwaltet das Laden und Abspielen von Soundeffekten.
 */
const SoundManager = (() => {
    /** @const {object} sounds - Speichert die Audio-Objekte. */
    const sounds = {};
    /** @let {number} masterVolume - Die globale Lautstärke für alle Sounds. */
    let masterVolume = 0.5; // Standardlautstärke (0.0 bis 1.0)
    /** @let {boolean} soundsEnabled - Gibt an, ob Sounds aktiviert sind. */
    let soundsEnabled = true;

    /**
     * @const {object} soundFiles
     * @description Mapping von Sound-Namen zu Dateipfaden. Endungen sind .ogg.
     */
    const soundFiles = {
        schuffle: 'sounds/schuffle.ogg', dealout: 'sounds/dealout.ogg',
        schupf0: 'sounds/schupf0.ogg', schupf1: 'sounds/schupf1.ogg', schupf2: 'sounds/schupf2.ogg', schupf3: 'sounds/schupf3.ogg',
        play0: 'sounds/play0.ogg', play1: 'sounds/play1.ogg', play2: 'sounds/play2.ogg', play3: 'sounds/play3.ogg',
        take0: 'sounds/take0.ogg', take1: 'sounds/take1.ogg', take2: 'sounds/take2.ogg', take3: 'sounds/take3.ogg',
        bomb0: 'sounds/bomb0.ogg', bomb1: 'sounds/bomb1.ogg', bomb2: 'sounds/bomb2.ogg', bomb3: 'sounds/bomb3.ogg',
        pass0: 'sounds/pass0.ogg', pass1: 'sounds/pass1.ogg', pass2: 'sounds/pass2.ogg', pass3: 'sounds/pass3.ogg',
        announce: 'sounds/announce.ogg', // Für Tichu-Ansagen
        // Beispiel UI-Sounds, falls benötigt und vorhanden:
        // cardSelect: 'sounds/ui_tap.ogg',
        // buttonClick: 'sounds/ui_click.ogg'
    };

    /**
     * Initialisiert den SoundManager und lädt alle definierten Sound-Dateien vor.
     * Lädt auch gespeicherte Sound-Einstellungen aus dem LocalStorage.
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
     * @param {string} soundName - Der Name des Sounds (Schlüssel in `soundFiles`).
     */
    function playSound(soundName) {
        if (soundsEnabled && sounds[soundName]) {
            sounds[soundName].currentTime = 0;
            sounds[soundName].play().catch(error => {
                // console.warn(`Sound ${soundName} konnte nicht abgespielt werden:`, error.message);
            });
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
        setSoundsEnabled,
        areSoundsEnabled,
        setVolume,
        getVolume
    };
})();