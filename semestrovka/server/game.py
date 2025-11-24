import time
import random

class GameState:
    def __init__(self):
        self.field = []
        self.positions = {} # player_name: (x, y)
        self.territories = {}  # player: set((x, y), ...)
        self.last_move = {} # player_name: time last move
        self.blocked_until = {} #player_name: time (когда разблокируется)
        self.start_time = None

    def init(self, players):
        self.field = [[0]*15 for _ in range(15)]
        self.positions = {}
        self.territories = {}
        self.blocked_until = {}
        self.last_move = {}
        self.start_time = time.time()

        for i, player in enumerate(players):
            if i == 0:
                self.positions[player] = (0, 0)
                self.territories[player] = {(0, 0)}
            elif i == 1:
                self.positions[player] = (14, 14)
                self.territories[player] = {(14, 14)}
            elif i == 2:
                self.positions[player] = (0, 14)
                self.territories[player] = {(0, 14)}
        
            self.blocked_until[player] = 0
            self.last_move[player] = 0

    def remove_player(self, player_name):
        if player_name in self.positions:
            del self.positions[player_name]
        if player_name in self.territories:
            del self.territories[player_name]
        if player_name in self.last_move:
            del self.last_move[player_name]
        if player_name in self.blocked_until:
            del self.blocked_until[player_name]

    def update_player_position(self, player_name, direction):
        now = time.time()

        if now < self.blocked_until[player_name]:
            return {'result': 'blocked', 'player': player_name, 'new_pos': self.positions[player_name]}
        
        if now - self.last_move[player_name] < 0.25:
            return {'result': 'cooldown', 'player':player_name, 'new_pos': self.positions[player_name]}
        
        x, y = self.positions[player_name]
        new_x, new_y = x, y
        if direction == 'up':
            new_y = y - 1 if y - 1 >= 0 else 0
        elif direction == 'down':
            new_y = y + 1 if y + 1 <= 14 else 14
        elif direction == 'left':
            new_x = x - 1 if x - 1 >= 0 else 0
        elif direction == 'right':
            new_x = x + 1 if x + 1 <=14 else 14
        
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
            self.blocked_until[blocked] = now + 1

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
            blocked = player_name if player_name != owner else occupant
            self.blocked_until[blocked] = now + 2

            self.last_move[player_name] = now

            return {
                'result': 'collision_own',
                'blocked': blocked,
                'owner': owner,
                'new_pos': self.positions[player_name]
            }
        
        #игрок зашел на чужую территорию
        if owner is not None and owner != player_name and occupant is None:
            self.blocked_until[player_name] = now + 2
            self.last_move[player_name] = now
            return {
                'result': 'blocked_own',
                'blocked': player_name,
                'owner': owner,
                'new_pos': self.positions[player_name]
            }
        
        if owner is None:
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
            self.last_move[player_name] = now
            return {
                'result': 'move',
                'blocked': player_name,
                'new_pos': (new_x, new_y)
            }
        
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
        
        return max(scores, key = scores.get)
        
    def generate_state_packet(self):
        return {
            'field': self.field,
            'positions':self.positions,
            'territories': {p: list(cells) for p, cells in self.territories.items()},
            'blocked': {p: max(0, self.blocked_until[p] - time.time()) for p in self.blocked_until}
        }
