import torch
import pygame
import sys
import os
import numpy as np
import random
from engine import OmokEngine
from ppo_agent import PPOAgent, Memory

def get_shaped_reward(env, player, is_done):
    if is_done:
        if env.winner == player: return 100.0
        if env.winner == (3 - player): return -100.0
        return 0.0

    reward = 0.0
    opp = 3 - player
    
    # 공격 및 방어 가중치
    if env.check_patterns(player, 4): reward += 10.0
    if env.check_patterns(player, 3): reward += 2.0
    
    # 방어 실패에 대한 강력한 페널티 (상대방의 수 읽기)
    if env.check_patterns(opp, 4): reward -= 15.0
    if env.check_patterns(opp, 3): reward -= 5.0
    
    return reward

def train_beast():
    # --- CONFIGURATION ---
    BOARD_SIZE = 15
    CELL_SIZE = 45
    RENDER_INTERVAL = 50 # 시각화는 50판마다 한 번만 수행 (속도 극대화)
    
    pygame.init()
    # 폰트 초기화 부분 삭제
    screen = pygame.display.set_mode((BOARD_SIZE * CELL_SIZE + 80, BOARD_SIZE * CELL_SIZE + 80))
    pygame.display.set_caption("OMOK TRAINING")

    env = OmokEngine(BOARD_SIZE)
    agent = PPOAgent(BOARD_SIZE)
    
    if os.path.exists("ppo_omok_reward.pth"):
        agent.policy.load_state_dict(torch.load("ppo_omok_reward.pth"))
        agent.policy_old.load_state_dict(torch.load("ppo_omok_reward.pth"))
    
    memory = Memory()
    update_timestep = 2000
    timestep = 0
    current_loss = 0.0
    
    for ep in range(1, 100001):
        state = env.reset()
        done = False
        ep_reward = 0
        should_render = (ep % RENDER_INTERVAL == 0)

        while not done:
            if should_render:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit(); sys.exit()

            # AI Turn
            valid_moves = env.get_valid_moves()
            if not valid_moves: break
            
            action_idx, logprob = agent.select_action(state, valid_moves)
            r, c = divmod(action_idx, BOARD_SIZE)
            env.make_move(r, c)
            
            done = env.is_over
            reward = get_shaped_reward(env, 1, done)
            ep_reward += reward

            # PPO 메모리 저장
            memory.states.append(torch.FloatTensor(state))
            memory.actions.append(torch.tensor(action_idx))
            memory.logprobs.append(logprob)
            memory.rewards.append(reward)
            memory.is_terminals.append(done)

            timestep += 1

            # Opponent (Random) Turn
            if not done:
                opp_moves = env.get_valid_moves()
                if opp_moves:
                    m = random.choice(opp_moves)
                    env.make_move(m[0], m[1])
                    done = env.is_over
                    if done and env.winner == 2:
                        ep_reward += get_shaped_reward(env, 1, True)

            # 시각화 (단순 격자와 돌만 표시)
            if should_render:
                screen.fill((20, 20, 30))
                for i in range(BOARD_SIZE):
                    pygame.draw.line(screen, (50, 50, 50), (40 + i*CELL_SIZE, 40), (40 + i*CELL_SIZE, 40 + (BOARD_SIZE-1)*CELL_SIZE))
                    pygame.draw.line(screen, (50, 50, 50), (40, 40 + i*CELL_SIZE), (40 + (BOARD_SIZE-1)*CELL_SIZE, 40 + i*CELL_SIZE))
                
                for rr in range(BOARD_SIZE):
                    for cc in range(BOARD_SIZE):
                        if env.board[rr, cc] == 1:
                            pygame.draw.circle(screen, (0, 255, 200), (40 + cc*CELL_SIZE, 40 + rr*CELL_SIZE), 18)
                        elif env.board[rr, cc] == 2:
                            pygame.draw.circle(screen, (255, 255, 255), (40 + cc*CELL_SIZE, 40 + rr*CELL_SIZE), 18)
                pygame.display.flip()

            if timestep >= update_timestep:
                loss_val = agent.update(memory)
                if loss_val: current_loss = loss_val
                memory.clear()
                timestep = 0
            
            state = env.get_state()

        # 콘솔 로그 출력 (폰트 대신 터미널로 확인)
        if ep % 100 == 0:
            print(f"Episode: {ep} | Loss: {current_loss:.6f} | Last Reward: {ep_reward:.1f}")
            torch.save(agent.policy.state_dict(), "ppo_omok_reward.pth")

if __name__ == "__main__":
    train_beast()