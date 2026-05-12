"""
game/paddle.py — Visual paddle nodes (player = coral-red, AI = cyan).
Redesigned to perfectly match the reference image: flat, top-down arcade style
with thick black outlines and color-matched handles.
"""
from panda3d.core import NodePath
import config as C
from game.geometry_utils import create_cylinder, create_box

class Paddle:
    def __init__(self, render, is_player: bool):
        self.render = render
        self.is_player = is_player
        color = C.COLOR_PLAYER_PADDLE if is_player else C.COLOR_AI_PADDLE
        black = (0.05, 0.05, 0.05, 1)

        # Root node
        self.node = render.attachNewNode(
            'player_paddle' if is_player else 'ai_paddle'
        )

        # ── Paddle Face ───────────────────────────────────────────────────────
        # The cylinder is generated along Z by default (a horizontal disc).
        # We rotate it 90° around X so its flat circular face points along Y
        # (toward the opponent) — the correct hitting surface orientation.

        # Black outline (slightly larger, thin depth)
        face_outline = create_cylinder('face_out', C.PADDLE_RADIUS + 0.025, 0.012,
                                       segments=32, color=black)
        face_outline.reparentTo(self.node)
        face_outline.setP(90)   # rotate 90° about X-axis (Pitch) → flat face parallel to net

        # Colored face
        face = create_cylinder('face', C.PADDLE_RADIUS, 0.018,
                               segments=32, color=color)
        face.reparentTo(self.node)
        face.setP(90)           # same rotation

        # ── Handle (box extending behind the paddle face) ──────────────────────
        hw, hh, hl = 0.04, 0.12, 0.018  # width (X), height (Z), length (Y)

        # Black outline for handle
        handle_outline = create_box('handle_out', hw + 0.025, hl + 0.01, hh + 0.025, color=black)
        handle_outline.reparentTo(self.node)

        # Colored handle
        handle = create_box('handle', hw, hl, hh, color=color)
        handle.reparentTo(self.node)

        if is_player:
            # Handle extends behind the paddle face (toward player, -Y)
            y_offset = -(C.PADDLE_RADIUS + hl / 2 + 0.01)
            handle.setPos(0, y_offset, 0)
            handle_outline.setPos(0, y_offset, 0)
            self.node.setPos(0, C.PLAYER_PADDLE_Y, 0.15)
        else:
            # Handle extends behind the paddle face (toward AI, +Y)
            y_offset = (C.PADDLE_RADIUS + hl / 2 + 0.01)
            handle.setPos(0, y_offset, 0)
            handle_outline.setPos(0, y_offset, 0)
            self.node.setPos(0, C.AI_PADDLE_Y, 0.15)

    def update(self, x: float, y: float, z: float):
        self.node.setPos(x, y, z)

    def get_pos(self):
        p = self.node.getPos()
        return p.x, p.y, p.z

