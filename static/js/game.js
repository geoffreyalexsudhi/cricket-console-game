/**
 * Cricket Clash - Stadium Game Client Engine
 * Handles user interactions, audio effects, server-authoritative deliveries,
 * animations, live scoreboard rendering, and match completion celebrations.
 */

class CricketGameClient {
  constructor() {
    this.audioEnabled = localStorage.getItem('cricket_sound') !== 'false';
    this.audioCtx = null;
    this.selectedTossCall = 1; // 1: Odd, 2: Even
    this.selectedTossNum = 3;
    this.isProcessing = false;
    this.currentState = null;

    this.initAudio();
    this.bindEvents();
    this.fetchInitialState();
  }

  // --- Web Audio Synthesizer (Zero External Dependencies) ---
  initAudio() {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) {
        this.audioCtx = new AudioContext();
      }
    } catch (e) {
      console.warn("Web Audio API not supported", e);
    }
  }

  resumeAudio() {
    if (this.audioCtx && this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
  }

  playSound(type) {
    if (!this.audioEnabled || !this.audioCtx) return;
    this.resumeAudio();

    const t = this.audioCtx.currentTime;
    const osc = this.audioCtx.createOscillator();
    const gain = this.audioCtx.createGain();
    osc.connect(gain);
    gain.connect(this.audioCtx.destination);

    if (type === 'bat') {
      // Wood crack sound
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(320, t);
      osc.frequency.exponentialRampToValueAtTime(80, t + 0.08);
      gain.gain.setValueAtTime(0.8, t);
      gain.gain.exponentialRampToValueAtTime(0.01, t + 0.08);
      osc.start(t);
      osc.stop(t + 0.08);
    } else if (type === 'four') {
      // Cheerful chime
      osc.type = 'sine';
      osc.frequency.setValueAtTime(440, t);
      osc.frequency.setValueAtTime(554.37, t + 0.1);
      osc.frequency.setValueAtTime(659.25, t + 0.2);
      gain.gain.setValueAtTime(0.5, t);
      gain.gain.exponentialRampToValueAtTime(0.01, t + 0.4);
      osc.start(t);
      osc.stop(t + 0.4);
    } else if (type === 'six') {
      // High celebratory chime
      osc.type = 'sine';
      osc.frequency.setValueAtTime(523.25, t);
      osc.frequency.setValueAtTime(659.25, t + 0.12);
      osc.frequency.setValueAtTime(783.99, t + 0.24);
      osc.frequency.setValueAtTime(1046.50, t + 0.36);
      gain.gain.setValueAtTime(0.6, t);
      gain.gain.exponentialRampToValueAtTime(0.01, t + 0.6);
      osc.start(t);
      osc.stop(t + 0.6);
    } else if (type === 'wicket') {
      // Stumps shattered crash
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(220, t);
      osc.frequency.exponentialRampToValueAtTime(40, t + 0.35);
      gain.gain.setValueAtTime(0.9, t);
      gain.gain.exponentialRampToValueAtTime(0.01, t + 0.35);
      osc.start(t);
      osc.stop(t + 0.35);
    } else if (type === 'win') {
      // Fanfare
      const notes = [440, 554, 659, 880];
      notes.forEach((freq, idx) => {
        const o = this.audioCtx.createOscillator();
        const g = this.audioCtx.createGain();
        o.connect(g);
        g.connect(this.audioCtx.destination);
        o.frequency.value = freq;
        g.gain.setValueAtTime(0.4, t + (idx * 0.12));
        g.gain.exponentialRampToValueAtTime(0.01, t + (idx * 0.12) + 0.3);
        o.start(t + (idx * 0.12));
        o.stop(t + (idx * 0.12) + 0.3);
      });
    }
  }

  // --- UI Event Listeners ---
  bindEvents() {
    // Sound Toggle
    const soundBtn = document.getElementById('toggleSoundBtn');
    if (soundBtn) {
      soundBtn.addEventListener('click', () => {
        this.audioEnabled = !this.audioEnabled;
        localStorage.setItem('cricket_sound', this.audioEnabled);
        soundBtn.textContent = this.audioEnabled ? '🔊 Sound On' : '🔇 Muted';
      });
    }

    // Toss Call Buttons (Odd / Even)
    document.querySelectorAll('.toss-choice-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.toss-choice-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        this.selectedTossCall = parseInt(btn.dataset.call, 10);
      });
    });

    // Toss Number Buttons (0-6)
    document.querySelectorAll('.toss-num-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.toss-num-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        this.selectedTossNum = parseInt(btn.dataset.num, 10);
      });
    });

    // Play Toss Button
    const playTossBtn = document.getElementById('playTossBtn');
    if (playTossBtn) {
      playTossBtn.addEventListener('click', () => this.handlePlayToss());
    }

    // Toss Bat / Bowl Decision Buttons
    const chooseBatBtn = document.getElementById('chooseBatBtn');
    const chooseBowlBtn = document.getElementById('chooseBowlBtn');
    if (chooseBatBtn) chooseBatBtn.addEventListener('click', () => this.handleTossDecision('bat'));
    if (chooseBowlBtn) chooseBowlBtn.addEventListener('click', () => this.handleTossDecision('bowl'));

    // Delivery Shot Buttons (0-6)
    document.querySelectorAll('.shot-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const num = parseInt(btn.dataset.num, 10);
        this.handleDelivery(num);
      });
    });

    // Keyboard Shortcuts (0-6 keys)
    window.addEventListener('keydown', (e) => {
      if (['0', '1', '2', '3', '4', '5', '6'].includes(e.key)) {
        const num = parseInt(e.key, 10);
        const tossModal = document.getElementById('tossModal');
        if (tossModal && tossModal.classList.contains('active')) {
          // Select in toss
          const b = document.querySelector(`.toss-num-btn[data-num="${num}"]`);
          if (b) b.click();
        } else {
          this.handleDelivery(num);
        }
      }
    });

    // Innings 2 start button
    const startInn2Btn = document.getElementById('startInn2Btn');
    if (startInn2Btn) {
      startInn2Btn.addEventListener('click', () => {
        document.getElementById('inningsBreakModal').classList.remove('active');
      });
    }

    // Play Again button
    const playAgainBtn = document.getElementById('playAgainBtn');
    if (playAgainBtn) {
      playAgainBtn.addEventListener('click', () => this.restartMatch());
    }
  }

  // --- Match State & API Calls ---
  async fetchInitialState() {
    try {
      const res = await fetch('/api/game/state');
      const data = await res.json();
      if (data.success) {
        this.currentState = data.state;
        this.renderState(data.state, data.phase);
      }
    } catch (err) {
      console.error("Error fetching state:", err);
    }
  }

  async handlePlayToss() {
    this.resumeAudio();
    const playTossBtn = document.getElementById('playTossBtn');
    if (playTossBtn) playTossBtn.disabled = true;

    try {
      const res = await fetch('/api/game/toss', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          call: this.selectedTossCall,
          number: this.selectedTossNum
        })
      });
      const data = await res.json();

      if (!data.success) {
        alert(data.error || "Toss failed");
        if (playTossBtn) playTossBtn.disabled = false;
        return;
      }

      this.showTossOutcome(data.toss, data.state);
    } catch (err) {
      console.error(err);
      if (playTossBtn) playTossBtn.disabled = false;
    }
  }

  showTossOutcome(toss, state) {
    const tossStep1 = document.getElementById('tossStep1');
    const tossStep2 = document.getElementById('tossStep2');
    const tossResultText = document.getElementById('tossResultText');

    tossStep1.style.display = 'none';
    tossStep2.style.display = 'block';

    const playerWon = (toss.winner === 'user');
    let summaryHtml = `
      <div style="font-size: 1.15rem; margin-bottom: 1rem;">
        You called <strong>${toss.user_call}</strong> and played <strong>${toss.user_number}</strong>.<br/>
        Computer played <strong>${toss.comp_number}</strong>.<br/>
        <span style="color: var(--accent);">Sum is ${toss.toss_sum} (${toss.sum_parity.toUpperCase()})!</span>
      </div>
    `;

    if (playerWon) {
      this.playSound('four');
      summaryHtml += `
        <h3 style="color: var(--primary); margin-bottom: 1rem;">🎉 YOU WON THE TOSS!</h3>
        <p style="color: var(--text-muted); margin-bottom: 1.5rem;">Choose what you would like to do first:</p>
      `;
      document.getElementById('tossDecisionButtons').style.display = 'flex';
      document.getElementById('compDecisionNotice').style.display = 'none';
    } else {
      this.playSound('wicket');
      const compDecText = toss.comp_decision === 'bat' ? 'BATTING' : 'BOWLING';
      summaryHtml += `
        <h3 style="color: #ff5252; margin-bottom: 1rem;">Computer won the toss!</h3>
      `;
      document.getElementById('tossDecisionButtons').style.display = 'none';
      const notice = document.getElementById('compDecisionNotice');
      notice.style.display = 'block';
      notice.innerHTML = `
        <p style="font-size: 1.1rem; margin-bottom: 1.25rem;">Computer decided to <strong>${compDecText}</strong> first.</p>
        <button class="btn-primary nav-btn" id="startMatchAfterCompToss" style="padding: 0.8rem 2rem;">Start Match</button>
      `;
      document.getElementById('startMatchAfterCompToss').addEventListener('click', () => {
        document.getElementById('tossModal').classList.remove('active');
        this.renderState(state, state.phase);
      });
    }

    tossResultText.innerHTML = summaryHtml;
  }

  async handleTossDecision(decision) {
    let customWickets = 3;
    const wicketsInput = document.getElementById('customWicketsInput');
    if (wicketsInput) {
      customWickets = parseInt(wicketsInput.value, 10) || 3;
    }

    try {
      const res = await fetch('/api/game/toss-decision', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, wickets: customWickets })
      });
      const data = await res.json();
      if (data.success) {
        document.getElementById('tossModal').classList.remove('active');
        this.renderState(data.state, data.state.phase);
      }
    } catch (err) {
      console.error(err);
    }
  }

  async handleDelivery(number) {
    if (this.isProcessing) return;
    this.resumeAudio();

    this.isProcessing = true;
    this.disableShotButtons(true);

    // Ball launch animation
    const ballObj = document.getElementById('pitchBall');
    if (ballObj) {
      ballObj.classList.remove('bowled');
      void ballObj.offsetWidth; // trigger reflow
      ballObj.classList.add('bowled');
    }

    try {
      const res = await fetch('/api/game/delivery', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ number })
      });
      const resData = await res.json();

      if (!resData.success) {
        alert(resData.error || "Delivery error");
        this.isProcessing = false;
        this.disableShotButtons(false);
        return;
      }

      const { ball, score, phase, innings_over, innings_over_reason } = resData.data;

      // Sound & Visual Event Pop
      this.triggerBallReaction(ball);

      // Render updated scoreboard & timeline
      this.renderDeliveryOutcome(ball, score);

      // Check for innings transition or match completion
      if (innings_over) {
        setTimeout(() => {
          if (phase === 'completed') {
            this.showMatchCompletion(score);
          } else if (phase === 'innings2') {
            this.showInningsBreak(score, innings_over_reason);
          }
        }, 900);
      }

    } catch (err) {
      console.error(err);
    } finally {
      setTimeout(() => {
        this.isProcessing = false;
        this.disableShotButtons(false);
      }, 550);
    }
  }

  triggerBallReaction(ball) {
    const pop = document.getElementById('eventPop');
    if (!pop) return;

    pop.className = 'event-pop';

    if (ball.is_wicket) {
      this.playSound('wicket');
      pop.textContent = 'OUT!';
      pop.classList.add('wicket-out', 'show');
    } else if (ball.runs === 6) {
      this.playSound('six');
      pop.textContent = '6';
      pop.classList.add('boundary-six', 'show');
    } else if (ball.runs === 4) {
      this.playSound('four');
      pop.textContent = '4';
      pop.classList.add('boundary-four', 'show');
    } else {
      this.playSound('bat');
      pop.textContent = ball.runs;
      pop.classList.add('show');
    }

    setTimeout(() => {
      pop.classList.remove('show');
    }, 700);
  }

  renderDeliveryOutcome(ball, score) {
    this.renderState(score, score.phase);

    // Append to Commentary Box
    const commList = document.getElementById('commentaryList');
    if (commList) {
      const commItem = document.createElement('div');
      let extraClass = '';
      if (ball.is_wicket) extraClass = 'comm-w';
      else if (ball.runs === 4) extraClass = 'comm-4';
      else if (ball.runs === 6) extraClass = 'comm-6';

      commItem.className = `comm-item ${extraClass}`;
      const batLabel = ball.batting_team === 'user' ? 'You' : score.ai_name;
      const bowlLabel = ball.batting_team === 'user' ? score.ai_name : 'You';

      commItem.innerHTML = `
        <div class="comm-meta">
          <span>Over ${ball.over} • ${batLabel} batting</span>
          <span>(P: ${ball.user_number} | C: ${ball.comp_number})</span>
        </div>
        <p>${ball.commentary}</p>
      `;
      commList.insertBefore(commItem, commList.firstChild);
    }
  }

  renderState(score, phase) {
    if (!score) return;
    this.currentState = score;

    // Check Toss Phase
    const tossModal = document.getElementById('tossModal');
    if (phase === 'toss' || phase === 'toss_decision') {
      if (tossModal) tossModal.classList.add('active');
      return;
    } else {
      if (tossModal) tossModal.classList.remove('active');
    }

    // Score numbers
    const runsEl = document.getElementById('dispRuns');
    const wicketsEl = document.getElementById('dispWickets');
    const oversEl = document.getElementById('dispOvers');
    const maxOversEl = document.getElementById('dispMaxOvers');
    const battingTeamEl = document.getElementById('dispBattingTeam');
    const bowlingTeamEl = document.getElementById('dispBowlingTeam');
    const targetBadge = document.getElementById('targetBadge');
    const targetNum = document.getElementById('targetNum');
    const equationText = document.getElementById('equationText');
    const runRateEl = document.getElementById('dispRunRate');

    if (runsEl) runsEl.textContent = score.runs;
    if (wicketsEl) wicketsEl.textContent = `${score.wickets}/${score.max_wickets}`;
    if (oversEl) oversEl.textContent = score.overs;
    if (maxOversEl) maxOversEl.textContent = score.max_overs > 0 ? `(${score.max_overs} ov)` : '(Endless)';

    if (runRateEl) runRateEl.textContent = `CRR: ${score.run_rate}`;

    const isUserBatting = (score.batting_team === 'user');
    if (battingTeamEl) {
      battingTeamEl.textContent = isUserBatting ? 'YOU ARE BATTING' : `${score.ai_name.toUpperCase()} BATTING`;
      battingTeamEl.style.color = isUserBatting ? 'var(--primary)' : 'var(--secondary)';
    }

    if (bowlingTeamEl) {
      bowlingTeamEl.textContent = isUserBatting ? `Bowler: ${score.ai_name}` : 'Bowler: You';
    }

    // Control instruction text
    const ctrlInstruction = document.getElementById('controlInstruction');
    if (ctrlInstruction) {
      if (isUserBatting) {
        ctrlInstruction.innerHTML = `Choose shot <strong>(0 - 6)</strong>. Score runs or risk wicket if numbers match!`;
      } else {
        ctrlInstruction.innerHTML = `Choose ball delivery <strong>(0 - 6)</strong>. Match computer's number to take a wicket!`;
      }
    }

    // Target display in 2nd Innings
    if (score.current_innings === 2 && score.target !== null) {
      if (targetBadge) targetBadge.style.display = 'block';
      if (targetNum) targetNum.textContent = score.target;

      if (equationText && score.runs_needed !== null) {
        if (score.balls_left !== null) {
          equationText.textContent = `Needs ${score.runs_needed} runs from ${score.balls_left} balls (RRR: ${score.req_run_rate || 0})`;
        } else {
          equationText.textContent = `Needs ${score.runs_needed} runs to win`;
        }
      }
    } else {
      if (targetBadge) targetBadge.style.display = 'none';
      if (equationText) equationText.textContent = `1st Innings • Setting Target`;
    }

    // Render Recent Timeline
    const timelineContainer = document.getElementById('timelineContainer');
    if (timelineContainer) {
      const activeInn = score.current_innings === 1 ? score.innings1 : score.innings2;
      timelineContainer.innerHTML = '';
      if (activeInn && activeInn.timeline_last) {
        activeInn.timeline_last.forEach(b => {
          const tag = document.createElement('div');
          tag.className = `ball-tag b-${b.event}`;
          tag.textContent = b.event;
          tag.title = `P: ${b.user_number} | C: ${b.comp_number}`;
          timelineContainer.appendChild(tag);
        });
      }
    }
  }

  showInningsBreak(score, reason) {
    this.playSound('four');
    const modal = document.getElementById('inningsBreakModal');
    const breakMsg = document.getElementById('breakMessage');
    const breakTarget = document.getElementById('breakTargetText');

    if (breakMsg) breakMsg.textContent = reason;
    if (breakTarget) {
      const chasingTeam = score.innings2.batting_team === 'user' ? 'You' : score.ai_name;
      breakTarget.innerHTML = `
        <strong>${chasingTeam}</strong> need 
        <span style="color: var(--accent); font-size: 1.8rem; font-weight: 800;">${score.target}</span> 
        runs to win!
      `;
    }

    if (modal) modal.classList.add('active');
  }

  showMatchCompletion(score) {
    const modal = document.getElementById('resultModal');
    const icon = document.getElementById('resultIcon');
    const title = document.getElementById('resultTitle');
    const summary = document.getElementById('resultSummaryText');
    const cardScores = document.getElementById('resultScorecard');

    if (score.winner === 'user') {
      this.playSound('win');
      this.launchConfetti();
      icon.textContent = '🏆';
      title.textContent = 'VICTORY!';
      title.style.color = 'var(--primary)';
    } else if (score.winner === 'computer') {
      this.playSound('wicket');
      icon.textContent = '💔';
      title.textContent = 'DEFEAT!';
      title.style.color = '#ff5252';
    } else {
      icon.textContent = '🤝';
      title.textContent = 'MATCH TIED!';
      title.style.color = 'var(--accent)';
    }

    if (summary) summary.textContent = score.result_summary;

    if (cardScores) {
      cardScores.innerHTML = `
        <div style="background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-weight: 600;">
            <span>You</span>
            <span style="color: var(--primary);">${score.user_total_runs} runs</span>
          </div>
          <div style="display: flex; justify-content: space-between; font-weight: 600;">
            <span>${score.ai_name}</span>
            <span style="color: var(--secondary);">${score.computer_total_runs} runs</span>
          </div>
        </div>
      `;
    }

    if (modal) modal.classList.add('active');
  }

  async restartMatch() {
    try {
      const mode = this.currentState ? this.currentState.mode : 'quick';
      const res = await fetch('/api/game/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode })
      });
      const data = await res.json();
      if (data.success) {
        window.location.reload();
      }
    } catch (e) {
      window.location.reload();
    }
  }

  disableShotButtons(disabled) {
    document.querySelectorAll('.shot-btn').forEach(b => b.disabled = disabled);
  }

  launchConfetti() {
    const canvas = document.getElementById('confettiCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const particles = [];
    const colors = ['#00e676', '#00b0ff', '#ffab00', '#ff1744', '#ffffff'];

    for (let i = 0; i < 90; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height * 0.4,
        size: Math.random() * 8 + 4,
        color: colors[Math.floor(Math.random() * colors.length)],
        velX: (Math.random() - 0.5) * 6,
        velY: Math.random() * 4 + 2,
        rot: Math.random() * 360,
        rotSpeed: (Math.random() - 0.5) * 8
      });
    }

    let frames = 0;
    function render() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach(p => {
        p.x += p.velX;
        p.y += p.velY;
        p.rot += p.rotSpeed;

        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rot * Math.PI) / 180);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
        ctx.restore();
      });

      frames++;
      if (frames < 140) {
        requestAnimationFrame(render);
      } else {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }
    requestAnimationFrame(render);
  }
}

// Instantiate once DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.cricketApp = new CricketGameClient();
});
