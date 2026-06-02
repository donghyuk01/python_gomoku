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
        self.board = np.zeros((self.board_size, self.board_size), dtype=int)
        self.current_player = 1 
        self.is_over = False
        self.winner = None
        return self.get_state()

    def get_state(self):
        state = np.zeros((2, self.board_size, self.board_size), dtype=np.float32)
        # 0번 채널: 현재 턴인 플레이어의 돌 위치 (나)
        state[0] = (self.board == self.current_player).astype(np.float32)
        # 1번 채널: 상대방 플레이어의 돌 위치 (적)
        state[1] = (self.board == (3 - self.current_player)).astype(np.float32)
        return state

    def get_valid_moves(self):
        """
        Finds all empty cells where a move is allowed.
        Returns an array of [row, col] coordinates.
        """
        all_empty = np.argwhere(self.board == 0)
        valid_moves = []
        for r, c in all_empty:
            if not self.forbidden(r, c, self.current_player):
                valid_moves.append([r, c])
        return np.array(valid_moves)

    def make_move(self, row, col):
        """
        Executes a move for the current player.
        """
        if not (0 <= row < self.board_size and 0 <= col < self.board_size):
            return False
        if self.board[row, col] != 0 or self.is_over:
            return False
        
        # 흑돌(1)일 때만 금수 규칙 체크
        if self.current_player == 1:
            if self.forbidden(row, col, 1):
                return False

        # 돌 배치
        self.board[row, col] = self.current_player
        
        # 승리 판정
        if self.check_win(row, col):
            self.is_over = True
            self.winner = self.current_player
        # 무승부 판정
        elif not np.any(self.board == 0):   
            self.is_over = True
            self.winner = 0 
            
        # 턴 교체
        self.current_player = 3 - self.current_player
        return True

    def check_win(self, r, c):
        player = self.board[r, c]
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            count = 1
            for sign in [1, -1]:
                nr, nc = r + dr * sign, c + dc * sign
                while 0 <= nr < self.board_size and 0 <= nc < self.board_size and self.board[nr, nc] == player:
                    count += 1
                    nr += dr * sign
                    nc += dc * sign
            
            if count >= 5: 
                return True
        return False

    def check_patterns(self, player, length):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.board[r, c] == player:
                    for dr, dc in directions:
                        count = 1
                        nr, nc = r + dr, c + dc
                        while 0 <= nr < self.board_size and 0 <= nc < self.board_size and self.board[nr, nc] == player:
                            count += 1
                            nr += dr
                            nc += dc
                        if count == length:
                            return True
        return False
    
    def count_in_direction(self, r, c, dr, dc, player):
        count = 0
        nr, nc = r + dr, c + dc
        while 0 <= nr < self.board_size and 0 <= nc < self.board_size and self.board[nr, nc] == player:
            count += 1
            nr += dr
            nc += dc
        return count

    def check_overline(self, r, c, player):
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            count += self.count_in_direction(r, c, dr, dc, player)
            count += self.count_in_direction(r, c, -dr, -dc, player)
            if count >= 6:
                return True
        return False

    def get_line_key(self, r, c, dr, dc):
        sr, sc = r, c
        while 0 <= sr - dr < self.board_size and 0 <= sc - dc < self.board_size:
            sr -= dr
            sc -= dc
        return (sr, sc, dr, dc)

    def collect_chain(self, r, c, dr, dc, player):
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
        return (1
                + self.count_in_direction(r, c, dr, dc, player)
                + self.count_in_direction(r, c, -dr, -dc, player))


    def count_open3_total(self, r, c, player, visited=None):
        """ [기존 고속 재귀] (r,c) 착수점을 포함하여 형성되는 열린 3목의 개수를 반환합니다. """
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

    def count_four_total(self, r, c, player, visited=None):
        """ [기존 고속 재귀] (r,c) 착수점을 포함하여 형성되는 4목(열린4/막힌4)의 개수를 반환합니다. """
        if visited is None:
            visited = {'stones': set(), 'lines': set()}

        visited['stones'].add((r, c))
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        four_count = 0

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

            if len(chain) == 4:
                sr, sc = chain[0]
                er, ec = chain[-1]

                is_really_four = True
                for ex_dr, ex_dc, corner in [(-dr, -dc, (sr, sc)), (dr, dc, (er, ec))]:
                    cx, cy = corner[0] + ex_dr, corner[1] + ex_dc
                    if (0 <= cx < self.board_size and 0 <= cy < self.board_size
                            and self.board[cx][cy] == player):
                        is_really_four = False
                        break

                if is_really_four:
                    e1r, e1c = sr - dr, sc - dc
                    e2r, e2c = er + dr, ec + dc
                    open1 = (0 <= e1r < self.board_size and 0 <= e1c < self.board_size
                             and self.board[e1r][e1c] == 0)
                    open2 = (0 <= e2r < self.board_size and 0 <= e2c < self.board_size
                             and self.board[e2r][e2c] == 0)

                    if open1 or open2:
                        visited['lines'].add(dir_key)
                        four_count += 1

            for pr, pc in chain:
                if (pr, pc) != (r, c) and (pr, pc) not in visited['stones']:
                    peer_lkey = self.get_line_key(pr, pc, dr, dc)
                    visited['lines'].add((dr, dc, peer_lkey))
                    four_count += self.count_four_total(pr, pc, player, visited)

        return four_count

    def forbidden(self, r, c, player):
        """ [고속 재귀 연동] 착수 지점에 가상의 돌을 두고, 사슬 탐색 방식으로 금수를 판정합니다. """
        if player != 1:
            return False
        if self.board[r, c] != 0:
            return False
        
        # 가상의 돌 임시 배치
        self.board[r, c] = player  
        
        # 1. 5목이 완성되는 자리는 금수보다 우선하여 승리 처리 (금수 해제)
        if self.check_win(r, c):
            self.board[r, c] = 0
            return False

        # 2. 장일(6목 이상) 금수 체크
        if self.check_overline(r, c, player):
            self.board[r, c] = 0
            return True

        # 3. 고속 재귀 사슬 추적을 통한 3-3 금수 체크
        open3_count = self.count_open3_total(r, c, player)
        if open3_count >= 2:   
            self.board[r, c] = 0  
            return True

        # 4. 고속 재귀 사슬 추적을 통한 4-4 금수 체크
        four_count = self.count_four_total(r, c, player)
        if four_count >= 2:   
            self.board[r, c] = 0  
            return True

        # 금수 아님 원상 복구
        self.board[r, c] = 0  
        return False
    
    def count_open3_board_total(self, player):
        """ 보드 전체를 순회하며 해당 플레이어의 모든 열린 3목 패턴 총합을 반환"""
        total_count = 0
        visited = {'stones': set(), 'lines': set()}
        
        for r in range(self.board_size):
            for c in range(self.board_size):
                # 해당 플레이어의 돌이면서, 아직 방문하지 않은 사슬 그룹의 돌일 때만 탐색
                if self.board[r, c] == player and (r, c) not in visited['stones']:
                    total_count += self.count_open3_total(r, c, player, visited)
        return total_count

    def count_four_board_total(self, player):
        """ 보드 전체를 순회하며 해당 플레이어의 모든 4목(열린4/막힌4) 패턴 총합을 반환"""
        total_count = 0
        visited = {'stones': set(), 'lines': set()}
        
        for r in range(self.board_size):
            for c in range(self.board_size):
                # 해당 플레이어의 돌이면서, 아직 방문하지 않은 사슬 그룹의 돌일 때만 탐색
                if self.board[r, c] == player and (r, c) not in visited['stones']:
                    total_count += self.count_four_total(r, c, player, visited)
        return total_count