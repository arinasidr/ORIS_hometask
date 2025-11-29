import random
import pickle
import threading
import time
from game import GameState

class Room:
    def __init__(self, room_id):
        self.room_id = room_id
        self.players = {}     # socket: player_name
        self.status = 'waiting'
        self.game_state = None
        self.loop_running = False

    def add_player(self, sock, name):
        self.players[sock] = name
        if len(self.players) == 3:     # старт игры
            self.start_game()

    def remove_player(self, sock):
        if sock in self.players:
            name = self.players[sock]
            del self.players[sock]

            if self.game_state:
                self.game_state.remove_player(name)

            if not self.players:
                self.loop_running = False

    def broadcast(self, msg, is_own=None):
        remove = []
        data = pickle.dumps(msg, pickle.HIGHEST_PROTOCOL)
        packet = len(data).to_bytes(4, 'big') + data

        for conn in list(self.players.keys()):
            if conn is is_own:
                continue
            try:
                conn.sendall(packet)
            except:
                remove.append(conn)

        for c in remove:
            if c in self.players:
                del self.players[c]

    def start_game(self):
        if self.status == 'playing':
            return
        self.status = 'playing'
        self.game_state = GameState()
        self.game_state.init(list(self.players.values()))

        initial_state = self.game_state.generate_state_packet()
        self.broadcast({'type': 'state_update', 'state': initial_state})

        self.loop_running = True
        threading.Thread(target=self.game_loop, daemon=True).start()

    def game_loop(self):
        print(f"Room {self.room_id} loop STARTED")
        while self.loop_running and self.status == 'playing':
            try:
                state = self.game_state.generate_state_packet() 

                self.broadcast({
                    'type': 'state_update',
                    'state': state
                })

                winner = self.game_state.check_game_over()
                if winner:
                    self.broadcast({'type': 'game_over', 'winner': winner})
                    self.status = 'finished'
                    self.loop_running = False
                    print(f'room {self.room_id} GAME OVER. winner: {winner}')
                    break
            
            except Exception as e:
                print(f'!!! CRITICAL ERROR IN GAME LOOP Room {self.room_id}: {e}')
            
            time.sleep(0.2)

class RoomManager:
    def __init__(self):
        self.rooms = {}

    def find_available_room(self):
        for room in self.rooms.values():
            if room.status == 'waiting' and len(room.players) < 3:
                return room
        return None

    def create_new_room(self):
        room_id = random.randint(1, 50)
        if room_id not in self.rooms:
            room = Room(room_id)
            self.rooms[room_id] = room
            return room
        else:
            return self.create_new_room()

    def add_client_to_room(self, sock, name):
        room = self.find_available_room()
        if not room:
            room = self.create_new_room()

        room.add_player(sock, name)
        return room.room_id

    def remove_client_from_room(self, sock):
        for room in list(self.rooms.values()):
            if sock in room.players:
                room.remove_player(sock)
                if not room.players:
                    del self.rooms[room.room_id]

    def get_room_players(self, room_id):
        r = self.rooms.get(room_id)
        if not r:
            return []
        return list(r.players.values())

    def get_client_room(self, sock):
        for room in self.rooms.values():
            if sock in room.players:
                return room.room_id
        return None

    def broadcast_to_room(self, room_id, msg, is_own=None):
        room = self.rooms.get(room_id)
        if room:
            room.broadcast(msg, is_own)
