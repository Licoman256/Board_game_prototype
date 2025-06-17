# game_with_walls.py

import keyboard
import os
import time
import random
from dataclasses import dataclass
from typing import List, Tuple

BOARD_SIZE = 5
MAX_HP = 100
DAMAGE = 10
WALL_PROBABILITY = 0.25  # Chance of wall between any two adjacent tiles

KEY_TO_DELTA = {
    'w': (-1, 0),
    's': (1, 0),
    'a': (0, -1),
    'd': (0, 1)
}

@dataclass
class Player:
    id: int
    name: str
    color: str
    position: Tuple[int, int]
    hp: int = MAX_HP

    def is_alive(self):
        return self.hp > 0

class Game:
    def __init__(self):
        self.board_size = BOARD_SIZE
        self.players: List[Player] = [
            Player(1, "Red", 'R', (0, 0)),
            Player(2, "Blue", 'B', (BOARD_SIZE - 1, BOARD_SIZE - 1)),
        ]
        self.turn_index = 0
        self.generate_walls()

    def generate_walls(self):
        size = self.board_size
        self.v_walls = [[random.random() < WALL_PROBABILITY for _ in range(size - 1)] for _ in range(size)]
        self.h_walls = [[random.random() < WALL_PROBABILITY for _ in range(size)] for _ in range(size - 1)]

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def get_current_player(self) -> Player:
        return self.players[self.turn_index]

    def get_opponents(self, player: Player) -> List[Player]:
        return [p for p in self.players if p.id != player.id and p.is_alive()]

    def draw_board(self):
        size = self.board_size
        board = [['.' for _ in range(size)] for _ in range(size)]
        for p in self.players:
            if p.is_alive():
                r, c = p.position
                symbol = p.color.upper() if p == self.get_current_player() else p.color.lower()
                board[r][c] = symbol

        for r in range(size):
            # Top line
            top_line = ""
            for c in range(size):
                top_line += "+"
                if r > 0 and self.h_walls[r - 1][c]:
                    top_line += "---"
                else:
                    top_line += "   "
            top_line += "+"
            print(top_line)

            # Middle line with pieces and vertical walls
            middle_line = ""
            for c in range(size):
                if c > 0 and self.v_walls[r][c - 1]:
                    middle_line += "|"
                else:
                    middle_line += " "
                middle_line += f" {board[r][c]} "
            middle_line += "|"
            print(middle_line)

        # Bottom border
        bottom_line = ""
        for c in range(size):
            bottom_line += "+"
            if self.h_walls[size - 2][c]:
                bottom_line += "---"
            else:
                bottom_line += "   "
        bottom_line += "+"
        print(bottom_line)


    def display_status(self):
        for p in self.players:
            print(f"{p.name}: {p.hp} HP at {p.position}")

    def is_move_blocked(self, r1: int, c1: int, r2: int, c2: int) -> bool:
        if r1 == r2:
            # Horizontal move
            col = min(c1, c2)
            return self.v_walls[r1][col]
        elif c1 == c2:
            # Vertical move
            row = min(r1, r2)
            return self.h_walls[row][c1]
        return True  # Diagonal moves not supported here

    def is_valid_move(self, r: int, c: int, from_pos: Tuple[int, int]) -> bool:
        if not (0 <= r < self.board_size and 0 <= c < self.board_size):
            return False
        if any(p.position == (r, c) and p.is_alive() for p in self.players):
            return False
        if self.is_move_blocked(from_pos[0], from_pos[1], r, c):
            return False
        return True

    def move_player(self, direction: str):
        player = self.get_current_player()
        dr, dc = KEY_TO_DELTA[direction]
        r, c = player.position
        nr, nc = r + dr, c + dc
        if self.is_valid_move(nr, nc, (r, c)):
            player.position = (nr, nc)
            print(f"{player.name} moved to ({nr}, {nc})")
            self.apply_attacks(player)
            self.turn_index = (self.turn_index + 1) % len(self.players)
        else:
            print("Blocked!")

    def apply_attacks(self, player: Player):
        prow, pcol = player.position
        for opp in self.get_opponents(player):
            orow, ocol = opp.position
            if abs(prow - orow) <= 1 and abs(pcol - ocol) <= 1:
                opp.hp -= DAMAGE
                print(f"{player.name} hits {opp.name} for {DAMAGE} damage!")

    def is_game_over(self) -> bool:
        return len([p for p in self.players if p.is_alive()]) <= 1

    def run(self):
        print("Starting game. Use W/A/S/D to move.")
        time.sleep(2)
        while not self.is_game_over():
            self.clear_screen()
            current = self.get_current_player()
            print(f"{current.name}'s turn ({current.color.upper()})")
            self.draw_board()
            self.display_status()
            print("Move with W A S D")

            while True:
                event = keyboard.read_event()
                if event.event_type == keyboard.KEY_DOWN:
                    key = event.name.lower()
                    if key in KEY_TO_DELTA:
                        self.move_player(key)
                        break

        self.clear_screen()
        self.draw_board()
        print("Game Over!")
        for p in self.players:
            if p.is_alive():
                print(f"{p.name} wins!")

if __name__ == "__main__":
    game = Game()
    game.run()
