import torch
import torch.nn as nn
import torch.nn.functional as F
#torch nn은 신경망을 구축하는데 필요한 모든 구성요소 제공
class PPOModel(nn.Module):
    def __init__(self, board_size):
        """
        Initialize the Actor-Critic Neural Network for PPO.
        The network uses Convolutional layers to 'see' the board patterns
        and Linear layers to make decisions.
        """
        super(PPOModel, self).__init__()
        self.board_size = board_size
        
        # --- CONVOLUTIONAL BLOCK (The 'Eyes' of the AI) ---
        # These layers extract spatial features (like lines of 3 or 4 stones)
        self.conv_block = nn.Sequential(
            # First layer: Detects basic patterns (1 input channel -> 64 feature maps)
            nn.Conv2d(2, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            #패턴 찾고, 돌이 있는지 없는지에대한 정보 부각
            # Second layer: Deepens the understanding (64 -> 128 feature maps)
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            
            # Third layer: Solidifies pattern recognition (128 -> 128 feature maps)
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.ReLU()
        )
        
        # Calculate the total number of features after flattening the 2D grid
        self.flatten_size = 128 * board_size * board_size
        
        # --- ACTOR HEAD (The Decision Maker) ---
        # Suggests where to move next by outputting a score for every cell on the board
        self.actor = nn.Sequential(
            nn.Linear(self.flatten_size, 256), #3차원 패턴 데이터중에서 256개 핵심 특징들 요약
            nn.ReLU(), #중요한 특징 강조, 불필요한 정보 제거
            # Output size is board_size^2 (one value for each possible move)
            nn.Linear(256, board_size * board_size)
            #256개 정보를 보고 보드 칸 각각 점수 부여
        )
        
        # --- CRITIC HEAD (The Judge) ---
        # Predicts the 'Value' of the current board state (how likely is Player 1 to win?)
        self.critic = nn.Sequential(
            nn.Linear(self.flatten_size, 256),
            nn.ReLU(),
            # Output is a single number representing the state value
            nn.Linear(256, 1)
            #수많은 정보를 하나의 숫자로 압축
            #자신이 둔 수가 실제로 좋은 수인지 판단
        )

    def forward(self, x):
        """
        The forward pass: How data flows through the network.
        :param x: The input board state (Tensor)
        :return: Action probabilities and State Value
        """
        # 1. Pass through convolutional layers to extract features
        x = self.conv_block(x)
        #패턴 읽기

        # 2. Flatten the 3D feature map into a 1D vector for the linear layers
        x = x.view(x.size(0), -1) 
        #1차원으로 펼치기

        # 3. Actor: Generate 'logits' (raw scores) and convert to probabilities using Softmax
        logits = self.actor(x) #배치할 위치
        probs = F.softmax(logits, dim=-1) # All probabilities will sum to 1.0
        #확률 분포 생성 어디에 두는 것이 몇% 확률로 조흔가를 계산

        # 4. Critic: Generate a single value estimate for the current state
        value = self.critic(x) #판단
        
        return probs, value #추천확률, 현재상태가치 반환
    
    