"""
main.py — Table Tennis 3D (Phase 1: Keyboard controls)
Entry point. Subclasses ShowBase; wires together scene, physics, AI, HUD.
"""
import os
import sys
import math
import builtins

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import (
    WindowProperties, ClockObject, LVecBase3f,
    loadPrcFileData
)

# ── Panda3D window config (must be before ShowBase) ───────────────────────────
loadPrcFileData('', f'window-title {__import__("config").WINDOW_TITLE}')
loadPrcFileData('', f'win-size {__import__("config").WINDOW_W} {__import__("config").WINDOW_H}')
loadPrcFileData('', 'sync-video 0')

import config as C
from game.scene        import Scene
from game.ball         import Ball
from game.paddle       import Paddle
from game.physics      import PhysicsEngine, BallState, PhysicsEngine
from game.ai_opponent  import AIOpponent
from game.match        import MatchState
from game.hud          import HUD
from input.keyboard_fallback import KeyboardController

import socket
import qrcode
import os

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


class TableTennisGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        builtins.base = self   # make base globally accessible (used by scene)

        # ── Window ────────────────────────────────────────────────────────────
        self.disableMouse()
        props = WindowProperties()
        props.setTitle(C.WINDOW_TITLE)
        self.win.requestProperties(props)

        # ── Camera ────────────────────────────────────────────────────────────
        self.camera.setPos(*C.CAM_POS)
        self.camera.lookAt(*C.CAM_LOOK)

        # ── Background ────────────────────────────────────────────────────────
        self.setBackgroundColor(*C.BG_COLOR)

        # ── Core systems ──────────────────────────────────────────────────────
        self.scene   = Scene(self.render, self.loader)
        self.physics = PhysicsEngine()
        self.ball_state = BallState()

        self.player_paddle = Paddle(self.render, is_player=True)
        self.ai_paddle     = Paddle(self.render, is_player=False)
        self.ball_vis      = Ball(self.render)

        self.ai      = AIOpponent(self.physics, C.DEFAULT_DIFFICULTY)
        self.match   = MatchState()
        self.hud     = HUD()
        self.keys    = KeyboardController(self)

        # ── Network / QR Code ─────────────────────────────────────────────────
        self.local_ip = get_local_ip()
        self.mobile_url = f"http://{self.local_ip}:{C.HTTP_PORT}"
        qr = qrcode.make(self.mobile_url)
        self.qr_path = 'assets/qrcode.png'
        qr.save(self.qr_path)

        # ── Sound ─────────────────────────────────────────────────────────────
        self._sounds = self._load_sounds()
        self._ambient_playing = False

        # ── Physics accumulator ───────────────────────────────────────────────
        self._phys_acc = 0.0

        # ── State ─────────────────────────────────────────────────────────────
        self._point_delay   = 0.0   # pause after point before next serve
        self._set_delay     = 0.0
        self._hit_cooldown  = 0.0   # prevent double-hit per swing

        # ── Wire input callbacks ───────────────────────────────────────────────
        self.keys.on_serve = self._player_serve
        self.keys.on_pause = self._toggle_pause

        # ── Show main menu ────────────────────────────────────────────────────
        self.hud.show_main_menu(
            on_start       = self._start_game,
            on_quit        = sys.exit,
            on_diff_change = self._set_difficulty,
            qr_path        = self.qr_path,
            url            = self.mobile_url
        )

        # ── Main task ─────────────────────────────────────────────────────────
        self.taskMgr.add(self._game_loop, 'game_loop')

    # ═══════════════════════════════════════════════════════════════════════════
    # Game Loop
    # ═══════════════════════════════════════════════════════════════════════════
    def _game_loop(self, task):
        dt = min(globalClock.getDt(), 0.05)  # cap for tab-out spikes
        ms = self.match

        if ms.state == MatchState.MENU:
            return Task.cont

        if ms.state == MatchState.PAUSED:
            return Task.cont

        if ms.state == MatchState.MATCH_WON:
            return Task.cont

        # ── Delay timers ──────────────────────────────────────────────────────
        if self._point_delay > 0:
            self._point_delay -= dt
            return Task.cont

        if self._set_delay > 0:
            self._set_delay -= dt
            if self._set_delay <= 0:
                self.match.start_new_set()
                self._reset_serve()
            return Task.cont

        # ── Serving state ─────────────────────────────────────────────────────
        if ms.state == MatchState.SERVING:
            is_serving = True
            if ms.server == 'ai':
                self._ai_auto_serve(dt)
        else:
            is_serving = False

        # ── Input (keyboard) ──────────────────────────────────────────────────
        self.keys.update(dt, is_serving=is_serving)
        self.player_paddle.update(self.keys.px, self.keys.py, self.keys.pz)

        # Ball follows player paddle during player serve
        if ms.state == MatchState.SERVING and ms.server == 'player':
            self.ball_state.set_pos(
                self.keys.px, self.keys.py + 0.02, self.keys.pz + 0.08
            )

        # ── Physics ───────────────────────────────────────────────────────────
        if ms.state == MatchState.RALLY:
            self._phys_acc += dt
            while self._phys_acc >= C.PHYSICS_DT:
                result = self.physics.step(self.ball_state)
                self._phys_acc -= C.PHYSICS_DT
                if result != PhysicsEngine.ONGOING:
                    self._handle_point(result)
                    break

            # Check AI and Player hits in RALLY
            self._check_ai_hit()
            self._check_player_hit()

        # ── AI update ─────────────────────────────────────────────────────────
        if ms.state == MatchState.RALLY:
            self.ai.update(dt, self.ball_state)
            self.ai_paddle.update(self.ai.px, self.ai.py, self.ai.pz)

        # ── Hit cooldown ──────────────────────────────────────────────────────
        if self._hit_cooldown > 0:
            self._hit_cooldown -= dt

        # ── Visuals ───────────────────────────────────────────────────────────
        bx, by, bz = self.ball_state.pos
        spd = math.sqrt(self.ball_state.vx**2 + self.ball_state.vy**2 + self.ball_state.vz**2)
        self.ball_vis.update(bx, by, bz, spd)

        # ── HUD ───────────────────────────────────────────────────────────────
        self.hud.update_score(self.match)
        self.hud.update_popup(dt)

        return Task.cont

    # ═══════════════════════════════════════════════════════════════════════════
    # Player Actions
    # ═══════════════════════════════════════════════════════════════════════════
    def _player_serve(self):
        if self.match.state != MatchState.SERVING:
            return
        if self.match.server != 'player':
            return

        bs = self.ball_state
        bs.set_vel(0, C.SERVE_SPEED_Y, C.SERVE_SPEED_Z)
        bs.in_play = True
        bs.bounced_on_side = None
        self.match.state = MatchState.RALLY
        self.ball_vis.clear_trail()
        self._play('pock', pitch=0.8)

    def _check_player_hit(self):
        if self._hit_cooldown > 0:
            return

        bs = self.ball_state
        if not bs.in_play or bs.vy > 0:
            return   # ball moving away from player

        # Check only X and Y distance (ignore Z for pure sideways arcade feel)
        dx = bs.x - self.keys.px
        dy = bs.y - self.keys.py

        if abs(dx) < C.PADDLE_RADIUS * 1.8 and bs.y < C.PLAYER_PADDLE_Y + 0.15:
            power = 0.8
            self.physics.apply_paddle_hit(
                bs,
                self.keys.px, self.keys.py, self.keys.pz,
                self.keys.vx, 2.8, 0,  # Fast enough to clear net
                power
            )
            # Override ball X-velocity based on hit position (Pong style)
            hit_factor = (bs.x - self.keys.px) / C.PADDLE_RADIUS
            bs.vx += hit_factor * 2.5
            bs.vz = 2.0  # Controlled arc
            self._hit_cooldown = 0.3
            self._play('pock', pitch=1.0)

    def _check_ai_hit(self):
        """Check if ball is within AI paddle hit range."""
        bs = self.ball_state
        if not bs.in_play or bs.vy < 0:
            return   # ball moving away from AI

        dx = bs.x - self.ai.px
        dy = bs.y - self.ai.py
        dz = bs.z - self.ai.pz
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)

        if dist < C.PADDLE_RADIUS * 1.6 and bs.y > 0.5:
            self.ai._try_hit(bs)
            self._play('pock', pitch=1.1)

    # ═══════════════════════════════════════════════════════════════════════════
    # AI Serve
    # ═══════════════════════════════════════════════════════════════════════════
    _ai_serve_timer = 0.0

    def _ai_auto_serve(self, dt):
        self._ai_serve_timer += dt
        if self._ai_serve_timer >= 1.5:   # AI waits 1.5s then serves
            self._ai_serve_timer = 0.0
            bs = self.ball_state
            # Spawn ball firmly in front of AI to prevent immediate paddle collision glitch
            bs.set_pos(self.ai.px, C.AI_PADDLE_Y - 0.08, 0.15)
            bs.set_vel(0, -C.SERVE_SPEED_Y, C.SERVE_SPEED_Z)
            bs.in_play = True
            bs.bounced_on_side = None
            self.match.state = MatchState.RALLY
            self.ball_vis.clear_trail()
            self._play('pock', pitch=0.9)

    # ═══════════════════════════════════════════════════════════════════════════
    # Point / Set / Match Handling
    # ═══════════════════════════════════════════════════════════════════════════
    def _handle_point(self, result):
        scorer = 'player' if result == PhysicsEngine.POINT_PLAYER else 'ai'
        outcome = self.match.score_point(scorer)

        if scorer == 'player':
            self.hud.show_popup('Point! YOU', 1.8)
            self._play('cheer')
        else:
            self.hud.show_popup('Point! AI', 1.8)

        self._play('thud')

        if outcome == 'match':
            self.hud.hide_score()
            self.hud.show_end_screen(
                self.match.match_winner,
                on_rematch     = self._start_game,
                on_main_menu   = self._go_main_menu,
            )
        elif outcome == 'set':
            winner = 'YOU' if self.match.player_sets > self.match.ai_sets else 'AI'
            self.hud.show_popup(f'Set to {winner}!', 3.0)
            self._set_delay   = 3.2
            self._point_delay = 0.0
        else:
            self._point_delay = 1.8
            self.taskMgr.doMethodLater(
                self._point_delay, self._reset_serve_callback, 'reset_serve'
            )

    def _reset_serve_callback(self, task):
        self._reset_serve()
        return Task.done

    def _reset_serve(self):
        self.ball_state.reset()
        self.ball_vis.clear_trail()
        self.ai.reset_to_idle()
        self._phys_acc = 0.0
        self._ai_serve_timer = 0.0
        self.match.state = MatchState.SERVING
        if self.match.server == 'player':
            self.hud.show_popup('Your serve — press SPACE', 2.0)
        else:
            self.hud.show_popup("AI's serve…", 1.5)

    # ═══════════════════════════════════════════════════════════════════════════
    # Menu / State transitions
    # ═══════════════════════════════════════════════════════════════════════════
    def _start_game(self):
        self.hud.hide_main_menu()
        self.hud.hide_end_screen()
        self.hud.show_score()
        self.hud.set_difficulty_label(self.match.difficulty)
        self.match.start_game()
        self.ai.set_difficulty(self.match.difficulty)
        self._reset_serve()
        if not self._ambient_playing:
            self._play_ambient()

    def _go_main_menu(self):
        self.match.state = MatchState.MENU
        self.hud.hide_end_screen()
        self.hud.hide_pause_menu()
        self.hud.hide_score()
        self.ball_state.in_play = False
        self.hud.show_main_menu(
            on_start       = self._start_game,
            on_quit        = sys.exit,
            on_diff_change = self._set_difficulty,
            qr_path        = self.qr_path,
            url            = self.mobile_url
        )

    def _toggle_pause(self):
        ms = self.match
        if ms.state == MatchState.PAUSED:
            ms.resume()
            self.hud.hide_pause_menu()
        elif ms.state not in (MatchState.MENU, MatchState.MATCH_WON):
            ms.pause()
            self.hud.show_pause_menu(
                on_resume    = self._toggle_pause,
                on_main_menu = self._go_main_menu,
            )

    def _set_difficulty(self, diff: str):
        self.match.difficulty = diff
        self.ai.set_difficulty(diff)
        self.hud.set_difficulty_label(diff)

    # ═══════════════════════════════════════════════════════════════════════════
    # Sound
    # ═══════════════════════════════════════════════════════════════════════════
    def _load_sounds(self) -> dict:
        sounds = {}
        for key, fname in C.SOUNDS.items():
            path = os.path.join(C.SOUND_DIR, fname)
            if os.path.exists(path):
                try:
                    sounds[key] = self.loader.loadSfx(path)
                except Exception:
                    pass
        return sounds

    def _play(self, key: str, pitch: float = 1.0):
        snd = self._sounds.get(key)
        if snd:
            snd.setPlayRate(pitch)
            snd.play()

    def _play_ambient(self):
        snd = self._sounds.get('ambient')
        if snd:
            snd.setLoop(True)
            snd.setVolume(0.25)
            snd.play()
            self._ambient_playing = True


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    game = TableTennisGame()
    game.run()
