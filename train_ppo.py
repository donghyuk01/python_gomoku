import torch
import pygame
import sys
import os
import numpy as np
from engine import OmokEngine
from ppo_agent import PPOAgent, Memory

# --- UI COLORS (Hex-like RGB tuples for a Cyberpunk aesthetic) ---
COLOR_BG = (15, 15, 25)      # Deep Dark Blue/Black
COLOR_BOARD = (40, 40, 60)   # Modern Grid Gray
COLOR_ACCENT = (0, 255, 200) # Cyberpunk Cyan
COLOR_LOSS = (255, 80, 80)   # Soft Red
COLOR_REWARD = (100, 255, 100)# Lime Green
COLOR_TEXT = (220, 220, 220)

def get_shaped_reward(env, player, prev_opp_four, prev_opp_three):
    """
    Reward Shaping: This function gives the AI 'hints' during the game.
    Instead of waiting until the end to get points, the AI gets small rewards 
    for making good patterns (like 3-in-a-row).
    """
    opp = 3 - player
    
    if env.is_over:
        cur4 = env.count_open_four(opp)
        cur3 = env.count_open_three(opp)
        if env.winner == player: 
            return 50.0, cur4,cur3     # 승리 시 (보상, 상태)
        if env.winner == (3 - player): 
            return -50.0, cur4,cur3     # 패배 시 (보상, 상태)
        return 0.0, cur4,cur3          # 무승부 시 (보상, 상태)

    reward = 0.0
    cur4 = env.count_open_four(opp)
    cur3 = env.count_open_three(opp)

    
    if prev_opp_four > cur4:
        reward += 20.0
    if prev_opp_three > cur3:
        reward += 10.0
    # 기존 패턴 보상들
    if env.check_patterns(player, 4): reward += 8.0
    if env.check_patterns(opp, 4): reward -= 15.0
    if env.check_patterns(player, 3): reward += 3.0
    if env.check_patterns(opp, 3): reward -= 5.0

    return reward, cur4,cur3

def train_beast():
    """
    The main training loop with Pygame visualization.
    """
    # --- CONFIGURATION ---
    BOARD_SIZE = 15
    CELL_SIZE = 45
    SIDEBAR_WIDTH = 280
    PADDING = 40
    
    BOARD_SCREEN_SIZE = BOARD_SIZE * CELL_SIZE + PADDING * 2
    SCREEN_WIDTH = BOARD_SCREEN_SIZE + SIDEBAR_WIDTH
    SCREEN_HEIGHT = BOARD_SCREEN_SIZE

    # Initialize Pygame and Fonts
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("BEAST MODE TRAINING")
    
    font_s = pygame.font.SysFont("Segoe UI", 18)
    font_m = pygame.font.SysFont("Segoe UI", 28, bold=True)
    font_l = pygame.font.SysFont("Segoe UI", 45, bold=True)

    # Initialize Engine, AI Agent, and Memory Buffer
    env = OmokEngine(BOARD_SIZE)
    agent = PPOAgent(BOARD_SIZE)
    memory = Memory()
    
    # Training Parameters
    update_timestep = 2000 # Update the AI every 2000 steps
    timestep = 0
    current_loss = 0.0
    last_ep_reward = 0.0
    
    print(f"BEAST MODE TRAINING STARTED ON: {agent.device}")

    # Start training across 100,000 episodes
    for ep in range(1, 100001):
        state = env.reset() # Reset board for a new game
        done = False
        ep_reward_accumulated = 0
        prev_four = 0 
        prev_three = 0
        while not done:
            # Handle Pygame window exit
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

            timestep += 1
            
            # AI selects an action (Move)
            valid_moves = env.get_valid_moves()
            action_idx, logprob = agent.select_action(state, valid_moves)
            
            # Convert flat index (0-99) back to (row, col) coordinates
            r, c = divmod(action_idx, BOARD_SIZE)
            env.make_move(r, c)
            
            # Calculate the reward for this specific move
            last_player = 3 - env.current_player
            step_reward,current_four, current_three = get_shaped_reward(env, last_player, prev_four,prev_three) 
            prev_four = current_four
            prev_three = current_three
            ep_reward_accumulated += step_reward

            # --- RENDER GUI ---
            screen.fill(COLOR_BG)
            
            # Draw the Game Board Grid
            pygame.draw.rect(screen, (25, 25, 35), (PADDING, PADDING, BOARD_SIZE*CELL_SIZE, BOARD_SIZE*CELL_SIZE))
            for i in range(BOARD_SIZE):
                # Vertical and Horizontal lines
                pygame.draw.line(screen, (45, 45, 60), (PADDING + i*CELL_SIZE, PADDING), (PADDING + i*CELL_SIZE, BOARD_SCREEN_SIZE-PADDING))
                pygame.draw.line(screen, (45, 45, 60), (PADDING, PADDING + i*CELL_SIZE), (BOARD_SCREEN_SIZE-PADDING, PADDING + i*CELL_SIZE))

            # Draw Stones (Black with cyan glow for Player 1, White for Player 2)
            for rr in range(BOARD_SIZE):
                for cc in range(BOARD_SIZE):
                    if env.board[rr, cc] == 1:
                        pygame.draw.circle(screen, (0, 0, 0), (PADDING + cc*CELL_SIZE, PADDING + rr*CELL_SIZE), 18)
                        pygame.draw.circle(screen, COLOR_ACCENT, (PADDING + cc*CELL_SIZE, PADDING + rr*CELL_SIZE), 18, 2)
                    elif env.board[rr, cc] == 2:
                        pygame.draw.circle(screen, (255, 255, 255), (PADDING + cc*CELL_SIZE, PADDING + rr*CELL_SIZE), 18)

            # --- SIDEBAR (Live Stats) ---
            sx = BOARD_SCREEN_SIZE + 20
            screen.blit(font_l.render("OMOK", True, COLOR_ACCENT), (sx, 40))
            screen.blit(font_s.render("BEAST MODE ACTIVE", True, (150, 150, 150)), (sx, 95))

            # Helper function to display text stats
            def draw_stat(label, value, y, color):
                screen.blit(font_s.render(label, True, COLOR_TEXT), (sx, y))
                screen.blit(font_m.render(str(value), True, color), (sx, y + 25))

            draw_stat("EPISODE", f"{ep:,}", 150, COLOR_TEXT)
            draw_stat("CURRENT LOSS", f"{current_loss:.6f}", 240, COLOR_LOSS)
            draw_stat("LAST EP REWARD", f"{last_ep_reward:.1f}", 330, COLOR_REWARD)
            
            # Draw Optimization Progress Bar
            pygame.draw.rect(screen, (40, 40, 50), (sx, 450, 220, 10))
            progress = (timestep / update_timestep) * 220
            pygame.draw.rect(screen, COLOR_ACCENT, (sx, 450, progress, 10))
            screen.blit(font_s.render("OPTIMIZATION PROGRESS", True, (100, 100, 100)), (sx, 465))

            pygame.display.flip() # Update the screen display

            # --- MEMORY STORAGE ---
            # Save the experience to the memory buffer for later training
            memory.states.append(torch.FloatTensor(state))
            memory.actions.append(torch.tensor(action_idx))
            memory.logprobs.append(logprob)
            memory.rewards.append(step_reward)
            
            state = env.get_state()
            done = env.is_over
            
            # --- AGENT UPDATE (Learning Step) ---
            # Once enough steps are collected, run the PPO update
            if timestep % update_timestep == 0:
                loss_val = agent.update(memory)
                if loss_val: current_loss = loss_val
                memory.clear() # Reset memory after learning
                timestep = 0
        
        last_ep_reward = ep_reward_accumulated
        
        # Periodic Saving and Console Logging
        if ep % 100 == 0:
            print(f"Ep: {ep:6d} | Loss: {current_loss:.6f} | Reward: {last_ep_reward:.1f}")
            # Save the "Brain" of the AI to a file
            torch.save(agent.policy.state_dict(), "ppo_omok_reward.pth")

if __name__ == "__main__":
    train_beast()