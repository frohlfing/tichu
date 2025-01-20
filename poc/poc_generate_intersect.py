from poc.poc_generate_4_bomb import get_conditions_for_4_bomb
from poc.poc_generate_streets import get_conditions_for_street

# Die Bedingungen müssen sich gegenseitig ausschließen!
# Zählt man die Kombinationen zusammen, die jeweils eine Bedingung erfüllen, würden die Kombinationen mehrfach gezählt werden,
# die mehrere Bedingungen erfüllen. Um dies zu korrigieren, kann man zwar das Prinzip der Inklusion und Exklusion anwenden,
# aber das kann sehr zeitintensiv bis unpraktikabel werden.
def count_intersections(all_conditions):
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


# Erzeugt die Bedingung für die Schnittmenge zweier Teilmengen
#
# Falls die Kombinationen dieser Schnittmenge nicht auf der Hand sein können, wird ein leeres Dictionary zurückgegeben.
#
# cond1: Bedingung für Teilmenge 1
# cond2: Bedingung für Teilmenge 2
# k: Anzahl Handkarten
def get_condition_for_intersection(cond1: dict, cond2: dict, k: int) -> dict:
    keys = set(cond1.keys()).union(cond2.keys())
    union_set = {}
    c_min_total = 0
    for key in keys:
        v1 = cond1.get(key, (0, 4))
        v2 = cond2.get(key, (0, 4))
        c_min = max(v1[0], v2[0])  # Mindestanzahl notwendiger Karten für Schnittmenge
        c_max = min(v1[1], v2[1])  # Maximalanzahl notwendiger Karten für Schnittmenge
        if c_min > c_max:
            return {}  # keine Überschneidung
        c_min_total += c_min
        if c_min_total > k:
            return {}  # zu viele Karten notwendig, um beide Kombinationen gleichzeit auf der Hand zu haben
        union_set[key] = (c_min, c_max)
    return union_set


# Erzeugt die Bedingung für die Schnittmenge zweier Teilmengen
#
# Es werden alle Bedingungen für Teilmenge 1 mit allen Bedingungen für Teilmenge 2 kombiniert und jeweils die
# Bedingung für die Schnittmenge berechnet. Falls Kombinationen dieser Schnittmenge auf der Hand sein können,
# wird die kombinierte Bedingung aufgelistet.
#
# conditions1: Liste mit Bedingungen für Teilmenge 1
# conditions2: Liste mit Bedingungen für Teilmenge 2
# k: Anzahl Handkarten
def get_conditions_for_intersection(conditions1: list[dict], conditions2: list[dict], k: int) -> list[dict]:
    conditions = []
    for cond1 in conditions1:
        for cond2 in conditions2:
            cond_intersect = get_condition_for_intersection(cond1, cond2, k)
            if cond_intersect:
                conditions.append(cond_intersect)
    return conditions


if __name__ == "__main__":  # pragma: no cover


    # r= Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
    h_ = [0, 1, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 1]

    print("Straße")
    streets = get_conditions_for_street(h_, 5, 14, 14)
    for cond_ in streets:
        print(cond_)

    print("Bombe")
    bombs = get_conditions_for_4_bomb(h_, 13, 14)
    for cond_ in bombs:
        print(cond_)

    print("Straße + Bombe")
    conditions = get_conditions_for_intersection(streets, bombs, 14)
    for cond_ in conditions:
        print(cond_)

    expected = [
        {10: (1, 4), 11: (1, 4), 12: (1, 4), 13: (4, 4), 14: (1, 4)},
        {10: (1, 4), 11: (1, 4), 12: (1, 4), 13: (1, 3), 14: (4, 4)},
        {16: (1, 1), 10: (0, 0), 11: (1, 4), 12: (1, 4), 13: (4, 4), 14: (1, 4)},
        {16: (1, 1), 10: (0, 0), 11: (1, 4), 12: (1, 4), 13: (1, 3), 14: (4, 4)},
        {16: (1, 1), 10: (1, 4), 11: (0, 0), 12: (1, 4), 13: (4, 4), 14: (1, 4)},
        {16: (1, 1), 10: (1, 4), 11: (0, 0), 12: (1, 4), 13: (1, 3), 14: (4, 4)},
        {16: (1, 1), 10: (1, 4), 11: (1, 4), 12: (0, 0), 13: (4, 4), 14: (1, 4)},
        {16: (1, 1), 10: (1, 4), 11: (1, 4), 12: (0, 0), 13: (1, 3), 14: (4, 4)},
        {16: (1, 1), 10: (1, 4), 11: (1, 4), 12: (1, 4), 13: (0, 0), 14: (4, 4)},
        {16: (1, 1), 10: (1, 4), 11: (1, 4), 12: (1, 4), 13: (4, 4), 14: (0, 0)},
    ]

    # print(f"Anzahl Straßen: {len(streets)}",  "ok" if len(streets) == 6 else "Mist :-(")
    # print(f"Anzahl Bomben: {len(bombs)}",  "ok" if len(bombs) == 2 else "Mist :-(")
    # print(f"Anzahl Straße mit Bombe: {len(conditions)}",  "ok" if len(conditions) == len(expected) else "Mist :-(")

    ok = compare_conditions(expected, conditions)
    print("Liste richtig generiert:", ok)
