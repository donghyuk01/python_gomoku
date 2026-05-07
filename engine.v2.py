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

    def count_four(self, r, c, player):
        # 4-4 금지
        directions = [(1,0),(0,1),(1,1),(1,-1)]
        fours = 0
        for dr, dc in directions:
            count = 1
            count += self.count_in_direction(r, c,  dr,  dc, player)
            count += self.count_in_direction(r, c, -dr, -dc, player)
            if count == 4:
                fours += 1
        return fours

    def collect_chain(self, r, c, dr, dc, player):
        coords = []
        skips = 0
        count = 0
        nr, nc = r+dr, c+dc
        
        while 0 <= nr < self.board_size and 0 <= nc < self.board_size:
            if self.board[nr, nc] == player:
                coords.append((nr, nc))
                count += 1
                if count >= 2:  # 최대 2개까지만 확장
                    break
            elif self.board[nr, nc] == 0 and skips == 0:
                # 빈칸 한 번만 건너뛰기 허용
                skips += 1
                nr += dr; nc += dc
                continue
            else:
                break
            nr += dr; nc += dc
        
        return coords

    def count_open3(self, r, c, player, visited=None):
        if visited is None:
            visited = set()
        directions = [(0,1),(1,0),(1,1),(1,-1)]
        open3s = 0
        
        for dr, dc in directions:
            # 돌 뭉치 좌표 수집
            chain = [(r,c)]
            chain += self.collect_chain(r,c,dr,dc,player)
            chain += self.collect_chain(r,c,-dr,-dc,player)
            chain.sort()
            
            if len(chain) == 3:
                start_r, start_c = chain[0]
                end_r, end_c = chain[-1]
                
                e1r, e1c = start_r - dr, start_c - dc
                e2r, e2c = end_r + dr, end_c + dc
                
                open1 = (0 <= e1r < self.board_size and 0 <= e1c < self.board_size and self.board[e1r,e1c] == 0)
                open2 = (0 <= e2r < self.board_size and 0 <= e2c < self.board_size and self.board[e2r,e2c] == 0)
                
                if open1 and open2:
                    key = (dr, dc, start_r, start_c, end_r, end_c)
                    if key not in visited:
                        visited.add(key)
                        open3s += 1
            
            # 이어진 좌표들을 기준으로 재귀 검사
            for pr, pc in chain:
                if (pr, pc) not in visited:
                    visited.add((pr, pc))
                    open3s += self.count_open3(pr, pc, player, visited)
        
        return open3s

    
    def forbidden(self, r, c, player):
        if player != 1: return False
        
        self.board[r, c] = player  # 돌 배치
        
        # 여기서 모든 방향을 다 검사해야 함
        open3_count = self.count_open3(r, c, player) 
        four_count = self.count_four(r, c, player)
        is_overline = self.check_overline(r, c, player)
        
        self.board[r, c] = 0  # 돌 제거
        
        # 디버깅 출력 추가
        if open3_count >= 1:
            print(f"좌표 ({r}, {c}) 검사 - 열린3 개수: {open3_count}")

        if is_overline: return True
        if open3_count >= 2: return True  # 여기서 2개 이상일 때만 True
        if four_count >= 2: return True
        
        return False

    
"""
33 방지를 위한 forbidden함수, is_open_three함수 추가
makemove함수 수정
is_open_three 함수 수정(연속된 돌만 감지가능 했음)
"""