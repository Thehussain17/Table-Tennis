"""
input/keyboard_fallback.py — Keyboard + IMU controller.

Controls:
  A / D        : Move paddle left / right (X axis)
  SPACE        : Serve
  ESC          : Pause

Z axis (height): auto-tracks ball height when ball is approaching.
The player only needs to control X positioning; the paddle height
adjusts automatically with a slight lag so skill is still required.
"""
import config as C
from input.ws_server import IMUServer


class KeyboardController:
    def __init__(self, base):
        self._base = base
        self._keys = {}

        # Paddle state
        self.px = 0.0
        self.py = C.PLAYER_PADDLE_Y
        self.pz = 0.15

        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0

        self.on_serve  = None
        self.on_pause  = None

        # Start WebSocket/HTTP servers for mobile control
        self.imu = IMUServer()
        self.imu.start()

        self._register_keys()

    def _register_keys(self):
        b = self._base
        for key in ('a', 'd', 'space'):
            b.accept(key,        self._key_down, [key])
            b.accept(key + '-up', self._key_up,  [key])
        b.accept('escape', self._pause)

    def _key_down(self, key):
        self._keys[key] = True
        if key == 'space' and self.on_serve:
            self.on_serve()

    def _key_up(self, key):
        self._keys[key] = False

    def _pause(self):
        if self.on_pause:
            self.on_pause()

    def update(self, dt: float, is_serving: bool = False, ball=None):
        """
        ball: BallState or None.
        X axis  — controlled by tilt (mobile) or A/D keys.
        Z axis  — auto-tracks ball height when ball approaches;
                  drifts back to rest height otherwise.
        """
        spd = C.PADDLE_SPEED
        prev_px = self.px
        prev_pz = self.pz

        # ── X axis (manual) ───────────────────────────────────────────────────
        if self.imu.is_connected:
            tilt = self.imu.get_tilt()          # -1..1
            target_px = tilt * C.PADDLE_MAX_X
            diff = target_px - self.px
            step = spd * 1.5 * dt
            self.px += max(-step, min(step, diff))

            if is_serving and self.imu.consume_serve_action() and self.on_serve:
                self.on_serve()
        else:
            if self._keys.get('a'):
                self.px -= spd * dt
            if self._keys.get('d'):
                self.px += spd * dt

        self.px = max(-C.PADDLE_MAX_X, min(C.PADDLE_MAX_X, self.px))

        # ── Z axis (auto-track ball height) ───────────────────────────────────
        REST_Z       = 0.15   # default paddle height
        TRACK_SPEED  = spd * 0.9   # slightly slower than full paddle speed
        RETURN_SPEED = spd * 0.5   # lazy drift back to rest

        ball_coming = (ball is not None and ball.in_play and ball.vy < 0)

        if ball_coming:
            # Clamp target Z to valid paddle range
            target_z = max(C.PADDLE_MIN_Z + 0.02,
                           min(C.PADDLE_MAX_Z - 0.02, ball.z))
            dz = target_z - self.pz
            step_z = TRACK_SPEED * dt
            self.pz += max(-step_z, min(step_z, dz))
        else:
            # Drift back to rest position
            dz = REST_Z - self.pz
            step_z = RETURN_SPEED * dt
            self.pz += max(-step_z, min(step_z, dz))

        self.pz = max(C.PADDLE_MIN_Z, min(C.PADDLE_MAX_Z, self.pz))

        # ── Fixed Y (arcade — no depth movement) ──────────────────────────────
        self.py = C.PLAYER_PADDLE_Y

        # ── Velocities (used by physics hit calc) ─────────────────────────────
        self.vx = (self.px - prev_px) / dt if dt > 0 else 0.0
        self.vy = 0.0
        self.vz = (self.pz - prev_pz) / dt if dt > 0 else 0.0

    def cleanup(self):
        b = self._base
        for key in ('a', 'd', 'space'):
            b.ignore(key)
            b.ignore(key + '-up')
        b.ignore('escape')

