__all__ = "calc_statistic"

# todo alles Überprüfen und bei Bedarf korrigieren

# todo Dokumentieren (reStructuredText)

# p_lo  # Wahrscheinlichkeit, dass die Kombination überstochen zu werden
# p_hi  # Wahrscheinlichkeit, mit der Kombination überstochen zu werden
# p_an = 1 - p_hi  # Wahrscheinlichkeit, mit der Kombination das Anspielrecht zu erhalten
# v_ausspielen = (1 - p_lo) * p_an  # Bewertung der Kombination, die ausgespielt wird
# v_bleibt = p_lo * p_an  # Bewertung der Kombination, die auf der Hand bleibt

# Berechnet die Wahrscheinlichkeit, dass die Mitspieler eine bestimmte Kombination anspielen bzw. überstechen können
#
# Für jede eigene Kombination liefert die Funktion folgende Werte:
# p_lo: Wahrscheinlichkeit, dass ein Mitspieler diese Kombination (mit niederem Rang) anspielen kann
# p_hi: Wahrscheinlichkeit, dass ein Mitspieler diese Kombination überstechen kann
#
# player: Meine Spielernummer (zw. 0 und 3)
# hand: Eigene Handkarten
# combis: Zu bewertende Kombinationen (gebildet aus den Handkarten) [(Karten, (Typ, Länge, Rang)), ...]
# number_of_cards: Anzahl der Handkarten aller Spieler.
# trick_figure: Typ, Länge, Rang des aktuellen Stichs ((0,0,0), falls kein Stich liegt)
# unplayed_cards: Noch nicht gespielte Karten (inkl. eigene Handkarten)
def calc_statistic(player: int, hand:  list[tuple], combis: list[tuple], number_of_cards:  list[int], trick_figure: tuple, unplayed_cards: list[tuple]) -> dict:
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
    opp_right = (player + 1) % 4
    partner = (player + 2) % 4
    opp_left = (player + 3) % 4

    # Uns interessieren nur die Kombinationen der Mitspieler, die zu den eigenen Handkarten passen...
    statistic = {}
    for cards, figure in combis:
        t, n, v = figure
        p_lo = 0.0
        p_hi = 0.0
        # todo
        statistic[tuple(cards)] = p_lo, p_hi

    return statistic