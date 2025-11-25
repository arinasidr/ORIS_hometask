from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QPushButton, QLabel, QLineEdit, QListWidget,
    QVBoxLayout, QHBoxLayout, QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from client import GameClient
from pyqtgameboards.gameboard import QRectangleboard

#ввод имени, подключение
class StartWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client = None
        self.name_input = None
        self.status_label = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 8, 15, 8)

        self.welcome_label = QLabel()
        pixmap_welcome = QPixmap('../welcome.png')
        self.welcome_label.setPixmap(pixmap_welcome)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('input your name...')
        
        self.registr_btn = QPushButton('i want to register!')

        layout.addWidget(self.welcome_label)
        layout.addWidget(QLabel('name'))
        layout.addWidget(self.username_input)
        layout.addWidget(self.registr_btn)

        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

        self.registr_btn.clicked.connect(self.on_connect)

    def on_connect(self):
        name = self.username_input.text().strip()
        if not name:
            QMessageBox.warning(self, 'error', 'input your username for playing!')
            return
        
        self.client = GameClient()
        self.client.player_name = name

        self.client.signal_join_room.connect(self.on_join_room)
        self.client.signal_error.connect(self.on_error)

        self.client.connect()

    def on_join_room(self, room_id):
        room = RoomWindow(self.client, room_id)
        room.show()
        self.close()

    def on_error(self, text):
        QMessageBox.warning(self, 'error', text)

#пока чат-заглушка, TODO дописать чат
class ChatWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.chat_view = QTextEdit()
        self.chat_view.setReadOnly(True)

        input_layout = QHBoxLayout()
        self.input = QLineEdit()
        self.send_btn = QPushButton('send')
        input_layout.addWidget(self.input)
        input_layout.addWidget(self.send_btn)

        layout.addWidget(QLabel('chat'))
        layout.addWidget(self.chat_view, stretch=1)
        layout.addLayout(input_layout)

        self.setLayout(layout)

#ожидание игроков
class RoomWindow(QMainWindow):
    def __init__(self, client, room_id):
        super().__init__()
        self.client = client
        self.room_id = room_id

        self.players_list = None
        self.status_label = None

        self.setWindowTitle(f"Room #{room_id}")
        self.resize(900, 600)

        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout()
        main_row = QHBoxLayout()

        left_layout = QVBoxLayout()

        info_layout = QVBoxLayout()

        room_label = QLabel(f'room #{self.room_id}')
        room_label.setAlignment(Qt.AlignCenter)

        players_label = QLabel('players: ')
        self.players_list = QListWidget()

        info_layout.addWidget(room_label)
        info_layout.addWidget(players_label)
        info_layout.addWidget(self.players_list)

        self.preview = QLabel()
        pixmap = QPixmap('../waiting.png')
        self.preview.setPixmap(pixmap)
        self.preview.setAlignment(Qt.AlignCenter)

        left_layout.addLayout(info_layout)
        left_layout.addWidget(self.preview, stretch=1)

        right_layout = QVBoxLayout()
        
        self.chat = ChatWidget()
        right_layout.addWidget(self.chat, stretch=1)

        self.leave_btn = QPushButton('leave room :(')
        right_layout.addWidget(self.leave_btn)

        main_row.addLayout(left_layout, stretch=2)
        main_row.addLayout(right_layout, stretch=1)

        root_layout.addLayout(main_row)

        central = QWidget()
        central.setLayout(root_layout)
        self.setCentralWidget(central)
        
    def update_room(self, players):
        # TODO Обновление списка игроков
        pass

    def start_game(self, state):
        # TODO Запуск игрового окна
        pass

# FinishWindow — результат игры
class FinishWindow(QMainWindow):
    def __init__(self, client, winner):
        super().__init__()
        self.client = client
        self.winner = winner
        self.init_ui()

    def init_ui(self):
        # TODO Создать интерфейс финального окна
        pass

    def exit_game(self):
        # TODO Выход
        pass

    def restart(self):
        # TODO Новая игра
        pass

class GameWindow(QMainWindow):
    def __init__(self, client):
        super().__init__()
        self.client = client


    def update_board(self, state):
        pass

    def update_move(self, result):
        pass

    def finish_game(self, winner):
        pass

    def keyPressEvent(self, event):
        pass

#старт приложения
def main():
    app = QApplication([])
    w = StartWindow()
    w.show()
    app.exec()


if __name__ == "__main__":
    main()



