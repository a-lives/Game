import torch
from torch.nn.modules import Linear,Conv2d,LeakyReLU,Flatten
import numpy as np


def dataload(scene,pos):
    return torch.stack([torch.from_numpy(scene.transpose(2,1,0)).float()]),torch.stack([torch.tensor(pos)])


class Otter(torch.nn.Module):
    def __init__(self):
        super(Otter,self).__init__()
        self.conv1 = self.block(2,16)               #(1,480,480) --> (16,240,240)
        self.conv2 = self.block(16,32)              #(16,240,240) --> (32,120,120)
        self.conv3 = self.block(32,64)              #(32,120,120) --> (64,60,60)
        self.linear = torch.nn.Sequential(
            Flatten(),
            Linear(64*60*60,3)
        )
        
    def block(self,in_channels,out_channels,kernel_size=5,stride=2):
        block = torch.nn.Sequential(
            Conv2d(in_channels,out_channels,kernel_size,stride,int((kernel_size-1)/2)),
            LeakyReLU()
        )
        return block
        
    def forward(self,x,pos:torch.Tensor):
        pos= pos.unsqueeze(1)
        pos= pos.repeat(1,1,x.size(2),int(x.size(2)/2))
        # print(x.shape,pos.shape)
        x = torch.cat(tensors=(x,pos),dim=1)
        # print(x.shape)
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.linear(x)
        return x

