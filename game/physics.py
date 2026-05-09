"""
game/physics.py — Ball physics: gravity, drag, collisions (no spin).
Runs at PHYSICS_HZ ticks/sec via fixed-timestep accumulator in main loop.
"""
import math
import config as C


class BallState:
    __slots__ = ('x', 'y', 'z', 'vx', 'vy', 'vz', 'in_play', 'bounced_on_side')

    def __init__(self):
        self.reset()

    def reset(self):
        self.x = 0.0
        self.y = -C.TABLE_HALF_L + 0.3   # player side
        self.z = 0.25
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.in_play = False
        # 'player' or 'ai' — which half the ball last bounced on
        self.bounced_on_side = None

    @property
    def pos(self):
        return (self.x, self.y, self.z)

    @property
    def vel(self):
        return (self.vx, self.vy, self.vz)

    def set_pos(self, x, y, z):
        self.x, self.y, self.z = x, y, z

    def set_vel(self, vx, vy, vz):
        self.vx, self.vy, self.vz = vx, vy, vz


class PhysicsEngine:
    """
    Integrates ball motion with Euler method at PHYSICS_DT steps.
    Handles: table bounce, net collision, out-of-bounds detection.
    """

    # Return codes from step()
    ONGOING    = 0
    POINT_AI   = 1   # player missed / ball out on player side
    POINT_PLAYER = 2   # AI missed / ball out on AI side

    def __init__(self):
        pass

    # ── Main Step ─────────────────────────────────────────────────────────────
    def step(self, ball: BallState) -> int:
        if not ball.in_play:
            return self.ONGOING

        dt = C.PHYSICS_DT
        vx, vy, vz = ball.vx, ball.vy, ball.vz

        # Speed magnitude
        spd = math.sqrt(vx*vx + vy*vy + vz*vz)

        # Drag deceleration (opposing velocity direction)
        if spd > 0.001:
            drag = C.DRAG_K * spd      # magnitude of drag acceleration
            ax = -drag * vx
            ay = -drag * vy
            az = -drag * vz + C.GRAVITY
        else:
            ax, ay, az = 0, 0, C.GRAVITY

        # Euler integrate velocity
        ball.vx += ax * dt
        ball.vy += ay * dt
        ball.vz += az * dt

        # Cap speed
        spd_new = math.sqrt(ball.vx**2 + ball.vy**2 + ball.vz**2)
        if spd_new > C.MAX_BALL_SPEED:
            scale = C.MAX_BALL_SPEED / spd_new
            ball.vx *= scale; ball.vy *= scale; ball.vz *= scale

        # Euler integrate position
        ball.x += ball.vx * dt
        ball.y += ball.vy * dt
        ball.z += ball.vz * dt

        # ── Collision checks ──────────────────────────────────────────────────

        result = self._check_table(ball)
        if result != self.ONGOING:
            return result

        result = self._check_net(ball)
        if result != self.ONGOING:
            return result

        result = self._check_bounds(ball)
        return result

    # ── Table Bounce ─────────────────────────────────────────────────────────
    def _check_table(self, ball: BallState) -> int:
        if ball.z - C.BALL_RADIUS > 0:
            return self.ONGOING                      # still airborne

        # Ball has reached table level — is it over the table?
        on_table = (abs(ball.x) <= C.TABLE_HALF_W and
                    abs(ball.y) <= C.TABLE_HALF_L)

        if not on_table:
            return self.ONGOING  # let bounds check handle it

        # ── Bounce ────────────────────────────────────────────────────────────
        ball.z = C.BALL_RADIUS                       # push out of surface
        ball.vz = -ball.vz * C.COR_TABLE             # reflect Z velocity
        ball.vx *= C.FRICTION_TABLE
        ball.vy *= C.FRICTION_TABLE

        # Record which half the bounce happened on
        if ball.vy > 0 or ball.y > 0:
            ball.bounced_on_side = 'ai'
        else:
            ball.bounced_on_side = 'player'

        return self.ONGOING

    # ── Net Collision ─────────────────────────────────────────────────────────
    def _check_net(self, ball: BallState) -> int:
        """Stop ball if it hits the net."""
        if abs(ball.y) > 0.02:
            return self.ONGOING            # not near net plane

        if ball.z < C.NET_HEIGHT + C.BALL_RADIUS:
            # Hit the net — award point to whoever's side the ball came FROM
            # If ball was travelling from player (vy>0) → AI gets point
            if ball.vy > 0:
                ball.in_play = False
                return self.POINT_AI
            else:
                ball.in_play = False
                return self.POINT_PLAYER

        return self.ONGOING

    # ── Out-of-Bounds ─────────────────────────────────────────────────────────
    def _check_bounds(self, ball: BallState) -> int:
        # Ball fell below table level without hitting table → off the edge
        if ball.z < -0.3:
            ball.in_play = False
            # Who loses the point depends on last side
            if ball.bounced_on_side == 'ai':
                # bounced AI side → AI failed to return → player scores
                return self.POINT_PLAYER
            else:
                return self.POINT_AI

        # Ball left the far end (AI side)
        if ball.y > C.TABLE_HALF_L + 0.3:
            ball.in_play = False
            if ball.bounced_on_side == 'ai':
                return self.POINT_PLAYER    # ball went over AI end
            return self.POINT_AI

        # Ball left the near end (player side)
        if ball.y < -C.TABLE_HALF_L - 0.3:
            ball.in_play = False
            if ball.bounced_on_side == 'player':
                return self.POINT_AI        # player missed return
            return self.POINT_PLAYER

        # Ball left the side
        if abs(ball.x) > C.TABLE_HALF_W + 0.5:
            ball.in_play = False
            # Attribute to whoever hit it last (simplified: use vy direction)
            return self.POINT_AI if ball.vy > 0 else self.POINT_PLAYER

        return self.ONGOING

    # ── Paddle Hit ───────────────────────────────────────────────────────────
    def apply_paddle_hit(self, ball: BallState,
                         paddle_x, paddle_y, paddle_z,
                         paddle_vx, paddle_vy, paddle_vz,
                         power: float = 1.0):
        """
        Reflect ball off paddle.
        Called by player input handler or AI when collision detected.
        power: 0.5 – 1.5 multiplier on outgoing speed.
        """
        # Direction from paddle to opponent
        if paddle_y < 0:
            dir_y = 1.0   # player hitting toward AI
        else:
            dir_y = -1.0  # AI hitting toward player

        # Outgoing speed based on incoming + paddle velocity + power
        in_spd = math.sqrt(ball.vx**2 + ball.vy**2 + ball.vz**2)
        out_spd = max(4.0, min(in_spd + abs(paddle_vy) * 2, C.MAX_BALL_SPEED)) * power

        # Angle: controlled by where on paddle the ball was hit
        dx = ball.x - paddle_x
        dz = ball.z - paddle_z
        angle_x = dx / (C.PADDLE_RADIUS + 0.01)   # -1 to 1
        angle_z = dz / (C.PADDLE_RADIUS + 0.01)

        # Outgoing direction (mostly Y, some X tilt, slight upward arc)
        vx_out = angle_x * 2.5 + paddle_vx * 0.5
        vz_out = max(1.0, 2.0 + angle_z * 1.0) + abs(paddle_vz) * 0.3
        vy_out = dir_y * math.sqrt(max(0, out_spd**2 - vx_out**2 - vz_out**2))

        ball.set_vel(vx_out, vy_out, vz_out)
        ball.in_play = True

    # ── Trajectory Predictor (used by AI) ────────────────────────────────────
    def predict_landing(self, ball: BallState, target_y: float,
                        max_steps: int = 500):
        """
        Integrate a COPY of the ball state forward until Y reaches target_y.
        Returns (x, z) of predicted hit point, or None if ball doesn't reach.
        """
        # Shallow copy
        px, py, pz = ball.x, ball.y, ball.z
        pvx, pvy, pvz = ball.vx, ball.vy, ball.vz
        dt = C.PHYSICS_DT

        for _ in range(max_steps):
            spd = math.sqrt(pvx*pvx + pvy*pvy + pvz*pvz)
            if spd > 0.001:
                drag = C.DRAG_K * spd
                pvx += (-drag * pvx) * dt
                pvy += (-drag * pvy) * dt
                pvz += (C.GRAVITY - drag * pvz) * dt
            else:
                pvz += C.GRAVITY * dt

            px += pvx * dt
            py += pvy * dt
            pz += pvz * dt

            # Bounce off table
            if pz - C.BALL_RADIUS <= 0 and abs(px) <= C.TABLE_HALF_W and abs(py) <= C.TABLE_HALF_L:
                pz = C.BALL_RADIUS
                pvz = -pvz * C.COR_TABLE
                pvx *= C.FRICTION_TABLE
                pvy *= C.FRICTION_TABLE

            # Crossed target Y
            if (pvy > 0 and py >= target_y) or (pvy < 0 and py <= target_y):
                return px, pz

        return None
