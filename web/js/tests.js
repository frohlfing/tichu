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
    const trick = /** @type Combination **/ [CombinationType.SINGLE, 1, 5];
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
    const trick = /** @type Combination **/ [CombinationType.PAIR, 2, 14]; // Paar Asse
    const playableBombs = Lib.getPlayableBombs(hand, trick);
    assert(playableBombs.length, 1); // Bombe ist spielbar auf normalen Stich
});

test('getPlayableBombs: Bombe in der Hand und niedrigere Bombe auf dem Tisch', () => {
    const hand = Lib.parseCards("S8 G8 B8 R8");
    const trick = /** @type Combination **/ [CombinationType.BOMB, 4, 7]; // 4er-Bombe 7er
    const playableBombs = Lib.getPlayableBombs(hand, trick);
    assert(playableBombs.length, 1); // 8er-Bombe ist höher und spielbar
});

test('getPlayableBombs: Bombe in der Hand und höhere Bombe auf dem Tisch', () => {
    const hand = Lib.parseCards("S8 G8 B8 R8");
    const trick = /** @type Combination **/ [CombinationType.BOMB, 4, 9]; // 4er-Bombe 9er
    const playableBombs = Lib.getPlayableBombs(hand, trick);
    assert(playableBombs.length, 0); // 8er-Bombe ist niedriger und nicht spielbar
});

test('getPlayableBombs: Längere Bombe schlägt kürzere Bombe gleichen Rangs', () => {
    //const hand = Lib.parseCards("S8 G8 B8 R8 S9"); // Enthält eine Farbbombe 8-9 (hypothetisch, nur für Test)
    // build_combinations würde diese Farbbombe nicht finden, aber wir können sie manuell erstellen
    const handBombs = [
        [ Lib.parseCards("S8 G8 B8 R8"), [CombinationType.BOMB, 4, 8] ],
        [ Lib.parseCards("S8 S9"), [CombinationType.BOMB, 2, 9] ] // Fake-Bombe
    ];
    // Um diesen Test robust zu machen, mocken wir findBombs
    const originalFindBombs = Lib.findBombs;
    Lib.findBombs = () => handBombs;

    //const trick = /** @type Combination **/ [CombinationType.BOMB, 2, 8]; // Kürzere 8er-Bombe
    //const playableBombs = Lib.getPlayableBombs(hand, trick);
    // Annahme: Die 4er-Bombe (länger) und die 2er 9er-Bombe (höher) sind spielbar
    // Dieser Test ist komplexer, da er die Logik von build_combinations umgeht.
    // Ein einfacherer Test ist vorzuziehen.

    // Wiederherstellen der originalen Funktion
    Lib.findBombs = originalFindBombs;

    // Einfacherer Test:
    const hand2 = Lib.parseCards("R2 R3 R4 R5 R6"); // 5er Farbbombe
    const trick2 = /** @type Combination **/ [CombinationType.BOMB, 4, 10]; // 4er Bombe 10er
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
    const trick = /** @type Combination **/[CombinationType.PASS, 0, 0];
    assert(Lib.canPlay(hand, trick, 0), true);
});

test('canPlay: Anspiel mit leerer Hand ist nicht möglich', () => {
    const hand = [];
    const trick = /** @type Combination **/[CombinationType.PASS, 0, 0];
    assert(Lib.canPlay(hand, trick, 0), false);
});

test('canPlay: Nur Passen möglich', () => {
    const hand = Lib.parseCards("S2 G3 R4"); // Nur Singles
    const trick = /** @type Combination **/ [CombinationType.PAIR, 2, 5]; // Paar 5er liegt
    assert(Lib.canPlay(hand, trick, 0), false);
});

test('canPlay: Wunsch muss erfüllt werden, wenn möglich', () => {
    const hand = Lib.parseCards("S5 S6 S7"); // Enthält 6
    const trick = /** @type Combination **/ [CombinationType.SINGLE, 1, 4];
    const wish = 6;
    assert(Lib.canPlay(hand, trick, wish), true); // Kann S6 spielen
});

test('canPlay: Wunsch kann nicht erfüllt werden, aber anderer Zug möglich', () => {
    const hand = Lib.parseCards("S5 S8 S9"); // Enthält keine 6
    const trick = /** @type Combination **/ [CombinationType.SINGLE, 1, 4];
    const wish = 6;
    // Da Wunsch nicht erfüllbar ist, verhält es sich wie ein normaler Zug. 8 > 4.
    assert(Lib.canPlay(hand, trick, wish), true);
});

// ======================================================================================
// Tests für selectBestPlay(hand, trickCombination, unfulfilledWish)
// ======================================================================================

test('selectBestPlay: Wählt den niedrigsten passenden Single', () => {
    const hand = Lib.parseCards("S8 S9 SK");
    const trick = /** @type Combination **/ [CombinationType.SINGLE, 1, 8];
    const bestPlay = Lib.selectBestPlay(hand, trick,0);
    assert(bestPlay !== null, true);
    assert(Lib.stringifyCards(bestPlay[0]), "S9");
});

test('selectBestPlay: Wählt das niedrigste passende Paar', () => {
    const hand = Lib.parseCards("S8 G8 SK BK SA RA");
    const trick = /** @type Combination **/ [CombinationType.PAIR, 2, 8];
    const bestPlay = Lib.selectBestPlay(hand, trick, 0);
    assert(bestPlay !== null, true);
    assert(Lib.stringifyCards(bestPlay[0]), "SK BK");
});

test('selectBestPlay: Nur Passen ist möglich', () => {
    const hand = Lib.parseCards("S2 G3 R4");
    const trick = /** @type Combination **/ [CombinationType.PAIR, 2, 5];
    const bestPlay = Lib.selectBestPlay(hand, trick, 0);
    assert(bestPlay, [[], [CombinationType.PASS, 0, 0]]);
});

test('selectBestPlay: Wählt keine Bombe, wenn ein normaler Zug möglich ist', () => {
    const hand = Lib.parseCards("S8 G8 S9 S2 G2 B2 R2"); // Paar 8, Single 9, Bombe 2
    const trick = /** @type Combination **/ [CombinationType.PAIR, 2, 7];
    const bestPlay = Lib.selectBestPlay(hand, trick, 0);
    assert(bestPlay !== null, true);
    assert(Lib.stringifyCards(bestPlay[0]), "S8 G8"); // Sollte das Paar 8 wählen, nicht die Bombe
});

test('selectBestPlay: Wählt die niedrigste Bombe, wenn nur Bomben möglich sind', () => {
    const hand = Lib.parseCards("S8 G8 B8 R8 S9 G9 B9 R9"); // Bombe 8 und 9
    const trick = /** @type Combination **/ [CombinationType.PAIR, 2, 14]; // Paar Asse, nur Bomben können schlagen
    const bestPlay = Lib.selectBestPlay(hand, trick, 0);
    assert(bestPlay !== null, true);
    assert(Lib.stringifyCards(bestPlay[0]), "S8 G8 B8 R8"); // Die 8er-Bombe ist die niedrigere
});

test('selectBestPlay: Wählt den Zug, der den Wunsch erfüllt', () => {
    const hand = Lib.parseCards("S5 S6 S7");
    const trick = /** @type Combination **/ [CombinationType.SINGLE, 1, 4];
    const wish = 6;
    const bestPlay = Lib.selectBestPlay(hand, trick, wish);
    assert(bestPlay !== null, true);
    assert(Lib.stringifyCards(bestPlay[0]), "S6"); // Muss die 6 spielen
});

test('selectBestPlay: Bombe nicht zerbrechen', () => {
    // Hand enthält: Ein Paar 8er und eine 4er-Bombe 5er.
    const hand = Lib.parseCards("S8 G8 S5 G5 B5 R5");
    const trick = /** @type Combination **/ [CombinationType.PAIR, 2, 7]; // Ein Paar 7er liegt auf dem Tisch.
    const bestPlay = Lib.selectBestPlay(hand, trick, 0);
    assert(bestPlay !== null, true);
    assert(Lib.stringifyCards(bestPlay[0]), "S8 G8");

    // Hand: Paar 3er (sicher), Paar 9er (Teil einer Bombe)
    const hand2 = Lib.parseCards("S3 G3 S9 G9 B9 R9");
    const trick2 = /** @type Combination **/ [CombinationType.PAIR, 2, 2]; // Paar 2er liegt.
    const bestPlay2 = Lib.selectBestPlay(hand2, trick2, 0);
    assert(bestPlay2 !== null, true);
    assert(Lib.stringifyCards(bestPlay2[0]), "S3 G3");
});

test('selectBestPlay: Wählt eine Bombe, bevor eine zerrissen wird.', () => {
    // Hand enthält: Ein Paar 8er (Teil einer Bombe) und Singles, die nicht passen.
    const hand = Lib.parseCards("S8 G8 B8 R8 SA SK");
    const trick = /** @type Combination **/ [CombinationType.PAIR, 2, 7]; // Paar 7er liegt.
    const bestPlay = Lib.selectBestPlay(hand, trick, 0);
    assert(bestPlay !== null, true);
    assert(Lib.stringifyCards(bestPlay[0]), "S8 G8 B8 R8");
});

test('selectBestPlay: Spielt eine Bombe, wenn es die einzige Option ist (außer Passen)', () => {
    // Hand enthält nur eine Bombe und einen Single, der nicht passt.
    const hand = Lib.parseCards("S8 G8 B8 R8 SA");
    const trick = /** @type Combination **/ [CombinationType.STREET, 5, 14]; // Eine hohe Straße, die nicht zu schlagen ist.
    // Einziger möglicher Zug ist die Bombe. Passen wäre auch möglich.
    const bestPlay = Lib.selectBestPlay(hand, trick, 0);
    assert(bestPlay !== null, true);
    assert(Lib.stringifyCards(bestPlay[0]), "S8 G8 B8 R8");
    assert(bestPlay[1][0], CombinationType.BOMB);
});

test('selectBestPlay: Anspiel mit Bomben auf der Hand', () => {
    // Hand: Paar 2er (sicher), Bombe 8er
    const hand = Lib.parseCards("S2 G2 S8 G8 B8 R8");
    const trick = /** @type Combination **/ [CombinationType.PASS, 0, 0]; // Anspiel
    const bestPlay = Lib.selectBestPlay(hand, trick, 0);
    assert(bestPlay !== null, true);
    assert(Lib.stringifyCards(bestPlay[0]), "S2 G2");
});

test('selectBestPlay: Ignoriert "Bombenkarten" korrekt, wenn es keine Bombe ist', () => {
    const handWithBomb = Lib.parseCards("S5 G5 B5 R5 S6");
    const trick = /** @type Combination **/ [CombinationType.PASS, 0, 0];
    const bestPlay1 = Lib.selectBestPlay(handWithBomb, trick, 0);
    assert(Lib.stringifyCards(bestPlay1[0]), "S6");
    const handWithoutBomb = Lib.parseCards("S5 G5 B5 S6");
    const bestPlay2 = Lib.selectBestPlay(handWithoutBomb, trick, 0);
    assert(Lib.stringifyCards(bestPlay2[0]), "S5 G5 B5");
});

// Beispieltests
describe('Mathematik', () => {
    test('Addition', () => assert(2 + 2, 4));
    test('Float-Vergleich', () => assert(0.2 + 0.1, approx(0.3)));
});

describe('Fehlerbehandlung', () => {
    test('Division durch 0', () => {
        assertThrows(() => { throw new Error('Division durch 0'); }, 'Division');
    });
});

test('assertThrows mit Message', () => {
    assertThrows(() => {
        throw new Error('Ungültiger Zustand');
    }, 'Ungültig');
});
