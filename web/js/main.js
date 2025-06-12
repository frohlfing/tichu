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
        console.error("MAIN: #game-wrapper nicht im DOM gefunden für Skalierung.");
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
    console.log(`MAIN: Game-Wrapper skaliert auf: ${scale.toFixed(3)} (Win: ${windowWidth}x${windowHeight})`);
}

/**
 * Wird ausgeführt, sobald das gesamte HTML-Dokument geladen und geparst wurde,
 * aber bevor externe Ressourcen wie Bilder vollständig geladen sind.
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log("MAIN: DOM vollständig geladen und geparst.");
    // Skalierung initial aufrufen, falls der Wrapper schon im DOM ist
    // (wird aber auch von window.onload abgedeckt)
    AppController.init();
    scaleGameWrapper(); // Initial skalieren
});

window.addEventListener('load', () => {
    console.log("MAIN: Seite vollständig geladen (inkl. Ressourcen).");
    scaleGameWrapper(); // Erneut skalieren, falls sich Dimensionen durch späte Ladevorgänge geändert haben
});

window.addEventListener('resize', () => {
    // console.log("MAIN: Fenstergröße geändert."); // Kann sehr oft feuern
    scaleGameWrapper();
});

/**
 * Optional: Wird ausgeführt, wenn die gesamte Seite inklusive aller Ressourcen
 * (Bilder, Stylesheets etc.) vollständig geladen ist.
 * Nützlich für Dinge, die erst nach dem Laden aller Assets passieren sollen.
 */
// window.onload = () => {
//     console.log("MAIN: Seite vollständig geladen (inkl. Ressourcen).");
//     // Hier könnten z.B. Sounds vorgeladen werden, falls nicht schon in SoundManager.init()
// };