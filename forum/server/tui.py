import select
from forum.server.model import Model
from threading import Thread
from socket import *
from forum.common.packet import *

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
            if message.data[0].s1 and message.data[0].s2:
                data_entered = [message.data[0].s1, message.data[0].s2]
                logins_returned = []
                if data_entered in cids_to_login.values():
                    permission = False
                else:
                    users = [data[0] for data in cids_to_login.values()]
                    if data_entered[0] in users:
                        permission = False
                if permission:
                    cids_to_login[self.cid] = data_entered
                    logins_returned.append(data_entered[0])
                    print("cids_to_login: ", cids_to_login)
            else:
                permission = False

            Model(clientSocket=self.notified_socket, packet=message, cid=self.cid, permission=permission, users=logins_returned, usersToCids=users_to_cids)

        elif message.type == PacketType.AUTHENTICATION:#-
            try:
                permission = False
                data_entered = [message.data[0].s1, message.data[0].s2]
                if data_entered in cids_to_login.values():

                    for cid, item in cids_to_login.items():
                        if item == data_entered:
                            permission = True
                            cids_to_login.pop(cid, None)
                            cids_to_login[self.cid] = [message.data[0].s1, message.data[0].s2]
                            break
            except:
                print("can't sign in")
                permission = False
            Model(clientSocket=self.notified_socket, packet=message, cid=self.cid, permission=permission)

        elif message.type == PacketType.GET_TOPICS:
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

        elif (message.type == PacketType.GET_MESSAGES):
            self.tid = message.tid
            users_to_tids[self.notified_socket] = self.tid

            messages_return = []
            authors_return = []
            r_from = message.data[0].getFrom()
            r_to = message.data[0].getTo()

            print("topics_to_messages: ", topics_to_messages)
            print("tids_to_topics: ", tids_to_topics)
            print("tid: ", self.tid)
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

            print("messages_for_topic: ", messages_for_topic)

            Model(clientSocket=self.notified_socket, packet=message, cid=self.cid, permission=permission,
                authors=authors_return, messages=messages_return, tid=self.tid)

        elif message.type == PacketType.ADD_TOPIC:
            topics_return = []
            authors_return = []
            for topic_item in message.data:
                topics_return.append(topic_item.s1)
                authors_return.append(cids_to_login[self.cid][0])
                topics_to_authors[topic_item.s1] = cids_to_login[self.cid][0]
                tids_to_topics[len(tids_to_topics)] = topic_item.s1
                topics_to_messages[topic_item.s1] = []

            print("topics_to_authors: ", topics_to_authors)
            print("tids_to_topics: ", tids_to_topics)
            print("topics_to_messages: ", topics_to_messages)

            print("topics_return: ", topics_return)
            print("authors_return: ", authors_return)
            Model(clientSocket=self.notified_socket, packet=message, cid=self.cid, permission=permission,
                authors=authors_return, topics=topics_return, tid=len(tids_to_topics)-1, usersToCids=users_to_cids)

        elif message.type == PacketType.ADD_MESSAGE:#-
            messages_return = []
            authors_return = []
            for message_item in message.data:
                topics_to_messages[tids_to_topics[message.tid]].append(message_item.s1)
                messages_return.append(message_item.s1)
                messages_to_authors[message_item.s1] = cids_to_login[self.cid][0]
                authors_return.append(cids_to_login[self.cid][0])

            print("topics_to_messages: ", topics_to_messages)
            print("messages_to_authors: ", messages_to_authors)
            Model(clientSocket=self.notified_socket, packet=message, cid=self.cid, permission=permission, authors=authors_return,
            messages=messages_return, tid=message.tid, usersToCids=users_to_cids, usersToTids=users_to_tids)

        elif (message.type == PacketType.GET_USERS):#-
            users_return = [login[0] for login in cids_to_login.values()]
            print("users_return: ", users_return)
            Model(clientSocket=self.notified_socket, packet=message, cid=self.cid, permission=permission, users=users_return)


class Server:
    def __init__(self, ip, port):
        self.server_socket = socket(AF_INET, SOCK_STREAM, 0)
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_socket.bind((ip, port))
        self.server_socket.listen()

        sockets_list.append(self.server_socket)
        socket_thread_created = []
        while True:
            read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
            for notified_socket in read_sockets:
                if notified_socket == self.server_socket:
                    client_socket, client_address = self.server_socket.accept()
                    global users_to_cids, users_to_tids, MAX_CIDS
                    sockets_list.append(client_socket)
                    print('Accepted new connection from user')
                    users_to_cids[client_socket] = MAX_CIDS
                    MAX_CIDS+=1
                    users_to_tids[client_socket] = -1

                else:
                    if notified_socket not in socket_thread_created:
                        receive_thread = ReceivingThread(notified_socket)
                        receive_thread.start()
                        socket_thread_created.append(notified_socket)

        for notified_socket in exception_sockets:
            sockets_list.remove(notified_socket)
            users_to_cids.pop(notified_socket, None)
