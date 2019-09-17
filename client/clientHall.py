#coding=utf8

# 大厅：界面-玩家积分和姓名，创建房间，加入房间
# # cmd25*80
import socket
import threading
import time
import json
import clientConfig
import os

class ClientHall():
    # 初始化：等待连接页面，建立连接，接收note,msg,模拟按键
    def __init__(self):
        os.system('cls')
        # [note,{msg:"msg"}]
        self.note = None
        self.msg = None
        # 模拟按键
        self.ButtonHall = 0
        self.ButtonCreate = 1
        self.ButtonJoin = 2
        self.ButtonReturn = 3
        # 在接收到消息和选择按钮时改变值
        self.ButtonValue = 0 
        # 心跳时间
        self.startTime = 0.0
        self.endTime = 0.0
        self.getPong = False
        # 账号
        self.account = clientConfig.ACCOUNT
        
    
    def start(self):
       # 绘制等待界面并建立连接
        self.frame()
        self.waitPage()

        # 发送账号获取姓名积分
        try:
            self.conn.sendall(json.dumps(["account",{"account":self.account}]).encode("utf-8"))
        except:
            self.note = "break"

        # 开启消息接收线程
        recvThread = threading.Thread(target=self.recv)
        recvThread.daemon = True
        recvThread.start()
        
        # 开启心跳线程
        self.startTime = time.time()
        heartThread = threading.Thread(target=self.heartBeat)
        heartThread.daemon = True
        heartThread.start()
        
        # 确保获取姓名
        while clientConfig.NAME == None:
            i = 1
        
        # 主逻辑：负责调用各个界面
        while True:
            if self.note == "connected" or self.note == "join fail" :
                self.note = None
                self.hallPage(self.msg)
            elif self.note == "create" or self.note == "join ok":
                clientConfig.ROOMID = self.msg["roomid"]
                clientConfig.LOGIN_ADDRESS = None
                self.conn.close()
                return (self.msg["ADDRESS"][0],self.msg["ADDRESS"][1])
            # 断线重连
            elif self.note == "break":
                os.system('cls')
                self.waitPage()

    # 心跳:
    # 客户端每隔30s发送一次ping,5s之内收不到pong则认为服务器离线，跳转到等待连接界面并尝试重连
    # 服务器每收到一次ping则立刻返回pong,若35s收不到ping，则认为客户端离线，删去连接
    def heartBeat(self):
        while True:
            self.endTime = time.time()
            # 发送ping
            if self.endTime - self.startTime >= 30:
                try:
                    self.conn.sendall(json.dumps(["ping"]).encode("utf-8"))
                except:
                    self.note = "break"
                self.startTime = self.endTime
                # 查看五秒内是否收到pong
                while True:
                    self.endTime = time.time()
                    if self.endTime - self.startTime <= 5 and self.getPong == True:
                        self.getPong = False
                        break
                    elif self.endTime - self.startTime > 5 and self.getPong == False:
                        self.note = "break"
                        break
                
    # 消息接收线程
    def recv(self):
        while True:
            try:
                bytes = self.conn.recv(10240)
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
                    # 接收pong
                    if data[0] == "pong":
                        self.getPong = True
                        continue
                    
                    if data[0] == "name":
                        clientConfig.NAME = data[1]["name"]
                        clientConfig.SCORE = data[1]["score"]
                        continue
                    elif data[0] == "score":
                        clientConfig.SCORE = data[1]["score"]
                        continue
                    self.note = data[0]
                    self.msg = data[1]
            except:
                self.note = "break"

    # 大厅界面,改变按键值或者发送登录信息，确认收到反馈后再结束(可以不确认)
    # 使用后self.msg = None
    def hallPage(self,msg):
        if "msg" in msg and msg["msg"] != None:
            print("**************%s**************" % msg["msg"])
        while True:
            print("------------大厅--------------")
            print("姓名：%s    积分：%s"%(clientConfig.NAME,clientConfig.SCORE))
            cmd = input("""
输入1：创建房间
输入2：加入房间
""")
            if cmd == '1':
                num = input("""------------创建房间--------------
输入1：输入对战局数
输入2：返回
""")            
                if num == '1':
                    totalNum = input("请输入对战局数：")
                    try:
                        self.conn.sendall(json.dumps(["create",{"total_num":totalNum}]).encode("utf-8"))
                    except:
                        self.note = "break"
                        break
                    os.system('cls')
                    break
                if num == '2':
                    self.note = "connected"
                    os.system('cls')
                    break

            if cmd == '2':
                print("--------------------------")
                roomid = input("请输入房间号：")
                try:
                    self.conn.sendall(json.dumps(["join",{"roomid":roomid}]).encode("utf-8"))
                except:
                    self.note = "break"
                    break
                os.system('cls')
                break
            os.system('cls')
                 
    # 边框
    def frame(self):
        print(" ")
    
    # 等待连接界面
    def waitPage(self):
        index = 0
        ch_list = ["\\", "|", "/", "-"]
        result = -1
        while result != 0: 
            self.conn = socket.socket()
            result = self.conn.connect_ex(clientConfig.HALL_ADDRESS)
            index = index % 4
            msg = "\r正在连接 " + ch_list[index]
            print(msg, end="")
            index += 1 
        os.system('cls')