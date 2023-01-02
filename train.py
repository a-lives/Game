import subprocess as sp
from threading import Timer
import time

def kill(x,y):
    print("Process Timeout!!!")
    x.kill()
    fail.append(y+1)
    
fail = []

st = time.time()
for i in range(10):
    p = sp.Popen("python Manager.py")
    timer = Timer(400,kill,[p,i])
    timer.start()
    print("第%d轮开始"%(i+1,))
    p.wait()
    p.terminate()
    timer.cancel()
    print("第%d轮成功结束"%(i+1,))
    print("当前总用时:%.2lfs"%(time.time()-st,))

    
print("训练完成，用时:%.2lfs"%(time.time()-st,))
print("Fail:",fail)
        