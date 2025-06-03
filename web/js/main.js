/**
 * Haupt-Einstiegspunkt der Tichu-Anwendung.
 *
 * Initialisiert den AppController, sobald das DOM geladen ist.
 */

/**
 * Wird ausgeführt, sobald das gesamte HTML-Dokument geladen und geparst wurde,
 * aber bevor externe Ressourcen wie Bilder vollständig geladen sind.
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log("MAIN: DOM vollständig geladen und geparst.");
    AppController.init();
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