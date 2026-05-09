"""
game/match.py — Score tracking, set management, serve logic.
Best of 5 sets (first to 3). Each set: first to 11, win by 2.
Serve alternates every 2 points.
"""
import config as C


class MatchState:
    # Game-flow states
    MENU        = 'menu'
    SERVING     = 'serving'   # ball held, waiting for launch
    RALLY       = 'rally'     # ball in play
    POINT_WON   = 'point_won'
    SET_WON     = 'set_won'
    MATCH_WON   = 'match_won'
    PAUSED      = 'paused'

    def __init__(self):
        self.player_sets  = 0
        self.ai_sets      = 0
        self.player_score = 0
        self.ai_score     = 0
        self.server       = 'player'      # who serves next
        self._serve_count = 0             # serves since last switch
        self.state        = self.MENU
        self._prev_state  = None          # for pause/resume
        self.point_timer  = 0.0           # delay after point
        self.difficulty   = C.DEFAULT_DIFFICULTY
        self.match_winner = None

    # ── State helpers ─────────────────────────────────────────────────────────
    def start_new_set(self):
        self.player_score = 0
        self.ai_score     = 0
        self._serve_count = 0
        self.state        = self.SERVING

    def start_game(self):
        self.player_sets  = 0
        self.ai_sets      = 0
        self.match_winner = None
        self.start_new_set()

    def pause(self):
        if self.state != self.PAUSED:
            self._prev_state = self.state
            self.state = self.PAUSED

    def resume(self):
        if self.state == self.PAUSED and self._prev_state:
            self.state = self._prev_state

    # ── Score a point ─────────────────────────────────────────────────────────
    def score_point(self, scorer: str) -> str:
        """
        scorer: 'player' | 'ai'
        Returns 'point' | 'set' | 'match'.
        """
        if scorer == 'player':
            self.player_score += 1
        else:
            self.ai_score += 1

        # Update serve rotation
        self._serve_count += 1
        if self._serve_count >= C.SERVE_ALTERNATES:
            self._serve_count = 0
            self.server = 'ai' if self.server == 'player' else 'player'

        # Check set win
        outcome = self._check_set_win()
        return outcome

    def _check_set_win(self) -> str:
        ps, as_ = self.player_score, self.ai_score
        # Win by 2 and at least 11
        if ps >= C.POINTS_PER_SET and ps - as_ >= C.WIN_BY:
            return self._award_set('player')
        if as_ >= C.POINTS_PER_SET and as_ - ps >= C.WIN_BY:
            return self._award_set('ai')
        return 'point'

    def _award_set(self, winner: str) -> str:
        if winner == 'player':
            self.player_sets += 1
        else:
            self.ai_sets += 1
        # Check match win
        if self.player_sets >= C.SETS_TO_WIN:
            self.match_winner = 'player'
            self.state = self.MATCH_WON
            return 'match'
        if self.ai_sets >= C.SETS_TO_WIN:
            self.match_winner = 'ai'
            self.state = self.MATCH_WON
            return 'match'
        self.state = self.SET_WON
        return 'set'

    # ── Convenience ───────────────────────────────────────────────────────────
    @property
    def score_str(self) -> str:
        return f"{self.player_score}  –  {self.ai_score}"

    @property
    def sets_str(self) -> str:
        return f"Sets  {self.player_sets} – {self.ai_sets}"

    @property
    def server_str(self) -> str:
        arrow = '▶' if self.server == 'player' else '◀'
        return f"Serve: {self.server.upper()} {arrow}"
