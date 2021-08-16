from PyQt5 import QtCore,QtGui
from PyQt5.QtWidgets import QFrame, QWidget,QApplication,QLabel
import numpy as np
import time
import sys
import _thread
from queue import Queue
from random import choice

DEBUG = False


FRESH_ITER = 0.01

SNAKE_SPEED = 10                                                    #每秒多少格
SNAKE_START_LONG = 5
SNAKE_WIDTH = 30

R = [0,1]
L = [0,-1]
T = [-1,0]
B = [1,0]

BOARD_SIZE = (800,800)
GRID_SIZE = (20,20)
APPLE_SIZE = (40,40)
SPACE_H = int(BOARD_SIZE[0] / GRID_SIZE[0])
SPACE_W = int(BOARD_SIZE[1] / GRID_SIZE[1])
SIDE_H = int((SPACE_H-SNAKE_WIDTH)/2)
SIDE_W = int((SPACE_W-SNAKE_WIDTH)/2)

START_POSITIONS = [ [8,3+i] for i in range(SNAKE_START_LONG)]
START_DRECTIONS = [(L,R)]*SNAKE_START_LONG

GAME_CONTNIUE = True
TURN_LOCK = True                                                  #转向锁，防止出现奇奇怪怪的BUG

#anime super param
PROGRESS,HEAD_D,HAIL_D,HEAD_P,HAIL_P    =    0,START_DRECTIONS[-1][1],START_DRECTIONS[0][0],START_POSITIONS[-1],START_POSITIONS[0]
STEP_H = SNAKE_WIDTH + SIDE_H*2
STEP_W = SNAKE_WIDTH + SIDE_W*2


def check_gp(p):
    global GAME_CONTNIUE
    if p[0]>=GRID_SIZE[0] or p[0]<0 or p[1]>=GRID_SIZE[1] or p[1]<0:
        GAME_CONTNIUE = False
        print("GAMEOVER,you out of the side")
        return True
    return False
        
def call_error():
    if GAME_CONTNIUE:
        print("ERROR")

class Board:
    def __init__(self):
        self.freshiter = FRESH_ITER                               #unit:second
        self.grid = np.zeros(GRID_SIZE)
        self.scene = np.zeros((*BOARD_SIZE,1),dtype=np.uint8)
        self.score = 0
        
        self.add_snake()
        self.add_apple()
    
    def add_apple(self):
        
        idx = np.argwhere(self.grid==0)
        idx = choice(idx)
        p = [idx[0],idx[1]]
        self.apple = Apple(self,p)
        self.grid[p[0]][p[1]] = 2                                #这里用2表示此格放了苹果
        #draw apple
        start_h = p[0]      * SPACE_H
        end_h   = (p[0]+1)  * SPACE_H
        start_w = p[1]      * SPACE_W
        end_w   = (p[1]+1)  * SPACE_W
        self.scene[start_h:end_h,start_w:end_w,:] = np.uint8(255)

    def eat_apple(self):
        self.score += self.apple.value                           #计分
        try:
            with open("SCORE.txt",'w+') as f:
                f.write(str(self.score))
        except:
            pass
        self.snake.lengthen()
        self.add_apple()
        
    
    def add_snake(self):
        self.snake = Snake(self)
        self.snake.draw()

    def board_refresh(self):
        self.scene = np.zeros((*BOARD_SIZE,1),dtype=np.uint8)
        self.snake.draw()
        self.apple.draw()
    
    def snake_move(self):
        global GAME_CONTNIUE,TURN_LOCK
        TURN_LOCK = False
        
        #添头去尾
        head = self.snake.body.queue[-1]
        head_pos = [head.position[0]+head.nd[0], head.position[1]+head.nd[1]]
        if check_gp(head_pos):
            return
        self.snake.body.put(Body(
            ld=[-head.nd[0],-head.nd[1]],
            nd=head.nd,
            position=head_pos,
            head=True,
        ))
        self.snake.body.queue[0].show = False       #新头先不显示，展示动画
        if self.grid[head_pos[0]][head_pos[1]] == 1:
            GAME_CONTNIUE = False
            print("GAME OVER : You eat yourself!")
        if self.grid[head_pos[0]][head_pos[1]] == 2:
            print("EAT APPLE!")
            self.eat_apple()
        hail_pos = self.snake.body.queue[0].position
        self.grid[head_pos[0]][head_pos[1]] = 1
        self.grid[hail_pos[0]][hail_pos[1]] = 0     #尾部过去
        
        TURN_LOCK = True
        
        #移动动画
        self.snake.body.queue[-2].head = False      #取消头，防止转向
        self.snake.body.queue[-2].head_draw = False #不画头的边缘
        self.snake.body.queue[1].hail = True        #设为尾巴，防止绘制边缘
        self.snake.body.queue[-1].show = False      #尾部不显示，显示动画
        self.move_anime()                           #动画播放
        self.snake.body.queue[-1].show = True       #动画播完了，可以显示头了
        self.snake.body.queue[-2].head_draw = True  #画头
        self.snake.body.get()                       #旧尾巴可以去掉了
                
        # time.sleep(1/SNAKE_SPEED)
    
    def move_anime(self):
        """ 
        说是动画，其实只是改参的
        """
        global PROGRESS,HEAD_D,HAIL_D,HEAD_P,HAIL_P
        last_head = self.snake.body.queue[-2]
        hail = self.snake.body.queue[0]
        drection = last_head.nd
        #动画
        p1 = last_head.position
        p2 = hail.position
        d = hail.nd
        HEAD_P,HAIL_P,HEAD_D,HAIL_D = p1,p2,drection,d,
        for i in range(int((1/SNAKE_SPEED)/FRESH_ITER)):
            PROGRESS = i*FRESH_ITER*SNAKE_SPEED
            time.sleep(FRESH_ITER)
        
                
    def refresh(self):
        global GAME_CONTNIUE
        while GAME_CONTNIUE:
            if DEBUG:
                self.snake_move()
            else:
                try:
                    self.snake_move()
                except:
                    call_error()
                    GAME_CONTNIUE = False
                    return
    

class Apple:
    def __init__(self,parent:Board,position):
        """ 
        position: (x,y) -> tuple | list
        """
        self.size = APPLE_SIZE
        self.parent = parent
        self.position = position
        self.value = 1
    def draw(self):
        p = self.position
        start_h = p[0]      * SPACE_H
        end_h   = (p[0]+1)  * SPACE_H
        start_w = p[1]      * SPACE_W
        end_w   = (p[1]+1)  * SPACE_W
        self.parent.scene[start_h:end_h,start_w:end_w,:] = np.uint8(255)
        # self.parent.grid[p[0]][p[1]] = 2

class Body:
    def __init__(self,ld,nd,position,order=None,head=False,show=True):
        self.ld = ld                                    #先前进入该位置的方向
        self.nd = nd                                    #出去的方向
        self.head = head
        self.hail = False
        self.show = show
        self.position = position
        self.order = order
        self.head_draw = True

class Snake:
    """ 
    width:60        px
    start_long:5    unit
    """
    def __init__(self,parent:Board):
        self.long = SNAKE_START_LONG
        self.body = Queue()
        self.parent = parent                            #用于绘制
        for i,(p,(ld,nd)) in enumerate(zip(START_POSITIONS,START_DRECTIONS)):
            self.body.put(
                Body(
                    ld=ld,
                    nd=nd,
                    position=p,
                    order=i
                )
            )
        self.parent.grid[p[0]][p[1]] = 1                     #格子先对上
        self.body.queue[0].hail = True
        self.body.queue[-1].head = True
        
    def lengthen(self):
        lb = self.body.queue[0]
        newbody = Body(
            ld=lb.ld,
            nd=lb.nd,
            position=lb.position,
            order=self.long
        )
        self.long += 1
        self.body.queue.appendleft(newbody)
        
    def draw(self):
        def draw_side(p,drection):
            if drection==R:    
                start_h = p[0]      * SPACE_H +SIDE_H
                end_h   = (p[0]+1)  * SPACE_H -SIDE_H
                start_w = (p[1]+1)  * SPACE_W -SIDE_W
                end_w   = (p[1]+1)  * SPACE_W
            elif drection==L:
                start_h = p[0]      * SPACE_H +SIDE_H
                end_h   = (p[0]+1)  * SPACE_H -SIDE_H
                start_w = p[1]      * SPACE_W
                end_w   = p[1]      * SPACE_W +SIDE_W
            elif drection==T:
                start_h = p[0]      * SPACE_H
                end_h   = p[0]      * SPACE_H +SIDE_H
                start_w = p[1]      * SPACE_W +SIDE_W
                end_w   = (p[1]+1)  * SPACE_W -SIDE_W
            elif drection==B:
                start_h = (p[0]+1)  * SPACE_H -SIDE_H
                end_h   = (p[0]+1)  * SPACE_H
                start_w = p[1]      * SPACE_W +SIDE_W
                end_w   = (p[1]+1)  * SPACE_W -SIDE_W
            else:
                print("ERROR")
            self.parent.scene[start_h:end_h,start_w:end_w,:] = np.uint8(255)
        def show():
            try:
                for b in self.body.queue:
                    if not b.show:
                        continue
                    p = b.position
                    
                    #绘制中心方块
                    start_h = p[0]      * SPACE_H +SIDE_H
                    end_h   = (p[0]+1)  * SPACE_H -SIDE_H
                    start_w = p[1]      * SPACE_W +SIDE_W
                    end_w   = (p[1]+1)  * SPACE_W -SIDE_W
                    self.parent.scene[start_h:end_h,start_w:end_w,:] = np.uint8(255)
                    
                    #绘制连接边缘
                    
                    k = False
                    
                    if not b.hail or k:
                        draw_side(p,b.ld)
                    if not b.head or k:
                        if b.head_draw:
                            draw_side(p,b.nd) 
            except:
                print("LOCKED")
                show()
        show()
        #draw anime
        #head anime
        if HEAD_D==R:    
            start_h = HEAD_P[0]     * SPACE_H + SIDE_H
            end_h   = (HEAD_P[0]+1) * SPACE_H - SIDE_H 
            start_w = (HEAD_P[1]+1) * SPACE_W - SIDE_W
            end_w   = start_w       + int(PROGRESS*STEP_W)
        elif HEAD_D==L:
            start_h = HEAD_P[0]     * SPACE_H + SIDE_H
            end_h   = (HEAD_P[0]+1) * SPACE_H - SIDE_H
            end_w   = HEAD_P[1]     * SPACE_W + SIDE_W
            start_w = end_w         - int(PROGRESS*STEP_W)
        elif HEAD_D==T:
            end_h   = HEAD_P[0]     * SPACE_H + SIDE_H
            start_h = end_h         - int(PROGRESS*STEP_H)
            start_w = HEAD_P[1]     * SPACE_W + SIDE_W
            end_w   = (HEAD_P[1]+1) * SPACE_W - SIDE_W
        elif HEAD_D==B:
            start_h = (HEAD_P[0]+1) * SPACE_H - SIDE_H
            end_h   = start_h       + int(PROGRESS*STEP_H)
            start_w = HEAD_P[1]     * SPACE_W + SIDE_W
            end_w   = (HEAD_P[1]+1) * SPACE_W - SIDE_W
        else:
            print("ERROR")
        self.parent.scene[start_h:end_h,start_w:end_w,:] = np.uint8(255)
        #hail anime
        #HAIL_D是旧蛇尾目前朝向，HAIL_P是旧蛇尾目前位置
        if HAIL_D==R:    
            start_h = HAIL_P[0]     * SPACE_H + SIDE_H
            end_h   = (HAIL_P[0]+1) * SPACE_H - SIDE_H
            end_w   = (HAIL_P[1]+1) * SPACE_W + SIDE_W
            start_w = end_w         - int((1-PROGRESS)*STEP_W)
        elif HAIL_D==L:
            start_h = HAIL_P[0]     * SPACE_H + SIDE_H
            end_h   = (HAIL_P[0]+1) * SPACE_H - SIDE_H
            start_w = HAIL_P[1]     * SPACE_W - SIDE_W
            end_w   = start_w       + int((1-PROGRESS)*STEP_W)
        elif HAIL_D==T:
            start_h = HAIL_P[0]     * SPACE_H - SIDE_H
            end_h   = start_h       + int((1-PROGRESS)*STEP_H)
            start_w = HAIL_P[1]     * SPACE_W + SIDE_W
            end_w   = (HAIL_P[1]+1) * SPACE_W - SIDE_W
        elif HAIL_D==B:
            end_h   = (HAIL_P[0]+1) * SPACE_H + SIDE_H
            start_h = end_h         - int((1-PROGRESS)*STEP_H)
            start_w = HAIL_P[1]     * SPACE_W + SIDE_W
            end_w   = (HAIL_P[1]+1) * SPACE_W - SIDE_W
        self.parent.scene[start_h:end_h,start_w:end_w,:] = np.uint8(255)
        
        
        
        

def turn_right(v):
    v_ = []
    v_.append(v[1])
    v_.append(-v[0])
    return v_
def turn_left(v):
    v_ = []
    v_.append(-v[1])
    v_.append(v[0])
    return v_

class MainWindow(QWidget):
    
    def __init__(self):
        super(MainWindow,self).__init__()
        self.board = Board()
        self.initUI()
        
    def initUI(self):
        self.setGeometry(50,50,BOARD_SIZE[1]+100,BOARD_SIZE[0])
        self.setStyleSheet(""" 
                           background: #7f8c8d;
                           """)
        self.setWindowTitle("Real-Python")
        self.show()
        
        #放置游戏界面
        self.lab = QLabel(self)
        img = self.board.scene
        pixmap = QtGui.QPixmap.fromImage( QtGui.QImage( img ,   img.shape[1] ,   img.shape[0]  ,  QtGui.QImage.Format_Indexed8 ) )
        self.lab.setPixmap(pixmap)
        self.lab.show()
        # self.refresh()
        
        #计分板
        self.score_box = QLabel(self)
        self.score_box.setGeometry(BOARD_SIZE[1],0,100,100)
        self.score_box.setStyleSheet(""" 
                                     background: black;
                                     color: red;
                                     font-size: 36px;
                                     font-family: Arial;
                                     """)
        self.score_box.setFrameShape(QFrame.Box)
        self.score_box.setFrameStyle(3)
        self.score_box.setAlignment(QtCore.Qt.AlignCenter)
        self.score_box.show()

    def refresh(self):

        def dothis():
            global GAME_CONTNIUE
            while GAME_CONTNIUE:
                if DEBUG:
                    self.board.board_refresh()
                else:
                    try:
                        self.board.board_refresh()
                    except:
                        call_error()
                        GAME_CONTNIUE = False
                        return
                img = self.board.scene
                pixmap = QtGui.QPixmap.fromImage( QtGui.QImage( img ,   img.shape[1] ,   img.shape[0]  ,  QtGui.QImage.Format_Indexed8 ) )
                self.lab.setPixmap(pixmap)
                
                #计分
                self.score_box.setText(str(self.board.score))
                
                time.sleep(FRESH_ITER)
            
        _thread.start_new_thread(dothis,())
        _thread.start_new_thread(self.board.refresh,())

    
    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        global GAME_CONTNIUE
        """ 
        ↑   :   16777235
        ↓   :   16777237
        ←   :   16777234
        →   :   16777236
        """
        if str(a0.key()) == "16777236" and TURN_LOCK:
            for b in self.board.snake.body.queue:
                if b.head == True:
                    b.nd = turn_right(b.nd)
        elif str(a0.key()) == "16777234" and TURN_LOCK:
            for b in self.board.snake.body.queue:
                if b.head == True:
                    b.nd = turn_left(b.nd)
        elif str(a0.key()) == "32":
            if GAME_CONTNIUE:
                print("GAME START")
                self.refresh()
            else:
                print("RESHART")
                GAME_CONTNIUE = True
                self.board = Board()
                self.refresh()
        # print(str(a0.key()))
        return super().keyPressEvent(a0)
        
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    box = MainWindow()
    app.exit(app.exec_())