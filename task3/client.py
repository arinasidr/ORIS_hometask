import socket
import threading
import sys
import json

from PyQt6.QtCore import QObject, pyqtSignal

class TaskClient(QObject):
    tasks_updated = pyqtSignal()

    def __init__(self, host = 'localhost', port = 1234):
        super().__init__()
        self.host = host
        self.port = port
        self.tasks = []
        self.client_socket = None
        self.running = False

    def start_client(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.client_socket.connect((self.host, self.port))
            self.running = True
            print("[ПОДКЛЮЧЕНИЕ] Подключено к серверу")
            
            listen_thread = threading.Thread(target=self.listen_server, daemon=True)
            listen_thread.start()

            return True
        except Exception as e:
            print(f"[ОШИБКА] {e}")
            return False
    
    def disconnect_client(self):
        self.running = False
        if self.client_socket:
            self.client_socket.close()
            print("клиент отключен")

    def send_command(self, command):
        if self.client_socket:
            try:
                message = json.dumps(command)
                self.client_socket.send(message.encode('utf-8'))
            except Exception as e:
                print(f"[ОШИБКА] {e}")
    
    def listen_server(self):
        try:
            while self.running:
                data = self.client_socket.recv(1024).decode('utf-8')
                if not data:
                    print("[ОТКЛЮЧЕНИЕ] Соединение разорвано сервером")
                    break

                msg_dict = json.loads(data)
                if 'tasks' in msg_dict:
                    self.tasks = msg_dict['tasks']
                self.tasks_updated.emit() 
        except Exception as e:
            print(f"[ОШИБКА] {e}")
        finally:
            self.running = False