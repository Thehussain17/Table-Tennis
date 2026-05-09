"""
game/confetti.py — 2D confetti particle burst for point/win celebrations.
Uses small CardMaker quads in aspect2d (screen-space overlay).
"""
import random
import math
from panda3d.core import CardMaker, NodePath


CONFETTI_COLORS = [
    (1.00, 0.25, 0.25, 1),   # red
    (0.25, 0.85, 0.30, 1),   # green
    (0.25, 0.55, 1.00, 1),   # blue
    (1.00, 0.90, 0.15, 1),   # yellow
    (0.90, 0.25, 0.95, 1),   # purple
    (1.00, 0.55, 0.10, 1),   # orange
    (0.20, 0.95, 0.95, 1),   # cyan
    (1.00, 0.40, 0.75, 1),   # pink
]


class Confetti:
    """
    Call burst() to launch confetti.
    Call update(dt) every frame (returns early when inactive).
    """

    def __init__(self, aspect2d, count: int = 90):
        self.aspect2d = aspect2d
        self._active  = False
        self._timer   = 0.0
        self._pieces  = []

        for i in range(count):
            sz = random.uniform(0.018, 0.045)
            cm = CardMaker(f'conf_{i}')
            cm.setFrame(-sz, sz, -sz * 1.6, sz * 1.6)   # rectangular pieces
            np = aspect2d.attachNewNode(cm.generate())
            np.setColor(*random.choice(CONFETTI_COLORS))
            np.setTransparency(True)
            np.hide()
            self._pieces.append({
                'np':  np,
                'vx':  0.0,
                'vz':  0.0,
                'rot': 0.0,
                'rot_spd': 0.0,
                'alive': False,
            })

    # ── Public API ────────────────────────────────────────────────────────────

    def burst(self, duration: float = 3.5):
        """Spawn all pieces from random positions near the top."""
        self._active = True
        self._timer  = duration
        for p in self._pieces:
            np = p['np']
            np.setColor(*random.choice(CONFETTI_COLORS))
            x0 = random.uniform(-1.2, 1.2)
            z0 = random.uniform(0.6, 1.1)
            np.setPos(x0, 0, z0)
            p['vx']      = random.uniform(-0.55, 0.55)
            p['vz']      = random.uniform(-0.15, 0.45)   # burst upward first
            p['rot']     = random.uniform(0, 360)
            p['rot_spd'] = random.uniform(-280, 280)
            p['alive']   = True
            np.setR(p['rot'])
            np.show()

    def stop(self):
        self._active = False
        for p in self._pieces:
            p['np'].hide()
            p['alive'] = False

    def update(self, dt: float):
        if not self._active:
            return
        self._timer -= dt
        if self._timer <= 0:
            self.stop()
            return

        for p in self._pieces:
            if not p['alive']:
                continue
            np = p['np']
            x, _, z = np.getPos()
            # Gravity + slight horizontal damping
            p['vz'] -= 1.5 * dt
            p['vx'] *= (1 - 0.6 * dt)
            x += p['vx'] * dt
            z += p['vz'] * dt
            p['rot'] += p['rot_spd'] * dt
            np.setPos(x, 0, z)
            np.setR(p['rot'])
            # Fade out near bottom or when timer low
            alpha = min(1.0, self._timer * 1.5)
            r, g, b, _ = np.getColor()
            np.setColor(r, g, b, alpha)
            if z < -1.3:
                np.hide()
                p['alive'] = False

    def cleanup(self):
        for p in self._pieces:
            p['np'].removeNode()
        self._pieces.clear()
