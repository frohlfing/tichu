import pytest
from src.lib.cards import parse_cards
from src.lib.combinations import stringify_figure, CombinationType
# noinspection PyProtectedMember
from src.lib.prob.prob_lo import possible_hands_lo, prob_of_lower_combi

@pytest.mark.parametrize("cards, k, figure, matches_expected, total_expected, msg", [
    # Einzelkarte
    ("Dr RK GK BD S4 R3 R2", 3, (1, 1, 11), 31, 35, "Einzelkarte"),
    ("Dr BD RB SB R3 R2", 3, (1, 1, 11), 16, 20, "Einzelkarte mit 2 Buben"),
    ("Ph RB G6 B5 R2", 3, (1, 1, 5), 9, 10, "Einzelkarte mit Phönix"),
    ("Dr Ph Ma S4 R3 R2", 1, (1, 1, 0), 0, 6, "Einzelkarte Hund"),
    ("Dr Hu Ph S4 R3 R2", 1, (1, 1, 1), 0, 6, "Einzelkarte Mahjong"),
    ("Hu Ph Ma S4 R3 R2", 1, (1, 1, 15), 5, 6, "Einzelkarte Drache"),
    ("Dr Hu Ma S4 R3 R2", 1, (1, 1, 16), 4, 6, "Einzelkarte Phönix"),
    ("Dr Hu Ma S4 R3 R2 Ph", 1, (1, 1, 16), 4, 7, "Einzelkarte Phönix (2)"),
    # Pärchen
    ("Dr RK GK BB SB RB R2", 5, (2, 2, 12), 18, 21, "Pärchen ohne Phönix"),
    ("Ph RK GK BD SB RB R2", 5, (2, 2, 11), 10, 21, "Pärchen mit Phönix"),
    ("Ph RK GK BD SB RB R2", 5, (2, 2, 12), 19, 21, "Pärchen mit Phönix (2)"),
    ("RZ GZ BZ SZ R9 S9", 5, (2, 2, 10), 4, 6, "Pärchen mit 4er-Bombe"),
    ("RZ R9 R8 R7 R6 S6", 5, (2, 2, 11), 4, 6, "Pärchen mit Farbbombe"),
    # Drilling
    ("SK RK GB BB SB R3 R2", 4, (3, 3, 12), 4, 35, "Drilling ohne Phönix"),
    ("Ph RK GK BB SB R3 R2", 4, (3, 3, 13), 4, 35, "Drilling mit Phönix"),
    ("RZ GZ BZ SZ R9 S9 B9", 5, (3, 3, 10), 6, 21, "Drilling mit 4er-Bombe"),
    ("SB RZ R9 R8 R7 R6", 5, (3, 3, 11), 0, 6, "Drilling mit Farbbombe"),
    # Treppe
    ("RK GK SK BD SD GB RB", 5, (4, 4, 13), 3, 21, "2er-Treppe aus Fullhouse"),
    ("SB RZ R9 G9 R8 G8 B4", 9, (4, 4, 9), 0, 0, "2er-Treppe nicht möglich"),
    ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 10), 12, 210, "2er-Treppe mit Phönix"),
    ("RK GK BD SD SB RB BB", 6, (4, 6, 14), 3, 7, "3er-Treppe ohne Phönix"),
    ("Ph GK BD SD SB RB BB", 6, (4, 6, 14), 3, 7, "3er-Treppe mit Phönix"),
    ("GA RA GK RK SD BD SB BB GB BZ RZ G9 B9 R9 Ph", 13, (4, 10, 14), 84, 105, "5er-Treppe"),
    # Fullhouse
    ("RK GD BD SB RB BB S2", 6, (5, 5, 13), 2, 7, "Fullhouse ohne Phönix"),
    ("BB RB SB BZ RZ R9 S9 R8", 7, (5, 5, 12), 5, 8, "Fullhouse und zusätzliches Pärchen"),
    ("BB RB SB G9 R9 S9 R7 S2", 7, (5, 5, 10), 5, 8, "Fullhouse mit 2 Drillinge"),
    ("Ph GK BD SB RB BB S2", 6, (5, 5, 12), 3, 7, "Fullhouse mit Phönix für Paar"),
    ("RK GK BD SB RB BZ Ph", 6, (5, 5, 12), 2, 7, "Fullhouse mit Phönix für Drilling"),
    # Straße
    ("BK SD BD RB BZ B9 R3", 6, (6, 5, 14), 3, 7, "5er-Straße bis König aus 7 Karten ohne Phönix"),
    ("RA GK BD SB RZ B9 R3", 6, (6, 5, 14), 2, 7, "5er-Straße bis Ass aus 7 Karten ohne Phönix"),
    ("GA RK GD RB GZ R9 S8 B7", 5, (6, 5, 13), 2, 56, "5er-Straße bis Ass aus 8 Karten ohne Phönix"),
    ("SK RD GB BB RZ B9 R8 R2", 6, (6, 5, 13), 5, 28, "5er-Straße mit 2 Buben aus 8 Karten ohne Phönix"),
    ("RA GK BD RZ B9 R8 Ph", 6, (6, 5, 13), 2, 7, "5er-Straße aus 7 Karten mit Phönix (Lücke gefüllt)"),
    ("RA BD BB RZ B9 B2 Ph", 6, (6, 5, 13), 0, 7, "5er-Straße aus 7 Karten mit Phönix (nicht unten verlängert)"),
    ("RA SK BD BB B9 B2 Ph", 6, (6, 5, 14), 2, 7, "5er-Straße bis zum Ass mit Phönix (Lücke gefüllt)"),
    ("Ph SK RK GD BB RZ B9 R8", 6, (6, 5, 13), 11, 28, "5er-Straße aus 8 Karten mit 2 Könige mit Phönix (verlängert)"),
    ("GA RK GD RB GZ R9 S8 B7 S6 Ph", 9, (6, 5, 11), 9, 10, "5er-Straße aus 10 Karten"),
    ("SB RZ R9 R8 R7 R6", 5, (6, 5, 11), 1, 6, "Straße mit Farbbombe (bekannter Fehler, 0/6 wäre eigentlich richtig)"),
    # Bombe
    ("RK GB BB SB RB BZ R2", 5, (7, 4, 10), 21, 21, "4er-Bombe"),
    ("BK BB BZ B9 B8 B7 B2", 5, (7, 7, 10), 21, 21, "Farbbombe"),
])
def test_possible_hands_lo(cards, k, figure, matches_expected, total_expected, msg):
    """Testfunktion possible_hands_lo() testen"""
    matches, hands = possible_hands_lo(parse_cards(cards), k, figure)
    assert sum(matches) == matches_expected
    assert len(hands) == total_expected
    assert len(matches) == total_expected

@pytest.mark.parametrize("cards, k, figure, expected, msg", [
    # Einzelkarte
    ("Dr RK GK BD S4 R3 R2", 3, (1, 1, 11), 31/35, "Einzelkarte"),
    ("Dr BD RB SB R3 R2", 3, (1, 1, 11), 16/20, "Einzelkarte mit 2 Buben"),
    ("Ph RB G6 B5 R2", 3, (1, 1, 5), 9/10, "Einzelkarte mit Phönix"),
    ("Dr Ph Ma S4 R3 R2", 1, (1, 1, 0), 0.0, "Einzelkarte Hund"),
    ("Dr Hu Ph S4 R3 R2", 1, (1, 1, 1), 0.0, "Einzelkarte Mahjong"),
    ("Hu Ph Ma S4 R3 R2", 1, (1, 1, 15), 5/6, "Einzelkarte Drache"),
    ("Dr Hu Ma S4 R3 R2", 1, (1, 1, 16), 4/6, "Einzelkarte Phönix"),
    ("Dr Hu Ma S4 R3 R2 Ph", 1, (1, 1, 16), 4/7, "Einzelkarte Phönix (2)"),
    ("Dr RB G6 B5 S4 R3 R2", 0, (1, 1, 11), 0.0, "Einzelkarte k == 0"),
    # Pärchen
    ("Dr RK GK BB SB RB R2", 5, (2, 2, 12), 18/21, "Pärchen ohne Phönix"),
    ("Ph RK GK BD SB RB R2", 5, (2, 2, 11), 10/21, "Pärchen mit Phönix"),
    ("Ph RK GK BD SB RB R2", 5, (2, 2, 12), 19/21, "Pärchen mit Phönix (2)"),
    ("RZ GZ BZ SZ R9 S9", 5, (2, 2, 10), 4/6, "Pärchen mit 4er-Bombe"),
    ("RZ R9 R8 R7 R6 S6", 5, (2, 2, 11), 4/6, "Pärchen mit Farbbombe"),
    # Drilling
    ("SK RK GB BB SB R3 R2", 4, (3, 3, 12), 4/35, "Drilling ohne Phönix"),
    ("Ph RK GK BB SB R3 R2", 4, (3, 3, 13), 4/35, "Drilling mit Phönix"),
    ("RZ GZ BZ SZ R9 S9 B9", 5, (3, 3, 10), 6/21, "Drilling mit 4er-Bombe"),
    ("SB RZ R9 R8 R7 R6", 5, (3, 3, 11), 0.0, "Drilling mit Farbbombe"),
    # Treppe
    ("RK GK SK BD SD GB RB", 5, (4, 4, 13), 3/21, "2er-Treppe aus Fullhouse"),
    ("SB RZ R9 G9 R8 G8 B4", 9, (4, 4, 9), 0.0, "2er-Treppe nicht möglich"),
    ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 10), 12/210, "2er-Treppe mit Phönix"),
    ("RK GK BD SD SB RB BB", 6, (4, 6, 14), 3/7, "3er-Treppe ohne Phönix"),
    ("Ph GK BD SD SB RB BB", 6, (4, 6, 14), 3/7, "3er-Treppe mit Phönix"),
    ("GA RA GK RK SD BD SB BB GB BZ RZ G9 B9 R9 Ph", 13, (4, 10, 14), 84/105, "5er-Treppe"),
    # Fullhouse
    ("RK GD BD SB RB BB S2", 6, (5, 5, 13), 2/7, "Fullhouse ohne Phönix"),
    ("BB RB SB BZ RZ R9 S9 R8", 7, (5, 5, 12), 5/8, "Fullhouse und zusätzliches Pärchen"),
    ("BB RB SB G9 R9 S9 R7 S2", 7, (5, 5, 10), 5/8, "Fullhouse mit 2 Drillinge"),
    ("Ph GK BD SB RB BB S2", 6, (5, 5, 12), 3/7, "Fullhouse mit Phönix für Paar"),
    ("RK GK BD SB RB BZ Ph", 6, (5, 5, 12), 2/7, "Fullhouse mit Phönix für Drilling"),
    # Straße
    ("BK SD BD RB BZ B9 R3", 6, (6, 5, 14), 3/7, "5er-Straße bis König aus 7 Karten ohne Phönix"),
    ("RA GK BD SB RZ B9 R3", 6, (6, 5, 14), 2/7, "5er-Straße bis Ass aus 7 Karten ohne Phönix"),
    ("GA RK GD RB GZ R9 S8 B7", 5, (6, 5, 13), 2/56, "5er-Straße bis Ass aus 8 Karten ohne Phönix"),
    ("SK RD GB BB RZ B9 R8 R2", 6, (6, 5, 13), 5/28, "5er-Straße mit 2 Buben aus 8 Karten ohne Phönix"),
    ("RA GK BD RZ B9 R8 Ph", 6, (6, 5, 13), 2/7, "5er-Straße aus 7 Karten mit Phönix (Lücke gefüllt)"),
    ("RA BD BB RZ B9 B2 Ph", 6, (6, 5, 13), 0.0, "5er-Straße aus 7 Karten mit Phönix (nicht unten verlängert)"),
    ("RA SK BD BB B9 B2 Ph", 6, (6, 5, 14), 2/7, "5er-Straße bis zum Ass mit Phönix (Lücke gefüllt)"),
    ("Ph SK RK GD BB RZ B9 R8", 6, (6, 5, 13), 11/28, "5er-Straße aus 8 Karten mit 2 Könige mit Phönix (verlängert)"),
    ("GA RK GD RB GZ R9 S8 B7 S6 Ph", 9, (6, 5, 11), 9/10, "5er-Straße aus 10 Karten"),
    ("SB RZ R9 R8 R7 R6", 5, (6, 5, 11), 1/6, "Straße mit Farbbombe (bekannter Fehler, 0/6 wäre eigentlich richtig)"),
    # Bombe
    ("RK GB BB SB RB BZ R2", 5, (7, 4, 10), 1.0, "4er-Bombe"),
    ("BK BB BZ B9 B8 B7 B2", 5, (7, 7, 10), 1.0, "Farbbombe"),
])
def test_prob_of_lower_combi_explicit(cards, k, figure, expected, msg):
    """prob_of_lower_combi() testen (explizit ausgesuchte Fälle)"""
    if k > len(cards.split()):
        with pytest.raises(AssertionError):
            prob_of_lower_combi(parse_cards(cards), k, figure)
    else:
        actual = prob_of_lower_combi(parse_cards(cards), k, figure)
        assert pytest.approx(actual, abs=1e-15) == expected, msg

@pytest.mark.parametrize("cards, k, combination", [
    # Rastertests für SINGLE
    *[
        (cards, k, (CombinationType.SINGLE, 1, r))
        for cards in [
            "SB RZ R9 G9 R8 G8 B4",
            "SB RZ GZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 R8 G8 B4",  # 4er-Bombe
            "SB RZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",  # 4er-Bombe
            "Ph SB RZ R9 G9 R8 G8 B4",
            "SB RZ Ph R9 G9 R8 G8 B4",
            "SB RZ GZ BZ Ph G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 Ph R8 G8 B4",  # 4er-Bombe
            "SB RZ R9 G9 S9 R8 G8 B4 Ph",
            "Ph SB RZ GZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "Ph Dr RB GZ BZ SZ R9 G9 S9 R8 G8 B4",
            "Ph SB RB GZ BZ SZ R9 G9 S9 R8 G8 B4 Hu",
            "Ph SB RB GZ BZ SZ R9 G9 S9 R8 G8 B4 B2 Ma",
            "Ph SB RB GZ BZ SZ R9 G9 B6 B5 B4 B3 B2 Ma",  # Farbbombe
        ]
        for r in [0, 1, 9, 10, 14, 15, 16]
        for k in [0, 3, 4, 5, 7, 9, 13, 14]
    ],
    # Rastertests für PAIR
    *[
        (cards, k, (CombinationType.PAIR, 2, r))
        for cards in [
            "SB RZ R9 G9 R8 G8 B4",
            "SB RZ GZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 R8 G8 B4",  # 4er-Bombe
            "SB RZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",  # 4er-Bombe
            "Ph SB RZ R9 G9 R8 G8 B4",
            "SB RZ Ph R9 G9 R8 G8 B4",
            "SB RZ GZ BZ Ph G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 Ph R8 G8 B4",  # 4er-Bombe
            "SB RZ R9 G9 S9 R8 G8 B4 Ph",
            "Ph SB RZ GZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",  # 4er-Bombe
            "Ph SB RB GZ BZ SZ R9 G9 B6 B5 B4 B3 B2 Ma",  # Farbbombe
        ]
        for r in [9]
        for k in [0, 3, 4, 5, 7, 9, 13, 14]
    ],
    # Rastertests für TRIPLE
    *[
        (cards, k, (CombinationType.TRIPLE, 3, r))
        for cards in [
            "SB RZ R9 G9 R8 G8 B4",
            "SB RZ GZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 R8 G8 B4",  # 4er-Bombe
            "SB RZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",  # 4er-Bombe
            "Ph SB RZ R9 G9 R8 G8 B4",
            "SB RZ Ph R9 G9 R8 G8 B4",
            "SB RZ GZ BZ Ph G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 Ph R8 G8 B4",  # 4er-Bombe
            "SB RZ R9 G9 S9 R8 G8 B4 Ph",
            "Ph SB RZ GZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",  # 4er-Bombe
            "Ph SB RB GZ BZ SZ R9 G9 B6 B5 B4 B3 B2 Ma",  # Farbbombe
        ]
        for r in [9]
        for k in [0, 3, 4, 5, 7, 9, 13, 14]
    ],
    # Rastertests für STAIR
    *[
        (cards, k, (CombinationType.STAIR, m, r))
        for cards in [
            "SB RZ R9 G9 R8 G8 B4",
            "SB RZ GZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 R8 G8 B4",  # 4er-Bombe
            "SB RZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",  # 4er-Bombe
            "Ph SB RZ R9 G9 R8 G8 B4",
            "SB RZ Ph R9 G9 R8 G8 B4",
            "SB RZ GZ BZ Ph G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 Ph R8 G8 B4",  # 4er-Bombe
            "SB RZ R9 G9 S9 R8 G8 B4 Ph",
            "Ph SB RZ GZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",  # 4er-Bombe
            "Ph GK BK SD SB RB BZ R9",
            "Ph GK BK SD SB RB R9",
            "Ph GK BK SD SB R9 S4",
        ]
        for m in [4, 6]
        for r in [9, 10]
        for k in [0, 3, 4, 5, 7, 9, 13, 14]
    ],
    # Rastertests für FULLHOUSE
    *[
        (cards, k, (CombinationType.FULLHOUSE, 5, r))
        for cards in [
            "SB RZ R9 G9 R8 G8 B4",
            "SB RZ GZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 R9 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 R8 G8 B4",  # mit 4er-Bombe
            "SB RZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",  # mit 4er-Bombe
            "Ph SB RZ R9 G9 R8 G8 B4",
            "SB RZ Ph R9 G9 R8 G8 B4",
            "SB RZ GZ BZ Ph G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 Ph R8 G8 B4",  # mit 4er-Bombe
            "SB RZ R9 G9 S9 R8 G8 B4 Ph",
            "Ph SB RZ GZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ SZ R9 G9 S9 R8 G8 B4",  # mit 4er-Bombe
            "Ph SB RB GZ BZ SZ R9 G9 B6 B5 B4 B3 B2 Ma",  # Farbbombe
        ]
        for r in [9]
        for k in [0, 3, 4, 5, 7, 9, 13, 14]
    ],
    # Rastertests für STREET
    *[
        (cards, k, (CombinationType.STREET, m, r))
        for cards in [
            # ohne Phönix
            "GB RZ G9 R8 G7",
            "GD RB GZ R9 G8 R7",
            "GA RK GD RB GZ R9 S8 B7 S6 B5 S4 B3 S2",
            "GA RK GD RB GZ R9 S8 B7 S6 B5 S4 B3 S2 Ma",
            "GK BB SB GB RZ BZ GZ R9 S9 B9 R8 S8 G8 R7 S7 G7 R4 R2",
            # mit Phönix
            "GA RK GD RB GZ R9 S8 B7 S6 B5 S4 B3 Ph",
            "GA RK GD Ph GZ R9 S8 B7 S6 B5 S4 B3 S2",
            "GA RK GD RB GZ R9 S8 Ph S6 B5 S4 B3 S2",
            "GA RK GD RB Ph R9 S8 B7 S6 B5 S4 B3 S2",
            "GK RK GD RB Ph R9 S8 B7 S6 B5 S4 B3 S2",
            "GK RB GZ R9 G8 R7 SB BZ S9 B8 S7 B4 Ph",
            "Ph R7 G6 R5 G4 R3 S2 B2 Ma",
            "Ph RB GZ R8 G7 R4 S2 B2",
            # mit Bombe, ohne Phönix
            "GB GZ G9 G8 G7",
            "GD GB GZ G9 G8 G7",
            "GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2",
            "SK GB GZ G9 G8 G7 RB RZ R9 R8 R7 BB BZ B9 B8 B7 S4 S2",
            # mit Bombe, mit Phönix
            "GA GK GD GB GZ G9 R8 G7 G6 G5 G4 G3 Ph",
            "GA GK GD Ph GZ G9 R8 G7 G6 G5 G4 G3 G2",
            "GA GK GD GB GZ G9 R8 Ph G6 G5 G4 G3 G2",
            "GA GK GD GB Ph G9 G8 G7 G6 G5 G4 G3 G2",
            "SK GB GZ G9 G8 G7 RB RZ R9 R8 R7 S4 Ph",
            "Ph SB RB GZ BZ SZ R9 G9 B6 B5 B4 B3 B2 Ma",  # Farbbombe
        ]
        for m in [5]
        for r in [10]
        for k in [0, 4, 5, 6, 7]
    ],
    # Rastertests für BOMB (4er)
    *[
        (cards, k, (CombinationType.BOMB, 4, r))
        for cards in [
            "SB RZ R9 G9 R8 G8 B4",
        ]
        for r in [9]
        for k in [0, 3, 4, 5, 7, 9, 13, 14]
    ],
    # Rastertests für BOMB (Farbbombe)
    *[
        (cards, k, (CombinationType.BOMB, m, r))
        for cards in [
            "GB GZ G9 G8 G7",
        ]
        for m in [5]
        for r in [10]
        for k in [0, 3, 4, 5, 7, 9, 13, 14]
    ],
])
def test_prob_of_lower_combi_raster(cards, k, combination):
    """prob_of_lower_combi() testen (Rastersuche)"""
    if k > len(cards.split()):
        with pytest.raises(AssertionError):
            prob_of_lower_combi(parse_cards(cards), k, combination)
        return
    matches, hands = possible_hands_lo(parse_cards(cards), k, combination)
    p_expected = sum(matches) / len(hands) if hands else 0.0
    msg = f"{stringify_figure(combination)}"
    # print(f'("{cards}", {k}, ({combination[0]}, {combination[1]}, {combination[2]}), {sum(matches)}, {len(hands)}, {p_expected}, "{msg}"),')
    actual = prob_of_lower_combi(parse_cards(cards), k, combination)
    assert pytest.approx(actual, abs=1e-15) == p_expected, msg
