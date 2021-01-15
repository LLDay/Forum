import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from forum.common.packet import Status


def _get_string_time(time_since_epoch: int) -> str:
    localtime = QDateTime.fromSecsSinceEpoch(time_since_epoch)
    return localtime.toString("dd.MM.yyyy hh:mm")


class Topic(QWidget):
    def __init__(self, tid: int, topic):
        QWidget.__init__(self)
        self.creation_time = topic.getTime()
        self.author = topic.s1
        self.name = topic.s2
        self.tid = tid

        layout = QHBoxLayout(self)
        name_label = QLabel(self.name)
        author_label = QLabel(self.author)

        time_label = QLabel(_get_string_time(self.creation_time))
        time_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        name_label.setWordWrap(True)
        author_label.setWordWrap(True)
        author_label.setAlignment(Qt.AlignRight)

        layout.addWidget(name_label)
        layout.addWidget(author_label)
        layout.addWidget(time_label)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)


class Message(QWidget):
    def __init__(self, mid: int, message):
        QWidget.__init__(self)
        self.creation_time = message.getTime()
        self.author = message.s1
        self.text = message.s2
        self.mid = mid

        author_label = QLabel(self.author)
        time_label = QLabel(_get_string_time(self.creation_time))
        text_label = QLabel(self.text)

        time_label.setAlignment(Qt.AlignRight)
        text_label.setWordWrap(True)

        title_layout = QHBoxLayout()
        title_layout.addWidget(author_label)
        title_layout.addWidget(time_label)

        layout = QVBoxLayout(self)
        layout.addLayout(title_layout)
        layout.addWidget(text_label)


class MessagePanel(QGroupBox):
    def __init__(self, model):
        QGroupBox.__init__(self)
        self.model = model

        input_field_size = 50
        sendButton = QPushButton()
        sendButton.setText("Send")
        sendButton.setFixedHeight(input_field_size)
        sendButton.setShortcut("Ctrl+Return")
        sendButton.clicked.connect(self._send_message)

        self.text_edit = QTextEdit(self)
        self.text_edit.setMaximumHeight(input_field_size)

        edit_button = QHBoxLayout()
        edit_button.addWidget(self.text_edit)
        edit_button.addWidget(sendButton)

        self.messages = QListWidget(self)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.messages)
        main_layout.addLayout(edit_button)

    def __len__(self):
        return len(self.messages)

    def _send_message(self):
        self.model.add_message(self.text_edit.toPlainText())

    def clear_messages(self):
        self.messages.clear()

    def clear_textbox(self):
        self.text_edit.clear()

    def show_message(self, message: Message):
        item = QListWidgetItem(self.messages)
        item.setSizeHint(message_widget.sizeHint())
        item.setFlags(Qt.NoItemFlags)
        self.messages.addItem(item)
        self.messages.setItemWidget(item, message_widget)


class TopicPanel(QGroupBox):
    def __init__(self, model):
        QGroupBox.__init__(self)
        self.model = model
        self.message_panel = MessagePanel(self.model)
        self.setTitle("Topics")

        addTopicButton = QPushButton()
        addTopicButton.setText("Add topic")
        addTopicButton.clicked.connect(self._add_topic)
        self.topics = QListWidget(self)
        self.topics.itemClicked.connect(self._open_topic)

        layout = QVBoxLayout(self)
        layout.addWidget(self.topics)
        layout.addWidget(addTopicButton)

    def __len__(self):
        return len(self.topics)

    def _add_topic(self):
        topic_name, ok = QInputDialog.getText(
            self, "New topic", "Topic name:", QLineEdit.Normal)
        if ok:
            self.model.add_topic(topic_name)

    def _open_topic(self, item: QListWidgetItem):
        topic = self.topics.itemWidget(item)
        self.model.request_messages(topic.tid)

    def clear_topics(self):
        self.topics.clear()

    def show_topic(self, topic: Topic):
        item = QListWidgetItem(self.topics)
        item.setSizeHint(topic.sizeHint())
        self.topics.addItem(item)
        self.topics.setItemWidget(item, topic)


class UsersPanel(QGroupBox):
    def __init__(self, model):
        QGroupBox.__init__(self)
        self.model = model
        self.users = QListWidget(self)
        self.setTitle("Users")

        layout = QVBoxLayout(self)
        layout.addWidget(self.users)

    def clear_users(self):
        self.users.clear()

    def show_user(self, user: str):
        self.users.addItem(user)


class Client(QWidget):
    def __init__(self, model):
        QWidget.__init__(self)
        self.model = model

        self.setWindowTitle("Forum")
        self.topic_panel = TopicPanel(self.model)
        self.users_panel = UsersPanel(self.model)
        self._statusLabel = QLabel(self)

        tu_splitter = QSplitter(self)
        tu_splitter.setOrientation(Qt.Horizontal)

        tum_splitter = QSplitter(self)
        tum_splitter.setOrientation(Qt.Vertical)

        tu_splitter.addWidget(self.users_panel)
        tu_splitter.addWidget(self.topic_panel)
        tu_splitter.setStretchFactor(0, 1)
        tu_splitter.setStretchFactor(1, 3)

        tum_splitter.addWidget(tu_splitter)
        tum_splitter.addWidget(self.topic_panel.message_panel)
        tum_splitter.setStretchFactor(0, 1)
        tum_splitter.setStretchFactor(1, 3)

        layout = QVBoxLayout(self)
        layout.addWidget(tum_splitter)
        layout.addWidget(self._statusLabel)
        self.setLayout(layout)

    def setStatus(self, text=""):
        if len(text) == 0:
            self._statusLabel.hide()
        else:
            self._statusLabel.setText(text)
            self._statusLabel.show()


class Authentication(QDialog):
    def __init__(self, model):
        QDialog.__init__(self)
        self.model = model
        self.setWindowTitle("Authentication")
        self.status = QLabel()
        self.status.setStyleSheet("QLabel {color: red;}")
        self.status.hide()

        self.login = QLineEdit()
        self.password = QLineEdit()

        sign_in = QPushButton("Sign in")
        sign_up = QPushButton("Sign up")

        sign_in.clicked.connect(self.sign_in)
        sign_up.clicked.connect(self.sign_up)

        hbox = QHBoxLayout()
        hbox.addWidget(sign_in)
        hbox.addWidget(sign_up)

        vbox = QVBoxLayout()
        vbox.addWidget(self.status)
        vbox.addLayout(hbox)

        form_layout = QFormLayout(self)
        form_layout.addRow("Login:", self.login)
        form_layout.addRow("Password:", self.password)
        form_layout.addRow(vbox)
        self.setLayout(form_layout)

    def setStatus(self, text: str):
        self.status.show()
        self.status.setText(text)

    def _sign_in_up(self, func, status_error: str):
        try:
            status = func(self.login.text(), self.password.text())
            if status != Status.OK:
                setStatus(status_error)
            else:
                self.close()
        except Exception as e:
            self.setStatus(str(e))

    def sign_in(self):
        self._sign_in_up(self.model.authenticate, "Invalid login or password")

    def sign_up(self):
        self._sign_in_up(self.model.register, "Cannot register")
