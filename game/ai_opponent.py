"""
game/ai_opponent.py — Arcade-style AI opponent.
Tracks ball position with speed / reaction limits based on difficulty profile.
"""
import random
import math
import config as C
from game.physics import BallState, PhysicsEngine


class AIOpponent:
    def __init__(self, physics: PhysicsEngine, difficulty: str = C.DEFAULT_DIFFICULTY):
        self.physics    = physics
        self.difficulty = difficulty
        self.profile    = C.AI_PROFILES[difficulty]

        # Paddle state
        self.px = 0.0
        self.py = C.AI_PADDLE_Y
        self.pz = 0.15

        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0

        self._hit_cooldown    = 0.0
        self._reaction_timer  = 0.0   # AI ignores ball until reaction window passes
        self._target_x        = 0.0   # cached target (updated after reaction delay)
        self._target_z        = 0.15

    def set_difficulty(self, difficulty: str):
        self.difficulty = difficulty
        self.profile    = C.AI_PROFILES[difficulty]

    def update(self, dt: float, ball: BallState) -> bool:
        if self._hit_cooldown > 0:
            self._hit_cooldown -= dt

        hit = False

        if not ball.in_play:
            # Return to center slowly
            self._move_towards(0.0, 0.15, dt, speed_mult=0.4)
            self._reaction_timer = 0.0
            return False

        # ── Ball coming toward AI ──────────────────────────────────────────────
        if ball.vy > 0:
            self._reaction_timer += dt

            if self._reaction_timer >= self.profile['reaction']:
                error = self.profile['error']

                # Medium / Hard: predict where ball will actually land
                if self.difficulty in ('Medium', 'Hard'):
                    landing = self.physics.predict_landing(ball, C.AI_PADDLE_Y)
                    if landing is not None:
                        pred_x, pred_z = landing
                        self._target_x = pred_x + random.uniform(-error, error)
                        self._target_z = max(C.PADDLE_MIN_Z + 0.05,
                                             min(C.PADDLE_MAX_Z - 0.05, pred_z))
                    else:
                        self._target_x = ball.x + random.uniform(-error, error)
                        self._target_z = max(C.PADDLE_MIN_Z + 0.05,
                                             min(C.PADDLE_MAX_Z - 0.05, ball.z))
                else:
                    # Easy: chase current position (slow + error = natural misses)
                    self._target_x = ball.x + random.uniform(-error, error)
                    self._target_z = max(C.PADDLE_MIN_Z + 0.05,
                                         min(C.PADDLE_MAX_Z - 0.05, ball.z))

            self._move_towards(self._target_x, self._target_z, dt,
                               speed_mult=self.profile['speed'] * 2.2)

        else:
            # Ball moving away — drift back to centre
            self._reaction_timer = 0.0
            self._move_towards(0.0, 0.15, dt, speed_mult=0.35)

        # Clamp paddle
        self.px = max(-C.PADDLE_MAX_X, min(C.PADDLE_MAX_X, self.px))
        self.pz = max(C.PADDLE_MIN_Z,  min(C.PADDLE_MAX_Z, self.pz))

        return False  # hit is triggered exclusively by main.py._check_ai_hit()


    # ── Movement ──────────────────────────────────────────────────────────────
    def _move_towards(self, tx: float, tz: float, dt: float, speed_mult: float):
        max_v = C.PADDLE_SPEED * speed_mult
        dx = tx - self.px
        dz = tz - self.pz
        dist = math.sqrt(dx * dx + dz * dz)

        if dist > 0.005:
            step = min(dist, max_v * dt)
            self.vx = (dx / dist) * step / max(dt, 1e-6)
            self.vz = (dz / dist) * step / max(dt, 1e-6)
            self.px += (dx / dist) * step
            self.pz += (dz / dist) * step
        else:
            self.vx = 0.0
            self.vz = 0.0

    # ── Hit ───────────────────────────────────────────────────────────────────
    def _try_hit(self, ball: BallState) -> bool:
        """Apply hit physics. Called exclusively by main.py._check_ai_hit()."""
        p     = self.profile
        aim_x = self._choose_aim_x()
        power = random.uniform(p['hit_pmin'], p['hit_pmax'])

        # Pass -3.0 as paddle_vy directly (no stale self.vy side-effect)
        self.physics.apply_paddle_hit(
            ball,
            self.px, self.py, self.pz,
            self.vx, -3.0, self.vz,
            power
        )

        # Steer X toward aim point, respecting vx cap
        ball.vx = max(-2.0, min(2.0, (aim_x - ball.x) * 2.0))

        # Arc from difficulty profile
        ball.vz = p['hit_arc']
        return True

    def _choose_aim_x(self) -> float:
        spread = self.profile['aim_spread'] * C.TABLE_HALF_W * 0.9
        if self.difficulty == 'Hard':
            # Strategic: aim at the edge farther from player paddle X
            # (approximated by random edge choice)
            return random.choice([-spread, spread])
        return random.uniform(-spread, spread)

    def reset_to_idle(self):
        self._hit_cooldown   = 0.0
        self._reaction_timer = 0.0
