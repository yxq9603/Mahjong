# 大厅服务器：显示玩家积分和负责创建房间、加入房间(当房间没人的时候从数据库中删去)
import socketserver
import config
import json
from dbUtil import DBUtil
import threading
import random
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
        self.score = None
        self.roomid = None
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
            # 离线删去socket
            elif self.endTime - self.startTime > 35 and self.getPing == False:
                self.remove()
                break

    # 为每个连接开线程处理接收的信息
    def handle(self):
        while True:
            try:
                bytes = self.request.recv(10240)
                bytes = bytes.decode("utf-8")
                print(bytes)
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
                print(listBytes)
                for byte in listBytes:
                    data = json.loads(byte)
                    # 接收ping,立刻回复pong,并开始计时
                    if data[0] == "ping":
                        self.getPing = True
                        self.request.sendall(json.dumps(["pong"]).encode("utf-8"))
                        continue

                    event = data[0]
                    para = data[1]

                    # 根据接收到的账号绑定ID,并发送姓名
                    if event == "account":
                        self.id = db.selectID(para["account"])["ID"]
                        name = db.selectName(para["account"])["NAME"]
                        score = db.select_score(self.id)["SCORE"]
                        self.request.sendall(json.dumps(["name",{"name":name,"score":score}]).encode("utf-8"))
                        config.HALL_CONN_POOL[self.id] = self.request

                    # 查询积分
                    elif event == "score":
                        self.score = db.select_score(para["score"])
                        self.request.sendall(json.dumps(["score",{"score":self.score}]).encode("utf-8"))
                        
                    # 创建房间，生成房间号，写入db，返回房间号和房间地址
                    elif event == "create":
                        roomId = self.generateRoomId()
                        # 查询生成的房间号是否存在
                        while db.select_roomID(roomId):
                            roomId = self.generateRoomId()
                        # 写入db
                        db.insertRoomID(roomId,para["total_num"])
                        # 写入房间池
                        self.roomid = roomId
                        config.ROOMID[roomId] = []
                        config.ROOMID[roomId].append(self.id)
                        # id写入数据库
                        db.roomUserID(roomId,0,self.id)
                        # 返回房间号和地址
                        self.request.sendall(json.dumps(["create",{"roomid":roomId,"ADDRESS":config.GAME_ADDRESS}]).encode("utf-8")) 

                    # 加入房间，验证房间号，返回房间地址
                    elif event == "join":
                        roomId = para["roomid"]
                        print("join")
                        # 验证房间号
                        if db.select_roomID(roomId):
                            print("you id")
                            print(config.ROOMID)
                            # 验证是否人满,未满
                            if len(config.ROOMID[roomId]) < 4:
                                print("ok")
                                config.ROOMID[roomId].append(self.id)
                                self.rooid = roomId
                                # id写入数据库
                                db.roomUserID(roomId,len(config.ROOMID[roomId])-1,self.id)
                                self.request.sendall(json.dumps(["join ok",{"roomid":roomId,"ADDRESS":config.GAME_ADDRESS}]).encode("utf-8")) 
                            else:
                                print("not ok")
                                self.request.sendall(json.dumps(["join fail",{"msg":"player enough"}]).encode("utf-8")) 
                        else:
                            self.request.sendall(json.dumps(["join fail",{"msg":"wrong roomid"}]).encode("utf-8"))

                    # 退出，清除连接池中的对应项
                    elif event == "exit":
                        self.remove()
       
            # 意外掉线
            except:  
                self.remove()
                break
    
    # 生成房间号
    def generateRoomId(self):
        roomId = ""
        for i in range(0,5):
            roomId += str(random.randint(0,9))
        return str(roomId)
    # 如果加入了房间，查看当前房间是否还有人，没人了就删去数据库和房间池里的数据
    def remove(self):
        if len(config.HALL_CONN_POOL) > 0 and self.id in config.HALL_CONN_POOL:
            try:
                config.HALL_CONN_POOL.pop(self.id)
            except:
                print("already delete")
            finally:
                self.request.close()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == "__main__":
    print("HALL")
    server = ThreadedTCPServer(config.HALL_ADDRESS, MyTCPHandler)
    # 新开一个线程运行服务端
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # 主线程逻辑
    while True:
        cmd = input("""--------------------------
输入1:查看当前在线人数
输入2:给所有客户端发送消息
输入close:关闭服务端
""")
        if cmd == '1':
            print("--------------------------")
            print("当前在线人数：", len(config.HALL_CONN_POOL))
        elif cmd == '2':
            print("--------------------------")
            msg = input("请输入：")
            for id in config.HALL_CONN_POOL:
                config.HALL_CONN_POOL[id].sendall(msg.encode(encoding='utf8'))
        elif cmd == 'close':
            server.shutdown()
            server.server_close()
            exit()
