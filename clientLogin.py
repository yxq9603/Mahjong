#coding=utf8

# 接收到连接成功后，绘制登录界面，获取输入账号密码，完成注册登录，显示传入的字符串
# # cmd25*80
import socket
import threading
import time
import json
import clientConfig
import os

class ClientLogin():
    # 初始化：等待连接页面，建立连接，接收note,msg,模拟按键
    def __init__(self):
        os.system('cls')
        # [note,{msg:"msg"}]
        self.note = None
        self.msg = None
        # 模拟按键
        self.ButtonLogin = 0
        self.ButtonReg = 1
        self.ButtonReturn = 2
        # 在接收到消息和选择按钮时改变值
        self.ButtonValue = 0 
        # 心跳时间
        self.startTime = 0.0
        self.endTime = 0.0
        self.getPong = False
        # 账号
        self.account = None
        
    
    def start(self):
       # 绘制等待界面并建立连接
        self.frame()
        self.waitPage()

        # 开启消息接收线程
        recvThread = threading.Thread(target=self.recv)
        recvThread.daemon = True
        recvThread.start()
        
        # 开启心跳线程
        self.startTime = time.time()
        heartThread = threading.Thread(target=self.heartBeat)
        heartThread.daemon = True
        heartThread.start()
        
        # 主逻辑：负责调用各个界面
        while True:
            if self.note == "connected" or self.note == "registered ok" or self.note == "registered fail" or self.note == "login fail":
                self.note = None
                if self.ButtonValue == self.ButtonLogin or self.ButtonValue == self.ButtonReturn:
                    self.loginPage(self.msg)
                elif self.ButtonValue == self.ButtonReg:
                    self.registeredPage(self.msg)
            elif self.note == "login ok":
                clientConfig.ACCOUNT = self.account
                self.conn.close()
                return (self.msg[0],self.msg[1])
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

                    if data[0] == "registered ok" or data[0] == "registered fail":
                        self.ButtonValue = 1
                    elif data[0] == "login ok" or data[0] == "login fail":
                        self.ButtonValue = 0
                    self.note = data[0]
                    self.msg = data[1]["msg"]
            except:
                self.note = "break"

    # 登录界面,改变按键值或者发送登录信息，确认收到反馈后再结束(可以不确认)
    # 使用后self.msg = None
    def loginPage(self,msg):
        if msg != None:
            print("**************%s**************" % msg)
        while True:
            cmd = input("""------------登录--------------
输入1：输入账号密码
输入2：注册
""")
            if cmd == '1':
                print("--------------------------")
                self.account = input("请输入账号：")
                print("--------------------------")
                passw = input("请输入密码：")
                try:
                    self.conn.sendall(json.dumps(["login",{"account":self.account,"pass":passw}]).encode("utf-8"))
                except:
                    self.note = "break"
                    break
                os.system('cls')
                break

            if cmd == '2':
                self.ButtonValue = self.ButtonReg
                self.note = "connected"
                os.system('cls')
                break
            os.system('cls')
                 
    # 注册界面,改变按键值或者发送注册信息，确认收到反馈后再结束
    def registeredPage(self,msg):
        if msg != None:
            print("**************%s**************" % msg)
        while True:
            cmd = input("""------------注册--------------
输入1：输入账号密码
输入2：返回
""")
            if cmd == '1':
                print("--------------------------")
                account = input("请输入账号：")
                print("--------------------------")
                passw = input("请输入密码：")
                print("--------------------------")
                name = input("请输入姓名：")
                try:
                    self.conn.sendall(json.dumps(["registered",{"account":account,"pass":passw,"name":name}]).encode("utf-8"))
                except:
                    self.note = "break"
                    break
                os.system('cls')
                break

            if cmd == '2':
                self.ButtonValue = self.ButtonReturn
                self.note = "connected"
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
            result = self.conn.connect_ex(clientConfig.LOGIN_ADDRESS)
            index = index % 4
            msg = "\r正在连接 " + ch_list[index]
            print(msg, end="")
            index += 1 
        os.system('cls')