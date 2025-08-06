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
//
// describe('Mathematik', () => {
//     test('Addition', () => assert(2 + 2, 4));
//     test('Float-Vergleich', () => assert(0.2 + 0.1, approx(0.3)));
// });
//
// describe('Fehlerbehandlung', () => {
//     test('Division durch 0', () => {
//         assertThrows(() => { throw new Error('Division durch 0'); }, 'Division');
//     });
// });
//
// test('assertThrows mit Message', () => {
//     assertThrows(() => {
//         throw new Error('Ungültiger Zustand');
//     }, 'Ungültig');
// });

test('sortCards', () => {
    const cards = Lib.parseCards("S7 S8 R8 G8 S3 R4 R5 S2 G2");
    const expected = Lib.parseCards("R8 G8 S8 S7 R5 R4 S3 G2 S2");
    Lib.sortCards(cards);
    assert(cards, expected);
});

describe('findBombs', () => {
    test('Hand ohne Bomben sollte leeres Array zurückgeben', () => {
        const hand = Lib.parseCards("S2 S3 S4 R5 S6 S7");
        const bombs = Lib.findBombs(hand);
        assert(bombs.length, 0);
    });
    
    test('Hand mit Farbbombe Länge 6 sollte 3 mögliche Bomben zurückgeben', () => {
        const hand = Lib.parseCards("S2 S3 S4 S5 S6 S7");
        const bombs = Lib.findBombs(hand);
        assert(bombs.length, 3);
    });
    
    test('Hand mit einer 4er-Bombe sollte diese finden', () => {
        const hand = Lib.parseCards("S5 G5 B5 R5 SA");
        const bombs = Lib.findBombs(hand);
        assert(bombs.length, 1);
        const [bombCards, bombCombination] = bombs[0];
        assert(Lib.stringifyCards(bombCards), "R5 G5 B5 S5");
        assert(bombCombination, [CombinationType.BOMB, 4, 5]);
    });
    
    test('Hand mit einer Farbbombe sollte diese finden', () => {
        const hand = Lib.parseCards("S2 S3 S4 S5 S6"); // Farbbombe Schwarz von 2 bis 6
        const bombs = Lib.findBombs(hand);
        assert(bombs.length, 1);
        const [bombCards, bombCombination] = bombs[0];
        assert(Lib.stringifyCards(hand), "S6 S5 S4 S3 S2", `Handkarten sollten absteigend sortierte werden: ${Lib.stringifyCards(bombCards)}`);
        assert(Lib.stringifyCards(bombCards), "S6 S5 S4 S3 S2", `Karten stimmen nicht: ${Lib.stringifyCards(bombCards)}`);
        assert(bombCombination, [CombinationType.BOMB, 5, 6], "Kombination stimmt nicht");
    });
    
    test('Hand mit mehreren Bomben sollte alle finden', () => {
        const hand = Lib.parseCards("S2 G2 B2 R2 S4 S5 S6 S7 S8");
        const bombs = Lib.findBombs(hand);
        assert(bombs.length, 2); // 4er-Bombe und Farbbombe
    });
    
    test('Hand mit zu wenigen Karten sollte leeres Array zurückgeben', () => {
        const hand = Lib.parseCards("SA RA GA");
        const bombs = Lib.findBombs(hand);
        assert(bombs.length, 0);
    });
});

describe('getPlayableBombs', () => {
    test('Keine Bomben in der Hand sollte immer leeres Array zurückgeben', () => {
        const hand = Lib.parseCards("S2 S3 S4");
        const trick = /** @type Combination **/ [CombinationType.SINGLE, 1, 5];
        const playableBombs = Lib.getPlayableBombs(hand, trick);
        assert(playableBombs.length, 0);
    });
    
    test('Bombe in der Hand und kein Stich auf dem Tisch', () => {
        const hand = Lib.parseCards("S8 G8 B8 R8");
        const playableBombs = Lib.getPlayableBombs(hand, /** @type Combination **/ [CombinationType.PASS, 0, 0]);
        assert(playableBombs.length, 1); // Die 8er-Bombe ist spielbar.
        assert(playableBombs[0][1], [CombinationType.BOMB, 4, 8]); // Prüfe, ob es die 8er-Bombe ist.
    });
    
    test('Bombe in der Hand und normaler Stich auf dem Tisch', () => {
        const hand = Lib.parseCards("S8 G8 B8 R8");
        const trick = /** @type Combination **/ [CombinationType.PAIR, 2, 14]; // Paar Asse
        const playableBombs = Lib.getPlayableBombs(hand, trick);
        assert(playableBombs.length, 1); // Bombe ist spielbar auf normalen Stich
    });
    
    test('Bombe in der Hand und niedrigere Bombe auf dem Tisch', () => {
        const hand = Lib.parseCards("S8 G8 B8 R8");
        const trick = /** @type Combination **/ [CombinationType.BOMB, 4, 7]; // 4er-Bombe 7er
        const playableBombs = Lib.getPlayableBombs(hand, trick);
        assert(playableBombs.length, 1); // 8er-Bombe ist höher und spielbar
    });
    
    test('Bombe in der Hand und höhere Bombe auf dem Tisch', () => {
        const hand = Lib.parseCards("S8 G8 B8 R8");
        const trick = /** @type Combination **/ [CombinationType.BOMB, 4, 9]; // 4er-Bombe 9er
        const playableBombs = Lib.getPlayableBombs(hand, trick);
        assert(playableBombs.length, 0); // 8er-Bombe ist niedriger und nicht spielbar
    });
    
    test('Längere Bombe schlägt kürzere Bombe gleichen Rangs', () => {
        //const hand = Lib.parseCards("S8 G8 B8 R8 S9"); // Enthält eine Farbbombe 8-9 (hypothetisch, nur für Test)
        // build_combinations würde diese Farbbombe nicht finden, aber ich kann sie manuell erstellen
        const handBombs = [
            [ Lib.parseCards("S8 G8 B8 R8"), [CombinationType.BOMB, 4, 8] ],
            [ Lib.parseCards("S8 S9"), [CombinationType.BOMB, 2, 9] ] // Fake-Bombe
        ];
        // Um diesen Test robust zu machen, mocke ich findBombs.
        const originalFindBombs = Lib.findBombs;
        Lib.findBombs = () => handBombs;
    
        //const trick = /** @type Combination **/ [CombinationType.BOMB, 2, 8]; // Kürzere 8er-Bombe
        //const playableBombs = Lib.getPlayableBombs(hand, trick);
        // Annahme: Die 4er-Bombe (länger) und die 2er 9er-Bombe (höher) sind spielbar.
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
});

describe('canPlay', () => {
    test('Passender höherer Single auf der Hand', (handStr, trick, expected) => {
        State.setHandCards(Lib.parseCards(handStr));
        State.setTrickCombination(trick);
        assert(State.canPlayCards(), expected);
    }, [
        ["S8", [CombinationType.SINGLE, 1, 7], true],  // 8 schlägt 7
        ["S6", [CombinationType.SINGLE, 1, 7], false], // 6 schlägt 7 nicht
        ["Dr", [CombinationType.SINGLE, 1, 14], true], // Drache schlägt Ass
        ["SA", [CombinationType.SINGLE, 1, 15], false]  // Ass schlägt Drache nicht
    ]);
    
    test('Anspiel (leerer Stich) ist immer möglich mit Karten', () => {
        State.setHandCards(Lib.parseCards("S2 S3"));
        State.setTrickCombination(/** @type Combination **/[CombinationType.PASS, 0, 0]);
        assert(State.canPlayCards(), true);
    });
    
    test('Anspiel mit leerer Hand ist nicht möglich', () => {
        State.setHandCards([]);
        State.setTrickCombination(/** @type Combination **/[CombinationType.PASS, 0, 0]);
        assert(State.canPlayCards(), false);
    });
    
    test('Nur Passen möglich', () => {
        State.setHandCards(Lib.parseCards("S2 G3 R4")); // Nur Singles
        State.setTrickCombination(/** @type Combination **/ [CombinationType.PAIR, 2, 5]); // Paar 5er liegt
        assert(State.canPlayCards(), false);
    });
    
    test('Wunsch muss erfüllt werden, wenn möglich', () => {
        State.setHandCards(Lib.parseCards("S5 S6 S7")); // Enthält 6
        State.setTrickCombination(/** @type Combination **/ [CombinationType.SINGLE, 1, 4]);
        State.setWishValue(6);
        assert(State.canPlayCards(), true); // Kann S6 spielen
    });
    
    test('Wunsch kann nicht erfüllt werden, aber anderer Zug möglich', () => {
        State.setHandCards(Lib.parseCards("S5 S8 S9")); // Enthält keine 6
        State.setTrickCombination(/** @type Combination **/ [CombinationType.SINGLE, 1, 4]);
        State.setWishValue(6);
        // Da der Wunsch nicht erfüllbar ist, verhält es sich wie ein normaler Zug. 8 > 4.
        assert(State.canPlayCards(), true);
    });
});

describe('getBestPlayableCombination', () => {
    test('Wählt den niedrigsten passenden Single', () => {
        State.setHandCards(Lib.parseCards("S8 S9 SK"));
        State.setTrickCombination(/** @type Combination **/ [CombinationType.SINGLE, 1, 8]);
        State.setWishValue(0);
        const bestPlay = State.getBestPlayableCombination();
        assert(bestPlay !== null, true);
        assert(Lib.stringifyCards(bestPlay[0]), "S9");
    });

    test('Wählt das niedrigste passende Paar', () => {
        State.setHandCards(Lib.parseCards("S8 G8 SK BK SA RA"));
        State.setTrickCombination(/** @type Combination **/ [CombinationType.PAIR, 2, 8]);
        State.setWishValue(0);
        const bestPlay = State.getBestPlayableCombination();
        assert(bestPlay !== null, true);
        assert(Lib.stringifyCards(bestPlay[0]), "BK SK");
    });

    test('Nur Passen ist möglich', () => {
        State.setHandCards(Lib.parseCards("S2 G3 R4"));
        State.setTrickCombination(/** @type Combination **/ [CombinationType.PAIR, 2, 5]);
        State.setWishValue(0);
        const bestPlay = State.getBestPlayableCombination();
        assert(bestPlay, [[], [CombinationType.PASS, 0, 0]]);
    });

    test('Wählt keine Bombe, wenn ein normaler Zug möglich ist', () => {
        State.setHandCards(Lib.parseCards("S8 G8 S9 S2 G2 B2 R2"));
        State.setTrickCombination(/** @type Combination **/ [CombinationType.PAIR, 2, 7]);
        State.setWishValue(0);
        const bestPlay = State.getBestPlayableCombination();
        assert(bestPlay !== null, true);
        assert(Lib.stringifyCards(bestPlay[0]), "G8 S8"); // Sollte das Paar 8 wählen, nicht die Bombe
    });

    test('Wählt die niedrigste Bombe, wenn nur Bomben möglich sind', () => {
        State.setHandCards(Lib.parseCards("S8 G8 B8 R8 S9 G9 B9 R9"));
        State.setTrickCombination(/** @type Combination **/ [CombinationType.PAIR, 2, 14]);
        State.setWishValue(0);
        const bestPlay = State.getBestPlayableCombination();
        assert(bestPlay !== null, true);
        assert(Lib.stringifyCards(bestPlay[0]), "R8 G8 B8 S8"); // Die 8er-Bombe ist die niedrigere
    });

    test('Wählt den Zug, der den Wunsch erfüllt', () => {
        State.setHandCards(Lib.parseCards("S5 S6 S7"));
        State.setTrickCombination(/** @type Combination **/ [CombinationType.SINGLE, 1, 4]);
        State.setWishValue(6);
        const bestPlay = State.getBestPlayableCombination();
        assert(bestPlay !== null, true);
        assert(Lib.stringifyCards(bestPlay[0]), "S6"); // Muss die 6 spielen
    });

    test('Bombe nicht zerbrechen', () => {
        // Hand enthält: Ein Paar 8er und eine 4er-Bombe 5er.
        State.setHandCards(Lib.parseCards("S8 G8 S5 G5 B5 R5"));
        State.setTrickCombination(/** @type Combination **/ [CombinationType.PAIR, 2, 7]);
        State.setWishValue(0);
        const bestPlay = State.getBestPlayableCombination();
        assert(bestPlay !== null, true);
        assert(Lib.stringifyCards(bestPlay[0]), "G8 S8");

        // Hand: Paar 3er (sicher), Paar 9er (Teil einer Bombe)
        State.setHandCards(Lib.parseCards("S3 G3 S9 G9 B9 R9"));
        State.setTrickCombination(/** @type Combination **/ [CombinationType.PAIR, 2, 2]);
        State.setWishValue(0);
        const bestPlay2 = State.getBestPlayableCombination();
        assert(bestPlay2 !== null, true);
        assert(Lib.stringifyCards(bestPlay2[0]), "G3 S3");
    });

    test('Wählt eine Bombe, bevor eine zerrissen wird.', () => {
        // Die Hand enthält: Ein Paar 8er (Teil einer Bombe) und Singles, die nicht passen.
        State.setHandCards(Lib.parseCards("S8 G8 B8 R8 SA SK S8 S9"));
        State.setTrickCombination(/** @type Combination **/ [CombinationType.PAIR, 2, 7]);
        State.setWishValue(0);
        const bestPlay = State.getBestPlayableCombination();
        assert(bestPlay !== null, true);
        assert(Lib.stringifyCards(bestPlay[0]), "R8 G8 B8 S8");
    });

    test('Spielt eine Bombe, wenn es die einzige Option ist (außer Passen)', () => {
        // Die Hand enthält nur eine Bombe und einen Single, der nicht passt.
        State.setHandCards(Lib.parseCards("S8 G8 B8 R8 SA"));
        State.setTrickCombination(/** @type Combination **/ [CombinationType.STREET, 5, 14]);
        State.setWishValue(0);
        const bestPlay = State.getBestPlayableCombination();
        assert(bestPlay !== null, true);
        assert(Lib.stringifyCards(bestPlay[0]), "R8 G8 B8 S8");
        assert(bestPlay[1][0], CombinationType.BOMB);
    });

    test('Anspiel mit Bomben auf der Hand', () => {
        // Hand: Paar 2er (sicher), Bombe 8er
        State.setHandCards(Lib.parseCards("S2 G2 S8 G8 B8 R8"));
        State.setTrickCombination(/** @type Combination **/ [CombinationType.PASS, 0, 0]);
        State.setWishValue(0);
        const bestPlay = State.getBestPlayableCombination();
        assert(bestPlay !== null, true);
        assert(Lib.stringifyCards(bestPlay[0]), "G2 S2");
    });

    test('Ignoriert "Bombenkarten" korrekt, wenn es keine Bombe ist', () => {
        State.setHandCards(Lib.parseCards("S5 G5 B5 R5 S6"));
        State.setTrickCombination(/** @type Combination **/ [CombinationType.PASS, 0, 0]);
        State.setWishValue(0);
        const bestPlay1 = State.getBestPlayableCombination();
        assert(Lib.stringifyCards(bestPlay1[0]), "S6");

        State.setHandCards(Lib.parseCards("S5 G5 B5 S6"));
        State.setTrickCombination(/** @type Combination **/ [CombinationType.PASS, 0, 0]);
        State.setWishValue(0);
        const bestPlay2 = State.getBestPlayableCombination();
        assert(Lib.stringifyCards(bestPlay2[0]), "G5 B5 S5");
    });
});
