import numpy as np
import torch
from PIL import ImageGrab
import time
import matplotlib.pyplot as plt
import os
import re

BOARD_POS = [40, 13, 861, 866]
# SCORE_POS = [860, 60, 943, 141]

def getimg(position=BOARD_POS) -> np.ndarray: 
    """ 
    position : tuple | list , (*top_left,*button_right) , 4 params
    
    return : ndarray(height,width,channel)
    """
    i = ImageGrab.grab()
    i = np.array(i)
    i = i/255
    if position != None:
        i = i[position[1]:position[3],position[0]:position[2],:]
    return i

def preprocess(imgmat:np.ndarray,toshape=(900,900)) -> np.ndarray:
    sha = imgmat.shape
    mat = np.pad(imgmat,( (0,toshape[0]-sha[0]) , (0,toshape[0]-sha[1]) , (0,0) ),constant_values=(0))
    # print(mat.shape)
    return mat

def totensor(imgmat):
    tensor = torch.tensor(imgmat.transpose(2,0,1)).float()
    return tensor

def getscore():
    with open("SCORE.txt",'r') as f:
        return torch.tensor(int(f.read())).float()
    
def get_game_state():
    """ 
    加载游戏状态
    0:未开始
    1:进行中
    2:已结束
    """
    with open("GAME_STATE.txt",'r') as f:
        return int(f.read())

def get_game_pid() -> str:
    res = os.popen("cut.bat")
    pid = re.findall(r"\d+",res.read())[0]
    return pid

def cut_game(pid = None):
    if pid != None:
        os.system("pssuspend %s" % (pid,))
    else:
        pid = get_game_pid()
        os.system("pssuspend %s" % (pid,))
    
def con_game(pid = None):
    if pid != None:
        os.system("pssuspend -r %s" % (pid,))
    else:
        pid = get_game_pid()
        os.system("pssuspend -r %s" % (pid,))

if __name__ == "__main__":
    # board_img = getimg(BOARD_POS)
    # plt.imshow(board_img)
    # plt.show()
    cut_game()