/**
 * Basisstruktur einer View.
 *
 * Jede View enthält mindestens die folgenden Funktionen.
 *
 * @typedef {Object} View
 * @property {Function} init - Initialisiert die View.
 * @property {Function} render - Rendert die View.
 */

/**
 * Schaltet zwischen den Views der Anwendung um.
 */
const ViewManager = (() => {

    /**
     * Die DOM-Container und Referenzen zu den View-Modulen.
     *
     * @type {Record<string, {container: HTMLElement, view: View}>}
     */
    const _subscreens = {
        loading: {
            container: document.getElementById('loading-screen'),
            view: LoadingView
        },
        login: {
            container: document.getElementById('login-screen'),
            view: LoginView
        },
        lobby: {
            container: document.getElementById('lobby-screen'),
            view: LobbyView
        },
        table: {
            container: document.getElementById('table-screen'),
            view: TableView
        },
    };

    /**
     * Initialisiert den ViewManager.
     */
    function init() {
        // View-Module initialisieren und aktuelle View rendern.
        for (const key in _subscreens) {
            if (_subscreens.hasOwnProperty(key)) {
                _subscreens[key].view.init();
                if (isVisible(key)) {
                    _subscreens[key].view.render();
                }
            }
        }
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
     * Zeigt eine bestimmte View an und blendet andere aus.
     *
     * @param {string} key - Schlüssel der View ('loading', 'login', 'lobby', 'table').
     */
    function _showView(key) {
        if (!_subscreens.hasOwnProperty(key)) {
            return;
        }

        if (isVisible(key)) {
            // die View ist bereits aktiv, also nur rendern
            _subscreens[key].view.render();
        }
        else {
            // alle Views ausblenden
            for (const k in _subscreens) {
                if (_subscreens.hasOwnProperty(k)) {
                    _subscreens[k].container.classList.remove('active'); // hide
                }
            }

            // gewünschte View anzeigen
            _subscreens[key].view.render();
            _subscreens[key].container.classList.add('active'); // show
        }

        EventBus.emit("view:rendered", {viewName: key});
    }

    /**
     * Ermittelt, ob die angegebene View gerade angezeigt wird.
     *
     * @param {string} key - Schlüssel der View ('loading', 'login', 'lobby', 'table').
     * @returns {boolean} True, wenn die View gerade angezeigt wird, sonst false.
     */
    function isVisible(key) {
        return _subscreens[key].container.classList.contains('active');
    }

    return {
        init,
        showLoadingView,
        showLoginView,
        showLobbyView,
        showTableView,
        isVisible,
    };
})();