/**
 * Basisstruktur einer View.
 *
 * Jede View enthält mindestens die folgenden Funktionen.
 *
 * todo show() und hide() aus der View rausnehmen. Dies sollte nur der View-Manager machen dürfen.
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
     * @property {LoadingView} loading - Die Ladeanzeige.
     * @property {LoginView} login - Der Login-Bildschirm.
     * @property {LobbyView} lobby - Der Lobby-Bildschirm.
     * @property {TableView} table - Der Spieltisch-Bildschirm.
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

        _views.table = TableView;
        _views.table.init();

        // for (const name in _views) {
        //     if (_views.hasOwnProperty(name)) {
        //         _views[name].init();
        //     }
        // }

        // Aktuelle View rendern
        for (const name in _views) {
            if (_views.hasOwnProperty(name) && _views[name].isVisible()) {
                _views[name].render();
                _currentViewName = name;
                break;
            }
        }
    }

    /**
     * Gibt die gewünschte View zurück.
     *
     * @param {string} viewName - Name der View ("loading", "login", "lobby" oder "table").
     * @returns {View} Die View.
     */
    function getViewByName(viewName) {
        return _views[viewName];
    }

    /**
     * Zeigt die Loading-View an und blendet die andere aus.
     */
    function showLoadingView() {
        _showView("loading");
    }

    /**
     * Zeigt die Login-View an und blendet die andere aus.
     */
    function showLoginView() {
        _showView("login");
    }

    /**
     * Zeigt die Lobby-View an und blendet die andere aus.
     */
    function showLobbyView() {
        _showView("lobby");
    }

    /**
     * Zeigt die Table-View an und blendet die andere aus.
     */
    function showTableView() {
        _showView("table");
    }

    /**
     * Zeigt einen bestimmten View an und blendet andere aus.
     *
     * @param {string} viewName - Der Name des Views, der angezeigt werden soll ('loading', 'login', 'lobby', 'table').
     */
    function _showView(viewName) {
        if (!_views.hasOwnProperty(viewName)) {
            return;
        }

        if (_currentViewName === viewName && _views[viewName].isVisible()) {
            // Die View ist bereits aktiv, aber wir rendern trotzdem (es könnten sich Daten geändert haben).
            _views[viewName].render();
        }
        else {
            // Alle Views ausblenden
            for (const name in _views) {
                if (_views.hasOwnProperty(name)) {
                    _views[name].hide();
                }
            }

            // Gewünschten View anzeigen
            _views[viewName].show();
            _currentViewName = viewName;
        }

        EventBus.emit("view:rendered", {viewName: viewName});
    }

    return {
        init,
        getViewByName,
        showLoadingView,
        showLoginView,
        showLobbyView,
        showTableView,
    };
})();