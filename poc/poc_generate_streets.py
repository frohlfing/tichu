# Bedingungen für eine 5er-Straße
#
# Eine Bedingung wird als Dictionary beschrieben, wobei der Key der Rang und der Wert die Anzahl (Min, Max) ist.

all_conditions = [
    # 1 - 5
    {1:(1,1), 2:(1,4), 3:(1,4), 4:(1,4), 5:(1,4)},  # oder...
    #{1:(0,0), 2:(1,4), 3:(1,4), 4:(1,4), 5:(1,4), 6:(0,0), 16:(1,1)},  # oder...
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


# Die Bedingungen müssen sich gegenseitig ausschließen!
# Zählt man die Kombinationen zusammen, die jeweils eine Bedingung erfüllen, würden die Kombinationen mehrfach gezählt werden,
# die mehrere Bedingungen erfüllen. Um dies zu korrigieren, kann man zwar das Prinzip der Inklusion und Exklusion anwenden,
# aber das kann sehr zeitintensiv bis unpraktikabel werden.
def count_intersections():
    c = 0
    length = len(all_conditions)
    for i in range(length):
        for j in range(i + 1, length):
            rangs = set(all_conditions[i].keys()).intersection(all_conditions[j].keys())  # die zu unterscheidende Ränge
            separate = False
            for r in rangs:
                a = set(range(all_conditions[i][r][0], all_conditions[i][r][1] + 1))  # z.B. Anzahl 1, 2, 3
                b = set(range(all_conditions[j][r][0], all_conditions[j][r][1] + 1))  # z.B. Anzahl 0
                if not a.intersection(b):  # die Anzahl unterscheidet sich?
                    separate = True
                    break
            if not separate:
                c += 1
                print(all_conditions[i])
                print(all_conditions[j])
                print()
    return c


# sind alle Bedingungen vorhanden?
def count_missing_conditions():
    def find_condition(cond: list):
        length = len(all_conditions)
        for i in range(length):
            match = True
            for key, (a, b) in all_conditions[i].items():
                z = 1 if key in cond else 0
                if not (a <= z <= b):
                    match = False
                    break
            if match:
                return True
        return False

    c = 0
    for r in range(5, 15):
        # ohne Phönix
        cond1 = list(range(r - 4, r + 1))
        if not find_condition(cond1):
            c += 1
            print(cond1)
        # mit Phönix
        for j in range(5):
            cond2 = cond1[:j] + cond1[j+1:] + [16]
            if not find_condition(cond2):
                c += 1
                print(cond2)
    return c


def compare_conditions(cond1, cond2):
    if len(cond1) != len(cond2):
        print("Länge unterschiedlich")
        return False

    for i, (dict1, dict2) in enumerate(zip(cond1, cond2)):
        if dict1 != dict2:
            print(f"Unterschied in Index {i}:")
            print(f"cond1: {dict1}")
            print(f"cond2: {dict2}")
            return False

    return True


# Listet alle möglichen Bedingungen für eine Straße auf
#
# Die Bedingungen schließen sich gegenseitig aus!
# Eine Bedingung wird als Dictionary beschrieben, wobei der Key der Rang und der Wert die Anzahl (Min, Max) ist.
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# m: Länge der Kombination
# r_min: niedrigster Rang der Kombination
# r_max: höchster Rang der Kombination
def get_conditions_for_street(h: list[int], m: int, r_min: int, r_max: int) -> list[dict]:
    assert 5 <= m <= 14
    assert m <= r_min <= 14
    assert r_min <= r_max <= 14
    conditions = []
    remain = {}
    for r in range(r_min, r_max + 1):
        r_start = r - m + 1
        r_end = r + 1  # exklusiv

        # ohne Phönix
        if all(h[i] >= 1 for i in range(r_start, r_end)):  # Karten für die Kombination verfügbar?
            cond = remain.copy()
            for i in range(r_start, r_end):
                cond[i] = (1, h[i])
            conditions.append(cond)
            remain[r_start] = (0, 0)  # ausschließendes Kriterium für die restlichen Bedingungen

        # mit Phönix
        if h[16]:
            for j in range(r_start + (1 if r < 14 else 0), r_end):  # Rang, den der Phönix ersetzt
                if all(h[i] >= 1 for i in range(r_start, r_end) if i != j):  # Karten für die Kombination verfügbar?
                    cond = remain.copy()
                    for i in range(r_start, r_end):
                        cond[i] = (0, 0) if i == j else (1, h[i])
                    cond[16] = (1, 1)
                    conditions.append(cond)
                    remain[r_start] = (0, 0)  # ausschließendes Kriterium für die restlichen Bedingungen

    return conditions


if __name__ == "__main__":  # pragma: no cover
    intersections = count_intersections()
    print(f"Schnittmengen: {intersections}", "ok" if intersections == 0 else "Mist :-(")

    missing_conditions = count_missing_conditions()
    print(f"Fehlende Bedingung: {missing_conditions}", "ok" if missing_conditions == 0 else "Mist :-(")

    # r= Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
    h_ = [0, 1, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 1]
    generated_conditions = get_conditions_for_street(h_, 5, 5, 14)
    ok = compare_conditions(all_conditions, generated_conditions)
    # if ok:
    #     for cond_ in generated_conditions:
    #         print(cond_)
    print("Liste richtig generiert:", ok)

    # r= Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
    h_ = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1]
    streets = get_conditions_for_street(h_, 5, 9, 14)
    for cond_ in streets:
        print(cond_)
