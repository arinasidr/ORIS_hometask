import sys
import json
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QApplication
from PyQt6.QtCore import *

from client_chat import ChatClient

class ChatWidget(QWidget):
    def __init__(self, name='Anonymous', text=''):
        super().__init__()
        self.name = name
        self.text = text

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 8, 15, 8)

        self.name_label = QLabel(self.name)
        self.name_label.setStyleSheet("font-weight: bold; color: #90EE90;")
        layout.addWidget(self.name_label)

        self.text_label = QLabel(self.text) 
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("color: #;")
        self.text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.text_label)

        self.setLayout(layout)
    
    def sizeHint(self):
        return QSize(400, 60)  

class ChatManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat")

        self.client = ChatClient()
        self.client.message_received.connect(self.handle_server_message)

        if not self.client.start_client():
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к серверу")
            sys.exit(1)

        layout = QVBoxLayout(self)
        self.room_input = QLineEdit()
        self.room_input.setPlaceholderText("Введите номер комнаты...")
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Введите ваше имя...")
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Введите сообщение...")
        self.message_input.returnPressed.connect(self.send_message)

        self.join_button = QPushButton("Присоединиться к комнате")
        self.send_button = QPushButton("Отправить сообщение")
        self.leave_button = QPushButton("Покинуть комнату")

        self.messages_list = QListWidget()

        layout.addWidget(QLabel("Комната:"))
        layout.addWidget(self.room_input)
        layout.addWidget(QLabel("Ваше имя:"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Сообщение:"))
        layout.addWidget(self.message_input)
        layout.addWidget(self.join_button)
        layout.addWidget(self.send_button)
        layout.addWidget(self.leave_button) 
        layout.addWidget(QLabel("Сообщения:"))
        layout.addWidget(self.messages_list)

        self.setLayout(layout)

        self.join_button.clicked.connect(self.join_room)
        self.send_button.clicked.connect(self.send_message)
        self.leave_button.clicked.connect(self.leave_room)
        
    def join_room(self):
        room_number = self.room_input.text().strip()
        username = self.username_input.text().strip()

        if room_number:
            self.client.username = username
            self.client.join_room(room_number, username)

    def send_message(self):
        text = self.message_input.text().strip()

        if not text:
            return

        if text and self.client.current_room:
            if self.client.send_message(text):
                self.message_input.clear()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось отправить сообщение")
        else:
            QMessageBox.warning(self, "Ошибка", "Сначала присоединитесь к комнате")

    def leave_room(self):
        if self.client.current_room:
            self.client.leave_room()
            self.add_message("Система", "Вы покинули комнату")
            self.client.current_room = None
        else:
            QMessageBox.information(self, "Информация", "Вы не в комнате")

    def add_message(self, username, text):
        chat_widget = ChatWidget(
            name = username,
            text = text,
        )

        item = QListWidgetItem()
        item.setSizeHint(chat_widget.sizeHint())
        self.messages_list.addItem(item)
        self.messages_list.setItemWidget(item, chat_widget)

        self.messages_list.scrollToBottom() #прокручивание к последнему сообщению

    def closeEvent(self, event):
        self.client.disconnect_client()
        event.accept()

    def handle_server_message(self, msg_dict):
        msg_type = msg_dict.get('type')
        text = msg_dict.get('text', '')
        sender = msg_dict.get('from', 'Система')
        
        if msg_type == 'message':
            self.add_message(sender, text)
        elif msg_type in ['info', 'room_joined']:
            self.add_message("Система", text)
        elif msg_type == 'error':
            QMessageBox.warning(self, "Ошибка", text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatManager()
    window.show()
    app.exec()   


