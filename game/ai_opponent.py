"""
game/ai_opponent.py — Arcade-style AI opponent.
Tracks ball position with speed limits based on difficulty.
Extremely responsive and fun to play against.
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

        self._hit_cooldown = 0.0

    def set_difficulty(self, difficulty: str):
        self.difficulty = difficulty
        self.profile    = C.AI_PROFILES[difficulty]

    def update(self, dt: float, ball: BallState) -> bool:
        if self._hit_cooldown > 0:
            self._hit_cooldown -= dt

        hit = False

        if not ball.in_play:
            # Return to center
            self._move_towards(0.0, 0.15, dt, speed_mult=0.5)
            return False

        # If ball is coming towards AI
        if ball.vy > 0:
            # Add some error margin based on difficulty
            error_margin = self.profile['error']
            target_x = ball.x + math.sin(ball.y * 5) * error_margin
            target_z = max(C.PADDLE_MIN_Z, min(C.PADDLE_MAX_Z, ball.z))
            
            self._move_towards(target_x, target_z, dt, speed_mult=self.profile['speed'] * 2.5)

            # Try to hit if close enough
            if self._hit_cooldown <= 0 and ball.y > 0.5:
                dx = ball.x - self.px
                dy = ball.y - self.py
                dz = ball.z - self.pz
                dist = math.sqrt(dx*dx + dy*dy + dz*dz)

                if dist < C.PADDLE_RADIUS * 2.0:
                    hit = self._try_hit(ball)
                    if hit:
                        self._hit_cooldown = 0.5
        else:
            # Ball moving away, return to center slowly
            self._move_towards(0.0, 0.15, dt, speed_mult=0.5)

        # Clamp paddle within reasonable bounds
        self.px = max(-C.PADDLE_MAX_X, min(C.PADDLE_MAX_X, self.px))
        self.pz = max(C.PADDLE_MIN_Z, min(C.PADDLE_MAX_Z, self.pz))

        return hit

    def _move_towards(self, tx: float, tz: float, dt: float, speed_mult: float):
        max_v = C.PADDLE_SPEED * speed_mult
        dx = tx - self.px
        dz = tz - self.pz
        dist = math.sqrt(dx*dx + dz*dz)
        
        if dist > 0.005:
            step = min(dist, max_v * dt)
            self.vx = (dx / dist) * step / dt
            self.vz = (dz / dist) * step / dt
            self.px += (dx / dist) * step
            self.pz += (dz / dist) * step
        else:
            self.vx = 0
            self.vz = 0

    def _try_hit(self, ball: BallState) -> bool:
        bx = ball.x
        aim_x = self._choose_aim_x()
        power = random.uniform(0.7, 0.95) # Reduced power to prevent out-of-bounds
        
        self.vy = -2.8 # Fast enough to clear net
        self.physics.apply_paddle_hit(
            ball,
            self.px, self.py, self.pz,
            self.vx, self.vy, 0,
            power
        )
        ball.vx = (aim_x - bx) * 2.0
        ball.vz = 2.0 # Controlled arc so it drops reliably onto the table
        return True

    def _choose_aim_x(self) -> float:
        if self.difficulty == 'Easy':
            return random.uniform(-0.2, 0.2)
        elif self.difficulty == 'Medium':
            return random.uniform(-0.6, 0.6)
        else:  # Hard
            # Strategic: aim at edges
            return random.choice([-C.TABLE_HALF_W*0.9, C.TABLE_HALF_W*0.9])

    def reset_to_idle(self):
        self._hit_cooldown = 0.0
