"""
Dieses Modul bietet Funktionen zur Berechnung der Wahrscheinlichkeit, dass niedrigere Kartenkombinationen
gespielt werden können.


Hauptfunktionen:
- `prob_of_lower_combi`: Wahrscheinlichkeit für eine niedrigere Kombination.
- `possible_hands_lo`: Listet mögliche Hände mit niedrigeren Kombinationen auf.
- `inspect`: Analyse spezifischer Kartenkombinationen und deren Wahrscheinlichkeiten.

Verwendung:
Dieses Modul dient der probabilistischen Analyse und der Entwicklung von Strategien im Spiel.
"""

__all__ = "prob_of_lower_combi",

import itertools
import math
from src.lib.cards import parse_cards, stringify_cards, ranks_to_vector, Cards
from src.lib.combinations import stringify_combination, validate_combination, CombinationType, Combination
from src.lib.prob.tables_lo import load_table_lo
from time import time

# ------------------------------------------------------
# Wahrscheinlichkeitsberechnung p_low
# ------------------------------------------------------

# Berechnet die Wahrscheinlichkeit, dass die Hand die gegebene Kombination anspielen kann
#
# Sonderkarte Phönix:
# Wir gehen davon aus, dass die gegebene Kombination den aktuellen Stich und somit den Phönix überstechen kann.
# Ausnahme: Der Mahjong kann den Phönix nicht überstechen (im Anspiel hat der Phönix den Rang 1.5).
#
# Sonderkarte Hund:
# Mit dem Hund als gegebene Kombination wird 0.0 zurückgegeben, da der Hund keine Karte stechen kann.
# Der Hund auf der Hand des Mitspielers kann aber auch keine Kombination anspielen. Daher wird der Hund ignoriert.
#
# Bekannter Fehler (weil die Kartenfarbe nicht berücksichtigt wird):  todo ist das so?
# Ist die gegebene Kombination eine Straße, und wäre eine Farbbombe mit kleinerem Rang auf der Hand, die nicht auch zu
# einer normalen Straße zerlegt werden könnte, so würde diese Farbbombe fälschlicherweise als niedrigere Kombination gezählt.
# Dieser Fall ist sehr selten und kann vernachlässigt werden.
#
# todo Hat der Partner allerdings den Hund, so erhält man das Anspielrecht, was gesondert bewertet werden muss (aber nicht hier).
#
# cards: Verfügbare Karten
# k: Anzahl der Handkarten
# combination: Die gegebenen Kombination (Typ, Länge und Rang).
# return: Wahrscheinlichkeit `p_low`
def prob_of_lower_combi(cards: Cards, k: int, combination: Combination) -> float:
    if k == 0:
        return 0.0
    n = len(cards)  # Gesamtanzahl der verfügbaren Karten
    assert k <= n <= 56
    assert 0 <= k <= 14

    if combination == (1, 1, 0):  # Hund
        return 0.0  # der Hund kann keine Karte stechen

    assert combination != (0, 0, 0) and validate_combination(combination)
    t, m, r = combination  # Typ, Länge und Rang der gegebenen Kombination

    # eine Bombe kann jede Einzelkarte aus der Hand übernehmen, allein das reicht schon
    if t == CombinationType.BOMB:
        return 1.0

    #debug = False

    # Anzahl der Karten je Rang zählen.
    h = ranks_to_vector(cards)

    # Sonderbehandlung für Phönix als Einzelkarte
    if t == CombinationType.SINGLE and r == 16:
        # Rang des Phönix anpassen (der Phönix schlägt das Ass, aber nicht den Drachen)
        r = 15  # 14.5 aufgerundet
        # Der verfügbare Phönix hat den Rang 1 (1.5 abgerundet); er würde von sich selbst geschlagen werden.
        # Daher degradieren wir den verfügbaren Phönix zu einer Noname-Karte (n bleibt gleich, aber es gibt kein Phönix mehr!).
        h[16] = 0

    # Hilfstabellen laden
    table = load_table_lo(t, m)

    # alle Muster der Hilfstabelle durchlaufen und mögliche Kombinationen zählen
    matches = 0
    r_min = 1 if t == CombinationType.SINGLE else int(m / 2) + 1 if t == CombinationType.STAIR else m if t == CombinationType.STREET else m + 1 if t == CombinationType.BOMB and m >= 5 else 2
    r_start = 1 if t in [CombinationType.SINGLE, CombinationType.STREET] else 2
    for pho in range(2 if h[16] and t != CombinationType.BOMB else 1):
        for r_lower in range(r_min, r):
            for case in table[pho][r_lower]:
                if sum(case) + pho > k:
                    continue
                # jeweils den Binomialkoeffizienten von allen Rängen im Muster berechnen und multiplizieren
                matches_part = 1
                n_remain = (n - h[16]) if t != CombinationType.BOMB else n
                k_remain = k - pho
                for i in range(len(case)):
                    if h[r_start + i] < case[i]:
                        matches_part = 0
                        break
                    matches_part *= math.comb(h[r_start + i], case[i])
                    n_remain -= h[r_start + i]
                    k_remain -= case[i]
                if matches_part > 0:
                    # Binomialkoeffizient vom Rest berechnen und mit dem Zwischenergebnis multiplizieren
                    matches_part *= math.comb(n_remain, k_remain)
                    # Zwischenergebnis zum Gesamtergebnis addieren
                    #if debug:
                    #    print(f"r={r_lower}, php={pho}, case={case}, matches={matches_part}")
                    matches += matches_part

    # Wahrscheinlichkeit berechnen
    total = math.comb(n, k)  # Gesamtanzahl der möglichen Kombinationen
    p = matches / total
    return p


# ------------------------------------------------------
# Test
# ------------------------------------------------------

# Listet die möglichen Hände auf und markiert, welche eine Kombination hat, die die gegebenen anspielen kann.
#
# Wenn k größer ist als die Anzahl der ungespielten Karten, werden leere Listen zurückgegeben.
#
# Bekannter Fehler (weil die Kartenfarbe nicht berücksichtigt wird):
# Ist die gegebene Kombination eine Straße, und wäre eine Farbbombe mit kleinerem Rang auf der Hand, die nicht auch zu
# einer normalen Straße zerlegt werden könnte, so würde diese Farbbombe fälschlicherweise als niedrigere Kombination gezählt.
# Dieser Fall ist sehr selten und kann vernachlässigt werden.
#
# Diese Methode wird nur für Testzwecke verwendet. Je mehr ungespielte Karten es gibt, desto langsamer werden sie.
# Ab ca. 20 Karten ist sie praktisch unbrauchbar.
#
# unplayed_cards: Ungespielte Karten
# k: Anzahl Handkarten
# combination: Die Kombination (Typ, Länge, Rang).
def possible_hands_lo(unplayed_cards: Cards, k: int, combination: Combination) -> tuple[list, list]:
    hands = list(itertools.combinations(unplayed_cards, k))  # die Länge der Liste entspricht math.comb(len(unplayed_cards), k)
    matches = []
    t, m, r = combination  # type, length, rank
    for hand in hands:
        b = False
        if t == CombinationType.SINGLE:  # Einzelkarte
            if r == 15:  # Drache
                b = any(v not in [0, 15] for v, _ in hand)  # jede Karte, die nicht der Hund ist, kann der Drache stechen
            elif 2 <= r <= 14:  # von der 2 bis zum Ass
                b = any(v == 16 or 0 < v < r for v, _ in hand)
            elif r <= 1:  # Hund oder Mahjong
                b = False  # der Hund und der Mahjong können keine Karte stechen
            else:  # Phönix
                assert r == 16
                b = any(0 < v < 15 for v, _ in hand)  # jede Karte, die nicht Hund oder Drache ist, kann der Phönix stechen
        else:
            r_min = int(m / 2) + 1 if t == CombinationType.STAIR else m if t == CombinationType.STREET else m + 1 if t == CombinationType.BOMB and m >= 5 else 2
            #r_min = 3 if t == CombinationType.STAIR else 5 if t == CombinationType.STREET else 6 if t == CombinationType.BOMB and m >= 5 else 2
            for rlo in range(r_min, r):  # rlo = Rang kleiner als der Rang der gegebenen Kombination
                if t in [CombinationType.PAIR, CombinationType.TRIPLE]:  # Paar oder Drilling
                    b = sum(1 for v, _ in hand if v in [rlo, 16]) >= m

                elif t == CombinationType.STAIR:  # Treppe
                    steps = int(m / 2)
                    if any(v == 16 for v, _ in hand):  # Phönix vorhanden?
                        for j in range(steps):
                            b = all(sum(1 for v, _ in hand if v == rlo - i) >= (1 if i == j else 2) for i in range(steps))
                            if b:
                                break
                    else:
                        b = all(sum(1 for v, _ in hand if v == rlo - i) >= 2 for i in range(steps))

                elif t == CombinationType.FULLHOUSE:  # Fullhouse
                    if any(v == 16 for v, _ in hand):  # Phönix vorhanden?
                        for j in range(2, 15):
                            b = (sum(1 for v, _ in hand if v == rlo) >= (2 if rlo == j else 3)
                                 and any(sum(1 for v2, _ in hand if v2 == r2) >= (1 if r2 == j else 2) for r2 in range(2, 15) if r2 != rlo))
                            if b:
                                break
                    else:
                        b = (sum(1 for v, _ in hand if v == rlo) >= 3
                             and any(sum(1 for v2, _ in hand if v2 == r2) >= 2 for r2 in range(2, 15) if r2 != rlo))

                elif t == CombinationType.STREET:  # Straße
                    if any(v == 16 for v, _ in hand):  # Phönix vorhanden?
                        a = rlo < 14  # die Straße könnte nach oben hin mit dem Phönix verlängert werden
                        for j in range(m - 1 if a else m):  # der Phönix wird möglichst nicht an das untere Ende der Straße eingereiht
                            b = all(sum(1 for v, _ in hand if v == rlo - i) >= (0 if i == j else 1) for i in range(m))
                            if b:
                                break
                    else:
                        b = all(sum(1 for v, _ in hand if v == rlo - i) >= 1 for i in range(m))

                elif t == CombinationType.BOMB:  # Bombe
                    b = k > 0  # bereits jede Einzelkarte ist einer Bombe unterlegen

                else:
                    assert False

                if b:
                    break

        matches.append(b)
    return matches, hands


# Ergebnisse untersuchen
def inspect(cards, k, combination, verbose=True):  # pragma: no cover
    print(f"Kartenauswahl: {cards}")
    print(f"Anzahl Handkarten: {k}")
    print(f"Kombination: {stringify_combination(combination)}")
    print("Mögliche Handkarten:")

    time_start = time()
    matches, hands = possible_hands_lo(parse_cards(cards), k, combination)
    if verbose:
        for match, sample in zip(matches, hands):
            print("  ", stringify_cards(sample), match)
    matches_expected = sum(matches)
    total_expected = len(hands)
    p_expected = (matches_expected / total_expected) if total_expected else "nan"
    print(f"Gezählt:   p = {matches_expected}/{total_expected} = {p_expected}"
          f" ({(time() - time_start) * 1000:.6f} ms)")

    time_start = time()
    p_actual = prob_of_lower_combi(parse_cards(cards), k, combination)
    print(f"Berechnet: p = {(total_expected * p_actual):.0f}/{total_expected} = {p_actual}"
          f" ({(time() - time_start) * 1000:.6f} ms (inkl. Daten laden))")


def inspect_combination():  # pragma: no cover
    test = [
        # Einzelkarte
        #("Dr RK GK BD S4 R3 R2", 3, (1, 1, 11), 31, 35, "Einzelkarte"),
        #("Dr BD RB SB R3 R2", 3, (1, 1, 11), 16, 20, "Einzelkarte mit 2 Buben"),
        #("Ph RB G6 B5 R2", 3, (1, 1, 5), 9, 10, "Einzelkarte mit Phönix"),
        #("Dr Ph Ma S4 R3 R2", 1, (1, 1, 0), 0, 6, "Einzelkarte Hund"),
        #("Dr Hu Ph S4 R3 R2", 1, (1, 1, 1), 0, 6, "Einzelkarte Mahjong"),
        #("Hu Ph Ma S4 R3 R2", 1, (1, 1, 15), 5, 6, "Einzelkarte Drache"),
        #("Dr Hu Ma S4 R3 R2", 1, (1, 1, 16), 4, 6, "Einzelkarte Phönix"),
        #("Dr Hu Ma S4 R3 R2 Ph", 1, (1, 1, 16), 4, 7, "Einzelkarte Phönix (2)"),
        #("SB RZ R9 G9 R8 G8 B4", 2, (1, 1, 9), 15, 21, "Neun, Test 1884"),
        #("Ph Dr RB GZ BZ SZ R9 G9 S9 R8 G8 B4", 1, (1, 1, 15), 12, 12, "Drache, Test 3289"),
        #("Dr", 1, (1, 1, 15), 12, 12, "Drache, Test 3289"),
        # # Pärchen
        #("Dr RK GK BB SB RB R2", 5, (2, 2, 12), 18, 21, "Pärchen ohne Phönix"),
        #("Ph RK GK BD SB RB R2", 5, (2, 2, 11), 10, 21, "Pärchen mit Phönix"),
        #("Ph RK GK BD SB RB R2", 5, (2, 2, 12), 19, 21, "Pärchen mit Phönix (2)"),
        #("RZ GZ BZ SZ R9 S9", 5, (2, 2, 10), 4, 6, "Pärchen mit 4er-Bombe"),
        #("RZ R9 R8 R7 R6 S6", 5, (2, 2, 11), 4, 6, "Pärchen mit Farbbombe"),
        # # Drilling
        #("SK RK GB BB SB R3 R2", 4, (3, 3, 12), 4, 35, "Drilling ohne Phönix"),
        #("Ph RK GK BB SB R3 R2", 4, (3, 3, 13), 4, 35, "Drilling mit Phönix"),
        #("RZ GZ BZ SZ R9 S9 B9", 5, (3, 3, 10), 6, 21, "Drilling mit 4er-Bombe"),
        #("SB RZ R9 R8 R7 R6", 5, (3, 3, 11), 0, 6, "Drilling mit Farbbombe"),
        # # Treppe
        #("RK GK SK BD SD GB RB", 5, (4, 4, 13), 3, 21, "2er-Treppe aus Fullhouse"),
        #("SB RZ R9 G9 R8 G8 B4", 9, (4, 4, 9), 0, 0, "2er-Treppe nicht möglich"),
        #("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 10), 12, 210, "2er-Treppe mit Phönix"),
        #("RK GK BD SD SB RB BB", 6, (4, 6, 14), 3, 7, "3er-Treppe ohne Phönix"),
        #("Ph GK BD SD SB RB BB", 6, (4, 6, 14), 3, 7, "3er-Treppe mit Phönix"),
        #("GA RA GK RK SD BD SB BB GB BZ RZ G9 B9 R9 Ph", 13, (4, 10, 14), 84, 105, "5er-Treppe"),
        # # Fullhouse
        #("RK GD BD SB RB BB S2", 6, (5, 5, 13), 2, 7, "Fullhouse ohne Phönix"),
        #("BB RB SB BZ RZ R9 S9 R8", 7, (5, 5, 12), 5, 8, "Fullhouse und zusätzliches Pärchen"),
        #("BB RB SB G9 R9 S9 R7 S2", 7, (5, 5, 10), 5, 8, "Fullhouse mit 2 Drillinge"),
        #("Ph GK BD SB RB BB S2", 6, (5, 5, 12), 3, 7, "Fullhouse mit Phönix für Paar"),
        #("RK GK BD SB RB BZ Ph", 6, (5, 5, 12), 2, 7, "Fullhouse mit Phönix für Drilling"),
        # # Straße
        #("BK SD BD RB BZ B9 R3", 6, (6, 5, 14), 3, 7, "5er-Straße bis König aus 7 Karten ohne Phönix"),
        #("RA GK BD SB RZ B9 R3", 6, (6, 5, 14), 2, 7, "5er-Straße bis Ass aus 7 Karten ohne Phönix"),
        #("GA RK GD RB GZ R9 S8 B7", 5, (6, 5, 13), 2, 56, "5er-Straße bis Ass aus 8 Karten ohne Phönix"),
        #("SK RD GB BB RZ B9 R8 R2", 6, (6, 5, 13), 5, 28, "5er-Straße mit 2 Buben aus 8 Karten ohne Phönix"),
        #("RA GK BD RZ B9 R8 Ph", 6, (6, 5, 13), 2, 7, "5er-Straße aus 7 Karten mit Phönix (Lücke gefüllt)"),
        #("RA BD BB RZ B9 B2 Ph", 6, (6, 5, 13), 0, 7, "5er-Straße aus 7 Karten mit Phönix (nicht unten verlängert)"),
        #("RA SK BD BB B9 B2 Ph", 6, (6, 5, 14), 2, 7, "5er-Straße bis zum Ass mit Phönix (Lücke gefüllt)"),
        #("Ph SK RK GD BB RZ B9 R8", 6, (6, 5, 13), 11, 28, "5er-Straße aus 8 Karten mit 2 Könige mit Phönix (verlängert)"),
        #("GA RK GD RB GZ R9 S8 B7 S6 Ph", 9, (6, 5, 11), 9, 10, "5er-Straße aus 10 Karten"),
        #("SB RZ R9 R8 R7 R6", 5, (6, 5, 11), 1, 6, "Straße mit Farbbombe (bekannter Fehler, 0/6 wäre eigentlich richtig)"),
        # Bombe
        ("RK GB BB SB RB BZ R2", 0, (7, 4, 10), 21, 21, "4er-Bombe"),
        #("BK BB BZ B9 B8 B7 B2", 5, (7, 7, 10), 21, 21, "Farbbombe"),
    ]
    for cards, k, combination, matches_expected, total_expected, msg in test:
        print(msg)
        inspect(cards, k, combination, verbose=True)


if __name__ == "__main__":  # pragma: no cover
    inspect_combination()
