import socket
import threading
import sys
import json

from PyQt6.QtCore import QObject, pyqtSignal

class ChatClient(QObject):
    message_received = pyqtSignal(dict)

    def __init__(self, host = '127.0.0.1', port = 12345):
        super().__init__()
        self.host = host
        self.port = port
        self.client_socket = None
        self.running = False
        self.current_room = None
        self.username = "Anonymous"

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
                self.handle_server_mess(msg_dict)
        
        except Exception as e:
            print(f"[ОШИБКА] {e}")
        finally:
            self.running = False
    
    def handle_server_mess(self, msg_dict):
        msg_type = msg_dict.get('type')
        if msg_type == 'room_joined':
            self.current_room = msg_dict.get('room')
        
        elif msg_type == 'info':
            print(f"[INFO] {msg_dict.get('text')}")
        
        elif msg_type == 'error':
            print(f"[ERROR] {msg_dict.get('text')}")
    
        self.message_received.emit(msg_dict)

    def join_room(self, room_name, username=None):
        if username:
            self.username = username
            
        command = {
            "cmd": "join", 
            "room": room_name,
            "username": self.username
        }
        self.send_command(command)

    def send_message(self, text):
        if not self.current_room:
            return False
            
        command = {
            "cmd": "msg", 
            "text": text
        }
        self.send_command(command)
        return True

    def leave_room(self):
        command = {"cmd": "leave"}
        self.send_command(command)
        self.current_room = None

