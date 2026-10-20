"""
Game Logic Engine for Cricket Clash.
Preserves original Hand Cricket / Odd-Even rules while supporting
Quick Match, Limited Overs, Classic Mode, and Tournament formats.
"""

import random
from typing import Dict, Any, List, Optional, Tuple


class CricketGame:
    """
    Cricket Clash match manager.
    Encapsulates state, toss, deliveries, innings transition, and result determination.
    """

    FORMAT_CONFIGS = {
        "quick": {
            "name": "Quick Match",
            "max_overs": 2,
            "max_wickets": 2,
            "description": "2 Overs • 2 Wickets Blitz"
        },
        "limited": {
            "name": "Limited Overs (T5)",
            "max_overs": 5,
            "max_wickets": 3,
            "description": "5 Overs • 3 Wickets Clash"
        },
        "classic": {
            "name": "Classic Endless",
            "max_overs": 0,  # 0 indicates unlimited overs until all out or 200 runs
            "max_wickets": 3, # Can be chosen by player
            "description": "Original Rules • Up to 200 Runs"
        },
        "tournament": {
            "name": "Tournament Mode",
            "max_overs": 3,
            "max_wickets": 3,
            "description": "Knockout Championship"
        }
    }

    AI_NAMES = [
        "Aussie Lightning",
        "English Lions",
        "Proteas Fire",
        "Caribbean Calypso",
        "Kiwi Thunder",
        "Royal Challengers AI"
    ]

    COMMENTARY_LINES = {
        "dot": [
            "Good length delivery, pushed straight to the fielder. No run.",
            "Beaten by pace and swing! Dot ball.",
            "Solid defensive block back to the bowler.",
            "Swing and a miss! Excellent dot ball."
        ],
        "one": [
            "Nudged into the gap for a quick single.",
            "Pushed down to long-on to rotate the strike.",
            "Smart cricket, tapped to mid-wicket for one.",
            "Quick single taken, good communication between batsmen."
        ],
        "two": [
            "Driven into the deep covers, they sprint back for the second!",
            "Flicked off the pads nicely, comfortable brace.",
            "Worked away behind square, superb running for two.",
            "Placed past point, easy double."
        ],
        "three": [
            "Glorious stroke through extra cover, outfield is slow, they run three!",
            "Punched through mid-wicket, electric running gets them three runs.",
            "Pierces the inner circle, athletic fielding saves the boundary, 3 runs."
        ],
        "four": [
            "CRACK! Pounded through the covers for a glorious FOUR!",
            "SHORT AND PUNISHED! Pulled away behind square to the boundary!",
            "PURE TIMING! Driven right down the ground with supreme authority!",
            "EDGED AND AWAY! Flashes past slip straight into the boundary rope!"
        ],
        "five": [
            "Overthrow! Five runs conceded by sloppy fielding!",
            "Direct hit attempt misses everyone, bonus runs awarded!"
        ],
        "six": [
            "BOOM! LAUNCHED INTO THE STRATOSPHERE FOR A HUGE SIX!",
            "SWEET SPOT! Clears long-on with ease, crowd is on its feet!",
            "MAXIMUM! That has sailed over deep mid-wicket into the top tier!",
            "STAND AND DELIVER! Picked up effortlessly and deposited into the stands!"
        ],
        "wicket": [
            "TIMBERRR! Cleans him up! Absolute peach of a delivery!",
            "CAUGHT! Mistimed the shot and straight down the throat of long-off!",
            "GONE! Numbers matched! Golden duck or crucial breakthrough!",
            "UP IN THE AIR... TAKEN! Outstanding catch under pressure!"
        ]
    }

    def __init__(self, mode: str = "quick", custom_wickets: int = 3, ai_name: Optional[str] = None):
        if mode not in self.FORMAT_CONFIGS:
            mode = "quick"
        
        self.mode = mode
        config = self.FORMAT_CONFIGS[mode]
        self.mode_name = config["name"]
        self.max_overs = config["max_overs"]
        self.max_wickets = custom_wickets if (mode == "classic" and custom_wickets > 0) else config["max_wickets"]
        self.ai_name = ai_name or random.choice(self.AI_NAMES)

        # Match flow states: 'toss', 'toss_decision', 'innings1', 'innings_break', 'innings2', 'completed'
        self.phase = "toss"

        # Toss results
        self.toss_choice: Optional[int] = None  # 1: Odd, 2: Even
        self.toss_user_num: Optional[int] = None
        self.toss_comp_num: Optional[int] = None
        self.toss_sum: Optional[int] = None
        self.toss_sum_parity: Optional[str] = None  # 'odd' or 'even'
        self.toss_winner: Optional[str] = None      # 'user' or 'computer'
        self.user_decision: Optional[str] = None    # 'bat' or 'bowl'
        self.comp_decision: Optional[str] = None

        # Innings details
        self.current_innings = 1
        self.first_batting_team: Optional[str] = None # 'user' or 'computer'
        self.current_batting_team: Optional[str] = None
        self.target: Optional[int] = None

        # Innings 1 score record
        self.innings1 = {
            "batting_team": None,
            "runs": 0,
            "wickets": 0,
            "balls": 0,
            "overs": "0.0",
            "timeline": []
        }

        # Innings 2 score record
        self.innings2 = {
            "batting_team": None,
            "runs": 0,
            "wickets": 0,
            "balls": 0,
            "overs": "0.0",
            "timeline": []
        }

        # Match outcome
        self.winner: Optional[str] = None # 'user', 'computer', 'draw'
        self.result_summary: str = ""
        self.runs_difference: int = 0
        self.wickets_difference: int = 0
        self.user_total_runs: int = 0
        self.computer_total_runs: int = 0

    def play_toss(self, user_call: int, user_number: int) -> Dict[str, Any]:
        """
        Original Toss Mechanics:
        1: Odd, 2: Even.
        Player number (0-6) + Computer number (0-6).
        Sum parity matches call -> Player wins, else Computer wins.
        """
        if self.phase != "toss":
            raise ValueError("Toss has already been conducted.")

        if user_call not in [1, 2]:
            raise ValueError("Toss choice must be 1 (Odd) or 2 (Even).")

        if not (0 <= user_number <= 6):
            raise ValueError("Number must be between 0 and 6.")

        comp_number = random.randrange(0, 7)
        toss_sum = user_number + comp_number
        is_even = (toss_sum % 2 == 0)
        sum_parity = "even" if is_even else "odd"

        # (call == 1 and odd) or (call == 2 and even)
        player_won = (user_call == 1 and not is_even) or (user_call == 2 and is_even)

        self.toss_choice = user_call
        self.toss_user_num = user_number
        self.toss_comp_num = comp_number
        self.toss_sum = toss_sum
        self.toss_sum_parity = sum_parity
        self.toss_winner = "user" if player_won else "computer"

        if player_won:
            self.phase = "toss_decision"
            comp_decision = None
        else:
            # Computer decides: 1: Batting, 2: Bowling (matches original k7)
            k7 = random.randrange(1, 3)
            comp_decision = "bat" if k7 == 1 else "bowl"
            self.comp_decision = comp_decision
            
            # In original code, if computer won toss and classic mode, computer picked wickets 1..2
            if self.mode == "classic":
                self.max_wickets = random.randrange(1, 3)

            self._set_batting_order(first_batting="computer" if comp_decision == "bat" else "user")
            self.phase = "innings1"

        return {
            "user_call": "Odd" if user_call == 1 else "Even",
            "user_number": user_number,
            "comp_number": comp_number,
            "toss_sum": toss_sum,
            "sum_parity": sum_parity,
            "winner": self.toss_winner,
            "comp_decision": comp_decision,
            "phase": self.phase,
            "max_wickets": self.max_wickets
        }

    def set_user_toss_decision(self, decision: str, custom_wickets: Optional[int] = None) -> Dict[str, Any]:
        """
        Player selects Bat or Bowl after winning toss.
        Optional custom wickets in classic mode.
        """
        if self.phase != "toss_decision":
            raise ValueError("Cannot set decision at this stage.")

        decision = decision.lower()
        if decision not in ["bat", "bowl"]:
            raise ValueError("Decision must be 'bat' or 'bowl'.")

        self.user_decision = decision
        if self.mode == "classic" and custom_wickets and custom_wickets > 0:
            self.max_wickets = min(max(custom_wickets, 1), 10)

        first_batting = "user" if decision == "bat" else "computer"
        self._set_batting_order(first_batting=first_batting)
        self.phase = "innings1"

        return {
            "user_decision": decision,
            "first_batting": first_batting,
            "max_wickets": self.max_wickets,
            "phase": self.phase
        }

    def _set_batting_order(self, first_batting: str):
        self.first_batting_team = first_batting
        self.current_batting_team = first_batting
        self.current_innings = 1
        self.innings1["batting_team"] = first_batting
        self.innings2["batting_team"] = "computer" if first_batting == "user" else "user"

    def _ai_choose_number(self, is_batting: bool, target_remaining: Optional[int] = None, balls_remaining: Optional[int] = None) -> int:
        """
        AI opponent strategy:
        Blends true random with cricket context (defensive when chasing low, aggressive when high).
        """
        if is_batting:
            if target_remaining is not None and balls_remaining is not None and balls_remaining > 0:
                req_rate = target_remaining / balls_remaining
                if req_rate > 3.0:
                    weights = [0.05, 0.10, 0.15, 0.10, 0.30, 0.05, 0.25]
                elif req_rate < 1.0:
                    weights = [0.15, 0.35, 0.25, 0.10, 0.10, 0.02, 0.03]
                else:
                    weights = [0.10, 0.20, 0.20, 0.10, 0.20, 0.05, 0.15]
            else:
                weights = [0.10, 0.20, 0.20, 0.10, 0.20, 0.05, 0.15]
        else:
            # Bowling: trying to guess batsman's number
            weights = [0.15, 0.20, 0.15, 0.10, 0.20, 0.05, 0.15]

        return random.choices(range(0, 7), weights=weights, k=1)[0]

    def play_delivery(self, user_number: int) -> Dict[str, Any]:
        """
        Play one delivery of the match:
        User selects 0-6.
        Computer generates 0-6.
        If numbers match -> OUT!
        If numbers differ -> Batsman scores their chosen number of runs.
        """
        if self.phase not in ["innings1", "innings2"]:
            raise ValueError(f"Cannot bowl delivery during match phase: {self.phase}")

        if not (0 <= user_number <= 6):
            raise ValueError("Input must be between 0 and 6.")

        current_inn = self.innings1 if self.current_innings == 1 else self.innings2
        user_is_batting = (self.current_batting_team == "user")

        # Context for AI
        target_rem = None
        balls_rem = None
        if self.current_innings == 2 and self.target is not None:
            target_rem = max(0, self.target - current_inn["runs"])
            if self.max_overs > 0:
                balls_rem = max(0, (self.max_overs * 6) - current_inn["balls"])

        comp_number = self._ai_choose_number(
            is_batting=not user_is_batting,
            target_remaining=target_rem,
            balls_remaining=balls_rem
        )

        batsman_number = user_number if user_is_batting else comp_number
        bowler_number = comp_number if user_is_batting else user_number

        # Ball processing
        is_wicket = (batsman_number == bowler_number)
        runs_scored = 0 if is_wicket else batsman_number

        current_inn["balls"] += 1
        over_num = (current_inn["balls"] - 1) // 6
        ball_in_over = ((current_inn["balls"] - 1) % 6) + 1
        current_inn["overs"] = f"{current_inn['balls'] // 6}.{current_inn['balls'] % 6}"

        if is_wicket:
            current_inn["wickets"] += 1
            event_type = "W"
            comm = random.choice(self.COMMENTARY_LINES["wicket"])
        else:
            current_inn["runs"] += runs_scored
            event_type = str(runs_scored)
            if runs_scored == 0:
                comm = random.choice(self.COMMENTARY_LINES["dot"])
            elif runs_scored == 1:
                comm = random.choice(self.COMMENTARY_LINES["one"])
            elif runs_scored == 2:
                comm = random.choice(self.COMMENTARY_LINES["two"])
            elif runs_scored == 3:
                comm = random.choice(self.COMMENTARY_LINES["three"])
            elif runs_scored == 4:
                comm = random.choice(self.COMMENTARY_LINES["four"])
            elif runs_scored == 5:
                comm = random.choice(self.COMMENTARY_LINES["five"])
            else:
                comm = random.choice(self.COMMENTARY_LINES["six"])

        ball_data = {
            "over": f"{over_num}.{ball_in_over}",
            "batting_team": self.current_batting_team,
            "user_number": user_number,
            "comp_number": comp_number,
            "batsman_number": batsman_number,
            "bowler_number": bowler_number,
            "runs": runs_scored,
            "is_wicket": is_wicket,
            "total_runs": current_inn["runs"],
            "total_wickets": current_inn["wickets"],
            "event": event_type,
            "commentary": comm
        }
        current_inn["timeline"].append(ball_data)

        # Check for Innings/Match conclusion conditions
        innings_over = False
        reason = ""

        # Condition 1: All wickets lost
        if current_inn["wickets"] >= self.max_wickets:
            innings_over = True
            reason = f"All {self.max_wickets} wickets lost!"

        # Condition 2: Max overs reached (if limited overs)
        elif self.max_overs > 0 and current_inn["balls"] >= (self.max_overs * 6):
            innings_over = True
            reason = f"Overs limit of {self.max_overs} overs reached!"

        # Condition 3: Original cap of 200 runs
        elif current_inn["runs"] >= 200:
            innings_over = True
            reason = "Maximum runs limit (200) reached!"

        # Condition 4: Innings 2 Chased Target successfully
        if self.current_innings == 2 and self.target is not None:
            if current_inn["runs"] >= self.target:
                innings_over = True
                reason = "Target chased down successfully!"

        if innings_over:
            if self.current_innings == 1:
                self._transition_to_innings2()
            else:
                self._finish_match()

        return {
            "ball": ball_data,
            "innings": self.current_innings,
            "phase": self.phase,
            "innings_over": innings_over,
            "innings_over_reason": reason,
            "score": self.get_scoreboard()
        }

    def _transition_to_innings2(self):
        """Prepares the match for second innings chasing target."""
        self.target = self.innings1["runs"] + 1
        self.current_innings = 2
        self.current_batting_team = "computer" if self.first_batting_team == "user" else "user"
        self.phase = "innings2"

    def _finish_match(self):
        """Concludes match and calculates winner and margin."""
        self.phase = "completed"

        if self.first_batting_team == "user":
            user_runs = self.innings1["runs"]
            comp_runs = self.innings2["runs"]
            user_wickets_lost = self.innings1["wickets"]
            comp_wickets_lost = self.innings2["wickets"]
        else:
            comp_runs = self.innings1["runs"]
            user_runs = self.innings2["runs"]
            comp_wickets_lost = self.innings1["wickets"]
            user_wickets_lost = self.innings2["wickets"]

        self.user_total_runs = user_runs
        self.computer_total_runs = comp_runs

        if user_runs > comp_runs:
            self.winner = "user"
            self.runs_difference = user_runs - comp_runs
            if self.first_batting_team == "user":
                self.result_summary = f"You won by {self.runs_difference} runs!"
            else:
                wickets_left = self.max_wickets - user_wickets_lost
                self.wickets_difference = wickets_left
                self.result_summary = f"You won by {wickets_left} {'wicket' if wickets_left == 1 else 'wickets'}!"
        elif comp_runs > user_runs:
            self.winner = "computer"
            self.runs_difference = comp_runs - user_runs
            if self.first_batting_team == "computer":
                self.result_summary = f"{self.ai_name} won by {self.runs_difference} runs!"
            else:
                wickets_left = self.max_wickets - comp_wickets_lost
                self.wickets_difference = wickets_left
                self.result_summary = f"{self.ai_name} won by {wickets_left} {'wicket' if wickets_left == 1 else 'wickets'}!"
        else:
            self.winner = "draw"
            self.runs_difference = 0
            self.result_summary = "Match Tied! A thrilling Draw!"

    def get_scoreboard(self) -> Dict[str, Any]:
        """Provides full structured data for the live scoreboard."""
        current_inn = self.innings1 if self.current_innings == 1 else self.innings2
        runs_needed = None
        balls_left = None
        req_run_rate = None

        if self.current_innings == 2 and self.target is not None:
            runs_needed = max(0, self.target - current_inn["runs"])
            if self.max_overs > 0:
                total_balls = self.max_overs * 6
                balls_left = max(0, total_balls - current_inn["balls"])
                if balls_left > 0:
                    req_run_rate = round((runs_needed / balls_left) * 6, 2)

        curr_overs_float = (current_inn["balls"] // 6) + ((current_inn["balls"] % 6) / 6)
        curr_run_rate = round(current_inn["runs"] / curr_overs_float, 2) if curr_overs_float > 0 else 0.0

        return {
            "mode": self.mode,
            "mode_name": self.mode_name,
            "phase": self.phase,
            "current_innings": self.current_innings,
            "batting_team": self.current_batting_team,
            "bowling_team": "computer" if self.current_batting_team == "user" else "user",
            "ai_name": self.ai_name,
            "runs": current_inn["runs"],
            "wickets": current_inn["wickets"],
            "max_wickets": self.max_wickets,
            "overs": current_inn["overs"],
            "max_overs": self.max_overs,
            "target": self.target,
            "runs_needed": runs_needed,
            "balls_left": balls_left,
            "run_rate": curr_run_rate,
            "req_run_rate": req_run_rate,
            "innings1": {
                "batting_team": self.innings1["batting_team"],
                "runs": self.innings1["runs"],
                "wickets": self.innings1["wickets"],
                "overs": self.innings1["overs"],
                "timeline_last": self.innings1["timeline"][-6:] if self.innings1["timeline"] else []
            },
            "innings2": {
                "batting_team": self.innings2["batting_team"],
                "runs": self.innings2["runs"],
                "wickets": self.innings2["wickets"],
                "overs": self.innings2["overs"],
                "timeline_last": self.innings2["timeline"][-6:] if self.innings2["timeline"] else []
            },
            "winner": self.winner,
            "result_summary": self.result_summary,
            "user_total_runs": self.user_total_runs,
            "computer_total_runs": self.computer_total_runs
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serializes game state for session or database storage."""
        return {
            "mode": self.mode,
            "mode_name": self.mode_name,
            "max_overs": self.max_overs,
            "max_wickets": self.max_wickets,
            "ai_name": self.ai_name,
            "phase": self.phase,
            "toss_choice": self.toss_choice,
            "toss_user_num": self.toss_user_num,
            "toss_comp_num": self.toss_comp_num,
            "toss_sum": self.toss_sum,
            "toss_sum_parity": self.toss_sum_parity,
            "toss_winner": self.toss_winner,
            "user_decision": self.user_decision,
            "comp_decision": self.comp_decision,
            "current_innings": self.current_innings,
            "first_batting_team": self.first_batting_team,
            "current_batting_team": self.current_batting_team,
            "target": self.target,
            "innings1": self.innings1,
            "innings2": self.innings2,
            "winner": self.winner,
            "result_summary": self.result_summary,
            "runs_difference": self.runs_difference,
            "wickets_difference": self.wickets_difference,
            "user_total_runs": self.user_total_runs,
            "computer_total_runs": self.computer_total_runs
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CricketGame':
        """Restores a game instance from a serialized dictionary."""
        game = cls(mode=data.get("mode", "quick"), custom_wickets=data.get("max_wickets", 2), ai_name=data.get("ai_name"))
        game.mode_name = data.get("mode_name", game.mode_name)
        game.max_overs = data.get("max_overs", game.max_overs)
        game.max_wickets = data.get("max_wickets", game.max_wickets)
        game.phase = data.get("phase", "toss")
        game.toss_choice = data.get("toss_choice")
        game.toss_user_num = data.get("toss_user_num")
        game.toss_comp_num = data.get("toss_comp_num")
        game.toss_sum = data.get("toss_sum")
        game.toss_sum_parity = data.get("toss_sum_parity")
        game.toss_winner = data.get("toss_winner")
        game.user_decision = data.get("user_decision")
        game.comp_decision = data.get("comp_decision")
        game.current_innings = data.get("current_innings", 1)
        game.first_batting_team = data.get("first_batting_team")
        game.current_batting_team = data.get("current_batting_team")
        game.target = data.get("target")
        game.innings1 = data.get("innings1", game.innings1)
        game.innings2 = data.get("innings2", game.innings2)
        game.winner = data.get("winner")
        game.result_summary = data.get("result_summary", "")
        game.runs_difference = data.get("runs_difference", 0)
        game.wickets_difference = data.get("wickets_difference", 0)
        game.user_total_runs = data.get("user_total_runs", 0)
        game.computer_total_runs = data.get("computer_total_runs", 0)
        return game
