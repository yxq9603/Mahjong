#coding=utf8
# 登录服务器：负责登录和注册
import socketserver
import config
import json
from dbUtil import DBUtil
import threading
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

                    # 接收ping,立刻回复pong,并开始计时
                    if data[0] == "ping":
                        self.getPing = True
                        self.request.sendall(json.dumps(["pong"]).encode("utf-8"))
                        continue

                    event = data[0]
                    para = data[1]

                    # 注册，查询账户是否存在，将id和socket绑定，返回结果信息
                    if event == "registered":
                        if db.configAccount(para["account"]) is False:
                            db.registered(para["account"],para["pass"],para["name"])
                            self.request.sendall(json.dumps(["registered ok",{"msg":"registered ok"}]).encode("utf-8"))
                        else:
                            self.request.sendall(json.dumps(["registered fail",{"msg":"account exist"}]).encode("utf-8"))
                    
                    # 登录，验证账户密码，将id和socket绑定，返回登录结果及大厅地址
                    elif event == "login":
                        result = db.login(para["account"],para["pass"])
                        print(result)
                        if result == "login ok":
                            self.id = db.selectID(para["account"])["ID"]
                            config.LOGIN_CONN_POOL[str(self.id)] = self.request
                            print("login",config.LOGIN_CONN_POOL,"id",self.id)
                            # 返回登录结果及大厅地址
                            self.request.sendall(json.dumps(["login ok",{"msg":config.HALL_ADDRESS}]).encode("utf-8"))
                        else:
                            self.request.sendall(json.dumps(["login fail",{"msg":result}]).encode("utf-8"))
                    
                    # 退出，清除连接池中的对应项
                    elif event == "exit":
                        self.remove()
       
            # 意外掉线
            except:  
                self.remove()
                break
    
    def remove(self):
        if len(config.LOGIN_CONN_POOL) > 0 and self.id in config.LOGIN_CONN_POOL:
            # print("remove",config.LOGIN_CONN_POOL,"id",self.id)
            try:
                config.LOGIN_CONN_POOL.pop(self.id)
            except:
                print("already delete")
            finally:
                self.request.close()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == "__main__":
    print("LOGIN")
    server = ThreadedTCPServer(config.LOGIN_ADDRESS, MyTCPHandler)
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
            print("当前在线人数：", len(config.LOGIN_CONN_POOL))
        elif cmd == '2':
            print("--------------------------")
            msg = input("请输入：")
            for id in config.LOGIN_CONN_POOL:
                config.LOGIN_CONN_POOL[id].sendall(msg.encode(encoding='utf8'))
        elif cmd == 'close':
            server.shutdown()
            server.server_close()
            exit()