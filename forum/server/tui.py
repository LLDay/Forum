from socket import *
from forum.common.packet import *
from threading import Thread
import signal
import sys
import select
from forum.common.packet import PacketType
from forum.server.model import Model

ENCODING = 1024
MAX_CIDS = 0
sockets_list = []
users_to_cids = {}
users_to_tids = {}
cids_to_login = {}
topics_to_authors = {}
tids_to_topics = {}
topics_to_messages = {}
messages_to_authors = {}

def receive_message(client_socket):
    try:
        read = client_socket.recv(ENCODING)

        if not len(read):
            return False

        packet = PacketHeader(data=read)
    #       data = bytearray()
    #       while len(message) > 0:
    #           read = client_socket.recv(ENCODING)
    #           data.append(read)
        return packet
    except:
        return False

class ReceivingThread(Thread):
    def __init__(self, notifiedSocket):
        Thread.__init__(self)
        self.notified_socket = notifiedSocket
        self.tid = -1
        self.cid = users_to_cids.get(notifiedSocket)

    def run(self):
        open_connection = True
        while open_connection:
            message = receive_message(self.notified_socket)

            if message is False:
                print(f"Closed connection from client")
                open_connection = False
                sockets_list.remove(self.notified_socket)
                users_to_cids.pop(self.notified_socket, None)
                continue
            self._unparce_packet(message)

    def _unparce_packet(self, message):
        global users_to_cids, users_to_tids, cids_to_login, topics_to_authors, tids_to_topics, topics_to_messages, messages_to_authors
        print("recived: ", message)

        permission = True
        if message.type == PacketType.REGISTRATION:#-
            cids_to_login[self.cid] = {message.data[0].s1, message.data[0].s2}
            Model(clientSocket=self.notified_socket, packet=message, cid=self.cid, permission=permission)

        elif message.type == PacketType.AUTHENTICATION:#-
            if (cids_to_login[self.cid] != {message.data[0].s1, message.data[0].s2}):
                permission = False
            Model(clientSocket=self.notified_socket, packet=message, cid=self.cid, permission=permission)

        elif message.type == PacketType.GET_TOPICS:#-
            #for i in range(1,5):
            #    topics_to_messages[str(i)] = {i, "ieei", "eue"}
            #    topics_to_authors[str(i)] = "author"
            topics_return = []
            authors_return = []
            r_from = message.data[0].getFrom()
            r_to = message.data[0].getTo()

            if r_from < len(topics_to_messages) and r_from <= r_to:
                if r_to < len(topics_to_messages):
                    topics_return = list(topics_to_messages.keys())[r_from:r_to]
                else:
                    topics_return = list(topics_to_messages.keys())[r_from:]
                for topic in topics_return:
                    authors_return.append(topics_to_authors[topic])
            else:
                permission = False

            Model(clientSocket=self.notified_socket, packet=message, cid=self.cid, permission=permission, authors=authors_return,
                topics=topics_return)

        elif (message.type == PacketType.GET_MESSAGES): #need checking
            self.tid = message.tid
            users_to_tids[self.notified_socket] = self.tid

            messages_return = []
            authors_return = []
            r_from = message.data[0].getFrom()
            r_to = message.data[0].getTo()

            #cids_to_login = {0: "fkfk"}
            #for i in range(1,3):
            #    topics_to_messages[str(i)] = [i, "ieei", "eue", "sjs", "aqq"]
            #    tids_to_topics[2] = str(i)
            #    topics_to_authors[str(i)] = "author"

            #messages_to_authors["ieei"] = "author1"
            #messages_to_authors["eue"] = "author2"
            #messages_to_authors["sjs"] = "author3"
            #messages_to_authors["aqq"] = "author4"

            messages_for_topic = topics_to_messages[tids_to_topics[self.tid]]


            if r_from < len(messages_for_topic) and r_from <= r_to:
                if r_to < len(messages_for_topic):
                    messages_return = messages_for_topic[r_from:r_to]
                else:
                    messages_return = messages_for_topic[r_from:]
                for messages in messages_return:
                    authors_return.append(messages_to_authors[messages])
            else:
                permission = False

            Model(clientSocket=self.notified_socket, packet=message, cid=self.cid, permission=permission,
                authors=authors_return, messages=messages_return, tid=self.tid)

        elif message.type == PacketType.ADD_TOPIC:#-
            #cids_to_login = {0: "fkfk"}
            for topic_item in message.data:
                topics_to_authors[topic_item.s1] = cids_to_login[self.cid]
                tids_to_topics[len(tids_to_topics)] = topic_item.s1
                topics_to_messages[topic_item.s1] = []
            Model(clientSocket=self.notified_socket, packet=message, cid=self.cid, permission=permission, tid=len(tids_to_topics)-1)
            #authors_return = []
            #messages_array = topics_to_messages[tids_to_topics[len(tids_to_topics)]]
            #for message_item in messages_array:
            #    authors_return.append(messages_to_authors[message_item])

            #Model(clientSocket=self.notified_socket, packet=message, cid=self.cid, permission=permission,
            #    authors=authors_return, messages=messages_array, tid=len(tids_to_topics)-1, usersToCids=users_to_cids)

        elif message.type == PacketType.ADD_MESSAGE:#-
            #cids_to_login = {0: "fkfk"}
            #for i in range(1,3):
            #    topics_to_messages[str(i)] = [i, "ieei", "eue"]
            #    tids_to_topics[2] = str(i)
            #    topics_to_authors[str(i)] = "author"
            messages_return = []
            authors_return = []
            for message_item in message.data:
                topics_to_messages[tids_to_topics[message.tid]].append(message_item.s1)
                messages_return.append(message_item.s1)
                messages_to_authors[message_item.s1] = cids_to_login[self.cid]
                authors_return.append(cids_to_login[self.cid])
            Model(clientSocket=self.notified_socket, packet=message, cid=self.cid, permission=permission, authors=authors_return,
            messages=messages_return, tid=message.tid, usersToCids=users_to_cids, usersToTids=users_to_tids)

        elif (message.type == PacketType.GET_USERS):#-
            users_return = cids_to_login.values()
            Model(clientSocket=self.notified_socket, packet=message, cid=self.cid, permission=permission, users=users_return)

class Server:
    def __init__(self, ip, port):
        self.server_socket = socket(AF_INET, SOCK_STREAM, 0)
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_socket.bind((ip, port))
        self.server_socket.listen()

        sockets_list.append(self.server_socket)
        print("here1")
        socket_thread_created = []
        while True:
            read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
            for notified_socket in read_sockets:
                if notified_socket == self.server_socket:
                    client_socket, client_address = self.server_socket.accept()
                    global users_to_cids, users_to_tids, MAX_CIDS
                    #packet = receive_message(client_socket) #problem
                    #if user is not False:
                    sockets_list.append(client_socket)
                    print('Accepted new connection from user')
                    users_to_cids[client_socket] = MAX_CIDS
                    MAX_CIDS+=1
                    users_to_tids[client_socket] = -1

                else:
                    #print("sock: ", socket_thread_created)
                    if notified_socket not in socket_thread_created:
                        print("new thread")
                        # create an another to receive data
                        receive_thread = ReceivingThread(notified_socket)
                        # start thread
                        receive_thread.start()
                        socket_thread_created.append(notified_socket)

        for notified_socket in exception_sockets:
            sockets_list.remove(notified_socket)
            users_to_cids.pop(notified_socket, None)
