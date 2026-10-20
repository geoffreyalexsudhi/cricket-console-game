"""
Unit tests for Cricket Clash Database Layer.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import Database, db


class TestCricketDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Use clean test user
        cls.test_user = "test_player_clash_99"
        cls.test_pass = "secret123"

    def setUp(self):
        # Ensure test user exists cleanly
        db.execute_query("DELETE FROM matches WHERE username = %s", (self.test_user,), commit=True)
        db.execute_query("DELETE FROM user WHERE Username = %s", (self.test_user,), commit=True)
        db.register_user(self.test_user, self.test_pass)

    def test_user_registration_and_login(self):
        # Register duplicate should fail
        ok2, msg2 = db.register_user(self.test_user, self.test_pass)
        self.assertFalse(ok2)

        # Verify correct password
        u = db.verify_user(self.test_user, self.test_pass)
        self.assertIsNotNone(u)
        self.assertEqual(u["Username"], self.test_user)

        # Verify wrong password fails
        u_wrong = db.verify_user(self.test_user, "wrongpass")
        self.assertIsNone(u_wrong)

    def test_record_match_and_stats_update(self):
        user_before = db.get_user(self.test_user)
        gp_before = user_before["Games_played"]
        wins_before = user_before["No_of_wins"]
        runs_before = user_before["Runs_scored"]

        # Record a win with 35 runs
        res = db.record_match_result(
            username=self.test_user,
            mode="Quick Match",
            user_score=35,
            comp_score=20,
            wickets_lost=1,
            total_wickets=2,
            overs_played="2.0",
            max_overs=2,
            result="Win",
            summary="You won by 15 runs!"
        )
        self.assertTrue(res)

        user_after = db.get_user(self.test_user)
        self.assertEqual(user_after["Games_played"], gp_before + 1)
        self.assertEqual(user_after["No_of_wins"], wins_before + 1)
        self.assertEqual(user_after["Runs_scored"], runs_before + 35)
        self.assertEqual(user_after["Last_game"], "Win")
        self.assertGreaterEqual(user_after["Highest_score"], 35)

        # Retrieve match history
        matches = db.get_user_matches(self.test_user, limit=5)
        self.assertGreater(len(matches), 0)
        self.assertEqual(matches[0]["user_score"], 35)
        self.assertEqual(matches[0]["result"], "Win")

    def test_leaderboard(self):
        lb = db.get_leaderboard(limit=10)
        self.assertIsInstance(lb, list)
        if len(lb) > 0:
            top = lb[0]
            self.assertIn("rank", top)
            self.assertIn("win_percentage", top)
            self.assertIn("Username", top)


if __name__ == '__main__':
    unittest.main()
