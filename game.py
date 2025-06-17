# Game with diagonal movement, readable logic, stay-in-place attack, and clear comments

import keyboard
import os
import time
import random
from dataclasses import dataclass
from typing import List, Tuple

# Game settings
BOARD_SIZE = 5
MAX_HEALTH = 5
ATTACK_DAMAGE = 1

# Key bindings for movement; added 'x' for down and 's' for stay-in-place attack
MOVEMENT_KEYS = {
    'w': (-1, 0),    # Up
    'x': (1, 0),     # Down (was 's')
    'a': (0, -1),    # Left
    'd': (0, 1),     # Right
    'q': (-1, -1),   # Up-left
    'e': (-1, 1),    # Up-right
    'z': (1, -1),    # Down-left
    'c': (1, 1)      # Down-right
}

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
        self.board_size = BOARD_SIZE
        self.players: List[Player] = [
            Player(1, "Red", 'R', (0, 0)),
            Player(2, "Blue", 'B', (BOARD_SIZE - 1, BOARD_SIZE - 1)),
        ]
        self.current_turn_index = 0
        self.generate_walls()

    def generate_walls(self):
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
            for direction, dr, dc in directions:
                next_row, next_col = row + dr, col + dc
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

        # Randomly break some additional walls
        extra_wall_break_chance = 0.25
        for row in range(size):
            for col in range(size - 1):
                if self.vertical_walls[row][col] and random.random() < extra_wall_break_chance:
                    self.vertical_walls[row][col] = False
        for row in range(size - 1):
            for col in range(size):
                if self.horizontal_walls[row][col] and random.random() < extra_wall_break_chance:
                    self.horizontal_walls[row][col] = False

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def get_current_player(self) -> Player:
        return self.players[self.current_turn_index]

    def is_straight_move_blocked(self, from_row, from_col, to_row, to_col):
        if from_row == to_row:
            col = min(from_col, to_col)
            return self.vertical_walls[from_row][col]
        elif from_col == to_col:
            row = min(from_row, to_row)
            return self.horizontal_walls[row][from_col]
        return True

    def is_diagonal_move_blocked(self, from_row, from_col, to_row, to_col):
        mid_1_clear = not self.is_straight_move_blocked(from_row, from_col, from_row, to_col) and \
                      not self.is_straight_move_blocked(from_row, to_col, to_row, to_col)
        mid_2_clear = not self.is_straight_move_blocked(from_row, from_col, to_row, from_col) and \
                      not self.is_straight_move_blocked(to_row, from_col, to_row, to_col)
        return not (mid_1_clear or mid_2_clear)

    def is_move_blocked(self, from_row, from_col, to_row, to_col):
        if abs(from_row - to_row) == 1 and abs(from_col - to_col) == 1:
            return self.is_diagonal_move_blocked(from_row, from_col, to_row, to_col)
        return self.is_straight_move_blocked(from_row, from_col, to_row, to_col)

    def is_valid_move(self, to_row, to_col, from_pos):
        from_row, from_col = from_pos
        if not (0 <= to_row < self.board_size and 0 <= to_col < self.board_size):
            return False
        if any(p.position == (to_row, to_col) and p.is_alive() for p in self.players):
            return False
        if self.is_move_blocked(from_row, from_col, to_row, to_col):
            return False
        return True

    def draw_board(self):
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

    def display_status(self):
        for p in self.players:
            print(f"{p.name}: {p.health} HP at {p.position}")

    # Game with knockback mechanic when attacked
    # (Start of code omitted for brevity; see below for modifications)

    # Refactored apply_attacks function for clarity and conciseness

    # Updated apply_attacks function with knockback distance and random direction resolution

    def apply_attacks(self, attacker: Player, stayed_in_place: bool = False, knockback_distance: int = 2):
        attacker_row, attacker_col = attacker.position
        bonus_damage = ATTACK_DAMAGE + 1 if stayed_in_place else ATTACK_DAMAGE

        for defender in self.players:
            # Skip invalid targets
            if defender.id == attacker.id or not defender.is_alive():
                continue

            defender_row, defender_col = defender.position
            if abs(attacker_row - defender_row) > 1 or abs(attacker_col - defender_col) > 1:
                continue

            defender.health -= bonus_damage

            delta_row = defender_row - attacker_row
            delta_col = defender_col - attacker_col

            def is_clear_move(r, c, origin):
                return self.is_valid_move(r, c, origin)

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

    def move_current_player(self, key: str):
        player = self.get_current_player()
        if key == 's':
            self.apply_attacks(player)
            self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
            return
        delta_row, delta_col = MOVEMENT_KEYS[key]
        cur_row, cur_col = player.position
        new_row = cur_row + delta_row
        new_col = cur_col + delta_col
        if self.is_valid_move(new_row, new_col, (cur_row, cur_col)):
            player.position = (new_row, new_col)
            self.apply_attacks(player)
            self.current_turn_index = (self.current_turn_index + 1) % len(self.players)

    def is_game_over(self):
        return sum(p.is_alive() for p in self.players) <= 1

    def run(self):
        print("Use W A X D Q E Z C to move, S to stay and attack")
        while not self.is_game_over():
            self.clear_screen()
            current = self.get_current_player()
            print(f"{current.name}'s turn ({current.color.upper()})")
            self.draw_board()
            self.display_status()
            row, col = current.position
            can_move = any(
                self.is_valid_move(row + dr, col + dc, (row, col))
                for dr, dc in MOVEMENT_KEYS.values()
            )
            if not can_move:
                print(f"{current.name} has no moves. Staying and attacking...")
                time.sleep(1.5)
                self.apply_attacks(current)
                self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
                continue
            print("Move with W A X D Q E Z C or press S to stay")
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
