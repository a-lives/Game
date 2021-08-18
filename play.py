import torch
from torch import nn
import pyautogui as ag
import time
from utils import get_game_state, getimg,getscore,totensor,preprocess
import numpy as np

SEQ_LEN = 5
TIME_WAIT = 0.01
LR = 1e-3
PUNISH = 0.1

LT = time.time()
NT = 0

class QPred(nn.Module):
    def __init__(self):
        super(QPred,self).__init__()
        self.conv1 = self.add_CBL(3,32)                 #->(32,450,450)
        self.conv2 = self.add_CBL(32,64)                #->(64,225,225)
        self.conv3 = self.add_CBL(64,128)               #->(128,113,113)
        self.conv4 = self.add_CBL(128,128)              #->(128,57,57)
        self.pred = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128*57*57,3),
            nn.ELU()
        )
        
    def add_CBL(self,input,output,kernel_size=3,stride=2):
        padding = int((kernel_size-1)/2)
        layer = nn.Sequential(
            nn.Conv2d(input,output,kernel_size,stride,padding),
            nn.BatchNorm2d(output),
            nn.LeakyReLU()
        )
        return layer
    
    def forward(self,x):
        x = torch.add(torch.add(torch.add(torch.add(x[0][0]*0.1,x[0][1]*0.2),x[0][2]*0.3),x[0][3]*0.4),x[0][4]*0.5)
        x = torch.stack([x])
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.pred(x)
        x = x + 1
        return x
    
    
class Net:
    def __init__(self,load=True):
        self.predictor = QPred()
        if load:
            self.predictor.load_state_dict(torch.load("params.pkl"))
        self.optimizer = torch.optim.Adam(self.predictor.parameters(),lr=LR)
        self.loss_func = nn.MSELoss()
        self.score = []
        self.timepunish = time.time()
        
    def get_scene(self):
        scene = []
        for _ in range(SEQ_LEN):
            time.sleep(TIME_WAIT)
            img = totensor(preprocess(getimg()))
            scene.append(img)
        return torch.stack([torch.stack(scene),])
        
    def play(self):
        global NT,LT
        scene = self.get_scene()
        pred = self.predictor(scene)
        print(pred)
        if torch.sum(pred) == 0:
            action = torch.randint(0,3,(1,)).item()
        else:
            action = torch.multinomial(pred,1).item()
        value = pred[0][action]
        # print(pred,action,value)
        """ 
        action: 0,1,2 分别为    左转，右转，保持
        """
        self.score.append(value)
        if action == 0:
            ag.write(["left"])
            print("left")
        elif action == 1:
            ag.write(["right"])
            print("right")
        elif action == 2:
            print("None")
        
    def learn(self):
        real_score = getscore() / (time.time() - self.timepunish)*PUNISH
        pred_score = torch.sum(torch.stack(self.score))
        self.optimizer.zero_grad()
        loss = self.loss_func(pred_score,real_score)
        loss.backward()
        self.optimizer.step()
        
        for p in self.predictor.parameters():
            p.data.clamp_(-1,1)
        
        self.score = []
        self.timeout = time.time()
        
    def save(self): 
        torch.save(self.predictor.state_dict(),"params.pkl")
        
    def learn_by_people(self):
        pass
    

def train(bouts=100):
    net = Net(load=False)
    for i in range(bouts):
        while 1:
            state = get_game_state()
            if state == 0:
                ag.write([" "])
                print("GAME START")
            elif state == 1:
                net.play()
            else:
                print("START LEARN")
                net.learn()
                print("END LEARN")
                ag.write([" "])
                print("GAME RESTART-----------------")
    

if __name__ == "__main__":
    # net = Net()
    # net.play()
    train()