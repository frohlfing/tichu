/**
 * Verwaltet das Laden und Abspielen von Soundeffekten.
 */
const Sound = (() => {

    /**
     * Audio-Objekte.
     *
     * @type {Object.<string, HTMLAudioElement>}
     */
    const _audio = {};

    /**
     * Gibt an, ob Sounds aktiviert sind.
     *
     * @type {boolean}
     */
    let _enabled =  (localStorage.getItem('tichuSoundsEnabled') || 'true').toLowerCase() === 'true';

    /**
     * Die Master-Lautstärke von 0.0 (stumm) bis 1.0 (volle Lautstärke).
     *
     * @type {number}
     */
    let _volume = parseFloat(localStorage.getItem('tichuMasterVolume') || '0.5');

    /**
     * Verfügbare Audio-Dateien
     *
     * @type {Array<string>}
     */
    const _files = [
        'announce.ogg',
        'bomb.ogg',
        'chips.ogg',
        'click.ogg',
        'dealout.ogg',
        'move.ogg',
        'pass0.ogg', 'pass1.ogg', 'pass2.ogg', 'pass3.ogg',
        'play0.ogg', 'play1.ogg', 'play2.ogg', 'play3.ogg',
        'schupf0.ogg', 'schupf1.ogg', 'schupf2.ogg', 'schupf3.ogg',
        'shuffle.ogg',
        'take.ogg',
    ]

    /**
     * Initialisiert das Sound-Modul und lädt alle definierten Sound-Dateien vor.
     */
    function init() {
        for (let filename of _files) {
            const basename = filename.substring(0, filename.lastIndexOf('.'));
            _audio[basename] = new Audio(`sounds/${filename}`);
            _audio[basename].volume = _volume;
        }
    }

    /**
     * Spielt einen Soundeffekt ab.
     *
     * @param {string} basename - Der Name der Audiodatei ohne Erweiterung.
     */
    function play(basename) {
        if (!_enabled) {
            return;
        }

        const audio = _audio[basename];
        if (!audio) {
            console.error(`Sound: '${basename}' ist unbekannt.`);
            return;
        }

        audio.currentTime = 0;
        audio.play().catch(error => {
            console.error(`Sound: "${audio.src}" konnte nicht abgespielt werden:`, error.message);
        });
    }

    /**
     * Schaltet Sounds an oder aus und speichert die Einstellung im LocalStorage.
     *
     * @param {boolean} enabled - True, um Sounds zu aktivieren, false zum Deaktivieren.
     */
    function setEnabled(enabled) {
        _enabled = !!enabled;
        localStorage.setItem('tichuSoundsEnabled', _enabled.toString());
    }

    /**
     * Gibt an, ob Sounds aktuell aktiviert sind.
     *
     * @returns {boolean} True, wenn Sounds aktiviert sind, sonst false.
     */
    function isEnabled() {
        return _enabled;
    }

    /**
     * Setzt die Master-Lautstärke für alle Sounds und speichert sie im LocalStorage.
     *
     * @param {number} volume - Lautstärke von 0.0 (stumm) bis 1.0 (volle Lautstärke).
     */
    function setVolume(volume) {
        _volume = Math.max(0, Math.min(1, volume));
        for (const key in _audio) {
            if (_audio.hasOwnProperty(key) && _audio[key]) {
                _audio[key].volume = _volume;
            }
        }
        localStorage.setItem('tichuMasterVolume', _volume.toString());
    }

    /**
     * Gibt die aktuelle Master-Lautstärke zurück.
     *
     * @returns {number} Die aktuelle Lautstärke (0.0 - 1.0).
     */
    function getVolume() {
        return _volume;
    }

    // noinspection JSUnusedGlobalSymbols
    return {
        init,
        play,
        setEnabled,
        isEnabled,
        setVolume,
        getVolume
    };
})();