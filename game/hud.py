"""
game/hud.py — Arcade-style HUD: scoreboard panel, popup messages, menus.
Color palette matches the reference image (yellow BG, green table aesthetic).
"""
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.DirectGui import (
    DirectFrame, DirectButton, DirectLabel, DirectOptionMenu
)
from panda3d.core import TextNode, LColor, TransparencyAttrib
import config as C

# ── Palette ───────────────────────────────────────────────────────────────────
_DARK       = (0.06, 0.06, 0.08, 1.0)
_PANEL      = (0.10, 0.10, 0.14, 0.92)
_WHITE      = (1.00, 1.00, 1.00, 1.0)
_YELLOW     = (1.00, 0.88, 0.15, 1.0)
_PLAYER_COL = (0.96, 0.32, 0.32, 1.0)   # coral-red
_AI_COL     = (0.18, 0.82, 0.96, 1.0)   # cyan
_GREEN      = (0.30, 0.90, 0.35, 1.0)


def _btn(text, pos, cmd, scale=0.065,
         fc=(0.14, 0.14, 0.22, 0.95), tc=(1, 1, 1, 1)):
    return DirectButton(
        text=text, pos=pos, scale=scale, command=cmd,
        frameColor=fc, text_fg=tc,
        relief=1,
        pad=(0.25, 0.12),
        rolloverSound=None, clickSound=None,
    )


class HUD:
    def __init__(self):
        self._popup_timer = 0.0
        self._popup_node  = None
        self._score_panel = None
        self._main_menu_frame = None
        self._pause_menu_frame = None
        self._end_frame = None
        self._build_scoreboard()
        self._build_popup()

    # ═══════════════════════════════════════════════════════════════════════════
    # Scoreboard
    # ═══════════════════════════════════════════════════════════════════════════
    def _build_scoreboard(self):
        # Dark panel at top
        self._score_panel = DirectFrame(
            frameColor=(0.06, 0.06, 0.10, 0.88),
            frameSize=(-1.35, 1.35, -0.135, 0.135),
            pos=(0, 0, 0.87),
            relief=1,
        )

        # Player label (left)
        DirectLabel(
            parent=self._score_panel, text='YOU',
            scale=0.072, pos=(-0.75, 0, 0.025),
            text_fg=_PLAYER_COL, frameColor=(0,0,0,0),
            text_align=TextNode.ACenter
        )
        # AI label (right)
        DirectLabel(
            parent=self._score_panel, text='AI',
            scale=0.072, pos=(0.75, 0, 0.025),
            text_fg=_AI_COL, frameColor=(0,0,0,0),
            text_align=TextNode.ACenter
        )

        # Player score (big, left)
        self._player_score_lbl = DirectLabel(
            parent=self._score_panel, text='0',
            scale=0.115, pos=(-0.42, 0, -0.04),
            text_fg=_WHITE, frameColor=(0,0,0,0),
            text_align=TextNode.ACenter
        )
        # AI score (big, right)
        self._ai_score_lbl = DirectLabel(
            parent=self._score_panel, text='0',
            scale=0.115, pos=(0.42, 0, -0.04),
            text_fg=_WHITE, frameColor=(0,0,0,0),
            text_align=TextNode.ACenter
        )
        # Dash separator
        DirectLabel(
            parent=self._score_panel, text='-',
            scale=0.10, pos=(0, 0, -0.04),
            text_fg=(0.5, 0.5, 0.5, 1), frameColor=(0,0,0,0),
            text_align=TextNode.ACenter
        )

        # Sets row (bottom of panel)
        self._sets_lbl = DirectLabel(
            parent=self._score_panel, text='Sets  0 - 0',
            scale=0.048, pos=(0, 0, -0.10),
            text_fg=(0.75, 0.85, 1.0, 1), frameColor=(0,0,0,0),
            text_align=TextNode.ACenter
        )
        # Serve dot
        self._serve_lbl = DirectLabel(
            parent=self._score_panel, text='',
            scale=0.048, pos=(0, 0, 0.065),
            text_fg=_YELLOW, frameColor=(0,0,0,0),
            text_align=TextNode.ACenter
        )
        # Difficulty tag (top right)
        self._diff_lbl = DirectLabel(
            parent=self._score_panel, text='[Medium]',
            scale=0.040, pos=(1.10, 0, 0.065),
            text_fg=(0.6, 0.6, 0.6, 1), frameColor=(0,0,0,0),
            text_align=TextNode.ARight
        )

        # Controls bar (bottom of screen)
        self._ctrl_text = OnscreenText(
            text='A/D: Move Sideways  |  SPACE: Serve  |  ESC: Pause',
            pos=(0, -0.93), scale=0.040,
            fg=(0.5, 0.5, 0.5, 0.85),
            align=TextNode.ACenter, mayChange=False
        )

        self.hide_score()

    # ── Score updates ─────────────────────────────────────────────────────────
    def update_score(self, match):
        self._player_score_lbl['text'] = str(match.player_score)
        self._ai_score_lbl['text']     = str(match.ai_score)
        self._sets_lbl['text']         = f'Sets  {match.player_sets} - {match.ai_sets}'
        srv_txt = 'YOUR SERVE' if match.server == 'player' else 'AI SERVE'
        self._serve_lbl['text'] = srv_txt

    def set_difficulty_label(self, diff: str):
        self._diff_lbl['text'] = f'[{diff}]'

    def show_score(self):
        self._score_panel.show()
        self._ctrl_text.show()

    def hide_score(self):
        self._score_panel.hide()
        self._ctrl_text.hide()

    # ═══════════════════════════════════════════════════════════════════════════
    # Popup
    # ═══════════════════════════════════════════════════════════════════════════
    def _build_popup(self):
        self._popup_node = OnscreenText(
            text='', pos=(0, 0.18), scale=0.12,
            fg=_YELLOW, shadow=(0, 0, 0, 0.9),
            shadowOffset=(0.04, 0.04),
            align=TextNode.ACenter, mayChange=True
        )
        self._popup_node.hide()

    def show_popup(self, text: str, duration: float = 2.0):
        self._popup_node.setText(text)
        self._popup_node.show()
        self._popup_timer = duration

    def update_popup(self, dt: float):
        if self._popup_timer > 0:
            self._popup_timer -= dt
            if self._popup_timer <= 0:
                self._popup_node.hide()

    # ═══════════════════════════════════════════════════════════════════════════
    # Main Menu
    # ═══════════════════════════════════════════════════════════════════════════
    def show_main_menu(self, on_start, on_quit, on_diff_change, qr_path=None, url=None):
        self._destroy_menu(self._main_menu_frame)
        frame = DirectFrame(
            frameColor=(0.07, 0.07, 0.12, 0.96),
            frameSize=(-0.85, 0.85, -0.68, 0.85),
            pos=(0, 0, 0)
        )

        # Title
        DirectLabel(
            parent=frame, text='TABLE TENNIS 3D',
            scale=0.105, pos=(0, 0, 0.65),
            text_fg=_YELLOW, frameColor=(0, 0, 0, 0),
            text_align=TextNode.ACenter
        )
        # Subtitle
        DirectLabel(
            parent=frame, text='Scan QR to use Phone as Paddle!',
            scale=0.055, pos=(0, 0, 0.50),
            text_fg=(0.6, 0.8, 1, 1), frameColor=(0, 0, 0, 0),
            text_align=TextNode.ACenter
        )

        if qr_path and url:
            # QR Code Image
            qr_img = OnscreenImage(image=qr_path, parent=frame, pos=(0, 0, 0.15), scale=0.25)
            qr_img.setTransparency(TransparencyAttrib.MAlpha)
            # URL Text
            DirectLabel(
                parent=frame, text=url,
                scale=0.045, pos=(0, 0, -0.15),
                text_fg=(0.5, 0.5, 0.5, 1), frameColor=(0, 0, 0, 0),
                text_align=TextNode.ACenter
            )

        # Decorative colored bar
        DirectFrame(
            parent=frame,
            frameColor=_PLAYER_COL,
            frameSize=(-0.30, 0.30, -0.005, 0.005),
            pos=(-0.22, 0, 0.44)
        )
        DirectFrame(
            parent=frame,
            frameColor=_AI_COL,
            frameSize=(-0.30, 0.30, -0.005, 0.005),
            pos=(0.22, 0, 0.44)
        )

        _btn('START GAME', (0, 0, -0.30), on_start,
             scale=0.072,
             fc=(0.18, 0.65, 0.22, 1),
             tc=(1, 1, 1, 1)).reparentTo(frame)

        # Difficulty row
        DirectLabel(parent=frame, text='Difficulty:', scale=0.055,
                    pos=(-0.18, 0, -0.45), text_fg=(0.85, 0.85, 0.85, 1),
                    frameColor=(0, 0, 0, 0))
        DirectOptionMenu(
            parent=frame, scale=0.058,
            pos=(0.22, 0, -0.45),
            items=['Easy', 'Medium', 'Hard'],
            initialitem=1,
            command=on_diff_change,
            frameColor=(0.18, 0.18, 0.30, 1),
            text_fg=(1, 1, 1, 1),
        )

        _btn('QUIT', (0, 0, -0.58), on_quit,
             fc=(0.35, 0.08, 0.08, 0.95)).reparentTo(frame)

        self._main_menu_frame = frame

    def hide_main_menu(self):
        self._destroy_menu(self._main_menu_frame)
        self._main_menu_frame = None

    # ═══════════════════════════════════════════════════════════════════════════
    # Pause Menu
    # ═══════════════════════════════════════════════════════════════════════════
    def show_pause_menu(self, on_resume, on_main_menu):
        self._destroy_menu(self._pause_menu_frame)
        frame = DirectFrame(
            frameColor=(0.07, 0.07, 0.12, 0.94),
            frameSize=(-0.52, 0.52, -0.48, 0.48),
            pos=(0, 0, 0)
        )
        DirectLabel(parent=frame, text='PAUSED', scale=0.105,
                    pos=(0, 0, 0.26), text_fg=_WHITE,
                    frameColor=(0, 0, 0, 0))
        _btn('RESUME',    (0, 0,  0.05), on_resume,
             fc=(0.18, 0.65, 0.22, 1)).reparentTo(frame)
        _btn('MAIN MENU', (0, 0, -0.20), on_main_menu,
             fc=(0.20, 0.08, 0.30, 0.95)).reparentTo(frame)
        self._pause_menu_frame = frame

    def hide_pause_menu(self):
        self._destroy_menu(self._pause_menu_frame)
        self._pause_menu_frame = None

    # ═══════════════════════════════════════════════════════════════════════════
    # End Screen
    # ═══════════════════════════════════════════════════════════════════════════
    def show_end_screen(self, winner: str, on_rematch, on_main_menu):
        self._destroy_menu(self._end_frame)
        frame = DirectFrame(
            frameColor=(0.07, 0.07, 0.12, 0.96),
            frameSize=(-0.68, 0.68, -0.55, 0.55),
            pos=(0, 0, 0)
        )
        if winner == 'player':
            msg  = 'YOU WIN!'
            col  = _GREEN
            sub  = 'Congratulations!'
        else:
            msg  = 'AI WINS!'
            col  = _PLAYER_COL
            sub  = 'Better luck next time'

        DirectLabel(parent=frame, text=msg, scale=0.115,
                    pos=(0, 0, 0.30), text_fg=col, frameColor=(0, 0, 0, 0),
                    text_align=TextNode.ACenter)
        DirectLabel(parent=frame, text=sub, scale=0.056,
                    pos=(0, 0, 0.14), text_fg=_WHITE, frameColor=(0, 0, 0, 0),
                    text_align=TextNode.ACenter)

        _btn('REMATCH',   (0, 0,  0.00 - 0.05), on_rematch,
             scale=0.070, fc=(0.18, 0.65, 0.22, 1)).reparentTo(frame)
        _btn('MAIN MENU', (0, 0, -0.28), on_main_menu,
             fc=(0.20, 0.08, 0.30, 0.95)).reparentTo(frame)
        self._end_frame = frame

    def hide_end_screen(self):
        self._destroy_menu(self._end_frame)
        self._end_frame = None

    # ═══════════════════════════════════════════════════════════════════════════
    @staticmethod
    def _destroy_menu(frame):
        if frame is not None:
            frame.destroy()
