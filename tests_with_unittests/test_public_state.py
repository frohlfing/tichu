import unittest
from src.lib.cards import *
from src.lib.combinations import *
from src.private_state import PrivateState
from src.public_state import PublicState


class TestPublicState(unittest.TestCase):
    def setUp(self):
        self.pub = PublicState()
        self.priv = PrivateState(player_index=0)

    def test_deal_out(self):
        self.assertEqual("GZ RZ S9 B9 G9 R9 S8 B8", stringify_cards(self.pub.deal_out(2, 8)), "8 Karten für Spieler 2")
        self.assertEqual("SB BB GB RB SZ BZ GZ RZ S9 B9 G9 R9 S8 B8", stringify_cards(self.pub.deal_out(2, 14)), "14 Karten für Spieler 2")

    def test_play(self):
        self.pub.count_hand_cards = [3, 2, 1, 0]
        self.pub.start_player_index = 0
        played_cards = other_cards(parse_cards("Ph RK R9 GK GZ BB BD"))
        self.pub.played_cards = played_cards.copy()
        self.pub.wish_value = 13
        self.pub.dragon_recipient = 1
        self.pub.winner_index = 3

        # passen
        self.pub.current_turn_index = 2
        self.pub.play(([], FIGURE_PASS))
        self.assertEqual([3, 2, 1, 0], self.pub.count_hand_cards)
        self.assertEqual([(2, ([], FIGURE_PASS))], self.pub.tricks)

        # Karten legen
        self.pub.current_turn_index = 0
        combi1 = parse_cards("RK"), (CombinationType.SINGLE, 1, 13)
        self.pub.play(combi1)
        played_cards.append((13, 1))
        self.assertEqual(played_cards, self.pub.played_cards)
        self.assertEqual([2, 2, 1, 0], self.pub.count_hand_cards)
        self.assertEqual(-13, self.pub.wish_value)
        self.assertEqual([(2, ([], FIGURE_PASS)), (0, combi1)], self.pub.tricks)
        self.assertEqual(0, self.pub.trick_owner_index)
        self.assertEqual(combi1[1], self.pub.trick_combination)
        self.assertEqual(10, self.pub.trick_points)

        # Phönix als Einzelkarte ausspielen
        self.pub.current_turn_index = 1
        combi2 = parse_cards("Ph"), FIGURE_PHO
        self.pub.play(combi2)
        played_cards.append((16, 0))
        self.assertEqual(played_cards, self.pub.played_cards)
        self.assertEqual([2, 1, 1, 0], self.pub.count_hand_cards)
        self.assertEqual([(2, ([], FIGURE_PASS)), (0, combi1), (1, combi2)], self.pub.tricks)
        self.assertEqual(1, self.pub.trick_owner_index)
        self.assertEqual(combi1[1], self.pub.trick_combination)
        self.assertEqual(-15, self.pub.trick_points)
        self.assertEqual(3, self.pub.count_active_players)

    def test_play_done(self):
        self.pub.count_hand_cards = [1, 1, 1, 1]
        self.pub.start_player_index = 0
        played_cards = other_cards(parse_cards("Ph RK R9 G9"))
        self.pub.played_cards = played_cards.copy()
        self.pub.wish_value = -13
        self.pub.dragon_recipient = 1

        # 1. Spieler wird fertig
        self.pub.current_turn_index = 3
        self.pub.play((parse_cards("Ph"), FIGURE_PHO))
        self.assertEqual(FIGURE_MAH, self.pub.trick_combination)  # Anspiel mit Phönix == Anspiel mit Mahjong
        self.assertEqual(-25, self.pub.trick_points)
        self.assertEqual([1, 1, 1, 0], self.pub.count_hand_cards)
        self.assertEqual(3, self.pub.count_active_players)
        self.assertEqual(3, self.pub.winner_index)
        self.assertEqual(-1, self.pub.loser_index)
        self.assertFalse(self.pub.is_round_over)
        self.assertFalse(self.pub.is_double_victory)

        # 2. Spieler wird fertig
        self.pub.current_turn_index = 2
        self.pub.play((parse_cards("R9"), (1, 1, 9)))
        self.assertEqual([1, 1, 0, 0], self.pub.count_hand_cards)
        self.assertEqual(2, self.pub.count_active_players)
        self.assertEqual(3, self.pub.winner_index)
        self.assertEqual(-1, self.pub.loser_index)
        self.assertFalse(self.pub.is_round_over)
        self.assertFalse(self.pub.is_double_victory)

        # 3. Spieler wird fertig
        self.pub.current_turn_index = 1
        self.pub.play((parse_cards("RK"), (1, 1, 13)))
        self.assertEqual([1, 0, 0, 0], self.pub.count_hand_cards)
        self.assertEqual(1, self.pub.count_active_players)
        self.assertEqual(3, self.pub.winner_index)
        self.assertEqual(0, self.pub.loser_index)
        self.assertTrue(self.pub.is_round_over)
        self.assertFalse(self.pub.is_double_victory)

    def test_play_double_win(self):
        self.pub.count_hand_cards = [1, 1, 1, 0]
        self.pub.start_player_index = 0
        played_cards = other_cards(parse_cards("RK R9 G9"))
        self.pub.played_cards = played_cards.copy()
        self.pub.wish_value = -13
        self.pub.dragon_recipient = 1
        self.pub.winner_index = 3

        # 2. Spieler wird fertig
        self.pub.current_turn_index = 1
        self.pub.play((parse_cards("RK"), (1, 1, 13)))
        self.assertEqual([1, 0, 1, 0], self.pub.count_hand_cards)
        self.assertEqual(2, self.pub.count_active_players)
        self.assertEqual(3, self.pub.winner_index)
        self.assertEqual(-1, self.pub.loser_index)
        self.assertTrue(self.pub.is_round_over)
        self.assertTrue(self.pub.is_double_victory)

    def test_clear_trick(self):
        self.pub.current_turn_index = 0
        self.pub.trick_owner_index = 0
        self.pub.trick_combination = CombinationType.SINGLE, 1, 10
        self.pub._trick_counter = 5
        self.pub.is_round_over = False
        self.pub.is_double_victory = False
        self.pub._announcements = [0, 0, 0, 1]
        self.pub.trick_points = 10
        unplayed_cards = parse_cards("RK GZ G5")  # 25 Punkte
        self.pub.played_cards = other_cards(unplayed_cards)  # 75 Punkte (inklusiv aktuellen Stich)
        self.pub._points = [5, 10, 20, 30]  # 65 Punkte (ohne aktuellen Stich, da noch nicht einkassiert)
        self.pub.clear_trick()
        self.assertEqual([15, 10, 20, 30], self.pub._points)
        self.assertEqual([0, 0], self.pub.game_score)
        self.assertEqual(-1, self.pub.dragon_recipient)
        self.assertEqual(-1, self.pub.trick_owner_index)
        self.assertEqual((0, 0, 0), self.pub.trick_combination)
        self.assertEqual(0, self.pub.trick_points)
        self.assertEqual(6, self.pub._trick_counter)

    def test_clear_trick_gift(self):
        self.pub.current_turn_index = 0
        self.pub.trick_owner_index = 0
        self.pub.trick_combination = FIGURE_DRA
        self.pub._trick_counter = 5
        self.pub.is_round_over = False
        self.pub.is_double_victory = False
        self.pub._announcements = [0, 0, 0, 1]
        self.pub.trick_points = 35
        unplayed_cards = parse_cards("RK GZ G5")  # 25 Punkte
        self.pub.played_cards = other_cards(unplayed_cards)  # 75 Punkte (inklusiv aktuellen Stich)
        self.pub._points = [5, 10, 10, 15]  # 65 Punkte (ohne aktuellen Stich, da noch nicht einkassiert)
        self.pub.clear_trick(opponent=1)
        self.assertEqual([5, 45, 10, 15], self.pub._points)
        self.assertEqual([0, 0], self.pub.game_score)
        self.assertEqual(1, self.pub.dragon_recipient)
        self.assertEqual(-1, self.pub.trick_owner_index)
        self.assertEqual((0, 0, 0), self.pub.trick_combination)
        self.assertEqual(0, self.pub.trick_points)
        self.assertEqual(6, self.pub._trick_counter)

    def test_clear_trick_done(self):
        self.pub.current_turn_index = 0
        self.pub.trick_owner_index = 0
        self.pub.trick_combination = CombinationType.SINGLE, 1, 10
        self.pub._trick_counter = 5
        self.pub.is_round_over = True
        self.pub.is_double_victory = False
        self.pub.winner_index = 3
        self.pub.loser_index = 2
        self.pub._announcements = [1, 0, 0, 1]
        self.pub.trick_points = 10
        unplayed_cards = parse_cards("RK GZ G5")  # 25 Punkte
        self.pub.played_cards = other_cards(unplayed_cards)  # 75 Punkte (inklusiv aktuellen Stich)
        self.pub._points = [5, 10, 20, 30]  # 65 Punkte (ohne aktuellen Stich, da noch nicht einkassiert)
        self.pub.clear_trick()
        self.assertEqual([-85, 10, 0, 175], self.pub._points)
        self.assertEqual([-85, 185], self.pub.game_score)
        self.assertEqual(-1, self.pub.dragon_recipient)

    def test_clear_trick_double_win(self):
        self.pub.current_turn_index = 0
        self.pub.trick_owner_index = 0
        self.pub.trick_combination = CombinationType.SINGLE, 1, 10
        self.pub._trick_counter = 5
        self.pub.is_round_over = True
        self.pub.is_double_victory = True
        self.pub.winner_index = 3
        self.pub._announcements = [0, 0, 0, 1]
        self.pub.trick_points = 10
        unplayed_cards = parse_cards("RK GZ G5")  # 25 Punkte
        self.pub.played_cards = other_cards(unplayed_cards)  # 75 Punkte (inklusiv aktuellen Stich)
        self.pub._points = [5, 10, 20, 30]  # 65 Punkte (ohne aktuellen Stich, da noch nicht einkassiert)
        self.pub.clear_trick()
        self.assertEqual([0, 0, 0, 300], self.pub._points)
        self.assertEqual([0, 300], self.pub.game_score)
        self.assertEqual(-1, self.pub.dragon_recipient)

    def test_step(self):
        # Hund liegt
        self.pub.trick_combination = FIGURE_DOG
        self.pub.trick_owner_index = 0
        self.pub.current_turn_index = 0
        self.pub.turn()
        self.assertEqual(2, self.pub.current_turn_index)
        self.pub.trick_owner_index = 3
        self.pub.current_turn_index = 3
        self.pub.turn()
        self.assertEqual(1, self.pub.current_turn_index)

        # kein Hund
        self.pub.trick_combination = FIGURE_PASS
        self.pub.current_turn_index = 0
        self.pub.turn()
        self.assertEqual(1, self.pub.current_turn_index)
        self.pub.current_turn_index = 3
        self.pub.turn()
        self.assertEqual(0, self.pub.current_turn_index)

if __name__ == "__main__":
    unittest.main()
