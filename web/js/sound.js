/**
 * Verwaltet das Laden und Abspielen von Soundeffekten.
 */
const Sound = (() => {

    /**
     * Audio-Objekte.
     *
     * @type {Record<string, HTMLAudioElement>}
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
     * Gibt an, ob der Browser den Audio-Blocker aktiviert hat.
     *
     * Moderne Browser verhindern, dass Websites unaufgefordert Töne oder Videos abspielen, bis der Benutzer einmal mit der Seite interagiert hat.
     * Fehlermeldung: "play() failed because the user didn't interact with the document first."
     *
     * @type {boolean}
     */
    let _audioBlocked = false;

    /**
     * Verfügbare Audio-Dateien
     *
     * @type {Array<string>}
     */
    const _files = [
        'announce.ogg',
        'bomb.ogg',
        'play0.ogg',
        'play1.ogg',
        'play2.ogg',
        'play3.ogg',
        'schupf.ogg',
        'score.ogg',
        'select.ogg',
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
     * @param {Function} [callback] - (Optional) Callback nach Soundende.
     */
    function play(basename, callback) {
        if (!_enabled || document.visibilityState !== 'visible') {
            if (typeof callback === 'function') {
                callback();
            }
            return; // Sound ist deaktiviert bzw. die Seite ist nicht sichtbar
        }

        const audio = _audio[basename];
        if (!audio) {
            console.error(`Sound: '${basename}' ist nicht vorhanden.`);
            if (typeof callback === 'function') {
                callback();
            }
            return; // Sound-Datei nicht vorhanden
        }

        audio.addEventListener('ended', () => {
            console.debug(`Sound: '${basename}' ist fertig`);

            if (typeof callback === 'function') {
                callback();
            }
        });

        console.debug(`Sound: '${basename}'`);
        audio.currentTime = 0;
        audio.play().then(() => {
            if (_audioBlocked) {
                console.info("🎵 Sound: Audio erfolgreich gestartet nach Interaktion.");
                _audioBlocked = false;
            }
        }).catch(error => {
            if (error.name === 'NotAllowedError') {
                if (!_audioBlocked) {
                    console.warn("⚠️ Sound: Audio blockiert. Der Benutzer hat noch nicht mit dem Browser interagiert.");
                    _audioBlocked = true;
                }
            }
            else {
                console.error(`Sound: "${audio.src}" konnte nicht abgespielt werden:`, error.message);
            }
            if (typeof callback === 'function') {
                callback();
            }
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