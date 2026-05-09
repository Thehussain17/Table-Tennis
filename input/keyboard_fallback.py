"""
input/keyboard_fallback.py — Phase 1 keyboard controller.

Controls:
  A / D        : Move paddle left / right (X axis)
  SPACE        : Serve
  ESC          : Pause
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

    def update(self, dt: float, is_serving: bool = False):
        spd = C.PADDLE_SPEED
        prev_px = self.px

        if self.imu.is_connected:
            # Mobile IMU Control
            tilt = self.imu.get_tilt()
            # tilt is [-1, 1]. Move towards max X position based on tilt.
            # tilt=-1 is left, tilt=1 is right.
            target_px = tilt * C.PADDLE_MAX_X
            
            # Smooth movement towards target
            diff = target_px - self.px
            step = spd * 1.5 * dt # IMU moves slightly faster for responsiveness
            if abs(diff) > step:
                self.px += step if diff > 0 else -step
            else:
                self.px = target_px

            # Handle Serve from Mobile
            if is_serving and self.imu.consume_serve_action() and self.on_serve:
                self.on_serve()
        else:
            # Keyboard Fallback
            if self._keys.get('a'):
                self.px -= spd * dt
            if self._keys.get('d'):
                self.px += spd * dt

        self.px = max(-C.PADDLE_MAX_X, min(C.PADDLE_MAX_X, self.px))
        
        # Lock Y and Z for pure arcade 2D mechanics
        self.py = C.PLAYER_PADDLE_Y
        self.pz = 0.15

        self.vx = (self.px - prev_px) / dt if dt > 0 else 0
        self.vy = 0.0
        self.vz = 0.0

    def cleanup(self):
        b = self._base
        for key in ('a', 'd', 'space'):
            b.ignore(key)
            b.ignore(key + '-up')
        b.ignore('escape')

