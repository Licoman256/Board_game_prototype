# Turn-based grid combat game with diagonal movement and knockback logic

import keyboard
import os
import time
import random
from dataclasses import dataclass
from typing import List, Tuple

### SETTINGS AND CONSTANTS
BOARD_SIZE = 10
MAX_HEALTH = 5
ATTACK_DAMAGE = 1
MAZE_TILE_SIZE = 2

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
    color: str
    position: Tuple[int, int]
    health: int = MAX_HEALTH

    def is_alive(self):
        return self.health > 0

class Game:
    def __init__(self):
        # Initialize board and players
        self.board_size = BOARD_SIZE
        self.players: List[Player] = [
            Player(1, "Red", 'R', (0, 0)),
            Player(2, "Blue", 'B', (self.board_size - 1, self.board_size - 1)),
        ]
        self.current_player_index = 0
        self.generate_walls()

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
        extra_wall_break_chance = 0.
        for row in range(size):
            for col in range(size - 1):
                if self.vertical_walls[row][col] and random.random() < extra_wall_break_chance:
                    self.vertical_walls[row][col] = False
        for row in range(size - 1):
            for col in range(size):
                if self.horizontal_walls[row][col] and random.random() < extra_wall_break_chance:
                    self.horizontal_walls[row][col] = False

    ### MOVEMENT

    def move_current_player(self, key: str):
        # Move the current player or stay and attack
        player = self.get_current_player()
        if key == 's':
            self.apply_attacks(player)
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            return
        delta_row, delta_col = MOVEMENT_KEYS[key]
        cur_row, cur_col = player.position
        new_row = cur_row + delta_row
        new_col = cur_col + delta_col
        if self.is_valid_destination(new_row, new_col, (cur_row, cur_col)):
            player.position = (new_row, new_col)
            self.apply_attacks(player)
            self.current_player_index = (self.current_player_index + 1) % len(self.players)

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

    def apply_attacks(self, attacker: Player, stayed_in_place: bool = False, knockback_distance: int = 2):
        # Deal damage and apply knockback to nearby enemies
        attacker_row, attacker_col = attacker.position
        bonus_damage = ATTACK_DAMAGE + 1 if stayed_in_place else ATTACK_DAMAGE

        for defender in self.players:
            if defender.id == attacker.id or not defender.is_alive():
                continue

            defender_row, defender_col = defender.position
            if abs(attacker_row - defender_row) > 1 or abs(attacker_col - defender_col) > 1:
                continue

            defender.health -= bonus_damage

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

    ### FORMATTING

    def draw_board(self):
        # Print the game board with walls and players
        size = self.board_size
        board = [['.' for _ in range(size)] for _ in range(size)]
        for p in self.players:
            if p.is_alive():
                row, col = p.position
                symbol = p.color.upper() if p == self.get_current_player() else p.color.lower()
                board[row][col] = symbol
        for row in range(size):
            top_line = ""
            for col in range(size):
                top_line += "+"
                top_line += "---" if row > 0 and self.horizontal_walls[row - 1][col] else "   "
            top_line += "+"
            print(top_line)
            middle_line = ""
            for col in range(size):
                middle_line += "|" if col > 0 and self.vertical_walls[row][col - 1] else " "
                middle_line += f" {board[row][col]} "
            middle_line += "|"
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
        # Display player health and positions
        for p in self.players:
            print(f"{p.name}: {p.health} HP at {p.position}")

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
        print("Use W A X D Q E Z C to move, S to stay and attack")
        while not self.is_game_over():
            self.clear_screen()
            current = self.get_current_player()
            print(f"{current.name}'s turn ({current.color.upper()})")
            self.draw_board()
            self.display_status()
            row, col = current.position
            can_move = any(
                self.is_valid_destination(row + dr, col + dc, (row, col))
                for dr, dc in MOVEMENT_KEYS.values()
            )
            if not can_move:
                print(f"{current.name} has no moves. Staying and attacking...")
                time.sleep(1.5)
                self.apply_attacks(current)
                self.current_player_index = (self.current_player_index + 1) % len(self.players)
                continue
            print("Move with: ")
            print("Q W E")
            print("A   D")
            print("Z X C")
            print("Stay and deal extra damage and knockback with S")
            while True:
                event = keyboard.read_event()
                if event.event_type == keyboard.KEY_DOWN:
                    key = event.name.lower()
                    if key in MOVEMENT_KEYS or key == 's':
                        self.move_current_player(key)
                        break
        print("Game Over!")
        for p in self.players:
            if p.is_alive():
                print(f"{p.name} wins!")

if __name__ == "__main__":
    Game().run()
