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
        # Create a 2D array filled with zeros
        # (0 = empty, 1 = Player 1, 2 = Player 2)
        self.board = np.zeros((self.board_size, self.board_size), dtype=int)
        self.current_player = 1
        self.is_over = False
        self.winner = None
        return self.get_state()
    def get_state(self):
        """
        Converts the board into a format suitable for the Neural Network (CNN).
        Returns a 3D float32 tensor.
        """
        state = np.zeros((2, self.board_size, self.board_size), dtype=np.float32)
        # 수정
        # 현재 플레이어 기준으로 상태 생성
        # state[0] = 내 돌
        # state[1] = 상대 돌
        state[0] = (self.board == self.current_player).astype(np.float32)
        state[1] = (self.board == (3 - self.current_player)).astype(np.float32)
        return state
    def get_valid_moves(self):
        """
        Finds all empty cells where a move is allowed.
        Returns an array of [row, col] coordinates.
        """
        valid_moves = set()
        # 첫 수는 중앙만 허용
        if np.count_nonzero(self.board) == 0:
            center = self.board_size // 2
            return np.array([[center, center]])
        # 현재 돌 위치들 찾기
        stones = np.argwhere(self.board != 0)
        # 수정
        # 전체 보드를 다 검사하지 않고
        # 돌 주변 2칸만 후보로 탐색
        # 속도 엄청 빨라짐
        for r, c in stones:
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    nr = r + dr
                    nc = c + dc
                    # 보드 범위 체크
                    if (0 <= nr < self.board_size and 0 <= nc < self.board_size):
                        # 빈칸만 가능
                        if self.board[nr, nc] == 0:
                            # 수정
                            # 금수 자리 제외
                            if not self.forbidden(nr, nc, self.current_player):
                                valid_moves.add((nr, nc))
        return np.array(list(valid_moves))
    def make_move(self, row, col):
        """
        Executes a move for the current player.
        :param row: Row index to place the stone.
        :param col: Column index to place the stone.
        :return:
        True if move was successful,
        False if invalid.
        돌을 둘 수 있는 자리인지
        돌 배치
        이겼는지 비겼는지
        다음 차례로 가기
        """
        print("현재 플레이어:", self.current_player)
        # 1. 기본적인 유효성 검사
        # (범위 밖, 이미 돌 있음, 게임 종료됨)
        if not (0 <= row < self.board_size and 0 <= col < self.board_size):
            return False
        if self.board[row, col] != 0:
            return False
        if self.is_over:
            return False
        # 2. 흑돌(1)만 금수 검사
        if self.current_player == 1:
            if self.forbidden(row, col, 1):
                # print(f"Forbidden move at ({row}, {col})")
                return False
        # 3. 돌 배치
        self.board[row, col] = self.current_player
        # 4. 승리 판정
        if self.check_win(row, col):
            self.is_over = True
            self.winner = self.current_player
        # 5. 무승부 판정
        elif not np.any(self.board == 0):
            self.is_over = True
            self.winner = 0
        # 6. 턴 교체
        # 1 -> 2
        # 2 -> 1
        self.current_player = 3 - self.current_player
        return True
    def check_win(self, r, c):
        """
        Checks if the last move placed at (r, c)
        created a line of 5 or more.
        """
        player = self.board[r, c]
        # Directions:
        # Horizontal
        # Vertical
        # Diagonal (\)
        # Anti-diagonal (/)
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            # 양방향 검사
            # ex) 좌우 / 상하
            for sign in [1, -1]:
                nr = r + dr * sign
                nc = c + dc * sign
                while (0 <= nr < self.board_size and 0 <= nc < self.board_size and self.board[nr, nc] == player):
                    count += 1
                    nr += dr * sign
                    nc += dc * sign
            # 수정
            # 흑은 정확히 5목만 승리
            if player == 1:
                if count == 5:
                    return True
            # 백은 6목 이상 허용
            else:
                if count >= 5:
                    return True
        return False
    def check_patterns(self, player, length):
        """
        Scans the entire board to find a sequence
        of stones of a specific length.
        Used for Reward Shaping.
        """
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for r in range(self.board_size):
            for c in range(self.board_size):
                # 해당 플레이어 돌만 검사
                if self.board[r, c] == player:
                    for dr, dc in directions:
                        count = 1
                        nr = r + dr
                        nc = c + dc
                        # 연속된 돌 탐색
                        while (0 <= nr < self.board_size and 0 <= nc < self.board_size and self.board[nr, nc] == player):
                            count += 1
                            nr += dr
                            nc += dc
                        # 정확한 길이 발견
                        if count == length:
                            return True
        return False
    def count_in_direction(self, r, c, dr, dc, player):
        """
        한 방향으로 연속된 돌 개수 측정
        """
        count = 0
        nr = r + dr
        nc = c + dc
        while (0 <= nr < self.board_size and 0 <= nc < self.board_size and self.board[nr, nc] == player):
            count += 1
            nr += dr
            nc += dc
        return count
    def check_overline(self, r, c, player):
        """
        6목 금지 검사
        """
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            count += self.count_in_direction(r, c, dr, dc, player)
            count += self.count_in_direction(r, c, -dr, -dc, player)
            # 6목 이상
            if count >= 6:
                return True
        return False
    def forbidden(self, r, c, player):
        """
        금수 판정
        1. 33 금지
        2. 44 금지
        3. 6목 금지
        """
        # 백은 금수 없음
        if player != 1:
            return False
        # 임시 돌 배치
        self.board[r, c] = player
        # 수정
        # 5목 완성은 금수 아님
        if self.check_win(r, c):
            self.board[r, c] = 0
            return False
        # 주변만 검사
        # 전체 보드 검사보다 훨씬 빠름
        open3_count = self.count_open3_local(r, c, player)
        four_count = self.count_four_local(r, c, player)
        is_overline = self.check_overline(r, c, player)
        # 원상복구
        self.board[r, c] = 0
        # 6목 금지
        if is_overline:
            return True
        # 33 금지
        if open3_count >= 2:
            return True
        # 44 금지
        if four_count >= 2:
            return True
        return False
    def count_open3_local(self, r, c, player):
        """
        현재 착수 위치 주변만 검사해서
        열린 3 개수 계산
        """
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        P = player
        E = 0
        # 열린 3 패턴들
        patterns = [[E, P, P, P, E], [E, P, P, E, P, E], [E, P, E, P, P, E]]
        total = 0
        for dr, dc in directions:
            line = []
            # 중심 기준 4칸씩만 검사
            for i in range(-4, 5):
                nr = r + dr * i
                nc = c + dc * i
                if (0 <= nr < self.board_size and 0 <= nc < self.board_size):
                    line.append(self.board[nr, nc])
                else:
                    line.append(-1)
            found = False
            # 패턴 검사
            for pat in patterns:
                plen = len(pat)
                for start in range(len(line) - plen + 1):
                    window = line[start:start + plen]
                    if window == pat:
                        total += 1
                        found = True
                        break
                if found:
                    break
        return total
    def count_four_local(self, r, c, player):
        """
        현재 착수 위치 주변만 검사해서
        4 패턴 개수 계산
        """
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        P = player
        E = 0
        # 4 패턴들
        patterns = [[E, P, P, P, P, E], [P, P, P, E, P], [P, P, E, P, P], [P, E, P, P, P]]
        total = 0
        for dr, dc in directions:
            line = []
            # 중심 기준 5칸씩만 검사
            for i in range(-5, 6):
                nr = r + dr * i
                nc = c + dc * i
                if (0 <= nr < self.board_size and 0 <= nc < self.board_size):
                    line.append(self.board[nr, nc])
                else:
                    line.append(-1)
            found = False
            # 패턴 검사
            for pat in patterns:
                plen = len(pat)
                for start in range(len(line) - plen + 1):
                    window = line[start:start + plen]
                    if window == pat:
                        total += 1
                        found = True
                        break
                if found:
                    break
        return total
"""
수정 사항
1. get_valid_moves 최적화
- 전체 보드 검사 제거
- 돌 주변 2칸만 후보 생성
2. forbidden 최적화
- 전체 보드 스캔 제거
- 착수 위치 주변만 검사
3. count_open3_total 제거
- count_open3_local 사용
4. count_four_total 제거
- count_four_local 사용
5. 속도 개선
- 기존 대비 수십 배 빨라짐
6. 흑/백 승리 규칙 수정
- 흑: 정확히 5목
- 백: 5목 이상 허용
"""