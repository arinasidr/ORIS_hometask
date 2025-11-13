import sys
import json
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QApplication, QPushButton, QListWidget, QHBoxLayout, QRadioButton, QListWidgetItem, QCheckBox, QLabel, QMessageBox

from client import TaskClient

class TaskWidget(QWidget):
    def __init__(self, text, priority, completed = False, index = 0, update_callback = None):
        super().__init__()
        self.text = text
        self.priority = priority
        self.completed = completed
        self.index = index
        self.update_callback = update_callback
        

        layout = QHBoxLayout(self)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(completed)
        self.checkbox.stateChanged.connect(self.update_style)
        self.label = QLabel(text)
        self.apply_priority_style()

        layout.addWidget(self.checkbox)
        layout.addWidget(self.label)

    def apply_priority_style(self):
        colors ={
            "high" : "red", 
            "medium" : "orange",
            "low" : "green"
        }
        color = colors.get(self.priority)
        if self.completed:
            self.label.setStyleSheet("color: gray; text-decoration: line-through;")
        else:
            self.label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def update_style(self, state):
        self.completed = state == 2
        if self.completed:
            self.label.setStyleSheet("color : gray; text-decoration: line-through;") 
        self.apply_priority_style() 
        if self.update_callback:
            self.update_callback(self.index, self.completed)


class TaskManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Task Manager")

        self.client = TaskClient()
        if not self.client.start_client():
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к серверу")
            sys.exit(1)
        
        self.client.tasks_updated.connect(self.update_gui)

        layout = QVBoxLayout(self)
        self.task_input = QLineEdit() #строка для ввода текста
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
    
    def get_priority(self):
        if self.high_priority.isChecked():
            return "high"
        elif self.low_priority.isChecked():
            return "low"
        return "medium"

    def add_task(self):
        text = self.task_input.text().strip()
        if text:
            command = {
                'action' : 'add',
                'text': text,
                'priority': self.get_priority()
            }
            self.client.send_command(command)
            self.task_input.clear()
            # task = TaskWidget(text, self.get_priority())
            # item = QListWidgetItem()
            # item.setSizeHint(task.sizeHint())
            # self.tasks_list.addItem(item)
            # self.tasks_list.setItemWidget(item, task)
            # self.task_input.clear()

            # priority = self.get_priority()
            # item = QListWidgetItem(text)
            # if priority == "high":
            #     item.setForeground(QColor("red"))
            # elif priority == "medium":
            #     item.setForeground(QColor("orange"))
            # elif priority == "low":
            #     item.setForeground(QColor("green"))
            # self.tasks_list.addItem(item)
            # self.task_input.clear()

    def delete_task(self):
        selected_row = self.tasks_list.currentRow()
        if selected_row >= 0:
            command = {
                    'action': 'delete',
                    'index': selected_row
            }
            self.client.send_command(command)

    def delete_completed_tasks(self):
        index_completed = []
        for i in range(len(self.client.tasks)):
            if self.client.tasks[i].get('completed', False):
                index_completed.append(i)

        for i in range(len(index_completed) - 1, -1, -1):
            command = {
               'action': 'delete',
                'index': index_completed[i] 
            }
            self.client.send_command(command)

        # count = 0

        # for i in range(self.tasks_list.count() - 1, -1, -1):
        #     item = self.tasks_list.item(i)
        #     widget = self.tasks_list.itemWidget(item)
        #     if widget.completed:
        #         self.tasks_list.takeItem(i)
        #         count += 1
        
        # msg = "Нет выполненных задач" if count == 0 else f"Удалено {count} задач"
        # QMessageBox.information(self)

    def update_tasks(self, index, completed):
        if index >= 0:
            command = {
                'action': 'update',
                'index': index,
                'completed': completed
            }
            self.client.send_command(command)
            
    def update_gui(self):
        self.tasks_list.clear()

        for i, task_data in enumerate(self.client.tasks):
            text = task_data.get('text', '')
            priority = task_data.get('priority', 'medium')
            completed = task_data.get('completed', False)
            
            task_widget = TaskWidget(
                text=text, 
                priority=priority, 
                completed=completed,
                index=i,
                update_callback=self.update_tasks
            )
                
            item = QListWidgetItem()
            item.setSizeHint(task_widget.sizeHint())
            self.tasks_list.addItem(item)
            self.tasks_list.setItemWidget(item, task_widget)

    def closeEvent(self, event):
        self.client.disconnect_client()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TaskManager()
    window.show()
    app.exec()   

