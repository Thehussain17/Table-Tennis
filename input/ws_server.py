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
        self.tilt_x = 0.0  # Normalized tilt [-1.0 to 1.0] for moving left/right
        self.is_connected = False
        self.action_serve = False

        self._ws_loop = None
        self._ws_thread = None
        self._http_thread = None

    def start(self):
        # Start HTTP Server for serving the HTML controller
        self._http_thread = threading.Thread(target=self._run_http_server, daemon=True)
        self._http_thread.start()

        # Start WebSocket Server
        self._ws_thread = threading.Thread(target=self._run_ws_server, daemon=True)
        self._ws_thread.start()

    def _run_http_server(self):
        web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mobile')
        if not os.path.exists(web_dir):
            os.makedirs(web_dir)
            
        import functools
        handler = functools.partial(SimpleHTTPRequestHandler, directory=web_dir)
        server = HTTPServer(('0.0.0.0', C.HTTP_PORT), handler)
        print(f"[HTTP] Mobile controller available at http://<YOUR_IP>:{C.HTTP_PORT}/")
        server.serve_forever()

    def _run_ws_server(self):
        async def main():
            print(f"[WS] WebSocket server started on ws://0.0.0.0:{C.WS_PORT}")
            async with websockets.serve(self._ws_handler, "0.0.0.0", C.WS_PORT):
                await asyncio.Future()  # run forever

        asyncio.run(main())

    async def _ws_handler(self, websocket, path):
        print("[WS] Mobile client connected!")
        self.is_connected = True
        try:
            async for message in websocket:
                data = json.loads(message)
                if data.get('type') == 'imu':
                    # Roll (beta) or tilt left/right controls the paddle
                    # beta is typically [-180, 180]
                    beta = data.get('beta', 0.0)
                    
                    # Normalize beta to a [-1, 1] range for steering.
                    # Max tilt of ~45 degrees (full speed)
                    tilt = beta / 45.0
                    self.tilt_x = max(-1.0, min(1.0, tilt))
                    
                elif data.get('type') == 'action' and data.get('action') == 'serve':
                    self.action_serve = True
                    
        except websockets.exceptions.ConnectionClosed:
            print("[WS] Mobile client disconnected.")
        finally:
            self.is_connected = False
            self.tilt_x = 0.0

    def get_tilt(self) -> float:
        return self.tilt_x

    def consume_serve_action(self) -> bool:
        if self.action_serve:
            self.action_serve = False
            return True
        return False
