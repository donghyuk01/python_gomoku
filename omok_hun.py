import tkinter as tk
from tkinter import messagebox

board_size = 15
cell_size = 40
stone_size = 18


class Omok_game:
    def __init__(self, root):
        self.root = root
        self.root.title("오목 게임")
        self.canvas = tk.Canvas(
            root,
            width=board_size * cell_size,
            height=board_size * cell_size,
            bg="#E0BB74",
        )
        self.canvas.pack()
        self.board = [["." for _ in range(board_size)] for _ in range(board_size)]
        self.turn = "black"
        self.draw_board()
        self.canvas.bind("<Button-1>", self.place_stone)

    def draw_board(self):
        for i in range(board_size):
            self.canvas.create_line(
                cell_size // 2,
                cell_size // 2 + i * cell_size,
                cell_size // 2 + (board_size - 1) * cell_size,
                cell_size // 2 + i * cell_size,
            )
            self.canvas.create_line(
                cell_size // 2 + i * cell_size,
                cell_size // 2,
                cell_size // 2 + i * cell_size,
                cell_size // 2 + (board_size - 1) * cell_size,
            )

    def place_stone(self, event):
        x = round((event.x - cell_size // 2) / cell_size)
        y = round((event.y - cell_size // 2) / cell_size)
        if 0 <= x < board_size and 0 <= y < board_size and self.board[y][x] == ".":
            if self.turn == "black":
                if (
                    self.is_forbidden_long(x, y)
                    or self.is_forbidden_44(x, y)
                    or self.is_forbidden_33(x, y)
                ):
                    messagebox.showwarning("금수", "금수 위치에는 둘 수 없습니다!")
                    return
            self.board[y][x] = self.turn
            color = "black" if self.turn == "black" else "white"
            self.canvas.create_oval(
                cell_size // 2 + x * cell_size - stone_size,
                cell_size // 2 + y * cell_size - stone_size,
                cell_size // 2 + x * cell_size + stone_size,
                cell_size // 2 + y * cell_size + stone_size,
                fill=color,
            )

            if self.check_win(x, y):
                self.canvas.delete("forbidden")
                self.canvas.unbind("<Button-1>")
                messagebox.showwarning("승리", f"{self.turn.upper()} 승리!")
            else:
                self.turn = "white" if self.turn == "black" else "black"
                self.draw_forbidden_marks()

    def check_win(self, x, y):
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dx, dy in directions:
            count = 1
            for direction in [1, -1]:
                nx, ny = x + dx * direction, y + dy * direction
                while (
                    0 <= nx < board_size
                    and 0 <= ny < board_size
                    and self.board[ny][nx] == self.turn
                ):
                    count += 1
                    nx += dx * direction
                    ny += dy * direction
            if count == 5:
                return True
        return False

    def is_forbidden_33(self, x, y, player="black"):

        current_state = self.board[y][x]
        self.board[y][x] = player

        open_three_count = 0
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

        for dx, dy in directions:
            if self.is_open_three(x, y, dx, dy, "black"):
                open_three_count += 1

        self.board[y][x] = current_state
        return open_three_count >= 2

    def is_open_three(self, x, y, dx, dy, player):

        line = []
        for i in range(-4, 5):
            nx, ny = x + i * dx, y + i * dy
            if 0 <= nx < board_size and 0 <= ny < board_size:
                line.append(self.board[ny][nx])
            else:
                line.append("X")

        line_str = "".join(
            ["1" if s == player else ("0" if s == "." else "X") for s in line]
        )

        open_3_patterns = ["01110", "011010", "010110"]

        for p in open_3_patterns:
            if p in line_str:
                return True
        return False

    def is_forbidden_long(self, x, y, player="black"):
        current_state = self.board[y][x]
        self.board[y][x] = player
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        is_long = False
        for dx, dy in directions:
            count = 1
            for d in [1, -1]:
                nx, ny = x + dx * d, y + dy * d
                while (
                    0 <= nx < board_size
                    and 0 <= ny < board_size
                    and self.board[ny][nx] == player
                ):
                    count += 1
                    nx += dx * d
                    ny += dy * d
            if count >= 6:
                is_long = True
                break
        self.board[y][x] = current_state
        return is_long

    def is_forbidden_44(self, x, y, player="black"):
        current_state = self.board[y][x]
        self.board[y][x] = player

        four_count = 0
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

        for dx, dy in directions:

            if self.is_four_pattern(x, y, dx, dy, player):
                four_count += 1

        self.board[y][x] = current_state
        return four_count >= 2

    def is_four_pattern(self, x, y, dx, dy, player):

        line = []
        for i in range(-4, 5):
            nx, ny = x + i * dx, y + i * dy
            if 0 <= nx < board_size and 0 <= ny < board_size:
                line.append(self.board[ny][nx])
            else:
                line.append("X")
        line_str = "".join(
            ["1" if s == player else ("0" if s == "." else "X") for s in line]
        )

        four_patterns = ["01111", "10111", "11011", "11101", "11110"]
        for p in four_patterns:
            if p in line_str:
                return True
        return False

    def draw_forbidden_marks(self):
        self.canvas.delete("forbidden")

        if self.turn == "black":
            for y in range(board_size):
                for x in range(board_size):
                    if self.board[y][x] == ".":

                        if (
                            self.is_forbidden_long(x, y)
                            or self.is_forbidden_44(x, y)
                            or self.is_forbidden_33(x, y)
                        ):

                            px = cell_size // 2 + x * cell_size
                            py = cell_size // 2 + y * cell_size
                            self.canvas.create_line(
                                px - 8,
                                py - 8,
                                px + 8,
                                py + 8,
                                fill="red",
                                width=2,
                                tags="forbidden",
                            )
                            self.canvas.create_line(
                                px + 8,
                                py - 8,
                                px - 8,
                                py + 8,
                                fill="red",
                                width=2,
                                tags="forbidden",
                            )


if __name__ == "__main__":
    root = tk.Tk()
    game = Omok_game(root)
    root.mainloop()
