from src.lib.cards import *
from src.lib.combinations import *
from timeit import timeit


# time_start = time.time()
# delay = time.time() - time_start

#
# Cards
#

def benchmark_list_index():
    s = 'Ph GK BD RB RZ R9 R8 R7 R6 B5 G4 G3 B2 Ma'
    ar = s.split(' ')

    print(f'cardlabels.index(): {timeit(lambda: [cardlabels.index(c) for c in ar], number=1000000):5.3f} µs per loop')
    # 4.654µs per loop

    print(f'cardlabels_index[]: {timeit(lambda: [cardlabels_index[c] for c in ar], number=1000000):5.3f} µs per loop')
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


if __name__ == '__main__':
    remove_combinations()
    # benchmark_get_figure()
    # benchmark_get_combinations()
