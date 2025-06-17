# Game with diagonal movement and readable wall logic, including comments for clarity

import keyboard
import os
import time
import random
from dataclasses import dataclass
from typing import List, Tuple

# Constants for game configuration
BOARD_SIZE = 5
MAX_HEALTH = 5
ATTACK_DAMAGE = 1

# Mapping movement keys to (row_offset, col_offset)
MOVEMENT_KEYS = {
    'w': (-1, 0),   # up
    's': (1, 0),    # down
    'a': (0, -1),   # left
    'd': (0, 1),    # right
    'q': (-1, -1),  # up-left
    'e': (-1, 1),   # up-right
    'z': (1, -1),   # down-left
    'c': (1, 1)     # down-right
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
        """Generate a fully connected maze and randomly break additional walls to open it up."""
        size = self.board_size

        # Initialize walls: all are present at start
        self.vertical_walls = [[True for _ in range(size - 1)] for _ in range(size)]
        self.horizontal_walls = [[True for _ in range(size)] for _ in range(size - 1)]

        visited = [[False for _ in range(size)] for _ in range(size)]

        def is_within_bounds(row, col):
            return 0 <= row < size and 0 <= col < size

        def generate_maze(row, col):
            """Recursive DFS to carve out a connected maze."""
            visited[row][col] = True
            directions = [
                ("up", -1, 0),
                ("down", 1, 0),
                ("left", 0, -1),
                ("right", 0, 1)
            ]
            random.shuffle(directions)

            for direction, row_offset, col_offset in directions:
                next_row = row + row_offset
                next_col = col + col_offset

                if is_within_bounds(next_row, next_col) and not visited[next_row][next_col]:
                    # Remove wall between current and next cell
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

        # Randomly break additional walls to make the board more open
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
        """Check for walls blocking a straight (non-diagonal) move."""
        if from_row == to_row:
            column = min(from_col, to_col)
            return self.vertical_walls[from_row][column]
        elif from_col == to_col:
            row = min(from_row, to_row)
            return self.horizontal_walls[row][from_col]
        return True

    def is_diagonal_move_blocked(self, from_row, from_col, to_row, to_col):
        """Check both potential paths for diagonal movement and block if both are blocked."""
        mid_row_1 = from_row
        mid_col_1 = to_col
        mid_row_2 = to_row
        mid_col_2 = from_col

        path_1_clear = not self.is_straight_move_blocked(from_row, from_col, mid_row_1, mid_col_1) and \
                       not self.is_straight_move_blocked(mid_row_1, mid_col_1, to_row, to_col)
        path_2_clear = not self.is_straight_move_blocked(from_row, from_col, mid_row_2, mid_col_2) and \
                       not self.is_straight_move_blocked(mid_row_2, mid_col_2, to_row, to_col)

        return not (path_1_clear or path_2_clear)

    def is_move_blocked(self, from_row, from_col, to_row, to_col):
        if abs(from_row - to_row) == 1 and abs(from_col - to_col) == 1:
            return self.is_diagonal_move_blocked(from_row, from_col, to_row, to_col)
        return self.is_straight_move_blocked(from_row, from_col, to_row, to_col)

    def is_valid_move(self, target_row, target_col, from_position):
        from_row, from_col = from_position
        if not (0 <= target_row < self.board_size and 0 <= target_col < self.board_size):
            return False
        if any(player.position == (target_row, target_col) and player.is_alive() for player in self.players):
            return False
        if self.is_move_blocked(from_row, from_col, target_row, target_col):
            return False
        return True

    def draw_board(self):
        """Draw the game board with players and wall indicators."""
        size = self.board_size
        board = [['.' for _ in range(size)] for _ in range(size)]
        for player in self.players:
            if player.is_alive():
                row, col = player.position
                symbol = player.color.upper() if player == self.get_current_player() else player.color.lower()
                board[row][col] = symbol

        for row in range(size):
            top_line = ""
            for col in range(size):
                top_line += "+"
                if row > 0 and self.horizontal_walls[row - 1][col]:
                    top_line += "---"
                else:
                    top_line += "   "
            top_line += "+"
            print(top_line)

            middle_line = ""
            for col in range(size):
                if col > 0 and self.vertical_walls[row][col - 1]:
                    middle_line += "|"
                else:
                    middle_line += " "
                middle_line += f" {board[row][col]} "
            middle_line += "|"
            print(middle_line)

        # Draw bottom line of the board
        bottom_line = ""
        for col in range(size):
            bottom_line += "+"
            if self.horizontal_walls[size - 2][col]:
                bottom_line += "---"
            else:
                bottom_line += "   "
        bottom_line += "+"
        print(bottom_line)

    def display_status(self):
        for player in self.players:
            print(f"{player.name}: {player.health} HP at {player.position}")

    def move_current_player(self, key: str):
        """Move the current player in the direction of the key pressed."""
        player = self.get_current_player()
        delta_row, delta_col = MOVEMENT_KEYS[key]
        current_row, current_col = player.position
        target_row = current_row + delta_row
        target_col = current_col + delta_col
        if self.is_valid_move(target_row, target_col, (current_row, current_col)):
            player.position = (target_row, target_col)
            self.apply_attacks(player)
            self.current_turn_index = (self.current_turn_index + 1) % len(self.players)

    def apply_attacks(self, attacker: Player):
        """Apply damage to adjacent enemy players."""
        attacker_row, attacker_col = attacker.position
        for defender in self.players:
            if defender.id != attacker.id and defender.is_alive():
                defender_row, defender_col = defender.position
                if abs(attacker_row - defender_row) <= 1 and abs(attacker_col - defender_col) <= 1:
                    defender.health -= ATTACK_DAMAGE

    def is_game_over(self):
        return sum(1 for player in self.players if player.is_alive()) <= 1

    def run(self):
        print("Game started. Use W A S D for straight moves, Q Z C E for diagonal.")
        while not self.is_game_over():
            self.clear_screen()
            current_player = self.get_current_player()
            print(f"{current_player.name}'s turn ({current_player.color.upper()})")
            self.draw_board()
            self.display_status()

            current_row, current_col = current_player.position
            has_moves = any(
                self.is_valid_move(current_row + delta_row, current_col + delta_col, (current_row, current_col))
                for delta_row, delta_col in MOVEMENT_KEYS.values()
            )

            if not has_moves:
                print(f"{current_player.name} has no moves. Skipping turn...")
                time.sleep(1.5)
                self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
                continue

            print("Choose a direction: W A S D Q E Z C")
            while True:
                event = keyboard.read_event()
                if event.event_type == keyboard.KEY_DOWN:
                    key = event.name.lower()
                    if key in MOVEMENT_KEYS:
                        self.move_current_player(key)
                        break

        print("Game Over!")
        for player in self.players:
            if player.is_alive():
                print(f"{player.name} wins!")

if __name__ == "__main__":
    game = Game()
    game.run()