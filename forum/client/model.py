import time

from typing import List

from forum.client.connection import ServerConnection
from forum.client.gui import Client, Authentication, Message, Topic, TopicPanel
from forum.common.packet import PacketHeader, PacketData, PacketType, Status, DataType
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.Qt import Qt
from pdb import *


class Model(QObject):
    new_topic = pyqtSignal(int, PacketData)
    new_message = pyqtSignal(int, PacketData)
    clear_message = pyqtSignal()

    def __init__(self, ip: str, port: int, timeout_sec=0.5, parent=None):
        super(Model, self).__init__(parent)
        self.gui = Client(self)
        self.authentication = Authentication(self)
        self.authentication.show()

        self.cid = 0
        self.tid = 0
        self.timeout = timeout_sec

        self.connection = ServerConnection(ip, port)
        self.connection.add_incoming_packet_handler(self._on_incoming_packet)
        self.connection.add_disconnect_handler(self._on_client_disconnected)
        self.connection.add_connection_handler(self._on_client_connected)
        self.connection.add_error_handler(self._on_connection_error)
        self.connection.start()

        self.new_topic.connect(
            self.gui.topic_panel.new_topic, Qt.BlockingQueuedConnection)
        self.new_message.connect(
            self.gui.topic_panel.message_panel.show_message, Qt.BlockingQueuedConnection)
        self.clear_message.connect(
            self.gui.topic_panel.message_panel.text_edit.clear, Qt.BlockingQueuedConnection)

    def _on_client_connected(self):
        print("connected")
        self.authentication.setStatus()
        self.gui.setStatus()
        if self.is_user_entered():
            self.request_topics()
            self.request_users()

    def _on_client_disconnected(self):
        print("disconnected")

    def _on_connection_error(self, description: str):
        self.gui.setStatus(description)
        self.authentication.setStatus(description)

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
        print("RECEIVE", packet)
        handler = {PacketType.REGISTRATION: self._on_authentication_answer,
                   PacketType.AUTHENTICATION: self._on_authentication_answer,
                   PacketType.GET_TOPICS: self._on_receive_topics,
                   PacketType.ADD_TOPIC: self._on_receive_topics,
                   PacketType.GET_MESSAGES: self._on_receive_messages,
                   PacketType.ADD_MESSAGE: self._on_receive_messages,
                   PacketType.GET_USERS: self._on_receive_users}[packet.type]
        handler(packet)

    def _on_receive_topics(self, packet: PacketHeader):
        size = len(self.gui.topic_panel)
        for i, data in enumerate(packet.data):
            if data.type == DataType.STATUS:
                if data.getStatus() != Status.OK:
                    self.gui.setStatus("Cannot create topic")
            else:
                self.new_topic.emit(size + i, data)

    def _on_receive_messages(self, packet: PacketHeader):
        size = len(self.gui.topic_panel)
        if self.tid == packet.tid:
            for i, data in enumerate(packet.data):
                if data.type == DataType.STATUS:
                    if data.getStatus() == Status.OK:
                        self.clear_message.emit()
                    else:
                        self.gui.setStatus("Cannot send message")
                else:
                    self.new_message.emit(size + i, data)

    def _on_receive_users(self, packet: PacketHeader):
        for data in packet.data:
            self.gui.users_panel.show_user(data.s1 + data.s2)

    def _on_authentication_answer(self, packet: PacketHeader):
        if len(packet.data) != 0:
            status = packet.data[-1].getStatus()
            if status == Status.OK:
                self.cid = packet.cid
                self.gui.show()
                self.authentication.close()
                self.request_topics()
                self.request_users()
            else:
                if packet.type == PacketType.REGISTRATION:
                    self.authentication.setStatus("Cannot register")
                elif packet.type == PacketType.AUTHENTICATION:
                    self.authentication.setStatus("Cannot authenticate")

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
        packet = self._get_header(PacketType.GET_USERS)
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
