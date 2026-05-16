import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical
from model import PPOModel

"""
torch - 오픈소스 머신러닝 프레임워크
PyTorch의 가장 기본 단위 Tensor(행렬과 비슷)
cpu가 아닌 gpu에서 계산할 수 있음
역할
자동 미분
정답과 예측의 차이를 줄일 수 있음
신경망 설계
데이터 관리
최적화

ppo
이전 정책과 새로운 정책 사이의 폭을 일정 범위내로 제한하여 학습하는 알고리즘
3대 구성요소
actor - critic : 어디에 돌을 둘지 결정하고 얼마나 유리한지 점수 계산
clipping: 새로운 정책이 예전 정책과 너무 많이 차이 나지 않도록 변화율 지정
advantage:  예상했던 결과보다 얼마나 더 좋았나를 따짐
학습 절차
- 데이터 수집: ai가 자기자신과 대국을 하여 상태,행동,보상,확률을 저장
- 계산 : 수집된 데이터를 보고 결과 판단
- 클리핑 업데이트: ppo의 제한선 안에서 안전하게 모델 가중치 수정
- 반복: 위 과정 여러 번 반복
"""
class PPOAgent:
    def __init__(self, board_size, lr=3e-4, gamma=0.99, eps_clip=0.2):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu") #gpu가 있으면 cuda를 사용 아니면 cpu로 학습 cuda : nvidia 그래픽 카드의 병렬처리 능력 
        self.board_size = board_size 
        self.gamma = gamma 
        self.eps_clip = eps_clip
        
        self.policy = PPOModel(board_size).to(self.device) #실제로 학습되는 신경망 매 에포크마다 가중치 업데이트
        self.optimizer = optim.Adam(self.policy.parameters(), lr=lr) # 최적화 알고리즘: 아담 
        self.policy_old = PPOModel(board_size).to(self.device) 
        self.policy_old.load_state_dict(self.policy.state_dict()) 
        self.MseLoss = nn.MSELoss() #평균 오차 계산

    def select_action(self, state, valid_moves):
        state = torch.FloatTensor(state).unsqueeze(0).to(self.device) #넘파이 배열 state를 PyTorch가 계산할 수 있는 실수형 텐서로 변환 unsqueeze: 데이터에 배치(Batch)차원을 추가 여러 데이터를 한꺼번에 처리 to : 데이터를 cpu나 gpu등으로 보냄
        with torch.no_grad():
            probs, _ = self.policy_old(state)
        #모델을 통해 결과만 알고 싶을 때 메모리 아끼고 계산속도 향상 probs에 각 위치에 둘 확률을 반환
        mask = torch.zeros(self.board_size * self.board_size).to(self.device) #판 크기만큼 0으로 가득 찬 텐서를 만든다.
        for m in valid_moves:
            mask[m[0] * self.board_size + m[1]] = 1 
        # 둘 수 있느 ㄴ곳에만 1을 표시
        
        masked_probs = probs.squeeze() * mask #신경망이ㅣ예측한 확률과 마스크를 곱함
        if masked_probs.sum() > 0:
            masked_probs = masked_probs / masked_probs.sum()
        else:
            masked_probs = mask / mask.sum()
        #확률의 총합이 다시 1이 되도록 나누어줌(정규화) - 확률 분포
        dist = Categorical(masked_probs) #계산된 확률을 바탕으로 칸 만들기 (1번칸 30% ~)
        action = dist.sample() #칸에서 확률에 따라 번호 하나를 뽑기 (높은 확률만 뽑는게 아닌 낮은 확률도 가끔)
        return action.item(), dist.log_prob(action) #.item 텐서 형태인 행동 번호를 파이썬 숫자로 변환 , dist.log_prob(action) : 선택한 행동의 로그 확률을 계산
        #ai가 현재 판의 상태를 보고 최선의 한 수를 고르는 단계

    def update(self, memory):
        states = torch.stack(memory.states).to(self.device).detach() #torch.stack : 리스트 안에 흩어져 있는 여러 텐서들을 하나의 Batch로 쌓아 올리기 .detach: 데이터가 기록용이고 당장 학습 대상이 아니라는 것을 명시하고 메모리 보호
        actions = torch.stack(memory.actions).to(self.device).detach()
        logprobs = torch.stack(memory.logprobs).to(self.device).detach()
        rewards = torch.tensor(memory.rewards).to(self.device).detach().float()
        
        if len(rewards) > 1:
            rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-5)
        # 정규화 단계 :  보상 값들을 평균 0, 표준편차1 근처로 맞ㅊ춰서 점수가 너무 크거나 작아서 학습 방해를 막음
        for _ in range(10): #반복학습 epochs ppo의 장점 중 하나 - 한 번 얻은 데이터를 버리지 않고 10번정도 다시 학습
            probs, state_values = self.policy(states)
            dist = Categorical(probs) #확률을 바탕으로 칸 만들기
            new_logprobs = dist.log_prob(actions) #선택한 행동의 로그 확률 계산
            entropy = dist.entropy() #ai의 탐험 정신을 나타내는 수치 
            
            ratios = torch.exp(new_logprobs - logprobs) #새로운 확률/이전확률을 계산 (로그 성질 덕분에 뺄샘 후 exp를 취하면 나눗셈으로 된다) - 예전보다 이 행동을 얼마나 더 선호하게 됬는지르ㄹ 뜻함
            advantages = rewards - state_values.detach().squeeze() # 보상 - 예상 점수 : 예상 점수보다 결과가 얼마나 더 좋았는지
            
            surr1 = ratios * advantages 
            surr2 = torch.clamp(ratios, 1-self.eps_clip, 1+self.eps_clip) * advantages
            # .clamp: ratios가 지정한 범위를 못 벗어나게 지정 - 새로운 정책과 예전 정책이 너무 다르면 학습이 불안정
            loss = -torch.min(surr1, surr2) + 0.5 * self.MseLoss(state_values.squeeze(), rewards) - 0.01 * entropy
            #변환율 작은 것 선택 / 신경망이 예측한 값에서 실제로 확인된 보상을 빼고 제곱하여 평균을 냄 .MseLoss : 판세 예측 증력을 키우기 / entropy : 너무 한 수만 고집하지 않고 다양하게 두기
            self.optimizer.zero_grad() #이전 미분값 초기화
            loss.mean().backward() # 오차를 평균으로 합치고 .backward() : Backpropagation : loss값에서 출발하여 신경망의 입력 방향으로 거꾸러 거슬러 올라감 
            # : 각 가중치에서 조금씩 변했을 때 최종 오차는 얼마나 변할지 계산 - 어느 방향으로 얼마나 수정해야 오차가 줄어드는지에 대한 정보 저장
            self.optimizer.step() #실제 모델 가중치 수정
        
        self.policy_old.load_state_dict(self.policy.state_dict()) # 학습이 끝났으니 policy내용을 policy_old에 복사 : 실력을 기준으로 또 비교하기 위해
        return loss.mean().item()

class Memory:
    def __init__(self):
        self.states, self.actions, self.logprobs, self.rewards = [], [], [], []
    def clear(self):
        self.states.clear(); self.actions.clear(); self.logprobs.clear(); self.rewards.clear()
    # 한 판에서 일어나ㄴ 일들을 잠시 적어두는 저장소