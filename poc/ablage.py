import config
import itertools
import math





# Listet die Straßen auf, die die gegebene Straße überstechen
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# m: Länge der Kombination
# r_min: niedrigster Rang der Kombination
# r_max: höchster Rang der Kombination
def get_streets(h: list[int], m: int, r_min: int, r_max: int) -> list[dict]:
    assert 5 <= m <= 14
    assert m <= r_min <= 14
    assert r_min <= r_max <= 14

    data = load_data()

    result = []
    for pho, r, top in data:
        r_start = r - m + 1
        r_end = r + 1  # exklusiv
        if pho:
            # mit Phönix
            pass
        else:
            # ohne Phönix
            if (all(h[i] >= 1 for i in range(r_start, r_end))
            and all(h[i] >= 1 for i in range(r_end, 15) if top[i - r_end] >= 1)):
                ranges_comb = [(1, h[i]) for i in range(r_start, r_end)]
                sets_comb = tuple(itertools.product(*ranges_comb))
                ranges_top = [(1, h[i]) for i in range(r_end, 15) if top[i - r_end] >= 1]
                sets_top = tuple(itertools.product(*ranges_top))
                result.append((r, sets_comb, sets_top))

        # # mit Phönix
        # if h[16]:
        #     for j in range(r_start + (1 if r < 14 else 0), r_end):  # Rang, den der Phönix ersetzt
        #         if all(h[i] >= 1 for i in range(r_start, r_end) if i != j):  # Karten für die Kombination verfügbar?
        #             cond = remain.copy()
        #             for i in range(r_start, r_end):
        #                 cond[i] = (0, 0) if i == j else (1, h[i])
        #             cond[16] = (1, 1)
        #             sets.append(cond)

    return result


# Berechnet die Wahrscheinlichkeit, dass die Hand die gegebene Kombination überstechen kann
#
# todo:
#  Falls die gegebene Kombination eine Farbbombe ist, kann sie von einer längeren Farbbombe überstochen werden, was auch berücksichtigt wird.
#  Falls die gegebene Kombination aber keine Farbbombe ist, kann sie von einer beliebigen Farbbombe überstochen werden, was NICHT berücksichtigt wird!
#  Ausnahme: Falls die gegebene Kombination eine Straße ist, wird eine Farbbombe, die einen höheren Rang hat, berücksichtigt.
#
# cards: Verfügbare Karten
# k: Anzahl der Handkarten
# figure: Typ, Länge und Rang der gegebenen Kombination
# r: Rang der gegebenen Kombination
def prob_of_hand(cards: list[tuple], k: int, figure: tuple) -> float:
    n = len(cards)  # Gesamtanzahl der verfügbaren Karten
    assert k <= n <= 56
    assert 0 <= k <= 14

    # die verfügbaren Karten in einen Vektor umwandeln
    t, m, r = figure
    h = ranks_to_vector(cards)  # wenn es keine Farbbombe ist, sind nur die Ränge der Karten von Interesse

    # Teilmengen finden, die die gegebene Kombination überstechen
    subsets = get_streets(h, m, r + 1, 14)

    # Anzahl Kombinationen mittels hypergeometrische Verteilung ermitteln
    matches = 0
    for subset in subsets:
        matches_part = hypergeom(subset, h, k)
        #print(subset, matches_part)
        matches += matches_part

    # # Anzahl der 4er-Bomben hinzufügen
    # if t != BOMB:
    #     conditions_bomb = _get_conditions_for_4_bomb(h, 2, 14)
    #     for cond in conditions_bomb:
    #         matches += hypergeom(cond, h, k)
    #     # die Schnittmenge wieder abziehen (Prinzip der Inklusion und Exklusion)
    #     conditions_intersection = get_conditions_for_intersection(subsets, conditions_bomb, k)
    #     for cond in conditions_intersection:
    #         matches -= hypergeom(cond, h, k)
    #     assert matches >= 0

    if matches == 0:
        return 0.0

    # Gesamtanzahl der möglichen Kombinationen
    total = math.comb(n, k)

    # Wahrscheinlichkeit
    p = matches / total

    return p

