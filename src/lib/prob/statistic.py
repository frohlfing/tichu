"""
Dieses Modul bietet eine Funktion zur Berechnung der Wahrscheinlichkeiten, dass die Mitspieler eine bestimmte
Kombination anspielen bzw. überstechen können.
"""

__all__ = "calc_statistic"

from src.lib.cards import CARD_DOG, CARD_MAH, CARD_DRA, CARD_PHO, Cards
from src.lib.combinations import FIGURE_DOG, FIGURE_DRA, FIGURE_PHO, CombinationType, Combination
from typing import List, Tuple, Dict, Optional


# todo dies ist noch die unveränderte (und nicht korrekte) Vorgänger-Version

# Wahrscheinlichkeit berechnen, dass die Mitspieler eine bestimmte Kombination anspielen bzw. überstechen können
# Für jede eigene Kombination liefert die Funktion folgende Werte:
# lo_opp: Wahrscheinlichkeit, das der Gegner eine Kombination hat, die ich stechen kann und somit das Anspiel gewinne
# lo_par: Wahrscheinlichkeit, das der Partner eine Kombination hat, die ich stechen kann und somit das Anspiel gewinne
# hi_opp: Wahrscheinlichkeit, das der Gegner eine höherwertige Kombination hat und das Anspiel verliere
# hi_par: Wahrscheinlichkeit, das der Partner eine höherwertige Kombination hat und das Anspiel verliere
# eq_opp: Wahrscheinlichkeit, dass der Gegner eine gleichwertige Kombinationen hat
# eq_par: Wahrscheinlichkeit, dass der Partner eine gleichwertige Kombinationen hat
# Daraus folgt:
# 1 - lo_opp - hi_opp - eq_opp: Wahrscheinlichkeit, dass der Gegner nicht die Kombi vom gleichen Typ und Länge hat
# 1 - lo_par - hi_par - eq_par: Wahrscheinlichkeit, dass der Partner nicht die Kombi vom gleichen Typ und Länge hat
# Diese Parameter werden erwartet:
# player: Meine Spielernummer (zw. 0 und 3)
# hand: Eigene Handkarten
# combis: Zu bewertende Kombinationen (gebildet aus den Handkarten) [(Karten, (Typ, Länge, Rang)), ...]
# number_of_cards: Anzahl der Handkarten aller Spieler.
# trick_combination: Kombination (Typ, Länge, Rang) des aktuellen Stichs ((0,0,0), falls kein Stich liegt).
# unplayed_cards: Noch nicht gespielte Karten
def calc_statistic(player: int, hand: Cards, combis: List[Tuple[Cards, Combination]], number_of_cards: List[int], trick_combination: Combination, unplayed_cards: Cards) -> Dict[Cards, Tuple[float, float, float, float, float, float]]:
    assert hand  # wir haben bereits bzw. noch Karten auf der Hand
    assert len(hand) == number_of_cards[player]

    if sum(number_of_cards) != len(unplayed_cards):
        # die Karten werden gerade verteilt bzw. es wird geschupft!
        m = len(hand)
        assert m in (0, 8, 11, 14)
        assert len(unplayed_cards) == 56
        n = int((56 - m) / 3)
        number_of_cards = [n, n, n, n]  # wir tun so, als wenn alle Karten bereits verteilt sind
        number_of_cards[player] = m

    # Anzahl der ungespielten Karten (die eigenen Handkarten werden hier nicht mitgezählt)
    #  Dog Mah 2  3  4  5  6  7  8  9 10 Bu Da Kö As Dra
    c = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # rot oder Sonderkarte
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # grün
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # blau
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]   # schwarz
    ]
    phoenix = False
    for card in unplayed_cards:
        if card not in hand:
            if card == CARD_DOG:
                c[0][0] = 1
            elif card == CARD_MAH:
                c[0][1] = 1
            elif card == CARD_DRA:
                c[0][15] = 1
            elif card == CARD_PHO:
                phoenix = True
            else:
                c[card[1]-1][card[0]] = 1

    # Anzahl der ungespielten Karten gesamt (ohne die eigenen Handkarten)
    sum_c = len(unplayed_cards) - len(hand)

    # Anzahl Kombinationen pro Typ (Single/1 bis Bombe/7)
    #           1   2   3   4   5   6   7
    d = [None, [], [], [], [], [], [], []]

    # Anzahl Einzelkarten gesamt (d[CombinationType.SINGLE][1][15] == Drache, d[CombinationType.SINGLE][1][16] == Phönix)
    d[CombinationType.SINGLE] = [None, [c[0][v] + c[1][v] + c[2][v] + c[3][v] for v in range(16)] + [int(phoenix)]]

    # Paare, Drillinge und Fullhouse (zunächst ohne Phönix)
    d[CombinationType.PAIR] = [None, None, [6 if d[CombinationType.SINGLE][1][v] == 4 else 3 if d[CombinationType.SINGLE][1][v] == 3 else 1 if d[CombinationType.SINGLE][1][v] == 2 else 0 for v in range(15)]]
    d[CombinationType.TRIPLE] = [None, None, None, [4 if d[CombinationType.SINGLE][1][v] == 4 else 1 if d[CombinationType.SINGLE][1][v] == 3 else 0 for v in range(15)]]
    sum_pairs = sum(d[CombinationType.PAIR][2])
    d[CombinationType.FULLHOUSE] = [None, None, None, None, None, [d[CombinationType.TRIPLE][3][v] * (sum_pairs - d[CombinationType.PAIR][2][v]) for v in range(15)]]

    # Treppen   0     1     2     3    4    5    6    7    8    9   10   11   12   13   14 Karten
    d[CombinationType.STAIR] = [None, None, None, None, [], None, [], None, [], None, [], None, [], None, []]
    for k in range(7, 1, -1):  # Anzahl Paare in der Treppe (7 bis 2)
        n = k * 2  # Anzahl Karten in der Treppe
        # Wert         0  1  2  3  4  5  6  7  8  9 10 11 12 13 14
        d[CombinationType.STAIR][n] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        for v in range(k + 1, 15):  # höchstes Paar (=Wert der Kombination)
            phoenix_available = phoenix
            counter = 1
            for i in range(k):  # Anzahl Paare
                if phoenix_available and not d[CombinationType.PAIR][2][v - i]:
                    phoenix_available = False  # Fehlendes Paar mit Einzelkarte und Phönix ersetzen
                    counter *= d[CombinationType.SINGLE][1][v - i]
                else:
                    counter *= d[CombinationType.PAIR][2][v - i]
            if phoenix_available and counter:
                counter_without_phoenix = counter  # Anzahl Kombinationsmöglichkeiten ohne Phönix
                for i in range(k):  # jede Karte mit dem Phönix ersetzten und zu den Möglichkeiten dazuzählen
                    if d[CombinationType.PAIR][2][v - i]:
                        counter += int(counter_without_phoenix / d[CombinationType.PAIR][2][v - i]) * 2
            d[CombinationType.STAIR][n][v] = counter

    # Paare, Drillinge und Fullhouse mit Phönix
    if phoenix:
        counter = 0
        sum_singles = sum(d[CombinationType.SINGLE][1][:16])  # Anzahl Karten ohne Phönix
        for v in range(2, 15):
            # fullhouse = # Drilling + Einzelkarte + Phönix
            # Ausnahmeregel: Der Drilling darf nicht vom gleichen Wert sein wie die Einzelkarte.
            d[CombinationType.FULLHOUSE][5][v] += d[CombinationType.TRIPLE][3][v] * (sum_singles - d[CombinationType.SINGLE][1][v])
            # fullhouse = Paar1 + Phönix + Paar2
            # Bedingung: Paar1 ist größer als Paar2 (man würde immer den Phönix zum höherwertigen Pärchen sortieren)
            d[CombinationType.FULLHOUSE][5][v] += d[CombinationType.PAIR][2][v] * counter
            counter += d[CombinationType.PAIR][2][v]
            d[CombinationType.TRIPLE][3][v] += d[CombinationType.PAIR][2][v]  # Drilling mit Phönix = Paar + Phönix
            d[CombinationType.PAIR][2][v] += d[CombinationType.SINGLE][1][v]  # Paar mit Phönix = Einzelkarte + Phönix

    # Bomben     0     1     2     3    4   5   6   7   8   9  10  11  12  13 Karten
    d[CombinationType.BOMB] = [None, None, None, None, [], [], [], [], [], [], [], [], [], []]
    # 4er-Bomben
    d[CombinationType.BOMB][4] = [1 if d[CombinationType.SINGLE][1][v] == 4 else 0 for v in range(15)]
    # Straßenbomben
    for n in range(5, 14):  # Anzahl Karten in der Straßenbombe (5 bis 13)
        bombs0 = [4 if v > n else 0 for v in range(15)]  # Werte 0 bis As
        for v in range(n + 1, 15):  # höchste Karte (=Wert der Kombination)
            for color in range(4):
                for i in range(n):
                    if c[color][v - i] == 0:
                        bombs0[v] -= 1
                        break
        d[CombinationType.BOMB][n] = bombs0

    # Straßen    0     1     2     3     4    5   6   7   8   9  10  11  12  13  14 Karten
    d[CombinationType.STREET] = [None, None, None, None, None, [], [], [], [], [], [], [], [], [], []]
    for n in range(14, 4, -1):  # Anzahl Karten in der Straße (14 bis 5)
        # Wert        0  1  2  3  4  5  6  7  8  9 10 11 12 13 14
        d[CombinationType.STREET][n] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        for v in range(n, 15):  # höchste Karte (=Wert der Kombination)
            phoenix_available = phoenix
            counter = 1
            for i in range(n):
                if phoenix_available and not d[CombinationType.SINGLE][1][v - i] and (i < n - 1 or v == 14):
                    phoenix_available = False  # Lücke mit Phönix ersetzten (nur nicht ganz hinten, wenn vorne noch Platz wäre)
                else:
                    counter *= d[CombinationType.SINGLE][1][v - i]
            if phoenix_available and counter:
                counter_without_phoenix = counter  # Anzahl Kombinationsmöglichkeiten ohne Phönix
                for i in range(n):  # jede Karte mit dem Phönix ersetzten und zu den Möglichkeiten dazuzählen
                    counter += int(counter_without_phoenix / d[CombinationType.SINGLE][1][v - i])
            d[CombinationType.STREET][n][v] = counter

    # Wir wissen nun die Anzahl Kombinationen, die mit allen Handkarten der anderen Spieler zusammen gebildet
    # werden können. Als Nächstes berechnen wir die statistische Häufigkeit der Kombinationen auf der Hand der
    # einzelnen Mitspieler.

    # Wahrscheinlichkeit, dass die Mitspieler eine Kombination mit bestimmter Länge auf der Hand haben.
    # p[0][n]+p[1][n]+p[2][n]+p[3][n] ist die Wahrscheinlichkeit, dass irgendein Mitspieler eine Kombi mit n Karten hat.
    # 1 - (p[0][n]+p[1][n]+p[2][n]+p[3][n]) ist die Wahrscheinlichkeit, das kein Mitspieler eine Kombi mit n Karten hat.
    #       0  1  2  3  4  5  6  7  8  9 10 11 12 13 14  Kombi-Länge n
    p: List[Optional[List[float]]] = [
        [None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Spieler 0
        [None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Spieler 1
        [None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Spieler 2
        [None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]   # Spieler 3
    ]
    if sum_c > 0:
        for i in range(4):  # Mitspieler
            if i == player:
                p[i] = None  # die Wahrscheinlichkeiten für die eigenen Handkarten werden nicht benötigt
                continue
            h = number_of_cards[i]  # Anzahl Handkarten des Mitspielers i
            p[i][1] = h / sum_c  # Wahrscheinlichkeit, dass der Spieler i eine bestimmte Einzelkarte hat
            for j in range(1, min(sum_c, 14)):
                # nachdem eine Karte gezogen wurde, gibt es noch h - 1 Handkarten und sum_c - 1 ungespielte Karten
                p[i][j + 1] = p[i][j] * (h - j) / (sum_c - j)

    # Indizes der Mitspieler
    opp_right = (player + 1) % 4
    partner = (player + 2) % 4
    opp_left = (player + 3) % 4

    # Wahrscheinlichkeit, dass ein Mitspieler eine Bombe werfen kann
    p_bomb_opp = sum([sum(d[CombinationType.BOMB][n]) * (p[opp_right][n] + p[opp_left][n]) for n in range(4, 14)])
    p_bomb_par = sum([sum(d[CombinationType.BOMB][n]) * p[partner][n] for n in range(4, 14)])

    # Anzahl der möglichen Bomben auf den Händen der Mitspieler gesamt
    sum_bombs = sum([sum(d[CombinationType.BOMB][n]) for n in range(4, 14)])

    # Uns interessieren nur die Kombinationen der Mitspieler, die zu den eigenen Handkarten passen...
    statistic = {}
    for cards, combination in combis:
        t, n, v = combination

        if t == CombinationType.BOMB:
            # Anzahl Kombis der Mitspieler insgesamt, die hier betrachtet werden (das sind alle Kombis bis auf Hund)
            sum_combis = \
                sum([sum(d[k][m]) for k in range(1, 7) for m in range(1, len(d[k])) if d[k][m] is not None]) \
                + (0 if combination == FIGURE_DOG else sum_bombs)

            # lo = normale Kombis + kürzere Bomben + niederwertige Bomben gleicher Länge
            lo_opp = \
                sum([sum(d[k][m]) * (p[opp_right][m] + p[opp_left][m]) for k in range(1, 7) for m in range(1, len(d[k])) if d[k][m] is not None]) \
                + sum([sum(d[CombinationType.BOMB][m]) * (p[opp_right][m] + p[opp_left][m]) for m in range(4, n)]) \
                + sum(d[CombinationType.BOMB][n][:v]) * (p[opp_right][n] + p[opp_left][n])
            lo_par = \
                sum([sum(d[k][m]) * p[partner][m] for k in range(1, 7) for m in range(1, len(d[k])) if d[k][m] is not None]) \
                + sum([sum(d[CombinationType.BOMB][m]) * p[partner][m] for m in range(4, n)]) \
                + sum(d[CombinationType.BOMB][n][:v]) * p[partner][n]

            # hi = längere Bomben + höherwertige Bomben gleicher Länge
            hi_opp = \
                sum([sum(d[CombinationType.BOMB][m]) * (p[opp_right][m] + p[opp_left][m]) for m in range(n + 1, 14)]) \
                + sum(d[CombinationType.BOMB][n][v + 1:]) * (p[opp_right][n] + p[opp_left][n])
            hi_par = \
                sum([sum(d[CombinationType.BOMB][m]) * p[partner][m] for m in range(n + 1, 14)]) \
                + sum(d[CombinationType.BOMB][n][v + 1:]) * p[partner][n]

            # eq = gleichwertige Bomben gleicher Länge
            eq_opp = d[CombinationType.BOMB][n][v] * (p[opp_right][n] + p[opp_left][n])
            eq_par = d[CombinationType.BOMB][n][v] * p[partner][n]

        else:  # keine Bombe
            # Anzahl Kombis der Mitspieler, die betrachtet werden (Kombis gleicher Länge (aber kein Hund) plus Bomben)
            sum_combis = sum(d[t][n][1:]) + (0 if combination == FIGURE_DOG else sum_bombs)

            # niederwertige Kombis (ohne Hund) - wie viele Kombinationen gibt es, die ich mit combi stechen kann?
            a = 1
            b = 15 if combination == FIGURE_PHO else v
            w = sum(d[t][n][a:b]) + (d[t][n][16] if combination == FIGURE_DRA else 0)  # Anzahl niederwertiger Kombinationen
            lo_opp = (p[opp_right][n] + p[opp_left][n]) * w
            lo_par = p[partner][n] * w

            # höherwertige Kombis
            a = trick_combination[2] + 1 if combination == FIGURE_PHO else v + 1
            b = 16
            w = sum(d[t][n][a:b]) + (d[t][n][16] if t == CombinationType.SINGLE and combination != FIGURE_DRA else 0)  # höherwertige (ohne Bomben)
            hi_opp = (p[opp_right][n] + p[opp_left][n]) * w + (0 if combination == FIGURE_DOG else p_bomb_opp)
            hi_par = p[partner][n] * w + (0 if combination == FIGURE_DOG else p_bomb_par)

            # gleichwertige Kombis
            w = d[t][n][v]  # Anzahl gleichwertige Kombinationen
            eq_opp = (p[opp_right][n] + p[opp_left][n]) * w
            eq_par = p[partner][n] * w

        # Beim Phönix wurden die spielbaren Kombinationen (außer Drache) doppelt gerechnet. Das liegt daran, dass der
        # Wert vom ausgelegten Stich abhängt.
        w = sum_combis + (sum(d[t][n][(trick_combination[2] + 1):15]) if combination == FIGURE_PHO else 0)
        if w:
            # normalisieren
            lo_opp /= w
            lo_par /= w
            hi_opp /= w
            hi_par /= w
            eq_opp /= w
            eq_par /= w
            # if combination == FIGURE_PHO:
            #     assert eq_opp == 0
            #     assert eq_par == 0
            #     w = lo_opp + lo_par + hi_opp + hi_par
            #     if w > 1:
            #         lo_opp /= w
            #         lo_par /= w
            #         hi_opp /= w
            #         hi_par /= w
            # assert 0 <= lo_opp + hi_opp + eq_opp <= 1
            # assert 0 <= lo_par + hi_par + eq_par <= 1
            assert 0 <= lo_opp + lo_par + hi_opp + hi_par + eq_opp + eq_par <= 1.000001, lo_opp + lo_par + hi_opp + hi_par + eq_opp + eq_par
        else:
            assert lo_opp + lo_par + hi_opp + hi_par + eq_opp + eq_par == 0

        statistic.setdefault(tuple(cards), (lo_opp, lo_par, hi_opp, hi_par, eq_opp, eq_par))
    return statistic


# todo dies wird neue Version, die die Wahrscheinlichkeitsberechnung korrekt durchführt (unter der Verwendung der Hilfstabelle)

# p_lo # Wahrscheinlichkeit, dass die Kombination angespielt wird.
# p_hi # Wahrscheinlichkeit, dass die Kombination überstochen wird.
# p_an = 1 - p_hi # Wahrscheinlichkeit, mit der Kombination das Anspielrecht zu erhalten.
# v_ausspielen = (1 - p_lo) * p_an # Bewertung der Kombination, die ausgespielt wird.
# v_bleibt = p_lo * p_an # Bewertung der Kombination, die auf der Hand bleibt.

# Berechnet die Wahrscheinlichkeit, dass die Mitspieler eine bestimmte Kombination anspielen bzw. überstechen können
#
# Für jede eigene Kombination liefert die Funktion folgende Werte:
# p_lo: Wahrscheinlichkeit, dass ein Mitspieler diese Kombination (mit niederem Rang) anspielen kann
# p_hi_opp_right: Wahrscheinlichkeit, dass der rechte Gegner diese Kombination überstechen kann
# p_hi_opp_left: Wahrscheinlichkeit, dass der linke Gegner diese Kombination überstechen kann
# p_hi_par: Wahrscheinlichkeit, dass der Partner diese Kombination überstechen kann
#
# player: Meine Spielernummer (zw. 0 und 3)
# hand: Eigene Handkarten
# combis: Zu bewertende Kombinationen (gebildet aus den Handkarten) [(Karten, (Typ, Länge, Rang)), ...]
# number_of_cards: Anzahl der Handkarten aller Spieler.
# trick_combination: Kombination (Typ, Länge, Rang) des aktuellen Stichs ((0,0,0), falls kein Stich liegt)
# unplayed_cards: Noch nicht gespielte Karten (inkl. eigene Handkarten)
def calc_statistic2(player: int, hand: Cards, combis: List[Tuple[Cards, Combination]], number_of_cards: List[int], _trick_combination: Combination, unplayed_cards: Cards) -> Dict[Cards, Tuple[float, float, float, float]]:
    assert hand  # wir haben bereits bzw. noch Karten auf der Hand
    assert len(hand) == number_of_cards[player]

    if sum(number_of_cards) != len(unplayed_cards):
        # die Karten werden gerade verteilt bzw. es wird geschupft!
        m = len(hand)
        assert m in (0, 8, 11, 14)
        assert len(unplayed_cards) == 56
        n = int((56 - m) / 3)
        number_of_cards = [n, n, n, n]  # wir tun so, als wenn alle Karten bereits verteilt sind
        number_of_cards[player] = m

    # Indizes der Mitspieler
    _opp_right = (player + 1) % 4
    _partner = (player + 2) % 4
    _opp_left = (player + 3) % 4

    # Uns interessieren nur die Kombinationen der Mitspieler, die zu den eigenen Handkarten passen...
    statistic = {}
    for cards, combination in combis:
        _t, _n, _v = combination
        p_lo = 0.0
        p_hi = 0.0
        # todo
        statistic[tuple(cards)] = p_lo, p_hi

    return statistic