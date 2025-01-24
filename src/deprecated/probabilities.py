# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# m: Länge der Kombination
# r_min: niedrigster Rang der Kombination
# r_max: höchster Rang der Kombination
def _get_conditions_for_street(h: list[int], m: int, r_min: int, r_max: int) -> list[dict]:
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


# Listet alle möglichen Bedingungen für eine 4er-Bombe auf
#
# Die Bedingungen schließen sich gegenseitig aus!
# Eine Bedingung wird als Dictionary beschrieben, wobei der Key der Rang und der Wert die Anzahl (Min, Max) ist.
#
# h: Verfügbaren Karten als Vektor (Index entspricht den Rang)
# r_min: niedrigster Rang der Kombination
# r_max: höchster Rang der Kombination
def _get_conditions_for_4_bomb(h: list[int], r_min: int, r_max: int) -> list[dict]:
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


# Erzeugt die Bedingung für die Schnittmenge zweier Teilmengen
#
# Falls die Kombinationen dieser Schnittmenge nicht auf der Hand sein können, wird ein leeres Dictionary zurückgegeben.
#
# cond1: Bedingung für Teilmenge 1
# cond2: Bedingung für Teilmenge 2
# k: Anzahl Handkarten
def _get_condition_for_intersection(cond1: dict, cond2: dict, k: int) -> dict:
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
            cond_intersect = _get_condition_for_intersection(cond1, cond2, k)
            if cond_intersect:
                conditions.append(cond_intersect)
    return conditions


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
    t, m, _r = figure
    if t == BOMB and m >= 5:  # Farbbombe
        h = cards_to_vector(cards)
    else:
        h = ranks_to_vector(cards)  # wenn es keine Farbbombe ist, sind nur die Ränge der Karten von Interesse

    #print(h)

    # Bedingungen für eine Kombination auflisten, die die gegebene übersticht
    conditions = get_conditions(h, figure)

    # Anzahl Kombinationen mittels hypergeometrische Verteilung ermitteln
    matches = 0
    for cond in conditions:
        matches_part = hypergeom(cond, h, k)
        #print(cond, matches_part)
        matches += matches_part

    # Anzahl der 4er-Bomben hinzufügen
    if t != BOMB:
        conditions_bomb = _get_conditions_for_4_bomb(h, 2, 14)
        for cond in conditions_bomb:
            matches += hypergeom(cond, h, k)
        # die Schnittmenge wieder abziehen (Prinzip der Inklusion und Exklusion)
        conditions_intersection = get_conditions_for_intersection(conditions, conditions_bomb, k)
        for cond in conditions_intersection:
            matches -= hypergeom(cond, h, k)
        assert matches >= 0

    if matches == 0:
        return 0

    # Gesamtanzahl der möglichen Kombinationen
    total = math.comb(n, k)

    # Wahrscheinlichkeit
    p = matches / total
    return p



# Generiert alle möglichen Kombinationen
# Beispiel: ranges = [(1, 2), (1, 1), (1, 3)]
# Rückgabe:
# [(1, 1, 1),
#  (1, 1, 2),
#  (1, 1, 3),
#  (2, 1, 1),
#  (2, 1, 2),
#  (2, 1, 3)]
def generate_subsets(ranges: list) -> list:
    # Generiere die Tabelle
    subsets = []
    for subset in itertools.product(*[range(start, end + 1) for start, end in ranges]):
        subsets.append(subset)
        #print(row)
    return subsets
