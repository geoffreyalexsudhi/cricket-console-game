"""
Unit tests for Cricket Clash Game Logic Engine.
"""

import unittest
from unittest.mock import patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game_logic import CricketGame


class TestCricketGameLogic(unittest.TestCase):

    def setUp(self):
        self.game = CricketGame(mode="quick")  # 2 overs, 2 wickets

    def test_initial_state(self):
        self.assertEqual(self.game.phase, "toss")
        self.assertEqual(self.game.max_overs, 2)
        self.assertEqual(self.game.max_wickets, 2)
        self.assertEqual(self.game.current_innings, 1)

    @patch('random.randrange')
    def test_toss_user_wins_odd(self, mock_rand):
        # User calls Odd (1), plays 3. Computer plays 2. Sum = 5 (Odd) -> User wins
        mock_rand.return_value = 2
        res = self.game.play_toss(user_call=1, user_number=3)
        self.assertEqual(res["winner"], "user")
        self.assertEqual(res["toss_sum"], 5)
        self.assertEqual(res["sum_parity"], "odd")
        self.assertEqual(self.game.phase, "toss_decision")

    @patch('random.randrange')
    def test_toss_computer_wins_even(self, mock_rand):
        # User calls Odd (1), plays 2. Computer plays 2. Sum = 4 (Even) -> Computer wins
        # mock_rand returns comp_number=2, then k7=1 (comp bats)
        mock_rand.side_effect = [2, 1]
        res = self.game.play_toss(user_call=1, user_number=2)
        self.assertEqual(res["winner"], "computer")
        self.assertEqual(res["sum_parity"], "even")
        self.assertEqual(self.game.phase, "innings1")
        self.assertEqual(self.game.first_batting_team, "computer")

    def test_user_toss_decision_bat(self):
        self.game.phase = "toss_decision"
        res = self.game.set_user_toss_decision("bat")
        self.assertEqual(res["first_batting"], "user")
        self.assertEqual(self.game.current_batting_team, "user")
        self.assertEqual(self.game.phase, "innings1")

    @patch.object(CricketGame, '_ai_choose_number')
    def test_batting_runs_scoring(self, mock_ai):
        # User batting: user plays 4, AI bowls 2 -> user scores 4 runs
        self.game.phase = "innings1"
        self.game._set_batting_order("user")
        mock_ai.return_value = 2

        out = self.game.play_delivery(user_number=4)
        ball = out["ball"]
        self.assertFalse(ball["is_wicket"])
        self.assertEqual(ball["runs"], 4)
        self.assertEqual(ball["total_runs"], 4)
        self.assertEqual(ball["total_wickets"], 0)
        self.assertEqual(ball["event"], "4")

    @patch.object(CricketGame, '_ai_choose_number')
    def test_batting_wicket_out(self, mock_ai):
        # User batting: user plays 3, AI bowls 3 -> OUT!
        self.game.phase = "innings1"
        self.game._set_batting_order("user")
        mock_ai.return_value = 3

        out = self.game.play_delivery(user_number=3)
        ball = out["ball"]
        self.assertTrue(ball["is_wicket"])
        self.assertEqual(ball["runs"], 0)
        self.assertEqual(ball["total_wickets"], 1)
        self.assertEqual(ball["event"], "W")

    @patch.object(CricketGame, '_ai_choose_number')
    def test_innings_transition_on_wickets_limit(self, mock_ai):
        # Quick match has max_wickets = 2. Two wickets fall -> transitions to innings2
        self.game.phase = "innings1"
        self.game._set_batting_order("user")
        mock_ai.return_value = 1

        # Ball 1: User 1, AI 1 -> Wicket 1
        self.game.play_delivery(1)
        self.assertEqual(self.game.innings1["wickets"], 1)
        self.assertEqual(self.game.phase, "innings1")

        # Ball 2: User 1, AI 1 -> Wicket 2 -> Innings over!
        out2 = self.game.play_delivery(1)
        self.assertTrue(out2["innings_over"])
        self.assertEqual(self.game.phase, "innings2")
        self.assertEqual(self.game.target, 1)  # 0 runs scored + 1 = target 1
        self.assertEqual(self.game.current_batting_team, "computer")

    @patch.object(CricketGame, '_ai_choose_number')
    def test_chasing_instant_win(self, mock_ai):
        # Set up 2nd innings where User is chasing target 10
        self.game.first_batting_team = "computer"
        self.game.current_batting_team = "user"
        self.game.current_innings = 2
        self.game.phase = "innings2"
        self.game.innings1["runs"] = 9
        self.game.target = 10

        # User scores 6 (total 6)
        mock_ai.return_value = 0
        self.game.play_delivery(6)
        self.assertEqual(self.game.innings2["runs"], 6)
        self.assertEqual(self.game.phase, "innings2")

        # User scores 4 (total 10 >= target 10) -> Instant Win!
        mock_ai.return_value = 1
        out = self.game.play_delivery(4)
        self.assertTrue(out["innings_over"])
        self.assertEqual(self.game.phase, "completed")
        self.assertEqual(self.game.winner, "user")
        self.assertIn("won by", self.game.result_summary)

    @patch.object(CricketGame, '_ai_choose_number')
    def test_overs_limit_innings_end(self, mock_ai):
        # Quick match: 2 overs = 12 balls
        self.game.phase = "innings1"
        self.game._set_batting_order("user")
        mock_ai.return_value = 0  # no wickets

        for i in range(11):
            out = self.game.play_delivery(1)
            self.assertFalse(out["innings_over"])

        # 12th ball
        out12 = self.game.play_delivery(1)
        self.assertTrue(out12["innings_over"])
        self.assertEqual(self.game.phase, "innings2")

    def test_invalid_delivery_numbers(self):
        self.game.phase = "innings1"
        self.game._set_batting_order("user")
        with self.assertRaises(ValueError):
            self.game.play_delivery(-1)
        with self.assertRaises(ValueError):
            self.game.play_delivery(7)

    @patch.object(CricketGame, '_ai_choose_number')
    def test_tie_match_result(self, mock_ai):
        # Innings 1: User bats and scores 5
        self.game.phase = "innings1"
        self.game._set_batting_order("user")
        mock_ai.return_value = 1
        self.game.play_delivery(5)  # 5 runs
        # Wicket 1 & Wicket 2
        mock_ai.return_value = 2
        self.game.play_delivery(2)
        self.game.play_delivery(2)

        self.assertEqual(self.game.phase, "innings2")
        self.assertEqual(self.game.target, 6)

        # Innings 2: Computer bats. User bowls.
        # Computer scores 5, then loses 2 wickets
        mock_ai.return_value = 5  # AI batsman plays 5
        self.game.play_delivery(1)  # user bowler bowls 1 -> 5 runs scored (total 5)

        mock_ai.return_value = 3  # AI batsman plays 3
        self.game.play_delivery(3)  # user bowler bowls 3 -> OUT (wicket 1)
        self.game.play_delivery(3)  # OUT (wicket 2) -> innings over!

        self.assertEqual(self.game.phase, "completed")
        self.assertEqual(self.game.winner, "draw")
        self.assertIn("Draw", self.game.result_summary)

    def test_serialization(self):
        d = self.game.to_dict()
        restored = CricketGame.from_dict(d)
        self.assertEqual(restored.mode, self.game.mode)
        self.assertEqual(restored.phase, self.game.phase)


if __name__ == '__main__':
    unittest.main()
