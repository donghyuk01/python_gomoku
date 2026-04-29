import tkinter as tk
from tkinter import messagebox

BOARD_SIZE = 15
CELL_SIZE = 40
STONE_SIZE = 18

class OmokGame:
    def __init__(self, root):
        self.root = root
        self.root.title("오목 게임")
        self.canvas = tk.Canvas(root, width=BOARD_SIZE*CELL_SIZE, height=BOARD_SIZE*CELL_SIZE, bg="#F5DEB3")
        self.canvas.pack()
        self.board = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.turn = "black"
        self.draw_board()
        self.canvas.bind("<Button-1>", self.place_stone)

    def draw_board(self):
        for i in range(BOARD_SIZE):
            self.canvas.create_line(CELL_SIZE//2, CELL_SIZE//2 + i*CELL_SIZE,
                                    CELL_SIZE//2 + (BOARD_SIZE-1)*CELL_SIZE, CELL_SIZE//2 + i*CELL_SIZE)
            self.canvas.create_line(CELL_SIZE//2 + i*CELL_SIZE, CELL_SIZE//2,
                                    CELL_SIZE//2 + i*CELL_SIZE, CELL_SIZE//2 + (BOARD_SIZE-1)*CELL_SIZE)

    def place_stone(self, event):
        x = round((event.x - CELL_SIZE//2) / CELL_SIZE)
        y = round((event.y - CELL_SIZE//2) / CELL_SIZE)
        if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and self.board[y][x] == ".":
            self.board[y][x] = self.turn
            color = "black" if self.turn == "black" else "white"
            self.canvas.create_oval(
                CELL_SIZE//2 + x*CELL_SIZE - STONE_SIZE,
                CELL_SIZE//2 + y*CELL_SIZE - STONE_SIZE,
                CELL_SIZE//2 + x*CELL_SIZE + STONE_SIZE,
                CELL_SIZE//2 + y*CELL_SIZE + STONE_SIZE,
                fill=color
            )
            if self.check_win(x, y):
                self.canvas.unbind("<Button-1>")
                # self.root.title(f"{self.turn.upper()} 승리!")
                messagebox.showwarning("승리",f"{self.turn.upper()} 승리!")
            else:
                self.turn = "white" if self.turn == "black" else "black"

    def check_win(self, x, y):
        directions = [(1,0), (0,1), (1,1), (1,-1)]
        for dx, dy in directions:
            count = 1
            for dir in [1, -1]:
                nx, ny = x + dx*dir, y + dy*dir
                while 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and self.board[ny][nx] == self.turn:
                    count += 1
                    nx += dx*dir
                    ny += dy*dir
            if count >= 5:
                return True
        return False

if __name__ == "__main__":
    root = tk.Tk()
    game = OmokGame(root)
    root.mainloop()
