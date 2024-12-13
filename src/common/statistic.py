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
# probability_of_sample(20, 5, (8, 5, 3), [(2, 1, None), (2, None, 2)], "==")  # 0.21130030959752322
#
# n: Anzahl der Elemente gesamt
# k: Stichprobengröße
# features: Anzahl der einzelnen Merkmale gesamt, z.B. (8, 5, 3)
# conditions: Gefragte Anzahl der einzelnen Merkmale in der Stichprobe, z.B. [(2, 1, None), (2, None, 2)]
# operator: "==" (conditions == exakte Anzahl), "<=" (conditions == Maximalanzahl), ">=" conditions == Mindestanzahl)
def probability_of_sample(n, k, features: list|tuple, conditions: list[list|tuple], operator="==") -> float:
    assert n >= 0 and k >= 0 and all(n_ >= 0 for n_ in features) and all(k_ >= 0 for condition in conditions for k_ in condition if k_ is not None), "the numbers must be non-negative integers"
    assert k <= n, "k must be less than or equal to n"
    assert sum(features) <= n, "the sum of features must be less than or equal to n"
    assert operator in ("==", "<=", ">=")

    def union(subset: tuple) -> Optional[tuple[list, list]]:
        # Ermittelt die Bedingung für eine Schnittmenge
        condition = []
        for values_of_feature in zip(*subset):
            k_ = None
            if operator == ">=":
                for v in values_of_feature:
                    if v is not None and (k_ is None or k_ < v):
                        k_ = v
            elif operator == "<=":
                for v in values_of_feature:
                    if v is not None and (k_ is None or k_ > v):
                        k_ = v
            else:  # "=="
                for v in values_of_feature:
                    if v is not None:
                        if k_ is None:
                            k_ = v
                        elif k_ != v:
                            return None
            condition.append(k_)
        return ([features[i] for i in range(len(features)) if condition[i] is not None],
                [k_ for k_ in condition if k_ is not None])

    def hypergeom_pmf(features_: list|tuple, condition: list|tuple) -> float:
        # Probability Mass Function für (multivariaten) hypergeometrische Verteilung, P(X = k)
        kf = sum(condition)
        if kf > k:
            return 0.0
        nf = sum(features_)
        prob = math.comb(n - nf, k - kf) / math.comb(n, k)
        for n_, k_ in zip(features_, condition):
            if k_ is not None:
                prob *= math.comb(n_, k_)
        return prob

    def hypergeom_cdf(features_: list|tuple, condition_max: list|tuple) -> float:
        # Cumulative Distribution Function für hypergeometrische Verteilung, P(X ≤ k)
        prob = 0.0
        for condition in itertools.product(*[range(v_max + 1) for v_max in condition_max if v_max is not None]):
            prob += hypergeom_pmf(features_, condition)
        return prob

    def hypergeom_ucdf(features_: list|tuple, condition_min: list|tuple) -> float:
        # Upper Cumulative Distribution Function für hypergeometrische Verteilung, P(X ≥ k)
        prob = 0.0
        for condition in itertools.product(*[range(v_min, v_max + 1) for v_min, v_max in zip(condition_min, features) if v_min is not None]):
            prob += hypergeom_pmf(features_, condition)
        return prob

    number_of_conditions = len(conditions)
    if number_of_conditions == 1:
        if operator == ">=":
            return hypergeom_ucdf(features, conditions[0])
        if operator == "<=":
            return hypergeom_cdf(features, conditions[0])
        return hypergeom_pmf(features, conditions[0])

    # alle Teilmengen und alle Schnittmengen durchlaufen... (jede Bedingung erzeugt eine Teilmenge)
    p = 0.0
    for length in range(1, number_of_conditions + 1):  # Schnittmenge mit length Überlappungen
        for subset_of_conditions in itertools.combinations(conditions, length):  # Bedingungen der Überlappungen in der Schnittmenge
            # Bedingung der Schnittmenge
            result = union(subset_of_conditions)
            if result is None:
                continue

            # Wahrscheinlichkeit für die Schnittmenge
            if operator == ">=":
                p_subset = hypergeom_ucdf(*result)
            elif operator == "<=":
                p_subset = hypergeom_cdf(*result)
            else:
                p_subset = hypergeom_pmf(*result)

            # um Schnittmengen nicht mehrfach zu zählen, wird das Prinzip der Inklusion und Exklusion angewendet
            if length % 2 == 1:  # ungerade Anzahl Mengen in der Schnittmenge?
                p += p_subset  # Inklusion
            else:
                p -= p_subset  # Exklusion
    return p


# Listet die Stichproben auf, die die gegebene Anzahl Merkmale hat
#
# Die Methode dient zur Überprüfung von probability_of_sample().
#
# Beispiel:
# matches, samples = match_samples(["g1", "g2", "g3", "r1", "r2", "r3", "r4"], 5, [{"g": 2}], "==")
# print(list(zip(matches, samples)))
# print(f"p = {sum(matches) / len(samples)}")
#
# elements: Liste der Elemente
# k: Stichprobengröße
# features: Anzahl jedes Merkmals in der Stichprobe
# operator: "==" (conditions == exakte Anzahl), "<=" (conditions == Maximalanzahl), ">=" conditions == Mindestanzahl)
def match_samples(elements: list | tuple, k: int, features: dict | list, operator="==") -> tuple[list, list]:
    assert operator in ("==", "<=", ">=")

    if isinstance(features, dict):
        features = [features]

    samples = list(itertools.combinations(elements, k))

    matches = []
    if operator == "<=":
        # Cumulative Distribution Function, P(X ≤ k)
        for sample in samples:
            matches.append(any(all(sum(1 for el in sample if el[0] == feature) <= k_max for feature, k_max in dic.items()) for dic in features))

    elif operator == ">=":
        # Upper Cumulative Distribution Function, P(X ≥ k)
        for sample in samples:
            matches.append(any(all(sum(1 for el in sample if el[0] == feature) >= k_min for feature, k_min in dic.items()) for dic in features))

    else:  # "=="
        # Probability Mass Function, P(X = k)
        for sample in samples:
            matches.append(any(all(sum(1 for el in sample if el[0] == feature) == k_ for feature, k_ in dic.items()) for dic in features))

    return matches, samples


def test():  # pragma: no cover
    #print(hypergeometric_pmf(7, 5, (2, 2, 2), (2, 1, None)))
    #print(hypergeometric_pmf_ext(7, 5, (2, 2, 2), [(2, 1, None)]))
    print(probability_of_sample(7, 5, (2, 2, 2), [(2, 1, None), (2, None, 2)], "=="))


if __name__ == "__main__":  # pragma: no cover
    test()
