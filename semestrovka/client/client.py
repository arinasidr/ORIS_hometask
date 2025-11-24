import socket
import threading
import pickle

class GameClient:
    def __init__(self, host = 'localhost', port = 5555):
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
        self.running = False
        if self.socket:
            self.socket.close()
            print('Клиент отключен')
    
    def send_command(self, command):
        if self.socket:
            try:
                message = pickle.dumps(command)
                self.socket.send(message)
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
                data = self.socket.recv(4096)
                if not data:
                    print('[ОТКЛЮЧЕНИЕ] Соединение разорвано сервером')
                    break
                    
                msg = pickle.loads(data)
                self.process_message(msg)
        except Exception as e:
            print(f'Ошибка получения данных: {e}')
        finally:
            self.running = False

    def process_message(self, message):
        msg_type = message.get('type')

        if msg_type == 'join_room':
            self.room_id = message['room_id']
            print(f'Вы вошли в комнату: {self.room_id}')
        elif msg_type == 'room_update':
            players = message['data']
            print('Игроки в комнате: ', players)
        elif msg_type == 'state_update':
            self.game_state = message['state']
            #TODO добавить сюда отрисовку поля когда она будет готова
        elif msg_type == 'move_result':
            result = message['data']['result']
            print('Результат хода: ', result)
        elif msg_type == 'game_over':
            winner = message['winner']
            print('Игра окончена! Победитель: ', winner)
            self.running = False
            
        