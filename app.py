"""
Cricket Clash - Modern Web Application Flask Server.
Handles authentication, game flow, match history recording,
leaderboards, and user statistics.
"""

import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from dotenv import load_dotenv

from database import db
from game_logic import CricketGame

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "cricket-clash-production-secret-key-2026")

# In-memory storage for active game sessions: session_id -> CricketGame
ACTIVE_GAMES = {}


def get_current_user():
    """Returns the logged-in username or None."""
    return session.get("username")


def get_or_create_game(mode="quick", custom_wickets=3, ai_name=None, reset=False):
    """Retrieves or creates the active game for current browser session."""
    session_id = session.get("game_session_id")
    if not session_id or reset or session_id not in ACTIVE_GAMES:
        session_id = str(uuid.uuid4())
        session["game_session_id"] = session_id
        game = CricketGame(mode=mode, custom_wickets=custom_wickets, ai_name=ai_name)
        ACTIVE_GAMES[session_id] = game
        return game
    return ACTIVE_GAMES[session_id]


@app.context_processor
def inject_user_context():
    """Injects current user and stats into all Jinja templates."""
    username = get_current_user()
    user_data = None
    if username:
        user_data = db.get_user(username)
    return {
        "current_user": username,
        "user_profile": user_data,
        "db_engine": db.engine_type.upper()
    }


# ==========================================
# PAGE ROUTES
# ==========================================

@app.route("/")
def index():
    """Landing page with branding, match modes, and quick stats."""
    leaderboard_preview = db.get_leaderboard(limit=5)
    return render_template("index.html", leaderboard=leaderboard_preview)


@app.route("/game")
def game_arena():
    """Interactive Cricket Stadium Game Arena."""
    mode = request.args.get("mode", "quick")
    custom_wickets = int(request.args.get("wickets", 3))
    
    # If starting a fresh match or changing mode
    if request.args.get("new") == "1":
        get_or_create_game(mode=mode, custom_wickets=custom_wickets, reset=True)
    else:
        # Resume or start
        session_id = session.get("game_session_id")
        if not session_id or session_id not in ACTIVE_GAMES:
            get_or_create_game(mode=mode, custom_wickets=custom_wickets, reset=True)

    return render_template("game.html", selected_mode=mode)


@app.route("/tournament")
def tournament():
    """Tournament Championship Mode."""
    username = get_current_user()
    return render_template("tournament.html", username=username)


@app.route("/leaderboard")
def leaderboard():
    """Global rankings and match records."""
    ranks = db.get_leaderboard(limit=50)
    return render_template("leaderboard.html", leaderboard=ranks)


@app.route("/profile")
def profile():
    """Player Profile, statistics, and recent match cards."""
    username = get_current_user()
    if not username:
        flash("Please log in to view your profile and match history.", "info")
        return redirect(url_for("login"))

    user = db.get_user(username)
    matches = db.get_user_matches(username, limit=30)
    
    # Calculate win percentage
    games_played = user.get("Games_played", 0) if user else 0
    wins = user.get("No_of_wins", 0) if user else 0
    win_pct = round((wins / games_played) * 100, 1) if games_played > 0 else 0.0

    return render_template("profile.html", user=user, matches=matches, win_pct=win_pct)


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login endpoint."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username:
            flash("Please enter your username.", "danger")
            return render_template("login.html")

        user = db.verify_user(username, password)
        if user:
            session["username"] = user["Username"]
            flash(f"Welcome back, {user['Username']}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("game_arena"))
        else:
            flash("Invalid username or password. Please try again.", "danger")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """User registration endpoint."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        avatar = request.form.get("avatar", "cricketer1")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        success, message = db.register_user(username, password, avatar)
        if success:
            session["username"] = username
            flash(message, "success")
            return redirect(url_for("game_arena"))
        else:
            flash(message, "danger")

    return render_template("register.html")


@app.route("/logout")
def logout():
    """Clears user session."""
    session.pop("username", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/rules")
def rules():
    """Detailed game rules and Odd/Even Hand Cricket guide."""
    return render_template("rules.html")


# ==========================================
# REST API ENDPOINTS (FOR DYNAMIC GAMEPLAY)
# ==========================================

@app.route("/api/game/state", methods=["GET"])
def api_game_state():
    """Returns current match state and scoreboard."""
    session_id = session.get("game_session_id")
    if not session_id or session_id not in ACTIVE_GAMES:
        game = get_or_create_game()
    else:
        game = ACTIVE_GAMES[session_id]

    return jsonify({
        "success": True,
        "state": game.get_scoreboard(),
        "phase": game.phase,
        "mode": game.mode,
        "ai_name": game.ai_name,
        "toss_winner": game.toss_winner
    })


@app.route("/api/game/start", methods=["POST"])
def api_game_start():
    """Starts or resets a match with chosen settings."""
    data = request.get_json() or {}
    mode = data.get("mode", "quick")
    custom_wickets = int(data.get("wickets", 3))
    ai_name = data.get("ai_name")

    game = get_or_create_game(mode=mode, custom_wickets=custom_wickets, ai_name=ai_name, reset=True)
    return jsonify({
        "success": True,
        "message": f"Match initialized: {game.mode_name}",
        "state": game.get_scoreboard(),
        "phase": game.phase
    })


@app.route("/api/game/toss", methods=["POST"])
def api_game_toss():
    """Executes toss call and odd/even calculation."""
    session_id = session.get("game_session_id")
    if not session_id or session_id not in ACTIVE_GAMES:
        return jsonify({"success": False, "error": "No active match found."}), 400

    game = ACTIVE_GAMES[session_id]
    data = request.get_json() or {}
    
    try:
        call = int(data.get("call")) # 1: Odd, 2: Even
        number = int(data.get("number")) # 0-6
        toss_result = game.play_toss(user_call=call, user_number=number)
        return jsonify({
            "success": True,
            "toss": toss_result,
            "state": game.get_scoreboard()
        })
    except ValueError as err:
        return jsonify({"success": False, "error": str(err)}), 400


@app.route("/api/game/toss-decision", methods=["POST"])
def api_game_toss_decision():
    """Handles batting or bowling decision after winning the toss."""
    session_id = session.get("game_session_id")
    if not session_id or session_id not in ACTIVE_GAMES:
        return jsonify({"success": False, "error": "No active match found."}), 400

    game = ACTIVE_GAMES[session_id]
    data = request.get_json() or {}

    try:
        decision = data.get("decision", "bat")
        custom_wickets = int(data.get("wickets", 3)) if "wickets" in data else None
        res = game.set_user_toss_decision(decision=decision, custom_wickets=custom_wickets)
        return jsonify({
            "success": True,
            "decision": res,
            "state": game.get_scoreboard()
        })
    except ValueError as err:
        return jsonify({"success": False, "error": str(err)}), 400


@app.route("/api/game/delivery", methods=["POST"])
def api_game_delivery():
    """Processes a single ball delivery (0-6). Validates and updates score server-side."""
    session_id = session.get("game_session_id")
    if not session_id or session_id not in ACTIVE_GAMES:
        return jsonify({"success": False, "error": "No active match found."}), 400

    game = ACTIVE_GAMES[session_id]
    data = request.get_json() or {}

    try:
        user_num = int(data.get("number"))
        delivery_res = game.play_delivery(user_number=user_num)

        # If match is completed, record statistics to database
        if game.phase == "completed":
            username = get_current_user()
            if username:
                # Record user match in DB
                user_score = game.user_total_runs
                comp_score = game.computer_total_runs
                
                # Determine user wickets lost
                if game.first_batting_team == "user":
                    user_wickets = game.innings1["wickets"]
                    user_overs = game.innings1["overs"]
                    inn1_summary = f"User: {game.innings1['runs']}/{game.innings1['wickets']} ({game.innings1['overs']} ov)"
                    inn2_summary = f"{game.ai_name}: {game.innings2['runs']}/{game.innings2['wickets']} ({game.innings2['overs']} ov)"
                else:
                    user_wickets = game.innings2["wickets"]
                    user_overs = game.innings2["overs"]
                    inn1_summary = f"{game.ai_name}: {game.innings1['runs']}/{game.innings1['wickets']} ({game.innings1['overs']} ov)"
                    inn2_summary = f"User: {game.innings2['runs']}/{game.innings2['wickets']} ({game.innings2['overs']} ov)"

                match_result = "Win" if game.winner == "user" else ("Lose" if game.winner == "computer" else "Draw")

                db.record_match_result(
                    username=username,
                    mode=game.mode_name,
                    user_score=user_score,
                    comp_score=comp_score,
                    wickets_lost=user_wickets,
                    total_wickets=game.max_wickets,
                    overs_played=user_overs,
                    max_overs=game.max_overs,
                    result=match_result,
                    summary=game.result_summary,
                    innings1_summary=inn1_summary,
                    innings2_summary=inn2_summary
                )

        return jsonify({
            "success": True,
            "data": delivery_res
        })
    except ValueError as err:
        return jsonify({"success": False, "error": str(err)}), 400


@app.route("/api/user/quick-register", methods=["POST"])
def api_quick_register():
    """Allows quick guest naming (preserving original CLI prompt feel)."""
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    if not username:
        return jsonify({"success": False, "error": "Username cannot be empty."}), 400

    user = db.get_user(username)
    if not user:
        # Create user account without password requirement for quick guest
        db.execute_query(
            "INSERT INTO user (Username, Games_played, No_of_wins, No_of_draws, No_of_losses, Runs_scored, Last_game) VALUES (%s, 0, 0, 0, 0, 0, NULL)",
            (username,),
            commit=True
        )
    session["username"] = username
    return jsonify({"success": True, "username": username})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
