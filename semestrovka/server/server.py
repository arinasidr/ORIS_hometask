import socket
import threading
import pickle
import random

def serialize(msg):
    return pickle.dumps(msg, protocol=pickle.HIGHEST_PROTOCOL)

def deserialize(data):
    return pickle.loads(data)

rooms = {}

def find_available_room():
    for room in rooms.values():
        if room['status'] == 'waiting' and len(room['players']) < 3:
            return room['room_id']
    return None

def create_new_room():
    room_id = random.randint(50) #мб потом поменять на счетчик
    room = {
        "room_id": room_id,
        "players": [],
        "status": "waiting",
        "state":None
    }
    rooms[room_id] = room
    return room_id

def add_client_to_room(client_socket, player_name):
    available_room = find_available_room()
    if not available_room:
        room_id = create_new_room()
    rooms[room_id]["players"].append((client_socket, player_name))


def handle_client(conn, addr):
    print(f"[ПОДКЛЮЧЕН] {addr}")
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                print(f"[ОТКЛЮЧЕНИЕ] {addr}")
                break

            msg = deserialize(data)
            print(f"[ПОЛУЧЕНО] {msg} от {addr}")

            response = {
                "type": "server_ack",
                "from_user": "server",
                "room_id": None,
                "data": "Сообщение получено"
            }
            conn.sendall(serialize(response))

        except Exception as e:
            print(f"[ОШИБКА] {addr}: {e}")
            break
    conn.close()

def accept_clients(server_socket):
    while True:
        conn, addr = server_socket.accept()
        client_thread = threading.Thread(target= handle_client, args=(conn, addr),daemon=True)
        client_thread.start()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('127.0.0.1', 12345))
    server_socket.listen()
    print("[СЕРВЕР ЗАПУЩЕН]")
    accept_clients(server_socket)

if __name__ == "__main__":
    start_server()