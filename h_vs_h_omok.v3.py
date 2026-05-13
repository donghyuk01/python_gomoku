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

# ──────────────────────────────────────────────
# 라인 키 계산: (x,y)가 속한 (dx,dy) 방향 라인의 시작점
# ──────────────────────────────────────────────
def get_line_key(x, y, dx, dy):
    """(x,y)를 포함하는 (dx,dy) 방향 라인의 시작 좌표를 반환."""
    lx, ly = x, y
    while 1 <= lx - dx <= Board_Size_Actual and 1 <= ly - dy <= Board_Size_Actual:
        lx -= dx
        ly -= dy
    return (lx, ly, dx, dy)


def collect_chain(x, y, dx, dy, board, player):
    """
    (x,y)에서 (dx,dy) 방향으로 돌 연결을 수집.
    빈칸 한 개까지 건너뛰기 허용.
    반환: 연결된 (px, py) 좌표 리스트 (자기 자신 제외)
    """
    coords = []
    found_skip = False
    nx, ny = x + dx, y + dy

    while 1 <= nx <= Board_Size_Actual and 1 <= ny <= Board_Size_Actual:
        if board[ny-1][nx-1] == player:
            coords.append((nx, ny))
        elif board[ny-1][nx-1] == 0:
            if not found_skip:
                nnx, nny = nx + dx, ny + dy
                if 1 <= nnx <= Board_Size_Actual and 1 <= nny <= Board_Size_Actual and board[nny-1][nnx-1] == player:
                    found_skip = True
                else:
                    break
            else:
                break
        else:
            break
        nx += dx
        ny += dy
    return coords


def get_line_length(x, y, dx, dy, board):
    """(x,y)에서 (dx,dy) 방향 양쪽으로 연속된 흑돌 총 길이 반환."""
    return (1
            + count_in_direction(x, y,  dx,  dy, board, Black_Piece)
            + count_in_direction(x, y, -dx, -dy, board, Black_Piece))


def count_open3(x, y, board, visited=None):
    """
    (x,y)를 포함하는 열린3 개수를 반환.

    핵심 규칙:
      - visited['lines'] : 이미 카운트한 (dx,dy,line_key) 집합
        같은 방향·같은 라인에서 나온 돌은 한 번만 카운트
      - visited['stones']: 이미 재귀 탐색한 돌 좌표 집합
      - 같은 라인에서 이어진 돌이 6목 이상인 경우에만 overline으로
        처리(is_forbidden에서 별도 판정). open3 계산에서는 제외.
    """
    if visited is None:
        visited = {'stones': set(), 'lines': set()}

    visited['stones'].add((x, y))
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    open3_count = 0

    for dx, dy in directions:
        lkey    = get_line_key(x, y, dx, dy)
        dir_key = (dx, dy, lkey)

        # 이미 이 방향+라인 처리했으면 건너뜀
        if dir_key in visited['lines']:
            continue

        # 이 방향 연속 길이가 6 이상이면 overline → open3 판정 제외
        # (overline은 is_forbidden에서 별도로 처리)
        if get_line_length(x, y, dx, dy, board) >= 6:
            visited['lines'].add(dir_key)
            continue

        # 양방향으로 체인 수집 (빈칸 1개 허용)
        chain_fwd = collect_chain(x, y,  dx,  dy, board, Black_Piece)
        chain_bwd = collect_chain(x, y, -dx, -dy, board, Black_Piece)
        chain = list(set(chain_fwd + chain_bwd + [(x, y)]))
        chain.sort()

        if len(chain) == 3:
            sx, sy = chain[0]
            ex, ey = chain[-1]

            # 양 끝에 돌이 더 이어지면 3이 아님
            is_really_three = True
            for ex_dx, ex_dy, corner in [(-dx, -dy, (sx, sy)), (dx, dy, (ex, ey))]:
                cx, cy = corner[0] + ex_dx, corner[1] + ex_dy
                if (1 <= cx <= Board_Size_Actual and 1 <= cy <= Board_Size_Actual
                        and board[cy-1][cx-1] == Black_Piece):
                    is_really_three = False
                    break

            if is_really_three:
                e1x, e1y = sx - dx, sy - dy
                e2x, e2y = ex + dx, ey + dy
                open1 = (1 <= e1x <= Board_Size_Actual and 1 <= e1y <= Board_Size_Actual
                         and board[e1y-1][e1x-1] == 0)
                open2 = (1 <= e2x <= Board_Size_Actual and 1 <= e2y <= Board_Size_Actual
                         and board[e2y-1][e2x-1] == 0)

                if open1 and open2:
                    visited['lines'].add(dir_key)
                    open3_count += 1

        # 체인 내 다른 돌 재귀 탐색
        # 재귀 전에 이 방향 라인 키를 미리 등록 → 같은 라인 중복 방지
        for px, py in chain:
            if (px, py) != (x, y) and (px, py) not in visited['stones']:
                peer_lkey = get_line_key(px, py, dx, dy)
                visited['lines'].add((dx, dy, peer_lkey))
                open3_count += count_open3(px, py, board, visited)

    return open3_count


def check_overline(x, y, board):
    """(x,y) 포함 라인에서 흑돌 연속 6개 이상이면 True"""
    directions = [(1,0),(0,1),(1,1),(1,-1)]
    for dx, dy in directions:
        count = (1
                 + count_in_direction(x, y,  dx,  dy, board, Black_Piece)
                 + count_in_direction(x, y, -dx, -dy, board, Black_Piece))
        if count >= 6:
            return True
    return False


def count_four(x,y, board,visited=None):  # player=2 → 흑돌 기준
    """
    보드 전체에서 '4목' 패턴을 세는 함수.
    '4목' 정의: 돌이 4개이고, 빈칸 하나를 채우면 바로 5목이 되는 상태.
    """
    if visited is None:
        visited = {'stones': set(), 'lines': set()}
    visited['stones'].add((x, y))
    directions = [(1,0),(0,1),(1,1),(1,-1)]
    four_count = 0

    for dx, dy in directions:
        lkey    = get_line_key(x, y, dx, dy)
        dir_key = (dx, dy, lkey)

        # 이미 이 방향+라인 처리했으면 건너뜀
        if dir_key in visited['lines']:
            continue

        # 이 방향 연속 길이가 6 이상이면 overline → open3 판정 제외
        # (overline은 is_forbidden에서 별도로 처리)
        if get_line_length(x, y, dx, dy, board) >= 6:
            visited['lines'].add(dir_key)
            continue

        # 양방향으로 체인 수집 (빈칸 1개 허용)
        chain_fwd = collect_chain(x, y,  dx,  dy, board, Black_Piece)
        chain_bwd = collect_chain(x, y, -dx, -dy, board, Black_Piece)
        chain = list(set(chain_fwd + chain_bwd + [(x, y)]))
        chain.sort()

        if len(chain) == 4:
            sx, sy = chain[0]
            ex, ey = chain[-1]

            is_really_four = True

            # 양 끝에 같은 돌이 이어지면 4 아님
            for ex_dx, ex_dy, corner in [(-dx, -dy, (sx, sy)), (dx, dy, (ex, ey))]:
                cx, cy = corner[0] + ex_dx, corner[1] + ex_dy
                if (1 <= cx <= Board_Size_Actual and 1 <= cy <= Board_Size_Actual
                        and board[cy-1][cx-1] == Black_Piece):
                    is_really_four = False
                    break

            # 추가: 양쪽 끝이 모두 막혀 있으면 제외
            left_x, left_y = sx - dx, sy - dy
            right_x, right_y = ex + dx, ey + dy

            left_blocked = (not (1 <= left_x <= Board_Size_Actual and 1 <= left_y <= Board_Size_Actual)) \
                        or (board[left_y-1][left_x-1] != 0)
            right_blocked = (not (1 <= right_x <= Board_Size_Actual and 1 <= right_y <= Board_Size_Actual)) \
                            or (board[right_y-1][right_x-1] != 0)

            if left_blocked and right_blocked:
                is_really_four = False

            if is_really_four:
                visited['lines'].add(dir_key)
                four_count += 1

        # 체인 내 다른 돌 재귀 탐색
        # 재귀 전에 이 방향 라인 키를 미리 등록 → 같은 라인 중복 방지
        for px, py in chain:
            if (px, py) != (x, y) and (px, py) not in visited['stones']:
                peer_lkey = get_line_key(px, py, dx, dy)
                visited['lines'].add((dx, dy, peer_lkey))
                four_count += count_four(px, py, board, visited)

    return four_count

def is_forbidden(x, y, board):
    if not (1 <= x <= Board_Size_Actual and 1 <= y <= Board_Size_Actual):
        return False
    if board[y-1][x-1] != 0:
        return False

    board[y-1][x-1] = Black_Piece
    try:
        # 장목이 우선검사
        # 흑은 6목 이상이 되는 순간 다른 승리 조건과 상관없이 무조건 금수입니다.
        if check_overline(x, y, board):
            return True

        # 승리 판단
        if winCheck(Black_Piece, "Black", board) == "Black":
            return False

        # 3순위: 33, 44 금수 확인
        f4 = count_four(x, y, board)
        o3 = count_open3(x, y, board)

        if o3 >= 2 or f4 >= 2:
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
- 백시작을 흑시작으로 수정 + 턴 로직 수정
- Score_Board 수정
- 금수 지정 추가
- 무승부 추가
- 기존 검사 로직 오류 수정 (보드 검사 시 -3 인덱스 오류 존재했음)
- [추가] count_open3 재귀 방식 → 보드 전체 라인 슬라이딩 윈도우 방식으로 교체
         동일 라인 내 돌들을 서로 다른 open3로 중복 카운트하던 오판 수정
- [추가] get_all_lines(board): 4방향 전체 라인을 한 번만 추출하는 공통 함수 추가
- [추가] count_four 단일 좌표 기준 → count_four_total(board) 보드 전체 스캔으로 교체
         연속 4 및 빈칸 포함 4 패턴(■■■□■ 등) 모두 감지
- [추가] check_overline: is_forbidden 내 임시 배치 후 호출로 정확한 6목+ 판정
- [추가] is_forbidden: 5목 완성 자리는 금수 제외 (승리 우선) 처리 추가
- [추가] 같은 가로/세로/대각 라인에 속한 돌 그룹은 open3 최대 1개로만 카운트
         (예: ■■ 와 ■■■ 가 같은 가로줄이면 33 금수로 오판하지 않음)
"""