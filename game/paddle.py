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

        # ── Paddle Face (Top-down circle) ─────────────────────────────────────
        # Black outline (slightly larger, slightly lower)
        face_outline = create_cylinder('face_out', C.PADDLE_RADIUS + 0.025, 0.01,
                                       segments=32, color=black)
        face_outline.reparentTo(self.node)
        face_outline.setZ(-0.01)

        # Colored face
        face = create_cylinder('face', C.PADDLE_RADIUS, 0.015,
                               segments=32, color=color)
        face.reparentTo(self.node)

        # ── Handle ────────────────────────────────────────────────────────────
        hw, hl = 0.04, 0.12 # handle width and length
        # Black outline for handle
        handle_outline = create_box('handle_out', hw + 0.05, hl + 0.05, 0.01, color=black)
        handle_outline.reparentTo(self.node)
        handle_outline.setZ(-0.015)

        # Colored handle
        handle = create_box('handle', hw, hl, 0.015, color=color)
        handle.reparentTo(self.node)

        if is_player:
            # Handle points toward player (-Y)
            y_offset = -(C.PADDLE_RADIUS + 0.04)
            handle.setY(y_offset)
            handle_outline.setY(y_offset)
            self.node.setPos(0, C.PLAYER_PADDLE_Y, 0.15)
        else:
            # Handle points away from player (+Y)
            y_offset = (C.PADDLE_RADIUS + 0.04)
            handle.setY(y_offset)
            handle_outline.setY(y_offset)
            self.node.setPos(0, C.AI_PADDLE_Y, 0.15)

    def update(self, x: float, y: float, z: float):
        self.node.setPos(x, y, z)

    def get_pos(self):
        p = self.node.getPos()
        return p.x, p.y, p.z

