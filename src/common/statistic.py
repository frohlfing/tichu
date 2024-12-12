import math
import itertools
from typing import Optional


# Berechnet die Anzahl der möglichen Stichproben (ohne Zurücklegen und ohne Beachtung der Reihenfolge).
#
# Beispiel: binomial_coefficient(3, 2) = 3  ->  ((A, B), (A, C), (B, C))
#
# Randbedingungen:
# 1, wenn k == 0 (unabhängig von n)
# 0, wenn k > n
#
# n: Anzahl der Elemente gesamt
# k: Stichprobengröße
def binomial_coefficient(n: int, k: int) -> int:
    return math.comb(n, k)  # Binomialkoeffizient n über k


# Listet die möglichen Stichproben auf (ohne Zurücklegen und ohne Beachtung der Reihenfolge)
# elements: Liste der Elemente
# k: Stichprobengröße
def possible_samples(elements: list|tuple , k: int) -> list:
    return list(itertools.combinations(elements, k))


# todo raus
# Berechnet die Wahrscheinlichkeit, dass die Elemente einer Stichprobe wie angegeben verteilt sind (ohne Zurücklegen)
#
# Beispiel: In einer Urne befinden sich 20 Kugeln. Davon sind 8 rot und 5 grün. Wir ziehen 5 Kugeln.
# Wie groß ist die Wahrscheinlichkeit, dass wir 2 rote und 1 grüne ziehen?
# hypergeometric_pmf(20, 5, (8, 5), (2, 1))  # 0.18962848297213622
#
# n: Anzahl der Elemente gesamt
# k: Stichprobengröße
# features: Anzahl der einzelnen Merkmale gesamt
# condition: Anzahl der einzelnen Merkmale in der Stichprobe
def hypergeometric_pmf(n, k, features: list|tuple, condition: list|tuple) -> float:
    assert n >= 0 and k >= 0 and all(n_ >= 0 for n_ in features) and all(k_ >= 0 for k_ in condition if k_ is not None), "the numbers must be non-negative integers"
    assert k <= n, "k must be less than or equal to n"
    assert sum(features) <= n, "the sum of features must be less than or equal to n"

    kf = sum(k_ for k_ in condition if k_ is not None)
    if kf > k:
        return 0.0
    nf = sum(features[i] for i in range(len(features)) if condition[i] is not None)

    # Formel für multivariaten hypergeometrische Verteilung (Probability Mass Function, exakt, P(X = k))
    p = math.comb(n - nf, k - kf) / math.comb(n, k)
    for n_, k_ in zip(features, condition):
        if k_ is not None:
            p *= math.comb(n_, k_)

    return p


# Berechnet die Wahrscheinlichkeit, dass die Elemente einer Stichprobe wie angegeben verteilt sind (ohne Zurücklegen)
#
# Beispiel: In einer Urne befinden sich 20 Kugeln. Davon sind 8 rot, 5 grün und 3 blau. Wir ziehen 5 Kugeln.
# Wie groß ist die Wahrscheinlichkeit, dass wir 2 rote und 1 grüne oder aber 2 rote und 2 blaue ziehen?
# probability_of_samples(20, 5, (8, 5, 3), [(2, 1, None), (2, None, 2)])  # 0.21130030959752322
#
# n: Anzahl der Elemente gesamt
# k: Stichprobengröße
# features: Anzahl der einzelnen Merkmale gesamt, z.B. (8, 5, 3)
# conditions: Gefragte Anzahl der einzelnen Merkmale in der Stichprobe, z.B. [(2, 1, None), (2, None, 2)]
def probability_of_sample(n, k, features: list | tuple, conditions: list[list | tuple]) -> float:
    assert n >= 0 and k >= 0 and all(n_ >= 0 for n_ in features) and all(k_ >= 0 for condition in conditions for k_ in condition if k_ is not None), "the numbers must be non-negative integers"
    assert k <= n, "k must be less than or equal to n"
    assert sum(features) <= n, "the sum of features must be less than or equal to n"

    # ermittelt die Bedingung für eine Schnittmenge
    def union(subset: tuple) -> Optional[tuple[list, list]]:
        condition = []
        for values_of_feature in zip(*subset):
            k_ = None
            for v in values_of_feature:
                if v is not None:
                    if k_ is None:
                        k_ = v
                    elif k_ != v:
                        return None
            condition.append(k_)
        # Merkmale filtern, die für die Schnittmenge relevant sind
        return ([features[i] for i in range(len(features)) if condition[i] is not None],
                [k_ for k_ in condition if k_ is not None])

    # Formel für multivariaten hypergeometrische Verteilung
    def hypergeom(features_, condition):
        kf = sum(condition)
        if kf > k:
            return 0.0
        nf = sum(features_)
        prob = math.comb(n - nf, k - kf) / math.comb(n, k)
        for n_, k_ in zip(features_, condition):
            if k_ is not None:
                prob *= math.comb(n_, k_)
        return prob

    number_of_conditions = len(conditions)
    if number_of_conditions == 1:
        return hypergeom(features, conditions[0])

    # alle Teilmengen und alle Schnittmengen durchlaufen... (jede Bedingung erzeugt eine Teilmenge)
    p = 0.0
    for length in range(1, number_of_conditions + 1):  # Schnittmenge mit length Überlappungen
        for subset_of_conditions in itertools.combinations(conditions, length):  # Bedingungen der Überlappungen in der Schnittmenge
            # Bedingung der Schnittmenge
            result = union(subset_of_conditions)
            if result is None:
                continue

            # Wahrscheinlichkeit für die Schnittmenge
            p_subset = hypergeom(*result)

            # um Schnittmengen nicht mehrfach zu zählen, wird das Prinzip der Inklusion und Exklusion angewendet
            if length % 2 == 1:  # ungerade Anzahl Mengen in der Schnittmenge?
                p += p_subset  # Inklusion
            else:
                p -= p_subset  # Exklusion
    return p


# Berechnet die Wahrscheinlichkeit, dass maximal eine bestimmte Anzahl von Merkmalen in der Stichprobe ist.
#
# Beispiel: In einer Urne befinden sich 20 Kugeln. Davon sind 8 rot und 5 grün. Wir ziehen 5 Kugeln.
# Wie groß ist die Wahrscheinlichkeit, dass wir maximal 2 rote und maximal 1 grüne ziehen?
# hypergeometric_probability_min(20, 5, (8, 5), (2, 1))  # 0.3738390092879257
#
# n: Anzahl der Elemente gesamt
# k: Stichprobengröße
# features: Anzahl der einzelnen Merkmale gesamt
# condition_max: Maximalanzahl der einzelnen Merkmale in der Stichprobe
def hypergeometric_cdf(n, k, features: list|tuple, condition_max: list|tuple) -> float:
    assert n >= 0 and k >= 0 and all(v >= 0 for v in features) and all(v >= 0 for v in condition_max if v is not None), "the numbers must be non-negative integers"
    assert k <= n, "k must be less than or equal to n"
    assert sum(features) <= n, "the sum of features must be less than or equal to n"

    # Cumulative Distribution Function, P(X ≤ k)
    p = 0.0
    for condition in itertools.product(*[range(v_max + 1) for v_max in condition_max if v_max is not None]):
        p += hypergeometric_pmf(n, k, features, condition)
    return p


# Berechnet die Wahrscheinlichkeit, dass mindestens eine bestimmte Anzahl von Merkmalen in der Stichprobe ist
#
# Beispiel: In einer Urne befinden sich 20 Kugeln. Davon sind 8 rot und 5 grün. Wir ziehen 5 Kugeln.
# Wie groß ist die Wahrscheinlichkeit, dass wir mindestens 2 rote und mindestens 1 grüne ziehen?
# hypergeometric_probability_min(20, 5, (8, 5), (2, 1))  # 0.5192208462332302
#
# n: Anzahl der Elemente gesamt
# k: Stichprobengröße
# features: Anzahl der einzelnen Merkmale gesamt (die Summe darf nicht größer n sein)
# condition_min: Mindestanzahl der einzelnen Merkmale in der Stichprobe
def hypergeometric_ucdf(n, k, features: list|tuple, condition_min: list|tuple) -> float:
    assert n >= 0 and k >= 0 and all(v >= 0 for v in features) and all(v_min >= 0 for v_min in condition_min if v_min is not None), "the numbers must be non-negative integers"
    assert k <= n, "k must be less than or equal to n"
    assert sum(features) <= n, "the sum of features must be less than or equal to n"

    # Upper Cumulative Distribution Function, P(X ≥ k)
    p = 0.0
    for condition in itertools.product(*[range(v_min, v_max + 1) for v_min, v_max in zip(condition_min, features) if v_min is not None]):
        p += hypergeometric_pmf(n, k, features, condition)
    return p


# Listet die Stichproben auf, die exakt die gegebene Anzahl Merkmale hat
#
# Die Methode dient zur Überprüfung von hypergeometric_pmf() und hypergeometric_pmf_ext().
#
# Beispiel:
# matches, samples = hypergeometric_pmf_samples(["g1", "g2", "g3", "r1", "r2", "r3", "r4"], 5, [{"g": 2}])
# print(list(zip(matches, samples)))
# print(f"p = {sum(matches) / len(samples)}")
#
# elements: Liste der Elemente
# k: Stichprobengröße
# features: Anzahl jedes Merkmals in der Stichprobe
def hypergeometric_pmf_samples(elements: list | tuple, k: int, features: dict|list) -> tuple[list, list]:
    if isinstance(features, dict):
        features = [features]
    samples = list(itertools.combinations(elements, k))
    matches = []
    for sample in samples:
        matches.append(any(all(sum(1 for el in sample if el[0] == feature) == k_ for feature, k_ in dic.items()) for dic in features))
    return matches, samples


# Listet die Stichproben auf, die maximal die gegebene Anzahl Merkmale hat
#
# Die Methode dient zur Überprüfung von hypergeometric_cdf() und hypergeometric_cdf_ext().
#
# elements: Liste der Elemente
# k: Stichprobengröße
# features: Maximalanzahl jedes Merkmals in der Stichprobe
def hypergeometric_cdf_samples(elements: list|tuple, k: int, features: dict|list) -> tuple[list, list]:
    if isinstance(features, dict):
        features = [features]
    samples = list(itertools.combinations(elements, k))
    matches = []
    for sample in samples:
        matches.append(any(all(sum(1 for el in sample if el[0] == feature) <= k_max for feature, k_max in dic.items()) for dic in features))
    return matches, samples


# Listet die Stichproben auf, die mindestens die gegebene Anzahl Merkmale hat
#
# Die Methode dient zur Überprüfung von hypergeometric_ucdf() und hypergeometric_ucdf_ext().
#
# elements: Liste der Elemente
# k: Stichprobengröße
# features: Mindestanzahl jedes Merkmals in der Stichprobe
def hypergeometric_ucdf_samples(elements: list|tuple, k: int, features: dict|list) -> tuple[list, list]:
    if isinstance(features, dict):
        features = [features]
    samples = list(itertools.combinations(elements, k))
    matches = []
    for sample in samples:
        matches.append(any(all(sum(1 for el in sample if el[0] == feature) >= k_min for feature, k_min in dic.items()) for dic in features))
    return matches, samples


def test():
    #print(hypergeometric_pmf(7, 5, (2, 2, 2), (2, 1, None)))
    #print(hypergeometric_pmf_ext(7, 5, (2, 2, 2), [(2, 1, None)]))
    print(probability_of_sample(7, 5, (2, 2, 2), [(2, 1, None), (2, None, 2)]))


if __name__ == "__main__":  # pragma: no cover
    test()
