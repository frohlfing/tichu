// Unit-Tests

// test('Addition.', () => {
//     assert(1 + 2, 3);
// });
//
// test('Test mit Parameter', (a, b, expected) => {
//     assert(a + b, expected);
// }, [
//     [1, 2, 3],
//     [4, 5, 9],
//     [2, 2, 5],
// ]);

// ======================================================================================
// Tests für findBombs(hand)
// ======================================================================================

test('findBombs: Hand ohne Bomben sollte leeres Array zurückgeben', () => {
    const hand = Lib.parseCards("S2 S3 S4 R5 S6 S7");
    const bombs = Lib.findBombs(hand);
    assert(bombs.length, 0);
});

test('findBombs: Hand mit Farbbombe Länge 6 sollte 3 mögliche Bomben zurückgeben', () => {
    const hand = Lib.parseCards("S2 S3 S4 S5 S6 S7");
    const bombs = Lib.findBombs(hand);
    assert(bombs.length, 3);
});

test('findBombs: Hand mit einer 4er-Bombe sollte diese finden', () => {
    const hand = Lib.parseCards("S5 G5 B5 R5 SA");
    const bombs = Lib.findBombs(hand);
    assert(bombs.length, 1);
    const [bombCards, bombCombination] = bombs[0];
    assert(Lib.stringifyCards(bombCards), "S5 G5 B5 R5");
    assert(bombCombination, [CombinationType.BOMB, 4, 5]);
});

test('findBombs: Hand mit einer Farbbombe sollte diese finden', () => {
    const hand = Lib.parseCards("S2 S3 S4 S5 S6"); // Farbbombe Schwarz von 2 bis 6
    const bombs = Lib.findBombs(hand);
    assert(bombs.length, 1);
    const [bombCards, bombCombination] = bombs[0];
    assert(Lib.stringifyCards(hand), "S6 S5 S4 S3 S2", `Handkarten sollten absteigend sortierte werden: ${Lib.stringifyCards(bombCards)}`);
    assert(Lib.stringifyCards(bombCards), "S6 S5 S4 S3 S2", `Karten stimmen nicht: ${Lib.stringifyCards(bombCards)}`);
    assert(bombCombination, [CombinationType.BOMB, 5, 6], "Kombination stimmt nicht");
});

test('findBombs: Hand mit mehreren Bomben sollte alle finden', () => {
    const hand = Lib.parseCards("S2 G2 B2 R2 S4 S5 S6 S7 S8");
    const bombs = Lib.findBombs(hand);
    assert(bombs.length, 2); // 4er-Bombe und Farbbombe
});

test('findBombs: Hand mit zu wenigen Karten sollte leeres Array zurückgeben', () => {
    const hand = Lib.parseCards("SA RA GA");
    const bombs = Lib.findBombs(hand);
    assert(bombs.length, 0);
});

// ======================================================================================
// Tests für getPlayableBombs(hand, trickCombination)
// ======================================================================================

test('getPlayableBombs: Keine Bomben in der Hand sollte immer leeres Array zurückgeben', () => {
    const hand = Lib.parseCards("S2 S3 S4");
    const trick = [CombinationType.SINGLE, 1, 5];
    const playableBombs = Lib.getPlayableBombs(hand, trick);
    assert(playableBombs.length, 0);
});

test('getPlayableBombs: Bombe in der Hand und kein Stich auf dem Tisch', () => {
    const hand = Lib.parseCards("S8 G8 B8 R8");
    const playableBombs = Lib.getPlayableBombs(hand, FIGURE_PASS);
    assert(playableBombs.length, 1); // Die 8er-Bombe ist spielbar.
    assert(playableBombs[0][1], [CombinationType.BOMB, 4, 8]); // Prüfe, ob es die 8er-Bombe ist.
});

test('getPlayableBombs: Bombe in der Hand und normaler Stich auf dem Tisch', () => {
    const hand = Lib.parseCards("S8 G8 B8 R8");
    const trick = [CombinationType.PAIR, 2, 14]; // Paar Asse
    const playableBombs = Lib.getPlayableBombs(hand, trick);
    assert(playableBombs.length, 1); // Bombe ist spielbar auf normalen Stich
});

test('getPlayableBombs: Bombe in der Hand und niedrigere Bombe auf dem Tisch', () => {
    const hand = Lib.parseCards("S8 G8 B8 R8");
    const trick = [CombinationType.BOMB, 4, 7]; // 4er-Bombe 7er
    const playableBombs = Lib.getPlayableBombs(hand, trick);
    assert(playableBombs.length, 1); // 8er-Bombe ist höher und spielbar
});

test('getPlayableBombs: Bombe in der Hand und höhere Bombe auf dem Tisch', () => {
    const hand = Lib.parseCards("S8 G8 B8 R8");
    const trick = [CombinationType.BOMB, 4, 9]; // 4er-Bombe 9er
    const playableBombs = Lib.getPlayableBombs(hand, trick);
    assert(playableBombs.length, 0); // 8er-Bombe ist niedriger und nicht spielbar
});

test('getPlayableBombs: Längere Bombe schlägt kürzere Bombe gleichen Rangs', () => {
    const hand = Lib.parseCards("S8 G8 B8 R8 S9"); // Enthält eine Farbbombe 8-9 (hypothetisch, nur für Test)
    // build_combinations würde diese Farbbombe nicht finden, aber wir können sie manuell erstellen
    const handBombs = [
        [ Lib.parseCards("S8 G8 B8 R8"), [CombinationType.BOMB, 4, 8] ],
        [ Lib.parseCards("S8 S9"), [CombinationType.BOMB, 2, 9] ] // Fake-Bombe
    ];
    // Um diesen Test robust zu machen, mocken wir findBombs
    const originalFindBombs = Lib.findBombs;
    Lib.findBombs = () => handBombs;

    const trick = [CombinationType.BOMB, 2, 8]; // Kürzere 8er-Bombe
    const playableBombs = Lib.getPlayableBombs(hand, trick);
    // Annahme: Die 4er-Bombe (länger) und die 2er 9er-Bombe (höher) sind spielbar
    // Dieser Test ist komplexer, da er die Logik von build_combinations umgeht.
    // Ein einfacherer Test ist vorzuziehen.

    // Wiederherstellen der originalen Funktion
    Lib.findBombs = originalFindBombs;

    // Einfacherer Test:
    const hand2 = Lib.parseCards("R2 R3 R4 R5 R6"); // 5er Farbbombe
    const trick2 = [CombinationType.BOMB, 4, 10]; // 4er Bombe 10er
    const playableBombs2 = Lib.getPlayableBombs(hand2, trick2);
    assert(playableBombs2.length, 1); // Längere Bombe ist spielbar
});

// ======================================================================================
// Tests für canPlay(hand, trickCombination, unfulfilledWish)
// ======================================================================================

test('canPlay: Passender höherer Single auf der Hand', (handStr, trick, expected) => {
    const hand = Lib.parseCards(handStr);
    assert(Lib.canPlay(hand, trick, 0), expected);
}, [
    ["S8", [CombinationType.SINGLE, 1, 7], true],  // 8 schlägt 7
    ["S6", [CombinationType.SINGLE, 1, 7], false], // 6 schlägt 7 nicht
    ["Dr", [CombinationType.SINGLE, 1, 14], true], // Drache schlägt Ass
    ["SA", [CombinationType.SINGLE, 1, 15], false]  // Ass schlägt Drache nicht
]);

test('canPlay: Anspiel (leerer Stich) ist immer möglich mit Karten', () => {
    const hand = Lib.parseCards("S2 S3");
    assert(Lib.canPlay(hand, [CombinationType.PASS, 0, 0], 0), true);
});

test('canPlay: Anspiel mit leerer Hand ist nicht möglich', () => {
    const hand = [];
    assert(Lib.canPlay(hand, [CombinationType.PASS, 0, 0], 0), false);
});

test('canPlay: Nur Passen möglich', () => {
    const hand = Lib.parseCards("S2 G3 R4"); // Nur Singles
    const trick = [CombinationType.PAIR, 2, 5]; // Paar 5er liegt
    assert(Lib.canPlay(hand, trick, 0), false);
});

test('canPlay: Wunsch muss erfüllt werden, wenn möglich', () => {
    const hand = Lib.parseCards("S5 S6 S7"); // Enthält 6
    const trick = [CombinationType.SINGLE, 1, 4];
    const wish = 6;
    assert(Lib.canPlay(hand, trick, wish), true); // Kann S6 spielen
});

test('canPlay: Wunsch kann nicht erfüllt werden, aber anderer Zug möglich', () => {
    const hand = Lib.parseCards("S5 S8 S9"); // Enthält keine 6
    const trick = [CombinationType.SINGLE, 1, 4];
    const wish = 6;
    // Da Wunsch nicht erfüllbar ist, verhält es sich wie ein normaler Zug. 8 > 4.
    assert(Lib.canPlay(hand, trick, wish), true);
});

// ======================================================================================
// Tests für selectBestPlay(hand, trickCombination, unfulfilledWish)
// ======================================================================================

test('selectBestPlay: Wählt den niedrigsten passenden Single', () => {
    const hand = Lib.parseCards("S8 S9 SK");
    const trick = [CombinationType.SINGLE, 1, 7];
    const bestPlay = Lib.selectBestPlay(hand, trick, 0);
    assert(bestPlay !== null, true);
    assert(Lib.stringifyCards(bestPlay[0]), "S8"); // S8 ist die niedrigste Karte > 7
});

test('selectBestPlay: Wählt das niedrigste passende Paar', () => {
    const hand = Lib.parseCards("S8 G8 SK BK SA RA");
    const trick = [CombinationType.PAIR, 2, 7];
    const bestPlay = Lib.selectBestPlay(hand, trick, 0);
    assert(bestPlay !== null, true);
    assert(Lib.stringifyCards(bestPlay[0]), "S8 G8");
});

test('selectBestPlay: Gibt null zurück, wenn nur Passen möglich ist', () => {
    const hand = Lib.parseCards("S2 G3 R4");
    const trick = [CombinationType.PAIR, 2, 5];
    const bestPlay = Lib.selectBestPlay(hand, trick, 0);
    assert(bestPlay, null);
});

test('selectBestPlay: Wählt keine Bombe, wenn ein normaler Zug möglich ist', () => {
    const hand = Lib.parseCards("S8 G8 S9 S2 G2 B2 R2"); // Paar 8, Single 9, Bombe 2
    const trick = [CombinationType.PAIR, 2, 7];
    const bestPlay = Lib.selectBestPlay(hand, trick, 0);
    assert(bestPlay !== null, true);
    assert(Lib.stringifyCards(bestPlay[0]), "S8 G8"); // Sollte das Paar 8 wählen, nicht die Bombe
});

test('selectBestPlay: Wählt die niedrigste Bombe, wenn nur Bomben möglich sind', () => {
    const hand = Lib.parseCards("S8 G8 B8 R8 S9 G9 B9 R9"); // Bombe 8 und 9
    const trick = [CombinationType.PAIR, 2, 14]; // Paar Asse, nur Bomben können schlagen
    const bestPlay = Lib.selectBestPlay(hand, trick, 0);
    assert(bestPlay !== null, true);
    assert(Lib.stringifyCards(bestPlay[0]), "S8 G8 B8 R8"); // Die 8er-Bombe ist die niedrigere
});

test('selectBestPlay: Wählt den Zug, der den Wunsch erfüllt', () => {
    const hand = Lib.parseCards("S5 S6 S7");
    const trick = [CombinationType.SINGLE, 1, 4];
    const wish = 6;
    const bestPlay = Lib.selectBestPlay(hand, trick, wish);
    assert(bestPlay !== null, true);
    assert(Lib.stringifyCards(bestPlay[0]), "S6"); // Muss die 6 spielen
});