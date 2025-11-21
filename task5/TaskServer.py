import socket
import threading
import json

class TaskServer:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.clients = [] # список кортежей (socket_name, board_name)
        self.tasks = {}  # {"Работа": [], "Учеба": []}
        self.lock = threading.Lock()

    # рассылка сообщения всем подключенным клиентам
    # exclude_client - по факту отправитель, у него и так уже должно быть обновлено
    # def broadcast(self, message):
    #     with self.lock:
    #         # используем копию списка, потому что мы оригигнал будем менять
    #         for client in self.clients[:]:
    #             try:
    #                 client.send((message + '\n').encode('utf-8'))
    #             except:
    #                 self.clients.remove(client)

    def broadcast_board(self, board_name):
        if board_name not in self.tasks:
            return 
        
        tasks_for_board = self.tasks[board_name]
        message = f"TASKS:{board_name}:{json.dumps(tasks_for_board)}"
        with self.lock:
            for client, client_board in self.clients[:]:
                if client_board == board_name:
                    try:
                        client.send((message + '\n').encode('utf-8'))
                    except:
                        self.clients.remove((client, client_board))

    # обработка сообщения от одного клиента
    def handle_client(self, client_socket):
        print(f"Новое подключение: {client_socket.getpeername()}")
        board_name = None
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8').strip()
                if not data:
                    break
                print(f"Получено: {data}")

                board_name_data = board_name
                if ':' in data:
                    parts = data.split(':', 2)
                    command  = parts[0]
                    board_name_data = parts[1]
                    if len(parts) > 2:
                        payload = parts[2]
                    else:
                        payload = None
                else:
                    command = data
                    board_name_data = "Главная доска"
                    payload = None

                if board_name is None and command in ['ADD', 'GET_TASKS', 'UPDATE']:
                    board_name = board_name_data
                    with self.lock:
                        for i, (client, board) in enumerate(self.clients):
                            if client == client_socket:
                                del self.clients[i]
                                break
                        self.clients.append((client_socket, board_name))
                        print(f"Клиент привязан к доске: {board_name}")

                with self.lock:
                    if board_name_data not in self.tasks:
                        self.tasks[board_name_data] = []
                        print(f"Создана новая доска: {board_name_data}")

                tasks_for_board = self.tasks[board_name_data]

                if command == "ADD":
                    try:
                        task = json.loads(payload)
                        tasks_for_board.append(task)
                        self.broadcast_board(board_name_data)
                    except json.JSONDecodeError:
                        print("JSON Error")
                    except Exception as e:
                        print(f"Ошибка в ADD: {e}")
                elif command == 'UPDATE':
                    try:
                        update_tasks = json.loads(payload)
                        self.tasks[board_name_data] = update_tasks
                        self.broadcast_board(board_name_data)
                    except json.JSONDecodeError:
                        print("JSON Error")
                    except Exception as e:
                        print(f"Ошибка в UPDATE: {e}")
                elif command == 'GET_TASKS' and board_name != board_name_data:
                    board_name = board_name_data
                    with self.lock:
                        for i, (client, board) in enumerate(self.clients):
                            if client == client_socket:
                                del self.clients[i]
                                break
                        self.clients.append((client_socket, board_name))
                    self.send_tasks_to_client(client_socket, board_name_data)

        except Exception as e:
            print(f"Ошибка: {e}")
        finally:
            with self.lock:
                for i, (client, board) in enumerate(self.clients):
                        if client == client_socket:
                            del self.clients[i]
                            break
            client_socket.close()
            print(f"Клиент отключен")

    # отправка текущего списка задач клиенту
    def send_tasks_to_client(self, client_socket, board_name):
        tasks_for_board = self.tasks.get(board_name, [])
        client_socket.send(f"TASKS:{board_name}:{json.dumps(tasks_for_board)}\n".encode('utf-8'))

    # запуск сервера
    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)

        print(f"Сервер задач запущен на {self.host}:{self.port}")

        try:
            while True:
                client_socket, address = server_socket.accept()
                with self.lock:
                    self.clients.append((client_socket, None)) #тут добавляем сначала None

                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,),
                    daemon=True
                )
                client_thread.start()

        except KeyboardInterrupt:
            print("Останавливаем сервер...")
        finally:
            server_socket.close()

if __name__ == "__main__":
    server = TaskServer()
    server.start()