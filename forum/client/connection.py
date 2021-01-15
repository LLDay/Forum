import threading
import time

from socket import *


class ServerConnection:
    def __init__(self, model):
        self.model = model
        self.sock = None
        self.lock = threading.Lock
        self.connection_handler = []
        self.error_handler = []

    def add_connection_handler(self, func):
        with self.lock:
            self.connection_handler.append(func)

    def add_error_handler(self, func):
        with self.lock:
            self.error_handler.append(func)

    def connect(self):
        connect_thread = threading.Thread(
            target=self._connect_loop, daemon=True)
        connect_thread.start()

    def _connect_loop(self):
        while True:
            with self.lock:
                self.sock = socket(AF_INET, SOCK_STREAM, 0)
                self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                try:
                    self.sock.connect((self.model._ip, self.model._port))
                    break
                except ConnectionRefusedError:
                    self.sock.close()
                    for handler in self.error_handler:
                        handler("Unable to connect to the server")
                    time.sleep(1)

        for handler in self.connection_handler:
            handler()

    def send(self, packet: PacketHeader):
        with self.lock:
            try:
                self.sock.sendall(packet.raw())
            except:
                for handler in self.error_handler:
                    handler("Cannot send packet to the server")
