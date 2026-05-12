"""
config.py — All game constants (physics, table, network, AI, render).
"""
import math

# ─── PHYSICS ───────────────────────────────────────────────────────────────────
PHYSICS_HZ          = 120          # ticks per second
PHYSICS_DT          = 1.0 / PHYSICS_HZ

GRAVITY             = -7.5         # m/s² (lowered for fun arcade arc)
BALL_RADIUS         = 0.02         # m  (40 mm diameter)
BALL_MASS           = 0.0027       # kg (2.7 g)
DRAG_CD             = 0.5
AIR_DENSITY         = 1.2          # kg/m³
BALL_CROSS_AREA     = math.pi * BALL_RADIUS ** 2
# F_drag = DRAG_K * |v|² → divide by mass for acceleration
DRAG_K              = 0.5 * DRAG_CD * AIR_DENSITY * BALL_CROSS_AREA / BALL_MASS

COR_TABLE           = 0.89         # coefficient of restitution (table surface)
COR_PADDLE          = 0.85
FRICTION_TABLE      = 0.95         # lateral speed kept after bounce

MAX_BALL_SPEED      = 8.0          # m/s global cap (Hard hits approach this)

# ─── TABLE (real dimensions in metres) ─────────────────────────────────────────
TABLE_LENGTH        = 2.74
TABLE_WIDTH         = 1.525
TABLE_HEIGHT        = 0.0          # surface at Z = 0 (we normalise)
TABLE_HALF_L        = TABLE_LENGTH  / 2   # 1.37
TABLE_HALF_W        = TABLE_WIDTH   / 2   # 0.7625

NET_HEIGHT          = 0.1525       # m

# ─── PADDLE ────────────────────────────────────────────────────────────────────
PADDLE_RADIUS       = 0.08         # hit-box radius (m)
PADDLE_THICKNESS    = 0.01
PLAYER_PADDLE_Y     = -TABLE_HALF_L + 0.15   # fixed Y depth (player side)
AI_PADDLE_Y         =  TABLE_HALF_L - 0.15   # fixed Y depth (AI side)

PADDLE_SPEED        = 5.0          # m/s keyboard speed
PADDLE_MAX_X        = TABLE_HALF_W + 0.2
PADDLE_MIN_Z        = 0.0
PADDLE_MAX_Z        = 0.5

# Initial serve speed
SERVE_SPEED_Y       = 3.5          # m/s toward opponent  (was 2.0, too slow to arc over net)
SERVE_SPEED_Z       = 3.0          # m/s upward           (was 2.2, not enough loft)

# ─── AI ────────────────────────────────────────────────────────────────────────
AI_PROFILES = {
    # reaction  : delay before tracking starts (seconds)
    # speed     : fraction of PADDLE_SPEED used for tracking
    # error     : random positional error added to target (metres)
    # hit_pmin  : minimum power multiplier on each hit
    # hit_pmax  : maximum power multiplier on each hit
    # hit_arc   : vz applied to ball after hit (lower = flatter, faster drop)
    # aim_spread: how far from center the AI can aim (0=center, 1=full width)
    "Easy": {
        "reaction":   0.30, "speed":     0.50, "error":     0.25,
        "hit_pmin":   0.45, "hit_pmax":  0.60,
        "hit_arc":    1.9,  "aim_spread": 0.8,
    },
    "Medium": {
        "reaction":   0.25, "speed":     0.78, "error":     0.08,
        "hit_pmin":   0.60, "hit_pmax":  0.78,
        "hit_arc":    2.0,  "aim_spread": 0.86,
    },
    "Hard": {
        "reaction":   0.05, "speed":     1.10, "error":     0.01,
        "hit_pmin":   0.85, "hit_pmax":  1.00,
        "hit_arc":    2.6,  "aim_spread": 1.0,
    },
}
DEFAULT_DIFFICULTY  = "Medium"

# ─── MATCH ─────────────────────────────────────────────────────────────────────
POINTS_PER_SET      = 11
WIN_BY              = 2
SETS_TO_WIN         = 3            # best of 5
SERVE_ALTERNATES    = 2            # switch serve every N points

# ─── RENDERING ─────────────────────────────────────────────────────────────────
WINDOW_TITLE        = "Table Tennis 3D"
WINDOW_W            = 1280
WINDOW_H            = 720
TARGET_FPS          = 60

# Camera (Panda3D Y-forward right-hand coordinate)
CAM_POS             = (0, -3.2, 3.0)
CAM_LOOK            = (0,  0.3, 0)

BG_COLOR            = (1.00, 0.82, 0.35, 1)   # warm arcade yellow

# ─── NETWORK ───────────────────────────────────────────────────────────────────
WS_HOST             = "0.0.0.0"
WS_PORT             = 8765
HTTP_PORT           = 8080
IMU_HZ              = 60

# ─── SOUNDS ────────────────────────────────────────────────────────────────────
SOUND_DIR           = "assets/sounds"
SOUNDS = {
    "pock":    "pock.wav",
    "thud":    "thud.wav",
    "cheer":   "cheer.wav",
    "ambient": "ambient.wav",
}

# ─── COLOURS (RGBA 0-1) ────────────────────────────────────────────────────────
COLOR_TABLE         = (0.35, 0.75, 0.18, 1)   # bright lime green
COLOR_TABLE_EDGE    = (0.04, 0.04, 0.04, 1)   # near-black border
COLOR_NET           = (1.00, 1.00, 1.00, 1)   # pure white
COLOR_LINE          = (1.00, 1.00, 1.00, 1)
COLOR_BALL          = (1.00, 1.00, 1.00, 1)   # white ball
COLOR_PLAYER_PADDLE = (0.96, 0.32, 0.32, 1)   # coral-red (player)
COLOR_AI_PADDLE     = (0.18, 0.82, 0.96, 1)   # cyan (AI)
COLOR_FLOOR         = (1.00, 0.82, 0.35, 1)   # same warm yellow as BG

# Trail
TRAIL_LENGTH        = 10           # number of ghost spheres
