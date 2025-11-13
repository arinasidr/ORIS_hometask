import socket
import threading
import json

class TaskServer:
    def __init__(self, host = 'localhost', port = 1234):
        self.host = host
        self.port = port
        self.tasks = []
        self.clients = []
        self.lock = threading.Lock()

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        with self.server_socket:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen()
            print(f"[СЕРВЕР ЗАПУЩЕН] {self.host}:{self.port}")

            while True:
                conn, addr = self.server_socket.accept()
                print(f"Подключен клиент: {addr}")

                self.send_message(conn, {'tasks': self.tasks})

                with self.lock:
                    self.clients.append(conn)

                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

    def handle_client(self, conn, addr):
        try:
           while True:
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    break

                msg_dict = json.loads(data)
                action = msg_dict.get('action', '').lower()

                if action == 'add':
                    task = {
                        'text': msg_dict['text'],
                        'priority': msg_dict['priority'],
                        'completed': False
                    }
                    self.tasks.append(task)
                elif action == 'delete':
                    index = msg_dict['index']
                    if index >= 0:
                        self.tasks.pop(index)
                elif action == 'update':
                    index = msg_dict['index']
                    self.tasks[index]['completed'] = msg_dict['completed']
                
                self.broadcast_tasks()
        except ConnectionResetError:
            print(f"[ОТКЛЮЧЕНИЕ] Клиент {addr} отключился")
        finally:
            with self.lock:
                if conn in self.clients:
                    self.clients.remove(conn)
            conn.close()

    def send_message(self, conn, message_dict):
        try:
            message_json = json.dumps(message_dict)
            conn.sendall(message_json.encode('utf-8'))
        except ConnectionResetError:
            with self.lock:
                if conn in self.clients:
                    self.clients.remove(conn)
    
    def broadcast_tasks(self):
        with self.lock:
            for client in self.clients:
                self.send_message(client, {'tasks': self.tasks})

if __name__ == "__main__":
    server = TaskServer()
    server.start_server()