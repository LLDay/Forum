import select
import threading

from collections.abc import Iterable
from forum.common.packet import PacketHeader


class EventListener:
    def __init__(self, timeout=0.5):
        print("ok")
        self.sockets = []
        self.timeout = timeout

        self._working = True
        self._disconnect_listeners = []
        self._read_listeners = []

        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._get_packets, daemon=True)
        self.thread.start()

    def add_socket(self, socket):
        with self.lock:
            self.sockets.append(socket)

    def remove_socket(self, socket):
        with self.lock:
            self.sockets.remove(socket)

    # Excepts function accepted socket object as an argument
    def add_disconnect_handler(self, function):
        with self.lock:
            self._disconnect_listeners.append(function)

    # Excepts function accepted PacketHeader object as an argument
    def add_incoming_packet_handler(self, function):
        with self.lock:
            self._read_listeners.append(function)

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
                read_data = socket.recv(1024)

                # Empty read means socket has disconnected
                if len(read_data) == 0:
                    with self.lock:
                        self.sockets.remove(socket)
                        for handler in self._disconnect_listeners:
                            handler(socket)

                while len(read_data) > 0:
                    buffer.append(read_data)
                    read_data = socket.recv(1024)

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

    def stop(self):
        with self.lock:
            self._working = False
