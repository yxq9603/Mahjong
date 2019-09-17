# 游戏服务器：
# 1.连接成功后，为房间池中对应的房间添加游戏实例（绑定玩家id,roomid,seat）
# 2.
import socketserver
import config
import json
from dbUtil import DBUtil
import threading
import random
from gbmj_logic import GBMJ
import time

db = DBUtil()

class MyTCPHandler(socketserver.BaseRequestHandler):
    # 为当前连接初始化
    def setup(self):
        # 心跳时间
        self.startTime = 0.0
        self.endTime = 0.0
        self.getPing = False
        
        self.id = None
        self.roomid = None
        self.seat = None
        self.request.sendall(json.dumps(["connected",{"msg":None}]).encode("utf-8"))
        

        # 开启心跳线程
        self.startTime = time.time()
        heartThread = threading.Thread(target=self.heartBeat)
        heartThread.daemon = True
        heartThread.start()

    # 心跳:
    # 客户端每隔30s发送一次ping,5s之内收不到pong则认为服务器离线，跳转到等待连接界面并尝试重连
    # 服务器每收到一次ping则立刻返回pong,若35s收不到ping，则认为客户端离线，删去连接
    def heartBeat(self):
        while True:
            # 查看35s内是否收到ping
            self.endTime = time.time()
            if self.endTime - self.startTime <= 35 and self.getPing == True:
                self.getPing = False
                self.startTime = self.endTime
            # 离线删去socket,退出线程
            elif self.endTime - self.startTime > 35 and self.getPing == False:
                self.remove()
                break

    # 为每个连接开线程处理接收的信息
    def handle(self):
        while True:
            try:
                bytes = self.request.recv(10240)
                bytes = bytes.decode("utf-8")
                listBytes = []
                bytes = bytes.split("][")
                if len(bytes) > 1:
                    for i in bytes:
                        if bytes.index(i) == 0:
                            i = i + "]"
                            listBytes.append(i)
                        elif bytes.index(i) == len(bytes)-1:
                            i = "[" + i
                            listBytes.append(i)
                        else:
                            i = "[" + i + "]"
                            listBytes.append(i)
                else:
                    listBytes = bytes
                for byte in listBytes:
                    data = json.loads(byte)
                    if data[0] != "ping":
                        print(data)

                    # 接收ping,立刻回复pong,并开始计时
                    if data[0] == "ping":
                        self.getPing = True
                        self.request.sendall(json.dumps(["pong"]).encode("utf-8"))
                        continue

                    event = data[0]
                    para = data[1]
                    
                    # 连接之后初始化
                    if event == "player":
                        # 获取id
                        self.id = db.selectID(para["account"])["ID"]
                        # 绑定房间号
                        self.roomid = para["roomid"]
                        # 对应房间号下绑定玩家id:socket
                        if self.roomid not in config.GAME_CONN_POOL:
                            config.GAME_CONN_POOL[self.roomid] = {}
                        config.GAME_CONN_POOL[self.roomid][self.id] = self.request
                        # 当房间内有四名玩家时，并且是第四名时，实例化游戏对象
                        if self.roomid not in config.ROOMID:
                            config.ROOMID[self.roomid] = []
                        config.ROOMID[self.roomid].append(self.id)
                        tempList = config.ROOMID[self.roomid]
                        # 绑定座位号
                        self.seat = tempList.index(self.id)
                        print("len",len(tempList))
                        if len(tempList) == 4 and self.id == tempList[3]:
                            msg = {}
                            # 根据id查询玩家姓名{"seat":name}
                            for playerId in tempList:
                                name = db.selectNameByID(playerId)["NAME"]
                                msg[str(tempList.index(playerId))] = name
                            # 向所有玩家广播开始游戏以及其余玩家的姓名和座位号
                            for playerId in tempList:
                                config.GAME_CONN_POOL[self.roomid][playerId].sendall(json.dumps(["begin",msg]).encode("utf-8"))
                            gbmj = GBMJ(tempList[0],tempList[1],tempList[2],tempList[3],self.roomid)
                            tempList.append(gbmj)
                            print("msg",msg)
                            # 游戏开始
                            print("begin")
                            gbmj.initPai()
                            gbmj.shuffle()
                            gbmj.deal()
                            print("next")
                    
                    # 新开一局
                    elif event == "continue":
                        gbmj = config.ROOMID[self.roomid][4]
                        if para not in gbmj.numOfCotinue:
                            gbmj.numOfCotinue.append(para)
                        if len(gbmj.numOfCotinue) == 4:
                            # 游戏开始
                            gbmj.initPai()
                            gbmj.shuffle()
                            gbmj.deal()
                         
                    # 出牌
                    elif event == "chupai":
                        self.penalty()
                        config.ROOMID[self.roomid][4].chuPai(self.seat,para["pai"])

                    # 决策选择,所有发过来的都要有paiList项
                    elif event == "choose":
                        self.penalty()
                        config.ROOMID[self.roomid][4].choose(self.seat,para["action"],para["pailist"])

                    # 退出
                    elif event == "exit":
                        # 游戏未开始，可以退出，当房间内全部退出，清除连接池，房间池以及db
                        # if len(config.ROOMID[self.roomid]) == 1:
                        #     # 清除房间池中的房间信息
                        #     config.ROOMID.pop(self.roomid)
                        #     # 清除连接池中信息
                        #     config.GAME_CONN_POOL.pop(self.roomid)
                        #     # 删除数据库中房间记录
                        #     db.delete_room(self.roomid)
                        # elif len(config.ROOMID[self.roomid]) < 4:
                        #     # 清除房间池中的玩家id信息
                        #     config.ROOMID[self.roomid].remove(self.id)
                        #     # 清除连接池中信息
                        #     self.remove()
                        
                        # 游戏正常结束
                        if para == "exit":
                            # 当最后一个人退出时，清除连接池，房间池以及db
                            if config.ROOMID[self.roomid].count(self.id) > 0:
                                del(config.ROOMID[self.roomid][config.ROOMID[self.roomid].index(self.id)])
                            if len(config.ROOMID[self.roomid]) == 0:
                                print("exit!")
                                # 清除房间池中的房间信息
                                config.ROOMID.pop(self.roomid)
                                # 清除连接池中信息
                                config.GAME_CONN_POOL.pop(self.roomid)
                                # 删除数据库中房间记录
                                db.delete_room(self.roomid)
                                # 结束
                                self.request.close()
      
            # 意外掉线
            except: 
                self.remove()
                break
    
    # 罚分
    def penalty(self):
        gbmj = config.ROOMID[self.roomid][4]
        # 接收到客户端发来的出牌或是决策选择消息
        gbmj.endTime = time.time()
        # 计算对应玩家超时情况
        valueTime = gbmj.endTime - gbmj.startTime
        # 超过0.5s，每100ms罚一分
        if valueTime > 0.5:
            gbmj.playList[self.seat].penalty += self.sishewuru(valueTime-0.5)

    # 四舍五入
    def sishewuru(self,value):
        temp1 = int(value*100)%10
        temp2 = int(value*10)
        if temp1 > 4:
            temp2 += 1
        return temp2

    def remove(self):
        try:
            if len(config.GAME_CONN_POOL[self.roomid]) > 0 and self.id in config.GAME_CONN_POOL[self.roomid]:
                print("remove",config.GAME_CONN_POOL[self.roomid],"id",self.id)
            
                config.GAME_CONN_POOL[self.roomid].pop(self.id)
        except:
            print("already delete")
        finally:
            self.request.close()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == "__main__":
    print("GAME")
    server = ThreadedTCPServer(config.GAME_ADDRESS, MyTCPHandler)
    server.serve_forever()
