import sys
import socket
import threading
import json
from datetime import datetime

from PyQt6.QtCore import Q_ARG, Qt, QMetaObject, QTimer, QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QApplication, QPushButton, QHBoxLayout, QListWidget, \
    QRadioButton, QListWidgetItem, QCheckBox, QLabel, QMessageBox, QMainWindow, QComboBox, QInputDialog


class TaskWidget(QWidget):
    def __init__(self, text, priority, completed=False):
        super().__init__()
        self.text = text
        self.priority = priority
        self.completed = completed
        # добавили ссылку на клиента
        self.client = None

        layout = QHBoxLayout(self)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(completed)
        self.checkbox.stateChanged.connect(self.update_style)

        self.label = QLabel(text)
        self.apply_priority_style()

        self.up_button = QPushButton("↑")
        self.down_button = QPushButton("↓")

        self.up_button.clicked.connect(self.increase_priority)
        self.down_button.clicked.connect(self.decrease_priority)

        layout.addWidget(self.checkbox)
        layout.addWidget(self.label)
        layout.addWidget(self.up_button)
        layout.addWidget(self.down_button)
        layout.addStretch()

    # функция для установки ссылки на клиента, чтобы отправлять изменения
    def set_client(self, client):
        self.client = client

    # стиль для определенного приоритета (остается без изменений)
    def apply_priority_style(self):
        colors = {
            "high" : "red",
            "medium" : "orange",
            "low" : "green"
        }
        color = colors.get(self.priority)
        self.label.setStyleSheet(f"color: {color}; font-weight: bold")

    # функция для смены стиля, если чекбокс прожали + отправляем клиенту изменения
    @pyqtSlot(int)
    def update_style(self, state):
        self.completed = state == 2
        if self.completed:
            self.label.setStyleSheet("color: gray; text-decoration: line-through;")
        else:
            self.apply_priority_style()

        if self.client:
            self.client.send_task_update()

    @pyqtSlot()
    def increase_priority(self):
        order = ["low", "medium", "high"]
        idx = order.index(self.priority)
        if idx < 2:
            self.priority = order[idx + 1]
            if self.client:
                self.client.send_task_update()

    @pyqtSlot()
    def decrease_priority(self):
        order = ["low", "medium", "high"]
        idx = order.index(self.priority)
        if idx > 0:
            self.priority = order[idx - 1]
            if self.client:
                self.client.send_task_update()

class TaskClient:
    def __init__(self, host='localhost', port=5555, board="Главная доска"):
        self.host = host
        self.port = port
        self.current_board = board
        self.socket = None
        # ссылка на поток для приема сообщений с сервера
        self.receive_thread = None
        # флаг для контроля работы потока
        self.running = False
        # ссылка на главное окно (то есть мы делаем взаимную связь между ними
        self.task_manager = None
        self.signals = TaskSignals()

    # функция для подключения к серверу
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            # ставим флаг работы - типа "да, теперь мы работаем, говорите..."
            self.running = True
            # создаем поток для постоянного приема сообщений от сервера
            self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.receive_thread.start()
            return True
        except Exception as e:
            print(f"Ошибочка: {e}")
            return False

    # функция получения сообщений с сервера
    def receive_messages(self):
        # буфер для накопления неполных сообщений
        buffer = ""
        while self.running:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                # если данных нет - сервер отключился, выходим из цикла
                if not data:
                    break
                # добавляем полученные данные в буфер
                buffer += data
                # обрабатываем все полные сообщения (разделенные \n)
                while '\n' in buffer:
                    # разделяем буфер на первую строку и оставшуюся часть
                    line, buffer = buffer.split('\n', 1)
                    # обрабатываем полученное сообщение (убираем пробелы)
                    self.process_message(line.strip())
            except Exception as e:
                print(f"Ошибка получения данных: {e}")
                break

    # функция обработки сообщений, которые пришли к нам с сервера
    def process_message(self, message):
        if message.startswith('TASKS:'):
            mess = message[6:]
            if ":" in mess:
                board_name, tasks_data = mess.split(":", 1)
                try:
                    tasks = json.loads(tasks_data)
                    # отправляем сигнал - он автоматически попадет в главный поток
                    self.signals.tasks_updated.emit(tasks)
                    self.signals.board_updated.emit(board_name)
                except json.JSONDecodeError as e:
                    print(f"Ошибка обработки задач: {e}")
            else:
                print(f"Неправильный формат сообщения: {message}")

    # отправляем сообщение на сервер
    def send(self, message):
        try:
            self.socket.send((message + '\n').encode('utf-8'))
        except Exception as e:
            print(f"Ошибка отправки: {e}")

    # отправляем новую таску на сервер
    def add_task(self, task):
        self.send(f"ADD:{self.current_board}:{json.dumps(task)}")

    # отправляем обновленный список тасок на сервер
    def update_tasks(self, tasks):
        self.send(f"UPDATE:{self.current_board}:{json.dumps(tasks)}")

    def get_tasks(self):
        self.send(f"GET_TASKS:{self.current_board}")
    
    def swicth_board(self, new_board):
        self.current_board = new_board
        self.get_tasks()

    # отрубиться от сервера
    def disconnect(self):
        self.running = False
        if self.socket:
            self.socket.close()

    @pyqtSlot()
    def send_task_update(self):
        if self.task_manager:
            self.task_manager.send_task_update()

class TaskSignals(QObject):
    tasks_updated = pyqtSignal(list)
    board_updated = pyqtSignal(str)

class TaskManager(QWidget):
    def __init__(self, board_name="Главная доска"):
        super().__init__()
        self.board_name = board_name
        # обмениваемся ссылками друг на друга
        self.client = TaskClient(board=self.board_name)
        self.client.signals.tasks_updated.connect(self.update_tasks)
        self.client.signals.board_updated.connect(self.update_board_name)
        self.client.task_manager = self

        self.tasks = []  # локальная копия задач
        self.task_widgets = []  # ссылки на виджеты задач

        self.setWindowTitle(f"Task Manager - {self.board_name}")

        layout = QVBoxLayout(self)

        # добавили статус подключения
        self.status_label = QLabel("Статус: Подключение..." + "00:00:00")
        layout.addWidget(self.status_label)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)

        self.board_select = QComboBox()
        self.board_select.addItems(["Главная доска", "Работа", "Учеба", "Личное", "Новая доска"])
        self.board_select.setCurrentText(board_name)
        self.board_select.currentTextChanged.connect(self.swicth_board)
        layout.addWidget(self.board_select)

        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Введите задачу...")

        buttons_layout = QHBoxLayout()

        add_button = QPushButton("Добавить задачу")
        delete_button = QPushButton("Удалить выбранную задачу")
        clear_completed_task = QPushButton("Удалить все выполненные")

        self.tasks_list = QListWidget()

        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(clear_completed_task)

        priority_layout = QHBoxLayout()

        self.low_priority = QRadioButton("Низкий")
        self.medium_priority = QRadioButton("Средний")
        self.high_priority = QRadioButton("Высокий")

        self.medium_priority.setChecked(True)

        priority_layout.addWidget(self.low_priority)
        priority_layout.addWidget(self.medium_priority)
        priority_layout.addWidget(self.high_priority)
        priority_layout.addStretch()

        layout.addWidget(self.task_input)
        layout.addLayout(priority_layout)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.tasks_list)

        add_button.clicked.connect(self.add_task)
        self.task_input.returnPressed.connect(self.add_task)
        delete_button.clicked.connect(self.delete_task)
        clear_completed_task.clicked.connect(self.delete_completed_tasks)

        # пытаемся подрубиться к серверу
        if not self.client.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к серверу")

        # запрашиваем текущие задачи
        self.client.get_tasks()
    
    @pyqtSlot()
    def update_clock(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.status_label.setText("Подключено " + str(now))
    
    @pyqtSlot()
    def swicth_board(self):
        new_board = self.board_select.currentText() #эти функции pyQt честно взяты с гпт, но я все поняла!
        if new_board == "Новая доска":
            new_board, p = QInputDialog.getText(self, "Новая доска", "Введите название доски: ")
            if p and new_board.strip():
                self.board_select.insertItem(0, new_board)
                self.board_select.setCurrentText(new_board)
            else:
                self.board_select.setCurrentText(self.board_name)
                return
        if new_board != self.board_name:
            self.board_name = new_board
            self.setWindowTitle(f"Task Manager - {self.board_name}")

            self.tasks_list.clear()
            self.task_widgets.clear()
            self.status_label.setText("Загрузка задач...")

            self.client.swicth_board(new_board)

    @pyqtSlot(str)
    def update_board_name(self, board_name):
        self.board_name = board_name
        self.setWindowTitle(f"Task Manager - {self.board_name}")
        if self.board_select.currentText() != board_name:
            self.board_select.setCurrentText(board_name)

    def get_priority(self):
        if self.high_priority.isChecked():
            return "high"
        elif self.low_priority.isChecked():
            return "low"
        return "medium"

    @pyqtSlot()
    def add_task(self):
        text = self.task_input.text().strip()
        if text:
            task_dict = {
                "text": text,
                "priority": self.get_priority(),
                "completed": False
            }
            # отправляем на сервер
            self.client.add_task(task_dict)
            self.task_input.clear()

    @pyqtSlot()
    def delete_task(self):
        selected_item = self.tasks_list.currentItem()
        if selected_item:
            reply = QMessageBox.question(
                self,
                "Подтверждение удаления",
                "Вы уверены?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                row = self.tasks_list.row(selected_item)
                current_tasks = []
                for i in range(self.tasks_list.count()):
                    item = self.tasks_list.item(i)
                    widget = self.tasks_list.itemWidget(item)
                    current_tasks.append({
                        "text": widget.text,
                        "priority": widget.priority,
                        "completed": widget.completed
                    })
                if 0 <= row < len(current_tasks):
                    current_tasks.pop(row)
                    self.client.update_tasks(current_tasks)

    @pyqtSlot()
    def delete_completed_tasks(self):
        # создаем новый список только с не выполненными задачами
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            "Вы уверены?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            new_tasks = []
            for i in range(self.tasks_list.count()):
                item = self.tasks_list.item(i)
                widget = self.tasks_list.itemWidget(item)
                if not widget.completed:
                    new_tasks.append({
                        "text": widget.text,
                        "priority": widget.priority,
                        "completed": widget.completed
                    })
            # проверяем, есть ли что удалять
            if len(new_tasks) < self.tasks_list.count():
                # отправляем обновленный список на сервер
                self.client.update_tasks(new_tasks)
                # просто уведомление
                deleted_count = self.tasks_list.count() - len(new_tasks)
                msg = f"Удалено {deleted_count} выполненных задач"
                QMessageBox.information(self, "Информация", msg)
            else:
                QMessageBox.information(self, "Информация", "Нет выполненных задач для удаления")

    # функция отправки задачек на сервер
    def send_task_update(self):
        # собираем актуальное состояние из виджетов в словари
        current_tasks = []
        for i in range(self.tasks_list.count()):
            item = self.tasks_list.item(i)
            widget = self.tasks_list.itemWidget(item)
            # создаем словарь с данными задачи
            task_data = {
                "text": widget.text,
                "priority": widget.priority,
                "completed": widget.completed
            }
            current_tasks.append(task_data)

        # отправляем на сервер
        self.client.update_tasks(current_tasks)

    # обновляем интерфейс на основе полученных задач (вызывается из сетевого потока)
    @pyqtSlot(list)
    def update_tasks(self, tasks):
        # Сохраняем задачи
        self.tasks = tasks

        # Очищаем список
        self.tasks_list.clear()
        self.task_widgets.clear()

        # Добавляем задачи обратно
        for task in tasks:
            widget = TaskWidget(task["text"], task["priority"], task["completed"])
            widget.set_client(self.client)

            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self.tasks_list.addItem(item)
            self.tasks_list.setItemWidget(item, widget)
            self.task_widgets.append(widget)

        self.status_label.setText(f"Статус: Подключено. Задач: {len(tasks)}")

    # закрываем окошко
    @pyqtSlot()
    def closeEvent(self, event):
        self.client.disconnect()
        event.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Доски")
        self.resize(400, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        self.boads_list = QListWidget()
        for board_name in ["Главная доска", "Работа", "Учеба", "Личное"]:
            self.boads_list.addItem(board_name)

        new_board_button = QPushButton("Создать новую доску")
        open_button = QPushButton("Открыть доску")
        layout.addWidget(self.boads_list)
        layout.addWidget(new_board_button)
        layout.addWidget(open_button)

        open_button.clicked.connect(self.open_board)
        self.boads_list.itemDoubleClicked.connect(self.open_board)
        new_board_button.clicked.connect(self.create_new_board)

    def create_new_board(self):
        new_board, p = QInputDialog.getText(self, "Новая доска", "Введите название доски: ")
        if p and new_board.strip():
            self.boads_list.addItem(new_board)
            
    def open_board(self):
        selected_item = self.boads_list.currentItem()
        if selected_item:
            board_name = selected_item.text()
            self.task_manager = TaskManager(board_name)
            self.task_manager.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()