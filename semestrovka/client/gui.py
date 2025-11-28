# gui.py
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QPushButton, QLabel, QLineEdit, QListWidget,
    QVBoxLayout, QHBoxLayout, QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt, QRect, QObject, QEvent
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QPixmap

from client import GameClient

def player_color(name: str) -> QColor:
    if not name:
        return QColor(200, 200, 200)
    h = abs(hash(name)) % 360
    return QColor.fromHsv(h, 200, 220)

class GameField(QWidget):
    CELL_SIZE = 32
    ROWS = 15
    COLS = 15

    def __init__(self):
        super().__init__(None)
        self.state = None

        w = self.COLS * self.CELL_SIZE
        h = self.ROWS * self.CELL_SIZE
        self.setMinimumSize(w, h)
        self.setMaximumSize(w, h)

        self.setFocusPolicy(Qt.StrongFocus)

    def update_state(self, state: dict):
        self.state = state
        self.update()
        self.setFocus()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(245, 245, 245))

        painter.setPen(QPen(QColor(200, 200, 200)))
        for r in range(self.ROWS + 1):
            y = r * self.CELL_SIZE
            painter.drawLine(0, y, self.COLS * self.CELL_SIZE, y)
        for c in range(self.COLS + 1):
            x = c * self.CELL_SIZE
            painter.drawLine(x, 0, x, self.ROWS * self.CELL_SIZE)

        if not self.state:
            return

        territories = self.state.get("territories", {})
        for player, cells in territories.items():
            col = QColor(player_color(player))
            col.setAlpha(100)
            painter.setBrush(QBrush(col))
            painter.setPen(Qt.NoPen)
            for (x, y) in cells:
                if 0 <= x < self.COLS and 0 <= y < self.ROWS:
                    rect = QRect(x * self.CELL_SIZE, y * self.CELL_SIZE,
                                 self.CELL_SIZE, self.CELL_SIZE)
                    painter.drawRect(rect)

        positions = self.state.get("positions", {})
        for player, (x, y) in positions.items():
            if not (0 <= x < self.COLS and 0 <= y < self.ROWS):
                continue
            col = player_color(player)
            painter.setBrush(QBrush(col))
            painter.setPen(QPen(Qt.black, 2))

            cx = x * self.CELL_SIZE + self.CELL_SIZE // 2
            cy = y * self.CELL_SIZE + self.CELL_SIZE // 2
            r = self.CELL_SIZE // 3
            painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)


class KeyFilter(QObject):
    def __init__(self):
        super().__init__()
        self.active_window = None

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and self.active_window is not None:
            print(f"KEY FILTER: Key press caught! Key code: {event.key()}")
            k = event.key()
            interested = {
                Qt.Key_W, Qt.Key_A, Qt.Key_S, Qt.Key_D,
                Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right
            }
            if k in interested:
                try:
                    self.active_window.handle_key(k)
                except Exception:
                    pass
                return True  
        return super().eventFilter(obj, event)


class StartWindow(QMainWindow):
    def __init__(self):
        super().__init__(None)
        self.client = None
        self.setWindowTitle('welcome to territory game!')
        self.resize(500, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.welcome_label = QLabel()
        try:
            pix = QPixmap('../welcome.png')
            self.welcome_label.setPixmap(pix)
        except Exception:
            pass
        self.welcome_label.setAlignment(Qt.AlignCenter)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('input your name...')

        self.reg_btn = QPushButton('i want to register!')
        self.reg_btn.clicked.connect(self.on_connect)

        layout.addWidget(self.welcome_label)
        layout.addWidget(QLabel("name"))
        layout.addWidget(self.username_input)
        layout.addWidget(self.reg_btn)

        c = QWidget(None)
        c.setLayout(layout)
        self.setCentralWidget(c)

    def on_connect(self):
        name = self.username_input.text().strip()
        if not name:
            QMessageBox.warning(self, "error", "input your username")
            return

        self.client = GameClient()
        self.client.player_name = name

        self.client.signal_join_room.connect(self.on_join_room)
        self.client.signal_error.connect(self.on_error)

        if not self.client.connect():
            QMessageBox.critical(self, "error", "unable to connect")
            return

    def on_join_room(self, room_id):
        self.room_window = RoomWindow(self.client, room_id)
        self.room_window.show()
        self.close()

    def on_error(self, text):
        QMessageBox.warning(self, "error", text)


class ChatWidget(QWidget):
    def __init__(self, client=None):
        super().__init__(None)
        self.client = client
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.chat_view = QTextEdit()
        self.chat_view.setReadOnly(True)

        row = QHBoxLayout()
        self.input = QLineEdit()
        self.send_btn = QPushButton("send")
        row.addWidget(self.input)
        row.addWidget(self.send_btn)

        layout.addWidget(QLabel("chat"))
        layout.addWidget(self.chat_view)
        layout.addLayout(row)

        self.setLayout(layout)

        self.send_btn.clicked.connect(self.on_send)
        if self.client:
            self.client.signal_chat.connect(self.append_message)

    def append_message(self, text):
        self.chat_view.append(text)

    def on_send(self):
        text = self.input.text().strip()
        if not text:
            return
        self.input.clear()
        self.append_message(f"you: {text}")
        try:
            self.client.send_command({"type": "chat", "data": text})
        except Exception:
            pass

class RoomWindow(QMainWindow):
    def __init__(self, client, room_id):
        super().__init__(None)
        self.client = client
        self.room_id = room_id
        self.setWindowTitle("Room")
        self.resize(900, 600)
        self.init_ui()

    def init_ui(self):
        root = QHBoxLayout()

        left = QVBoxLayout()
        left.addWidget(QLabel(f"room #{self.room_id}"))

        self.players_list = QListWidget()
        left.addWidget(QLabel("players:"))
        left.addWidget(self.players_list)

        self.status_label = QLabel("")
        left.addWidget(self.status_label)

        self.preview = QLabel()
        try:
            pix = QPixmap('../waiting.png')
            self.preview.setPixmap(pix)
            self.preview.setScaledContents(True)
        except Exception:
            pass
        left.addWidget(self.preview, 1)

        right = QVBoxLayout()
        self.chat = ChatWidget(self.client)
        right.addWidget(self.chat, 1)

        self.leave_btn = QPushButton("leave room :(")
        self.leave_btn.clicked.connect(self.leave_room)
        right.addWidget(self.leave_btn)

        root.addLayout(left, 2)
        root.addLayout(right, 1)

        c = QWidget(None)
        c.setLayout(root)
        self.setCentralWidget(c)

        self.client.signal_room_update.connect(self.update_room)
        self.client.signal_state_update.connect(self.start_game)

    def update_room(self, players):
        self.players_list.clear()
        for p in players:
            self.players_list.addItem(p)

    def start_game(self, state):
        if hasattr(self, "game_window") and self.game_window is not None:
            return

        self.game_window = GameWindow(self.client, self.room_id)
        if state:
            self.game_window.update_board(state)
        self.game_window.show()

        self.close()
    
    def leave_room(self):
        try:
            self.client.disconnect_client()
        except Exception:
            pass
        w = StartWindow()
        w.show()
        self.close()


class FinishWindow(QMainWindow):
    def __init__(self, client, winner):
        super().__init__(None)
        self.client = client
        self.winner = winner
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        pic = QLabel()
        try:
            pic.setPixmap(QPixmap('../game_over.png'))
        except Exception:
            pass
        layout.addWidget(pic)
        layout.addWidget(QLabel(f"Winner: {self.winner}"))

        btn = QPushButton("play again!")
        btn.clicked.connect(self.restart)
        layout.addWidget(btn)

        quit_btn = QPushButton("quit")
        quit_btn.clicked.connect(QApplication.quit)
        layout.addWidget(quit_btn)

        c = QWidget(None)
        c.setLayout(layout)
        self.setCentralWidget(c)

    def restart(self):
        try:
            self.client.disconnect_client()
        except Exception:
            pass
        w = StartWindow()
        w.show()
        self.close()

class GameWindow(QMainWindow):
    def __init__(self, client, room_id):
        super().__init__(None)
        self.client = client
        self.room_id = room_id

        self.setWindowTitle("game! good luck")
        self.resize(900, 600)

        self.finish_window = None

        self.key_filter = None

        self.init_ui()

        if getattr(self.client, "game_state", None):
            self.update_board(self.client.game_state)

        self.client.signal_state_update.connect(self.update_board)
        self.client.signal_room_update.connect(self.update_room)
        self.client.signal_game_over.connect(self.on_game_over)
        self.client.signal_move_result.connect(self.on_move_result)
        self.client.signal_error.connect(self.on_error)

        self.setFocusPolicy(Qt.StrongFocus)

    def init_ui(self):
        root = QHBoxLayout()

        left = QVBoxLayout()
        left.addWidget(QLabel(f"room #{self.room_id}"))
        left.addWidget(QLabel("players:"))

        self.players_list = QListWidget()
        left.addWidget(self.players_list)

        self.status_label = QLabel("")
        left.addWidget(self.status_label)

        self.field = GameField()
        left.addWidget(self.field, 1)

        right = QVBoxLayout()

        right.addWidget(QLabel("status panel"))
        self.turn_label = QLabel("Turn: —")
        right.addWidget(self.turn_label)

        self.alive_label = QLabel("Alive: —")
        right.addWidget(self.alive_label)

        self.last_event_label = QLabel("Last: —")
        right.addWidget(self.last_event_label)

        right.addStretch(1)
        self.leave_btn = QPushButton("leave game :(")
        self.leave_btn.clicked.connect(self.leave_game)
        right.addWidget(self.leave_btn)

        root.addLayout(left, 2)
        root.addLayout(right, 1)

        c = QWidget(None)
        c.setLayout(root)
        self.setCentralWidget(c)

    def showEvent(self, event):
        super().showEvent(event)
        try:
            self.field.setFocus()
        except Exception:
            pass

        app = QApplication.instance()
        if app is not None:
            if not hasattr(app, "_game_key_filter"):
                app._game_key_filter = KeyFilter()
                app.installEventFilter(app._game_key_filter)
            app._game_key_filter.active_window = self
            self.key_filter = app._game_key_filter

    def closeEvent(self, event):
        app = QApplication.instance()
        if app is not None and hasattr(app, "_game_key_filter"):
            if app._game_key_filter.active_window is self:
                app._game_key_filter.active_window = None
        super().closeEvent(event)

    def update_room(self, players):
        self.players_list.clear()
        for p in players:
            self.players_list.addItem(str(p))
        try:
            self.alive_label.setText(f"Alive: {len(players)}")
        except Exception:
            pass

    def update_board(self, state):
        try:
            self.field.update_state(state)
            if isinstance(state, dict):
                turn = state.get("turn")
                if turn is not None:
                    self.turn_label.setText(f"Turn: {turn}")
                self.last_event_label.setText(f"Last: {state.get('last_event','-')}")
            self.field.setFocus()
        except Exception:
            pass

    def on_move_result(self, result):
        self.status_label.setText(str(result))
        self.last_event_label.setText(f"Last: {result}")

    def on_game_over(self, winner):
        self.finish_window = FinishWindow(self.client, winner)
        self.finish_window.show()
        self.close()

    def leave_game(self):
        try:
            self.client.disconnect_client()
        except Exception:
            pass
        w = StartWindow()
        w.show()
        self.close()

    def on_error(self, text):
        QMessageBox.warning(self, "error", text)

    def handle_key(self, key):
        mapping = {
            Qt.Key_W: "up",
            Qt.Key_Up: "up",
            Qt.Key_S: "down",
            Qt.Key_Down: "down",
            Qt.Key_A: "left",
            Qt.Key_Left: "left",
            Qt.Key_D: "right",
            Qt.Key_Right: "right",
            # Qt.Key_Cyrillic_Tse: "up", 
            # Qt.Key_Cyrillic_Yer: "down", 
            # Qt.Key_Cyrillic_Ef: "left",  
            # Qt.Key_Cyrillic_Ve: "right",  
            # 1067: "up", 
            # 1066: "down",
            # 1065: "left", 
            # 1068: "right",
        }
        if key in mapping:
            direction = mapping[key]
            try:
                print(f"Sending move: {direction}") 
                self.client.send_move(direction)
            except Exception as e:
                print(f"Error sending move: {e}")
            self.field.setFocus()

    def keyPressEvent(self, event):
        k = event.key()
        self.handle_key(k)

def main():
    app = QApplication([])
    w = StartWindow()
    w.show()
    app.exec()


if __name__ == "__main__":
    main()
