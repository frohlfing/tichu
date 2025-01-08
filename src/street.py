import math


# Berechnet die Wahrscheinlichkeit, aus den gezogenen Kugeln eine gültige Reihe zu bilden, einschließlich eines Jokers.
#
# h: Liste mit der Anzahl der Kugeln für jede Zahl (Index entspricht der Zahl, h[0] = Anzahl der Joker)
# k: Anzahl der zu ziehenden Kugeln
# m: Länge der Reihe (exakte Anzahl der Kugeln in der Reihe)
# r: Rang der vorgegebenen Reihe (höchste Zahl der Reihe)
def calc(h: list[int], k: int, m: int, r: int) -> float:
    # Gesamtanzahl der Kugeln in der Urne
    n = sum(h)

    # Vorabprüfung: Sind genügend Kugeln vorhanden, um eine gültige Reihe zu bilden?
    if n < m or k < m:
        return 0

    # Rekursive Hilfsfunktion zur Berechnung der günstigen Kombinationen (inkl. Joker)
    def _number_of_singles(n_remain: int, k_remain: int, r_cur: int, joker: int, c: int) -> int:
        # n_remain: Anzahl der verbleibenden Kugeln
        # k_remain: Anzahl der noch zu ziehenden Kugeln
        # r_cur: Aktuelle Zahl, die in die Reihe aufgenommen werden soll
        # joker: 1, wenn Joker verfügbar, sonst 0
        # c: Aktuelle Länge der Reihe

        # Basisfall: Wenn die gewünschte Länge erreicht ist, berechne Kombinationen
        if c >= m:
            return math.comb(n_remain, k_remain)

        # Abbruchbedingung: Nicht genügend Kugeln oder Ziehungen verbleiben
        if n_remain < m - c or k_remain < m - c:
            return 0

        # Prüfe ohne Joker
        matches_ = 0
        if h[r_cur] > 0:
            for i in range(1, h[r_cur] + 1):  # 1 bis 4 Kugeln
                if k_remain >= i:
                    matches_ += math.comb(h[r_cur], i) * _number_of_singles(n_remain - h[r_cur], k_remain - i, r_cur + 1, joker, c + 1)

        # Prüfe mit Joker an beliebiger Position
        if joker and c > 0:
            matches_ += _number_of_singles(n_remain - h[r_cur] - joker, k_remain - 1, r_cur + 1, 0, c + 1)

        if r_cur < r_max_first:  # kann eine neue Reihe begonnen werden?
            # Prüfe Rekursion zur nächsten Zahl ohne aktuelle Auswahl
            matches_ += _number_of_singles(n_remain - h[r_cur], k_remain, r_cur + 1, joker, 0)

        return matches_

    # Maximal mögliche Startzahl der Reihe
    r_max_first = 14 - m + 1

    # Anzahl günstiger Kombinationen berechnen
    matches = _number_of_singles(n, k, r - m + 2, h[0], 0)

    # Gesamtanzahl der möglichen Kombinationen
    total_combinations = math.comb(n, k)

    # Rückgabe der Wahrscheinlichkeit
    return matches / total_combinations


print(f"{calc([1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1], 6, 5, 10):<20} 1.0                  Testfall 1 mit Joker")
print(f"{calc([1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1], 6, 5, 10):<20} 0.5595238095238095   Testfall 2 mit Joker")
print(f"{calc([0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1], 6, 5, 10):<20} 0.42857142857142855  Testfall 1")
print(f"{calc([0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 0], 6, 5, 10):<20} 0.21428571428571427  Testfall 2")
print(f"{calc([0, 0, 1, 0, 1, 0, 0, 3, 3, 3, 3, 3, 0, 1, 0], 7, 5, 10):<20} 0.22652714932126697  Testfall 3")


# Straße (Phönix am Ende der Straße
# Kartenauswahl: GD RB GZ R9 S8 B7 Ph
# Anzahl Handkarten: 6
# Straßenlänge: 5, Rang: 10
# Mögliche Handkarten:
#    GD RB GZ R9 S8 B7 True
#    GD RB GZ R9 S8 Ph True
#    GD RB GZ R9 B7 Ph True
#    GD RB GZ S8 B7 Ph True
#    GD RB R9 S8 B7 Ph True
#    GD GZ R9 S8 B7 Ph True
#    RB GZ R9 S8 B7 Ph True
# Expected: 7
# Calculated: 8
#
# Rang 8 übersprungen, Phönix für König:
# Ph GD RB GZ R9 (B7)
#
# Phönix für 8:
# (GD) RB GZ R9 Ph B7