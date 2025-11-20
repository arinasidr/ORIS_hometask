import random
import pickle

class Room:
    def __init__(self, room_id):
        self.room_id = room_id
        self.players = {} #socket:player
        self.status = 'waiting'
        #self.game_state = GameState()

    def add_player(self, client_socket, player_name):
        self.players[client_socket] = player_name
        if len(self.players) == 2:
            self.start_game()

    def remove_player(self, client_socket):
        if client_socket in self.players:
            del self.players[client_socket]
    
    def start_game(self):
        self.status = 'playing'
        #TODO реализовать начало игры (это когда будет готов класс GameState)

class RoomManager:
    def __init__(self):
        self.rooms = {}

    def find_available_room(self):
        for room in self.rooms.values():
            if len(room.players) < 3:
                return room
        return None

    def create_new_room(self):
        while True:
            room_id = random.randint(0, 50) #мб потом поменять на счетчик
            if room_id not in self.rooms:
                room = Room(room_id)
                self.rooms[room_id] = room
                return room
        
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
        if not room:
            return
        
        for conn in list(room.players.keys()):
            if conn is is_own:
                continue
            try:
                conn.sendall(pickle.dumps(message, protocol=pickle.HIGHEST_PROTOCOL))
            except:
                self.remove_client_from_room(conn)

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

