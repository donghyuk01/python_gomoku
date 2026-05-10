# 출처 : https://github.com/BobscHuang/Gomoku/blob/master/Gomoku/Gomoku.py
from tkinter import *
from time import *
import sys

myInterface = Tk()
myInterface.title("Gomoku (1-based Coordinate)")
s = Canvas(myInterface, width=800, height=800, background= "#b69b4c")
s.pack()

# Board Size 설정 (15x15 바둑판 기준)
Board_Size_Actual = 15 
Frame_Gap = 35
width = 800
height = 800

forbidden_marks = []  # 금수 표시 저장 리스트

def draw_forbidden_marks():
    global forbidden_marks
    if not s.winfo_exists(): return

    try:
        for mark in forbidden_marks:
            s.delete(mark)
        forbidden_marks = []
        
        if Turn == "black":
            for y in range(1, Board_Size_Actual + 1):
                for x in range(1, Board_Size_Actual + 1):
                    if board[y-1][x-1] == 0 and is_forbidden(x, y, board):
                        cx = Board_X1 + Board_GapX * (x - 1)
                        cy = Board_Y1 + Board_GapY * (y - 1)
                        r = Chess_Radius * 0.4
                        m1 = s.create_line(cx-r, cy-r, cx+r, cy+r, fill="red", width=2)
                        m2 = s.create_line(cx+r, cy-r, cx-r, cy+r, fill="red", width=2)
                        forbidden_marks.append(m1)
                        forbidden_marks.append(m2)
    except TclError: pass

def count_in_direction(x, y, dx, dy, board, piece):
    count = 0
    nx, ny = x + dx, y + dy
    while 1 <= nx <= Board_Size_Actual and 1 <= ny <= Board_Size_Actual and board[ny-1][nx-1] == piece:
        count += 1
        nx += dx
        ny += dy
    return count

def check_overline(x, y, board):
    directions = [(1,0),(0,1),(1,1),(1,-1)]
    for dx, dy in directions:
        count = 1 + count_in_direction(x, y, dx, dy, board, Black_Piece) + count_in_direction(x, y, -dx, -dy, board, Black_Piece)
        if count >= 6: return True
    return False

def count_four(x, y, board):
    directions = [(1,0),(0,1),(1,1),(1,-1)]
    fours = 0
    for dx, dy in directions:
        count = 1 + count_in_direction(x, y, dx, dy, board, Black_Piece) + count_in_direction(x, y, -dx, -dy, board, Black_Piece)
        if count == 4: fours += 1
    return fours

# ──────────────────────────────────────────────
# [수정] count_open3: 보드 전체 라인 스캔 방식
# 핵심 원칙:
#   - 같은 방향(라인)에서는 open3 최대 1개만 카운트
#   - 방향별로 라인을 한 번만 추출 → 슬라이딩 윈도우로 패턴 매칭
#   - 돌이 겹치는 패턴은 같은 라인 open3로 간주 (중복 카운트 방지)
# ──────────────────────────────────────────────
def count_open3_total(board):
    """
    보드 전체를 방향별로 스캔해서 열린3 패턴 수를 반환.
    같은 방향의 라인에서는 최대 1개만 카운트하여 중복 오판 방지.

    열린3 패턴 (E=빈칸, P=흑돌):
      E P P P E
      E P P E P E
      E P E P P E
    """
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    P = Black_Piece
    E = 0

    open3_patterns = [
        [E, P, P, P, E],
        [E, P, P, E, P, E],
        [E, P, E, P, P, E],
    ]

    open3_count = 0

    for dx, dy in directions:
        visited_line_starts = set()

        for sy in range(1, Board_Size_Actual + 1):
            for sx in range(1, Board_Size_Actual + 1):

                # 이 셀이 속한 라인의 시작점(역방향 끝까지)을 구해 중복 라인 방지
                lx, ly = sx, sy
                while 1 <= lx - dx <= Board_Size_Actual and 1 <= ly - dy <= Board_Size_Actual:
                    lx -= dx
                    ly -= dy
                line_key = (lx, ly, dx, dy)
                if line_key in visited_line_starts:
                    continue
                visited_line_starts.add(line_key)

                # 라인 전체 셀 값 추출
                line = []
                nx, ny = lx, ly
                while 1 <= nx <= Board_Size_Actual and 1 <= ny <= Board_Size_Actual:
                    line.append(board[ny-1][nx-1])
                    nx += dx
                    ny += dy

                # 슬라이딩 윈도우로 패턴 탐색
                # 같은 라인에서 돌이 겹치는 패턴은 1개로 간주
                used_positions = set()
                for pat in open3_patterns:
                    if open3_count > 1:
                        break  # 이미 2개 이상이면 조기 종료 가능
                    wlen = len(pat)
                    for start in range(len(line) - wlen + 1):
                        window = line[start:start + wlen]
                        if window == pat:
                            stone_positions = frozenset(
                                start + i for i in range(wlen) if pat[i] == P
                            )
                            # 이미 카운트된 돌과 겹치지 않으면 새로운 open3
                            if not stone_positions & used_positions:
                                used_positions |= stone_positions
                                open3_count += 1
                                break  # 같은 라인에서는 1개만 카운트

    return open3_count


def is_forbidden(x, y, board):
    """
    (x, y)에 흑돌을 임시로 놓은 뒤 보드 전체를 스캔하여 금수 여부 판단.
    - 기존: (x,y) 기준으로만 탐색 → 다른 위치의 open3 놓침
    - 수정: 보드 전체 open3 카운트 → 모든 패턴 정확히 감지
    """
    if not (1 <= x <= Board_Size_Actual and 1 <= y <= Board_Size_Actual):
        return False
    if board[y-1][x-1] != 0:
        return False

    board[y-1][x-1] = Black_Piece

    try:
        # 5목이 되는 자리는 금수 아님 (승리 우선)
        if winCheck(Black_Piece, "Black", board) == "Black":
            return False

        overline = check_overline(x, y, board)
        f4 = count_four(x, y, board)
        o3 = count_open3_total(board)  # ← 보드 전체 스캔

        if overline or o3 >= 2 or f4 >= 2:
            return True
    finally:
        board[y-1][x-1] = 0

    return False

# ──────────────────────────────────────────────

def create_circle(x, y, radius, fill = "", outline = "black", width = 1):
    s.create_oval(x - radius, y - radius, x + radius, y + radius, fill = fill, outline = outline, width = width)

def MouseClick(event):
    global Click_Cord
    X_click, Y_click = event.x, event.y
    Click_Cord = Piece_Location(X_click, Y_click)

s.bind("<Button-1>", MouseClick)
Click_Cord = [None, None]

def Piece_Location(X_click, Y_click):    
    X, Y = None, None
    for i in range(len(Actual_CordX1)):
        if Actual_CordX1[i] < X_click < Actual_CordX2[i]:
            X = Game_CordX[i]
        if Actual_CordY1[i] < Y_click < Actual_CordY2[i]:
            Y = Game_CordY[i]
    return X, Y

def Location_Validation():
    if X == None or Y == None: return False
    return board[Y-1][X-1] == 0

def Score_Board():
    if Winner == None:
        return s.create_text(width / 2, height - Frame_Gap + 15, text = "Turn = " + Turn, font = "Helvetica 25 bold", fill = Turn)
    else:
        s.create_rectangle(width*0.1, height/2 - 60, width*0.9, height/2 + 60, fill = "white", outline = "black", width = 3)
        text_val = "Draw!" if Draw == 1 else Winner.upper() + " WINS!"
        s.create_text(width / 2, height / 2, text = text_val, font = "Helvetica 60 bold", fill = "black")

def drawCheck(board):
    for row in board:
        if 0 in row: return None
    return 1

def winCheck(Piece_Number, Piece_Colour, board):
    if rowCheck(Piece_Number, board) or \
       rowCheck(Piece_Number, transpose(board)) or \
       rowCheck(Piece_Number, transposeDiagonalInc(board)) or \
       rowCheck(Piece_Number, transposeDiagonalDec(board)):
        return Piece_Colour
    return None

def rowCheck(Piece_Number, board):
    for row in board:
        count = 0
        for val in row:
            if val == Piece_Number:
                count += 1
                if count == 5: return True
            else: count = 0
    return False

def getCol(loa, colNum): return [row[colNum] for row in loa]
def transpose(loa): return [getCol(loa, i) for i in range(len(loa[0]))]

def transposeDiagonalInc(loa):
    size = len(loa)
    res = []
    for d in range(2 * size - 1):
        line = []
        for y in range(size):
            x = d - y
            if 0 <= x < size: line.append(loa[y][x])
        if line: res.append(line)
    return res

def transposeDiagonalDec(loa):
    size = len(loa)
    res = []
    for d in range(-(size - 1), size):
        line = []
        for y in range(size):
            x = y - d
            if 0 <= x < size: line.append(loa[y][x])
        if line: res.append(line)
    return res

def Exit():
    global Winner
    Winner = "Exit"
    myInterface.destroy()

myInterface.protocol("WM_DELETE_WINDOW", Exit)

# 초기 설정 값 계산
Board_X1 = width / 10
Board_Y1 = height / 10
Board_GapX = (width - Board_X1 * 2) / (Board_Size_Actual - 1)
Board_GapY = (height - Board_Y1 * 2) / (Board_Size_Actual - 1)
Chess_Radius = (Board_GapX * 0.9) / 2

Turn_Num, Turn, Winner, Draw = 1, "black", None, None
Black_Piece, White_Piece = 2, 1
board = [[0] * Board_Size_Actual for _ in range(Board_Size_Actual)]

Game_CordX, Game_CordY = [], []
Actual_CordX1, Actual_CordY1, Actual_CordX2, Actual_CordY2 = [], [], [], []

for z in range(1, Board_Size_Actual + 1): 
    for i in range(1, Board_Size_Actual + 1):
        Game_CordX.append(z)
        Game_CordY.append(i)
        Actual_CordX1.append((z - 1) * Board_GapX + Board_X1 - Chess_Radius)
        Actual_CordY1.append((i - 1) * Board_GapY + Board_Y1 - Chess_Radius)
        Actual_CordX2.append((z - 1) * Board_GapX + Board_X1 + Chess_Radius)
        Actual_CordY2.append((i - 1) * Board_GapY + Board_Y1 + Chess_Radius)

# UI 그리기
B = Button(myInterface, text="EXIT", font="Helvetica 10 bold", command=Exit, bg="gray")
B.place(x=width*0.25, y=height-40, height=30, width=80)

s.create_rectangle(Board_X1-Frame_Gap, Board_Y1-Frame_Gap, 
                   Board_X1+(Board_Size_Actual-1)*Board_GapX+Frame_Gap, 
                   Board_Y1+(Board_Size_Actual-1)*Board_GapY+Frame_Gap, width=3)

for f in range(Board_Size_Actual):
    s.create_line(Board_X1, Board_Y1 + f * Board_GapY, Board_X1 + (Board_Size_Actual-1) * Board_GapX, Board_Y1 + f * Board_GapY)
    s.create_line(Board_X1 + f * Board_GapX, Board_Y1, Board_X1 + f * Board_GapX, Board_Y1 + (Board_Size_Actual-1) * Board_GapY)
    s.create_text(Board_X1 - 25, Board_Y1 + f * Board_GapY, text=f+1, font="Helvetica 10")
    s.create_text(Board_X1 + f * Board_GapX, Board_Y1 - 25, text=f+1, font="Helvetica 10")

Turn_Text = Score_Board()

# 메인 루프
while Winner is None and Draw is None:
    s.update()
    X, Y = Click_Cord
    if Location_Validation():
        if Turn == "black" and is_forbidden(X, Y, board):
            Click_Cord = [None, None]
            continue
            
        s.delete(Turn_Text)
        create_circle(Board_X1 + Board_GapX * (X - 1), Board_Y1 + Board_GapY * (Y - 1), radius=Chess_Radius, fill=Turn)
        
        board[Y-1][X-1] = Black_Piece if Turn == "black" else White_Piece
        
        if Turn == "black":
            Turn, Colour_Check, Win_Check = "white", Black_Piece, "Black"
        else:
            Turn, Colour_Check, Win_Check = "black", White_Piece, "White"

        Winner = winCheck(Colour_Check, Win_Check, board)
        Draw = drawCheck(board)
        Turn_Text = Score_Board()
        draw_forbidden_marks()
        Click_Cord = [None, None]

if Winner != "Exit":
    s.delete(Turn_Text)
    Score_Board()
    myInterface.mainloop()
"""
수정사항
백시작을 흑시작으로 수정해둠+턴로직 수정
score_board 수정
금수지정추가
무승부 추가
기존 검사 로직 오류수정(보드판의 검사할때 -3을써서 인덱스 오류 존재함)
"""

    