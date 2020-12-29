from forum.common.packet import *
from random import randint, choice
import string


def random_string() -> str:
    length = randint(0, 30)
    letters = string.ascii_lowercase
    return ''.join(choice(letters) for i in range(length))


def generate_packet() -> PacketHeader:
    packet = PacketHeader()
    packet.source = randint(0, 1)
    packet.type = PacketType(randint(0, 6))
    packet.cid = randint(0, 10000000)
    packet.tid = randint(0, 10000000)

    data_size = randint(0, 20)
    for _ in range(data_size):
        data = PacketData()
        data.type = DataType(randint(0, 2))

        if data.type == 2:
            data.tfts = randint(0, 4)
        else:
            data.tfts = randint(0, 2 ** 64 - 1)

        data.s1 = random_string()
        data.s2 = random_string()
        packet.data.append(data)
    return packet


def test_completness(repeats=10):
    for _ in range(repeats):
        packet = generate_packet()
        assert packet.build

        packet_raw = packet.raw()
        partial_data = bytearray()

        for byte in packet_raw:
            PacketHeader(data=partial_data)
            partial_data.append(byte)

        complete_packet = PacketHeader(data=packet_raw)
        assert complete_packet.build

        for _ in range(randint(0, 1024)):
            partial_data.append(randint(0, 255))

        complete_packet = PacketHeader(data=partial_data)
        assert complete_packet.build
        assert len(complete_packet) == len(packet)


def test_serialization(repeats=10):
    for _ in range(repeats):
        packet = generate_packet()
        raw = packet.raw()
        tested_packet = PacketHeader(data=raw)

        assert packet.source == tested_packet.source
        assert packet.type == tested_packet.type
        assert packet.tid == tested_packet.tid
        assert packet.cid == tested_packet.cid
        assert packet.build == tested_packet.build
        assert len(packet.data) == len(tested_packet.data)
        assert len(packet) == len(tested_packet)
        assert len(raw) == len(packet)

        for pd, td in zip(packet.data, tested_packet.data):
            assert pd.type == td.type
            assert pd.s1 == td.s1
            assert pd.s2 == td.s2
            assert pd.tfts == td.tfts
            assert pd.build == td.build


if __name__ == "__main__":
    test_serialization(100)
    test_completness(100)
