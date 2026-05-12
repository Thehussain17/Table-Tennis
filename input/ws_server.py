"""
input/ws_server.py — WebSocket server to receive IMU data from the mobile client.
Also serves the HTML controller page via a simple HTTP server.
"""
import asyncio
import json
import threading
import websockets
from http.server import SimpleHTTPRequestHandler, HTTPServer
import os

import config as C


class IMUServer:
    def __init__(self):
        self._lock       = threading.Lock()
        self._tilt_x     = 0.0     # Normalized tilt [-1.0 to 1.0]
        self._action_serve = False
        self.is_connected  = False

        self._ws_loop   = None
        self._ws_thread = None
        self._http_thread = None

    # ── Public getters (called from Panda3D main thread) ──────────────────────
    def get_tilt(self) -> float:
        with self._lock:
            return self._tilt_x

    def consume_serve_action(self) -> bool:
        with self._lock:
            if self._action_serve:
                self._action_serve = False
                return True
        return False

    # ── Start servers ─────────────────────────────────────────────────────────
    def start(self):
        self._http_thread = threading.Thread(
            target=self._run_http_server, daemon=True, name='http-server')
        self._http_thread.start()

        self._ws_thread = threading.Thread(
            target=self._run_ws_server, daemon=True, name='ws-server')
        self._ws_thread.start()

    # ── HTTP server ───────────────────────────────────────────────────────────
    def _run_http_server(self):
        web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mobile')
        os.makedirs(web_dir, exist_ok=True)

        import functools
        handler = functools.partial(SimpleHTTPRequestHandler,
                                    directory=web_dir)
        server = HTTPServer(('0.0.0.0', C.HTTP_PORT), handler)
        print(f"[HTTP] Mobile controller → http://0.0.0.0:{C.HTTP_PORT}/")
        server.serve_forever()

    # ── WebSocket server ──────────────────────────────────────────────────────
    def _run_ws_server(self):
        async def main():
            print(f"[WS] WebSocket server → ws://0.0.0.0:{C.WS_PORT}")
            async with websockets.serve(
                self._ws_handler, "0.0.0.0", C.WS_PORT,
                ping_interval=None,
                ping_timeout=None,
            ):
                await asyncio.Future()   # run forever

        asyncio.run(main())

    # ── WebSocket message handler ─────────────────────────────────────────────
    async def _ws_handler(self, websocket):
        print("[WS] Mobile client connected!")
        self.is_connected = True
        with self._lock:
            self._tilt_x = 0.0

        try:
            async for raw in websocket:
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                msg_type = data.get('type')

                if msg_type == 'imu':
                    # The mobile page sends { type:'imu', beta:<degrees> }
                    # beta here is actually gamma (left/right tilt) in degrees.
                    # Server-side we normalize by 45° → [-1, 1].
                    beta = float(data.get('beta', 0.0))
                    tilt = max(-1.0, min(1.0, beta / 45.0))
                    with self._lock:
                        self._tilt_x = tilt
                    # Uncomment for verbose debugging:
                    # print(f"[WS] tilt={tilt:.3f}  (beta={beta:.1f}°)")

                elif msg_type == 'action' and data.get('action') == 'serve':
                    print("[WS] Serve action received")
                    with self._lock:
                        self._action_serve = True

        except websockets.exceptions.ConnectionClosed:
            print("[WS] Mobile client disconnected.")
        finally:
            self.is_connected = False
            with self._lock:
                self._tilt_x = 0.0
