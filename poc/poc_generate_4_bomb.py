# Bedingungen für eine 4er-Bombe
#
# Eine Bedingung wird als Dictionary beschrieben, wobei der Key der Rang und der Wert die Anzahl (Min, Max) ist.
all_conditions = [
    {2:(4,4)},  # oder...
    {2:(0,3), 3:(4,4)},  # oder...
    {2:(0,3), 3:(0,3), 4:(4,4)},
    {2:(0,3), 3:(0,3), 4:(0,3), 5:(4,4)},
    {2:(0,3), 3:(0,3), 4:(0,3), 5:(0,3), 6:(4,4)},
    {2:(0,3), 3:(0,3), 4:(0,3), 5:(0,3), 6:(0,3), 7:(4,4)},
    {2:(0,3), 3:(0,3), 4:(0,3), 5:(0,3), 6:(0,3), 7:(0,3), 8:(4,4)},
    {2:(0,3), 3:(0,3), 4:(0,3), 5:(0,3), 6:(0,3), 7:(0,3), 8:(0,3), 9:(4,4)},
    {2:(0,3), 3:(0,3), 4:(0,3), 5:(0,3), 6:(0,3), 7:(0,3), 8:(0,3), 9:(0,3), 10:(4,4)},
    {2:(0,3), 3:(0,3), 4:(0,3), 5:(0,3), 6:(0,3), 7:(0,3), 8:(0,3), 9:(0,3), 10:(0,3), 11:(4,4)},
    {2:(0,3), 3:(0,3), 4:(0,3), 5:(0,3), 6:(0,3), 7:(0,3), 8:(0,3), 9:(0,3), 10:(0,3), 11:(0,3), 12:(4,4)},
    {2:(0,3), 3:(0,3), 4:(0,3), 5:(0,3), 6:(0,3), 7:(0,3), 8:(0,3), 9:(0,3), 10:(0,3), 11:(0,3), 12:(0,3), 13:(4,4)},
    {2:(0,3), 3:(0,3), 4:(0,3), 5:(0,3), 6:(0,3), 7:(0,3), 8:(0,3), 9:(0,3), 10:(0,3), 11:(0,3), 12:(0,3), 13:(0,3), 14:(4,4)},
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
                z = 4 if key in cond else 0
                if not (a <= z <= b):
                    match = False
                    break
            if match:
                return True
        return False

    c = 0
    for r in range(2, 15):
        cond1 = list(range(r, r + 1))
        if not find_condition(cond1):
            c += 1
            print(cond1)
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


# Listet alle möglichen Bedingungen für eine 4er-Bombe auf
#
# Die Bedingungen schließen sich gegenseitig aus!
# Eine Bedingung wird als Dictionary beschrieben, wobei der Key der Rang und der Wert die Anzahl (Min, Max) ist.
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# r_min: niedrigster Rang der Kombination
# r_max: höchster Rang der Kombination
def get_conditions_for_4_bomb(h: list[int], r_min: int, r_max: int) -> list[dict]:
    assert 2 <= r_min <= 14
    assert r_min <= r_max <= 14
    conditions = []
    remain = {}

    for r in range(r_min, r_max + 1):
        if h[r] == 4:  # Karten für die Kombination verfügbar?
            cond = remain.copy()
            cond[r] = (4, 4)
            conditions.append(cond)
            remain[r] = (0, 3)  # ausschließendes Kriterium für die restlichen Bedingungen

    return conditions


if __name__ == "__main__":  # pragma: no cover
    intersections = count_intersections()
    print(f"Schnittmengen: {intersections}", "ok" if intersections == 0 else "Mist :-(")

    missing_conditions = count_missing_conditions()
    print(f"Fehlende Bedingung: {missing_conditions}", "ok" if missing_conditions == 0 else "Mist :-(")

    # r= Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
    h_ = [0, 1, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 1]
    generated_conditions = get_conditions_for_4_bomb(h_, 2, 14)
    ok = compare_conditions(all_conditions, generated_conditions)
    # if ok:
    #     for cond_ in generated_conditions:
    #         print(cond_)
    print("Liste richtig generiert:", ok)

    # r= Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
    h_ = [0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 4, 2, 4, 2, 2, 0, 1]
    generated_conditions = get_conditions_for_4_bomb(h_, 9, 12)
    for cond_ in generated_conditions:
        print(cond_)
