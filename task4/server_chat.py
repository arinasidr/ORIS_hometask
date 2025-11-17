import socket
import threading
import json

class ChatServer:
    def __init__(self, host = '127.0.0.1', port = 12345):
        self.host = host
        self.port = port
        self.clients = {}
        self.rooms = {}
        self.messages = {}
        self.lock = threading.Lock()

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        with self.server_socket:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen()
            print(f"[СЕРВЕР ЗАПУЩЕН] {self.host} : {self.port}")
            while True:
                conn, addr = self.server_socket.accept()
                print(f"Подключен клиент: {addr}")

                with self.lock:
                    self.clients[conn] = {'username' : f"User{addr[1]}", 'room':None}

                self.send_message(conn, {'type': 'info', 'text': 'Добро пожаловать в чат!'})
                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

    def send_message(self, conn, message_dict):
        try:
            message_json = json.dumps(message_dict)
            conn.sendall(message_json.encode('utf-8'))
        except ConnectionResetError:
            self.remove_client(conn)

    def send_to_room(self, room_name,message):
        with self.lock:
            if room_name in self.rooms:
                for conn in self.rooms[room_name]:
                    try:
                        self.send_message(conn, message)
                    except:
                        self.remove_client(conn)

    def remove_client(self, conn):
        with self.lock:
            for room_name, members in list(self.rooms.items()):
                if conn in members:
                    members.remove(conn)
                if not members:
                    del self.rooms[room_name]
                else:
                    if conn in self.clients:
                        message_dict = {"type": "message", "from" : "server", "text": f"{self.clients[conn]['username']} покинул комнату"}
                        self.send_to_room(room_name, message_dict)
            if conn in self.clients:
                del self.clients[conn]

    def handle_client(self, conn, addr):
        current_room = None
        try:
            while True:
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    break
                
                msg_dict = json.loads(data)
                cmd = msg_dict.get('cmd', '').lower()

                if cmd == "exit":
                    self.send_message(conn, {"type" : "info", "text": "пока-пока!"})
                    break

                if cmd == "join":
                    room_name = msg_dict.get('room', '')
                    username = msg_dict.get('username', f"User{addr[1]}")
                    if not room_name:
                        self.send_message(conn, {"type": "error", "text": "Укажите название комнаты"})
                        continue
                    
                    with self.lock:
                        self.clients[conn]['username'] = username
                        current_room = self.clients[conn].get('room')
                        if room_name not in self.rooms:
                            self.rooms[room_name] = []

                        if current_room and current_room in self.rooms and conn in self.rooms[current_room]:
                            self.rooms[current_room].remove(conn)
                            if not self.rooms[current_room]:
                                del self.rooms[current_room]
                            else:
                                leave_msg = {"type": "info", "from": "server", "text": f"{self.clients[conn]['username']} покинул комнату"}
                                self.send_to_room(current_room, leave_msg)
                            
                        self.rooms[room_name].append(conn)
                        self.clients[conn]['room'] = room_name
                        current_room = room_name
                    self.send_message(conn, {"type": "room_joined", "room": room_name})
                    join_msg = {"type": "info", "from": "server", "text": f"{self.clients[conn]['username']} подключился к комнате"}
                    self.send_to_room(room_name, join_msg)

                elif cmd == 'leave':
                    if not current_room:
                        self.send_message(conn, {"type": "error", "text": "Вы не в комнате"})
                        continue
                    with self.lock:
                        if current_room and current_room in self.rooms and conn in self.rooms[current_room]:
                            self.rooms[current_room].remove(conn)
                            self.clients[conn]['room'] = None
                            if not self.rooms[current_room]:
                                del self.rooms[current_room]
                            else:
                                leave_msg = {"type": "info", "from": "server", "text": f"{self.clients[conn]['username']} покинул комнату"}
                                self.send_to_room(current_room, leave_msg)

                    self.send_message(conn, {"type": "info", "text": "Вы покинули комнату"})
                    current_room = None

                elif cmd == 'msg' or cmd == 'message':
                    message_text = msg_dict.get('text', '')
                    username = self.clients[conn].get('username')
                    current_room = self.clients[conn].get('room')
                    if not message_text:
                        self.send_message(conn, {"type": "error", "text": "Введите текст сообщения"})
                        continue
                    if not current_room:
                        self.send_message(conn, {"type": "error", "text": "Вы не в комнате"})
                        continue
                        
                    if current_room in self.rooms and conn in self.rooms[current_room]:
                        message_dict = {"type": "message", "from": self.clients[conn]['username'], "text": message_text}
                        print(f"[MESSAGE] {current_room} - {self.clients[conn]['username']} : {message_text}")
                        self.send_to_room(current_room, message_dict)
                    else:
                        self.send_message(conn, {"type": "error", "text": "Вы не в комнате"})

                else:
                    self.send_message(conn, {"type": "error", "text": "Неизвестная команда"})
        except ConnectionResetError:
            print(f"[ОТКЛЮЧЕНИЕ] Клиент {addr} отключился")
        finally:
            self.remove_client(conn)
            conn.close()
            print(f"Клиент отключен {addr}")

if __name__ == "__main__":
    server = ChatServer()
    server.start_server()