import time
import random
import threading

class GameState:
    def __init__(self):
        self.field = []
        self.positions = {} # player_name: (x, y)
        self.territories = {}  # player: set((x, y), ...)
        self.last_move = {} # player_name: time last move
        self.blocked_until = {} #player_name: time (когда разблокируется)
        self.start_time = None
        self.lock = threading.Lock()

    def init(self, players):
        self.field = [[0]*15 for _ in range(15)]
        self.positions = {}
        self.territories = {}
        self.blocked_until = {}
        self.last_move = {}
        self.start_time = time.time()

        for i, player in enumerate(players):
            if i == 0:
                pos = (0, 0)
            elif i == 1:
                pos = (14, 14)
            elif i == 2:
                pos = (0, 14)
            else:
                pos = (0, 0)

            self.positions[player] = pos
            self.territories[player] = {pos}
            self.blocked_until[player] = 0.0
            self.last_move[player] = 0.0

    def remove_player(self, player_name):
        with self.lock:
            if player_name in self.positions:
                del self.positions[player_name]
            if player_name in self.territories:
                del self.territories[player_name]
            if player_name in self.last_move:
                del self.last_move[player_name]
            if player_name in self.blocked_until:
                del self.blocked_until[player_name]

    def update_player_position(self, player_name, direction):
        with self.lock:
            now = time.time()
            if player_name not in self.positions:
                return {'result': 'invalid', 'new_pos': None}
            
            if now < self.blocked_until[player_name]:
                return {'result': 'blocked', 'player': player_name, 'new_pos': self.positions[player_name]}
            
            if now - self.last_move[player_name] < 0.25:
                return {'result': 'cooldown', 'player':player_name, 'new_pos': self.positions[player_name]}
            
            x, y = self.positions[player_name]
            new_x, new_y = x, y
            if direction == 'up':
                new_y = max(0, y - 1)
            elif direction == 'down':
                new_y = min(14, y + 1)
            elif direction == 'left':
                new_x = max(0, x - 1)
            elif direction == 'right':
                new_x = min(14, x + 1)
            else:
                return {'result': 'invalid_direction', 'new_pos': (x, y)}
            
            if (new_x, new_y) == (x, y):
                self.last_move[player_name] = now
                return {'result': 'move', 'blocked': None, 'new_pos': (x, y)}

            # кто стоит в клетке
            occupant = None
            for other, pos in self.positions.items():
                if other != player_name and pos == (new_x, new_y):
                    occupant = other
                    break
            
            #кто владелец клетки
            owner = None
            for p, cells in self.territories.items():
                if (new_x, new_y) in cells:
                    owner = p
                    break

            #столкновение на пустой клетке
            if owner is None and occupant is not None:
                players = [player_name, occupant]
                blocked = random.choice(players)
                self.blocked_until[blocked] = now + 1.0

                winner = occupant if blocked == player_name else player_name

                self.positions[winner] = (new_x, new_y)
                self.territories[winner].add((new_x, new_y))

                self.last_move[winner] = now
                self.last_move[player_name] = now

                return {
                    'result': 'collision_empty',
                    'blocked': blocked,
                    'winner': winner,
                    'new_pos': self.positions[player_name]
                }
            
            #столкновение на занятой клетке
            if owner is not None and occupant is not None:
                if player_name != owner:
                    blocked = player_name
                else:
                    blocked = occupant
                self.blocked_until[blocked] = now + 2.0
                self.last_move[player_name] = now

                return {
                    'result': 'collision_own',
                    'blocked': blocked,
                    'owner': owner,
                    'new_pos': self.positions[player_name]
                }
            
            #игрок зашел на чужую территорию
            if owner is not None and owner != player_name and occupant is None:
                self.blocked_until[player_name] = now + 2.0
                self.last_move[player_name] = now
                return {
                    'result': 'blocked_own',
                    'blocked': player_name,
                    'owner': owner,
                    'new_pos': self.positions[player_name]
                }
            
            if owner is None and occupant is None:
                self.positions[player_name] = (new_x, new_y)
                self.territories[player_name].add((new_x, new_y))
                self.last_move[player_name] = now
                return {
                    'result': 'move',
                    'blocked': None,
                    'new_pos': (new_x, new_y)
                }
            
            if owner == player_name:
                self.positions[player_name] = (new_x, new_y)
                self.territories[player_name].add((new_x, new_y))
                self.last_move[player_name] = now
                return {
                    'result': 'move',
                    'blocked': player_name,
                    'new_pos': (new_x, new_y)
                }

            return {'result': 'unknown', 'new_pos': self.positions[player_name]}
        
    def check_game_over(self):
        if time.time() - self.start_time >= 300:
            return self.get_winner()
        
        if len(self.positions) == 1:
            return list(self.positions.keys())[0]
        
        for player, cells in self.territories.items():
            if len(cells) >= 120:
                return player
            
        return None
        
    def get_winner(self):
        scores = {}
        for player, cells in self.territories.items():
            scores[player] = len(cells)
        if not scores:
            return None
        return max(scores, key = scores.get)
        
    def generate_state_packet(self):
        with self.lock:
            return {
                'field': self.field,
                'positions': {p: tuple(pos) for p, pos in list(self.positions.items())},
                'territories': {p: [tuple(c) for c in cells] for p, cells in list(self.territories.items())},
                'blocked': {p: max(0.0, self.blocked_until.get(p, 0.0) - time.time()) for p in list(self.blocked_until.keys())}
            }
