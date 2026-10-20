"""
Integration tests for Cricket Clash Flask Routes and REST APIs.
"""

import unittest
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from database import db


class TestCricketClashRoutes(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_pages_load_successfully(self):
        # 1. Home page
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'CRICKET', res.data)

        # 2. Game Arena
        res = self.client.get('/game')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'LIVE-SCOREBOARD', res.data.upper())
        self.assertIn(b'LIVE COMMENTARY', res.data.upper())

        # 3. Leaderboard
        res = self.client.get('/leaderboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'LEADERBOARD', res.data.upper())

        # 4. Tournament
        res = self.client.get('/tournament')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'TOURNAMENT', res.data.upper())

        # 5. Rules
        res = self.client.get('/rules')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'HOW TO PLAY', res.data.upper())

    def test_auth_and_profile_flow(self):
        test_uname = "web_cricketer_auth_test"
        db.execute_query("DELETE FROM matches WHERE username = %s", (test_uname,), commit=True)
        db.execute_query("DELETE FROM user WHERE Username = %s", (test_uname,), commit=True)

        # Register user
        reg_res = self.client.post('/register', data={
            'username': test_uname,
            'password': 'password123',
            'confirm_password': 'password123',
            'avatar': 'cricketer1'
        }, follow_redirects=True)
        self.assertEqual(reg_res.status_code, 200)

        # Profile page
        prof_res = self.client.get('/profile')
        self.assertEqual(prof_res.status_code, 200)
        self.assertIn(test_uname.encode(), prof_res.data)

        # Logout
        logout_res = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(logout_res.status_code, 200)

        # Login
        login_res = self.client.post('/login', data={
            'username': test_uname,
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)

    def test_full_match_via_api_and_stat_recording(self):
        star_uname = "match_player_star"
        db.execute_query("DELETE FROM matches WHERE username = %s", (star_uname,), commit=True)
        db.execute_query("DELETE FROM user WHERE Username = %s", (star_uname,), commit=True)

        # Login test user
        self.client.post('/register', data={
            'username': star_uname,
            'password': 'password123',
            'confirm_password': 'password123'
        })

        # Start match
        self.client.post('/api/game/start', json={'mode': 'quick'})

        # Toss
        toss_res = self.client.post('/api/game/toss', json={'call': 1, 'number': 3})
        toss_data = json.loads(toss_res.data)['toss']

        if toss_data['winner'] == 'user':
            self.client.post('/api/game/toss-decision', json={'decision': 'bat'})

        # Play deliveries until match completion
        max_balls = 40
        completed = False
        for _ in range(max_balls):
            deliv_res = self.client.post('/api/game/delivery', json={'number': 4})
            deliv_data = json.loads(deliv_res.data)['data']
            if deliv_data['phase'] == 'completed':
                completed = True
                break

        self.assertTrue(completed)

        # Verify that match history was stored
        matches = db.get_user_matches('match_player_star')
        self.assertGreater(len(matches), 0)
        user = db.get_user('match_player_star')
        self.assertGreater(user['Games_played'], 0)


if __name__ == '__main__':
    unittest.main()
