import enum
import threading
import time

from typing import List

from forum.client.connection import ServerConnection
from forum.client.gui import Client, Message, Topic
from forum.common.packet import PacketHeader, PacketData, PacketType, Status, DataType


class Model:
    def __init__(self, ip: str, port: int, timeout_sec=0.5):
        self.gui = Client(self)
        self._ip = ip
        self._port = port
        self.cid = 0
        self.tid = 0
        self.timeout = timeout_sec

        self.connection = ServerConnection()
        self.connection.add_incoming_packet_handler(self._on_incoming_packet)
        self.connection.add_disconnect_handler(self._on_client_disconnected)
        self.connection.add_connection_handler(self._on_client_connected)
        self.connection.add_error_handler(self._on_connection_error)
        self.connection.start()

    def _on_client_connected(self):
        self.request_topics()
        self.request_users()
        self.events.add_socket(self.connection.sock)

    def _on_client_disconnected(self):
        self.connection.connect()

    def _on_connection_error(self, description: str):
        self.gui.setStatus(description)

    def _get_header(self, ptype: PacketType) -> PacketHeader:
        return PacketHeader(ptype=ptype, cid=self.cid, source=0)

    def is_user_entered(self) -> bool:
        return self.cid != 0

    def _register_authenticate(self, ptype: PacketType, login: str, passwd: str):
        packet = self._get_header(ptype)
        packet.add_data_field(PacketData(s1=login, s2=passwd))
        self.connection.send(packet)

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
                   PacketType.GET_USERS: self._on_receive_users}[packet.type]
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
        packet.add_data_field(PacketData(
            dtype=DataType.RANGE, r_from=t_from, r_to=t_to))
        self.connection.send(packet)

    def request_messages(self, tid: int, m_from=0, m_to=2**32-1):
        self.gui.topic_panel.message_panel.clear_messages()
        packet = self._get_header(PacketType.GET_MESSAGES)
        packet.tid = tid
        packet.data.append(PacketData(
            dtype=DataType.RANGE, r_from=m_from, r_to=m_to))
        self.tid = tid
        self.connection.send(packet)

    def request_users(self):
        packet = self._get_header(6)
        self.connection.send(packet)

    def add_topic(self, name: str):
        packet = self._get_header(PacketType.ADD_TOPIC)
        packet.add_data_field(PacketData(s1=name))
        self.connection.send(packet)

    def add_message(self, text: str):
        packet = self._get_header(PacketType.ADD_MESSAGE)
        packet.tid = self.tid
        packet.add_data_field(PacketData(s1=text))
        self.connection.send(packet)
