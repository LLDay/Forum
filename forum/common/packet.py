from enum import IntEnum


class PacketType(IntEnum):
    REGISTRATION = 0,
    AUTHENTICATION = 1,
    GET_TOPICS = 2,
    GET_MESSAGES = 3,
    ADD_TOPIC = 4,
    ADD_MESSAGE = 5,
    GET_USERS = 6


class DataType(IntEnum):
    STRING = 0,
    RANGE = 1,
    STATUS = 2


class Status(IntEnum):
    OK = 0,
    PERMISSION_ERROR = 1,
    AUTHENTICATION_ERROR = 2,
    REGISTRATION_ERROR = 3,
    FORMAT_ERROR = 4


class PacketData:
    def __init__(self, data=None, dtype=DataType.STRING, status=0, time=0, r_from=0, r_to=0, s1=str(), s2=str()):
        self.type = DataType(dtype)
        self.s1 = s1
        self.s2 = s2
        self.tfts = 0
        self._range_shift = 2 ** 32
        self.build = True

        if self.type is DataType.STRING:
            self.setTime(time)
        elif self.type is DataType.RANGE:
            self.setFrom(r_from)
            self.setTo(r_to)
        elif self.type is DataType.STATUS:
            self.setStatus(status)

        if data is not None:
            self.build = False

            if len(data) < self.__len__():
                return

            self.type = DataType(data[0])
            self.tfts = int.from_bytes(data[1:9], "big")

            size1 = int.from_bytes(data[9:13], "big")
            if len(data) < self.__len__() + size1:
                return
            self.s1 = data[13:13 + size1].decode("UTF-8")

            size2 = int.from_bytes(data[13 + size1:17 + size1], "big")
            if len(data) < self.__len__() + size2:
                return
            self.s2 = data[17 + size1:17 + size1 + size2].decode("UTF-8")

            self.build = True

    def __len__(self) -> int:
        return 17 + len(self.s1) + len(self.s2)

    def __str__(self) -> str:
        s = "=====  DATA  =====\n"
        s += f"  Type: {self.type} ({self.type.name})\n"
        if self.type is DataType.STRING:
            s += f"  Time: {self.getTime()}\n"
        elif self.type is DataType.RANGE:
            s += f"  From: {self.getFrom()}\n"
            s += f"    To: {self.getTo()}\n"
        elif self.type is DataType.STATUS:
            s += f"  Stat: {self.tfts} ({Status(self.tfts).name})\n"
        s += f" Size1: {len(self.s1)}\n"
        s += f'    S1: "{self.s1}"\n'
        s += f" Size2: {len(self.s2)}\n"
        s += f'    S2: "{self.s2}"\n'
        return s

    def getTime(self) -> int:
        if self.type is not DataType.STRING:
            raise RuntimeError("The data doesn't have a time field")
        return self.tfts

    def setTime(self, time: int):
        self.tfts = time
        self.type = DataType.STRING

    def getFrom(self) -> int:
        if self.type is not DataType.RANGE:
            raise RuntimeError("The data doesn't have a r_from field")
        return self.tfts // self._range_shift

    def setFrom(self, from_: int):
        self.tfts = from_ * self._range_shift + self.tfts % self._range_shift
        self.type = DataType.RANGE

    def getTo(self) -> int:
        if self.type is not DataType.RANGE:
            raise RuntimeError("The data doesn't have a r_to field")
        return self.tfts % self._range_shift

    def setTo(self, to: int):
        self.tfts = self.tfts - self.tfts % self._range_shift + to
        self.type = DataType.RANGE

    def getStatus(self) -> Status:
        if self.type is not DataType.STATUS:
            raise RuntimeError("The data doesn't have a status field")
        return Status(self.tfts)

    def setStatus(self, status: Status):
        self.tfts = Status(status).value
        self.type = DataType.STATUS

    def raw(self) -> bytes:
        r = b""
        r += self.type.to_bytes(1, "big")
        r += self.tfts.to_bytes(8, "big")
        r += len(self.s1).to_bytes(4, "big")
        r += self.s1.encode("UTF-8")
        r += len(self.s2).to_bytes(4, "big")
        r += self.s2.encode("UTF-8")
        return r


class PacketHeader:
    def __init__(self, data=None, source=0, ptype=0, cid=0, tid=0):
        self.source = source
        self.type = PacketType(ptype)
        self.cid = cid
        self.tid = tid
        self.data = []
        self.build = True

        if data is not None:
            self.build = False
            if (len(data) < self.__len__()):
                return

            st = data[0]
            self.source = st // 128
            self.type = PacketType(st % 128)
            self.cid = int.from_bytes(data[1:5], "big")
            data_size = int.from_bytes(data[5:9], "big")
            self.tid = int.from_bytes(data[9:13], "big")
            data = data[13:]

            for _ in range(data_size):
                if len(data) == 0:
                    return

                packet_data = PacketData(data=data)
                if packet_data.build:
                    self.data.append(packet_data)
                    data = data[len(packet_data):]
                else:
                    return

            self.build = data_size == len(self.data)

    def __len__(self) -> int:
        return 13 + sum(len(d) for d in self.data)

    def __str__(self) -> str:
        source = {0: "CLIENT", 1: "SERVER"}
        s = "===== HEADER =====\n"
        s += f"Source: {self.source} ({source[self.source]})\n"
        s += f"  Type: {self.type} ({self.type.name})\n"
        s += f"   Cid: {self.cid}\n"
        s += f"   Tid: {self.tid}\n"
        s += f" Ndata: {len(self.data)}\n"
        s += '\n'.join([str(d) for d in self.data])
        return s

    def add_data_field(self, data: PacketData):
        self.data.append(data)

    def raw(self) -> bytes:
        st = self.source * 128
        st += self.type.value
        r = st.to_bytes(1, "big")
        r += self.cid.to_bytes(4, "big")
        r += len(self.data).to_bytes(4, "big")
        r += self.tid.to_bytes(4, "big")
        r += b"".join(dr.raw() for dr in self.data)
        return r
