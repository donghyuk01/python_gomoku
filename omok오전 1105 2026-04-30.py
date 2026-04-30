# 출처 : https://github.com/BobscHuang/Gomoku/blob/master/Gomoku/Gomoku.py
from tkinter import *
from time import *
import sys
myInterface = Tk()
s = Canvas(myInterface, width=800, height=800, background= "#b69b4c")
s.pack()

#Board Size
Board_Size = 15
Frame_Gap = 35
width = 800
height = 800

#Note: all "exit" does is terminate the while loop, so it dosen't really do much...
#      to begin another round you would need to restart the program.

forbidden_marks = []  # 금수 표시 저장 리스트

def draw_forbidden_marks():
    global forbidden_marks
    # 기존 금수 표시 삭제
    for mark in forbidden_marks:
        s.delete(mark)
    forbidden_marks = []
    
    # 흑 차례일 때만 표시
    if Turn_Num % 2 == 1:
        for x in range(1, Board_Size + 2):
            for y in range(1, Board_Size + 2):
                if board[y-1][x-1] == 0 and is_forbidden(x, y, board):
                    cx = Board_X1 + Board_GapX * (x - 1)
                    cy = Board_Y1 + Board_GapY * (y - 1)
                    r = Chess_Radius * 0.5
                    mark1 = s.create_line(cx - r, cy - r, cx + r, cy + r,
                                          fill="red", width=2)
                    mark2 = s.create_line(cx + r, cy - r, cx - r, cy + r,
                                          fill="red", width=2)
                    forbidden_marks.append(mark1)
                    forbidden_marks.append(mark2)

def is_forbidden(x, y, board):
    # 임시로 돌을 놓아보기
    board[y-1][x-1] = Black_Piece 
    open3 = count_open3(x, y, board)
    four  = count_four(x, y, board)
    six   = check_overline(x, y, board)
    # 임시 돌 제거
    board[y-1][x-1] = 0
    if six:             # 장목 금지
        return True
    if open3 >= 2:      # 3-3 금지
        return True
    if four >= 2:       # 4-4 금지
        return True
    return False

def count_in_direction(x, y, dx, dy, board, piece):
    # 길이 측정
    count = 0
    nx, ny = x + dx, y + dy
    while 0 < nx <= Board_Size+1 and 0 < ny <= Board_Size+1 and board[ny-1][nx-1] == piece:
        count += 1
        nx += dx
        ny += dy
    return count

def check_overline(x, y, board):
    # 6목 금지 
    directions = [(1,0),(0,1),(1,1),(1,-1)]
    for dx, dy in directions:
        count = 1
        count += count_in_direction(x, y,  dx,  dy, board, Black_Piece)
        count += count_in_direction(x, y, -dx, -dy, board, Black_Piece)
        if count >= 6:
            return True
    return False

def count_four(x, y, board):
    # 4-4 금지
    directions = [(1,0),(0,1),(1,1),(1,-1)]
    fours = 0
    for dx, dy in directions:
        count = 1
        count += count_in_direction(x, y,  dx,  dy, board, Black_Piece)
        count += count_in_direction(x, y, -dx, -dy, board, Black_Piece)
        if count == 4:
            fours += 1
    return fours

def count_open3(x, y, board):
    # 안 막힌 3-3 금지
    directions = [(1,0),(0,1),(1,1),(1,-1)]
    open3s = 0
    for dx, dy in directions:
        fwd = count_in_direction(x, y,  dx,  dy, board, Black_Piece)
        bwd = count_in_direction(x, y, -dx, -dy, board, Black_Piece)
        count = 1 + fwd + bwd
        
        if count == 3:
            end1x = x +  dx * fwd
            end1y = y +  dy * fwd
            end2x = x + -dx * bwd
            end2y = y + -dy * bwd
            
            open1 = (0 < end1x+dx <= Board_Size+1 and 0 < end1y+dy <= Board_Size+1
                     and board[end1y+dy-1][end1x+dx-1] == 0)
            open2 = (0 < end2x-dx <= Board_Size+1 and 0 < end2y-dy <= Board_Size+1
                     and board[end2y-dy-1][end2x-dx-1] == 0)
            
            if open1 and open2:
                open3s += 1
    return open3s

def create_circle(x, y, radius, fill = "", outline = "black", width = 1):
    # 동그라미 그리기
    s.create_oval(x - radius, y - radius, x + radius, y + radius, fill = fill, outline = outline, width = width)

def Value_Check_int(Value):
    try:
        Value = int(Value)
    except ValueError:
        return "string"
    else:
        return "int"

def MouseClick(event):
    # 클릭 위치 감지
    global Click_Cord
    X_click = event.x
    Y_click = event.y
    Click_Cord = Piece_Location(X_click, Y_click)
    # print(Click_Cord)

s.bind("<Button-1>", MouseClick)

Click_Cord = [None, None]

def Piece_Location(X_click, Y_click):    
    # 좌표
    X = None
    Y = None
    for i in range(len(Actual_CordX1)):
        
        if X_click > Actual_CordX1[i] and X_click < Actual_CordX2[i]:
            X = Game_CordX[i]

        if Y_click > Actual_CordY1[i] and Y_click < Actual_CordY2[i]:
            Y = Game_CordY[i]

    return X, Y

def Location_Validation():
    # 존재 여부 확인
    if X == None or Y == None:
        return False
        
    elif board[Y - 1][X - 1] == 0:
        return True


def Score_Board():
    # 점수 표시
    if Winner == None:
        Turn_Text = s.create_text(width / 2, height - Frame_Gap + 15, text = "Turn = " + Turn, font = "Helvetica 25 bold", fill = Turn)
        return Turn_Text
    elif Draw == 1:
        s.create_rectangle(width*0.1, height/2 - 60, width*0.9, height/2 + 60, fill = "white", outline = "black", width = 3)
        s.create_text(width / 2, height / 2,  # 이 줄 추가
                      text = "Draw!", 
                      font = "Helvetica 60 bold", 
                      fill = "black")
    else:
        # s.create_text(width / 2, height - Frame_Gap + 15, text = Winner.upper() + " WINS!", font = "Helvetica 25 bold", fill = Winner.lower())
        s.create_rectangle(width*0.1, height/2 - 60, width*0.9, height/2 + 60, fill = "white", outline = "black", width = 3)
        s.create_text(width / 2, height / 2,  # 이 줄 추가
                      text = Winner.upper() + " WINS!", 
                      font = "Helvetica 60 bold", 
                      fill = "black")

def drawCheck(board):
    for row in board:
        if 0 not in row:
            Draw=1

def winCheck(Piece_Number, Piece_Colour, board):
    # 승리 확인
    if rowCheck(Piece_Number, board) or rowCheck(Piece_Number, transpose(board)) or rowCheck(Piece_Number, transposeDiagonalInc(board)) or rowCheck(Piece_Number, transposeDiagonalDec(board)):
        Winner = Piece_Colour
        return Winner

def rowCheck(Piece_Number, board):
    for i in range(len(board)):
        if board[i].count(Piece_Number) >= 5:
            
            for z in range(len(board[i]) - 4):
                Connection = 0

                for c in range(5):
                    if board[i][z + c] == Piece_Number:
                        Connection += 1

                    else:
                        break

                    if Connection == 5:
                        return True

def getDiagonalDec(loa, digNum):
    lst=[]
    if digNum <= len(loa) - 1:
        index = len(loa) - 1
        for i in range(digNum, -1, -1):
            lst.append(loa[i][index])
            index -= 1
        return lst
    else:
        index = (len(loa) * 2 - 2) - digNum
        for i in range(len(loa) - 1, digNum - len(loa), -1):
            lst.append(loa[i][index])
            index -= 1
        return lst


def transposeDiagonalDec(loa):
    lst = []
    for i in range(len(loa) * 2 - 1):
        lst.append(getDiagonalDec(loa, i))
    return lst

def getDiagonalInc(loa, digNum):
    lst=[]
    if digNum <= len(loa) - 1:
        index = 0
        for i in range(digNum, -1, -1):
            lst.append(loa[i][index])
            index += 1
        return lst
    else:
        index =  digNum - len(loa) + 1
        for i in range(len(loa) - 1, digNum - len(loa), -1):
            lst.append(loa[i][index])
            index += 1
        return lst


def transposeDiagonalInc(loa):
    lst = []
    for i in range(len(loa) * 2 - 1):
        lst.append(getDiagonalInc(loa, i))
    return lst

def transpose(loa):
    # 
    lst = []
    for i in range(len(loa)):
        lst.append(getCol(loa, i))
    return lst
    
def getCol(loa, colNum):
    # 
    lst = []
    for i in range(len(loa)):
        lst.append(loa[i][colNum])
    return lst

def Index2D_Cord(List, Find):
    # 정확한 용도를 모르겠음
    for i, x in enumerate(List):
        if Find in x:
            Colour_CordX.append(i - 1)
            Colour_CordY.append(x.index(Find) - 1)

def Exit():
    # 종료
    global Winner
    Winner = "Exit"
    myInterface.destroy()
    
#Board
Board_Size = Board_Size - 1
Board_X1 = width / 10
Board_Y1 = height / 10
Board_GapX = (width - Board_X1 * 2) / Board_Size
Board_GapY = (height - Board_Y1 * 2) / Board_Size

#Chess Piece
Chess_Radius = (Board_GapX * (9 / 10)) / 2

#Turn
Turn_Num = 1
Turn = "black"
Winner = None
Draw=None

#Cord List
Black_Cord_PickedX = []
Black_Cord_PickedY = []
White_Cord_PickedX = []
White_Cord_PickedY = []

#Click Detection Cord
Game_CordX = []
Game_CordY = []
Actual_CordX1 = []
Actual_CordY1 = []
Actual_CordX2 = []
Actual_CordY2 = []

#2D Board List
board = []

#Buttons
B = Button(myInterface, text = "EXIT", font = "Helvetica 10 bold", command = Exit, bg = "gray", fg = "black")
B.pack()
B.place(x = width / 2 * 0.5, y = height - Frame_Gap * 1.6 + 15, height = Chess_Radius * 2, width = Chess_Radius * 4)

#2D list for gameboard
for i in range(Board_Size + 1):
    board.append([0] * (Board_Size + 1))
    
Unfilled = 0
Black_Piece = 2
White_Piece = 1

#Fills Empty List
for z in range(1, Board_Size + 2): 
    for i in range(1, Board_Size + 2):
        Game_CordX.append(z)
        Game_CordY.append(i)
        Actual_CordX1.append((z - 1) * Board_GapX + Board_X1 - Chess_Radius)
        Actual_CordY1.append((i - 1) * Board_GapY + Board_Y1 - Chess_Radius)
        Actual_CordX2.append((z - 1) * Board_GapX + Board_X1 + Chess_Radius)
        Actual_CordY2.append((i - 1) * Board_GapY + Board_Y1 + Chess_Radius)

#Create Board
s.create_rectangle(Board_X1 - Frame_Gap, Board_Y1 - Frame_Gap, Board_X1 + Frame_Gap + Board_GapX * Board_Size, Board_Y1 + Frame_Gap + Board_GapY * Board_Size, width = 3)

for f in range(Board_Size + 1):
    s.create_line(Board_X1, Board_Y1 + f * Board_GapY, Board_X1 + Board_GapX * Board_Size, Board_Y1 + f * Board_GapY)
    s.create_line(Board_X1 + f * Board_GapX, Board_Y1, Board_X1 + f * Board_GapX, Board_Y1 + Board_GapY * Board_Size)

    s.create_text(Board_X1 - Frame_Gap * 1.7, Board_Y1 + f * Board_GapY, text = f + 1, font = "Helvetica 10 bold", fill = "black")
    s.create_text(Board_X1 + f * Board_GapX, Board_Y1 - Frame_Gap * 1.7, text = f + 1, font = "Helvetica 10 bold", fill = "black")

Turn_Text = Score_Board()
#Game Code
while Winner == None or Draw == None:
    s.update()

    X = Click_Cord[0]
    Y = Click_Cord[1]

    Picked = Location_Validation()

    if Picked:
        if Turn_Num % 2 == 1 and is_forbidden(X, Y, board):
            Click_Cord = [None, None]
            continue
        s.delete(Turn_Text)
        
        create_circle(Board_X1 + Board_GapX * (X - 1), Board_Y1 + Board_GapY * (Y - 1), radius = Chess_Radius, fill = Turn)

        if Turn_Num % 2 == 1:
            Black_Cord_PickedX.append(X)
            Black_Cord_PickedY.append(Y)
            board[Y - 1][X - 1] = 2
            Turn = "white"

        elif Turn_Num % 2 == 0:
            White_Cord_PickedX.append(X)
            White_Cord_PickedY.append(Y)
            board[Y - 1][X - 1] = 1
            Turn = "black"


        Turn_Text = Score_Board()

        Turn_Num = Turn_Num + 1
        draw_forbidden_marks()

        if Turn == "white":
            Colour_Check = Black_Piece
            Win_Check = "Black"

        elif Turn == "black":
            Colour_Check = White_Piece
            Win_Check = "White"

        Winner = winCheck(Colour_Check, Win_Check, board)
        Draw = drawCheck(board)

s.delete(Turn_Text)
if Draw == 1:
    a=0

if Winner != "Exit":
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

    