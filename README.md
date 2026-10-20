# 🏏 Cricket Clash - Modern Gaming Arena

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://palletsprojects.com/p/flask/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0%2F9.0+-orange.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

An authentic, modern, and responsive web adaptation of the classic Indian **Hand Cricket (Odd or Even)** game. Upgraded directly from the original terminal Python project (`cricket original.py`) into a full-featured gaming website with stadium animations, dynamic scoring, user authentication, match history, and a real-time global leaderboard.

---

## 🌟 Key Features

### 1. 🏟️ Modern Website & Stadium Interface
- **Stadium Vibes**: Dynamic dark cricket aesthetic with lush pitch green accents, floodlight gradients, and glassmorphism cards.
- **Visual Pitch Arena**: Animated turf strip with bowling crease lines, stumps, and a cricket ball that delivers on every shot.
- **Dynamic Scoreboard**: Displays Live Runs / Wickets, Overs, Current Run Rate (CRR), Required Run Rate (RRR), Target, and balls remaining.
- **Visual Celebrations**: Pop-up boundary cards (`4`, `6`), wicket alerts (`OUT!`), and celebratory confetti for victory moments.
- **Web Audio Sound Effects**: Custom synthesized audio effects for bat cracks, boundary cheers, wicket crashes, and win fanfares (zero external audio file dependencies, instant playback).

### 2. 🎮 Authentic Game Mechanics (Preserved & Enhanced)
- **Authentic Odd-Even Toss**:
  - Choose call: **1. Odd** or **2. Even**.
  - Enter number **0 to 6**.
  - Computer plays **0 to 6**.
  - Parity matches your call $\rightarrow$ You win the toss and choose to **Bat** or **Bowl**!
  - Computer win $\rightarrow$ Decides dynamically whether to bat or bowl.
- **Core Hand Cricket Rules**:
  - Numbers Match ($Player == Computer$) $\rightarrow$ **OUT!** Wicket falls!
  - Numbers Differ $\rightarrow$ Batsman scores runs equal to their chosen number!
  - Number `0` acts as a solid defense (dot ball, 0 runs, safe unless bowler bowls 0).
- **Target & Innings Flow**:
  - 1st Innings: Sets the total score.
  - 2nd Innings: Chasing team targets $Total + 1$.
  - Instant match conclusion as soon as target is overtaken or all wickets fall.
  - Cap of 200 runs preserved from original code.
- **Keyboard Shortcuts**: Numeric keys `0` through `6` can be pressed on desktop keyboards for fast, seamless play.

### 3. 🎯 Game Modes
1. **Quick Match (2 Overs Blitz)**: 2 Overs, 2 Wickets. High-stakes, thrilling 3-minute clash.
2. **Limited Overs (T5 Clash)**: 5 Overs, 3 Wickets. Balance defense, singles, and big hits.
3. **Classic Endless**: Original rules from your Python script! Unlimited balls until all wickets fall or 200 runs cap. Choose your wickets (1 to 10).
4. **Tournament Championship**: 3-stage knockout cup against international powerhouses:
   - **Quarter-Final** vs *Kiwi Thunder* 🇳🇿
   - **Semi-Final** vs *English Lions* 🏴󠁧󠁢󠁥󠁮󠁧󠁿
   - **Championship Final** vs *Aussie Lightning* 🇦🇺

### 4. 👤 User Accounts & Player Profiles
- User registration and login with secure **PBKDF2-SHA256** password hashing.
- Guest play option for immediate gameplay.
- Complete player profile displaying:
  - Matches Played, Won, Lost, and Drawn.
  - Win Percentage & Status Badge (*Recent Winner*, *Active Contender*).
  - Total Runs Scored & Highest Individual Score.
  - Full match history table with individual innings summaries.

### 5. 🏆 Verified Global Leaderboard
- Real rankings computed strictly from database records (no fake or hardcoded stats).
- Ranked by: **Wins $\rightarrow$ Total Runs $\rightarrow$ Highest Score**.
- Interactive win percentage progress indicators and Gold, Silver, Bronze badges.

### 6. 🔒 Enterprise Security & Anti-Cheat
- **Server-Authoritative Game State**: Deliveries, AI choices, wickets, and run calculations happen 100% on the Flask backend. Players cannot spoof scores via browser DevTools.
- **SQL Injection Prevention**: All queries use parameterized statements (`%s`).
- **Graceful Database Resilience**: Connects to MySQL by default. If MySQL is offline or initializing during development, it seamlessly falls back to a local SQLite database (`cricket.db`) so the app never crashes.

---

## 🗄️ Database Architecture

The original `user` table structure is 100% preserved and extended:

### `user` Table
| Column | Type | Description | Origin |
|---|---|---|---|
| `Username` | VARCHAR(250) PK | Player username | *Original* |
| `Games_played` | INT | Total matches played | *Original* |
| `No_of_wins` | INT | Total victories | *Original* |
| `No_of_draws` | INT | Total ties/draws | *Original* |
| `No_of_losses` | INT | Total defeats | *Original* |
| `Runs_scored` | INT | Total runs accumulated | *Original* |
| `Last_game` | VARCHAR(7) | Outcome of last match ('Win', 'Lose', 'Draw') | *Original* |
| `Password_hash`| VARCHAR(255) | Secure PBKDF2 hash | *New* |
| `Highest_score`| INT | Highest single-match run score | *New* |
| `Avatar` | VARCHAR(50) | Selected avatar | *New* |
| `Created_at` | TIMESTAMP | Account registration date | *New* |

### `matches` Table
Stores complete match scorecards: `id`, `username`, `mode`, `user_score`, `computer_score`, `wickets_lost`, `total_wickets`, `overs_played`, `max_overs`, `result`, `summary`, `innings1_summary`, `innings2_summary`, `created_at`.

---

## 🚀 Installation & Local Setup

### Prerequisites
- Python 3.9+
- MySQL Server (Optional, auto-detects MySQL or falls back to SQLite)

### Step 1: Clone or Navigate to the Project
```bash
cd "cricket-clash"
```

### Step 2: Create and Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and configure your credentials:
```env
SECRET_KEY=your-custom-secret-key-here
FLASK_ENV=development
PORT=5000

# MySQL Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=cricket

# Fallback to local SQLite if MySQL server is offline
ENABLE_SQLITE_FALLBACK=true
```

### Step 5: Run the Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://localhost:5000
```

---

## 🧪 Running the Automated Test Suite

A comprehensive test suite of **18 automated unit and integration tests** verifies every aspect of game logic, database persistence, and API routes.

To run the tests:
```bash
python -m unittest discover -s tests
```

### Verified Test Results:
```text
..................
----------------------------------------------------------------------
Ran 18 tests in 4.051s

OK
```

**Tested Scenarios**:
1. `test_toss_user_wins_odd`: User calls Odd and sum is odd $\rightarrow$ User wins toss.
2. `test_toss_computer_wins_even`: Parity matches computer $\rightarrow$ Computer wins toss and bats/bowls.
3. `test_batting_runs_scoring`: Differing numbers correctly accumulate runs for batsman.
4. `test_batting_wicket_out`: Matching numbers trigger OUT and increment wickets.
5. `test_overs_limit_innings_end`: Innings concludes at exactly `max_overs * 6` balls.
6. `test_innings_transition_on_wickets_limit`: Innings transitions to 2nd innings when all wickets fall.
7. `test_chasing_instant_win`: Chasing team wins immediately upon overtaking target.
8. `test_tie_match_result`: Equal scores at the end of 2nd innings correctly declare a Draw.
9. `test_invalid_delivery_numbers`: Out-of-bounds numbers (< 0 or > 6) throw validation errors.
10. `test_serialization`: Game state serializes and deserializes accurately.
11. `test_user_registration_and_login`: User registration, duplicate rejection, and password checking.
12. `test_record_match_and_stats_update`: Match history storage and incremental stats updates.
13. `test_leaderboard`: Dynamic ranking calculation and accurate win rates.
14. `test_pages_load_successfully`: All 5 primary HTML views return HTTP 200.
15. `test_auth_and_profile_flow`: End-to-end registration, profile access, and login flow.
16. `test_full_match_via_api_and_stat_recording`: Simulated complete match from toss to victory with verified DB insertion.

---

## 📁 Project Directory Structure

```
cricket-clash/
├── cricket original.py   # Preserved original Python console script
├── app.py                # Main Flask web server & route handlers
├── game_logic.py         # Pure Python game mechanics & AI opponent engine
├── database.py           # MySQL & SQLite database abstraction layer
├── requirements.txt      # Project Python dependencies
├── .env                  # Local environment configuration
├── .env.example          # Template environment file
├── README.md             # Complete documentation
├── templates/            # Modern HTML5 Jinja2 Templates
│   ├── base.html         # Base layout with navbar, footer & sound toggle
│   ├── index.html        # Landing page with mode selection & hero banner
│   ├── game.html         # Live cricket stadium arena & interactive pitch
│   ├── tournament.html   # World knockout cup stages
│   ├── leaderboard.html  # Verified global player rankings
│   ├── profile.html      # Player stats & match history scorecard
│   ├── login.html        # User login portal
│   ├── register.html     # Player profile registration
│   └── rules.html        # Hand cricket rulebook & guidelines
├── static/               # Frontend Assets
│   ├── css/
│   │   └── style.css     # Stadium dark theme, neon accents & glassmorphism
│   └── js/
│       └── game.js       # Client engine, Web Audio synth & delivery controls
└── tests/                # Automated Test Suite
    ├── test_game_logic.py
    ├── test_database.py
    └── test_routes.py
```

---

## 🛡️ License

This project is licensed under the MIT License. Built with passion for cricket gaming.
