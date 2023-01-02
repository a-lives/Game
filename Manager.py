import threading
import EE
import time
from Model import Otter,dataload
import torch
import win32gui,win32con,win32api
import gc
import numpy as np
import random

gc.isenabled()

starttime = time.time()

EE.AISAFE = True
EE.TORECORD = True
GAMMA = 0.9
LR = 1e-4
EPS= 0.1
exp_pool = {
    "counter":0,
    "s":[],
    "r":[],
    "s_":[],
}


target = Otter()
otter = Otter()
target.cuda()
otter.cuda()
try:
    target.load_state_dict(torch.load("./params/long_term/target.pkl"))
    otter.load_state_dict(torch.load("./params/long_term/otter.pkl"))
    print("load success")
except:
    target.load_state_dict(otter.state_dict().copy())
    print("new model")
torch.save(target.state_dict(),"./params/temp/target.pkl")
torch.save(otter.state_dict(),"./params/temp/otter.pkl")
optimizer = torch.optim.Adam(otter.parameters(),LR,betas=(0,0.9))

def game():
    app = EE.QApplication(EE.sys.argv)
    box = EE.MainWindow()
    app.exit(app.exec_())

def dataprocess():
    #RECORD: (t,s,a,r)
    for i,re in enumerate(EE.RECORD):
        if re[-2] >2 or np.random.rand() <= 0.2:
            try:
                #(s,r',a,s')
                r = [0,0,0]
                if EE.RECORD[i-1][-2] >2:
                    continue
                else:
                    r[EE.RECORD[i-1][-2]] = re[-1]
                s = np.concatenate(EE.RECORD[i-1][1],axis=2)
                s_ = np.concatenate(re[1],axis=2)
                # print(s.shape,s_.shape)
                exp_pool["s"].append(torch.from_numpy(s.transpose(2,1,0)).float().cuda())
                exp_pool["r"].append(torch.tensor(r).cuda())
                exp_pool["s_"].append(torch.from_numpy(s_.transpose(2,1,0)).float().cuda())
                exp_pool["counter"] += 1
                # print(re[-2],end="")
            except:
                print("dataprocess error")
    print("dataprocess sucess","counter=",exp_pool["counter"])

def train(batch_size=16):
    #(s,r',a,s')
    exp_pool["s"] = torch.stack(exp_pool["s"]).split(batch_size,dim=0)
    exp_pool["r"] = torch.stack(exp_pool["r"]).split(batch_size,dim=0)
    exp_pool["s_"] = torch.stack(exp_pool["s_"]).split(batch_size,dim=0)
    for s,r,s_ in zip(exp_pool["s"],exp_pool["r"],exp_pool["s_"]):
        loss = torch.nn.functional.mse_loss(r+GAMMA*target(s_),otter(s))
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    print("Train success")

def operator():
    EE.GET_NEW_RECORD = False
    while 1:
        time.sleep(0.1)
        try:
            hwnd = win32gui.FindWindow(None,"Greedy Python")
            print("get window")
            time.sleep(3)
            break
        except:
            pass
    count = 1
    while exp_pool["counter"]<128:
        time.sleep(3)
        #start game
        
        win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_SPACE,0)
        win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_SPACE, 0)
        print("game start",count)
        count +=1
        time.sleep(0.2)
        count2 = 0
        while 1:
            if not td1.is_alive():
                print("td1 not exist,break")
                break
            if (EE.GAME_CONTNIUE):
                start = time.time()
                while 1:
                    board = EE.BOARD
                    if board.full():
                        break
                b = dataload(board)
                b = b.cuda()
                values = otter(b)
                end = time.time()
                
                #operate
                action_ = torch.argmax(values).item()
                rn = np.random.rand()
                if rn<=EPS or count2 < 5:
                    action = random.choice([0,1,2])
                    count2 += 1
                else:
                    action = action_
                
                print("\r",end-start,action_,action,values.data,end="       ")
                if action == 0:
                    EE.RECORD.append([None,board.queue,0,EE.REWARD["N"]])
                elif action == 1:
                    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_LEFT, 0)
                    win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_LEFT, 0)
                elif action == 2:
                    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RIGHT, 0)
                    win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RIGHT, 0)
            else:
                break
            time.sleep(0.17)
        if not td1.is_alive():
            break
        dataprocess()
    train()
    torch.save(otter.state_dict(),"./params/long_term/otter.pkl")
    torch.save(torch.load("./params/temp/otter.pkl"),"./params/long_term/target.pkl")
    print("params saved")
    print("Used time:",time.time()-starttime)
    win32api.PostMessage(hwnd,win32con.WM_CLOSE,0,0)
    
if __name__ == "__main__":            
    td1 = threading.Thread(target=game)
    td2 = threading.Thread(target=operator)
    td1.start()
    td2.start()
