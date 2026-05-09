"""
game/ball.py — Ball visual node with speed-based trail effect.
"""
from panda3d.core import NodePath, LColor
import config as C
from game.geometry_utils import create_sphere


class Ball:
    def __init__(self, render):
        self.render = render

        # Main ball node
        self.node: NodePath = create_sphere('ball', C.BALL_RADIUS,
                                            stacks=10, slices=14,
                                            color=C.COLOR_BALL)
        self.node.reparentTo(render)
        self.node.setPos(0, -C.TABLE_HALF_L + 0.3, 0.25)

        # Trail ghosts
        self._trail: list[NodePath] = []
        for i in range(C.TRAIL_LENGTH):
            ghost = create_sphere(f'trail_{i}', C.BALL_RADIUS * 0.9,
                                  stacks=6, slices=8,
                                  color=(1.0, 0.6, 0.1, 0.0))
            ghost.reparentTo(render)
            ghost.setPos(0, -C.TABLE_HALF_L + 0.3, 0.25)
            ghost.setTransparency(True)  # enable alpha blending
            self._trail.append(ghost)

        self._history: list[tuple] = []   # recent positions

    def update(self, x: float, y: float, z: float, speed: float):
        """Call every render frame with current ball position and speed."""
        self.node.setPos(x, y, z)

        # Push into history
        self._history.append((x, y, z))
        if len(self._history) > C.TRAIL_LENGTH + 1:
            self._history.pop(0)

        # Update trail ghosts
        speed_norm = min(speed / C.MAX_BALL_SPEED, 1.0)
        for i, ghost in enumerate(self._trail):
            idx = len(self._history) - 2 - i
            if idx >= 0:
                gx, gy, gz = self._history[idx]
                ghost.setPos(gx, gy, gz)
                alpha = speed_norm * (1.0 - (i / C.TRAIL_LENGTH)) * 0.6
                ghost.setColorScale(1, 1, 1, alpha)
                ghost.show()
            else:
                ghost.hide()

    def set_visible(self, vis: bool):
        if vis:
            self.node.show()
        else:
            self.node.hide()

    def clear_trail(self):
        self._history.clear()
        for g in self._trail:
            g.hide()
