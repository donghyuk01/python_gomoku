import numpy as np

class OmokEngine:
    def __init__(self, board_size=15):
        """
        Initialize the Omok (Gomoku) game engine.
        :param board_size: The width and height of the square board.
        """
        self.board_size = board_size
        self.reset()

    def reset(self):
        """
        Resets the game state to start a new match.
        Returns the initial empty board state.
        """
        # Create a 2D array filled with zeros (0 = empty, 1 = Player 1, 2 = Player 2)
        self.board = np.zeros((self.board_size, self.board_size), dtype=int)
        self.current_player = 1 
        self.is_over = False
        self.winner = None
        return self.get_state()

    def get_state(self):
        """
        Converts the board into a format suitable for the Neural Network (CNN).
        Returns a 3D float32 tensor of shape (1, board_size, board_size).
        """
        state = np.zeros((2, self.board_size, self.board_size), dtype=np.float32)
        state[0] = (self.board == 1).astype(np.float32)  # 검은 돌
        state[1] = (self.board == 2).astype(np.float32)  # 백돌
        return state

    def get_valid_moves(self):
        """
        Finds all empty cells where a move is allowed.
        Returns an array of [row, col] coordinates.
        """
        # 수정 금수 자리를 아예 선택하지 못하도록 제외
        all_empty = np.argwhere(self.board==0)
        valid_moves = []

        for r,c in all_empty:
            if not self.forbidden(r,c,self.current_player):
                valid_moves.append([r,c])
        return np.array(valid_moves)

    def make_move(self, row, col):
        """
        Executes a move for the current player.
        :param row: Row index to place the stone.
        :param col: Column index to place the stone.
        :return: True if move was successful, False if invalid.
        돌을 둘 수 있는 자리인지
        돌 배치
        이겼는지 비겻는지
        다음 차례로 가기
        """
        print("현재 플레이어:", self.current_player)
        # 1. 기본적인 유효성 검사 (범위 밖, 이미 돌이 있음, 게임 종료됨)
        if not (0 <= row < self.board_size and 0 <= col < self.board_size):
            return False
        if self.board[row, col] != 0 or self.is_over:
            return False
        
        # 2. 흑돌(1)일 때만 금수 규칙(3-3 등)을 체크
        if self.current_player == 1:
            if self.forbidden(row, col, 1):
                # print(f"Forbidden move for Black at ({row}, {col})")
                return False

        # 3. 돌 배치
        self.board[row, col] = self.current_player
        
        # 4. 승리 판정
        if self.check_win(row, col):
            self.is_over = True
            self.winner = self.current_player
        # 5. 무승부 판정 (빈 공간이 없음)
        elif not np.any(self.board == 0):   
            self.is_over = True
            self.winner = 0 
            
        # 6. 턴 교체 (1->2, 2->1)
        self.current_player = 3 - self.current_player
        return True

    def check_win(self, r, c):
        """
        Checks if the last move placed at (r, c) created a line of 5 or more.
        
        """ 
        player = self.board[r, c]
        # Directions: Horizontal, Vertical, Diagonal (\), Anti-diagonal (/)
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)] #순서대로 가로 세로 우하향 우상향
        
        for dr, dc in directions:
            count = 1
            # Check in both directions along the line (e.g., Left and Right)
            for sign in [1, -1]:
                nr, nc = r + dr * sign, c + dc * sign
                # Stay within board boundaries and match player stone
                while 0 <= nr < self.board_size and 0 <= nc < self.board_size and self.board[nr, nc] == player:
                    count += 1
                    nr += dr * sign
                    nc += dc * sign
            
            # If 5 or more in a row are found, the player wins
            if count >= 5: return True # 5개 이상
        return False

    def check_patterns(self, player, length):
        """
        Scans the entire board to find a sequence of stones of a specific 'length'.
        Used for Reward Shaping (e.g., giving the AI points for creating a 3-in-a-row).
        """
        # Directions: Horizontal, Vertical, Diagonal, Anti-diagonal
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for r in range(self.board_size):
            for c in range(self.board_size):
                # If the cell belongs to the player we are checking
                if self.board[r, c] == player:
                    for dr, dc in directions:
                        count = 1
                        nr, nc = r + dr, c + dc
                        
                        # Trace the line in the current direction
                        while 0 <= nr < self.board_size and 0 <= nc < self.board_size and self.board[nr, nc] == player:
                            count += 1
                            nr += dr
                            nc += dc
                        
                        # If a sequence of the exact length is found
                        if count == length:
                            return True
        return False
    
    def count_in_direction(self, r, c, dr, dc, player):
        # 길이 측정
        count = 0
        nr, nc = r + dr, c + dc
        while 0 <= nr < self.board_size and 0 <= nc < self.board_size and self.board[nr, nc] == player:
            count += 1
            nr += dr
            nc += dc
            # print(f"찾은 count={count}")
        return count
    

    def check_overline(self, r, c, player):
    # 6목 금지 
        directions = [(1,0),(0,1),(1,1),(1,-1)]
        for dr, dc in directions:
            count = 1
            count += self.count_in_direction(r, c,  dr,  dc, player)
            count += self.count_in_direction(r, c, -dr, -dc, player)
            if count >= 6:
                return True
        return False



    def count_open3_total(self, tr, tc, player):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        P = player
        E = 0

        open3_patterns = [
            [E, P, P, P, E],
            [E, P, P, E, P, E],
            [E, P, E, P, P, E],
            [E, P, E, P, E, P, E],
        ]

        open3_count = 0

        for dr, dc in directions:
            # 이미 처리한 라인 셀 추적
            visited_lines = set()
            start_r,end_r= tr-7 if tr-7>0 else 0, tr+7 if tr+7<self.board_size else self.board_size
            start_c, end_c=tc-7 if tc-7>0 else 0, tc+7 if tc+7<self.board_size else self.board_size
            for r in range(start_r,end_r):
                for c in range(start_c,end_c):
                    # 이 셀이 속한 라인의 "기준점" 계산 (라인 중복 방지)
                    # 역방향으로 끝까지 가면 라인의 시작점을 구할 수 있음
                    sr, sc = r, c
                    black_count=0
                    check_white=False
                    while 0 <= sr - dr < self.board_size and 0 <= sc - dc < self.board_size:
                        sr -= dr
                        sc -= dc
                        if self.board[sr,sc]==2:
                            check_white=True
                        if not check_white:
                            if self.board[sr,sc]==1:
                                black_count+=1
                        
                    line_key = (sr, sc, dr, dc)
                    if line_key in visited_lines:
                        continue
                    visited_lines.add(line_key)

                    if black_count>3:
                        continue
                    if check_white:
                        continue


                    # 이 라인 전체 셀 추출
                    line = []
                    nr, nc = sr, sc
                    while 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                        line.append(self.board[nr, nc])
                        nr += dr
                        nc += dc

                    # 이 라인에서 open3 패턴이 존재하는지 (최대 1개)
                    # 같은 라인에서 겹치는 패턴은 1개로 간주
                    line_has_open3 = False
                    used_positions = set()  # 이미 사용된 돌 위치

                    for pat in open3_patterns:
                        wlen = len(pat)
                        for start in range(len(line) - wlen + 1):
                            window = line[start:start + wlen]
                            if window == pat:
                                # 이 패턴의 P 위치들
                                stone_positions = frozenset(
                                    start + i for i in range(wlen) if pat[i] == P
                                )
                                # 이미 카운트된 돌과 겹치면 같은 라인의 연장으로 봄
                                if not stone_positions & used_positions:
                                    used_positions |= stone_positions
                                    line_has_open3 = True
                                    break
                        if line_has_open3:
                            break

                    if line_has_open3:
                        open3_count += 1

        return open3_count

    def forbidden(self, r, c, player):
        if player != 1:
            return False

        self.board[r, c] = player  # 임시로 돌 배치

        # 5목이 되는 자리는 금수 아님
        if self.check_win(r, c):
            self.board[r, c] = 0
            return False

        # 보드 전체 기준으로 패턴 카운트
        open3_count = self.count_open3_total(r,c,player)
        if open3_count >= 2:   
            self.board[r, c] = 0  # 돌 제거
            return True
        four_count  = self.count_four_total(r,c,player)
        if four_count  >= 2:   
            self.board[r, c] = 0  # 돌 제거
            return True
        is_overline = self.check_overline(r, c, player)
        if is_overline:        
            self.board[r, c] = 0  # 돌 제거
            return True
        self.board[r, c] = 0  # 돌 제거
        return False

    def count_four_total(self, r, c, player):
        """
        (r, c)에 돌을 놓았을 때 만들어지는 '4'의 개수를 세는 로직
        '4'의 정의: 돌이 4개이고, 빈 칸에 돌을 놓아 바로 5가 될 수 있는 상태
        """
        four_count = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for dr, dc in directions:
            # 해당 방향 라인에서 '4'가 형성되는지 확인
            line_stones = []
            # 중심 (r, c)를 포함하여 앞뒤로 4칸씩 총 9칸을 살펴봄 (5를 만들기 위한 최소 범위)
            for i in range(-4, 5):
                nr, nc = r + dr * i, c + dc * i
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    line_stones.append({'pos': (nr, nc), 'val': self.board[nr, nc]})
                else:
                    line_stones.append({'pos': None, 'val': -1}) # 벽

            # 추출된 라인 내에서 (r, c)를 포함하는 '4'가 있는지 검사
            # '4'란? : 현재 라인에서 player의 돌이 4개이고, 빈칸(0) 하나를 채워서 5가 되는 경우
            # 단, 그 5는 6목(Overline)이 아니어야 함 (흑 기준)
            
            possible_fives = 0
            # 5개가 들어갈 수 있는 모든 윈도우(연속 5칸) 조사
            for start in range(len(line_stones) - 4):
                window = line_stones[start : start + 5]
                values = [w['val'] for w in window]
                
                # 윈도우 안에 내 돌이 4개 있고, 빈 공간이 1개 있는 경우
                if values.count(player) == 4 and values.count(0) == 1:
                    # 그 빈 공간에 두었을 때 정확히 5가 되는지(6목 제외) 확인 필요
                    # (간단한 구현을 위해 여기서는 4목 형성 여부만 우선 체크)
                    possible_fives += 1
            
            # 한 방향 라인에서 만들어진 '4'가 있다면 카운트 증가
            if possible_fives > 0:
                four_count += 1
                
        return four_count




    
"""
33 방지를 위한 forbidden함수, is_open_three함수 추가
makemove함수 수정
is_open_three 함수 수정(연속된 돌만 감지가능 했음)
count_open3_total 속도 향상 05-12 17:02
"""