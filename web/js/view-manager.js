/**
 * Basisstruktur einer View.
 *
 * Jede View enthält mindestens die folgenden Funktionen.
 *
 * @typedef {Object} View
 * @property {function} init - Initialisiert die View.
 * @property {function} render - Rendert die View.
 * @property {function} show - Rendert die View und zeigt sie anschließend an.
 * @property {function} hide - Blendet die View aus.
 * @property {function} isVisible - Ermittelt, ob die View gerade angezeigt wird.
 */

/**
 * Schaltet zwischen den Views der Anwendung um.
 */
const ViewManager = (() => {
    /**
     * Der Name des aktuell angezeigten Views.
     *
     * @type {string|null} _currentViewName -
     */
    let _currentViewName = null;

    /**
     * Referenzen zu den Views.
     *
     * @property {View} loading - Die Ladeanzeige.
     * @property {LoginView} login - Der Login-Bildschirm.
     * @property {LobbyView} lobby - Der Lobby-Bildschirm.
     * @property {GameTableView} gameTable - Der Spieltisch-Bildschirm.
     */
    const _views = {};

    /**
     * Initialisiert den ViewManager.
     */
    function init() {
        // View-Module registrieren und initialisieren
        _views.loading = LoadingView;
        _views.loading.init();

        _views.login = LoginView;
        _views.login.init();

        _views.lobby = LobbyView;
        _views.lobby.init();

        _views.gameTable = GameTableView;
        _views.gameTable.init();

        // Initial den Ladebildschirm anzeigen, AppController entscheidet dann weiter
        _views.loading.show();
    }

    /**
     * Zeigt einen bestimmten View an und blendet andere aus.
     *
     * @param {string} viewName - Der Name des Views, der angezeigt werden soll ('loading', 'login', 'lobby', 'gameTable').
     */
    function toggleView(viewName) {
        if (!_views.hasOwnProperty(viewName)) {
            console.error(`VIEWMGR: View '${viewName}' nicht gefunden.`);
            return;
        }

        if (_currentViewName === viewName && _views[viewName].isVisible()) {
            // Die View ist bereits aktiv, aber wir rendern trotzdem (es könnten sich Daten geändert haben).
            _views[viewName].render();
            return;
        }

        // Alle Views ausblenden
        for (const key in _views) {
            if (_views.hasOwnProperty(key)) {
                _views[key].hide();
            }
        }

        // Gewünschten View anzeigen
        _views[viewName].render();
        _views[viewName].show()
        _currentViewName = viewName;
    }

    /**
     * Wird vom AppController aufgerufen, wenn sich der globale Spielzustand geändert hat.
     * Stößt ein Neu-Rendern des aktuellen Views an.
     */
    function renderCurrentView() {
        if (_currentViewName) {
            _views[_currentViewName].render();
        }
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
        toggleView,
        renderCurrentView,
        getCurrentViewName
    };
})();