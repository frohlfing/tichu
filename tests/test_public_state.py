import unittest
from src.lib.cards import *
from src.lib.combinations import *
from src.private_state import PrivateState
from src.public_state import PublicState


class TestPublicState(unittest.TestCase):
    def setUp(self):
        self.pub = PublicState(seed=123)
        self.priv = PrivateState(0)
        
    def test_shuffle_cards(self):
        cards = self.pub._mixed_deck.copy()
        self.pub.shuffle_cards()
        self.assertNotEqual(cards, self.pub._mixed_deck, "die Karten wurden gemischt")

    def test_deal_out(self):
        self.assertEqual("GZ RZ S9 B9 G9 R9 S8 B8", stringify_cards(self.pub.deal_out(2, 8)), "8 Karten für Spieler 2")
        self.assertEqual("SB BB GB RB SZ BZ GZ RZ S9 B9 G9 R9 S8 B8", stringify_cards(self.pub.deal_out(2, 14)), "14 Karten für Spieler 2")

    def test_play(self):
        self.pub._number_of_cards = [3, 2, 1, 0]
        self.pub._number_of_players = 3
        self.pub._start_player_index = 0
        played_cards = other_cards(parse_cards("Ph RK R9 GK GZ BB BD"))
        self.pub._played_cards = played_cards.copy()
        self.pub._wish = 13
        self.pub._gift = 1
        self.pub._winner = 3

        # passen
        self.pub._current_player_index = 2
        self.pub.play(([], FIGURE_PASS))
        self.assertEqual([3, 2, 1, 0], self.pub._number_of_cards)
        self.assertEqual([(2, ([], FIGURE_PASS))], self.pub._history)

        # Karten legen
        self.pub._current_player_index = 0
        combi1 = parse_cards("RK"), (SINGLE, 1, 13)
        self.pub.play(combi1)
        played_cards.append((13, 1))
        self.assertEqual(played_cards, self.pub._played_cards)
        self.assertEqual([2, 2, 1, 0], self.pub._number_of_cards)
        self.assertEqual(-13, self.pub._wish)
        self.assertEqual([(2, ([], FIGURE_PASS)), (0, combi1)], self.pub._history)
        self.assertEqual(0, self.pub._trick_player_index)
        self.assertEqual(combi1[1], self.pub._trick_figure)
        self.assertEqual(10, self.pub._trick_points)

        # Phönix als Einzelkarte ausspielen
        self.pub._current_player_index = 1
        combi2 = parse_cards("Ph"), FIGURE_PHO
        self.pub.play(combi2)
        played_cards.append((16, 0))
        self.assertEqual(played_cards, self.pub._played_cards)
        self.assertEqual([2, 1, 1, 0], self.pub._number_of_cards)
        self.assertEqual([(2, ([], FIGURE_PASS)), (0, combi1), (1, combi2)], self.pub._history)
        self.assertEqual(1, self.pub._trick_player_index)
        self.assertEqual(combi1[1], self.pub._trick_figure)
        self.assertEqual(-15, self.pub._trick_points)
        self.assertEqual(3, self.pub._number_of_players)

    def test_play_done(self):
        self.pub._number_of_cards = [1, 1, 1, 1]
        self.pub._number_of_players = 4
        self.pub._start_player_index = 0
        played_cards = other_cards(parse_cards("Ph RK R9 G9"))
        self.pub._played_cards = played_cards.copy()
        self.pub._wish = -13
        self.pub._gift = 1

        # 1. Spieler wird fertig
        self.pub._current_player_index = 3
        self.pub.play((parse_cards("Ph"), FIGURE_PHO))
        self.assertEqual(FIGURE_MAH, self.pub._trick_figure)  # Anspiel mit Phönix == Anspiel mit Mahjong
        self.assertEqual(-25, self.pub._trick_points)
        self.assertEqual([1, 1, 1, 0], self.pub._number_of_cards)
        self.assertEqual(3, self.pub._number_of_players)
        self.assertEqual(3, self.pub._winner)
        self.assertEqual(-1, self.pub._loser)
        self.assertFalse(self.pub._is_done)
        self.assertFalse(self.pub._double_win)

        # 2. Spieler wird fertig
        self.pub._current_player_index = 2
        self.pub.play((parse_cards("R9"), (1, 1, 9)))
        self.assertEqual([1, 1, 0, 0], self.pub._number_of_cards)
        self.assertEqual(2, self.pub._number_of_players)
        self.assertEqual(3, self.pub._winner)
        self.assertEqual(-1, self.pub._loser)
        self.assertFalse(self.pub._is_done)
        self.assertFalse(self.pub._double_win)

        # 3. Spieler wird fertig
        self.pub._current_player_index = 1
        self.pub.play((parse_cards("RK"), (1, 1, 13)))
        self.assertEqual([1, 0, 0, 0], self.pub._number_of_cards)
        self.assertEqual(1, self.pub._number_of_players)
        self.assertEqual(3, self.pub._winner)
        self.assertEqual(0, self.pub._loser)
        self.assertTrue(self.pub._is_done)
        self.assertFalse(self.pub._double_win)

    def test_play_double_win(self):
        self.pub._number_of_cards = [1, 1, 1, 0]
        self.pub._number_of_players = 3
        self.pub._start_player_index = 0
        played_cards = other_cards(parse_cards("RK R9 G9"))
        self.pub._played_cards = played_cards.copy()
        self.pub._wish = -13
        self.pub._gift = 1
        self.pub._winner = 3

        # 2. Spieler wird fertig
        self.pub._current_player_index = 1
        self.pub.play((parse_cards("RK"), (1, 1, 13)))
        self.assertEqual([1, 0, 1, 0], self.pub._number_of_cards)
        self.assertEqual(2, self.pub._number_of_players)
        self.assertEqual(3, self.pub._winner)
        self.assertEqual(-1, self.pub._loser)
        self.assertTrue(self.pub._is_done)
        self.assertTrue(self.pub._double_win)

    def test_clear_trick(self):
        self.pub._current_player_index = 0
        self.pub._trick_player_index = 0
        self.pub._trick_figure = SINGLE, 1, 10
        self.pub._trick_counter = 5
        self.pub._is_done = False
        self.pub._double_win = False
        self.pub._number_of_players = 3
        self.pub._announcements = [0, 0, 0, 1]
        self.pub._trick_points = 10
        unplayed_cards = parse_cards("RK GZ G5")  # 25 Punkte
        self.pub._played_cards = other_cards(unplayed_cards)  # 75 Punkte (inklusiv aktuellen Stich)
        self.pub._points = [5, 10, 20, 30]  # 65 Punkte (ohne aktuellen Stich, da noch nicht einkassiert)
        self.pub.clear_trick()
        self.assertEqual([15, 10, 20, 30], self.pub._points)
        self.assertEqual([0, 0], self.pub._score)
        self.assertEqual(-1, self.pub._gift)
        self.assertEqual(-1, self.pub._trick_player_index)
        self.assertEqual((0, 0, 0), self.pub._trick_figure)
        self.assertEqual(0, self.pub._trick_points)
        self.assertEqual(6, self.pub._trick_counter)

    def test_clear_trick_gift(self):
        self.pub._current_player_index = 0
        self.pub._trick_player_index = 0
        self.pub._trick_figure = FIGURE_DRA
        self.pub._trick_counter = 5
        self.pub._is_done = False
        self.pub._double_win = False
        self.pub._number_of_players = 3
        self.pub._announcements = [0, 0, 0, 1]
        self.pub._trick_points = 35
        unplayed_cards = parse_cards("RK GZ G5")  # 25 Punkte
        self.pub._played_cards = other_cards(unplayed_cards)  # 75 Punkte (inklusiv aktuellen Stich)
        self.pub._points = [5, 10, 10, 15]  # 65 Punkte (ohne aktuellen Stich, da noch nicht einkassiert)
        self.pub.clear_trick(opponent=1)
        self.assertEqual([5, 45, 10, 15], self.pub._points)
        self.assertEqual([0, 0], self.pub._score)
        self.assertEqual(1, self.pub._gift)
        self.assertEqual(-1, self.pub._trick_player_index)
        self.assertEqual((0, 0, 0), self.pub._trick_figure)
        self.assertEqual(0, self.pub._trick_points)
        self.assertEqual(6, self.pub._trick_counter)

    def test_clear_trick_done(self):
        self.pub._current_player_index = 0
        self.pub._trick_player_index = 0
        self.pub._trick_figure = SINGLE, 1, 10
        self.pub._trick_counter = 5
        self.pub._is_done = True
        self.pub._double_win = False
        self.pub._number_of_players = 1
        self.pub._winner = 3
        self.pub._loser = 2
        self.pub._announcements = [1, 0, 0, 1]
        self.pub._trick_points = 10
        unplayed_cards = parse_cards("RK GZ G5")  # 25 Punkte
        self.pub._played_cards = other_cards(unplayed_cards)  # 75 Punkte (inklusiv aktuellen Stich)
        self.pub._points = [5, 10, 20, 30]  # 65 Punkte (ohne aktuellen Stich, da noch nicht einkassiert)
        self.pub.clear_trick()
        self.assertEqual([-85, 10, 0, 175], self.pub._points)
        self.assertEqual([-85, 185], self.pub._score)
        self.assertEqual(-1, self.pub._gift)

    def test_clear_trick_double_win(self):
        self.pub._current_player_index = 0
        self.pub._trick_player_index = 0
        self.pub._trick_figure = SINGLE, 1, 10
        self.pub._trick_counter = 5
        self.pub._is_done = True
        self.pub._double_win = True
        self.pub._number_of_players = 2
        self.pub._winner = 3
        self.pub._announcements = [0, 0, 0, 1]
        self.pub._trick_points = 10
        unplayed_cards = parse_cards("RK GZ G5")  # 25 Punkte
        self.pub._played_cards = other_cards(unplayed_cards)  # 75 Punkte (inklusiv aktuellen Stich)
        self.pub._points = [5, 10, 20, 30]  # 65 Punkte (ohne aktuellen Stich, da noch nicht einkassiert)
        self.pub.clear_trick()
        self.assertEqual([0, 0, 0, 300], self.pub._points)
        self.assertEqual([0, 300], self.pub._score)
        self.assertEqual(-1, self.pub._gift)

    def test_step(self):
        # Hund liegt
        self.pub._trick_figure = FIGURE_DOG
        self.pub._trick_player_index = 0
        self.pub._current_player_index = 0
        self.pub.step()
        self.assertEqual(2, self.pub._current_player_index)
        self.pub._trick_player_index = 3
        self.pub._current_player_index = 3
        self.pub.step()
        self.assertEqual(1, self.pub._current_player_index)

        # kein Hund
        self.pub._trick_figure = FIGURE_PASS
        self.pub._current_player_index = 0
        self.pub.step()
        self.assertEqual(1, self.pub._current_player_index)
        self.pub._current_player_index = 3
        self.pub.step()
        self.assertEqual(0, self.pub._current_player_index)

    def test_points_per_team(self):
        self.pub._points = [5, 10, 20, 40]
        self.assertEqual([25, 50], self.pub.points_per_team)


if __name__ == "__main__":
    unittest.main()
