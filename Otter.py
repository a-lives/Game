import threading
import EE
import time
import torch
from torch.nn.modules import Linear,Softmax,Conv2d,LeakyReLU,Dropout




def game():
    app = EE.QApplication(EE.sys.argv)
    box = EE.MainWindow()
    app.exit(app.exec_())

def otter():
    while 1:
        if td1.is_alive():
            time.sleep(1)
            print("\r",EE.GAME_CONTNIUE,EE.BOARD)
        else:
            break
    
td1 = threading.Thread(target=game)
td2 = threading.Thread(target=otter)
td1.start()
td2.start()
