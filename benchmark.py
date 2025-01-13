import math
from collections import Counter
from src.deprecated.calc_statistic import calc_statistic
from src.deprecated.statistic import probability_of_sample
# noinspection PyProtectedMember
from src.lib.cards import _cardlabels, _cardlabels_index
from src.lib.cards import *
from src.lib.combinations import *
from scipy.special import comb
from scipy.stats import hypergeom
from timeit import timeit

# time_start = time.time()
# delay = time.time() - time_start

#
# Cards
#

def benchmark_list_index():
    s = 'Ph GK BD RB RZ R9 R8 R7 R6 B5 G4 G3 B2 Ma'
    ar = s.split(' ')

    print(f'cardlabels.index(): {timeit(lambda: [_cardlabels.index(c) for c in ar], number=1000000):5.3f} µs per loop')
    # 4.654µs per loop

    print(f'cardlabels_index[]: {timeit(lambda: [_cardlabels_index[c] for c in ar], number=1000000):5.3f} µs per loop')
    # 0.728µs per loop


def benchmark_get_figure():
    cards = parse_cards('Ph R8 R9 BZ RB RD RK')
    print(f'get_figure(): {timeit(lambda: get_figure(cards, 10, shift_phoenix=True), number=1000000):5.3f} µs per loop')
    # 2.970 µs per loop

    cards = parse_cards('Ph R8 R9 BZ RB RD RK')
    print(f'get_figure(): {timeit(lambda: get_figure(cards, 10), number=1000000):5.3f} µs per loop')
    # 2.167 µs per loop


#
# Combinations
#

def benchmark_get_combinations():
    # Ergebnis in Tichu V1: 342 µs ± 10 µs per loop (mean ± std. dev. of 7 runs, 1000 loops each)
    cards = parse_cards('Ph GK BD RB RZ R9 R8 R7 R6 B5 G4 G3 B2 Ma')
    print(f'get_combinations(), {len(build_combinations(cards))} Kombinationen: {timeit(lambda: build_combinations(cards), number=1000):5.3f} ms per loop (in Tichu V1: 0.342 ms)')
    # 0.334ms per loop

    # Ergebnis in Tichu V1: 8.02 ms ± 175 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
    cards = parse_cards('R5 R4 G4 B4 S4 R3 G3 B3 S3 R2 G2 B2 S2 Ph')  # 3 Bomben + Phönix
    print(f'get_combinations(), {len(build_combinations(cards))} Kombinationen: {timeit(lambda: build_combinations(cards), number=1000):5.3f} ms per loop (in Tichu V1: 8.02 ms)')
    # 4.766ms per loop

    # Ergebnis in Tichu V1: 3.01 ms ± 286 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
    cards = parse_cards('S6 R6 G6 B5 S5 R4 G4 B3 S3 R3 G2 B2 S2 Ph')
    print(f'get_combinations(), {len(build_combinations(cards))} Kombinationen: {timeit(lambda: build_combinations(cards), number=1000):5.3f} ms per loop (in Tichu V1: 3.01 ms)')
    # 2.228ms per loop


def remove_list_items():
    arr = [(10, False), (30, False), (1, True), (5, True), (70, False), (9, True)]

    # Using list comprehension
    print(timeit(lambda: list(filter(lambda e: not e[1], arr)), number=10000000))
    # 6.033138407976367

    # Using Lambda & filter
    print(timeit(lambda: [e for e in arr if not e[1]], number=10000000))
    # 3.2553157720249146


def remove_combinations():
    cards = [(2, 3), (2, 4)]
    print(timeit(lambda: [card for card in deck if not set(deck).intersection(cards)], number=100000))
    # 7.9025329649448395
    print(timeit(lambda: [card for card in deck if not set(cards).intersection(deck)], number=100000))
    # 6.577613882953301


#
# Berechnung des Binomialkoeffizienten
#

def binomial_math(n, k):
    return math.comb(n, k)

def binomial_scipy(n, k):
    return comb(n, k)

def binomial_scipy_exact(n, k):
    return comb(n, k, exact=True)

def binomial_scipy_int(n, k):
    return int(comb(n, k))

def binomial_manual(n, k):
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    k = min(k, n - k)
    c = 1
    for i in range(k):
        c = c * (n - i) // (i + 1)
    return c

def binomial_benchmark(n=56, k=14):
    number = 1000  # Anzahl der Wiederholungen
    print(f"\nn={n}, k={k}")
    print("math", binomial_math(n, k))
    print("scipy", binomial_scipy(n, k))
    print("scipy int", binomial_scipy_int(n, k))
    print("scipy exact", binomial_scipy_exact(n, k))
    print("manual", binomial_manual(n, k))

    time_math = timeit(lambda: binomial_math(n, k), number=number)
    time_scipy = timeit(lambda: binomial_scipy(n, k), number=number)
    time_scipy_int = timeit(lambda: binomial_scipy_int(n, k), number=number)
    time_scipy_exact = timeit(lambda: binomial_scipy_exact(n, k), number=number)
    time_manual = timeit(lambda: binomial_manual(n, k), number=number)

    print(f"math: {time_math:.6f} Sekunden")
    print(f"scipy: {time_scipy:.6f} Sekunden")
    print(f"scipy int: {time_scipy_int:.6f} Sekunden")
    print(f"scipy exact: {time_scipy_exact:.6f} Sekunden")
    print(f"manual: {time_manual:.6f} Sekunden")

    # math: 0.000093 Sekunden
    # scipy: 0.003983 Sekunden
    # scipy int: 0.003876 Sekunden
    # scipy exact: 0.001189 Sekunden
    # manual: 0.001108 Sekunden


# Berechnung der hypergeometrischen Verteilung
# https://matheguru.com/stochastik/hypergeometrische-verteilung.html?utm_content=cmp-true

# N: Anzahl der Elemente insgesamt (56 Karten im Kartendeck)
# n: Anzahl der Elemente in der Stichprobe (14 Handkarten)
# M: Anzahl der gefragten Elemente insgesamt (z.B. 4 Damen)
# k: Anzahl der gefragten Elemente, die in der Stichprobe enthalten sind (z.B. 3 Damen als Drilling)

# noinspection PyPep8Naming
def hypergeometric_math(N, n, M, k):
    return math.comb(M, k) * math.comb(N - M, n - k) / math.comb(N, n)

# noinspection PyPep8Naming
def hypergeometric_scipy(N, n, M, k):
    return hypergeom.pmf(k, N, M, n)

# noinspection PyPep8Naming
def hypergeometric_scipy_comb(N, n, M, k):
    return comb(M, k) * comb(N - M, n - k) / comb(N, n)

# noinspection PyPep8Naming
def hypergeometric_scipy_exact(N, n, M, k):
    return comb(M, k, exact=True) * comb(N - M, n - k, exact=True) / comb(N, n, exact=True)

# noinspection PyPep8Naming
def hypergeometric_manual(N, n, M, k):
    return binomial_manual(M, k) * binomial_manual(N - M, n - k) / binomial_manual(N, n)

# noinspection PyPep8Naming
def hypergeometric_benchmark(N=56, n=14, M=4, k=3):
    number = 1000  # Anzahl der Wiederholungen
    print(f"\nN={N}, n={n}, M={M}, k={k}")
    print("math", hypergeometric_math(N, n, M, k))
    print("scipy", hypergeometric_scipy(N, n, M, k))
    print("scipy comb", hypergeometric_scipy_comb(N, n, M, k))
    print("scipy exact", hypergeometric_scipy_exact(N, n, M, k))
    print("manual", hypergeometric_manual(N, n, M, k))
    print("final2", probability_of_sample(N, n, (M,), [(k,)], "=="))

    time_math = timeit(lambda: hypergeometric_math(N, n, M, k), number=number)
    time_scipy = timeit(lambda: hypergeometric_scipy(N, n, M, k), number=number)
    time_scipy_comb = timeit(lambda: hypergeometric_scipy_comb(N, n, M, k), number=number)
    time_scipy_exact = timeit(lambda: hypergeometric_scipy_exact(N, n, M, k), number=number)
    time_manual = timeit(lambda: hypergeometric_manual(N, n, M, k), number=number)
    time_final2 = timeit(lambda: probability_of_sample(N, n, (M,), [(k,)], "=="), number=number)

    print(f"math: {time_math:.6f} Sekunden")
    print(f"scipy: {time_scipy:.6f} Sekunden")
    print(f"scipy comb: {time_scipy_comb:.6f} Sekunden")
    print(f"scipy exact: {time_scipy_exact:.6f} Sekunden")
    print(f"manual: {time_manual:.6f} Sekunden")
    print(f"final2: {time_final2:.6f} Sekunden")

    # math: 0.000233 Sekunden
    # scipy: 0.058888 Sekunden
    # scipy comb: 0.012480 Sekunden
    # scipy exact: 0.002330 Sekunden
    # manual: 0.002328 Sekunden


def possible_hands_benchmark():
    cards = parse_cards("BK BD BB BZ B9 RK RD RB RZ R9 S2 S3 G7 G6 G4 G3 Ph Hu Dr Ma")
    number = 10
    t = timeit(lambda: possible_hands(cards, 9, (SINGLE, 1, 10)), number=number) * 1000 / number
    print(f"possible_hands SINGLE: {t:.6f} ms")
    t = timeit(lambda: possible_hands(cards, 9, (PAIR, 2, 10)), number=number) * 1000 / number
    print(f"possible_hands PAIR: {t:.6f} ms")
    t = timeit(lambda: possible_hands(cards, 9, (TRIPLE, 3, 10)), number=number) * 1000 / number
    print(f"possible_hands TRIPLE: {t:.6f} ms")
    t = timeit(lambda: possible_hands(cards, 9, (STAIR, 6, 10)), number=number) * 1000 / number
    print(f"possible_hands STAIR: {t:.6f} ms")
    t = timeit(lambda: possible_hands(cards, 9, (FULLHOUSE, 5, 10)), number=number) * 1000 / number
    print(f"possible_hands FULLHOUSE: {t:.6f} ms")
    t = timeit(lambda: possible_hands(cards, 9, (STREET, 6, 10)), number=number) * 1000 / number
    print(f"possible_hands STREET: {t:.6f} ms")
    t = timeit(lambda: possible_hands(cards, 9, (BOMB, 4, 10)), number=number) * 1000 / number
    print(f"possible_hands BOMB: {t:.6f} ms")
    t = timeit(lambda: possible_hands(cards, 9, (BOMB, 6, 10)), number=number) * 1000 / number
    print(f"possible_hands Color BOMB: {t:.6f} ms")
    # possible_hands SINGLE: 95.057590 ms
    # possible_hands PAIR: 143.110650 ms
    # possible_hands TRIPLE: 138.049920 ms
    # possible_hands STAIR: 463.120050 ms
    # possible_hands FULLHOUSE: 766.137180 ms
    # possible_hands STREET: 1428.695620 ms
    # possible_hands BOMB: 92.035310 ms
    # possible_hands Color BOMB: 736.242620 ms

def probability_of_hand_benchmark():
    cards = parse_cards("BK BD BB BZ B9 RK RD RB RZ R9 S2 S3 G7 G6 G4 G3 Ph Hu Dr Ma")
    number = 1000
    t = timeit(lambda: probability_of_hand(cards, 9, (SINGLE, 1, 10)), number=number) * 1000 / number
    print(f"probability_of_hand SINGLE: {t:.6f} ms")
    t = timeit(lambda: probability_of_hand(cards, 9, (PAIR, 2, 10)), number=number) * 1000 / number
    print(f"probability_of_hand PAIR: {t:.6f} ms")
    t = timeit(lambda: probability_of_hand(cards, 9, (TRIPLE, 3, 10)), number=number) * 1000 / number
    print(f"probability_of_hand TRIPLE: {t:.6f} ms")
    t = timeit(lambda: probability_of_hand(cards, 9, (STAIR, 6, 10)), number=number) * 1000 / number
    print(f"probability_of_hand STAIR: {t:.6f} ms")
    t = timeit(lambda: probability_of_hand(cards, 9, (FULLHOUSE, 5, 10)), number=number) * 1000 / number
    print(f"probability_of_hand FULLHOUSE: {t:.6f} ms")
    t = timeit(lambda: probability_of_hand(cards, 9, (STREET, 6, 10)), number=number) * 1000 / number
    print(f"probability_of_hand STREET: {t:.6f} ms")
    t = timeit(lambda: probability_of_hand(cards, 9, (BOMB, 4, 10)), number=number) * 1000 / number
    print(f"probability_of_hand BOMB: {t:.6f} ms")
    t = timeit(lambda: probability_of_hand(cards, 9, (BOMB, 6, 10)), number=number) * 1000 / number
    print(f"probability_of_hand Color BOMB: {t:.6f} ms")
    # probability_of_hand SINGLE: 0.003127 ms
    # probability_of_hand PAIR: 0.003207 ms
    # probability_of_hand TRIPLE: 0.002966 ms
    # probability_of_hand STAIR: 0.002860 ms
    # probability_of_hand FULLHOUSE: 0.397888 ms
    # probability_of_hand STREET: 0.005616 ms
    # probability_of_hand BOMB: 0.002504 ms
    # probability_of_hand Color BOMB: 0.003605 ms

def calc_statistic_benchmark():
    number = 10
    hand = parse_cards("S7 G7 R7 G4 G4 R4 Ph Dr Ma")
    hidden = parse_cards("BK BD BB BZ B9 RK RD RB RZ R9 S2")
    combis = build_combinations(hand)
    number_of_cards = [len(hand), len(hidden), 0, 0]
    unplayed_cards = hand + hidden
    t = timeit(lambda: calc_statistic(0, hand, combis, number_of_cards, (0, 0, 0), unplayed_cards), number=number) * 1000 / number
    print(f"calc_statistic: {t:.6f} ms")
    #calc_statistic: 0.198650 ms


def build_unions1(subsets, k):
    union_count = {}
    for i in range(len(subsets)):
        for j in range(i + 1, len(subsets)):
            union = frozenset(subsets[i]).union(subsets[j])
            if len(union) <= k:
                if union not in union_count:
                    union_count[union] = 1
                else:
                    union_count[union] += 1
    return union_count

def build_unions2(subsets, k):
    union_count = Counter()
    for i in range(len(subsets)):
        for j in range(i + 1, len(subsets)):
            union = frozenset(subsets[i]).union(subsets[j])
            if len(union) <= k:
                union_count[union] += 1
    return union_count

def test_unions():
    number = 100
    subset = [{7, 8, 9, 10, 11}, {0, 8, 9, 10, 11}, {0, 7, 9, 10, 11}, {0, 7, 8, 10, 11}, {0, 7, 8, 9, 11}, {0, 7, 8, 9, 10}, {8, 9, 10, 11, 12}, {0, 9, 10, 11, 12}, {0, 8, 10, 11, 12}, {0, 8, 9, 11, 12}, {0, 8, 9, 10, 12}, {9, 10, 11, 12, 13}, {0, 10, 11, 12, 13}, {0, 9, 11, 12, 13}, {0, 9, 10, 12, 13}, {0, 9, 10, 11, 13}, {10, 11, 12, 13, 14}, {0, 11, 12, 13, 14}, {0, 10, 12, 13, 14}, {0, 10, 11, 13, 14}, {0, 10, 11, 12, 14}]
    t = timeit(lambda: build_unions1(subset, 6), number=number) * 1000 / number
    print(f"combine_and_count1: {t:.6f} ms")
    t = timeit(lambda: build_unions2(subset, 6), number=number) * 1000 / number
    print(f"combine_and_count2: {t:.6f} ms")


if __name__ == '__main__':
    test_unions()
    #possible_hands_benchmark()
    #probability_of_hand_benchmark()
    #calc_statistic_benchmark()
    #binomial_benchmark(n=56, k=14)
    #binomial_benchmark(n=1000, k=500)
    #hypergeometric_benchmark(N=56, n=14, M=4, k=3)
    #hypergeometric_benchmark(N=1000, n=500, M=100, k=50)
