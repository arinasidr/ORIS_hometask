import socket
import threading
import pickle

from PyQt5.QtCore import QObject, pyqtSignal

class GameClient(QObject):
    signal_join_room = pyqtSignal(int)            # room_id
    signal_room_update = pyqtSignal(list)         # список имён
    signal_state_update = pyqtSignal(dict)        # state dict
    signal_move_result = pyqtSignal(dict)         # результат хода
    signal_game_over = pyqtSignal(str)            # winner 
    signal_error = pyqtSignal(str)                # текст ошибки 
    signal_chat = pyqtSignal(str)
    def __init__(self, host = 'localhost', port = 12345):
        super().__init__()
        self.host = host
        self.port = port
        self.socket = None
        #поток принимает данные с сервера, обрабатывает сообщения, кладет их в очередь для гуи
        self.net_thread = None
        self.running = False
        self.game_state = None
        self.room_id = None
        self.player_name = None
        self.players = None
    
    def recv_exact(self, n):
        data = b''
        while len(data) < n:
            packet = self.socket.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def recv_message(self):
        header = self.recv_exact(4)
        if not header:
            return None
        length = int.from_bytes(header, 'big')
        data = self.recv_exact(length)
        if not data:
            return None
        return pickle.loads(data)

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))

            self.running = True

            self.net_thread = threading.Thread(target = self.listen_server, daemon=True)
            self.net_thread.start()
            self.send_command({'type':'signup', 'data':self.player_name})
            return True
        except Exception as e:
            print(f'Ошибочка: {e}')
            return False
        
    def disconnect_client(self):
        try:
            self.send_command({'type': 'disconnect'})
        except:
            pass
        self.running = False
        if self.socket:
            self.socket.close()
            print('Клиент отключен')
    
    def send_command(self, command):
        if self.socket:
            try:
                message = pickle.dumps(command)
                self.socket.sendall(len(message).to_bytes(4, 'big') + message)
            except Exception as e:
                print(f'Ошибочка: {e}')

    def send_move(self, direction):
        command = {
            'type': 'move',
            'direction': direction
        }
        self.send_command(command)

    def listen_server(self):
        try:
            while self.running:
                msg = self.recv_message()
                if not msg:
                    print('[ОТКЛЮЧЕНИЕ] Соединение разорвано сервером')
                    break
                self.process_message(msg)
        except Exception as e:
            print(f'Ошибка получения данных: {e}')
        finally:
            self.running = False

    def process_message(self, message):
        msg_type = message.get('type')

        if msg_type == 'join_room':
            self.room_id = message['room_id']
            self.signal_join_room.emit(self.room_id)
            print(f'Вы вошли в комнату: {self.room_id}')
        elif msg_type == 'room_update':
            self.players = message['data']
            self.signal_room_update.emit(self.players)
            print('Игроки в комнате: ', self.players)
        elif msg_type == 'state_update':
            state = message['state']
            self.game_state = state
            self.signal_state_update.emit(state)
        elif msg_type == 'move_result':
            result = message['data']['result']
            self.signal_move_result.emit(message['data'])
            print('Результат хода: ', result)
        elif msg_type == 'game_over':
            winner = message['winner']
            self.signal_game_over.emit(winner)
            print('Игра окончена! Победитель: ', winner)
            self.running = False
            self.disconnect_client()
        elif msg_type == 'chat':
            user = message['from_user']
            text = message['data']
            self.signal_chat.emit(f'{user}: {text}')
        else:
            self.signal_error.emit(f'Неизвестная команда: {msg_type}')