import logging
from tichu.tichu import *
from unittest import TestCase
from web.database import init_flask_db

logger = logging.getLogger(__name__)
db = init_flask_db()
ws = WebSocket()


class TestTichu(TestCase):
    def setUp(self):
        self.tichu = Tichu(logger, db, ws, seed=123)

    def test_shuffle_cards(self):
        cards = self.tichu._mixed_deck.copy()
        self.tichu._shuffle_cards()
        self.assertNotEqual(cards, self.tichu._mixed_deck, 'die Karten wurden gemischt')

    def test_deal_out(self):
        self.assertEqual('GZ RZ S9 B9 G9 R9 S8 B8', stringify_cards(self.tichu.deal_out(2, 8)), '8 Karten für Spieler 2')
        self.assertEqual('SB BB GB RB SZ BZ GZ RZ S9 B9 G9 R9 S8 B8', stringify_cards(self.tichu.deal_out(2, 14)), '14 Karten für Spieler 2')

    def test_play(self):
        self.tichu._number_of_cards = [3, 2, 1, 0]
        self.tichu._number_of_players = 3
        self.tichu._start_player = 0
        played_cards = other_cards(parse_cards('Ph RK R9 GK GZ BB BD'))
        self.tichu._played_cards = played_cards.copy()
        self.tichu._wish = 13
        self.tichu._gift = 1
        self.tichu._winner = 3

        # passen
        self.tichu._current_player = 2
        self.tichu.play(([], FIGURE_PASS))
        self.assertEqual([3, 2, 1, 0], self.tichu._number_of_cards)
        self.assertEqual([(2, ([], FIGURE_PASS))], self.tichu._history)

        # Karten legen
        self.tichu._current_player = 0
        combi1 = parse_cards('RK'), (SINGLE, 1, 13)
        self.tichu.play(combi1)
        played_cards.append((13, 1))
        self.assertEqual(played_cards, self.tichu._played_cards)
        self.assertEqual([2, 2, 1, 0], self.tichu._number_of_cards)
        self.assertEqual(-13, self.tichu._wish)
        self.assertEqual([(2, ([], FIGURE_PASS)), (0, combi1)], self.tichu._history)
        self.assertEqual(0, self.tichu._trick_player)
        self.assertEqual(combi1[1], self.tichu._trick_figure)
        self.assertEqual(10, self.tichu._trick_points)

        # Phönix als Einzelkarte ausspielen
        self.tichu._current_player = 1
        combi2 = parse_cards('Ph'), FIGURE_PHO
        self.tichu.play(combi2)
        played_cards.append((16, 0))
        self.assertEqual(played_cards, self.tichu._played_cards)
        self.assertEqual([2, 1, 1, 0], self.tichu._number_of_cards)
        self.assertEqual([(2, ([], FIGURE_PASS)), (0, combi1), (1, combi2)], self.tichu._history)
        self.assertEqual(1, self.tichu._trick_player)
        self.assertEqual(combi1[1], self.tichu._trick_figure)
        self.assertEqual(-15, self.tichu._trick_points)
        self.assertEqual(3, self.tichu._number_of_players)

    def test_play_done(self):
        self.tichu._number_of_cards = [1, 1, 1, 1]
        self.tichu._number_of_players = 4
        self.tichu._start_player = 0
        played_cards = other_cards(parse_cards('Ph RK R9 G9'))
        self.tichu._played_cards = played_cards.copy()
        self.tichu._wish = -13
        self.tichu._gift = 1

        # 1. Spieler wird fertig
        self.tichu._current_player = 3
        self.tichu.play((parse_cards('Ph'), FIGURE_PHO))
        self.assertEqual(FIGURE_MAH, self.tichu._trick_figure)  # Anspiel mit Phönix == Anspiel mit Mahjong
        self.assertEqual(-25, self.tichu._trick_points)
        self.assertEqual([1, 1, 1, 0], self.tichu._number_of_cards)
        self.assertEqual(3, self.tichu._number_of_players)
        self.assertEqual(3, self.tichu._winner)
        self.assertEqual(-1, self.tichu._loser)
        self.assertFalse(self.tichu._is_done)
        self.assertFalse(self.tichu._double_win)

        # 2. Spieler wird fertig
        self.tichu._current_player = 2
        self.tichu.play((parse_cards('R9'), (1, 1, 9)))
        self.assertEqual([1, 1, 0, 0], self.tichu._number_of_cards)
        self.assertEqual(2, self.tichu._number_of_players)
        self.assertEqual(3, self.tichu._winner)
        self.assertEqual(-1, self.tichu._loser)
        self.assertFalse(self.tichu._is_done)
        self.assertFalse(self.tichu._double_win)

        # 3. Spieler wird fertig
        self.tichu._current_player = 1
        self.tichu.play((parse_cards('RK'), (1, 1, 13)))
        self.assertEqual([1, 0, 0, 0], self.tichu._number_of_cards)
        self.assertEqual(1, self.tichu._number_of_players)
        self.assertEqual(3, self.tichu._winner)
        self.assertEqual(0, self.tichu._loser)
        self.assertTrue(self.tichu._is_done)
        self.assertFalse(self.tichu._double_win)

    def test_play_double_win(self):
        self.tichu._number_of_cards = [1, 1, 1, 0]
        self.tichu._number_of_players = 3
        self.tichu._start_player = 0
        played_cards = other_cards(parse_cards('RK R9 G9'))
        self.tichu._played_cards = played_cards.copy()
        self.tichu._wish = -13
        self.tichu._gift = 1
        self.tichu._winner = 3

        # 2. Spieler wird fertig
        self.tichu._current_player = 1
        self.tichu.play((parse_cards('RK'), (1, 1, 13)))
        self.assertEqual([1, 0, 1, 0], self.tichu._number_of_cards)
        self.assertEqual(2, self.tichu._number_of_players)
        self.assertEqual(3, self.tichu._winner)
        self.assertEqual(-1, self.tichu._loser)
        self.assertTrue(self.tichu._is_done)
        self.assertTrue(self.tichu._double_win)

    def test_clear_trick(self):
        self.tichu._current_player = 0
        self.tichu._trick_player = 0
        self.tichu._trick_figure = SINGLE, 1, 10
        self.tichu._trick_counter = 5
        self.tichu._is_done = False
        self.tichu._double_win = False
        self.tichu._number_of_players = 3
        self.tichu._announcements = [0, 0, 0, 1]
        self.tichu._trick_points = 10
        unplayed_cards = parse_cards('RK GZ G5')  # 25 Punkte
        self.tichu._played_cards = other_cards(unplayed_cards)  # 75 Punkte (inklusiv aktuellen Stich)
        self.tichu._points = [5, 10, 20, 30]  # 65 Punkte (ohne aktuellen Stich, da noch nicht einkassiert)
        self.tichu.clear_trick()
        self.assertEqual([15, 10, 20, 30], self.tichu._points)
        self.assertEqual([0, 0], self.tichu._score)
        self.assertEqual(-1, self.tichu._gift)
        self.assertEqual(-1, self.tichu._trick_player)
        self.assertEqual((0, 0, 0), self.tichu._trick_figure)
        self.assertEqual(0, self.tichu._trick_points)
        self.assertEqual(6, self.tichu._trick_counter)

    def test_clear_trick_gift(self):
        self.tichu._current_player = 0
        self.tichu._trick_player = 0
        self.tichu._trick_figure = FIGURE_DRA
        self.tichu._trick_counter = 5
        self.tichu._is_done = False
        self.tichu._double_win = False
        self.tichu._number_of_players = 3
        self.tichu._announcements = [0, 0, 0, 1]
        self.tichu._trick_points = 35
        unplayed_cards = parse_cards('RK GZ G5')  # 25 Punkte
        self.tichu._played_cards = other_cards(unplayed_cards)  # 75 Punkte (inklusiv aktuellen Stich)
        self.tichu._points = [5, 10, 10, 15]  # 65 Punkte (ohne aktuellen Stich, da noch nicht einkassiert)
        self.tichu.clear_trick(opponent=1)
        self.assertEqual([5, 45, 10, 15], self.tichu._points)
        self.assertEqual([0, 0], self.tichu._score)
        self.assertEqual(1, self.tichu._gift)
        self.assertEqual(-1, self.tichu._trick_player)
        self.assertEqual((0, 0, 0), self.tichu._trick_figure)
        self.assertEqual(0, self.tichu._trick_points)
        self.assertEqual(6, self.tichu._trick_counter)

    def test_clear_trick_done(self):
        self.tichu._current_player = 0
        self.tichu._trick_player = 0
        self.tichu._trick_figure = SINGLE, 1, 10
        self.tichu._trick_counter = 5
        self.tichu._is_done = True
        self.tichu._double_win = False
        self.tichu._number_of_players = 1
        self.tichu._winner = 3
        self.tichu._loser = 2
        self.tichu._announcements = [1, 0, 0, 1]
        self.tichu._trick_points = 10
        unplayed_cards = parse_cards('RK GZ G5')  # 25 Punkte
        self.tichu._played_cards = other_cards(unplayed_cards)  # 75 Punkte (inklusiv aktuellen Stich)
        self.tichu._points = [5, 10, 20, 30]  # 65 Punkte (ohne aktuellen Stich, da noch nicht einkassiert)
        self.tichu.clear_trick()
        self.assertEqual([-85, 10, 0, 175], self.tichu._points)
        self.assertEqual([-85, 185], self.tichu._score)
        self.assertEqual(-1, self.tichu._gift)

    def test_clear_trick_double_win(self):
        self.tichu._current_player = 0
        self.tichu._trick_player = 0
        self.tichu._trick_figure = SINGLE, 1, 10
        self.tichu._trick_counter = 5
        self.tichu._is_done = True
        self.tichu._double_win = True
        self.tichu._number_of_players = 2
        self.tichu._winner = 3
        self.tichu._announcements = [0, 0, 0, 1]
        self.tichu._trick_points = 10
        unplayed_cards = parse_cards('RK GZ G5')  # 25 Punkte
        self.tichu._played_cards = other_cards(unplayed_cards)  # 75 Punkte (inklusiv aktuellen Stich)
        self.tichu._points = [5, 10, 20, 30]  # 65 Punkte (ohne aktuellen Stich, da noch nicht einkassiert)
        self.tichu.clear_trick()
        self.assertEqual([0, 0, 0, 300], self.tichu._points)
        self.assertEqual([0, 300], self.tichu._score)
        self.assertEqual(-1, self.tichu._gift)

    def test_step(self):
        # Hund liegt
        self.tichu._trick_figure = FIGURE_DOG
        self.tichu._trick_player = 0
        self.tichu._current_player = 0
        self.tichu.step()
        self.assertEqual(2, self.tichu._current_player)
        self.tichu._trick_player = 3
        self.tichu._current_player = 3
        self.tichu.step()
        self.assertEqual(1, self.tichu._current_player)

        # kein Hund
        self.tichu._trick_figure = FIGURE_PASS
        self.tichu._current_player = 0
        self.tichu.step()
        self.assertEqual(1, self.tichu._current_player)
        self.tichu._current_player = 3
        self.tichu.step()
        self.assertEqual(0, self.tichu._current_player)

    def test_points_per_team(self):
        self.tichu._points = [5, 10, 20, 40]
        self.assertEqual([25, 50], self.tichu.points_per_team)
