import keyboard
import os
import time
import random
from dataclasses import dataclass
from typing import List, Tuple

### SETTINGS AND CONSTANTS
# BOARD
BOARD_SIZE = 10
RANDOM_WALL_BREAK_CHANCE = 0.35
GOLD_PICKUPS_AMOUNT = 10
GOLD_ICON = "💰"
# PLAYERS
STARTING_MAX_HEALTH = 5
STARTING_KNOCKBACK_DISTANCE = 2
STARTING_KNOCKBACK_RESISTANCE = 0
STARTING_ATTACK_DAMAGE = 1
DEFAULT_MOVES_PER_TURN = 3
# GOLD SYSTEM
DEFAULT_GOLD_FROM_PICKUP = 4
DEFAULT_GOLD_PER_TURN = 1


PLAYER_STARTING_STATS = [
    {
        "name": "Dragon",
        "icon": "🐲",
        "start": (0, 0)
    },
    {
        "name": "Fox", 
        "icon": "🦊", 
        "start": (BOARD_SIZE - 1, BOARD_SIZE - 1)
    },
]

# UNUSED
MAZE_TILE_SIZE = 2
STARTING_ATTACK_RANGE = 1
STARTING_MOVE_COUNT = 1

SHOP_KEY = 's'
MOVEMENT_KEYS = {
    'w': (-1, 0),    # Move up
    'x': (1, 0),     # Move down
    'a': (0, -1),    # Move left
    'd': (0, 1),     # Move right
    'q': (-1, -1),   # Move diagonally up-left
    'e': (-1, 1),    # Move diagonally up-right
    'z': (1, -1),    # Move diagonally down-left
    'c': (1, 1)      # Move diagonally down-right
}

### INITIAL
@dataclass
class Player:
    id: int
    name: str
    position: Tuple[int, int]
    icon: str
    max_health: int = STARTING_MAX_HEALTH
    health: int = STARTING_MAX_HEALTH
    damage: int = STARTING_ATTACK_DAMAGE
    knockback_strength: int = STARTING_KNOCKBACK_DISTANCE
    knockback_resistance: int = STARTING_KNOCKBACK_RESISTANCE
    gold: int = 0
    gold_per_turn: int = DEFAULT_GOLD_PER_TURN
    gold_from_pickup: int = DEFAULT_GOLD_FROM_PICKUP

    total_moves: int = DEFAULT_MOVES_PER_TURN
    moves_used: int = 0

    def is_alive(self):
        return self.health > 0



class Game:
    def __init__(self):
        # players
        self.players = []
        for i in range(len(PLAYER_STARTING_STATS)):
            self.players.append(Player(i, PLAYER_STARTING_STATS[i]["name"], PLAYER_STARTING_STATS[i]["start"], PLAYER_STARTING_STATS[i]["icon"]))
        self.current_player_index = 0

        # board
        self.board_size = BOARD_SIZE
        self.gold_positions = []
        self.place_random_gold(GOLD_PICKUPS_AMOUNT)

        self.generate_walls()

    def place_random_gold(self, count):
        empty_tiles = [
            (r, c) for r in range(self.board_size) for c in range(self.board_size)
            if all(p.position != (r, c) for p in self.players)
        ]
        self.gold_positions = random.sample(empty_tiles, min(count, len(empty_tiles)))


    def generate_walls(self):
        # Generate maze-like walls with a guarantee of a connected path
        size = self.board_size
        self.vertical_walls = [[True for _ in range(size - 1)] for _ in range(size)]
        self.horizontal_walls = [[True for _ in range(size)] for _ in range(size - 1)]
        visited = [[False for _ in range(size)] for _ in range(size)]

        def is_within_bounds(row, col):
            return 0 <= row < size and 0 <= col < size

        def generate_maze(row, col):
            visited[row][col] = True
            directions = [("up", -1, 0), ("down", 1, 0), ("left", 0, -1), ("right", 0, 1)]
            random.shuffle(directions)
            for direction, delta_row, delta_col in directions:
                next_row, next_col = row + delta_row, col + delta_col
                if is_within_bounds(next_row, next_col) and not visited[next_row][next_col]:
                    if direction == "up":
                        self.horizontal_walls[row - 1][col] = False
                    elif direction == "down":
                        self.horizontal_walls[row][col] = False
                    elif direction == "left":
                        self.vertical_walls[row][col - 1] = False
                    elif direction == "right":
                        self.vertical_walls[row][col] = False
                    generate_maze(next_row, next_col)

        generate_maze(0, 0)

        # Break additional random walls
        for row in range(size):
            for col in range(size - 1):
                if self.vertical_walls[row][col] and random.random() < RANDOM_WALL_BREAK_CHANCE:
                    self.vertical_walls[row][col] = False
        for row in range(size - 1):
            for col in range(size):
                if self.horizontal_walls[row][col] and random.random() < RANDOM_WALL_BREAK_CHANCE:
                    self.horizontal_walls[row][col] = False

    ### MOVEMENT

    def move_current_player(self, key: str):
        # Move the current player or stay and attack
        # returns True if movement successful, False if failed
        player = self.get_current_player()
        delta_row, delta_col = MOVEMENT_KEYS[key]
        cur_row, cur_col = player.position
        new_row = cur_row + delta_row
        new_col = cur_col + delta_col

        # move failed
        if not self.is_valid_destination(new_row, new_col, (cur_row, cur_col)):
            return False
        
        player.position = (new_row, new_col)
        
        # pickup gold
        if player.position in self.gold_positions:
            player.gold += player.gold_from_pickup
            self.gold_positions.remove(player.position)

        return True
        


    def is_cardinal_move_blocked(self, from_row, from_col, to_row, to_col):
        # Check for walls in horizontal or vertical movement
        if from_row == to_row:
            min_col = min(from_col, to_col)
            return self.vertical_walls[from_row][min_col]
        elif from_col == to_col:
            min_row = min(from_row, to_row)
            return self.horizontal_walls[min_row][from_col]
        return True

    def is_diagonal_path_blocked(self, from_row, from_col, to_row, to_col):
        # Determine if diagonal movement is blocked using L-shaped checks
        mid_1_clear = not self.is_cardinal_move_blocked(from_row, from_col, from_row, to_col) and \
                      not self.is_cardinal_move_blocked(from_row, to_col, to_row, to_col)
        mid_2_clear = not self.is_cardinal_move_blocked(from_row, from_col, to_row, from_col) and \
                      not self.is_cardinal_move_blocked(to_row, from_col, to_row, to_col)
        return not (mid_1_clear or mid_2_clear)

    def is_any_move_blocked(self, from_row, from_col, to_row, to_col):
        # Wrapper to check whether any move is blocked (straight or diagonal)
        if abs(from_row - to_row) == 1 and abs(from_col - to_col) == 1:
            return self.is_diagonal_path_blocked(from_row, from_col, to_row, to_col)
        return self.is_cardinal_move_blocked(from_row, from_col, to_row, to_col)

    def is_valid_destination(self, to_row, to_col, from_pos):
        # Ensure move is inside the board, not occupied, and not blocked by walls
        from_row, from_col = from_pos
        if not (0 <= to_row < self.board_size and 0 <= to_col < self.board_size):
            return False
        if any(p.position == (to_row, to_col) and p.is_alive() for p in self.players):
            return False
        if self.is_any_move_blocked(from_row, from_col, to_row, to_col):
            return False
        return True

    ### PLAYER INTERACTIONS

    def player_turn(self, current_player, key):
        # returns turn_over, moved

        # invalid key
        if key not in MOVEMENT_KEYS and key != SHOP_KEY:
            return False, False

        if key == SHOP_KEY:
            # shop here
            return True, current_player.moves_used
        
        if self.move_current_player(key):
            current_player.moves_used += 1

        if current_player.moves_used >= current_player.total_moves:
            return True, current_player.moves_used
        else:
            return False, False

    def apply_attacks(self, attacker: Player, moved: bool = True):
        damage = attacker.damage if moved else attacker.damage * 2
        knockback_dealt = attacker.knockback_strength if moved else attacker.knockback_strength * 2

        # Deal damage and apply knockback to nearby enemies
        attacker_row, attacker_col = attacker.position

        for defender in self.players:
            # Get attacker's effective knockback distance
            knockback_distance = max(0, knockback_dealt - defender.knockback_resistance)
        
            if defender.id == attacker.id or not defender.is_alive():
                continue

            defender_row, defender_col = defender.position
            if abs(attacker_row - defender_row) > 1 or abs(attacker_col - defender_col) > 1:
                continue

            # Wall collision
            if self.is_any_move_blocked(attacker_row, attacker_col, defender_row, defender_col):
                print(f"{attacker.name}'s attack on {defender.name} is blocked by a wall.")
                continue

            defender.health -= damage

            delta_row = defender_row - attacker_row
            delta_col = defender_col - attacker_col

            def is_clear_move(r, c, origin):
                return self.is_valid_destination(r, c, origin)

            # Knockback over specified distance
            for _ in range(knockback_distance):
                current_row, current_col = defender.position
                new_row = current_row + delta_row
                new_col = current_col + delta_col

                if is_clear_move(new_row, new_col, (current_row, current_col)):
                    defender.position = (new_row, new_col)
                    print(f"{defender.name} is pushed to {defender.position}")
                    continue

                # Diagonal fallback resolution
                if delta_row != 0 and delta_col != 0:
                    option_row = (current_row + delta_row, current_col)
                    option_col = (current_row, current_col + delta_col)
                    options = []
                    if is_clear_move(*option_row, (current_row, current_col)):
                        options.append(option_row)
                    if is_clear_move(*option_col, (current_row, current_col)):
                        options.append(option_col)

                    if options:
                        chosen = random.choice(options)
                        defender.position = chosen
                        print(f"{defender.name} is pushed to {defender.position} (random choice)")
                        delta_row = chosen[0] - current_row
                        delta_col = chosen[1] - current_col
                        continue

                print(f"{defender.name} could not be pushed further due to obstacles")
                break

    def upgrade_stat(self, player, stat_to_upgrade):
        print("Upgrading " + stat_to_upgrade)
        if stat_to_upgrade == 'max_health':
            player.max_health *= 2
            player.health *= 2
        elif stat_to_upgrade == 'damage':
            player.damage *= 2
        elif stat_to_upgrade == 'knockback_strength':
            player.knockback_strength *= 2
        elif stat_to_upgrade == 'knockback_resistance':
            if player.knockback_resistance > 0:
                player.knockback_resistance *= 2
            else:
                player.knockback_resistance = 1

                
    ### FORMATTING

    def draw_board(self):
        # Print the game board with walls and players
        size = self.board_size
        board = [[' ◻️' for _ in range(size)] for _ in range(size)]

        # objects
        for row, col in self.gold_positions:
            board[row][col] = GOLD_ICON

        for player in self.players:
            if player.is_alive():
                row, col = player.position
                board[row][col] = player.icon

        # main board
        for row in range(size):
            top_line = ""
            for col in range(size):
                top_line += "+"
                top_line += "---" if row > 0 and self.horizontal_walls[row - 1][col] else "   "
            top_line += "+"
            print(top_line)
            middle_line = ""
            for col in range(size):
                middle_line += "┊" if col > 0 and self.vertical_walls[row][col - 1] else " "
                middle_line += f"{board[row][col]} "
            print(middle_line)
        bottom_line = ""
        for col in range(size):
            bottom_line += "+"
            bottom_line += "---" if self.horizontal_walls[size - 2][col] else "   "
        bottom_line += "+"
        print(bottom_line)

    def clear_screen(self):
        # Clear terminal screen
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_status(self):
        for player in self.players:
            print(f"--- {player.name} ---")
            print(f"Health: {player.health} / {player.max_health}")
            print(f"Damage: {player.damage}")
            print(f"Knockback Strength: {player.knockback_strength}")
            print(f"Knockback Resistance: {player.knockback_resistance}")
            print(f"Position: {player.position}")
            print(f"Gold: {player.gold}")
            print()

    ### UTILS

    def get_current_player(self) -> Player:
        # Return the player whose turn it is
        return self.players[self.current_player_index]

    def is_game_over(self):
        # Check if only one player remains
        return sum(p.is_alive() for p in self.players) <= 1
    
    ### MAIN LOOP

    def run(self):
        # Main game loop handling rendering and input
        while not self.is_game_over():
            current_player = self.get_current_player()
            row, col = current_player.position
            can_move = any(
                self.is_valid_destination(row + dr, col + dc, (row, col))
                for dr, dc in MOVEMENT_KEYS.values()
            )
            if not can_move:
                print(f"{current_player.name} has no moves. Staying and attacking...")
                time.sleep(1.5)
                self.apply_attacks(current_player, moved = False)
                self.current_player_index = (self.current_player_index + 1) % len(self.players)
                continue

            turn_over = False
            moved = True
            while not turn_over:
                self.render_all(current_player)
                event = keyboard.read_event()
                if event.event_type == keyboard.KEY_DOWN:
                    key = event.name.lower()
                    if key in MOVEMENT_KEYS or key == SHOP_KEY:
                        turn_over, moved = self.player_turn(current_player, key)
            self.player_end_turn(current_player, moved)

        print("Game Over!")
        for p in self.players:
            if p.is_alive():
                print(f"{p.name} wins!")

    def render_all(self, current_player):
        self.clear_screen()
        print(current_player.icon * BOARD_SIZE)
        self.draw_board()
        self.display_status()
            
        print("Move with: ")
        print("Q W E")
        print("A   D")
        print("Z X C")
        print("Stay and deal extra damage and knockback with S.")
        print()

    def player_end_turn(self, current_player, moved):
        self.apply_attacks(current_player, moved = moved)
        current_player.gold += current_player.gold_per_turn
        current_player.moves_used = 0

        self.current_player_index = (self.current_player_index + 1) % len(self.players)

if __name__ == "__main__":
    Game().run()
