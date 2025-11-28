import socket
import threading
import pickle

from rooms import RoomManager

class Server:
    def __init__(self, host = '127.0.0.1', port = 12345):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {} # socket: player_name
        self.rooms = RoomManager()
        self.lock = threading.Lock()

    def recv_exact(self, conn, n):
        data = b''
        while len(data) < n:
            packet = conn.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def recv_message(self, conn):
        header = self.recv_exact(conn, 4)
        if not header:
            return None
        length = int.from_bytes(header, 'big')
        data = self.recv_exact(conn, length)
        if not data:
            return None
        return pickle.loads(data)

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
                client_thread = threading.Thread(target=self.handle_client, args=(conn, ), daemon=True)
                client_thread.start()
    
    def send_message(self, conn, message_dict):
        try:
            pickle_mes = pickle.dumps(message_dict, protocol=pickle.HIGHEST_PROTOCOL)
            conn.sendall(len(pickle_mes).to_bytes(4, 'big') + pickle_mes)
        except Exception:
            self.rooms.remove_client_from_room(conn)
            try:
                conn.close()
            except:
                pass

    def remove_client(self, conn):
        with self.lock:
            if conn in self.clients:
                player_name = self.clients[conn]
                room_id = self.rooms.get_client_room(conn)
                self.rooms.remove_client_from_room(conn)
                del self.clients[conn]
                print(f'[ОТКЛЮЧЕНИЕ] {player_name} из комнаты {room_id}')
                if room_id in self.rooms.rooms:
                    players_list = self.rooms.get_room_players(room_id)

                    self.rooms.broadcast_to_room(room_id, {
                        'type': 'room_update',
                        'room_id': room_id,
                        'data': players_list
                    })
            conn.close()

    def handle_client(self, conn):
        player_name = None
        try:
            while True:
                msg_dict = self.recv_message(conn)
                if not msg_dict:
                    break

                msg_type = msg_dict.get('type').lower()

                if msg_type == 'signup':
                    player_name = msg_dict.get('data')
                    with self.lock:
                        self.clients[conn] = player_name
                    room_id = self.rooms.add_client_to_room(conn, player_name)
                    self.send_message(conn, {'type': 'join_room', 'room_id': room_id, 'data':room_id})
                    players_list = self.rooms.get_room_players(room_id)
                    self.rooms.broadcast_to_room(room_id, {'type': 'room_update', 'room_id': room_id, 'data': players_list})
                
                elif msg_type == 'chat':
                    if player_name is None:
                        continue
                    room_id = self.rooms.get_client_room(conn)
                    text = msg_dict.get('data')
                    self.rooms.broadcast_to_room(room_id, {
                        'type': 'chat',
                        'from_user': player_name,
                        'data': text
                    }, conn)

                elif msg_type == 'move':
                    room_id = self.rooms.get_client_room(conn)
                    if room_id is None:
                        continue

                    room = self.rooms.rooms.get(room_id)
                    if not room:
                        print(f"Move error: Room {room_id} not found")
                        continue
                    if not room.game_state:
                        print(f"Move error: Game in room {room_id} not started yet (Players: {len(room.players)})")
                        continue
                    
                    direction = msg_dict.get('direction')
                    if not direction:
                        continue
                    print(f"SERVER: Receiving move {direction} from {player_name} in Room {room_id}")
                    result = room.game_state.update_player_position(player_name, direction)
                                    
                elif msg_type == 'disconnect':
                    break

        except Exception as e:
             print('Ошибка в handle_client:', e)

        finally:
            self.remove_client(conn)

if __name__ == "__main__":
    server = Server()
    server.start_server()
