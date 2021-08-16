import torch
from torch import nn




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
            nn.ReLU()
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
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.pred(x)
        return x