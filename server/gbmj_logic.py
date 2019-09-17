#coding=utf8
# 国标麻将
# chi angang hu都是list类型发送和接收

import random
from player import Player
import copy
import json
import os
import signal 
import sys
import time
from dbUtil import DBUtil
import socket
import config
from copy import deepcopy

class GBMJ():
    def __init__(self,id0,id1,id2,id3,roomid):
        # 房间号
        self.roomid = roomid
        self.db = DBUtil()
        # 总牌数
        self.countOfPai = 0
        # 存放所有牌
        self.majiang = []
        # 弃牌
        self.fold = []
        # 当前发牌序号
        self.currentPaiIndex = 0
        # 初始化玩家
        self.playList = [Player(0,id0),Player(1,id1),Player(2,id2),Player(3,id3)]
        # 确定0号位为庄家
        self.banker = self.playList[0]
        # 当前摸牌出牌玩家（序号）
        self.currentSeatIndex = self.banker.seatIndex
        # 决策选择
        self.actionSwitch = {
            "peng":    self.peng,
            "minggang":self.mingGang,
            "jiagang": self.jiaGang,
            "guo":     self.guo
        }
        # 罚分计时
        self.startTime = 0.0
        self.endTime = 0.0
        # 重新开局个数
        self.numOfCotinue = []
    
    # 下一摸牌玩家
    def nextPlayer(self):
        self.currentSeatIndex = (self.currentSeatIndex + 1) % 4

    # 初始化牌
    def initPai(self):
        # 新开局的一些初始化
        self.countOfPai = 0
        # 存放所有牌
        self.majiang = []
        # 弃牌
        self.fold = []
        # 当前发牌序号
        self.currentPaiIndex = 0
        # 当前摸牌出牌玩家（序号）
        self.currentSeatIndex = self.banker.seatIndex
        # 罚分计时
        self.startTime = 0.0
        self.endTime = 0.0
        # 玩家信息初始化
        for index in range(0,4):
            self.playList[index].init()
        # 重新开局个数
        self.numOfCotinue = []
            
        # 筒 0 ~ 8
        for i in range(0,9):
            for j in range(0,4):
                self.majiang.append(i)
                self.countOfPai += 1
        # 条 9 ~ 17
        for i in range(9,18):
            for j in range(0,4):
                self.majiang.append(i)
                self.countOfPai += 1
        # 万 18 ~ 26
        for i in range(18,27):
            for j in range(0,4):
                self.majiang.append(i)
                self.countOfPai += 1
        # 东南西北中发白 27 ~ 33
        for i in range(27,34):
            for j in range(0,4):
                self.majiang.append(i)
                self.countOfPai += 1
        # # 春夏秋冬梅兰竹菊
        # for i in range(34,42):
        #     self.majiang.append(i)
        #     self.countOfPai += 1

    # 洗牌
    def shuffle(self):
        for index in range(0,len(self.majiang)):
            randomIndex = random.randint(0,len(self.majiang)-1)
            temp = self.majiang[index]
            self.majiang[index] = self.majiang[randomIndex]
            self.majiang[randomIndex] = temp

    # 发牌
    def deal(self):
        # 每人13张,庄家多一张 共53张
        seatIndex = 0
        for i in range(0,52):
            self.playList[seatIndex].handList.append(self.majiang[i])
            seatIndex = (seatIndex + 1) % 4
        # 通知每位玩家手牌
        for index in range(0,4):
            self.noteHandList(index)
        # 防止两条指令到达客户端后续优化
        # time.sleep(1)
        self.currentPaiIndex = 52
        self.moPai(self.banker.seatIndex)

    # 出牌
    def chuPai(self,seatIndex,pai):
        # 确定当前轮玩家，出牌，改变手牌，其他玩家检查是否可以胡杠碰吃,弃牌
        if self.currentSeatIndex is not seatIndex:
            return
        # 所有玩家清除可以吃碰杠以及对应的牌
        for index in range(0,4):
            self.playList[index].clearCan()

        player = self.playList[seatIndex]
        player.chuMo = True
        # 改变手牌
        player.handList.remove(pai)
        player.chuPai = pai
        # 检查听牌列表有没有变
        if self.checkHandTing(player):
            self.checkCanTing(seatIndex)
        print("KeYiTing?",player.canTing)
        # 检查是否可以胡
        for index in range(0,4):
            if index == seatIndex:
                continue
            if self.checkCanHu(index,pai):
                self.note(index)
                return
        # 检查是否可以碰明杠,当下家可以碰杠时同时下家检查是否可以吃
        for index in range(0,4):
            if index == seatIndex:
                continue
            if self.checkCanMingGang(index,pai) or self.checkCanPeng(index,pai):
                if index == (seatIndex+1)%4:
                    self.checkCanChi(index,pai)
                self.note(index)
                return
        # 检查下家是否可以吃
        index = (seatIndex+1)%4
        if self.checkCanChi(index,pai):
            self.note(index)
            return
        # 弃牌
        self.fold.append(pai)
        self.noteALL(seatIndex,{"chupai":pai})
        # 下一位
        self.nextPlayer()
        self.moPai(self.currentSeatIndex)
    
    # 检查手牌和听牌列表是否一致
    def checkHandTing(self,player):
        _bool = False
        if player.handList != player.tingList:
            player.canTing = False
            player.resetTingHuType()
            _bool = True
        return _bool
    
    # 摸牌
    def moPai(self,seatIndex):
        # 确定当前轮玩家，还有牌，摸牌，判断是否可以胡暗杠加杠
        if self.currentPaiIndex >= self.countOfPai - 1:
            self.result(False)
            return
        if self.currentSeatIndex is not seatIndex:
            return
        # 所有玩家清除可以吃碰杠以及对应的牌
        for index in range(0,4):
            self.playList[index].clearCan()
        
        self.playList[seatIndex].chuMo = False
        pai = self.majiang[self.currentPaiIndex]
        
        # 判断是否可以胡
        if self.checkCanHu(seatIndex,pai):
            self.note(seatIndex)
            return
        # 添加手牌
        self.playList[seatIndex].handList.append(pai)
        self.playList[seatIndex].moPai = pai
        self.currentPaiIndex += 1
        # 判断是否可以暗杠
        if self.checkCanAnGang(seatIndex,pai):
            self.note(seatIndex)
            return
        # 抢杠
        if self.checkCanJiaGang(seatIndex,pai):
            for index in range(0,4):
                if(index == seatIndex):
                    continue
                if self.checkCanHu(index,pai):
                    self.playList[seatIndex].canJiaGang = False
                    self.note(index)
                    return
            self.note(seatIndex)
        # 通知摸到的牌并且可以出牌
        self.noteMoPai(seatIndex,pai)
    # 通知手牌 
    def noteHandList(self,seatIndex):
        print("noteHandList",seatIndex)
        conn = self.sock(seatIndex)
        bytes = json.dumps(["handlist",{"handlist":self.playList[seatIndex].handList}]).encode("utf-8")
        conn.sendall(bytes)
    # 通知摸到的牌
    def noteMoPai(self,seatIndex,pai):
        print("noteMoPai",seatIndex,pai)
        conn = self.sock(seatIndex)
        self.startTime = time.time()
        bytes = json.dumps(["mopai",{"pai":pai,"canchupai":seatIndex}]).encode("utf-8")
        conn.sendall(bytes)
    # 使用通信模块，通知seatIndex可以出牌
    def noteChupai(self,seatIndex):
        print("noteChupai",seatIndex)
        self.startTime = time.time()
        conn = self.sock(seatIndex)
        bytes = json.dumps(["canchupai",{"canchupai":seatIndex}]).encode("utf-8")
        conn.sendall(bytes)
    # 使用通信模块，通知seatIndex进行决策选择
    def note(self,seatIndex):
        print("note",seatIndex)
        self.startTime = time.time()
        conn = self.sock(seatIndex)
        msg = {}
        player = self.playList[seatIndex]
        if player.canChi:
            msg["chi"] = player.canChiPai
        if player.canPeng:
            msg["peng"] = player.canPengPai
        if player.canAnGang:
            msg["angang"] = player.canAnGangPai
        if player.canMingGang:
            msg["minggang"] = player.canMingGangPai
        if player.canJiaGang:
            msg["jiagang"] = player.canJiaGangPai
        if player.canHu:
            msg["hu"] = player.canHuPai 
        print("error",msg)
        bytes = json.dumps(["choose",msg]).encode("utf-8")
        conn.sendall(bytes)
    # 使用通信模块广播
    # 广播内容：
    # ["noteall",{seat:msg}]
    # msg = {"chupai":pai}/{"choose":[choose,pai],"chi":[[1,2,3],[]],"peng":[]}+手牌+是否可以出牌
    # seatIndex = 5时，通知全员
    def noteALL(self,seatIndex,msg):
        print("noteALL",seatIndex)
        for index in range(0,4):
            # 通知自己的手牌
            if seatIndex != 5:
                tempMsg = deepcopy(msg)
                tempMsg["handlist"] = self.playList[index].handList
                conn = self.sock(index)
                bytes = json.dumps(["noteall",{str(seatIndex):tempMsg}]).encode("utf-8")
                conn.sendall(bytes)
                continue
            conn = self.sock(index)
            bytes = json.dumps(["noteall",{str(seatIndex):msg}]).encode("utf-8")
            conn.sendall(bytes)

    # 通过seatIndex查询玩家socket
    def sock(self,seatIndex):
        return config.GAME_CONN_POOL[self.roomid][self.playList[seatIndex].id]
    
    # 吃碰杠听胡过选择
    def choose(self,seatIndex,action,paiList):
        if action == "chi":
            self.chi(seatIndex,paiList)
        elif action == "hu":
            self.hu(seatIndex,paiList)
        elif action == "angang":
            self.anGang(seatIndex,paiList)
        else:
            self.actionSwitch.get(action)(seatIndex)   
    
    # 是否可以听牌
    def checkCanTing(self,seatIndex):
        # 不提醒玩家选择，保存听的牌，作为玩家胡的判别标准，有UI时提醒用户正在听牌和出那张牌
        player = self.playList[seatIndex]

        # 添加一张凑够牌，添加牌的要求：不在其他玩家和自己的杠里，所有玩家的吃够不够四张，也不在弃牌里
        for addPai in range(0,34):
            # 判断能否使用addPai
            conti = 0
            chiCount = 0
            for index in range(0,4):
                tempPlayer = self.playList[index]
                if addPai in tempPlayer.anGangPai or \
                    addPai in tempPlayer.jiaGangPai or \
                        addPai in tempPlayer.mingGangPai:
                        conti = 1
                        break
                for chiList in tempPlayer.chiPai:
                    for pai in chiList:
                        if addPai == pai:
                            chiCount += 1
            if self.fold.count(addPai) == 4 or conti == 1 or chiCount == 4:
                continue
            # 新建手牌列表
            handList = []
            for pai in player.handList:
                handList.append(pai)
            handList.append(addPai)
            handList.sort()
            # 初始化(胡牌类型及番数)的列表作为键str(addPai)的值放入字典
            finalHuType = []
            # 计算手牌中有多少个list2,字牌的list2
            list1 = self.countList(handList,1)
            list2_ = self.countList(handList,2)
            # 先判断特殊牌型
            # 七对
            if self.checkQiDui(list2_):
                self.simpleAdd(finalHuType,"qidui",24)
                continue
            # 十三幺0,8,9,17,18,26,27,28,29,30,31,32,33
            if self.checkShiSanYao(handList,list1,list2_):
                self.simpleAdd(finalHuType,"shisanyao",88)
                continue         
            # 拆分，跳过
            _list = self.split123(handList,list1,list2_)
            
            if len(_list) == 0:
                continue
            self._list = _list
            gangList = self.gangList(player)
            chiPengGangList = self.chiPengGangList(gangList,player)
        
            # 遍历各个addPai的_List中的组合,取各addPai中番数和最大的一种情况,并保存此时的组合方法
            tempHuType = []
            tempSplit = []
            for tempList in _list:
                huType = []
                list2 = tempList[0]
                list3 = tempList[1]
                list123 = tempList[2] 
                if len(list2) != 1 or len(list3)+len(gangList)+len(list123)+len(player.pengPai)+len(player.chiPai) != 4:
                    continue
                # 开始判断，从高到低注意叠加
                # 大四喜
                if self.checkDaSiXi(player,list2,gangList):
                    self.simpleAdd(huType,"dasixi",88)
                # 大三元
                if self.checkDaSanYuan(player,list2,list3,list123,gangList):
                    self.simpleAdd(huType,"dasanyuan",88)
                # 绿一色
                if self.checkLvYiSe(handList,chiPengGangList):
                    self.simpleAdd(huType,"lvyise",88)
                # 四杠
                if self.checkSiGang(gangList,list2):
                    self.simpleAdd(huType,"sigang",88)
                # 小四喜
                if self.checkXiaoSiXi(player,handList,gangList,list2,list3,list123):
                    self.simpleAdd(huType,"xiaosixi",64)
                # 小三元
                if self.checkXiaoSanYuan(player,gangList,list2,list3,list123):
                    self.simpleAdd(huType,"xiaosanyuan",64)
                # 字一色
                if self.checkZiYiSe(player,chiPengGangList,handList,gangList,list2,list3,list123):
                    self.simpleAdd(huType,"ziyise",64)
                # 四暗刻
                if self.checkSiAnKe(player,list2,list3):
                    self.simpleAdd(huType,"sianke",64)
                # 清幺九 
                if self.checkQingYaoJiu(player,gangList,list2,list3,list123):
                    self.simpleAdd(huType,"qingyaojiu",64)
                # 一色四同顺
                if self.checkYiSeSiTongShun(player,list123):
                    self.simpleAdd(huType,"yisesitongshun",48)
                # 三杠
                if "sigang" not in huType:
                    if self.checkSanGang(gangList):
                        self.simpleAdd(huType,"sangang",32)
                # 混幺九
                if "shisanyao" not in huType:
                    if self.checkHunYaoJiu(player,chiPengGangList,handList,list123):
                        self.simpleAdd(huType,"hunyaojiu",32)
                # 清一色
                if self.checkQingYiSe(chiPengGangList,handList):
                    self.simpleAdd(huType,"qingyise",24)
                # 一色三同顺
                if "yisesitongshun" not in huType:
                    if self.checkYiSeSanTongShun(player,list123):
                        self.simpleAdd(huType,"yisesantongshun",24)
                # 三同刻
                if self.checkSanTongKe(player,gangList,list3):
                    self.simpleAdd(huType,"santongke",16)
                # 三暗刻
                if "sianke" not in huType:
                    if self.checkSanAnKe(player,list3):
                        self.simpleAdd(huType,"sananke",16)
                # 三色三同顺
                if self.checkSanSeSanTongShun(player,list123):
                    self.simpleAdd(huType,"sansesantongshun",8)
                # 碰碰和
                if "dasixi" not in huType and "sigang" not in huType and "ziyise" not in huType \
                    and "sianke" not in huType and "qingyaojiu" not in huType and "hunyaojiu" not in huType:
                    if self.checkPengPenghu(player,gangList,list3):
                        self.simpleAdd(huType,"pengpenghu",6)
                # 混一色
                if self.checkHunYiSe(handList,chiPengGangList):
                    self.simpleAdd(huType,"hunyise",6)
                # 五门齐
                if "shisanyao" not in huType:
                    if self.checkWuMenQi(handList,chiPengGangList):
                        self.simpleAdd(huType,"wumenqi",6)
                # 门前清 __如果有门前清，则需要是胡别人的牌才能算番(到时候改)
                if "shisanyao" not in huType and "sianke" not in huType and "qidui" not in huType:
                    if self.checkMenQianQing(player,list3,list123):
                       self.simpleAdd(huType,"menqianqing",0)
                #  断幺
                if self.checkDuanYao(handList,chiPengGangList):
                    self.simpleAdd(huType,"duanyao",2)
                # 平和
                if self.checkPingHe(player,list2,list123):
                    self.simpleAdd(huType,"pinghe",2)
                # 箭刻
                if "dasanyuan" not in huType and "xiaosanyuan" not in huType:
                    jianKeCount = self.checkJianKe(player,list3)
                    if jianKeCount != 0:
                        self.simpleAdd(huType,"jianke",2*jianKeCount)
                # 暗杠
                anGangCount = self.checkAnGang(player)
                if anGangCount != 0:
                    self.simpleAdd(huType,"anang",2*anGangCount)
                # 自摸 __需要自己摸的牌胡
                self.simpleAdd(huType,"zimo",0)
                # 一般高
                if "yisesitongshun" not in huType and "yisesantongshun" not in huType:
                    yiCount = self.checkYiBanGao(player,list123) 
                    if yiCount != 0:
                        self.simpleAdd(huType,"yibangao",1*yiCount)
                # 喜相逢
                if "sansesantongshun" not in huType and "yisesantongshun" not in huType and "yisesitongshun" not in huType:
                    xiCount = self.checkXiXiangFeng(player,list123)
                    if xiCount != 0:
                        self.simpleAdd(huType,"xixiangfeng",1*xiCount)
                # 明杠
                mingGangCount = self.checkMingGang(player)
                if mingGangCount != 0:
                    self.simpleAdd(huType,"minggang",1*mingGangCount)
                # 单钓将 
                if "shisanyao" not in huType and "qidui" not in huType:
                    if self.checkDanDiaoJiang(list2,addPai):
                        self.simpleAdd(huType,"dandiaojiang",1)
                # 小胡
                if len(huType) == 2 and "zimo" in huType:
                    self.simpleAdd(huType,"xiaohu",1)
                tempHuType.append(huType)
                tempSplit.append([list2,list3,list123])
            if tempHuType == []:
                continue
            # 当前addPai在tempHuType中选取番数和最大的一个作为finalHuType
            maxFanShu = 0
            maxhuType = []
            for huType in tempHuType:
                fanShu = 0
                i = 1
                while i < len(huType):
                        fanShu += huType[i]
                        i += 2
                if fanShu > maxFanShu:
                    maxFanShu = fanShu
                    maxhuType = huType
            for cont in maxhuType:
                finalHuType.append(cont)
            
            # huType非空的话，听牌序列改为手牌，将str(addPai)：huType放入字典tingHuType，空的话，删除SplitList中该项
            if finalHuType != []:
                if "qidui" in finalHuType:
                    split = [list2_,[],[]]
                elif "ahisanyao" in finalHuType:
                    split = [list1,list2_,[],[]]
                else:
                    split = tempSplit[tempHuType.index(maxhuType)]
                player.canTing = True
                player.tingList = copy.deepcopy(player.handList)
                # 将str(addPai)：[huType,split]放入字典tingHuType
                player.tingHuType[str(addPai)] = [finalHuType,split]
                self.addTingPai(player,addPai)
    
    # 单钓将 钓单张牌作将成和
    def checkDanDiaoJiang(self,list2,addPai):
        if addPai in list2:
            return True
        return False
    
    # 明杠
    def checkMingGang(self,player):
        return len(player.mingGangPai)+len(player.jiaGangPai)
    
    # 喜相逢 2种花色2副序数相同的顺子（可算多次）
    def checkXiXiangFeng(self,player,list123):
        yushuList = []
        count = 0
        if len(list123) + len(player.chiPai) >= 2:
            for j in list123,player.chiPai:
                for i in j:
                    yushuList.append(i[0] % 9)
            for i in yushuList:
                if yushuList.count(i) == 2:
                    flag = 0
                    for j in range(0,3):
                        paiList = [j*9+i,j*9+i+1,j*9+i+2]
                        if list123.count(paiList) + player.chiPai.count(paiList) == 2:
                            flag = 1
                            break
                    if flag == 1:
                        continue
                    else:
                        count += 1
                    yushuList.remove(i)
                    yushuList.remove(i)
                if yushuList.count(i) == 3:
                    count = 1
                    break
                if yushuList.count(i) == 4:
                    count = 2
                    break
        return count
    
    # 一般高 由一种花色2副相同的顺子组成的牌（可算多次）
    def checkYiBanGao(self,player,list123):
        count = []
        if len(list123) + len(player.chiPai) >= 2:
            for _list in list123,player.chiPai:
                for i in _list:
                    if list123.count(i) + player.chiPai.count(i) >= 2:
                        if i not in count:
                            count.append(i)
        return len(count)
    
    # 暗杠 可算多次
    def checkAnGang(self,player):
        return len(player.anGangPai)
    
    # 箭刻 由中、发、白3张相同的牌组成的刻子（可算多次）31,32,33
    def checkJianKe(self,player,list3):
        count = 0
        for paiList in player.pengPai,list3:
            for pai in paiList: 
                if pai in range(31,34):
                    count += 1
        return count

    # 平和 由4副顺子及序数牌作将组成的和牌
    def checkPingHe(self,player,list2,list123):
        if len(player.chiPai) + len(list123) == 4 and list2[0] < 27:
            return True
        return False

    # 断幺 和牌中没有一、九及字牌
    def checkDuanYao(self,handList,chiPengGangList):
        tempList = [0,8,9,17,18,26,27,28,29,30,31,32,33]
        for paiList in handList,chiPengGangList:
            for pai in paiList:
                if pai in tempList:
                    return False
        return True
    
    # 门前清 没有吃、碰、明杠而听牌，和别人打出的牌
    def checkMenQianQing(self,player,list3,list123):
        if len(player.anGangPai) + len(list3) + len(list123)== 4:
            return True
        return False
    
    # 五门齐 和牌时3种序数牌、风、箭牌齐全
    def checkWuMenQi(self,handList,chiPengGangList):
        checkType = []
        for paiList in handList,chiPengGangList:
            for pai in paiList:
                shang = int(pai/9)
                if shang == 0 and "tong" not in checkType:
                    checkType.append("tong")
                elif shang == 1 and "tiao" not in checkType:
                    checkType.append("tiao")
                elif shang == 2 and "wan" not in checkType:
                    checkType.append("wan")
                elif shang == 3:
                    if pai in range(27,31) and "feng" not in checkType:
                        checkType.append("feng")
                    elif pai in range(31,34) and "jian" not in checkType:
                        checkType.append("jian")
        if len(checkType) == 5:
            return True
        return False
    
    # 混一色 由一种花色序数牌及字牌组成的和牌
    def checkHunYiSe(self,handList,chiPengGangList):
        huase = -1
        for paiList in handList,chiPengGangList:
            for pai in paiList:
                if pai < 27:
                    if huase == -1:
                        huase = int(pai/9)
                    elif int(pai/9) != huase:
                        return False
        return True

    # 碰碰和 4副刻子（或杠）
    def checkPengPenghu(self,player,gangList,list3):
        if len(gangList) + len(list3) == 4:
            return True
        return False
    
    # 三色三同顺 有3种花色3副序数相同的顺子
    def checkSanSeSanTongShun(self,player,list123):
        yushuList = []
        if len(list123) + len(player.chiPai) >= 3:
            for j in list123,player.chiPai:
                for i in j:
                    yushuList.append(i[0] % 9)
            for i in yushuList:
                if yushuList.count(i) >= 3:
                    for j in range(0,3):
                        paiList = [j*9+i,j*9+i+1,j*9+i+2]
                        if paiList not in list123 or paiList not in player.chiPai:
                            return False
                    return True
        return False
            
    # 三暗刻 有3个暗刻(杠)
    def checkSanAnKe(self,player,list3):
        if len(player.anGangPai) + len(list3)== 3:
            return True
        return False

    # 三同刻 3个序数相同的刻子(杠)
    def checkSanTongKe(self,player,gangList,list3):
        if len(list3) + len(player.pengPai) + len(gangList) >= 3:
            yushuList = []
            for j in list3,gangList,player.pengPai:
                for i in j:
                    if i < 27:
                        yushuList.append(i % 9)
            for i in yushuList:
                if yushuList.count(i) >= 3:
                    return True
        return False
                
    # 一色三同顺 一种花色3副序数相同的顺子
    def checkYiSeSanTongShun(self,player,list123):
        if len(list123) + len(player.chiPai) >= 3:
            for _list in list123,player.chiPai:
                for i in _list:
                    if list123.count(i) + player.chiPai.count(i) >= 3:
                        return True
        return False
        
    # 清一色 由一种花色的序数牌组成
    def checkQingYiSe(self,chiPengGangList,handList):
        huase = -1
        for paiList in handList,chiPengGangList:
            for pai in paiList:
                if pai > 26:
                    return False
                if huase == -1:
                    huase = int(pai/9)
                elif int(pai/9) != huase:
                    return False
        return True
    
    # 混幺九 字牌和序数牌一、九组成的和牌
    def checkHunYaoJiu(self,player,chiPengGangList,handList,list123):
        tempList = [0,8,9,17,18,26,27,28,29,30,31,32,33]
        if len(list123) == 0 and len(player.chiPai) == 0:
            for j in handList,chiPengGangList:
                for i in j:
                    if i not in tempList:
                        return False
            return True
        return False
    
    # 三杠 
    def checkSanGang(self,gangList):
        if len(gangList) == 3:
            return True
        return False
    
    # 一色四同顺 一种花色4副序数相同的顺子
    def checkYiSeSiTongShun(self,player,list123):
        if len(list123) + len(player.chiPai) == 4:
            tempList = []
            for list in list123,player.chiPai:
                for subList in list:
                    tempList.append(subList)
            if tempList.count(tempList[0]) == 4:
                return True
        return False

    # 清幺九 1、9组成刻子（杠）、将牌
    def checkQingYaoJiu(self,player,gangList,list2,list3,list123):
        tempList = [0,8,9,17,18,26]
        if len(list123) == 0 and len(player.chiPai) == 0 and list2[0] in tempList:
            for j in list3,gangList,player.pengPai:
                for i in j:
                    if i not in tempList:
                        return False
            return True
        return False

    # 四暗刻 4个暗刻（list3 + angang + list4 == 4）
    def checkSiAnKe(self,player,list2,list3):
        if len(player.anGangPai) + len(list3) == 4:
            return True
        return False
    
    # 字一色 27-33
    def checkZiYiSe(self,player,chiPengGangList,handList,gangList,list2,list3,list123):
        tempList = [27,28,29,30,31,32,33]
        if len(list123) == 0 and len(player.chiPai) == 0:
            for j in handList,chiPengGangList:
                for i in j:
                    if i not in tempList:
                        return False
                return True
        return False 
    
    # 小三元 31 32 33(wenti)
    def checkXiaoSanYuan(self,player,gangList,list2,list3,list123):
        count = 0
        if list2[0] in range(31,34):
            for i in range(31,34):
                if i in list2 or i in list3 or i in gangList or i in player.pengPai:
                    count += 1
            if count == 3:
                return True
        return False
    
    # 小四喜 风牌的三副刻子（杠），第四种风牌作将,27,28,29,30(wenti)
    def checkXiaoSiXi(self,player,handList,gangList,list2,list3,list123):
        count = 0
        tempList = [27,28,29,30]
        if list2[0] in tempList:
            for i in tempList:
                if i in list2 or i in list3 or i in gangList or i in player.pengPai:
                    count += 1
            if count == 4:
                return True
        return False
             
    # 四缸
    def checkSiGang(self,gangList,list2):
        if len(gangList) == 4:
            return True
        return False

    # 绿一色 23468条及发
    def checkLvYiSe(self,handList,chiPengGangList):
        tempList = [10,11,12,14,16,32]
        for paiList in handList,chiPengGangList:
            for pai in paiList:
                if pai not in tempList:
                    return False
        return True
    
    # 大三元 有中发白3副刻(杠)(手牌，碰31,32,33)
    def checkDaSanYuan(self,player,list2,list3,list123,gangList):
        count = 0
        for pai in range(31,34):
            if pai in list3 or pai in player.pengPai or pai in gangList:
                count += 1
        if count == 3:
            return True
        return False

    # 大四喜 4副风碰27,28,29,30（杠）组成的和牌
    def checkDaSiXi(self,player,list2,gangList):
        for i in range(27,31):
            if i not in gangList and i not in player.pengPai:
                return False
        return True
        
    # 七对
    def checkQiDui(self,list2):
        if len(list2) == 7:
            return True
        return False

    # 十三幺0,8,9,17,18,26,27,28,29,30,31,32,33
    def checkShiSanYao(self,handList,list1,list2):
        tempList = [0,8,9,17,18,26,27,28,29,30,31,32,33]
        if len(list1) == 12 and len(list2) == 1:
            for pai in handList:
                if pai not in tempList:
                    return False
            return True
        return False
                
    # 吃碰杠的牌型列表 
    def chiPengGangList(self,gangList,player):
        chiPengGangList = []
        for pai in gangList:
            chiPengGangList.append(pai)
        for pai in player.pengPai:
            chiPengGangList.append(pai)
        for _list in player.chiPai:
            for pai in _list:
                chiPengGangList.append(pai)
        return chiPengGangList

    # 吃碰杠组成列表
    # {"choose":[choose,pai],"chi":[[1,2,3],[]],"peng":[]}
    def chooseList(self,seatIndex,choose,paiList):
        player = self.playList[seatIndex]
        chooseList = {}
        chooseList["choose"] = [choose,paiList]        
        chooseList["chi"] = player.chiPai
        chooseList["peng"] = player.pengPai
        chooseList["minggang"] = player.mingGangPai
        chooseList["angang"] = player.anGangPai
        chooseList["jiagang"] = player.jiaGangPai
        return chooseList
    # 三种杠的牌型列表
    def gangList(self,player):
        gangList = []
        for pai in player.anGangPai:
            gangList.append(pai)
        for pai in player.mingGangPai:
            gangList.append(pai)
        for pai in player.jiaGangPai:
            gangList.append(pai)
        return gangList
             
    def simpleAdd(self,huType,typeStr,fan):
        huType.append(typeStr)
        huType.append(fan)

    def addTingPai(self,player,addPai):
        if addPai not in player.tingPai:
            player.tingPai.append(addPai)
    
    # 计算并返回手牌中list
    def countList(self,handList,num):
        list = []
        for pai in handList:
            if handList.count(pai) == num and pai not in list:
                list.append(pai)
        return list
                
    # 手牌中
    # 先判断27-33的牌的个数，1张和对于一个的对子结束否
    # 再顺序遍历0-26中可以组成顺子的或没有顺子时，且有list2 > 1,放入splitList中
    # return list[list123[[123],],list3]，
    def split123(self,handList,list1,list2):
        _list = []
        _list2 = []
        list3 = []
        list123 = []
        ziPai2 = []
        
        for pai in range(27,34):
            if pai in list1 or handList.count(pai) == 4:
                return _list
            if pai in list2:
                ziPai2.append(pai)

        if len(ziPai2) > 1:
            return _list
        # 获取手牌中的序数牌
        tempList = []
        for pai in handList:
            if pai < 27:
                tempList.append(pai)
        # 从第一种牌型开始查找各种顺子组合的情况
        prePai = -1
        for tempPai in tempList:
            _list2 = []
            list3 = []
            list123 = []
            shuPai2 = 0
            # 查看上一种牌型是否只有一张
            if prePai != -1:
                if tempList.count(prePai) == 1 or tempList.count(prePai) == 4:
                    return _list
            # 跳过相同的牌，到达下一种牌型
            if tempPai == prePai:
                continue
            prePai = tempPai
            # 获取当前指针指向的序数            
            index = tempList.index(tempPai)
            # 获取已经跳过的子列表
            preSub = []
            for i in range(0,index):
                preSub.append(tempList[i])
            # 判断前子列表的组合形式（list2/list3）
            preIndex = 0
            ifcontinue = 0
            while len(preSub) > 0:
                pai = preSub[preIndex]
                if preSub.count(pai) == 2:
                    shuPai2 += 1
                    if shuPai2 + len(ziPai2) > 1:
                        return _list
                    _list2.append(pai)
                    for i in range(0,2):
                        preSub.remove(pai)
                elif preSub.count(pai) == 3:
                    list3.append(pai)
                    for i in range(0,3):
                        preSub.remove(pai)

            # 获取后面的子列表
            latSub  = []
            for i in range(index,len(tempList)):
                latSub.append(tempList[i])
            # 遍历latSub,查看当前组合是否合理
            latIndex = 0
            while len(latSub) > 0: 
                pai = latSub[latIndex]
                if pai % 9 <= 6 and latSub.count(pai+1) != 0 and latSub.count(pai+2) != 0:
                    list123.append([pai,pai+1,pai+2])
                    latSub.remove(pai)
                    latSub.remove(pai+1)
                    latSub.remove(pai+2)
                else:          
                    if latSub.count(pai) == 1:
                        ifcontinue = 1
                        break
                    elif latSub.count(pai) == 2:
                        shuPai2 += 1
                        if shuPai2 + len(ziPai2) > 1:
                            ifcontinue = 1
                            break
                        _list2.append(pai)
                        for i in range(0,2):
                            latSub.remove(pai)
                    elif latSub.count(pai) == 3:
                        list3.append(pai)
                        for i in range(0,3):
                            latSub.remove(pai)
                    elif latSub.count(pai) == 4:
                        return _list
            if ifcontinue == 1:
                continue
            if len(_list2) == 0 and len(ziPai2) == 1:
                    _list2.append(ziPai2[0])
            #  当前组合合理
            for pai in range(27,34):
                if handList.count(pai) == 3:
                    list3.append(pai)
            _list.append([_list2,list3,list123])
        return _list
        

    # 是否可以胡
    def checkCanHu(self,seatIndex,pai):
        player = self.playList[seatIndex]
        if player.canTing:
            if pai in player.tingPai:
                player.canHu = True
                player.canHuPai = pai
                return True
            else:
                return False

    # 是否可以明杠
    def checkCanMingGang(self,seatIndex,pai):
        # 手里有三张一样的
        player = self.playList[seatIndex]
        if player.handList.count(pai) == 3:
            player.canMingGang = True
            player.canMingGangPai = pai
            return True
        else:
            return False
    
    # 是否可以暗杠(有问题)
    def checkCanAnGang(self,seatIndex,pai):
        # 手里有四张一样的
        player = self.playList[seatIndex]
        for pai in player.handList:
            if pai in player.canAnGangPai:
                continue
            if player.handList.count(pai) == 4:
                player.canAnGang = True
                player.canAnGangPai.append(pai)
        if player.canAnGangPai != []:
            return True
        else:
            return False
    
    # 是否可以加杠
    def checkCanJiaGang(self,seatIndex,pai):
        # 手上有碰
        player = self.playList[seatIndex]
        if pai in player.pengPai:
            player.canJiaGang = True
            player.canJiaGangPai = pai
            return True
        else:
            return False
    
    # 是否可以碰
    def checkCanPeng(self,seatIndex,pai):
        # 手上有两张一样的
        player = self.playList[seatIndex]
        if player.handList.count(pai) == 2:
            player.canPeng = True
            player.canPengPai = pai
            return True
        else:
            return False

    # 是否可以吃
    def checkCanChi(self,seatIndex,pai):
        if (pai >= 27 and pai <= 33):
            return False
        player = self.playList[seatIndex]
        # 余数0-6
        if pai%9 < 7:
            if pai+1 in player.handList and pai+2 in player.handList:
                player.canChi = True
                player.canChiPai.append([pai,pai+1,pai+2])
        # 余数1-7
        if pai%9 > 0 and pai%9 < 8:
            if pai-1 in player.handList and pai+1 in player.handList:
                player.canChi = True
                player.canChiPai.append([pai-1,pai,pai+1])
        # 余数2-8
        if pai%9 > 1 and pai%9 < 9:
            if pai-1 in player.handList and pai-2 in player.handList:
                player.canChi = True
                player.canChiPai.append([pai-2,pai-1,pai])
        if player.canChi:
            return True
        else:
            return False
        
    # 明杠
    def mingGang(self,seatIndex):
        # 明杠列表里添加，删除手牌，补一张牌
        player = self.playList[seatIndex]
        pai = player.canMingGangPai
        player.mingGangPai.append(pai)
        while player.handList.count(pai) > 0:
            player.handList.remove(pai)
        # 检查听牌列表有没有变
        self.checkHandTing(player)
        self.noteALL(seatIndex,self.chooseList(seatIndex,"minggang",pai))
        # 摸牌出牌
        self.currentSeatIndex = seatIndex
        self.moPai(seatIndex)
        
    # 暗杠
    def anGang(self,seatIndex,paiList):
        # 暗杠列表里添加，删除手牌，补一张牌
        player = self.playList[seatIndex]
        player.anGangPai.append(paiList[0])
        while player.handList.count(paiList[0]) > 0:
            player.handList.remove(paiList[0])
        # 检查听牌列表有没有变
        self.checkHandTing(player)
        self.noteALL(seatIndex,self.chooseList(seatIndex,"angang",paiList[0]))
        # 摸牌出牌
        self.currentSeatIndex = seatIndex
        self.moPai(seatIndex)

    # 加杠
    def jiaGang(self,seatIndex):
        # 加杠列表里添加，删除对应碰牌，补一张牌
        player = self.playList[seatIndex]
        pai = player.canJiaGangPai
        player.pengPai.remove(pai)
        player.handList.remove(pai)
        player.jiaGangPai.append(pai)
        # 检查听牌列表有没有变
        self.checkHandTing(player)
        self.noteALL(seatIndex,self.chooseList(seatIndex,"jiagang",pai))
        # 摸牌出牌
        self.currentSeatIndex = seatIndex
        self.moPai(seatIndex)

    # 碰
    def peng(self,seatIndex):
        # 碰列表里添加，删除手牌，轮换到下一人
        player = self.playList[seatIndex]
        pai = player.canPengPai
        player.pengPai.append(pai)
        while player.handList.count(pai) != 0:
            player.handList.remove(pai)
        # 检查听牌列表有没有变
        self.checkHandTing(player)
        msg = self.chooseList(seatIndex,"peng",pai)
        msg["canchupai"] = seatIndex
        self.startTime = time.time()
        self.noteALL(seatIndex,msg)
        self.currentSeatIndex = seatIndex

    # 吃
    def chi(self,seatIndex,paiList):
        # 吃列表里添加子列表，删除手牌，轮换到下一人
        player = self.playList[seatIndex]
        player.chiPai.append(paiList)
        for pai in paiList:
            if pai == self.playList[self.currentSeatIndex].chuPai:
                continue
            if player.handList.count(pai) != 0:
                player.handList.remove(pai)
        # 检查听牌列表有没有变
        # 下一人
        self.nextPlayer()
        self.checkHandTing(player)
        msg = self.chooseList(seatIndex,"chi",self.playList[self.currentSeatIndex].chuPai)
        msg["canchupai"] = self.currentSeatIndex
        self.startTime = time.time()
        self.noteALL(seatIndex,msg)

    # 胡
    def hu(self,seatIndex,paiList):
        player = self.playList[seatIndex]
        player.huPai = paiList
        huTypeList = player.tingHuType[str(player.huPai)][0]
        # 判断门前清和自摸，并修改番数
        if "zimo" in huTypeList and player.chuMo == False:
            huTypeList[huTypeList.index("zimo")+1] = 1
        # 不是自摸，删除
        elif "zimo" in huTypeList and player.chuMo == True:
            del(huTypeList[huTypeList.index("zimo")+1])
            huTypeList.remove("zimo")   
        if "menqianqing" in huTypeList and player.chuMo == True:
            huTypeList[huTypeList.index("menqianqing")+1] = 2
        player.handList.append(player.huPai)
        self.noteALL(seatIndex,self.chooseList(seatIndex,"hu",player.huPai))
        # 计算各个玩家番数
        self.result(True)

    # 过
    def guo(self,seatIndex):
        # 玩家出牌（手上13张），有人过，顺次检查其他玩家是否可以胡
        # 其他玩家是否可以碰杠，下家可以碰杠同时检查下家是否可以吃，自己是否可以听牌，都过则下家摸牌出牌
        self.noteALL(seatIndex,self.chooseList(seatIndex,"guo",None))
        currentPlayer = self.playList[self.currentSeatIndex]
        nextIndex = (self.currentSeatIndex + 1) % 4
        self.playList[seatIndex].checkGuo()

        if currentPlayer.chuMo == True:
            # 顺次检查其他玩家是否可以胡
            for index in range(0,4):
                if(index == self.currentSeatIndex or index == seatIndex):
                    continue
                player = self.playList[index]
                if player.chooseGuo:
                    continue
                if self.checkCanHu(index,currentPlayer.chuPai):
                    self.note(index)
                    return
            # 顺次检查其他玩家是否可以碰明杠,下家可以碰杠同时检查下家是否可以吃
            for index in range(0,4):
                if(index == self.currentSeatIndex or index == seatIndex):
                    continue
                player = self.playList[index]  
                if player.chooseGuo:
                    continue              
                if self.checkCanPeng(index,currentPlayer.chuPai) or self.checkCanMingGang(index,currentPlayer.chuPai):
                    if(index == nextIndex):
                        self.checkCanChi(nextIndex,currentPlayer.chuPai)
                    self.note(index)
                    return
            # 检查下家是否可以吃 
            if self.playList[nextIndex].chooseGuo == False:
                if self.checkCanChi(nextIndex,currentPlayer.chuPai):
                    self.note(nextIndex)
                    return
            # 全部过，则下家摸牌出牌
            self.nextPlayer()
            self.moPai(self.currentSeatIndex)

        # 玩家摸牌，可胡自己过，自己出牌
        if currentPlayer.chuMo == False:
            if currentPlayer.chooseGuo:
                self.noteChupai(seatIndex)
                return
            # 玩家加杠时，其他玩家过胡，顺次检查其他玩家，最后玩家加杠，自己过，则出牌
            for index in range(0,4):
                if(index == self.currentSeatIndex or index == seatIndex):
                    continue
                player = self.playList[index]
                if player.chooseGuo:
                    continue  
                if self.checkCanHu(index,currentPlayer.moPai):
                    self.note(index)
                    return
            # 通知玩家加杠
            if currentPlayer.chooseJiaGangGuo is False:
                if self.checkCanJiaGang(self.currentSeatIndex,currentPlayer.moPai):
                    self.note(self.currentSeatIndex)
            else:
                self.noteChupai(self.currentSeatIndex)
    
    # 计算各个玩家番数,向数据库中写入玩家总分数
    def result(self,normal):
        # 无牌结束
        if normal == False:
            self.end(None)

        # 正常结束
        # 赢家基本分
        for index in range(0,4):
            winPlayer = self.playList[index]
            if winPlayer.huPai != -1:
                huTypeList = winPlayer.tingHuType[str(winPlayer.huPai)][0]
                i = 1
                while i< len(huTypeList):
                    winPlayer.fanShu += huTypeList[i]
                    i += 2
                if "zimo" in huTypeList:
                    winPlayer.score = (8 + winPlayer.fanShu) * 3 - winPlayer.penalty
                    for j in range(0,4):
                        if j != index:
                            lossPlayer = self.playList[j]
                            lossPlayer.score = -1 * (8 + winPlayer.fanShu) - lossPlayer.penalty
                else:
                    winPlayer.score = 8 * 3 + winPlayer.fanShu - winPlayer.penalty
                    for j in range(0,4):
                        if j != index:
                            lossPlayer = self.playList[j]
                            lossPlayer.score = -1 * 8 - lossPlayer.penalty
                            if self.currentSeatIndex == j:
                                lossPlayer.score -= winPlayer.fanShu
                # 写入数据库
                for seat in range(0,4):
                    tempPlayer = self.playList[seat]
                    self.db.updateRecord(tempPlayer.id,tempPlayer.score)            
                self.end(winPlayer)
    
    # 改变庄家，查询数据库本房间游戏局数，修改已进行的局数，并开始下一局游戏
    # 局数-1时，一直进行下去
    def end(self,player):
        if player != None:
            self.banker = player
        total,already = self.db.select_num(self.roomid)
        # 训练用，循环下去
        if int(total) == -1:
            self.db.update_num( self.roomid,int(already)+1)
            print("total",total,"already",already)
            self.noteALL(5,["next"])
            print("next")
        if int(total) - 1 > int(already):
            self.db.update_num( self.roomid,int(already)+1)
            print("total",total,"already",already)
            # 通知玩家重新开局（发送结果：胡牌类型，番数，分数）
            self.noteALL(5,["next"])
            print("next")
        else:
            self.noteALL(5,["over"])
            print("over")

    # 生成胡牌列表
    def finalPaiList(self,player):
        paiList = []
        split = player.tingHuType[str(player.huPai)][1]
        list2 = split[0]
        for pai in list2:
            paiList.append("双:"+self.numToType(pai))
        list3 = split[1]
        for pai in list3:
            paiList.append("刻:"+self.numToType(pai))
        list123 = split[2]
        for i in list123:
            _str = "顺:"
            for pai in i:
                _str += self.numToType(pai)
            paiList.append(_str)
        for i in player.chiPai:
            _str = "吃:"
            for pai in i:
                _str += self.numToType(pai)
            paiList.append(_str)
        for pai in player.pengPai:
            paiList.append("碰:"+self.numToType(pai))
        for pai in player.anGangPai:
            paiList.append("暗:"+self.numToType(pai))
        for pai in player.mingGangPai:
            paiList.append("明:"+self.numToType(pai))
        for pai in player.jiaGangPai:
            paiList.append("加:"+self.numToType(pai))
        return paiList
    
    # 数字映射成牌型
    def numToType(self,pai):
        list1 = ["一","二","三","四","五","六","七","八","九"]
        list2 = ["筒","条","万"]
        list3 = ["东风","南风","西风","北风","红中","发财","白板"]
        if pai < 27:
            return list1[pai%9] + list2[int(pai/9)] 
        else:
            return list3[pai-27]