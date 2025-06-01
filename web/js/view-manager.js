// js/view-manager.js

/**
 * @module ViewManager
 * Verantwortlich für das Verwalten und Umschalten der Haupt-Views der Anwendung (Login, Lobby, Spieltisch).
 * Ruft die Render-Methoden der jeweiligen Views auf und reagiert auf Zustandsänderungen.
 */
const ViewManager = (() => {
    /** @let {string|null} _currentViewName - Der Name des aktuell angezeigten Views. */
    let _currentViewName = null;
    /** @const {object} _viewElements - Referenzen zu den DOM-Elementen der Haupt-Views. */
    const _viewElements = {};
    /** @const {object} _viewModules - Referenzen zu den Modulen der Haupt-Views. */
    const _viewModules = {};

    /**
     * Initialisiert den ViewManager.
     * Sammelt Referenzen zu den View-DOM-Elementen und View-Modulen.
     * Zeigt initial den Ladebildschirm (oder einen anderen Start-View).
     */
    function init() {
        console.log("VIEWMGR: Initialisiere ViewManager...");
        // DOM-Elemente der Views sammeln
        _viewElements.loading = document.getElementById('loading-screen');
        _viewElements.login = document.getElementById('login-screen');
        _viewElements.lobby = document.getElementById('lobby-screen');
        _viewElements.gameTable = document.getElementById('game-table-screen');

        // View-Module registrieren und initialisieren
        // Die init-Methoden der View-Module sollten ihre internen DOM-Referenzen holen
        // und Event-Listener setzen, die spezifisch für diesen View sind.
        _viewModules.login = LoginView;
        _viewModules.login.init(); // LoginView eigene Initialisierung (z.B. Form-Listener)

        _viewModules.lobby = LobbyView;
        _viewModules.lobby.init();

        _viewModules.gameTable = GameTableView;
        _viewModules.gameTable.init();

        // Initial den Ladebildschirm anzeigen, AppController entscheidet dann weiter
        showView('loading');
    }

    /**
     * Zeigt einen bestimmten View an und blendet andere aus.
     * Ruft die `render`-Methode des anzuzeigenden Views auf.
     * @param {string} viewName - Der Name des Views, der angezeigt werden soll ('loading', 'login', 'lobby', 'gameTable').
     */
    function showView(viewName) {
        if (!viewName || !_viewElements[viewName]) {
            console.error(`VIEWMGR: View '${viewName}' nicht gefunden.`);
            return;
        }

        if (_currentViewName === viewName && _viewElements[viewName].classList.contains('active')) {
            // console.log(`VIEWMGR: View '${viewName}' ist bereits aktiv.`);
            // Trotzdem rendern, falls sich Daten geändert haben aber der View derselbe bleibt
            if (_viewModules[viewName] && typeof _viewModules[viewName].render === 'function') {
                _viewModules[viewName].render();
            }
            return;
        }

        console.log(`VIEWMGR: Zeige View '${viewName}'.`);

        // Alle Views ausblenden
        for (const key in _viewElements) {
            if (_viewElements.hasOwnProperty(key) && _viewElements[key]) {
                _viewElements[key].classList.remove('active');
                // Optional: 'hide' Methode des Moduls aufrufen, falls vorhanden
                if (_currentViewName === key && _viewModules[key] && typeof _viewModules[key].hide === 'function') {
                    _viewModules[key].hide();
                }
            }
        }

        // Gewünschten View anzeigen
        _viewElements[viewName].classList.add('active');
        _currentViewName = viewName;

        // `show` und `render` Methode des neuen View-Moduls aufrufen, falls vorhanden
        if (_viewModules[viewName]) {
            if (typeof _viewModules[viewName].show === 'function') {
                _viewModules[viewName].show(); // Für spezielle Logik beim Anzeigen
            }
            if (typeof _viewModules[viewName].render === 'function') {
                _viewModules[viewName].render(); // Daten in den View laden/aktualisieren
            }
        }
    }

    /**
     * Wird vom AppController aufgerufen, wenn sich der globale Spielzustand geändert hat.
     * Stößt ein Neu-Rendern des aktuellen Views an.
     * Diese Funktion kann erweitert werden, um basierend auf dem State auch View-Wechsel auszulösen.
     */
    function updateViewsBasedOnState() {
        // console.log("VIEWMGR: updateViewsBasedOnState aufgerufen für View:", _currentViewName);
        if (_currentViewName && _viewModules[_currentViewName] && typeof _viewModules[_currentViewName].render === 'function') {
            _viewModules[_currentViewName].render();
        }
        // Hier könnte auch Logik stehen, um basierend auf State.getPublicState().current_phase
        // automatisch den View zu wechseln, z.B. von Lobby zu GameTable.
        // Dies wird aber aktuell eher durch explizite Aufrufe von showView() im AppController gehandhabt.
    }

    /**
     * Gibt den Namen des aktuell aktiven Views zurück.
     * @returns {string|null}
     */
    function getCurrentViewName() {
        return _currentViewName;
    }

    return {
        init,
        showView,
        updateViewsBasedOnState,
        getCurrentViewName
    };
})();