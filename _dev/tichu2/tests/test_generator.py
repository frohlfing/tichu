from tichu.brettspielwelt.generator import generator
from tichu.cards import cardlabels
from tichu.combinations import figures_index, figurelabels, FULLHOUSE, SINGLE
from unittest import TestCase


def cards_to_str(vector):
    return ' '.join([cardlabels[i + 2] for i, v in reversed(list(enumerate(vector))) if v])


def specify_cards_to_str(vector):
    cardlabels_ = (
        'Hu',  # Hund
        'Ma',  # MahJong
        'Dr',  # Drache
        'Ph',  # Phönix
    )
    return ' '.join([cardlabels_[i] for i, v in reversed(list(enumerate(vector))) if v])


def trick_to_str(t_, n_, v_):
    return figurelabels[figures_index[(
        t_.argmax() + 1 if t_.sum() == 1 else 0,
        n_.argmax() + 1 if n_.sum() == 1 else 0,
        v_.argmax() + 1 if v_.sum() == 1 else 0
    )]]


# Beispiel-Datensatz
# Datei: 202201/2358807.tch
# lap_id: 21975358
class TestGenerator(TestCase):
    def setUp(self):
        pass

    # Anzahl Datensätze testen
    def test_length(self):
        n = len(list(generator(section='all', part='all', endless=False, test_lap_id=21975358, test_player=0, validate=True)))
        assert n == 18, n
        n = len(list(generator(section='all', part='all', endless=False, test_lap_id=21975358, test_player=1, validate=True)))
        assert n == 16, n
        n = len(list(generator(section='all', part='all', endless=False, test_lap_id=21975358, test_player=2, validate=True)))
        assert n == 9, n
        n = len(list(generator(section='all', part='all', endless=False, test_lap_id=21975358, test_player=3, validate=True)))
        assert n == 19, n

    # Endlosschleife testen
    def test_endless(self):
        c = 0
        xa = None
        for _, x, y in generator(section='all', part='all', test_lap_id=21975358, test_player=0, validate=True):
            if c == 0:
                xa = cards_to_str(x[0].reshape(52))
            c += 1
            if c > 18:
                xb = cards_to_str(x[0].reshape(52))
                assert xa == xb, 'Fehler in der Endlosschleife'
                break

    # Ausgabe testen
    def test_prelude(self):
        gen = generator(section='all', part='prelude', test_lap_id=21975358, test_player=0, endless=False, validate=True)

        # Auftakt
        for n in (8, 14):
            id_, x, y = next(gen)
            assert id_, 21975358
            x0a, x0b, x4b, x4c, x4d = x
            p0 = y
            assert x0a.shape == (13, 4)
            assert x0b.shape == (4,)
            if n == 8:
                assert cards_to_str(x0a.reshape(52)) == 'RK BB RB S9 S7 B7 S6 R3', cards_to_str(x0a.reshape(52))
                assert specify_cards_to_str(x0b) == '', specify_cards_to_str(x0b)
            else:
                assert cards_to_str(x0a.reshape(52)) == 'RK RD BB RB S9 B9 S7 B7 G7 S6 G6 B3 R3', cards_to_str(x0a.reshape(52))
                assert specify_cards_to_str(x0b) == 'Dr', specify_cards_to_str(x0b)
            assert x4b.sum() == 0 and x4c.sum() == 0 and x4d.sum() == 0
            assert p0.sum() == 1 and p0.argmax() == 0

        eof = False
        try:
            next(gen)
        except StopIteration:
            eof = True
        assert eof

    def test_tichu(self):
        for player in (0, 2):
            gen = generator(section='all', part='tichu', test_lap_id=21975358, test_player=player, endless=False, validate=True)

            # Hauptspiel
            if player == 0:
                for c in range(2):
                    id_, x, y = next(gen)
                    assert id_, 21975358
                    x0a, x0b, x1a, x1b, x1c, x2, x3a, x3b, x4b, x4c, x4d, x5, x6a, x6b, x6c, x6d, x6e, x7, x8 = x
                    p0 = y
                    assert p0.sum() < 2
                    assert x2[0] == 1

                    # Tichu-Ansage
                    assert x4b.shape == x4c.shape == x4d.shape == (2,)
                    assert x4b.sum() == 0 and x4d.sum() == 0, (x4b, x4d)
                    assert x4c.sum() == 1 and x4c.argmax() == 0, x4c

                    # Target
                    assert p0.shape == (2,)
                    assert p0.sum() == 1, p0
                    assert p0.argmax() == 0, p0.argmax()

                eof = False
                try:
                    next(gen)
                except StopIteration:
                    eof = True
                assert eof

            if player == 1:
                id_, x, y = next(gen)
                assert id_, 21975358
                x0a, x0b, x1a, x1b, x1c, x2, x3a, x3b, x4b, x4c, x4d, x5, x6a, x6b, x6c, x6d, x6e, x7, x8 = x
                p0 = y
                assert p0.sum() < 2
                assert x2[0] == 1

                # Tichu-Ansage
                assert x4b.shape == x4c.shape == x4d.shape == (2,)
                assert x4b.sum() == 0 and x4c.sum() == 0 and x4d.sum() == 0, (x4b, x4c, x4d)

                # Target
                assert p0.shape == (2,)
                assert p0.sum() == 1, p0
                assert p0.argmax() == 1, p0.argmax()

                eof = False
                try:
                    next(gen)
                except StopIteration:
                    eof = True
                assert eof

    def test_schupf1(self):
        gen = generator(section='all', part='schupf1', test_lap_id=21975358, test_player=0, endless=False, validate=True)
        # Auftakt
        id_, x, y = next(gen)
        assert id_, 21975358
        x0a, x0b, x4a, x4b, x4c, x4d = x
        p4a = y
        assert x0a.shape == (13, 4)
        assert x0b.shape == (4,)
        assert cards_to_str(x0a.reshape(52)) == 'RK RD BB RB S9 B9 S7 B7 G7 S6 G6 B3 R3', cards_to_str(x0a.reshape(52))
        assert specify_cards_to_str(x0b) == 'Dr', specify_cards_to_str(x0b)
        assert x4a.sum() == 0 and x4b.sum() == 0 and x4c.sum() == 0 and x4d.sum() == 0
        assert p4a.sum() == 1
        assert p4a.argmax() == 3

        eof = False
        try:
            next(gen)
        except StopIteration:
            eof = True
        assert eof

    def test_figure_t(self):
        gen = generator(section='all', part='figure_t', test_lap_id=21975358, test_player=0, endless=False, validate=True)

        # Hauptspiel
        for c in range(2):
            id_, x, y = next(gen)
            assert id_, 21975358
            x0a, x0b, x1a, x1b, x1c, x2, x3a, x3b, x4a, x4b, x4c, x4d, x5, x7, x8 = x
            p1a = y
            # print('c', c)
            assert p1a.sum() < 2
            # assert p0.sum() < 2 and p2.sum() < 2 and p3.sum() < 2 and p4a.sum() < 2 and p4b.sum() < 2 and p4b.sum() < 2
            # Handkarten
            if c == 0:
                assert cards_to_str(x0a.reshape(52)) == 'BB RB S9 B9 R9 R2', cards_to_str(x0a.reshape(52))
                assert cards_to_str(x0b) == '', cards_to_str(x0b)
            if c == 1:
                assert cards_to_str(x0a.reshape(52)) == 'R2', cards_to_str(x0a.reshape(52))
                assert cards_to_str(x0b) == '', cards_to_str(x0b)
            else:
                print('Handkarten')
                print('x0a', cards_to_str(x0a.reshape(52)))
                print('x0b', specify_cards_to_str(x0b))

            # Schupf-Kartenwert
            assert x1a.shape == x1b.shape == x1c.shape == (16,)
            assert x1a.argmax() == 2, x1a.argmax()
            assert x1b.argmax() == 14, x1b.argmax()
            assert x1c.argmax() == 2, x1c.argmax()

            # Anzahl Handkarten (normalisiert: 1 == 14 Karten)
            a = x2 * 14
            if c == 0:
                assert a.shape == (4,)
                assert a[0] == 6 and a[1] == 0 and a[2] == 0 and a[3] == 3, a
            elif c == 1:
                assert a[0] == 1 and a[1] == 0 and a[2] == 0 and a[3] == 3, a

            # Ausgespielte Karten
            if c == 0:
                assert cards_to_str(x3a.reshape(52)) == 'SA BA GA RA SK BK GK RK SD BD GD RD SB GB SZ BZ GZ RZ G9 S8 R8 S7 B7 G7 R7 S6 B6 G6 R6 S5 B5 G5 R5 S4 B4 G4 R4 S3 B3 G3 S2 B2 G2', cards_to_str(x3a.reshape(52))
                assert specify_cards_to_str(x3b) == 'Ph Dr Ma Hu', specify_cards_to_str(x3b)
            elif c == 1:
                assert cards_to_str(x3a.reshape(52)) == 'SA BA GA RA SK BK GK RK SD BD GD RD SB BB GB RB SZ BZ GZ RZ S9 B9 G9 R9 S8 R8 S7 B7 G7 R7 S6 B6 G6 R6 S5 B5 G5 R5 S4 B4 G4 R4 S3 B3 G3 S2 B2 G2', cards_to_str(x3a.reshape(52))
                assert specify_cards_to_str(x3b) == 'Ph Dr Ma Hu', specify_cards_to_str(x3b)
            else:
                print('Ausgespielte Karten')
                print('x3a', cards_to_str(x3a.reshape(52)))
                print('x3b', specify_cards_to_str(x3b))

            # Tichu-Ansage
            assert x4a.shape == x4b.shape == x4c.shape == x4d.shape == (2,)
            assert x4a.sum() == 0 and x4b.sum() == 0 and (x4c.sum() == 1 and x4c.argmax() == 0) and x4d.sum() == 0, (x4a, x4b, x4c, x4d)

            # Wunsch
            assert x5.sum() == 1, x5
            assert x5.argmax() == 0, x5.argmax()

            # Bisherige Punkte (normalisiert: 1 == 100 Punkte)
            a = x7 * 100
            if c <= 1:
                assert a[0] == 10 and round(a[1]) == 85 and a[2] == -5 and a[3] == 10, a
            else:
                print('Bisherige Punkte')
                print('a', a)

            # Spieler zuerst fertig
            assert x8.argmax() == 2, x8.argmax()

            # Target

            # Gespielte Kartenkombination (Figure)
            if c == 0:
                assert p1a.sum() == 1, p1a
                assert p1a.argmax() + 1 == FULLHOUSE, p1a.argmax()
            elif c == 1:
                assert p1a.sum() == 1, p1a
                assert p1a.argmax() + 1 == SINGLE, p1a.argmax()
            else:
                print('Gespielte Kartenkombination (Figure)')
                print('p1a', p1a.sum(), p1a.argmax())

        eof = False
        try:
            x, y =next(gen)
        except StopIteration:
            eof = True
        assert eof

    def test_gift(self):
        gen = generator(section='all', part='gift', test_lap_id=21975358, test_player=2, endless=False, validate=True)
        id_, x, y = next(gen)
        assert id_, 21975358
        p3 = y
        assert p3.shape == (2,)
        assert p3.sum() == 1 and p3.argmax() == 1, p3

        eof = False
        try:
            next(gen)
        except StopIteration:
            eof = True
        assert eof

    def test_wish(self):
        gen = generator(section='all', part='wish', test_lap_id=21975358, test_player=2, endless=False, validate=True)

        # Hauptspiel
        id_, x, y = next(gen)
        assert id_, 21975358
        # noinspection PyUnusedLocal
        x0a, x0b, x1a, x1b, x1c, x2, x3a, x3b, x4a, x4b, x4c, x4d, x6a, x6b, x6c, x6d, x6e, x7, x8 = x
        p2 = y
        assert p2.sum() < 2

        # Target
        assert p2.shape == (13,)
        assert p2.sum() == 1 and p2.argmax() == 7, p2

        eof = False
        try:
            next(gen)
        except StopIteration:
            eof = True
        assert eof

    def test_points(self):
        gen = generator(section='all', part='points', test_lap_id=21975358, test_player=0, endless=False, validate=True)

        id_, x, y = next(gen)
        assert id_, 21975358
        # noinspection PyUnusedLocal
        x0a, x0b, x1a, x1b, x1c, x2, x3a, x3b, x4a, x4b, x4c, x4d, x5, x6a, x6b, x6c, x6d, x6e, x7, x8 = x
        v1 = y
        self.assertAlmostEqual(v1 * 400, 30, 6)

        eof = False
        try:
            next(gen)
        except StopIteration:
            eof = True
        assert eof

    def test_bonus(self):
        gen = generator(section='all', part='bonus', test_lap_id=21975358, test_player=0, endless=False, validate=True)

        id_, x, y = next(gen)
        assert id_, 21975358
        # noinspection PyUnusedLocal
        x0a, x0b, x1a, x1b, x1c, x2, x3a, x3b, x4a, x4b, x4c, x4d, x5, x6a, x6b, x6c, x6d, x6e, x7, x8 = x
        v0 = y
        assert v0 == 0

        eof = False
        try:
            next(gen)
        except StopIteration:
            eof = True
        assert eof
