"""Minimal WebSocket server (stdlib) for live dashboard updates."""
from __future__ import annotations

import base64
import hashlib
import socket
import struct
import threading
import time
from typing import Any, Dict, List, Set


class WebSocketHub:
    def __init__(self, host: str = "0.0.0.0", port: int = 8001):
        self.host = host
        self.port = port
        self.clients: Set[socket.socket] = set()
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._server_sock: socket.socket | None = None

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass
        with self._lock:
            for c in list(self.clients):
                try:
                    c.close()
                except Exception:
                    pass
            self.clients.clear()

    def _run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        s.listen(32)
        s.settimeout(1.0)
        self._server_sock = s
        while not self._stop.is_set():
            try:
                conn, addr = s.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            t = threading.Thread(target=self._handle_client, args=(conn,), daemon=True)
            t.start()

    def _handle_client(self, conn: socket.socket):
        # perform handshake
        try:
            data = b""
            while b"\r\n\r\n" not in data:
                chunk = conn.recv(4096)
                if not chunk:
                    conn.close()
                    return
                data += chunk
                if len(data) > 8192:
                    conn.close()
                    return
            headers = data.split(b"\r\n\r\n", 1)[0].decode("utf-8", "replace")
            key = None
            for line in headers.split("\r\n"):
                if line.lower().startswith("sec-websocket-key:"):
                    key = line.split(":", 1)[1].strip()
            if key is None:
                conn.close()
                return
            accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
            resp = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept}\r\n"
                "\r\n"
            )
            conn.sendall(resp.encode())
            with self._lock:
                self.clients.add(conn)
            # read loop
            while not self._stop.is_set():
                try:
                    conn.settimeout(30.0)
                    msg = self._read_frame(conn)
                except Exception:
                    break
                if msg is None:
                    break
                # echo not needed; ignore client messages (or handle ping)
        finally:
            with self._lock:
                self.clients.discard(conn)
            try:
                conn.close()
            except Exception:
                pass

    def _read_frame(self, conn: socket.socket):
        # returns text payload or None on close
        header = conn.recv(2)
        if not header or len(header) < 2:
            return None
        b1, b2 = header[0], header[1]
        opcode = b1 & 0x0F
        masked = (b2 & 0x80) != 0
        length = b2 & 0x7F
        if length == 126:
            ext = conn.recv(2)
            length = struct.unpack("!H", ext)[0]
        elif length == 127:
            ext = conn.recv(8)
            length = struct.unpack("!Q", ext)[0]
        mask = b""
        if masked:
            mask = conn.recv(4)
        payload = b""
        while len(payload) < length:
            chunk = conn.recv(min(4096, length - len(payload)))
            if not chunk:
                return None
            payload += chunk
        if masked:
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        if opcode == 8:
            return None
        if opcode == 9:
            # ping -> pong
            try:
                conn.sendall(self._frame(payload, opcode=10))
            except Exception:
                pass
            return ""
        if opcode == 1:
            return payload.decode("utf-8", "replace")
        return ""

    def _frame(self, payload: bytes, opcode: int = 1) -> bytes:
        header = bytes([0x80 | opcode])
        n = len(payload)
        if n < 126:
            header += bytes([n])
        elif n < 65536:
            header += bytes([126]) + struct.pack("!H", n)
        else:
            header += bytes([127]) + struct.pack("!Q", n)
        return header + payload

    def broadcast(self, message: str):
        payload = message.encode("utf-8")
        frame = self._frame(payload, opcode=1)
        dead = []
        with self._lock:
            for c in list(self.clients):
                try:
                    c.sendall(frame)
                except Exception:
                    dead.append(c)
            for c in dead:
                self.clients.discard(c)
                try:
                    c.close()
                except Exception:
                    pass
