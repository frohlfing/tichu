import math
import itertools


# Binomialkoeffizient (n über k)
# Berechnet die Anzahl der möglichen Stichproben (ohne Zurücklegen und ohne Beachtung der Reihenfolge).
#
# Beispiel: comb(3, 2) = 3  ->  ((A, B), (A, C), (B, C))
#
# Randbedingungen:
# 1, wenn k == 0 (unabhängig von n)
# 0, wenn k > n
#
# n: Anzahl der Elemente gesamt
# k: Stichprobengröße
def binomial_coefficient(n: int, k: int) -> int:
    return math.comb(n, k)


# Listet die möglichen Stichproben auf (ohne Zurücklegen und ohne Beachtung der Reihenfolge)
# elements: Liste der Elemente
# k: Stichprobengröße
def possible_samples(elements: list|tuple , k: int) -> list:
    return list(itertools.combinations(elements, k))


# Multivariaten hypergeometrische Verteilung - Probability Mass Function, P(X = k)
#
# Berechnet die Wahrscheinlichkeit, dass die Elemente einer Stichprobe wie angegeben verteilt sind (ohne Zurücklegen).
# Dabei wird das Inklusion-Exklusion-Prinzip verwendet, um mehrfache Zählungen der Schnittmenge zu vermeiden.
#
# Beispiel: In einer Urne befinden sich 20 Kugeln. Davon sind 8 rot und 5 grün. Wir ziehen 5 Kugeln.
# Wie groß ist die Wahrscheinlichkeit, dass wir 2 rote und 1 grüne ziehen?
# hypergeometric_pmf(20, 5, (8, 5), (2, 1))  # 0.18962848297213622
#
# Beispiel 2: In einer Urne befinden sich 20 Kugeln. Davon sind 8 rot, 5 grün und 3 gelb. Wir ziehen 5 Kugeln.
# Wie groß ist die Wahrscheinlichkeit, dass wir 2 rote und 1 grüne oder aber 2 rote und 2 gelbe ziehen?
# hypergeometric_pmf(20, 5, (8, 5, 3), [(2, 1, None), (2, None, 2)])  # 0.07467722301565241
#
# n: Anzahl der Elemente gesamt
# k: Stichprobengröße
# n_features: Anzahl der einzelnen Merkmale gesamt
# k_features: Anzahl der einzelnen Merkmale in der Stichprobe
def hypergeometric_pmf_old(n, k, n_features: list|tuple, k_features: list|tuple) -> float:
    assert n >= 0 and k >= 0 and all(n_ >= 0 for n_ in n_features) and all(k_ >= 0 for k_ in k_features), "n and k must be non-negative integers"
    assert k <= n, "k must be less than or equal to n"
    nf = sum(n_features)
    assert nf <= n, "the sum of n_features must be less than or equal to n"

    kf = sum(k_features)
    p = math.comb(n - nf, k - kf) / math.comb(n, k) if kf <= k else 0.0
    for n_, k_ in zip(n_features, k_features):
        p *= math.comb(n_, k_)
    return p


def hypergeometric_pmf(n, k, n_features: list|tuple, k_conditions: list|tuple) -> float:
    assert n >= 0 and k >= 0 and all(n_ >= 0 for n_ in n_features), "n and k must be non-negative integers"
    assert k <= n, "k must be less than or equal to n"
    nf = sum(n_features)
    assert nf <= n, "the sum of n_features must be less than or equal to n"
    p_total = 0.0
    for c in range(len(k_conditions)):
        for subset in itertools.combinations(k_conditions, c + 1):
            p = 1.0
            for k_features in subset:
                if k_features is not None:
                    kf = sum(k_ for k_ in k_features if k_ is not None)
                    p *= math.comb(n - nf, k - kf) / math.comb(n, k) if kf <= k else 0.0
                    for n_, k_ in zip(n_features, k_features):
                        if k_ is not None:
                            p *= math.comb(n_, k_)
            p_total += (-1) ** (c + 2) * p
    return p_total



def hypergeometric_pmf_(n, k, n_features: list | tuple, k_conditions: list | tuple) -> float:
    assert n >= 0 and k >= 0 and all(n_ >= 0 for n_ in n_features), "n and k must be non-negative integers"
    assert k <= n, "k must be less than or equal to n"
    nf = sum(n_features)
    assert nf <= n, "the sum of n_features must be less than or equal to n"

    def comb(n, k):
        return math.comb(n, k) if k <= n else 0

    def condition_prob(n, k, n_features, k_features):
        p = comb(n - sum(n_features), k - sum(k_ for k_ in k_features if k_ is not None)) / comb(n, k)
        for n_, k_ in zip(n_features, k_features):
            if k_ is not None:
                p *= comb(n_, k_)
        return p

    total_prob = 0.0
    for r in range(1, len(k_conditions) + 1):
        for subset in itertools.combinations(k_conditions, r):
            subset_prob = 1.0
            for k_features in subset:
                subset_prob *= condition_prob(n, k, n_features, k_features)
            total_prob += (-1) ** (r + 1) * subset_prob

    return total_prob



# Hypergeometrische Verteilung - Cumulative Distribution Function, P(X ≤ k)
#
# Berechnet die Wahrscheinlichkeit, dass maximal eine bestimmte Anzahl von Merkmalen in der Stichprobe ist
#
# Beispiel: In einer Urne befinden sich 20 Kugeln. Davon sind 8 rot und 5 grün.
# Wir ziehen 5 Kugeln. Wie groß ist die Wahrscheinlichkeit, dass wir maximal 2 rote und maximal 1 grüne ziehen?
# hypergeometric_probability_min(20, 5, (8, 5), (2, 1))  # 0.3738390092879257
#
# n: Anzahl der Elemente gesamt
# k: Stichprobengröße
# n_features: Anzahl der einzelnen Merkmale gesamt
# k_max_features: Maximalanzahl der einzelnen Merkmale in der Stichprobe
def hypergeometric_cdf(n, k, n_features: list|tuple, k_max_features: list|tuple) -> float:
    assert n >= 0 and k >= 0 and all(n_ >= 0 for n_ in n_features) and all(k_ >= 0 for k_ in k_max_features), "n and k must be non-negative integers"
    assert k <= n, "k must be less than or equal to n"
    assert sum(n_features) <= n, "the sum of n_features must be less than or equal to n"
    p = 0.0
    for k_features in itertools.product(*[range(k_max + 1) for k_max in k_max_features]):
        if sum(k_features) <= k:
            p += hypergeometric_pmf(n, k, n_features, [k_features])
    return p


# Hypergeometrische Verteilung - Upper Cumulative Distribution Function, P(X ≥ k)
#
# Berechnet die Wahrscheinlichkeit, dass mindestens eine bestimmte Anzahl von Merkmalen in der Stichprobe ist
#
# Beispiel: In einer Urne befinden sich 20 Kugeln. Davon sind 8 rot und 5 grün.
# Wir ziehen 5 Kugeln. Wie groß ist die Wahrscheinlichkeit, dass wir mindestens 2 rote und mindestens 1 grüne ziehen?
# hypergeometric_probability_min(20, 5, (8, 5), (2, 1))  # 0.5192208462332302
#
# n: Anzahl der Elemente gesamt
# k: Stichprobengröße
# n_features: Anzahl der einzelnen Merkmale gesamt (die Summe darf nicht größer n sein)
# k_min_features: Mindestanzahl der einzelnen Merkmale in der Stichprobe
def hypergeometric_ucdf(n, k, n_features: list|tuple, k_min_features: list|tuple) -> float:
    assert n >= 0 and k >= 0 and all(n_ >= 0 for n_ in n_features) and all(k_ >= 0 for k_ in k_min_features), "n and k must be non-negative integers"
    assert k <= n, "k must be less than or equal to n"
    assert sum(n_features) <= n, "the sum of n_features must be less than or equal to n"
    p = 0.0
    for k_features in itertools.product(*[range(k_min, n + 1) for n, k_min in zip(n_features, k_min_features)]):
        if sum(k_features) <= k:
            p += hypergeometric_pmf(n, k, n_features, [k_features])
    return p


# Listet die Stichproben auf, die exakt die gegebene Anzahl Merkmale hat
#
# Beispiel:
# matches, samples = hypergeometric_pmf_samples(["g1", "g2", "g3", "r1", "r2", "r3", "r4"], 5, {"g": 2})
# print(list(zip(matches, samples)))
# print(f"p = {sum(matches) / len(samples)}")
#
# elements: Liste der Elemente
# k: Stichprobengröße
# features: Anzahl jedes Merkmals in der Stichprobe
def hypergeometric_pmf_samples(elements: list | tuple, k: int, features: dict) -> tuple[list, list]:
    samples = list(itertools.combinations(elements, k))
    matches = []
    for sample in samples:
        matches.append(all(sum(1 for el in sample if el[0] == feature) == k_ for feature, k_ in features.items()))
    return matches, samples


# Listet die Stichproben auf, die maximal die gegebene Anzahl Merkmale hat
#
# elements: Liste der Elemente
# k: Stichprobengröße
# features: Maximalanzahl jedes Merkmals in der Stichprobe
def hypergeometric_cdf_samples(elements: list|tuple, k: int, features: dict) -> tuple[list, list]:
    samples = list(itertools.combinations(elements, k))
    matches = []
    for sample in samples:
        matches.append(all(sum(1 for el in sample if el[0] == feature) <= k_max for feature, k_max in features.items()))
    return matches, samples


# Listet die Stichproben auf, die mindestens die gegebene Anzahl Merkmale hat
#
# elements: Liste der Elemente
# k: Stichprobengröße
# features: Mindestanzahl jedes Merkmals in der Stichprobe
def hypergeometric_ucdf_samples(elements: list|tuple, k: int, features: dict) -> tuple[list, list]:
    samples = list(itertools.combinations(elements, k))
    matches = []
    for sample in samples:
        matches.append(all(sum(1 for el in sample if el[0] == feature) >= k_min for feature, k_min in features.items()))
    return matches, samples


def test():
    print(hypergeometric_pmf(20, 5, (8, 5, 3), [(2, 1, None), (2, None, 2)]))


if __name__ == "__main__":  # pragma: no cover
    test()
