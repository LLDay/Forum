from socket import *
from forum.common.packet import *


class Model:
    def __init__(self, ip, port):
        self.sock = socket(AF_INET, SOCK_STREAM, 0)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.sock.bind((ip, port))
        self.cid = -1

    def _get_header(self, ptype: PacketType) -> PacketHeader:
        return PacketHeader(ptype=ptype, cid=self.cid, source=0)

    def _talk_with_server(self, packet: PacketHeader) -> PacketHeader:
        # self.sock.sendall(packet.raw())
        data = bytearray()
        read = [0]
        # while len(read) > 0:
        # read = self.sock.recv(1024)
        # data.append(read)

        # packet = PacketHeader(data=read)
        packet = PacketHeader(source=1, ptype=PacketType.REGISTRATION, cid=3)
        data = PacketData(s1="Denis", s2="Message text")
        packet.data.append(data)
        return packet

    def _register_authenticate(self, ptype: PacketType, login: str, passwd: str) -> int:
        packet = self._get_header(ptype)
        packet.data.append(PacketData(s1=login, s2=passwd))
        answer = self._talk_with_server(packet)
        status = answer.data[-1].tft
        if status == Status.OK:
            self.cid = answer.cid
        return status

    def is_user_entered(self) -> bool:
        return self.cid != -1

    def register(self, login: str, passwd: str) -> int:
        return self._register_authenticate(PacketType.REGISTRATION, login, passwd)

    def authenticate(self, login: str, passwd: str) -> int:
        return self._register_authenticate(PacketType.AUTHENTICATION, login, passwd)

    def get_topics(self, t_from=0, t_to=2**32-1) -> list[PacketData]:
        packet = self._get_header(PacketType.GET_TOPICS)
        packet.data.append(PacketData(
            dtype=DataType.RANGE, r_from=t_from, r_to=t_to))
        answer = self._talk_with_server(packet)
        return answer.data

    def get_messages(self, tid: int, m_from=0, m_to=2**32-1) -> list[PacketData]:
        packet = self._get_header(PacketType.GET_MESSAGES)
        packet.tid = tid
        packet.data.append(PacketData(
            dtype=DataType.RANGE, r_from=m_from, r_to=m_to))
        answer = self._talk_with_server(packet)
        return answer.data

    def add_topic(self, name: str) -> PacketData:
        packet = self._get_header(PacketType.ADD_TOPIC)
        packet.data.append(PacketData(s1=name))
        answer = self._talk_with_server(packet)
        return answer.data[-1]

    def add_message(self, tid: int, text: str) -> PacketData:
        packet = self._get_header(PacketType.ADD_MESSAGE)
        packet.tid = tid
        packet.data.append(PacketData(s1=text))
        answer = self._talk_with_server(packet)
        return answer.data[-1]

    def get_users(self) -> list[str]:
        packet = self._get_header(6)
        answer = self._talk_with_server(packet)
        return [d.s1 + d.s2 for d in answer.data]
