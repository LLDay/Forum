import select
import time
import threading

from collections.abc import Iterable
from forum.common.packet import PacketHeader
from socket import *


class ServerConnection:
    def __init__(self, ip, port, timeout=0.5):
        self.sockets = []
        self.ip = ip
        self.port = port
        self.timeout = timeout

        self.lock = threading.Lock()
        self._working = True
        self._connection_listeners = []
        self._disconnect_listeners = []
        self._read_listeners = []
        self._error_listeners = []

    def start(self):
        listen_thread = threading.Thread(target=self._get_packets, daemon=True)
        listen_thread.start()
        self._start_connection()

    def _start_connection(self):
        connect_thread = threading.Thread(
            target=self._connect_loop, daemon=True)
        connect_thread.start()

    def _connect_loop(self):
        sock = None
        while True:
            sock = socket(AF_INET, SOCK_STREAM, 0)
            sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            try:
                sock.connect((self.ip, self.port))
                sock.setblocking(False)
                break
            except:
                with self.lock:
                    for handler in self._error_listeners:
                        handler("Unable to connect to the server")

            time.sleep(1)

        with self.lock:
            self.sockets = [sock]
            for handler in self._connection_listeners:
                handler()

    def add_connection_handler(self, function):
        with self.lock:
            self._connection_listeners.append(function)

    def add_disconnect_handler(self, function):
        with self.lock:
            self._disconnect_listeners.append(function)

    # Excepts function accepted PacketHeader object as an argument
    def add_incoming_packet_handler(self, function):
        with self.lock:
            self._read_listeners.append(function)

    def add_error_handler(self, function):
        with self.lock:
            self._error_listeners.append(function)

    def _get_packets(self):
        buffer = bytearray()

        while True:
            sockets_copy = []
            with self.lock:
                sockets_copy = self.sockets[:]
                if not self._working:
                    break

            r_sock, _, _ = select.select(sockets_copy, [], [], self.timeout)

            for socket in r_sock:
                try:
                    read_data = socket.recv(1024)
                except:
                    read_data = []

                # Empty read means socket has disconnected
                if len(read_data) == 0:
                    with self.lock:
                        for handler in self._disconnect_listeners:
                            handler()
                        self.sockets = []
                        self._start_connection()

                while True:
                    buffer.extend(read_data)
                    try:
                        read_data = socket.recv(1024)
                    except:
                        break

                while True:
                    # Keep building until buffer has full packets
                    packet = PacketHeader(data=buffer)
                    if packet.built:
                        buffer = buffer[len(packet):]
                        with self.lock:
                            for handler in self._read_listeners:
                                handler(packet)
                    else:
                        break

    def send(self, packet):
        if len(self.sockets) != 0:
            print("SEND", packet)
            self.sockets[0].sendall(packet.raw())
        else:
            with self.lock:
                for handler in self._error_listeners:
                    handler("Cannot send a packet to the server")

    def stop(self):
        with self.lock:
            self._working = False
