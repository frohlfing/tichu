# Wandelt die Karten in einen Vektor um
def cards_to_vector(cards: list[tuple]) -> list[int]:
    # r=Hu Ma  2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As  2  3  4  5  6  7  8  9 10 Bu Da Kö As Dr Ph
    # i= 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55
    h = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for r, c in cards:
        if c > 0:
            h[r + 13 * (c - 1)] = 1
        else:
            h[r if r < 2 else r + 39] = 1
    return h


# Zählt die Karten von 2 bis Ass (ohne Sonderkarten)
#
# Zurückgegeben wird eine zweidimensionale Liste.
# Die erste Dimension ist die Farbe, die zweite der Rang.
def cards_to_vector2(cards: list[tuple]) -> list[list[int]]:
    # r= 2  3  4  5  6  7  8  9 10 Bu Da Kö As
    # i= 0  1  2  3  4  5  6  7  8  9 10 11 12
    h = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # schwarz
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # blau
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # grün
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # rot
    ]
    for r, c in cards:
        if c > 0:
            h[c - 1][r - 2] = 1
    return h
