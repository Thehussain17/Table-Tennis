"""
game/scene.py — Builds the Panda3D scene: table, net, lines, lighting, background.
"""
from panda3d.core import (
    AmbientLight, DirectionalLight, PointLight,
    LColor, Vec3, NodePath, CardMaker
)
import config as C
from game.geometry_utils import create_box, create_cylinder


class Scene:
    def __init__(self, render, loader):
        self.render = render
        self.loader = loader
        self._setup_background()
        self._setup_lighting()
        self._build_table()
        self._build_net()
        self._build_floor()

    # ── Background ────────────────────────────────────────────────────────────
    def _setup_background(self):
        from direct.showbase.ShowBase import ShowBase
        import builtins
        base = builtins.__dict__.get('base')
        if base:
            base.setBackgroundColor(*C.BG_COLOR)

    # ── Lighting ──────────────────────────────────────────────────────────────
    def _setup_lighting(self):
        r = self.render

        # Ambient fill
        al = AmbientLight('ambient')
        al.setColor(LColor(0.25, 0.25, 0.30, 1))
        r.setLight(r.attachNewNode(al))

        # Main overhead directional (slightly off-axis for depth)
        dl1 = DirectionalLight('d1')
        dl1.setColor(LColor(0.80, 0.80, 0.75, 1))
        dl1np = r.attachNewNode(dl1)
        dl1np.setHpr(20, -60, 0)
        r.setLight(dl1np)

        # Fill from player side
        dl2 = DirectionalLight('d2')
        dl2.setColor(LColor(0.25, 0.25, 0.30, 1))
        dl2np = r.attachNewNode(dl2)
        dl2np.setHpr(180, -30, 0)
        r.setLight(dl2np)

        # Stadium rim lights (point lights above table corners)
        for px, py, pz, col in [
            (-2, -2, 4, (0.5, 0.5, 0.8)),
            ( 2, -2, 4, (0.5, 0.5, 0.8)),
            (-2,  2, 4, (0.4, 0.6, 0.5)),
            ( 2,  2, 4, (0.4, 0.6, 0.5)),
        ]:
            pl = PointLight(f'pl_{px}_{py}')
            pl.setColor(LColor(*col, 1))
            pl.setAttenuation((1, 0, 0.05))
            plnp = r.attachNewNode(pl)
            plnp.setPos(px, py, pz)
            r.setLight(plnp)

        r.setShaderAuto()   # enables per-pixel lighting / shadows

    # ── Table ─────────────────────────────────────────────────────────────────
    def _build_table(self):
        r = self.render

        # ── Thick black border frame (sits around & slightly below table top)
        border_t = 0.04   # border thickness
        # Outer box slightly larger than table
        border = create_box('table_border',
                            C.TABLE_WIDTH  + border_t * 2,
                            C.TABLE_LENGTH + border_t * 2,
                            0.05,
                            C.COLOR_TABLE_EDGE)
        border.reparentTo(r)
        border.setPos(0, 0, -0.02) # Moved lower to prevent Z fighting with top

        # Table top surface (sits on top of border)
        top = create_box('table_top',
                         C.TABLE_WIDTH, C.TABLE_LENGTH, 0.03,
                         C.COLOR_TABLE)
        top.reparentTo(r)
        top.setPos(0, 0, 0.0)    # surface flush at Z=0

        # Table legs
        leg_h = 0.72
        leg_r = 0.025
        frame_col = (0.08, 0.08, 0.08, 1)   # dark legs
        for lx, ly in [(-C.TABLE_HALF_W+0.06,  C.TABLE_HALF_L-0.06),
                        ( C.TABLE_HALF_W-0.06,  C.TABLE_HALF_L-0.06),
                        (-C.TABLE_HALF_W+0.06, -C.TABLE_HALF_L+0.06),
                        ( C.TABLE_HALF_W-0.06, -C.TABLE_HALF_L+0.06)]:
            leg = create_cylinder(f'leg_{lx}_{ly}', leg_r, leg_h, color=frame_col)
            leg.reparentTo(r)
            leg.setPos(lx, ly, -leg_h/2 - 0.03)

        # White boundary lines on surface (forming a continuous inner border)
        lc = C.COLOR_LINE
        lt = 0.005
        lw = 0.035 # Thicker white lines
        # Offset from edge
        margin = 0.04
        
        # Side lines (along Y)
        for sx in [-C.TABLE_HALF_W + margin, C.TABLE_HALF_W - margin]:
            ln = create_box('sideline', lw, C.TABLE_LENGTH - margin*2, lt, lc)
            ln.reparentTo(r); ln.setPos(sx, 0, lt/2)
            
        # End lines (along X)
        for sy in [-C.TABLE_HALF_L + margin, C.TABLE_HALF_L - margin]:
            ln = create_box('endline', C.TABLE_WIDTH - margin*2 + lw, lw, lt, lc)
            ln.reparentTo(r); ln.setPos(0, sy, lt/2)
            
        # Center line (thin)
        ln = create_box('centerline_x', C.TABLE_WIDTH - margin*2, lw/2, lt, lc)
        ln.reparentTo(r); ln.setPos(0, 0, lt/2)

    # ── Net ───────────────────────────────────────────────────────────────────
    def _build_net(self):
        r = self.render
        net_w = C.TABLE_WIDTH + 0.15    # overhangs slightly
        # Net mesh (white)
        net = create_box('net', net_w, 0.01, C.NET_HEIGHT, C.COLOR_NET)
        net.reparentTo(r)
        net.setPos(0, 0, C.NET_HEIGHT / 2)

        # Net posts (dark cylinders)
        for sx in [-net_w/2, net_w/2]:
            post = create_cylinder('post', 0.015, C.NET_HEIGHT + 0.02,
                                   segments=8, color=(0.2, 0.2, 0.2, 1))
            post.reparentTo(r)
            post.setPos(sx, 0, C.NET_HEIGHT / 2)

    # ── Floor / Arena ─────────────────────────────────────────────────────────
    def _build_floor(self):
        cm = CardMaker('floor')
        cm.setFrame(-8, 8, -7, 7)
        floor = self.render.attachNewNode(cm.generate())
        floor.setP(-90)
        floor.setZ(-0.80)
        floor.setColor(*C.COLOR_FLOOR)
