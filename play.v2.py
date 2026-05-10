import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import pygame
import sys
import numpy as np
from engine import OmokEngine  # 개선된 2번 엔진
from model import PPOModel    # Conv2d(2, ...) 가 적용된 모델

# --- UI CONSTANTS ---
BOARD_SIZE = 15  
CELL_SIZE = 40
SIDEBAR_WIDTH = 220
PADDING = 40
SCREEN_WIDTH = (BOARD_SIZE * CELL_SIZE) + PADDING + SIDEBAR_WIDTH
SCREEN_HEIGHT = (BOARD_SIZE * CELL_SIZE) + PADDING
COLOR_BG = (28, 28, 38)
COLOR_SIDEBAR = (35, 35, 50)
COLOR_BOARD = (210, 170, 110)
COLOR_GRID = (45, 45, 55)
COLOR_ACCENT = (0, 255, 200)

class ModernOmok:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("OMOK AI - 15x15 Compact")
        # 폰트 사이즈도 창 크기에 맞춰 약간 줄임
        self.font_m = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font_s = pygame.font.SysFont("Segoe UI", 16)
        self.clock = pygame.time.Clock()
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # 모델 초기화 (입력 채널 2개가 적용된 PPOModel)
        self.model = PPOModel(BOARD_SIZE).to(self.device)
        self.load_model()
        self.reset_game()

    def load_model(self):
        model_path = "ppo_omok_reward.pth"
        if os.path.exists(model_path):
            try:
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
                self.model.eval()
                self.model_status = "AI READY"
            except:
                self.model_status = "MODEL ERROR"
        else:
            self.model_status = "RANDOM MODE"

    def reset_game(self):
        self.env = OmokEngine(BOARD_SIZE)
        self.last_move = None

    def draw_glass_rect(self, rect, color, alpha):
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        s.fill((*color, alpha))
        self.screen.blit(s, (rect.x, rect.y))

    def draw(self):
        self.screen.fill(COLOR_BG)
        
        # --- DRAW SIDEBAR ---
        pygame.draw.rect(self.screen, COLOR_SIDEBAR, (SCREEN_WIDTH - SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT))
        self.screen.blit(self.font_m.render("OMOK AI", True, COLOR_ACCENT), (SCREEN_WIDTH - SIDEBAR_WIDTH + 20, 30))
        self.screen.blit(self.font_s.render(f"STATUS: {self.model_status}", True, (150, 150, 150)), (SCREEN_WIDTH - SIDEBAR_WIDTH + 20, 65))
        
        turn_txt = "YOUR TURN (BLACK)" if self.env.current_player == 1 else "AI THINKING... (WHITE)"
        turn_clr = (255, 255, 255) if self.env.current_player == 1 else COLOR_ACCENT
        self.screen.blit(self.font_s.render(turn_txt, True, turn_clr), (SCREEN_WIDTH - SIDEBAR_WIDTH + 30, 150))
        
        # 흑돌 전용 안내 (3-3 금지)
        if self.env.current_player == 1:
            self.screen.blit(self.font_s.render("RULE: NO 3-3 FOR BLACK", True, (200, 100, 100)), (SCREEN_WIDTH - SIDEBAR_WIDTH + 30, 180))

        self.screen.blit(self.font_s.render("PRESS 'R' TO RESTART", True, (100, 100, 100)), (SCREEN_WIDTH - SIDEBAR_WIDTH + 30, SCREEN_HEIGHT - 60))

        # --- DRAW BOARD ---
        board_rect = pygame.Rect(PADDING//2, PADDING//2, (BOARD_SIZE-1)*CELL_SIZE + PADDING, (BOARD_SIZE-1)*CELL_SIZE + PADDING)
        pygame.draw.rect(self.screen, COLOR_BOARD, board_rect, border_radius=8)
        
        for i in range(BOARD_SIZE):
            # 가로선
            pygame.draw.line(self.screen, COLOR_GRID, 
                             (PADDING, PADDING + i*CELL_SIZE), 
                             (PADDING + (BOARD_SIZE-1)*CELL_SIZE, PADDING + i*CELL_SIZE), 1)
            # 세로선
            pygame.draw.line(self.screen, COLOR_GRID, 
                             (PADDING + i*CELL_SIZE, PADDING), 
                             (PADDING + i*CELL_SIZE, PADDING + (BOARD_SIZE-1)*CELL_SIZE), 1)

        # --- DRAW STONES ---
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                pos = (PADDING + c * CELL_SIZE, PADDING + r * CELL_SIZE)
                if self.env.board[r, c] == 1: # Black
                    pygame.draw.circle(self.screen, (10, 10, 15), pos, 16)
                    pygame.draw.circle(self.screen, (60, 60, 70), (pos[0]-4, pos[1]-4), 4)
                elif self.env.board[r, c] == 2: # White
                    pygame.draw.circle(self.screen, (240, 240, 250), pos, 16)
                    pygame.draw.circle(self.screen, (255, 255, 255), (pos[0]-4, pos[1]-4), 5)

                # 금수 자리 표시 (빈칸이면서 흑 금수인 경우)
                elif self.env.board[r, c] == 0 and self.env.forbidden(r, c, 1):
                    # X 표시
                    x1 = pos[0] - 10
                    y1 = pos[1] - 10
                    x2 = pos[0] + 10
                    y2 = pos[1] + 10
                    pygame.draw.line(self.screen, (200, 50, 50), (x1, y1), (x2, y2), 2)
                    pygame.draw.line(self.screen, (200, 50, 50), (x1, y2), (x2, y1), 2)


        # --- GAME OVER OVERLAY ---
        if self.env.is_over:
            self.draw_glass_rect(pygame.Rect(0,0, SCREEN_WIDTH, SCREEN_HEIGHT), (0,0,0), 180)
            msg = "VICTORY!" if self.env.winner == 1 else "DEFEAT!" if self.env.winner == 2 else "DRAW"
            color = (0, 255, 150) if self.env.winner == 1 else (255, 80, 80)
            txt = self.font_m.render(msg, True, color)
            self.screen.blit(txt, (SCREEN_WIDTH//2 - SIDEBAR_WIDTH//2 - txt.get_width()//2, SCREEN_HEIGHT//2 - 20))

    def run(self):
        while True:
            self.draw()
            pygame.display.flip()
            
            if not self.env.is_over:
                if self.env.current_player == 1: # Human (Black)
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                        if event.type == pygame.KEYDOWN and event.key == pygame.K_r: self.reset_game()
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            mx, my = pygame.mouse.get_pos()
                            # 클릭 좌표 계산 개선
                            c = int(round((mx - PADDING) / CELL_SIZE))
                            r = int(round((my - PADDING) / CELL_SIZE))
                            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                                # 1. 빈칸 체크
                                if self.env.board[r, c] != 0:
                                    continue

                                # 2. 흑 금수 체크 (UI에서 먼저 차단)
                                if self.env.current_player == 1 and self.env.forbidden(r, c, 1):
                                    continue

                                # 3. 정상 착수
                                if self.env.make_move(r, c):
                                    self.last_move = (r, c)
                
                else: # AI (White)
                    pygame.time.wait(500)
                    # 1. 현재 상태 가져오기 (이미 2채널 float32 반환됨)
                    state_np = self.env.get_state() 
                    state_tensor = torch.from_numpy(state_np).unsqueeze(0).to(self.device)
                    
                    with torch.no_grad():
                        probs, _ = self.model(state_tensor)
                    
                    # 2. 유효한 수(금수 제외) 마스킹
                    mask = torch.zeros(BOARD_SIZE * BOARD_SIZE).to(self.device)
                    valid_moves = self.env.get_valid_moves()
                    
                    if len(valid_moves) > 0:
                        for m in valid_moves:
                            mask[m[0] * BOARD_SIZE + m[1]] = 1
                        
                        # 확률 분포에 마스크 적용
                        probs = probs.squeeze() * mask
                        
                        if probs.sum() > 0:
                            action = torch.argmax(probs).item()
                        else:
                            # 확률이 모두 0이면 랜덤하게 유효한 수 선택
                            idx = np.random.choice(len(valid_moves))
                            action = valid_moves[idx][0] * BOARD_SIZE + valid_moves[idx][1]
                        
                        r, c = divmod(action, BOARD_SIZE)
                        self.env.make_move(r, c)
                        self.last_move = (r, c)
            
            else: # Game Over 상태
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_r: self.reset_game()
            
            self.clock.tick(60)

if __name__ == "__main__":
    ModernOmok().run()