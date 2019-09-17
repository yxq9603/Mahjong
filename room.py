#coding=utf8
from gbmj_logic import GBMJ
import time

# 房间类,分配逻辑规则里的玩家实例化对象给各个玩家（当前局座位序号和玩家id配对）
# 使用通信模块，room接收玩家出牌或决策选择消息，执行对应函，逻辑里自主发送通知消息
class Room():
    def __init__(self,id0,id1,id2,id3):
        gbmj = GBMJ()
        # 创建房间号（或者不在这里），数据库写入房间号，游戏局数，已进行=0，玩家ID
    
        # 配对
        id0 = gbmj.playList[0]
        id1 = gbmj.playList[1]
        id2 = gbmj.playList[2]
        id3 = gbmj.playList[3]
        # 开局
        gbmj.initPai()
        gbmj.shuffle()
        gbmj.deal()

        
        gbmj.endTime = time.time()
        
        
            
    def sishewuru(self,value):
        temp1 = int(value*100)%10
        temp2 = int(value*10)
        if temp1 > 4:
            temp2 += 1
        return temp2

        