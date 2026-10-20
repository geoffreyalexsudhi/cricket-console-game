"""
Database Layer for Cricket Clash.
Supports MySQL with automated schema management, parameterized queries,
password hashing, match history recording, and dynamic leaderboard calculation.
Gracefully falls back to SQLite if MySQL service is offline or inaccessible in the local environment.
"""

import os
import sqlite3
import logging
from typing import Dict, Any, List, Optional, Tuple
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

logger = logging.getLogger("cricket_db")
logging.basicConfig(level=logging.INFO)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "cricket")
ENABLE_SQLITE_FALLBACK = os.getenv("ENABLE_SQLITE_FALLBACK", "true").lower() in ("1", "true", "yes")

SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cricket.db")


class Database:
    """Manages MySQL / SQLite connections and database operations."""

    def __init__(self):
        self.engine_type = "mysql"
        self._test_or_init()

    def _get_mysql_connection(self, create_db_if_missing: bool = True):
        import mysql.connector
        if create_db_if_missing:
            # First connect without database to ensure DB exists
            temp_conn = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD
            )
            temp_cursor = temp_conn.cursor()
            temp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
            temp_conn.commit()
            temp_cursor.close()
            temp_conn.close()

        return mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

    def _get_sqlite_connection(self):
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def get_connection(self):
        """Returns active database connection based on configured engine."""
        if self.engine_type == "mysql":
            try:
                return self._get_mysql_connection(create_db_if_missing=False)
            except Exception as err:
                if ENABLE_SQLITE_FALLBACK:
                    logger.warning(f"MySQL unavailable ({err}). Falling back to SQLite.")
                    self.engine_type = "sqlite"
                    return self._get_sqlite_connection()
                raise
        else:
            return self._get_sqlite_connection()

    def _test_or_init(self):
        """Attempts connection to MySQL, initializes tables, or falls back to SQLite."""
        try:
            import mysql.connector
            conn = self._get_mysql_connection(create_db_if_missing=True)
            conn.close()
            self.engine_type = "mysql"
            logger.info("Connected to MySQL successfully.")
        except Exception as e:
            if ENABLE_SQLITE_FALLBACK:
                logger.warning(f"Could not connect to MySQL ({e}). Initializing SQLite fallback at {SQLITE_PATH}.")
                self.engine_type = "sqlite"
            else:
                raise ConnectionError(f"Failed to connect to MySQL database: {e}")

        self.init_db()

    def init_db(self):
        """Initializes tables preserving existing legacy columns while adding modern features."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if self.engine_type == "mysql":
                # Preserve original user table structure and add modern extensions
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS user (
                    Username VARCHAR(250) PRIMARY KEY,
                    Games_played INTEGER DEFAULT 0,
                    No_of_wins INTEGER DEFAULT 0,
                    No_of_draws INTEGER DEFAULT 0,
                    No_of_losses INTEGER DEFAULT 0,
                    Runs_scored INTEGER DEFAULT 0,
                    Last_game VARCHAR(7) DEFAULT NULL,
                    Password_hash VARCHAR(255) DEFAULT NULL,
                    Highest_score INTEGER DEFAULT 0,
                    Avatar VARCHAR(50) DEFAULT 'cricketer1',
                    Created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)

                # Check if legacy table was missing columns and alter if needed
                cursor.execute("SHOW COLUMNS FROM user LIKE 'Password_hash'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE user ADD COLUMN Password_hash VARCHAR(255) DEFAULT NULL")
                cursor.execute("SHOW COLUMNS FROM user LIKE 'Highest_score'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE user ADD COLUMN Highest_score INTEGER DEFAULT 0")
                cursor.execute("SHOW COLUMNS FROM user LIKE 'Avatar'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE user ADD COLUMN Avatar VARCHAR(50) DEFAULT 'cricketer1'")
                cursor.execute("SHOW COLUMNS FROM user LIKE 'Created_at'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE user ADD COLUMN Created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

                # Match History table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(250) NOT NULL,
                    mode VARCHAR(50) NOT NULL,
                    user_score INT NOT NULL,
                    computer_score INT NOT NULL,
                    wickets_lost INT NOT NULL,
                    total_wickets INT NOT NULL,
                    overs_played VARCHAR(10) NOT NULL,
                    max_overs INT NOT NULL,
                    result VARCHAR(20) NOT NULL,
                    summary VARCHAR(255) NOT NULL,
                    innings1_summary TEXT,
                    innings2_summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (username) REFERENCES user(Username) ON DELETE CASCADE
                )
                """)

                # Tournament table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS tournaments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(250) NOT NULL,
                    tournament_name VARCHAR(100) NOT NULL,
                    stage VARCHAR(50) NOT NULL,
                    matches_won INT DEFAULT 0,
                    status VARCHAR(50) DEFAULT 'in_progress',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (username) REFERENCES user(Username) ON DELETE CASCADE
                )
                """)

            else:
                # SQLite implementation
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS user (
                    Username VARCHAR(250) PRIMARY KEY,
                    Games_played INTEGER DEFAULT 0,
                    No_of_wins INTEGER DEFAULT 0,
                    No_of_draws INTEGER DEFAULT 0,
                    No_of_losses INTEGER DEFAULT 0,
                    Runs_scored INTEGER DEFAULT 0,
                    Last_game VARCHAR(7) DEFAULT NULL,
                    Password_hash VARCHAR(255) DEFAULT NULL,
                    Highest_score INTEGER DEFAULT 0,
                    Avatar VARCHAR(50) DEFAULT 'cricketer1',
                    Created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(250) NOT NULL,
                    mode VARCHAR(50) NOT NULL,
                    user_score INT NOT NULL,
                    computer_score INT NOT NULL,
                    wickets_lost INT NOT NULL,
                    total_wickets INT NOT NULL,
                    overs_played VARCHAR(10) NOT NULL,
                    max_overs INT NOT NULL,
                    result VARCHAR(20) NOT NULL,
                    summary VARCHAR(255) NOT NULL,
                    innings1_summary TEXT,
                    innings2_summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (username) REFERENCES user(Username) ON DELETE CASCADE
                )
                """)

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS tournaments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(250) NOT NULL,
                    tournament_name VARCHAR(100) NOT NULL,
                    stage VARCHAR(50) NOT NULL,
                    matches_won INT DEFAULT 0,
                    status VARCHAR(50) DEFAULT 'in_progress',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (username) REFERENCES user(Username) ON DELETE CASCADE
                )
                """)

            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error during init_db: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    def execute_query(self, query: str, params: Tuple = (), commit: bool = False, fetch_one: bool = False, fetch_all: bool = False):
        """Unified query runner handling parameter placeholder differences between MySQL (%s) and SQLite (?)."""
        conn = self.get_connection()
        cursor = conn.cursor()

        actual_query = query
        if self.engine_type == "sqlite":
            actual_query = query.replace("%s", "?")

        try:
            cursor.execute(actual_query, params)
            if commit:
                conn.commit()

            if fetch_one:
                row = cursor.fetchone()
                if row is None:
                    return None
                if self.engine_type == "sqlite":
                    return dict(row)
                else:
                    cols = [d[0] for d in cursor.description]
                    return dict(zip(cols, row))

            if fetch_all:
                rows = cursor.fetchall()
                if self.engine_type == "sqlite":
                    return [dict(r) for r in rows]
                else:
                    cols = [d[0] for d in cursor.description]
                    return [dict(zip(cols, r)) for r in rows]

            return cursor.lastrowid
        except Exception as e:
            if commit:
                conn.rollback()
            logger.error(f"Database query error: {e} | Query: {actual_query} | Params: {params}")
            raise
        finally:
            cursor.close()
            conn.close()

    # User Management Methods
    def register_user(self, username: str, password: str, avatar: str = "cricketer1") -> Tuple[bool, str]:
        """Registers a new user with securely hashed password."""
        username = username.strip()
        if not username:
            return False, "Username cannot be empty."
        if len(username) > 250:
            return False, "Username must contain 250 characters or less."
        if len(password) < 4:
            return False, "Password must be at least 4 characters long."

        existing = self.get_user(username)
        if existing:
            return False, f"Username '{username}' already exists. Please login instead."

        try:
            pw_hash = generate_password_hash(password, method="pbkdf2:sha256")
        except Exception:
            pw_hash = generate_password_hash(password)
        try:
            self.execute_query(
                "INSERT INTO user (Username, Games_played, No_of_wins, No_of_draws, No_of_losses, Runs_scored, Last_game, Password_hash, Highest_score, Avatar) VALUES (%s, 0, 0, 0, 0, 0, NULL, %s, 0, %s)",
                (username, pw_hash, avatar),
                commit=True
            )
            return True, "Registration successful! You can now login."
        except Exception as e:
            return False, f"Failed to register user: {str(e)}"

    def verify_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Verifies credentials. Also supports legacy accounts without passwords."""
        user = self.get_user(username)
        if not user:
            return None

        pw_hash = user.get("Password_hash")
        # If legacy user without password, allow setting it or initial login
        if not pw_hash:
            return user

        if check_password_hash(pw_hash, password):
            return user
        return None

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Fetches user record by username."""
        return self.execute_query(
            "SELECT * FROM user WHERE Username = %s",
            (username,),
            fetch_one=True
        )

    def record_match_result(self, username: str, mode: str, user_score: int, comp_score: int,
                            wickets_lost: int, total_wickets: int, overs_played: str,
                            max_overs: int, result: str, summary: str,
                            innings1_summary: str = "", innings2_summary: str = "") -> bool:
        """
        Updates user statistics (games played, wins, draws, losses, runs, highest score, last game)
        and inserts a complete record into matches history.
        """
        user = self.get_user(username)
        if not user:
            return False

        games_played = user["Games_played"] + 1
        wins = user["No_of_wins"]
        draws = user["No_of_draws"]
        losses = user["No_of_losses"]
        runs_scored = user["Runs_scored"] + user_score
        highest_score = max(user.get("Highest_score", 0) or 0, user_score)

        if result == "Win":
            wins += 1
            last_game = "Win"
        elif result == "Lose":
            losses += 1
            last_game = "Lose"
        else:
            draws += 1
            last_game = "Draw"

        # Update user stats
        self.execute_query(
            """UPDATE user SET 
                Games_played = %s,
                No_of_wins = %s,
                No_of_draws = %s,
                No_of_losses = %s,
                Runs_scored = %s,
                Last_game = %s,
                Highest_score = %s
               WHERE Username = %s""",
            (games_played, wins, draws, losses, runs_scored, last_game, highest_score, username),
            commit=True
        )

        # Insert match history record
        self.execute_query(
            """INSERT INTO matches (
                username, mode, user_score, computer_score, wickets_lost,
                total_wickets, overs_played, max_overs, result, summary,
                innings1_summary, innings2_summary
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (username, mode, user_score, comp_score, wickets_lost,
             total_wickets, overs_played, max_overs, result, summary,
             innings1_summary, innings2_summary),
            commit=True
        )
        return True

    def get_user_matches(self, username: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Retrieves match history for a specific user ordered by latest."""
        return self.execute_query(
            "SELECT * FROM matches WHERE username = %s ORDER BY id DESC LIMIT %s",
            (username, limit),
            fetch_all=True
        ) or []

    def get_leaderboard(self, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Calculates dynamic leaderboard based on Wins, Win Percentage, Total Runs, and Highest Score.
        Never uses hardcoded or fake statistics.
        """
        users = self.execute_query(
            """SELECT Username, Games_played, No_of_wins, No_of_draws, No_of_losses, Runs_scored, Highest_score, Avatar, Last_game
               FROM user
               ORDER BY No_of_wins DESC, Runs_scored DESC, Highest_score DESC
               LIMIT %s""",
            (limit,),
            fetch_all=True
        ) or []

        # Calculate win percentage
        leaderboard = []
        for rank, u in enumerate(users, start=1):
            gp = u.get("Games_played", 0)
            wins = u.get("No_of_wins", 0)
            win_pct = round((wins / gp) * 100, 1) if gp > 0 else 0.0
            item = dict(u)
            item["rank"] = rank
            item["win_percentage"] = win_pct
            leaderboard.append(item)

        return leaderboard


# Global singleton instance
db = Database()
