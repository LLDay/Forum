import enum
import threading
import time

from socket import *
from typing import List

from forum.client.gui import Client, Message, Topic
from forum.common.packet import PacketHeader, PacketData, PacketType, Status
from forum.common.events_listener import EventListener


class Model:
    def __init__(self, ip: str, port: int, timeout_sec=0.5):
        self.gui = Client(self)
        self._ip = ip
        self._port = port
        self.sock = None
        self.cid = 0
        self.tid = 0
        self.timeout = timeout_sec
        self.events = EventListener()
        self.events.add_incoming_packet_handler(self._on_incoming_packet)
        self.connect()

    def connect(self):
        connect_thread = threading.Thread(
            target=self._connect_loop, daemon=True)
        connect_thread.start()

    def _connect_loop(self):
        while True:
            try:
                self.sock = socket(AF_INET, SOCK_STREAM, 0)
                self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                self.sock.connect((self._ip, self._port))
                break
            except ConnectionRefusedError:
                self.gui.setStatus("Unable to connect to the server")
                time.sleep(1)
        self._on_client_connected()

    def _on_client_connected(self):
        self.request_topics()
        self.requeist_users()
        self.events.add_socket(self.sock)

    def _on_client_disconencted(self, sock):
        sock.close()
        connect()

    def _get_header(self, ptype: PacketType) -> PacketHeader:
        return PacketHeader(ptype=ptype, cid=self.cid, source=0)

    def _send_to_server(self, packet: PacketHeader):
        self.sock.sendall(packet.raw())

    def is_user_entered(self) -> bool:
        return self.cid != 0

    def _register_authenticate(self, ptype: PacketType, login: str, passwd: str):
        packet = self._get_header(ptype)
        packet.data.append(PacketData(s1=login, s2=passwd))
        self._send_to_server(packet)

    def register(self, login: str, passwd: str):
        self._register_authenticate(
            PacketType.REGISTRATION, login, passwd)

    def authenticate(self, login: str, passwd: str):
        self._register_authenticate(
            PacketType.AUTHENTICATION, login, passwd)

    def _on_incoming_packet(self, packet: PacketHeader):
        handler = {PacketType.REGISTRATION: self._on_authentication_answer,
                   PacketType.AUTHENTICATION: self._on_authentication_answer,
                   PacketType.GET_TOPICS: self._on_receive_topics,
                   PacketType.ADD_TOPIC: self._on_receive_topics,
                   PacketType.GET_MESSAGES: self._on_receive_messages,
                   PacketType.ADD_MESSAGE: self._on_receive_messages,
                   Packet.Type.GET_USERS: self._on_receive_users}[packet.type]
        handler(packet)

    def _on_receive_topics(self, packet: PacketHeader):
        topic_panel = self.gui.topic_panel
        for i, data in enumerate(packet.data):
            topic = Topic(len(self.gui.topic_panel) + i, data)
            topic_panel.show_topic(topic)

    def _on_receive_messages(self, packet: PacketHeader):
        if self.tid == packet.tid:
            for i, data in enumerate(packet.data):
                message = Message(
                    len(self.gui.topic_panel.message_panel) + i, data)
                self.gui.topic_panel.message_panel.show_message(message)

    def _on_receive_users(self, packet: PacketHeader):
        for data in packet.data:
            self.gui.users_panel.show_user(data.s1 + data.s2)

    def _on_authentication_answer(self, packet: PacketHeader):
        if len(packet.data) != 0:
            status = packet.data[-1].tft
            if status == Status.OK:
                self.cid = packet.cid
                self.gui.show()
                self.working = True

    def request_topics(self, t_from=0, t_to=2**32-1):
        self.gui.topic_panel.clear_topics()
        packet = self._get_header(PacketType.GET_TOPICS)
        packet.data.append(PacketData(
            dtype=DataType.RANGE, r_from=t_from, r_to=t_to))
        self._send_to_server(packet)

    def request_messages(self, tid: int, m_from=0, m_to=2**32-1):
        self.gui.topic_panel.message_panel.clear_messages()
        packet = self._get_header(PacketType.GET_MESSAGES)
        packet.tid = tid
        packet.data.append(PacketData(
            dtype=DataType.RANGE, r_from=m_from, r_to=m_to))
        self.tid = tid
        self._send_to_server(packet)

    def requeist_users(self):
        packet = self._get_header(6)
        self._send_to_server(packet)

    def add_topic(self, name: str):
        packet = self._get_header(PacketType.ADD_TOPIC)
        packet.data.append(PacketData(s1=name))
        self._send_to_server(packet)

    def add_message(self, text: str):
        packet = self._get_header(PacketType.ADD_MESSAGE)
        packet.tid = self.tid
        packet.data.append(PacketData(s1=text))
        self._send_to_server(packet)
