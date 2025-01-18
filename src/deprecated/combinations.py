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


# -----------------------------------------------------------------------------
# Test
# -----------------------------------------------------------------------------

# if __name__ == "__main__":  # pragma: no cover
#     pass
