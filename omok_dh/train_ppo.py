import torch
import pygame
import sys
import os
import numpy as np
from engine import OmokEngine
from ppo_agent import PPOAgent, Memory

# --- UI COLORS ---
COLOR_BG = (15, 15, 25)      
COLOR_BOARD = (40, 40, 60)   
COLOR_ACCENT = (0, 255, 200) 
COLOR_LOSS = (255, 80, 80)   
COLOR_REWARD = (100, 255, 100)
COLOR_TEXT = (220, 220, 220)

def get_shaped_reward(env, last_player, row, col, opp_4_before, opp_3_before, my_4_before, my_3_before, is_first_move):
    """
    [개선안] 첫 수 예외처리를 추가하여 AI의 보상 왜곡을 방지합니다.
    """
    opp = 3 - last_player
    
    # 1. 게임 종료 시 강력한 보상/페널티
    if env.is_over:
        if env.winner == last_player: 
            return 150.0  
        if env.winner == opp: 
            return -150.0 
        return 0.0

    reward = 0.0

    # 2. 첫 번째 수는 판 중앙 부근에 두면 보상을 줌 (우주 관광 방지)
    if is_first_move:
        center = env.board_size // 2
        distance_from_center = abs(row - center) + abs(col - center)
        if distance_from_center <= 2:
            reward += 10.0
        else:
            reward -= 5.0
    else:
        # 3. 이후 돌들은 무조건 붙여 두도록 강력히 유도
        adjacent_stone_found = False
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < env.board_size and 0 <= nc < env.board_size:
                    if env.board[nr, nc] != 0:
                        adjacent_stone_found = True
                        break
            if adjacent_stone_found: break

        if adjacent_stone_found:
            reward += 10.0  # 밀집 지역 착수 가산점 상향
        else:
            reward -= 15.0  # 뜬금없는 곳에 낙하산 투하 시 강력한 페널티

    # 4. 판 전체 상태 변화량 실시간 추적
    opp_4_after = env.count_four_board_total(opp)
    opp_3_after = env.count_open3_board_total(opp)
    my_4_after = env.count_four_board_total(last_player)
    my_3_after = env.count_open3_board_total(last_player)

    
    if opp_4_before > opp_4_after: reward += 80.0   
    if opp_3_before > opp_3_after: reward += 50.0   

    
    if opp_4_after > opp_4_before: reward -= 120.0  
    if opp_3_after > opp_3_before: reward -= 50.0   

    # 공격 보상
    if my_4_after > my_4_before: reward += 25.0   # 30 → 25
    if my_3_after > my_3_before: reward += 12.0 

    return reward

def get_adjacent_valid_moves(env, valid_moves):
    """
    [핵심 추가 알고리즘] 
    판 위에 돌이 하나라도 있다면, 빈칸 중 '기존 돌의 8방향 이내'인 칸들만 필터링하여 반환합니다.
    이를 통해 AI의 무작위 행동 반경을 기존 돌 주변으로 강제 제한(마스킹)합니다.
    """
    # 바둑판이 완전히 비어있다면 전체 유효 장소를 반환
    if not np.any(env.board != 0):
        return valid_moves

    adjacent_moves = []
    for r, c in valid_moves:
        is_adjacent = False
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < env.board_size and 0 <= nc < env.board_size:
                    if env.board[nr, nc] != 0:
                        is_adjacent = True
                        break
            if is_adjacent: break
        
        if is_adjacent:
            adjacent_moves.append([r, c])
            
    # 만약 주변에 둘 수 있는 자리가 규칙(금수 등)으로 인해 하나도 없다면 예외적으로 전체에서 선택
    if len(adjacent_moves) == 0:
        return valid_moves
        
    return np.array(adjacent_moves)

def train_beast():
    BOARD_SIZE = 15
    CELL_SIZE = 45
    SIDEBAR_WIDTH = 280
    PADDING = 40
    
    BOARD_SCREEN_SIZE = BOARD_SIZE * CELL_SIZE + PADDING * 2
    SCREEN_WIDTH = BOARD_SCREEN_SIZE + SIDEBAR_WIDTH
    SCREEN_HEIGHT = BOARD_SCREEN_SIZE

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("BEAST MODE TRAINING")
    
    font_s = pygame.font.SysFont("Segoe UI", 18)
    font_m = pygame.font.SysFont("Segoe UI", 28, bold=True)
    font_l = pygame.font.SysFont("Segoe UI", 45, bold=True)

    env = OmokEngine(BOARD_SIZE)
    agent = PPOAgent(BOARD_SIZE)
    memory = Memory()
    
    update_timestep = 2000 
    timestep = 0
    current_loss = 0.0  
    last_ep_reward = 0.0
    
    print(f"BEAST MODE TRAINING STARTED ON: {agent.device}")

    for ep in range(1, 100001):
        state = env.reset() 
        done = False
        ep_reward_accumulated = 0
        
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

            timestep += 1
            player_to_move = env.current_player
            opp = 3 - player_to_move
            
            opp_4_before = env.count_four_board_total(opp)
            opp_3_before = env.count_open3_board_total(opp)
            my_4_before = env.count_four_board_total(player_to_move)
            my_3_before = env.count_open3_board_total(player_to_move)

            # 판에 최초로 돌이 올라가는 시점인지 체크
            is_first_move = not np.any(env.board != 0)

            # [핵심 변경] 전체 유효 구역이 아닌, '돌 주변 인접 구역'으로 액션 마스크를 타이트하게 조입니다.
            all_valid_moves = env.get_valid_moves()
            focused_moves = get_adjacent_valid_moves(env, all_valid_moves)
            
            # 좁혀진 탐색 구역(focused_moves)을 전달하여 행동 선택
            action_idx, logprob = agent.select_action(state, focused_moves)
            
            r, c = divmod(action_idx, BOARD_SIZE)
            env.make_move(r, c)
            
            last_player = player_to_move 
            step_reward = get_shaped_reward(
                env, last_player, r, c,
                opp_4_before, opp_3_before, 
                my_4_before, my_3_before,
                is_first_move
            ) 
            
            ep_reward_accumulated += step_reward

            # --- RENDER GUI ---
            screen.fill(COLOR_BG)
            pygame.draw.rect(screen, (25, 25, 35), (PADDING, PADDING, BOARD_SIZE*CELL_SIZE, BOARD_SIZE*CELL_SIZE))
            for i in range(BOARD_SIZE):
                pygame.draw.line(screen, (45, 45, 60), (PADDING + i*CELL_SIZE, PADDING), (PADDING + i*CELL_SIZE, BOARD_SCREEN_SIZE-PADDING))
                pygame.draw.line(screen, (45, 45, 60), (PADDING, PADDING + i*CELL_SIZE), (BOARD_SCREEN_SIZE-PADDING, PADDING + i*CELL_SIZE))

            for rr in range(BOARD_SIZE):
                for cc in range(BOARD_SIZE):
                    if env.board[rr, cc] == 1:
                        pygame.draw.circle(screen, (0, 0, 0), (PADDING + cc*CELL_SIZE, PADDING + rr*CELL_SIZE), 18)
                        pygame.draw.circle(screen, COLOR_ACCENT, (PADDING + cc*CELL_SIZE, PADDING + rr*CELL_SIZE), 18, 2)
                    elif env.board[rr, cc] == 2:
                        pygame.draw.circle(screen, (255, 255, 255), (PADDING + cc*CELL_SIZE, PADDING + rr*CELL_SIZE), 18)

            # --- SIDEBAR ---
            sx = BOARD_SCREEN_SIZE + 20
            screen.blit(font_l.render("OMOK", True, COLOR_ACCENT), (sx, 40))
            screen.blit(font_s.render("BEAST MODE ACTIVE", True, (150, 150, 150)), (sx, 95))

            def draw_stat(label, value, y, color):
                screen.blit(font_s.render(label, True, COLOR_TEXT), (sx, y))
                screen.blit(font_m.render(str(value), True, color), (sx, y + 25))

            draw_stat("EPISODE", f"{ep:,}", 150, COLOR_TEXT)
            draw_stat("CURRENT LOSS", f"{current_loss:.6f}", 240, COLOR_LOSS)
            draw_stat("LAST EP REWARD", f"{last_ep_reward:.1f}", 330, COLOR_REWARD)
            
            pygame.draw.rect(screen, (40, 40, 50), (sx, 450, 220, 10))
            progress = (timestep / update_timestep) * 220
            pygame.draw.rect(screen, COLOR_ACCENT, (sx, 450, progress, 10))
            screen.blit(font_s.render("OPTIMIZATION PROGRESS", True, (100, 100, 100)), (sx, 465))

            pygame.display.flip()

            # --- MEMORY STORAGE ---
            memory.states.append(torch.FloatTensor(state))
            memory.actions.append(torch.tensor(action_idx))
            memory.logprobs.append(logprob)
            memory.rewards.append(step_reward)
            
            state = env.get_state()
            done = env.is_over
            
            # --- AGENT UPDATE ---
            if timestep % update_timestep == 0:
                loss_val = agent.update(memory)
                if loss_val: current_loss = loss_val
                memory.clear() 
                timestep = 0
        
        last_ep_reward = ep_reward_accumulated
        
        if ep % 100 == 0:
            print(f"Ep: {ep:6d} | Loss: {current_loss:.6f} | Reward: {last_ep_reward:.1f}")
            torch.save(agent.policy.state_dict(), "ppo_omok_reward.pth")

if __name__ == "__main__":
    train_beast()