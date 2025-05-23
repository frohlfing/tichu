import pytest
from src.lib.cards import parse_cards
from src.lib.combinations import stringify_figure, CombinationType
# noinspection PyProtectedMember
from src.lib.prob.prob_hi import possible_hands_hi, prob_of_higher_combi_or_bomb

@pytest.mark.parametrize("cards, k, figure, matches_expected, total_expected, msg", [
    # Einzelkarte
    ("Dr RB G6 B5 S4 R3 R2", 4, (1, 1, 11), 20, 35, "Einzelkarte"),
    ("Dr RB SB B5 S4 R3 R2", 5, (1, 1, 11), 15, 21, "Einzelkarte mit 2 Buben"),
    ("Ph RB G6 B5 S4 R3 R2", 5, (1, 1, 11), 15, 21, "Einzelkarte mit Phönix"),
    ("Dr Hu Ph Ma S4 R3 R2", 1, (1, 1, 0), 7, 7, "Einzelkarte Hund"),
    ("Dr Hu Ph Ma S4 R3 R2", 1, (1, 1, 1), 5, 7, "Einzelkarte Mahjong"),
    ("Dr Hu Ph Ma S4 R3 R2", 1, (1, 1, 15), 0, 7, "Einzelkarte Drache"),
    ("Dr Hu Ph Ma S4 R3 R2", 1, (1, 1, 16), 4, 7, "Einzelkarte Phönix"),
    ("SB RZ GZ BZ SZ R9", 5, (1, 1, 11), 2, 6, "Einzelkarte Bube mit 4er-Bombe"),
    ("Hu Ma RZ GZ BZ SZ", 4, (1, 1, 15), 1, 15, "Einzelkarte Drache mit 4er-Bombe"),
    ("SB RZ R9 R8 R7 R6", 5, (1, 1, 11), 1, 6, "Einzelkarte mit Farbbombe"),
    # Pärchen
    ("Dr RK GK BB SB RB R2", 5, (2, 2, 11), 10, 21, "Pärchen ohne Phönix"),
    ("Ph RK GK BD SB RB R2", 5, (2, 2, 11), 19, 21, "Pärchen mit Phönix"),
    ("SB RZ GZ BZ SZ R9", 5, (2, 2, 11), 2, 6, "Pärchen mit 4er-Bombe"),
    ("SB RZ R9 R8 R7 R6", 5, (2, 2, 11), 1, 6, "Pärchen mit Farbbombe"),
    # Drilling
    ("SK RK GB BB SB R3 R2", 4, (3, 3, 10), 4, 35, "Drilling ohne Phönix"),
    ("Ph RK GB BB SB R3 R2", 4, (3, 3, 10), 13, 35, "Drilling mit Phönix"),
    ("SB RZ GZ BZ SZ R9", 5, (3, 3, 11), 2, 6, "Drilling mit 4er-Bombe"),
    ("SB RZ R9 R8 R7 R6", 5, (3, 3, 11), 1, 6, "Drilling mit Farbbombe"),
    # Treppe
    ("RK GK BD SD GD R9 B2", 6, (4, 4, 12), 5, 7, "2er-Treppe aus Fullhouse"),
    ("SB RZ R9 G9 R8 G8 B4", 9, (4, 4, 9), 0, 0, "2er-Treppe nicht möglich"),
    ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 9), 13, 210, "2er-Treppe mit Phönix"),
    ("RK GK BD SD SB RB BB", 6, (4, 6, 12), 3, 7, "3er-Treppe ohne Phönix"),
    ("Ph GK BD SD SB RB BB", 6, (4, 6, 12), 3, 7, "3er-Treppe mit Phönix"),
    ("GA RA GK RK SD BD SB BB GB BZ RZ G9 B9 R9 Ph", 13, (4, 10, 12), 84, 105, "5er-Treppe"),
    ("GA RA GK RK SD BD SB BB GB BZ RZ G9 B9 R9 S7 R7 Ph", 14, (4, 12, 13), 252, 680, "6er-Treppe"),
    ("GA RA GK RK SD BD SB BB GB BZ RZ G9 B9 R9 S8 R8 S3 S2 Ma Ph", 14, (4, 14, 13), 117, 38760, "7er-Treppe"),
    ("SB RZ GZ BZ SZ R9", 5, (4, 4, 11), 2, 6, "Treppe mit 4er-Bombe"),
    ("SB RZ R9 R8 R7 R6", 5, (4, 4, 11), 1, 6, "Treppe mit Farbbombe"),
    ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 5, (4, 14, 14), 6, 252, "keine 7er-Treppe, aber 4er-Bombe"),
    ("RK RD RB RZ R9 Ph R8 G8 B4", 6, (4, 14, 14), 7, 84, "keine 7er-Treppe, aber Farbbombe"),

    # Fullhouse
    ("RK GK BD SB RB BB S2", 6, (5, 5, 10), 2, 7, "Fullhouse ohne Phönix"),
    ("BK RK SK BZ RZ R9 S9 RB", 7, (5, 5, 12), 5, 8, "Fullhouse und zusätzliches Pärchen"),
    ("BK RK SK G9 R9 S9 RB S2", 7, (5, 5, 12), 5, 8, "Fullhouse mit 2 Drillinge"),
    ("Ph GK BD SB RB BB S2", 6, (5, 5, 10), 3, 7, "Fullhouse mit Phönix für Paar"),
    ("RK GK BD SB RB BZ Ph", 6, (5, 5, 10), 2, 7, "Fullhouse mit Phönix für Drilling"),
    ("SB RZ GZ BZ SZ R9", 5, (5, 5, 11), 2, 6, "Fullhouse mit 4er-Bombe"),
    ("SB RZ R9 R8 R7 R6", 5, (5, 5, 11), 1, 6, "Fullhouse mit Farbbombe"),
    # Straße
    ("BK SD BD RB BZ B9 R3", 6, (6, 5, 12), 3, 7, "5er-Straße bis König aus 7 Karten ohne Phönix"),
    ("RA GK BD SB RZ B9 R3", 6, (6, 5, 12), 3, 7, "5er-Straße bis Ass aus 7 Karten ohne Phönix"),
    ("GA RK GD RB GZ R9 S8 B7", 5, (6, 5, 9), 4, 56, "5er-Straße bis Ass aus 8 Karten ohne Phönix"),
    ("SK RK GD BB RZ B9 R8 R2", 6, (6, 5, 12), 5, 28, "5er-Straße mit 2 Könige aus 8 Karten ohne Phönix"),
    ("RA GK BD RZ B9 R3 Ph", 6, (6, 5, 12), 3, 7, "5er-Straße aus 7 Karten mit Phönix (Lücke gefüllt)"),
    ("Ph SK RK GD BB RZ B9 R8", 6, (6, 5, 12), 18, 28, "5er-Straße aus 8 Karten mit 2 Könige mit Phönix (verlängert)"),
    ("Ph RK GD BB RZ B9 R8 R2", 6, (6, 5, 12), 13, 28, "5er-Straße aus 8 Karten mit Phönix (verlängert)"),
    ("SA RK GD BB RZ B9 R8 Ph", 6, (6, 5, 12), 18, 28, "5er-Straße aus 8 Karten mit Phönix (verlängert, 2)"),
    ("GA RK GD RB GZ R9 S8 B7 Ph", 9, (6, 5, 6), 1, 1, "5er-Straße aus 9 Karten"),
    ("GA RK GD RB GZ R9 S8 B7 S6 Ph", 9, (6, 5, 6), 10, 10, "5er-Straße aus 10 Karten"),
    ("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 G2 S2 Ma Ph", 14, (6, 10, 10), 92, 120, "10er-Straße aus 16 Karten (1)"),
    ("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 G2 S2 Ma Ph", 14, (6, 10, 12), 75, 120, "10er-Straße aus 16 Karten (2)"),
    ("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 S2 Ma Ph", 13, (6, 13, 13), 14, 105, "13er-Straße aus 15 Karten"),
    ("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 G2 S2 Ma Ph", 14, (6, 13, 13), 42, 120, "13er-Straße aus 16 Karten"),
    ("SB RZ GZ BZ SZ R9", 5, (6, 5, 11), 2, 6, "keine Straße, sondern 4er-Bombe"),
    ("SB RZ R9 R8 R7 R6", 5, (6, 5, 11), 1, 6, "Straße mit Farbbombe (1)"),
    ("GD GB GZ G9 G8 G7", 5, (6, 5, 10), 2, 6, "Straße ist Farbbombe (2)"),
    ("BK SD BD BB BZ B9 R3", 6, (6, 5, 12), 3, 7, "Straße mit Farbbombe (3)"),
    ("BK BD BB BZ B9 RK RD RB RZ R9 G2 G3 G4", 11, (6, 5, 12), 73, 78, "Straße mit 2 Farbbomben"),
    # 4er-Bombe
    ("RK GB BB SB RB BZ R2", 5, (7, 4, 10), 3, 21, "4er-Bombe"),
    ("SB RZ R9 R8 R7 R6", 5, (7, 4, 11), 1, 6, "4er-Bombe mit Farbbombe"),
    # Farbbombe
    ("BK BB BZ B9 B8 B7 B2", 5, (7, 5, 10), 1, 21, "Farbbombe"),
    ("SD RZ R9 R8 R7 R6 R5", 6, (7, 5, 11), 1, 7, "Farbbombe mit längerer Farbbombe (1)"),
    ("SK RB RZ R9 R8 R7 R6 S2", 7, (7, 5, 11), 2, 8, "Farbbombe mit längerer Farbbombe (2)"),
    ("BK BD BB BZ B9 RK RD RB RZ R9 S2 S3", 11, (7, 5, 12), 12, 12, "2 Farbbomben aus 12 Karten"),
    ("BK BD BB BZ B9 RK RD RB RZ R9 S2 S3 G7", 11, (7, 5, 12), 53, 78, "2 Farbbomben aus 13 Karten"),
])
def test_possible_hands_hi(cards, k, figure, matches_expected, total_expected, msg):
    """Testfunktion possible_hands_hi() testen"""
    matches, hands = possible_hands_hi(parse_cards(cards), k, figure, with_bombs=True)
    assert sum(matches) == matches_expected, f"{msg} — Trefferanzahl stimmt nicht"
    assert len(hands) == total_expected, f"{msg} — Anzahl Handkarten stimmt nicht"
    assert len(matches) == total_expected, f"{msg} — Länge der Matches stimmt nicht"

@pytest.mark.parametrize("cards, k, figure, expected, msg", [
    # Einzelkarte
    ("Dr RB G6 B5 S4 R3 R2", 0, (1, 1, 11), 0.0, "Einzelkarte k == 0"),
    ("Dr RB G6 B5 S4 R3 R2", 4, (1, 1, 11), 0.5714285714285714, "Einzelkarte"),
    ("Dr RB SB B5 S4 R3 R2", 5, (1, 1, 11), 0.7142857142857143, "Einzelkarte mit 2 Buben"),
    ("Ph RB G6 B5 S4 R3 R2", 5, (1, 1, 11), 0.7142857142857143, "Einzelkarte mit Phönix"),
    # Sonderkarten
    ("Ma", 0, (1, 1, 0), 0.0, "Einzelkarte Hund (keine Handkarten)"),
    ("Ma", 1, (1, 1, 0), 1.0, "Einzelkarte Hund (nur der Mahjong als Handkarte möglich)"),
    ("Dr Ph Ma S4 R3 R2", 1, (1, 1, 0), 1.0, "Einzelkarte Hund"),
    ("Dr Hu Ph S4 R3 R2", 1, (1, 1, 1), 0.8333333333333334, "Einzelkarte Mahjong"),
    ("Hu Ph Ma S4 R3 R2", 1, (1, 1, 15), 0.0, "Einzelkarte Drache"),
    ("Dr Hu Ma S4 R3 R2", 1, (1, 1, 16), 0.6666666666666666, "Einzelkarte Phönix"),
    # Einzelkarte mit 4er-Bombe
    ("SB RZ GZ BZ SZ R9", 5, (1, 1, 11), 0.3333333333333333, "Einzelkarte Bube mit 4er-Bombe"),
    ("Hu Ma RZ GZ BZ SZ", 4, (1, 1, 15), 0.06666666666666667, "Einzelkarte Drache mit 4er-Bombe"),
    # Einzelkarte mit Farbbombe
    ("SB RZ R9 R8 R7 R6", 5, (1, 1, 11), 0.16666666666666667, "Einzelkarte mit Farbbombe"),
    # Einzelkarte mit 4er-Bombe und Farbbombe
    ("RB GZ SZ BZ RZ R9 R8 R7", 5, (1, 1, 10), 0.6785714285714286, "Einzelkarte mit 4er-Bombe und Farbbombe"),
    # Pärchen
    ("Dr RK GK BB SB RB R2", 0, (2, 2, 11), 0.0, "Pärchen k == 0"),
    ("Dr RK GK BB SB RB R2", 5, (2, 2, 11), 0.47619047619047616, "Pärchen ohne Phönix"),
    ("Ph RK GK BD SB RB R2", 5, (2, 2, 11), 0.9047619047619048, "Pärchen mit Phönix"),
    # Pärchen mit 4er-Bombe
    ("SB RZ GZ BZ SZ R9", 5, (2, 2, 11), 0.3333333333333333, "Pärchen mit 4er-Bombe"),
    # Pärchen mit Farbbombe
    ("SB RZ R9 R8 R7 R6", 5, (2, 2, 11), 0.16666666666666667, "Pärchen mit Farbbombe"),
    # Pärchen mit 4er-Bombe und Farbbombe
    ("SB RB GZ SZ BZ RZ R9 R8 R7", 5, (2, 2, 10), 0.3253968253968253, "Pärchen mit 4er-Bombe und Farbbombe"),
    # Drilling
    ("SK RK GB BB SB R3 R2", 0, (3, 3, 10), 0.0, "Drilling k == 0"),
    ("SK RK GB BB SB R3 R2", 4, (3, 3, 10), 0.11428571428571428, "Drilling ohne Phönix"),
    ("Ph RK GB BB SB R3 R2", 4, (3, 3, 10), 0.37142857142857144, "Drilling mit Phönix"),
    # Drilling mit 4er-Bombe
    ("SB RZ GZ BZ SZ R9", 5, (3, 3, 11), 0.3333333333333333, "Drilling mit 4er-Bombe"),
    # Drilling mit Farbbombe
    ("SB RZ R9 R8 R7 R6", 5, (3, 3, 11), 0.16666666666666667, "Drilling mit Farbbombe"),
    # Drilling mit 4er-Bombe und Farbbombe
    ("GB SB RB GZ SZ BZ RZ R9 R8 R7", 5, (3, 3, 10), 0.08333333333333333, "Drilling mit 4er-Bombe und Farbbombe"),
    # 2er-Treppe ohne Phönix
    ("RK GK BD SD GD R9 B2", 0, (4, 4, 12), 0.0, "2er-Treppe k == 0"),
    ("SB RZ R9 G9 R8 G8 B4", 9, (4, 4, 9), 0.0, "2er-Treppe - Exception (k > n)"),
    ("RK GK BD SD GD R9 B2", 6, (4, 4, 12), 0.7142857142857143, "2er-Treppe aus Fullhouse"),
    ("Dr GA BA GK BK SD BD", 6, (4, 4, 14), 0.0, "2er-Treppe über Ass"),
    # 2er-Treppe mit Phönix
    ("Ph GK BK SD SB RB R9", 0, (4, 4, 10), 0.0, "2er-Treppe mit Phönix k == 0"),
    ("Ph GK BK SD SB RB R9", 6, (4, 4, 10), 0.7142857142857143, "2er-Treppe aus 7 Karten mit Phönix (1)"),
    ("Ph GK BK SD SB R9 S4", 6, (4, 4, 10), 0.42857142857142855, "2er-Treppe aus 7 Karten mit Phönix (2)"),
    ("Ph GK BK SD SB RB BZ R9", 6, (4, 4, 10), 0.5, "2er-Treppe aus 8 Karten mit Phönix"),
    ("Ph SB RZ GZ R9 G9 S9 R8 G8 B4", 4, (4, 4, 9), 0.06190476190476191, "2er-Treppe aus 10 Karten mit Phönix"),
    # 3er-Treppe
    ("RK GK BD SD SB RB BB", 6, (4, 6, 12), 0.42857142857142855, "3er-Treppe ohne Phönix"),
    ("Ph GK BD SD SB RB BB", 6, (4, 6, 12), 0.42857142857142855, "3er-Treppe mit Phönix"),
    # 5er-Treppe
    ("GA RA GK RK SD BD SB BB GB BZ RZ G9 B9 R9 Ph", 13, (4, 10, 12), 0.8, "5er-Treppe"),
    # 6er-Treppe
    ("GA RA GK RK SD BD SB BB GB BZ RZ G9 B9 R9 S7 R7 Ph", 14, (4, 12, 13), 0.37058823529411766, "6er-Treppe"),
    # 7er-Treppe
    ("GA RA GK RK SD BD SB BB GB BZ RZ G9 B9 R9 S8 R8 S3 S2 Ma Ph", 14, (4, 14, 13), 0.003018575851393189, "7er-Treppe"),
    # Treppe mit 4er-Bombe
    ("GB SB RZ GZ BZ SZ", 5, (4, 4, 10), 1.0, "Treppe mit 4er-Bombe (1)"),
    ("GB SB RZ GZ BZ SZ", 5, (4, 4, 11), 0.3333333333333333, "Treppe mit 4er-Bombe (2)"),
    ("SB RZ GZ BZ SZ R9 Ph R8 G8 B4", 5, (4, 14, 14), 0.023809523809523808, "keine 7er-Treppe, aber 4er-Bombe"),
    # Treppe mit Farbbombe
    ("GB RB GZ RZ R9 R8 R7", 5, (4, 4, 11), 0.047619047619047616, "Treppe mit Farbbombe (1)"),
    ("GB RB GZ RZ R9 R8 R7", 5, (4, 4, 12), 0.047619047619047616, "Treppe mit Farbbombe (2)"),
    ("RK RD RB RZ R9 Ph R8 G8 B4", 6, (4, 14, 14), 0.08333333333333333, "keine 7er-Treppe, aber Farbbombe"),
    # Treppe mit 4er-Bombe und Farbbombe
    ("GB RB GZ SZ BZ RZ R9 R8 R7", 5, (4, 4, 10), 0.2222222222222222, "Treppe mit 4er-Bombe und Farbbombe (1)"),
    ("GB RB GZ SZ BZ RZ R9 R8 R7", 5, (4, 4, 11), 0.047619047619047616, "Treppe mit 4er-Bombe und Farbbombe (2)"),
    ("GB RB GZ SZ BZ RZ R9 R8 R7", 6, (4, 4, 10), 0.5238095238095238, "Treppe mit 4er-Bombe und Farbbombe (3)"),
    ("GB RB GZ SZ BZ RZ R9 R8 R7", 6, (4, 4, 11), 0.16666666666666666, "Treppe mit 4er-Bombe und Farbbombe (4)"),
    # Fullhouse ohne Phönix
    ("RK GK BD SB RB BB S2", 6, (5, 5, 10), 0.2857142857142857, "Fullhouse ohne Phönix"),
    ("BK RK SK BZ RZ R9 S9 RB", 7, (5, 5, 12), 0.625, "Fullhouse und zusätzliches Pärchen"),
    ("BK RK SK G9 R9 S9 RB S2", 7, (5, 5, 12), 0.625, "Fullhouse mit 2 Drillinge"),
    # Fullhouse mit Phönix
    ("Ph GK BD SB RB BB S2", 0, (5, 5, 10), 0.0, "Fullhouse k == 0"),
    ("Ph GK BD SB RB BB S2", 6, (5, 5, 10), 0.42857142857142855, "Fullhouse mit Phönix für Paar"),
    ("RK GK BD SB RB BZ Ph", 6, (5, 5, 10), 0.2857142857142857, "Fullhouse mit Phönix für Drilling"),
    ("SB RZ GZ BZ Ph G9 R8 G8 B4", 5, (5, 5, 9), 0.07142857142857142, "Fullhouse mit 5 Handkarten mit Phönix"),
    ("SB RZ GZ BZ Ph G9 R8 G8 B4", 6, (5, 5, 9), 0.2619047619047619, "Fullhouse mit 6 Handkarten mit Phönix"),
    # Fullhouse mit 4er-Bombe
    ("SB RZ GZ BZ SZ R9", 5, (5, 5, 11), 0.3333333333333333, "Fullhouse mit 4er-Bombe"),
    # Fullhouse mit Farbbombe
    ("SB RZ R9 R8 R7 R6", 5, (5, 5, 11), 0.16666666666666667, "Fullhouse mit Farbbombe"),
    # Fullhouse mit 4er-Bombe und Farbbombe
    ("GB SB RB GZ SZ BZ RZ R9 R8 R7", 5, (3, 3, 10), 0.1111111111111111, "Fullhouse mit 4er-Bombe und Farbbombe (1)"),
    # 5er-Straße ohne Phönix
    ("BK SD BD RB BZ B9 R3", 0, (6, 5, 12), 0.0, "5er-Straße k == 0"),
    ("BK SD BD RB BZ B9 R3", 6, (6, 5, 12), 0.42857142857142855, "5er-Straße aus 7 Karten ohne Phönix"),
    ("RA RK GD BB RZ B9 R2", 6, (6, 5, 10), 0.42857142857142855, "5er-Straße bis Ass aus 7 Karten ohne Phönix"),
    ("GA RK GD RB GZ R9 S8 B7", 5, (6, 5, 9), 0.07142857142857142, "5er-Straße bis Ass aus 8 Karten ohne Phönix"),
    ("SK RK GD BB RZ B9 R8 R2", 6, (6, 5, 12), 0.17857142857142858, "5er-Straße aus 8 Karten mit 2 Könige ohne Phönix"),
    ("RK GD BB RZ B9 R8 S6 S2", 6, (6, 5, 10), 0.17857142857142858, "5er-Straße bis König aus 8 Karten ohne Phönix"),
    ("SK RK GD BB RZ B9 R8 S6 S2", 6, (6, 5, 10), 0.10714285714285714, "5er-Straße bis König aus 9 Karten mit 2 Könige ohne Phönix"),
    ("RA RK GD BB RZ B9 R8 S7 S6", 6, (6, 5, 10), 0.15476190476190477, "5er-Straße bis Ass aus 9 Karten ohne Phönix"),
    ("GK BB SB GB RZ BZ GZ R9 S9 B9 R8 S8 G8 R7 S7 G7 R4 R2", 7, (6, 5, 10), 0.22652714932126697, "5er-Straße mit Drillinge ohne Phönix"),
    # 5er-Straße mit Phönix
    ("GA RK GD RB GZ Ph", 6, (6, 5, 10), 1.0, "5er-Straße aus 6 Karten mit Phönix (verlängert)"),
    ("RA GK BD RZ B9 R3 Ph", 6, (6, 5, 12), 0.42857142857142855, "5er-Straße aus 7 Karten mit Phönix (Lücke gefüllt)"),
    ("SA RK GD BB RZ B9 Ph", 6, (6, 5, 11), 1.0, "5er-Straße aus 7 Karten mit Phönix (verlängert)"),
    ("Ph SK RK GD BB RZ B9 R8", 6, (6, 5, 12), 0.6428571428571429, "5er-Straße aus 8 Karten mit 2 Könige mit Phönix (verlängert)"),
    ("Ph RK GD BB RZ B9 R8 R2", 6, (6, 5, 12), 0.4642857142857143, "5er-Straße aus 8 Karten mit Phönix (verlängert)"),
    ("GA RK GD RB GZ R9 S8 B7 Ph", 9, (6, 5, 6), 1.0, "5er-Straße aus 9 Karten mit Phönix (verlängert, 1)"),
    ("SA RK GD BB RZ B9 S8 R7 Ph", 6, (6, 5, 10), 0.5595238095238095, "5er-Straße aus 9 Karten mit Phönix (verlängert, 2)"),
    ("GA RK GD RB GZ R9 S8 B7 S6 Ph", 9, (6, 5, 6), 1.0, "5er-Straße aus 10 Karten mit Phönix"),
    ("GA RK GD RB GZ R9 S8 B7 S6 B5 S4 B3 Ph", 6, (6, 5, 10), 0.07634032634032634, "5er-Straße aus 13 Karten mit Phönix (verlängert)"),
    ("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 S2 Ph", 6, (6, 5, 6), 0.0959040959040959, "5er-Straße aus 14 Karten mit Phönix (1)"),
    ("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 S2 Ph", 9, (6, 5, 6), 0.7372627372627373, "5er-Straße aus 14 Karten mit Phönix (2)"),
    ("GA RK GD BB GB RB GZ R9 S8 B7 B6 S6 S5 G4 B4 R4 S3 S2 Ma Ph", 9, (6, 5, 6), 0.3347225529888069, "5er-Straße aus 20 Karten mit Phönix"),
    # Straße mit der Länge 10
    ("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 G2 S2 Ma Ph", 14, (6, 10, 10), 0.7666666666666667, "10er-Straße aus 16 Karten (1)"),
    ("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 G2 S2 Ma Ph", 14, (6, 10, 12), 0.625, "10er-Straße aus 16 Karten (2)"),
    ("GA RK GD BB GB RB GZ R9 S8 B7 B6 S6 S5 G4 B4 R4 S3 S2 Ma Ph", 14, (6, 10, 13), 0.09326625386996903, "10er-Straße aus 20 Karten (1)"),
    ("GA RK GD BB GB RB GZ R9 S8 B7 B6 S6 S5 G4 B4 R4 S3 S2 Ma Ph", 14, (6, 10, 14), 0.0, "10er-Straße aus 20 Karten (2)"),
    # Straße mit der Länge 13
    ("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 S2 Ma Ph", 13, (6, 13, 13), 0.13333333333333333, "13er-Straße aus 15 Karten"),
    ("GA RK GD RB GZ R9 S8 B7 S6 S5 R4 S3 G2 S2 Ma Ph", 14, (6, 13, 13), 0.35, "13er-Straße aus 16 Karten"),
    ("GA RK GD BB GB RB GZ R9 S8 B7 B6 S6 S5 G4 B4 R4 S3 S2 Ma Ph", 14, (6, 13, 13), 0.019814241486068113, "13er-Straße aus 20 Karten"),
    # Straße mit der Länge 14
    ("GA RK GD BB GB RB GZ R9 S8 B7 B6 S6 S5 G4 B4 R4 S3 S2 Ma Ph", 14, (6, 14, 14), 0.0, "14er-Straße"),
    # Straße mit 4er-Bombe
    ("SB RZ GZ BZ SZ R9", 5, (6, 5, 11), 0.3333333333333333, "Straße mit 4er-Bombe"),
    # Straße mit Farbbombe
    ("SB RZ R9 R8 R7 R6", 5, (6, 5, 11), 0.16666666666666667, "Straße mit Farbbombe"),
    ("GB GZ G9 G8 G7", 5, (6, 5, 10), 1.0, "5er-Straße ist Farbbombe"),
    ("GD GB GZ G9 G8 G7", 5, (6, 5, 10), 0.3333333333333333, "6er-Straße ist Farbbombe"),
    ("BK SD BD BB BZ B9 R3", 6, (6, 5, 12), 0.42857142857142855, "5er-Straße mit 2 Damen und mit Farbbombe"),
    ("BK BD BB BZ B9 RK RD RB RZ R9 G2 G3 G4", 11, (6, 5, 12), 0.9358974358974359, "5er-Straße mit 2 Farbbomben"),
    ("GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2", 5, (6, 5, 10), 0.006993006993006993, "13er-Straße mit Farbbombe"),
    ("GA GK GD GB GZ G9 R8 G7 G6 G5 G4 G3 Ph", 5, (6, 5, 10), 0.017094017094017096, "13er-Straße mit 2 Farbbomben mit Phönix"),
    ("SK GB GZ G9 G8 G7 RB RZ R9 R8 R7 S4 Ph", 6, (6, 5, 10), 0.3006993006993007, "2 5er-Straßen mit 2 Farbbomben"),
    # Straße mit 4er-Bombe und Farbbombe
    ("GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2 SA SK SD SB SZ S9 S8 S7 S6 S5 S4 S3 S2 RA RK RD RB RZ R9 R8 R7 R6 R5 R4 R3 R2 BA BK BD BB BZ B9 B8 B7 B6 B5 B4 B3 B2", 5, (6, 5, 6), 0.003393665158371041, "Straße mit 4er-Bombe und Farbbombe (1)"),
    ("GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2 SA SK SD SB SZ S9 S8 S7 S6 S5 S4 S3 S2 RA RK RD RB RZ R9 R8 R7 R6 R5 R4 R3 R2 BA BK BD BB BZ B9 B8 B7 B6 B5 B4 B3 B2", 6, (6, 5, 6), 0.015214661969534131, "Straße mit 4er-Bombe und Farbbombe (2)"),
    ("GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2 SA SK SD SB SZ S9 S8 S7 S6 S5 S4 S3 S2 RA RK RD RB RZ R9 R8 R7 R6 R5 R4 R3 R2 BA BK BD BB BZ B9 B8 B7 B6 B5 B4 B3 B2", 5, (6, 5, 13), 0.0006464124111182935, "Straße mit 4er-Bombe und Farbbombe (3)"),
    ("GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2 SA SK SD SB SZ S9 S8 S7 S6 S5 S4 S3 S2 RA RK RD RB RZ R9 R8 R7 R6 R5 R4 R3 R2 BA BK BD BB BZ B9 B8 B7 B6 B5 B4 B3 B2", 5, (6, 5, 14), 0.0002539477329393296, "Straße mit 4er-Bombe und Farbbombe (4)"),
    # 4er-Bombe
    ("RK GB BB SB RB BZ R2", 5, (7, 4, 10), 0.14285714285714285, "4er-Bombe"),
    # 4er-Bombe mit Farbbombe
    ("SB RZ R9 R8 R7 R6", 5, (7, 4, 11), 0.16666666666666667, "4er-Bombe mit Farbbombe"),
    # Farbbombe
    ("BK BB BZ B9 B8 B7 B2", 5, (7, 5, 10), 0.047619047619047616, "Farbbombe"),
    ("BK BD BB BZ B9 RK RD RB RZ R9 S3 S2", 11, (7, 5, 12), 1.0, "2 Farbbomben in 12 Karten"),
    ("BK BD BB BZ B9 RK RD RB RZ R9 G7 S3 S2", 11, (7, 5, 12), 0.6794871794871795, "2 Farbbomben in 13 Karten"),
    ("RK RD RB RZ R9 BD BB BZ B9 B8 B7 S3 S2", 11, (7, 5, 12), 0.6153846153846154, "2 Farbbomben in 13 Karten (davon ein länger)"),
    # Farbbombe mit längerer Farbbombe
    ("SD RZ R9 R8 R7 R6 R5", 6, (7, 5, 11), 0.14285714285714285, "Farbbombe mit längerer Farbbombe (1)"),
    ("SK RB RZ R9 R8 R7 R6 S2", 7, (7, 5, 11), 0.25, "Farbbombe mit längerer Farbbombe (2)"),
])
def test_prob_of_higher_combi_or_bomb_explicit(cards, k, figure, expected, msg):
    """prob_of_higher_combi_or_bomb() testen (explizit ausgesuchte Fälle)"""
    if k > len(cards.split()):
        with pytest.raises(AssertionError):
            prob_of_higher_combi_or_bomb(parse_cards(cards), k, figure)
    else:
        p_min, p_max = prob_of_higher_combi_or_bomb(parse_cards(cards), k, figure)
        if p_min == p_max:
            assert pytest.approx(expected, abs=1e-15) == p_min, msg
        else:
            assert p_min <= expected <= p_max, msg

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
            "Ph SB RB GZ BZ SZ R9 G9 S9 R8 G8 B4",
            "Ph SB RB GZ BZ SZ R9 G9 S9 R8 G8 B4 Hu",
            "Ph SB RB GZ BZ SZ R9 G9 S9 R8 G8 B4 B2 Ma",
            "Ph SB RB GZ BZ SZ R9 G9 B6 B5 B4 B3 B2 Ma",  # Farbbombe
        ]
        for r in [10]
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
            "SB RZ GZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 S9 B9 G8 B4",
            "Ph SB RZ R9 G9 R8 G8 B4",
            "SB RZ GZ BZ Ph G9 R8 G8 B4",
            "SB RZ GZ BZ SZ R9 Ph R8 G8 B4",
            "Ph SB RZ GZ BZ R9 G9 S9 R8 G8 B4",
            "Ph SB RZ GZ BZ SZ R9 G9 S9 B9 G8 B4",
            "SB RZ GZ BZ SZ R9 G9 S9 B9 R8 G8 S8 B8 B4 B2",
            "Ph SB RB GZ BZ SZ R9 G9 B6 B5 B4 B3 B2 Ma",  # Farbbombe
        ]
        for r in [9]
        for k in [0, 3, 4, 5, 7, 9, 13, 14]
    ],
    # Rastertests für BOMB (Farbbombe)
    *[
        (cards, k, (CombinationType.BOMB, m, r))
        for cards in [
            "GB GZ G9 G8 G7",
            "GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2",
            "GA GK GD GB GZ G9 G8 G7 G6 G5 G4 G3 G2 B2 S2",
            "SK GB GZ G9 G8 G7 RB RZ R9 R8 R7 BB BZ B9 B8 B7 S4 S2",
            "Ph GB GZ G8 G7 G4 B2 S2",
        ]
        for m in [5]
        for r in [10]
        for k in [0, 4, 5, 6, 7]
    ],
])
def test_prob_of_higher_combi_or_bomb_raster(cards, k, combination):
    """prob_of_higher_combi_or_bomb() testen (Rastersuche)"""
    if k > len(cards.split()):
        with pytest.raises(AssertionError):
            prob_of_higher_combi_or_bomb(parse_cards(cards), k, combination)
        return
    matches, hands = possible_hands_hi(parse_cards(cards), k, combination, with_bombs=True)
    p_expected = sum(matches) / len(hands) if hands else 0.0
    msg = f"{stringify_figure(combination)}"
    # print(f'("{cards}", {k}, ({combination[0]}, {combination[1]}, {combination[2]}), {sum(matches)}, {len(hands)}, {p_expected}, "{msg}"),')
    p_actual_min, p_actual_max = prob_of_higher_combi_or_bomb(parse_cards(cards), k, combination)
    if p_actual_min == p_actual_max:
        assert pytest.approx(p_actual_min, abs=1e-15) == p_expected, msg
    else:
        assert p_actual_min - 1e-15 <= p_expected <= p_actual_max + 1e-15, msg
