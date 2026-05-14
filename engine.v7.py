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

    def get_line_key(self, r, c, dr, dc):
        """(r,c)를 포함하는 (dr,dc) 방향 라인의 시작 좌표 반환 (0-based)."""
        sr, sc = r, c
        while 0 <= sr - dr < self.board_size and 0 <= sc - dc < self.board_size:
            sr -= dr
            sc -= dc
        return (sr, sc, dr, dc)

    def collect_chain(self, r, c, dr, dc, player):
        """
        (r,c)에서 (dr,dc) 방향으로 돌 연결을 수집.
        빈칸 한 개까지 건너뛰기 허용.
        반환: 연결된 좌표 리스트 (자기 자신 제외)
        """
        coords = []
        found_skip = False
        nr, nc = r + dr, c + dc

        while 0 <= nr < self.board_size and 0 <= nc < self.board_size:
            if self.board[nr][nc] == player:
                coords.append((nr, nc))
            elif self.board[nr][nc] == 0:
                if not found_skip:
                    nnr, nnc = nr + dr, nc + dc
                    if (0 <= nnr < self.board_size and 0 <= nnc < self.board_size
                            and self.board[nnr][nnc] == player):
                        found_skip = True
                    else:
                        break
                else:
                    break
            else:
                break
            nr += dr
            nc += dc
        return coords

    def get_line_length(self, r, c, dr, dc, player):
        """(r,c)에서 (dr,dc) 방향 양쪽으로 연속된 돌 총 길이 반환."""
        return (1
                + self.count_in_direction(r, c, dr, dc, player)
                + self.count_in_direction(r, c, -dr, -dc, player))

    def count_open3_total(self, r, c, player, visited=None):
        """
        (r,c)를 포함하는 열린3 개수를 반환.
        """
        if visited is None:
            visited = {'stones': set(), 'lines': set()}

        visited['stones'].add((r, c))
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        open3_count = 0

        for dr, dc in directions:
            lkey = self.get_line_key(r, c, dr, dc)
            dir_key = (dr, dc, lkey)

            if dir_key in visited['lines']:
                continue

            if self.get_line_length(r, c, dr, dc, player) >= 6:
                visited['lines'].add(dir_key)
                continue

            chain_fwd = self.collect_chain(r, c, dr, dc, player)
            chain_bwd = self.collect_chain(r, c, -dr, -dc, player)
            chain = list(set(chain_fwd + chain_bwd + [(r, c)]))
            chain.sort()

            if len(chain) == 3:
                sr, sc = chain[0]
                er, ec = chain[-1]

                is_really_three = True
                for ex_dr, ex_dc, corner in [(-dr, -dc, (sr, sc)), (dr, dc, (er, ec))]:
                    cx, cy = corner[0] + ex_dr, corner[1] + ex_dc
                    if (0 <= cx < self.board_size and 0 <= cy < self.board_size
                            and self.board[cx][cy] == player):
                        is_really_three = False
                        break

                if is_really_three:
                    e1r, e1c = sr - dr, sc - dc
                    e2r, e2c = er + dr, ec + dc
                    open1 = (0 <= e1r < self.board_size and 0 <= e1c < self.board_size
                            and self.board[e1r][e1c] == 0)
                    open2 = (0 <= e2r < self.board_size and 0 <= e2c < self.board_size
                            and self.board[e2r][e2c] == 0)

                    if open1 and open2:
                        visited['lines'].add(dir_key)
                        open3_count += 1

            for pr, pc in chain:
                if (pr, pc) != (r, c) and (pr, pc) not in visited['stones']:
                    peer_lkey = self.get_line_key(pr, pc, dr, dc)
                    visited['lines'].add((dr, dc, peer_lkey))
                    open3_count += self.count_open3_total(pr, pc, player, visited)

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

    def count_four_total(self, tr, tc, player):
        """
        보드 전체에서 (tr, tc)에 돌을 놓았을 때 만들어지는 '4'의 개수를 세는 로직
        '4'의 정의: 돌이 4개이고, 빈 칸 하나를 채우면 바로 5목이 되는 상태
        열린4/막힌4 모두 포함
        """
        four_count = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for dr, dc in directions:
            visited_lines = set()
            start_r,end_r= tr-7 if tr-7>0 else 0, tr+7 if tr+7<self.board_size else self.board_size
            start_c,end_c=tc-7 if tc-7>0 else 0, tc+7 if tc+7<self.board_size else self.board_size

            for r in range(start_r,end_r):
                for c in range(start_c,end_c):
                    if self.board[r, c] != player:
                        continue

                    # 라인 시작점 찾기
                    sr, sc = r, c
                    while 0 <= sr - dr < self.board_size and 0 <= sc - dc < self.board_size:
                        sr -= dr
                        sc -= dc

                    line_key = (sr, sc, dr, dc)
                    if line_key in visited_lines:
                        continue
                    visited_lines.add(line_key)

                    # 라인 전체 추출
                    line = []
                    nr, nc = sr, sc
                    while 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                        line.append(self.board[nr, nc])
                        nr += dr
                        nc += dc

                    for start in range(len(line) - 4):
                        window = line[start:start + 5]
                        values = list(window)

                        if values.count(player) == 4 and values.count(0) == 1:
                            # 양쪽 끝 좌표 계산
                            left_idx = start - 1
                            right_idx = start + 5

                            left_blocked = (left_idx < 0) or (line[left_idx] != 0)
                            right_blocked = (right_idx >= len(line)) or (line[right_idx] != 0)

                            # 양쪽 다 막힌 경우는 제외
                            if not (left_blocked and right_blocked):
                                four_count += 1
                                break

        return four_count

"""
33 방지를 위한 forbidden함수, is_open_three함수 추가
makemove함수 수정
is_open_three 함수 수정(연속된 돌만 감지가능 했음)
count_open3_total 속도 향상 05-12 17:02
"""