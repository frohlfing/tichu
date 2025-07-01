#!/usr/bin/env python

"""
Dieses Modul wird nur für die Entwicklung benötigt.
Es testet die Ausführungsgeschwindigkeit bestimmter Funktionen.
"""

import math
from collections import Counter
from src.common.rand import Random
# from scipy.special import comb
# from scipy.stats import hypergeom
# noinspection PyProtectedMember
from src.lib.cards import *
# noinspection PyProtectedMember
from src.lib.combinations import *
from src.lib.prob.statistic import calc_statistic
# noinspection PyProtectedMember
from src.lib.prob.prob_hi import possible_hands_hi, prob_of_higher_combi
from timeit import timeit
import time
import asyncio


# from time import time
# time_start = time()
# delay = time() - time_start
# print(f"delay={delay * 1000:.6f} ms")

#
# Cards
#

def benchmark_get_figure():
    cards = parse_cards('Ph R8 R9 BZ RB RD RK')
    print(f'get_figure(): {timeit(lambda: get_combination(cards, 10, shift_phoenix=True), number=1000000):5.3f} µs per loop')
    # 2.970 µs per loop

    cards = parse_cards('Ph R8 R9 BZ RB RD RK')
    print(f'get_figure(): {timeit(lambda: get_combination(cards, 10), number=1000000):5.3f} µs per loop')
    # 2.167 µs per loop

#
# Combinations
#

def benchmark_build_combinations():
    # Ergebnis in Tichu V1: 342 µs ± 10 µs per loop (mean ± std. dev. of 7 runs, 1000 loops each)
    cards = parse_cards('Ph GK BD RB RZ R9 R8 R7 R6 B5 G4 G3 B2 Ma')
    print(f'build_combinations(), {len(build_combinations(cards))} Kombinationen: {timeit(lambda: build_combinations(cards), number=1000):5.3f} ms per loop (in Tichu V1: 0.342 ms)')
    # 0.334ms per loop

    # Ergebnis in Tichu V1: 8.02 ms ± 175 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
    cards = parse_cards('R5 R4 G4 B4 S4 R3 G3 B3 S3 R2 G2 B2 S2 Ph')  # 3 Bomben + Phönix
    print(f'build_combinations(), {len(build_combinations(cards))} Kombinationen: {timeit(lambda: build_combinations(cards), number=1000):5.3f} ms per loop (in Tichu V1: 8.02 ms)')
    # 4.766ms per loop

    # Ergebnis in Tichu V1: 3.01 ms ± 286 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
    cards = parse_cards('S6 R6 G6 B5 S5 R4 G4 B3 S3 R3 G2 B2 S2 Ph')
    print(f'build_combinations(), {len(build_combinations(cards))} Kombinationen: {timeit(lambda: build_combinations(cards), number=1000):5.3f} ms per loop (in Tichu V1: 3.01 ms)')
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
    print("manual", binomial_manual(n, k))

    time_math = timeit(lambda: binomial_math(n, k), number=number)
    time_manual = timeit(lambda: binomial_manual(n, k), number=number)

    print(f"math: {time_math:.6f} Sekunden")
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
def hypergeometric_manual(N, n, M, k):
    return binomial_manual(M, k) * binomial_manual(N - M, n - k) / binomial_manual(N, n)

# noinspection PyPep8Naming
def hypergeometric_benchmark(N=56, n=14, M=4, k=3):
    number = 1000  # Anzahl der Wiederholungen
    print(f"\nN={N}, n={n}, M={M}, k={k}")
    print("math", hypergeometric_math(N, n, M, k))
    print("manual", hypergeometric_manual(N, n, M, k))

    time_math = timeit(lambda: hypergeometric_math(N, n, M, k), number=number)
    time_manual = timeit(lambda: hypergeometric_manual(N, n, M, k), number=number)

    print(f"math: {time_math:.6f} Sekunden")
    print(f"manual: {time_manual:.6f} Sekunden")

    # math: 0.000233 Sekunden
    # scipy: 0.058888 Sekunden
    # scipy comb: 0.012480 Sekunden
    # scipy exact: 0.002330 Sekunden
    # manual: 0.002328 Sekunden


def possible_hands_benchmark():
    cards = parse_cards("BK BD BB BZ B9 RK RD RB RZ R9 S2 S3 G7 G6 G4 G3 Ph Hu Dr Ma")  # 20
    #cards = parse_cards("B2 B3 B4 B5 B9 BK BD BB BZ B9 RK RD RB RZ R9 S2 S3 G7 G6 G4 G3 Ph Hu Dr Ma") # 25
    number = 1
    for figure in [(CombinationType.SINGLE, 1, 8), (CombinationType.PAIR, 2, 8), (CombinationType.TRIPLE, 3, 8), (CombinationType.STAIR, 6, 8), (CombinationType.FULLHOUSE, 5, 8), (CombinationType.STREET, 6, 8), (CombinationType.BOMB, 4, 8), (CombinationType.BOMB, 6, 8)]:
        for k in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]:
            t = timeit(lambda: possible_hands_hi(cards, k, figure, with_bombs=True), number=number) * 1000 / number
            print(f"possible_hands_hi, {stringify_combination(figure)}, {k}, {t:.6f} ms")


def prob_of_hand_benchmark():
    number = 1
    for k in range(5, 10):
        t = timeit(lambda: prob_of_higher_combi(parse_cards("GA RA BK SK GD RD BZ SZ G9 R9 B9 S9 G8 R8 B8 S8 G7 R7 B7 S7 G6 R6 B6 S6 Ph Hu Dr Ma"), 9, (CombinationType.SINGLE, 1, 8)), number=number) * 1000 / number
        print(f"prob_of_hand SINGLE, k={k}: {t:.6f} ms")

        t = timeit(lambda: prob_of_higher_combi(parse_cards("GA RA BK SK GD RD BZ SZ G9 R9 B9 S9 G8 R8 B8 S8 G7 R7 B7 S7 G6 R6 B6 S6 Ph Hu Dr Ma"), 9, (CombinationType.PAIR, 2, 8)), number=number) * 1000 / number
        print(f"prob_of_hand PAIR, k={k}: {t:.6f} ms")

        t = timeit(lambda: prob_of_higher_combi(parse_cards("GA RA BA BK SK GK GD RD BD BZ SZ G9 G9 R9 B9 S9 G8 R8 B8 S8 G7 R6 B6 S6 Ph Hu Dr Ma"), 9, (CombinationType.TRIPLE, 3, 8)), number=number) * 1000 / number
        print(f"prob_of_hand TRIPLE, k={k}: {t:.6f} ms")

        t = timeit(lambda: prob_of_higher_combi(parse_cards("GA RA BK SK GD RD BZ SZ G9 R9 B9 S9 G8 R8 B8 S8 G7 R7 B7 S7 G6 R6 B6 S6 Ph Hu Dr Ma"), 9, (CombinationType.STAIR, 6, 8)), number=number) * 1000 / number
        print(f"prob_of_hand STAIR, k={k}: {t:.6f} ms")

        t = timeit(lambda: prob_of_higher_combi(parse_cards("GA RA SA BK RK SK RD SD GD GZ RZ BZ Ph Hu Dr Ma"), 9, (CombinationType.FULLHOUSE, 5, 8)), number=number) * 1000 / number
        print(f"prob_of_hand FULLHOUSE, k={k}: {t:.6f} ms")

        t = timeit(lambda: prob_of_higher_combi(parse_cards("GA RK GD RB GZ R9 S8 B7 S6 S5 S4 S3 S2 Ph"), k, (CombinationType.STREET, 5, 8)), number=number) * 1000 / number
        print(f"prob_of_hand STREET, k={k}: {t:.6f} ms")

        #t = timeit(lambda: possible_hands_hi(parse_cards("GA RK GD RB GZ R9 S8 B7 S6 S5 S4 S3 S2 Ph"), k, (STREET, 6, 8)), number=number) * 1000 / number
        #print(f"possible_hands_hi STREET, k={k}: {t:.6f} ms")

        t = timeit(lambda: prob_of_higher_combi(parse_cards("BA RA SA GA BK RK SK GK BD RD SD GD Ph Hu Dr Ma"), 9, (CombinationType.BOMB, 4, 8)), number=number) * 1000 / number
        print(f"prob_of_hand BOMB, k={k}: {t:.6f} ms")

        t = timeit(lambda: prob_of_higher_combi(parse_cards("GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2"), 9, (CombinationType.BOMB, 6, 8)), number=number) * 1000 / number
        print(f"prob_of_hand Color BOMB, k={k}: {t:.6f} ms")


def calc_statistic_benchmark():
    number = 10
    hand = parse_cards("S7 G7 R7 G4 G4 R4 Ph Dr Ma")
    hidden = parse_cards("BK BD BB BZ B9 RK RD RB RZ R9 S2")
    combis = build_combinations(hand)
    number_of_cards = [len(hand), len(hidden), 0, 0]
    unplayed_cards = hand + hidden
    t = timeit(lambda: calc_statistic(0, hand, combis, number_of_cards, (CombinationType.PASS, 0, 0), unplayed_cards), number=number) * 1000 / number
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




def validate_figure1(figure: tuple) -> bool:
    t, m, r = figure
    if t == CombinationType.SINGLE:  # Einzelkarte
        return 0 <= r <= 16
    if t in [CombinationType.PAIR, CombinationType.TRIPLE, CombinationType.FULLHOUSE] or (t == CombinationType.BOMB and m == 4):  # Paar, Drilling, Fullhouse, 4er-Bombe
        return 2 <= r <= 14
    if t == CombinationType.STAIR:  # Treppe
        return m % 2 == 0 and 4 <= m <= 14 and int(m / 2) + 1 <= r <= 14
    if t == CombinationType.STREET:  # Straße
        return 5 <= m <= 14 and m <= r <= 14
    return t == CombinationType.BOMB and 5 <= m <= 14 and m + 1 <= r <= 14  # Farbbombe


async def async_func():
    return 4711

def sync_func():
    return 4711

random = Random()

async def async_func2():
    return random.integer(1, 100)

def sync_func2():
    return random.integer(1, 100)

# Benchmark-Funktion:
def sync_vs_async_benchmark():
    number = 1000000

    # Benchmark für synchrone Funktion
    start = time.time()
    for _ in range(number):
        sync_func()
    sync_duration = time.time() - start

    # Benchmark für asynchrone Funktion
    async def run_async():
        # noinspection PyShadowingNames
        start = time.time()
        for _ in range(number):
            await async_func()
        return time.time() - start

    async_duration = asyncio.run(run_async())

    print("Nur der reine Funktionsaufruf:")
    print(f"Sync : {sync_duration:.3f} µs / Aufruf")
    print(f"Async: {async_duration:.3f} µs / Aufruf")
    print(f"Diff: {async_duration - sync_duration:.3f} µs / Aufruf")
    print()

    # Benchmark für synchrone Funktion
    start = time.time()
    for _ in range(number):
        sync_func2()
    sync_duration = time.time() - start

    # Benchmark für asynchrone Funktion
    async def run_async2():
        # noinspection PyShadowingNames
        start = time.time()
        for _ in range(number):
            await async_func2()
        return time.time() - start

    async_duration = asyncio.run(run_async2())

    print("Funktionsaufruf und Berechnung einer Zufallszahl:")
    print(f"Sync : {sync_duration:.3f} µs / Aufruf")
    print(f"Async: {async_duration:.3f} µs / Aufruf")
    print(f"Diff: {async_duration - sync_duration:.3f} µs / Aufruf")
    print(f"Async/Sync: {async_duration/sync_duration:.3f} mal langsamer")


if __name__ == '__main__':
    benchmark_build_combinations()
    #sync_vs_async_benchmark()

    #possible_hands_benchmark()
    #prob_of_hand_benchmark()

    #calc_statistic_benchmark()
    #binomial_benchmark(n=56, k=14)
    #binomial_benchmark(n=1000, k=500)
    #hypergeometric_benchmark(N=56, n=14, M=4, k=3)
    #hypergeometric_benchmark(N=1000, n=500, M=100, k=50)
