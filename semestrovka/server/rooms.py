import random
import pickle
import threading
import time

from game import GameState

class Room:
    def __init__(self, room_id):
        self.room_id = room_id
        self.players = {} #socket:player
        self.status = 'waiting'
        self.game_state = None
        self.loop_running = False

    def add_player(self, client_socket, player_name):
        self.players[client_socket] = player_name
        if len(self.players) == 2 or len(self.players) == 3:
            self.start_game()

    def remove_player(self, client_socket):
        if client_socket in self.players:
            name = self.players[client_socket]
            del self.players[client_socket]

            if self.game_state:
                self.game_state.remove_player(name)

            if not self.players:
                self.loop_running = False
    
    def start_game(self):
        if self.status == 'playing':
            return 
        
        self.game_state = GameState()
        self.game_state.init(list(self.players.values()))
        self.status = 'playing'

        self.loop_running = True
        threading.Thread(target=self.game_loop, daemon=True).start()

    def game_loop(self):
        while self.loop_running and self.status == 'playing':
            state = self.game_state.generate_state_packet()
            self.broadcast({
                'type': 'state_update',
                'state': state
            })

            winner = self.game_state.check_game_over()
            if winner is not None:
                self.broadcast({
                    'type': 'game_over',
                    'winner': winner
                })
                self.status = 'finished'
                self.loop_running = False
                break
            
            time.sleep(0.2)
    
    def broadcast(self, message_dict, is_own = None):
        lst = []
        for conn in list(self.players.keys()):
            if conn is is_own:
                continue
            try:
                conn.sendall(pickle.dumps(message_dict))
            except:
                lst.append(conn)
        
        for i in lst:
            del self.players[i]
        

class RoomManager:
    def __init__(self):
        self.rooms = {}

    def find_available_room(self):
        for room in self.rooms.values():
            if room.status == 'waiting' and len(room.players) < 3:
                return room
        return None

    def create_new_room(self):
        room_id = random.randint(0, 50) #мб все таки потом мы поменяем на счетчик да арина
        if room_id not in self.rooms:
            room = Room(room_id)
            self.rooms[room_id] = room
            return room
        else:
            return self.create_new_room()
        
    def add_client_to_room(self, client_socket, player_name):
        room = self.find_available_room()
        if not room:
            room = self.create_new_room()
        room.add_player(client_socket, player_name)
        return room.room_id
        
    def remove_client_from_room(self,  client_socket):
        rooms_list = list(self.rooms.values())
        for room in rooms_list:
            if client_socket in room.players:
                room.remove_player(client_socket)
                if not room.players:
                    del self.rooms[room.room_id]

    def broadcast_to_room(self, room_id, message, is_own = None):
        room = self.rooms.get(room_id)
        if room:
            room.broadcast(message, is_own)

    def get_client_room(self, client_socket):
        for room in self.rooms.values():
            if client_socket in room.players:
                return room.room_id
        return None
    
    def get_room_players(self, room_id):
        room = self.rooms.get(room_id)
        if not room:
            return []
        return list(room.players.values())

