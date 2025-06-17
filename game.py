import keyboard
import os
import time
import random
from dataclasses import dataclass
from typing import List, Tuple

# Constants for the board and game mechanics
BOARD_SIZE = 7
MAX_HEALTH = 5
DAMAGE_AMOUNT = 1

# Key mappings to direction vectors
KEY_TO_DIRECTION = {
    'w': (-1, 0),  # Up
    's': (1, 0),   # Down
    'a': (0, -1),  # Left
    'd': (0, 1)    # Right
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
        self.turn_index = 0
        self.generate_connected_maze_with_extra_walls()

    def generate_connected_maze_with_extra_walls(self):
        size = self.board_size
        # Initialize all walls as present
        self.vertical_walls = [[True for _ in range(size - 1)] for _ in range(size)]
        self.horizontal_walls = [[True for _ in range(size)] for _ in range(size - 1)]

        visited = [[False for _ in range(size)] for _ in range(size)]

        def is_within_bounds(row, col):
            return 0 <= row < size and 0 <= col < size

        def depth_first_search(row, col):
            visited[row][col] = True
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            random.shuffle(directions)

            for row_offset, col_offset in directions:
                neighbor_row, neighbor_col = row + row_offset, col + col_offset
                if is_within_bounds(neighbor_row, neighbor_col) and not visited[neighbor_row][neighbor_col]:
                    # Remove the wall between the current cell and the neighbor
                    if row_offset == 0 and col_offset == 1:
                        self.vertical_walls[row][col] = False  # Remove right wall
                    elif row_offset == 1 and col_offset == 0:
                        self.horizontal_walls[row][col] = False  # Remove bottom wall
                    elif row_offset == 0 and col_offset == -1:
                        self.vertical_walls[row][col - 1] = False  # Remove left wall
                    elif row_offset == -1 and col_offset == 0:
                        self.horizontal_walls[row - 1][col] = False  # Remove top wall
                    depth_first_search(neighbor_row, neighbor_col)

        # Start DFS from the top-left corner to ensure all spaces are connected
        depth_first_search(0, 0)

        # Randomly remove extra walls to open the board up more
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
        return self.players[self.turn_index]

    def get_opposing_players(self, current_player: Player) -> List[Player]:
        return [player for player in self.players if player.id != current_player.id and player.is_alive()]

    def draw_board(self):
        size = self.board_size
        board = [['.' for _ in range(size)] for _ in range(size)]

        for player in self.players:
            if player.is_alive():
                row, col = player.position
                symbol = player.color.upper() if player == self.get_current_player() else player.color.lower()
                board[row][col] = symbol

        for row in range(size):
            # Draw top wall
            top_line = ""
            for col in range(size):
                top_line += "+"
                if row > 0 and self.horizontal_walls[row - 1][col]:
                    top_line += "---"
                else:
                    top_line += "   "
            top_line += "+"
            print(top_line)

            # Draw middle row with pieces and vertical walls
            middle_line = ""
            for col in range(size):
                if col > 0 and self.vertical_walls[row][col - 1]:
                    middle_line += "|"
                else:
                    middle_line += " "
                middle_line += f" {board[row][col]} "
            middle_line += "|"
            print(middle_line)

        # Draw bottom border
        bottom_line = ""
        for col in range(size):
            bottom_line += "+"
            if self.horizontal_walls[size - 2][col]:
                bottom_line += "---"
            else:
                bottom_line += "   "
        bottom_line += "+"
        print(bottom_line)

    def display_health_status(self):
        for player in self.players:
            print(f"{player.name}: {player.health} HP at {player.position}")

    def is_movement_blocked(self, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        if from_row == to_row:
            col = min(from_col, to_col)
            return self.vertical_walls[from_row][col]
        elif from_col == to_col:
            row = min(from_row, to_row)
            return self.horizontal_walls[row][from_col]
        return True  # Diagonal movement is invalid

    def is_valid_movement(self, destination_row: int, destination_col: int, origin: Tuple[int, int]) -> bool:
        if not (0 <= destination_row < self.board_size and 0 <= destination_col < self.board_size):
            return False
        if any(player.position == (destination_row, destination_col) and player.is_alive() for player in self.players):
            return False
        if self.is_movement_blocked(origin[0], origin[1], destination_row, destination_col):
            return False
        return True

    def move_player(self, direction_key: str):
        current_player = self.get_current_player()
        row_offset, col_offset = KEY_TO_DIRECTION[direction_key]
        current_row, current_col = current_player.position
        new_row, new_col = current_row + row_offset, current_col + col_offset

        if self.is_valid_movement(new_row, new_col, (current_row, current_col)):
            current_player.position = (new_row, new_col)
            print(f"{current_player.name} moved to ({new_row}, {new_col})")
            self.apply_attack_logic(current_player)
            self.turn_index = (self.turn_index + 1) % len(self.players)
        else:
            print("Move blocked by wall or invalid destination!")

    def apply_attack_logic(self, attacker: Player):
        attacker_row, attacker_col = attacker.position
        for opponent in self.get_opposing_players(attacker):
            opponent_row, opponent_col = opponent.position
            if abs(attacker_row - opponent_row) <= 1 and abs(attacker_col - opponent_col) <= 1:
                opponent.health -= DAMAGE_AMOUNT
                print(f"{attacker.name} attacks {opponent.name} for {DAMAGE_AMOUNT} damage!")

    def is_game_finished(self) -> bool:
        return len([player for player in self.players if player.is_alive()]) <= 1

    def run(self):
        print("Game start! Use W/A/S/D to move.")
        while not self.is_game_finished():
            self.clear_screen()
            current_player = self.get_current_player()
            print(f"{current_player.name}'s turn ({current_player.color.upper()})")
            self.draw_board()
            self.display_health_status()

            # Check for available movement directions
            current_row, current_col = current_player.position
            has_available_move = False
            for key, (row_offset, col_offset) in KEY_TO_DIRECTION.items():
                new_row = current_row + row_offset
                new_col = current_col + col_offset
                if self.is_valid_movement(new_row, new_col, (current_row, current_col)):
                    has_available_move = True
                    break

            if not has_available_move:
                print(f"{current_player.name} is trapped! Skipping turn...")
                time.sleep(2)
                self.turn_index = (self.turn_index + 1) % len(self.players)
                continue

            print("Use W A S D to move")
            while True:
                key_event = keyboard.read_event()
                if key_event.event_type == keyboard.KEY_DOWN:
                    key_pressed = key_event.name.lower()
                    if key_pressed in KEY_TO_DIRECTION:
                        self.move_player(key_pressed)
                        break

if __name__ == "__main__":
    game = Game()
    game.run()
