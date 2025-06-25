/**
 * Ladeanzeige
 *
 * @type {View}
 */
const LoadingView = (() => {

    /**
     * Der Container des Loading-Bildschirms.
     *
     * @type {HTMLElement}
     */
    const _viewContainer = document.getElementById('loading-screen');

    /**
     * Initialisiert die Ladeanzeige.
     */
    function init() {
    }

    /**
     * Rendert die Ladeanzeige.
     */
    function render() {
    }

    /**
     * Rendert die Ladeanzeige und zeigt sie anschließend an.
     */
    function show() {
        render();
        _viewContainer.classList.add('active');
    }

    /**
     * Blendet die Ladeanzeige aus.
     */
    function hide() {
        _viewContainer.classList.remove('active');
    }

    /**
     * Ermittelt, ob die Ladeanzeige gerade angezeigt wird.
     *
     * @returns {boolean}
     */
    function isVisible() {
        return _viewContainer.classList.contains('active');
    }

    return {
        init,
        render,
        show,
        hide,
        isVisible
    };
})();