#coding=utf8

# 大厅：界面-玩家积分和姓名，创建房间，加入房间(绑定自己的座位号，获取其他玩家的座位号和姓名，逻辑每次广播时的内容整理)
# # cmd25*80
import socket
import threading
import time
import json
import clientConfig
import os

class ClientGame():
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
        self.roomId = clientConfig.ROOMID
        self.name = clientConfig.NAME
        self.seat = -1
        # 玩家
        self.player = {}
        # 弃牌
        self.flod = []
        # 是否刷新
        self.flush = False

    def start(self):
       # 绘制等待界面并建立连接
        self.frame()
        self.waitPage()

        # 发送账号房间号
        try:
            self.conn.sendall(json.dumps(["player",{"account":self.account,"roomid":self.roomId}]).encode("utf-8"))
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
        
        # 主逻辑：负责调用各个界面
        while True:
            if self.note == "connected":
                self.flush = False
                self.waitPlayerPage()
            # 重开一局（添加结果）
            elif self.note == "next":
                self.flush = False
                for seat in range(0,4):
                    self.player[seat].clear()
                self.conn.sendall(json.dumps(["continue",self.seat]).encode("utf-8"))
                self.gamePage(self.msg)
            # 结束
            elif self.note == "over":
                self.conn.sendall(json.dumps(["exit","exit"]).encode("utf-8"))
                clientConfig.GAME_ADDRESS = None
                self.conn.close()
                return
            # 断线重连
            elif self.note == "break":
                os.system('cls')
                self.waitPage()
            elif self.note != None and self.flush == True and self.note != "break" and self.note != "next" and self.note != "over":
                self.flush = False
                self.gamePage(self.msg)
            
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
            # try:
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
            elif len(bytes) == 1:
                listBytes = bytes
            else:
                continue
            # 指令分开来
            for byte in listBytes:
                if byte == "['']" or byte == "" or byte == " " or byte == "''":
                    continue
                data = json.loads(byte)
                if data[0] != "pong":
                    pass
                # 接收pong
                if data[0] == "pong":
                    self.getPong = True
                    continue
                
                if data[0] == "begin":
                    for str in data[1]:
                        seat = int(str)
                        self.player[seat] = clientConfig.Player(seat,data[1][str])
                        if data[1][str] == self.name:
                            self.seat = seat
                            self.player[seat].mySelf = True
                elif data[0] == "handlist":
                    self.player[self.seat].handList = data[1]["handlist"]
                    self.player[self.seat].handList.sort()
                    # 应该刷新一下
                    self.note = data[0]
                    self.flush = True
                    continue
                elif data[0] == "mopai":
                    self.player[self.seat].moPai = data[1]["pai"]
                    # 应该刷新一下
                    self.note = "canchupai"
                    self.flush = True
                    continue
                elif data[0] == "canchupai":
                    # 显示可以出牌
                    self.note = data[0]
                    self.flush = True
                    continue
                elif data[0] == "choose":
                    self.flush = True
                    # 其余人的出牌改为-1
                    for i in range(0,4):
                        if i == int(seat):
                            continue
                        self.player[i].chuPai = -1
                        self.player[i].choose = []
                    pass
                    # 显示可以选择
                # ["noteall",{seat:msg}]
                # msg = {"chupai":pai}/{"choose":[choose,pai],"chi":[[1,2,3],[]],"peng":[]}
                elif data[0] == "noteall":
                    if "5" in data[1]:
                        self.note = data[1]["5"][0]
                        continue
                    else:
                        for seat in data[1]:
                            # 其余人的出牌改为-1
                            for i in range(0,4):
                                if i == int(seat):
                                    continue
                                self.player[i].chuPai = -1
                                self.player[i].choose = []
                            if "chupai" in data[1][seat]:
                                self.player[int(seat)].chuPai = data[1][seat]["chupai"]
                                self.player[self.seat].flod.append(data[1][seat]["chupai"])                               
                            else:
                                self.player[int(seat)].choose = data[1][seat]["choose"]
                                del data[1][seat]["choose"]
                                self.player[int(seat)].chooseList = data[1][seat]
                            if "handlist" in data[1][seat]:
                                self.player[self.seat].handList = data[1][seat]["handlist"]
                                self.player[self.seat].handList.sort()
                            if "canchupai" in data[1][seat] and data[1][seat]["canchupai"] == self.seat:
                                self.note = "canchupai"
                    self.flush = True
                    if self.note == "canchupai":
                        continue
                self.note = data[0]
                self.msg = data[1]
                # except:
                #     print("接收错误",time.time())
                #     self.note = "break"

    # 大厅界面,改变按键值或者发送登录信息，确认收到反馈后再结束(可以不确认)
    # 使用后self.msg = None
    def gamePage(self,msg):
        os.system('cls')
        print("------------------------")
        print("弃牌:")
        for pai in self.player[self.seat].flod:
            print(self.numToType(pai),end = "||")
        print("\n")
        for seat in range(0,4):
            if seat == self.seat:
                continue
            print("------------------------")
            print("%s号玩家：%s" % (str(seat),self.player[seat].name))
            # print("手牌数：%d" % len(self.player[seat].handList))
            if self.player[seat].chuPai != -1:
                print("出牌:%s" % self.numToType(self.player[seat].chuPai))
            if self.player[seat].choose != []:
                print("选择:%s"%self.player[seat].choose[0])
            self.juZi(seat)
        print("------------------------")
        index = 0
        for num in self.player[self.seat].handList:
            pai = self.numToType(num)
            print(pai,end ="|%d|"%index)
            index += 1
        print("\n")
        self.juZi(self.seat)
        if self.player[self.seat].moPai != -1:
            print("摸到：%s"%self.numToType(self.player[self.seat].moPai),end ="|%d|"%index)
        if self.note == "canchupai":   
            while True:
                paiIndex = input("请输入所要出牌的序号：")
                if paiIndex >= "0" and paiIndex <= "9":
                    if int(paiIndex)  < len(self.player[self.seat].handList):
                        self.conn.sendall(json.dumps(["chupai",{"pai":self.player[self.seat].handList[int(paiIndex)]}]).encode("utf-8"))
                        break
                    elif int(paiIndex)  == len(self.player[self.seat].handList):
                        self.conn.sendall(json.dumps(["chupai",{"pai":self.player[self.seat].moPai}]).encode("utf-8"))
                        break
            self.player[self.seat].moPai = -1
            self.note = "wait"
            self.flush = True
        if self.note == "choose":
            print("请选择：")
            # 显示用
            chooseList1 = []
            # 发送用
            chooseList2 = []
            print("msg",msg)
            for key in msg:
                if key == "chi":
                    for list in msg["chi"]:
                        temp = []
                        for pai in list:
                            temp.append(self.numToType(pai))
                        chooseList1.append(["chi",temp])
                        chooseList2.append(["chi",list])
                elif key == "angang":
                    for list in msg["angang"]:
                        temp = []
                        for pai in list:
                            temp.append(self.numToType(pai))
                        chooseList1.append(["angang",temp])
                        chooseList2.append(["angang",list])
                else:
                    print("error",msg)
                    chooseList1.append([key, self.numToType(msg[key])])
                    chooseList2.append([key, msg[key]])
            # 添加过
            chooseList1.append(["guo", None])
            chooseList2.append(["guo", None])
            index1 = 0
            for list in chooseList1:
                print(list,end ="|%d|"%index1)
                index1 += 1
            while True:
                choose = input("请输入选择的序号：")
                if 0 <= int(choose) < len(chooseList1):
                    self.conn.sendall(json.dumps(["choose",{"action":chooseList2[int(choose)][0],"pailist":chooseList2[int(choose)][1]}]).encode("utf-8")) 
                    break

    # 输出句子
    def juZi(self,seat):
        print("句子：",end = " ")
        for key in self.player[seat].chooseList:
            if key == "chi":
                for list in self.player[seat].chooseList["chi"]:
                    temp = []
                    for pai in list:
                        temp.append(self.numToType(pai))
                    if temp != []:
                        print("吃:%s"%str(temp),end = "||")
            if key == "peng":
                temp = []
                for pai in self.player[seat].chooseList["peng"]:
                    temp.append(self.numToType(pai))
                if temp != []:
                    print("碰:%s"%str(temp),end = "||")
            if key == "minggang":
                temp = []
                for pai in self.player[seat].chooseList["minggang"]:
                    temp.append(self.numToType(pai))
                if temp != []:
                    print("明杠:%s"%str(temp),end = "||")
            if key == "angang":
                temp = []
                for pai in self.player[seat].chooseList["angang"]:
                    temp.append(self.numToType(pai))
                if temp != []:
                    print("暗杠:%s"%str(temp),end = "||")
            if key == "jiagang":
                temp = []
                for pai in self.player[seat].chooseList["jiagang"]:
                    temp.append(self.numToType(pai))
                if temp != []:    
                    print("加杠:%s"%str(temp),end = "||")
        print("\n")
    #  数字转牌字
    def numToType(self,pai):
        list1 = ["一","二","三","四","五","六","七","八","九"]
        list2 = ["筒","条","万"]
        list3 = ["东风","南风","西风","北风","红中","发财","白板"]
        if pai < 27:
            return list1[pai%9] + list2[int(pai/9)] 
        else:
            return list3[pai-27]
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
            result = self.conn.connect_ex(clientConfig.GAME_ADDRESS)
            index = index % 4
            msg = "\r正在连接 " + ch_list[index]
            print(msg, end="")
            index += 1 
        os.system('cls')

    # 等待其他玩家
    def waitPlayerPage(self):
        os.system('cls')
        index = 0
        ch_list = ["\\", "|", "/", "-"]
        while self.flush == False: 
            index = index % 4
            msg = "\r房间号：%s,正在等待其他玩家 "%str(self.roomId) + ch_list[index]
            print(msg, end="")
            index += 1 
        os.system('cls')