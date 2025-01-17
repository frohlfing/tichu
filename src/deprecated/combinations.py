import itertools
from src.lib.combinations import *


# Listet die möglichen Hände auf und markiert, welche die gegebene Kombination hat
def possible_hands(unplayed_cards: list[tuple], k: int, figure: tuple) -> tuple[list, list]:
    hands = list(itertools.combinations(unplayed_cards, k))
    matches = []
    t, m, r = figure  # type, length, rank
    for hand in hands:
        if t == SINGLE:  # Einzelkarte
            b = any(v == r for v, _ in hand)

        elif t in [PAIR, TRIPLE]:  # Paar oder Drilling
            b = sum(1 for v, _ in hand if v in [r, 16]) >= m

        elif t == STAIR:  # Treppe
            steps = int(m / 2)
            if any(v == 16 for v, _ in hand):  # Phönix vorhanden?
                b = False
                for j in range(steps):
                    b = all(sum(1 for v, _ in hand if v == r - i) >= (1 if i == j else 2) for i in range(steps))
                    if b:
                        break
            else:
                b = all(sum(1 for v, _ in hand if v == r - i) >= 2 for i in range(steps))

        elif t == FULLHOUSE:  # Fullhouse
            if any(v == 16 for v, _ in hand):  # Phönix vorhanden?
                b = False
                for j in range(2, 15):
                    b = (sum(1 for v, _ in hand if v == r) >= (2 if r == j else 3)
                         and any(sum(1 for v2, _ in hand if v2 == r2) >= (1 if r2 == j else 2) for r2 in range(2, 15) if r2 != r))
                    if b:
                        break
            else:
                b = (sum(1 for v, _ in hand if v == r) >= 3
                     and any(sum(1 for v2, _ in hand if v2 == r2) >= 2 for r2 in range(2, 15) if r2 != r))

        elif t == STREET:  # Straße
            colors = set([c for i in range(m) for v, c in hand if v == r - i])  # Auswahl an Farben in der Straße
            if any(v == 16 for v, _ in hand):  # Phönix vorhanden?
                b = False
                for j in range(int(m)):
                    b = all(sum(1 for v, _ in hand if v == r - i) >= (0 if i == j else 1) for i in range(m))
                    if b:
                        break
            elif len(colors) == 1: # nur eine Auswahl an Farben → wenn eine Straße, dann Farbbombe
                b = False
            else:
                b = all(sum(1 for v, _ in hand if v == r - i) >= 1 for i in range(m))

        elif t == BOMB and m == 4:  # 4er-Bombe
            b = sum(1 for v, _ in hand if v == r) >= 4

        elif t == BOMB and m >= 5:  # Farbbombe
            b = any(all(sum(1 for v, c in hand if v == r - i and c == color) >= 1 for i in range(m)) for color in range(1, 5))
        else:
            assert False

        matches.append(b)
    return matches, hands


# Listet die möglichen Hände auf und markiert, welche eine Kombination hat, die die gegebene überstechen kann
#
# todo:
#  Falls die gegebene Kombination eine Farbbombe ist, kann sie von einer längeren Farbbombe überstochen werden, was auch berücksichtigt wird.
#  Falls die gegebene Kombination aber keine Farbbombe ist, kann sie von einer beliebigen Farbbombe überstochen werden, was NICHT berücksichtigt wird!
#  Ausnahme: Falls die gegebene Kombination eine Straße ist, wird eine Farbbombe, die einen höheren Rang hat, berücksichtigt.
#
# todo: nach probabilities verschieben (und den zugehörigen Unit-Test nach test_probabilities)
#
# Beispiel:
# matches, hands = possible_hands(parse_cards("Dr RK GK BB SB RB R2"), 5, (2, 2, 11))
# for match, hand in zip(matches, hands):
#     print(match, stringify_cards(hand))
# print(f"Wahrscheinlichkeit für ein Bubenpärchen: {sum(matches) / len(hands)}")  # 18/21 = 0.8571428571428571
#
# unplayed_cards: Ungespielte Karten
# k: Anzahl Handkarten
# figure: Typ, Länge, Rang der Kombination
def possible_hands_hi(unplayed_cards: list[tuple], k: int, figure: tuple) -> tuple[list, list]:
    hands = list(itertools.combinations(unplayed_cards, k))
    matches = []
    t, m, r = figure  # type, length, rank
    for hand in hands:
        b = False
        if t == SINGLE:  # Einzelkarte
            if r == 15:  # Drache
                b = False
            elif r < 15:  # bis zum Ass
                b = any(v > r for v, _ in hand)
            else:  # Phönix
                assert r == 16
                b = any(1 < v < 16 for v, _ in hand)
        else:
            for rhi in range(r + 1, 15):
                if t in [PAIR, TRIPLE]:  # Paar oder Drilling
                    b = sum(1 for v, _ in hand if v in [rhi, 16]) >= m

                elif t == STAIR:  # Treppe
                    steps = int(m / 2)
                    if any(v == 16 for v, _ in hand):  # Phönix vorhanden?
                        for j in range(steps):
                            b = all(sum(1 for v, _ in hand if v == rhi - i) >= (1 if i == j else 2) for i in range(steps))
                            if b:
                                break
                    else:
                        b = all(sum(1 for v, _ in hand if v == rhi - i) >= 2 for i in range(steps))

                elif t == FULLHOUSE:  # Fullhouse
                    if any(v == 16 for v, _ in hand):  # Phönix vorhanden?
                        for j in range(2, 15):
                            b = (sum(1 for v, _ in hand if v == rhi) >= (2 if rhi == j else 3)
                                 and any(sum(1 for v2, _ in hand if v2 == r2) >= (1 if r2 == j else 2) for r2 in range(2, 15) if r2 != rhi))
                            if b:
                                break
                    else:
                        b = (sum(1 for v, _ in hand if v == rhi) >= 3
                             and any(sum(1 for v2, _ in hand if v2 == r2) >= 2 for r2 in range(2, 15) if r2 != rhi))

                elif t == STREET:  # Straße
                    # colors = set([c for i in range(m) for v, c in hand if v == rhi - i])  # Auswahl an Farben in der Straße
                    if any(v == 16 for v, _ in hand):  # Phönix vorhanden?
                        for j in range(int(m)):
                            b = all(sum(1 for v, _ in hand if v == rhi - i) >= (0 if i == j else 1) for i in range(m))
                            if b:
                                break
                    # elif len(colors) == 1: # nur eine Auswahl an Farben → wenn eine Straße, dann Farbbombe
                    #     b = False
                    else:
                        b = all(sum(1 for v, _ in hand if v == rhi - i) >= 1 for i in range(m))

                elif t == BOMB and m == 4:  # 4er-Bombe
                    b = sum(1 for v, _ in hand if v == rhi) >= 4

                elif t == BOMB and m >= 5:  # Farbbombe (hier werden zunächst nur Farbbomben gleicher Länge verglichen)
                    b = any(all(sum(1 for v, c in hand if v == rhi - i and c == color) >= 1 for i in range(m)) for color in range(1, 5))
                else:
                    assert False

                if b:
                    break

        # falls die gegebene Kombination keine Bombe ist, kann sie von einer 4er-Bombe überstochen werden
        if not b and t != BOMB:
            for rhi in range(2, 15):
                b = sum(1 for v, _ in hand if v == rhi) >= 4
                if b:
                    break

        # falls die gegebene Kombination eine Farbbombe ist, kann sie von einer längeren Farbbombe überstochen werden
        if not b and t == BOMB and m >= 5:
            m2 = m + 1
            for rhi in range(m2 + 1, r + 1):
                b = any(all(sum(1 for v, c in hand if v == rhi - i and c == color) >= 1 for i in range(m2)) for color in range(1, 5))
                if b:
                    break

        # todo: Farbbombe berücksichtigen
        # # falls die gegebene Kombination keine Farbbombe ist, kann sie von einer beliebigen Farbbombe überstochen werden
        # if not b and not (t == BOMB and m >= 5):
        #     m2 = 5
        #     for rhi in range(m2 + 1, 15):
        #         b = any(all(sum(1 for v, c in hand if v == rhi - i and c == color) >= 1 for i in range(m2)) for color in range(1, 5))
        #         if b:
        #             break

        # oder beide Fälle zusammengefasst:
        # # falls die gegebene Kombination eine Farbbombe ist, kann sie von einer längeren Farbbombe überstochen werden, ansonsten von einer beliebigen
        # if not b:
        #     m2 = m + 1 if t == BOMB and m >= 5 else 5
        #     for rhi in range(m2 + 1, r + 1 if t == BOMB and m >= 5 else 15):
        #         b = any(all(sum(1 for v, c in hand if v == rhi - i and c == color) >= 1 for i in range(m2)) for color in range(1, 5))
        #         if b:
        #             break

        matches.append(b)
    return matches, hands


# -----------------------------------------------------------------------------
# Test
# -----------------------------------------------------------------------------

# if __name__ == "__main__":  # pragma: no cover
#     pass
