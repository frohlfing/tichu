# Alle Teilmengen, die eine 5er-Straße abbilden
#
# Die Teilmengen überlappen sich nicht.
#
# Die Teilmenge wird als Dictionary beschrieben, wobei der Key der Rang und der Wert der Bereich zw. Mindestanzahl und
# Maximalanzahl (einschließlich) von Karten mit diesem Rang ist.

subsets = [
    # 1 - 5
    {1:(1,1), 2:(1,4), 3:(1,4), 4:(1,4), 5:(1,4)},
    #{1:(0,0), 2:(3,1), 3:(1,4), 4:(1,4), 5:(1,4), 6:(0,0), 16:(1,1)},
    {1:(1,1), 2:(0,0), 3:(1,4), 4:(1,4), 5:(1,4), 16:(1,1)},
    {1:(1,1), 2:(1,4), 3:(0,0), 4:(1,4), 5:(1,4), 16:(1,1)},
    {1:(1,1), 2:(1,4), 3:(1,4), 4:(0,0), 5:(1,4), 16:(1,1)},
    {1:(1,1), 2:(1,4), 3:(1,4), 4:(1,4), 5:(0,0), 16:(1,1)},

    # 2 - 6
    {1:(0,0), 2:(1,4), 3:(1,4), 4:(1,4), 5:(1,4), 6:(1,4)},
    #{1:(0,0), 2:(0,0), 3:(1,4), 4:(1,4), 5:(1,4), 6:(1,4), 7:(0,0), 16:(1,1)},
    {1:(0,0), 2:(1,4), 3:(0,0), 4:(1,4), 5:(1,4), 6:(1,4), 16:(1,1)},
    {1:(0,0), 2:(1,4), 3:(1,4), 4:(0,0), 5:(1,4), 6:(1,4), 16:(1,1)},
    {1:(0,0), 2:(1,4), 3:(1,4), 4:(1,4), 5:(0,0), 6:(1,4), 16:(1,1)},
    {1:(0,0), 2:(1,4), 3:(1,4), 4:(1,4), 5:(1,4), 6:(0,0), 16:(1,1)},

    # 3 - 7
    {1:(0,0), 2:(0,0), 3:(1,4), 4:(1,4), 5:(1,4), 6:(1,4), 7:(1,4)},
    #{1:(0,0), 2:(0,0), 3:(0,0), 4:(1,4), 5:(1,4), 6:(1,4), 7:(1,4), 8:(0,0), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(1,4), 4:(0,0), 5:(1,4), 6:(1,4), 7:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(1,4), 4:(1,4), 5:(0,0), 6:(1,4), 7:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(1,4), 4:(1,4), 5:(1,4), 6:(0,0), 7:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(1,4), 4:(1,4), 5:(1,4), 6:(1,4), 7:(0,0), 16:(1,1)},

    # 4 - 8
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(1,4), 5:(1,4), 6:(1,4), 7:(1,4), 8:(1,4)},
    #{1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(1,4), 6:(1,4), 7:(1,4), 8:(1,4), 9:(0,0), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(1,4), 5:(0,0), 6:(1,4), 7:(1,4), 8:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(1,4), 5:(1,4), 6:(0,0), 7:(1,4), 8:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(1,4), 5:(1,4), 6:(1,4), 7:(0,0), 8:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(1,4), 5:(1,4), 6:(1,4), 7:(1,4), 8:(0,0), 16:(1,1)},

    # 5 - 9
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(1,4), 6:(1,4), 7:(1,4), 8:(1,4), 9:(1,4)},
    #{1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(1,4), 7:(1,4), 8:(1,4), 9:(1,4), 10:(0,0), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(1,4), 6:(0,0), 7:(1,4), 8:(1,4), 9:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(1,4), 6:(1,4), 7:(0,0), 8:(1,4), 9:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(1,4), 6:(1,4), 7:(1,4), 8:(0,0), 9:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(1,4), 6:(1,4), 7:(1,4), 8:(1,4), 9:(0,0), 16:(1,1)},

    # 6 - 10
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(1,4), 7:(1,4), 8:(1,4), 9:(1,4), 10:(1,4)},
    #{1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(1,4), 8:(1,4), 9:(1,4), 10:(1,4), 11:(0,0), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(1,4), 7:(0,0), 8:(1,4), 9:(1,4), 10:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(1,4), 7:(1,4), 8:(0,0), 9:(1,4), 10:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(1,4), 7:(1,4), 8:(1,4), 9:(0,0), 10:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(1,4), 7:(1,4), 8:(1,4), 9:(1,4), 10:(0,0), 16:(1,1)},

    # 7 - 11
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(1,4), 8:(1,4), 9:(1,4), 10:(1,4), 11:(1,4)},
    #{1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(0,0), 8:(1,4), 9:(1,4), 10:(1,4), 11:(1,4), 12:(0,0), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(1,4), 8:(0,0), 9:(1,4), 10:(1,4), 11:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(1,4), 8:(1,4), 9:(0,0), 10:(1,4), 11:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(1,4), 8:(1,4), 9:(1,4), 10:(0,0), 11:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(1,4), 8:(1,4), 9:(1,4), 10:(1,4), 11:(0,0), 16:(1,1)},

    # 8 - 12
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(0,0), 8:(1,4), 9:(1,4), 10:(1,4), 11:(1,4), 12:(1,4)},
    #{1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(0,0), 8:(0,0), 9:(1,4), 10:(1,4), 11:(1,4), 12:(1,4), 13:(0,0), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(0,0), 8:(1,4), 9:(0,0), 10:(1,4), 11:(1,4), 12:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(0,0), 8:(1,4), 9:(1,4), 10:(0,0), 11:(1,4), 12:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(0,0), 8:(1,4), 9:(1,4), 10:(1,4), 11:(0,0), 12:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(0,0), 8:(1,4), 9:(1,4), 10:(1,4), 11:(1,4), 12:(0,0), 16:(1,1)},

    # 9 - 13
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(0,0), 8:(0,0), 9:(1,4), 10:(1,4), 11:(1,4), 12:(1,4), 13:(1,4)},
    #{1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(0,0), 8:(0,0), 9:(0,0), 10:(1,4), 11:(1,4), 12:(1,4), 13:(1,4), 14:(0,0), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(0,0), 8:(0,0), 9:(1,4), 10:(0,0), 11:(1,4), 12:(1,4), 13:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(0,0), 8:(0,0), 9:(1,4), 10:(1,4), 11:(0,0), 12:(1,4), 13:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(0,0), 8:(0,0), 9:(1,4), 10:(1,4), 11:(1,4), 12:(0,0), 13:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(0,0), 8:(0,0), 9:(1,4), 10:(1,4), 11:(1,4), 12:(1,4), 13:(0,0), 16:(1,1)},

    # 10 - 14
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(0,0), 8:(0,0), 9:(0,0), 10:(1,4), 11:(1,4), 12:(1,4), 13:(1,4), 14:(1,4)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(0,0), 8:(0,0), 9:(0,0), 10:(0,0), 11:(1,4), 12:(1,4), 13:(1,4), 14:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(0,0), 8:(0,0), 9:(0,0), 10:(1,4), 11:(0,0), 12:(1,4), 13:(1,4), 14:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(0,0), 8:(0,0), 9:(0,0), 10:(1,4), 11:(1,4), 12:(0,0), 13:(1,4), 14:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(0,0), 8:(0,0), 9:(0,0), 10:(1,4), 11:(1,4), 12:(1,4), 13:(0,0), 14:(1,4), 16:(1,1)},
    {1:(0,0), 2:(0,0), 3:(0,0), 4:(0,0), 5:(0,0), 6:(0,0), 7:(0,0), 8:(0,0), 9:(0,0), 10:(1,4), 11:(1,4), 12:(1,4), 13:(1,4), 14:(0,0), 16:(1,1)},
]


# Die Teilmengen dürfen sich nicht überlappen!
# Wenn Teilmengen sich überlappen, sich also gegenseitig nicht ausschließen, können mehrere auf derselben Hand sein.
# Zählt man die Kombinationen zusammen, die die Teilmengen beinhalten, würden die Schnittmengen der überlappenden Teilmengen
# mehrfach gezählt. Um dies zu korrigieren, kann man das Prinzip der Inklusion und Exklusion auf die Vereinigungsmengen dieser
# überlappenden Teilmengen anwenden. Das Bilden der Vereinigungsmengen kann jedoch sehr zeitintensiv bis unpraktikabel sein.
# Das gilt daher zu vermeiden.
def count_intersections():
    c = 0
    length = len(subsets)
    for i in range(length):
        for j in range(i + 1, length):
            rangs = set(subsets[i].keys()).intersection(subsets[j].keys())  # die zu unterscheidende Ränge
            separate = False
            for r in rangs:
                a = set(range(subsets[i][r][0], subsets[i][r][1] + 1))  # z.B. Anzahl 1, 2, 3
                b = set(range(subsets[j][r][0], subsets[j][r][1] + 1))  # z.B. Anzahl 0
                if not a.intersection(b):  # die Anzahl unterscheidet sich?
                    separate = True
                    break
            if not separate:
                c += 1
                print(subsets[i])
                print(subsets[j])
                print()
    return c


# sind alle Teilmengen vorhanden?
def count_missing_subsets():
    def find_subset(subset: list):
        length = len(subsets)
        for i in range(length):
            match = True
            for key, (a, b) in subsets[i].items():
                z = 1 if key in subset else 0
                if not (a <= z <= b):
                    match = False
                    break
            if match:
                return True
        return False

    c = 0
    for r in range(5, 15):
        # ohne Phönix
        subset1 = list(range(r - 4, r + 1))
        if not find_subset(subset1):
            c += 1
            print(subset1)
        # mit Phönix
        for j in range(5):
            subset2 = subset1[:j] + subset1[j+1:] + [16]
            if not find_subset(subset2):
                c += 1
                print(subset2)
    return c


def compare_subsets(subsets1, subsets2):
    if len(subsets1) != len(subsets2):
        print("Länge unterschiedlich")
        return False

    for i, (dict1, dict2) in enumerate(zip(subsets1, subsets2)):
        if dict1 != dict2:
            print(f"Unterschied in Index {i}:")
            print(f"subsets1: {dict1}")
            print(f"subsets2: {dict2}")
            return False

    return True


# Generiert alle möglichen Teilmengen für 5er-Straßen
def generate_subsets():
    m = 5
    result = []
    for r in range(5, 15):
        # ohne Phönix
        subset = {i: (0, 0) if i <= r - m else (1, 1) if i == 1 else (1, 4) for i in range(1, r + 1)}
        result.append(subset)
        # mit Phönix
        for j in range(r - m + (2 if r < 14 else 1), r + 1):
            subset = {i: (0, 0) if i <= r - m or i == j else (1, 1) if i == 1 else (1, 4) for i in range(1, r + 1)}
            subset[16] = (1, 1)
            result.append(subset)
    return result


# Listet alle Teilmengen aus den verfügbaren Karten auf, die eine Straße im angegebenen Bereich bilden
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# m: Länge der Kombination
# r_min: niedrigster Rang der Kombination
# r_max: höchster Rang der Kombination
def _get_subsets_of_streets(h: list[int], m: int, r_min: int, r_max: int) -> list[dict]:
    assert 5 <= m <= 14
    assert m <= r_min <= 14
    assert r_min <= r_max <= 14
    r_first = r_min - m + 1
    subsets = []
    for r in range(r_min, r_max + 1):
        # ohne Phönix
        if all(h[i] >= 1 for i in range(r - m + 1, r + 1)):
            subset = {i: (0, 0) if i <= r - m else (1, h[i]) for i in range(r_first, r + 1)}
            subsets.append(subset)
        # mit Phönix
        for j in range(r - m + (2 if r < 14 else 1), r + 1):
            if all(h[i] >= 1 for i in range(r - m + 1, r + 1) if i != j):
                subset = {i: (0, 0) if i <= r - m or i == j else (1, h[i]) for i in range(r_first, r + 1)}
                subset[16] = (1, 1)
                subsets.append(subset)
    return subsets



if __name__ == "__main__":  # pragma: no cover
    # intersections = count_intersections()
    # print(f"Schnittmengen: {intersections}", "ok" if intersections == 0 else "Mist :-(")

    # missing_subsets = count_missing_subsets()
    # print(f"Fehlende Teilmengen: {missing_subsets}", "ok" if missing_subsets == 0 else "Mist :-(")

    # subsets2 = generate_subsets()
    # ok = compare_subsets(subsets, subsets2)
    # if ok:
    #     for subset in subsets2:
    #         print(subset)
    # print("Liste richtig generiert:", ok)

    # # r=Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
    # h = [0, 1, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 1]
    # subsets2 = _get_subsets_of_streets(h, 5, 5, 14)
    # ok = compare_subsets(subsets, subsets2)
    # if ok:
    #     for subset in subsets2:
    #         print(subset)
    # print("Liste richtig generiert:", ok)

    # r=Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
    h = [0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 1]
    subsets3 = _get_subsets_of_streets(h, 5, 9, 12)
    for subset in subsets3:
        print(subset)
