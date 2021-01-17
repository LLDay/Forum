import time
from socket import *
from forum.common.packet import *

class Model:
    def __init__(self, clientSocket, packet: PacketHeader, cid, permission: bool, authors=[], topics=[], messages=[], users=[], tid=-1, usersToCids={}, usersToTids={}):
        packet.cid = cid
        packet.source = 1
        self.cid = cid
        self.users_to_cids = usersToCids
        self.users_to_tids = usersToTids
        self.client_socket = clientSocket
        self.packet = packet
        self.permission = permission
        self.authors = authors
        self.topics = topics
        self.messages = messages
        self.users = users
        self.tid = tid
        self._on_incoming_packet()

    def _on_incoming_packet(self):
        handler = {PacketType.REGISTRATION: self._on_registration_answer,
                    PacketType.AUTHENTICATION: self._on_authentication_answer,
                    PacketType.GET_TOPICS: self._on_send_topics,
                    PacketType.ADD_TOPIC: self._on_add_topics,
                    PacketType.GET_MESSAGES: self._on_send_messages,
                    PacketType.ADD_MESSAGE: self._on_add_messages,
                    PacketType.GET_USERS: self._on_send_users}[self.packet.type]
        handler()
        self._send_to_server()

    def _on_registration_answer(self):
        self._status(types="registration")

    def _on_authentication_answer(self):
        self._status(types="authentication")

    def _status(self, types: str):
        self.packet.data.clear()
        if self.permission:
            self.packet.data.append(PacketData(dtype=DataType.STATUS, status=0))
        elif types == "authentication":
            self.packet.data.append(PacketData(dtype=DataType.STATUS, status=2))
        elif types == "registration":
            self.packet.data.append(PacketData(dtype=DataType.STATUS, status=3))
        elif types == "error":
            self.packet.data.append(PacketData(dtype=DataType.STATUS, status=1))

    def _on_send_topics(self):
        self._on_send(array=self.topics)

    def _on_send_messages(self):
        self.packet.tid = self.tid
        self._on_send(array=self.messages)

    def _on_send(self, array):
        self.packet.data.clear()
        for author, array_item in zip(self.authors, array):
            self.packet.data.append(PacketData(dtype=DataType.STRING, time=int(time.time()), s1=author, s2=array_item))

    def _on_add_topics(self):
        self.packet.tid = self.tid
        self._status(types="error")

    def _on_add_messages(self):
        self.packet.tid = self.tid
        self._status(types="error")

    def _on_send_users(self):
        self.packet.data.clear()
        for user in self.users:
            self.packet.data.append(PacketData(dtype=DataType.STRING, time=int(time.time()), s1=user))

    def _send_to_server(self):
        print("sended: ", self.packet)
        self.client_socket.send(self.packet.raw())

        if self.packet.type == PacketType.ADD_TOPIC:
            self.packet.type = PacketType.GET_TOPICS
            print("array: ", self.topics)
            self._broadcast_data(array=self.topics)

        if self.packet.type == PacketType.ADD_MESSAGE:
            self.packet.type = PacketType.GET_MESSAGES
            self.packet.tid = self.tid
            self._broadcast_data(array=self.messages)

        if self.packet.type == PacketType.REGISTRATION:
            self.packet.type = PacketType.GET_USERS
            self._broadcast_data(array=self.users, is_registration=True)

    def _broadcast_data(self, array, is_registration=False):
        print("authors: ", self.authors)
        print('array: ', array)
        self.packet.data.clear()
        if not is_registration:
            for author, array in zip(self.authors, array):
                self.packet.data.append(PacketData(dtype=DataType.STRING, time=int(time.time()), s1=author, s2=array))
        else:
            for user in self.users:
                self.packet.data.append(PacketData(dtype=DataType.STRING, time=int(time.time()), s1=user))
        self._broadcast()

    def _broadcast(self):
        for client_socket, cid in self.users_to_cids.items():
            print('type: ', self.packet.type)
            if self.packet.type == PacketType.GET_MESSAGES:
                print(self.users_to_tids[client_socket])
                print(self.tid)
                if self.users_to_tids[client_socket] == self.tid:
                    print("broadcast:", self.packet)
                    client_socket.send(self.packet.raw())
            elif self.packet.type == PacketType.GET_TOPICS:
                print("broadcast:", self.packet)
                client_socket.send(self.packet.raw())
            elif self.packet.type == PacketType.GET_USERS:
                if cid != self.cid:
                    print("broadcast:", self.packet)
                    client_socket.send(self.packet.raw())
