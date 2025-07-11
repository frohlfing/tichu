    /**
 * Haupt-Einstiegspunkt der Tichu-Anwendung.
 *
 * Initialisiert den AppController, sobald das DOM geladen ist.
 */

/**
 * Skaliert den #game-wrapper, um das 1080x1920 Seitenverhältnis beizubehalten und ihn in den verfügbaren Browser-Viewport einzupassen.
 */
function scaleGameWrapper() {
    const wrapper = document.getElementById('game-wrapper');
    if (!wrapper) {
        console.error("Main: #game-wrapper nicht im DOM gefunden!");
        return;
    }
    const targetWidth = 1080;
    const targetHeight = 1920;
    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;
    const scaleX = windowWidth / targetWidth;
    const scaleY = windowHeight / targetHeight;
    const scale = Math.min(scaleX, scaleY); // Wählt den kleineren Skalierungsfaktor, um alles sichtbar zu halten
    wrapper.style.transform = `scale(${scale})`;
    wrapper.top = (windowHeight - targetHeight) / 2;
    wrapper.left = (windowHeight - targetWidth) / 2;
}

/**
 * Wird ausgeführt, sobald das gesamte HTML-Dokument geladen und geparst wurde,
 * aber bevor externe Ressourcen wie Bilder vollständig geladen sind.
 */
document.addEventListener('DOMContentLoaded', () => {
    // Skalierung initial aufrufen, falls der Wrapper schon im DOM ist
    // (wird aber auch von window.onload abgedeckt)
    AppController.init();
    scaleGameWrapper(); // Initial skalieren

    // Bot aktivieren, falls gewünscht
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('bot') === 'true') {
        Bot.setEnabled(true);
    }
});

window.addEventListener('load', () => {
    scaleGameWrapper(); // Erneut skalieren, falls sich Dimensionen durch späte Ladevorgänge geändert haben
});

window.addEventListener('resize', () => {
    scaleGameWrapper();
});

/**
 * Wird ausgeführt, wenn die gesamte Seite inklusive aller Ressourcen (Bilder, Stylesheets etc.) vollständig geladen ist.
 * Nützlich für Dinge, die erst nach dem Laden aller Assets passieren sollen.
 */
window.onload = () => {
    // Hier könnten z.B. Sounds vorgeladen werden, falls nicht schon in SoundManager.init()
};