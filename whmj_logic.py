#coding=utf8
# 武汉麻将的主要逻辑部分
# 包括函数：洗牌、确定赖子、发牌、出牌、摸牌、听牌，出牌推荐，是否可以吃碰杠胡，吃碰杠胡听过选择，吃碰杠胡，计算结果
# 红中不能碰、明杠、暗杠，手上持有红中时不能胡牌
# 赖子不能碰,只可暗杠，只有在听牌时可当任意牌，小胡只能有一张，大胡可有任意张
# 东南西北中发白赖子不能吃
# 吃碰不补牌，杠要补一张

import random
from player import Player
from room import Room

class WHMJ():
    def __init__(self):
        # 总牌数
        self.countOfPai = 0
        # 存放所有牌
        self.majiang = []
        # 弃牌
        self.fold = []
        # 当前发牌序号
        self.currentPaiIndex = 0
        # 初始化玩家
        self.playList = [Player(0),Player(1),Player(2),Player(3)]
        # 初始化本局房间信息
        self.roomInfo = Room()
        # 确定0号位为庄家
        self.roomInfo.banker = self.playList[0]
        self.roomInfo.currentSeatIndex = self.roomInfo.banker.seatIndex
        # 决策选择
        self.actionSwitch = {
            "peng":    self.peng,
            "angang":  self.anGang,
            "minggang":self.mingGang,
            "jiagang": self.jiaGang,
            "hu":      self.hu,
            "guo":     self.guo
        }
    
    # 下一摸牌玩家
    def nextPlayer(self):
        self.roomInfo.currentSeatIndex = (self.roomInfo.currentSeatIndex + 1) % 4

    # 初始化牌
    def initPai(self):
        self.countOfPai = 0
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

    # 洗牌
    def shuffle(self):
        for index in range(self.countOfPai):
            randomIndex = random.randint(0,self.countOfPai-1)
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
        self.roomInfo.banker.handList.append(self.majiang[52])
        # 当前发牌序号
        self.currentPaiIndex = 53

    # 确定本局赖子
    def setLaiZi(self):
        tempPai = self.majiang[self.currentPaiIndex]
        # 筒条万东南西
        if(tempPai < 30):
            self.roomInfo.laizi = (tempPai + 1) % 9 + 9 * int(tempPai / 9)
        # 北中
        elif(tempPai == 30 or tempPai == 31):
            self.roomInfo.laizi = 32
        # 发
        elif(tempPai == 32):
            self.roomInfo.laizi = 33
        # 白
        elif(tempPai == 33):
            self.roomInfo.laizi = 27
        self.fold.append(tempPai)
        self.currentPaiIndex += 1

    # 出牌
    def chuPai(self,pai,seatIndex):
        # 确定当前轮玩家，出牌，改变手牌，其他玩家检查是否可以胡杠碰吃,弃牌
        if(self.roomInfo.currentSeatIndex is not seatIndex):
            return
        # 所有玩家清除可以吃碰杠以及对应的牌
        for index in range(0,4):
            self.playList[index].clearCan()

        player = self.playList[seatIndex]
        # 改变手牌
        player.handList.remove(pai)
        player.chuPai = pai
        # 检查自己是否可以听牌
        if(player.handList != player.tingList):
            player.canTing = False
            self.checkCanTing(seatIndex)
        # 检查是否可以胡
        for index in range(0,4):
            if(index == seatIndex):
                continue
            if self.checkCanHu(index,pai):
                self.note(index)
                return
        # 检查是否可以碰明杠,当下家可以碰杠时同时下家检查是否可以吃
        for index in range(0,4):
            if(index == seatIndex):
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
        # 下一位
        self.nextPlayer()
    
    # 摸牌
    def moPai(self,seatIndex):
        # 确定当前轮玩家，还有牌，摸牌，判断是否可以胡暗杠加杠
        if(self.roomInfo.currentSeatIndex is not seatIndex or self.currentPaiIndex == self.countOfPai - 1):
            return
        # 所有玩家清除可以吃碰杠以及对应的牌
        for index in range(0,4):
            self.playList[index].clearCan()
        
        # 添加手牌
        pai = self.majiang[self.currentPaiIndex]
        self.playList[seatIndex].handList.append(pai)
        self.playList[seatIndex].moPai = pai
        self.currentPaiIndex += 1
        # 判断是否可以胡暗杠
        if self.checkCanHu(seatIndex,pai) or self.checkCanAnGang(seatIndex,pai):
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
        # 通知可以出牌
        self.noteChuPai(seatIndex)

    # 吃碰杠听胡过通知
    def note(self,seatIndex):
        pass

    # 通知可以出牌
    def noteChuPai(self,seatIndex):
        pass
    
    # 吃碰杠听胡过选择
    def choose(self,seatIndex,action,paiList):
        if(action == "chi"):
            self.chi(seatIndex,paiList)
        else:
            self.actionSwitch.get(action)()   
    
    # 是否可以听牌
    def checkCanTing(self,seatIndex):
        # 不提醒玩家选择，保存听的牌，作为玩家胡的判别标准，有UI时提醒用户正在听牌和出那张牌
        pass

    # 是否可以胡
    def checkCanHu(self,seatIndex,pai):
        player = self.playList[seatIndex]
        if player.canTing:
            if pai in player.tingPai:
                player.canHu = True
                return True
            else:
                return False

    # 是否可以明杠
    def checkCanMingGang(self,seatIndex,pai):
        if pai == 31 or pai == self.roomInfo.laizi:
            return False
        # 手里有三张一样的
        player = self.playList[seatIndex]
        if player.handList.count(pai) == 3:
            player.canMingGang = True
            player.canMingGangPai = pai
            return True
        else:
            return False
    
    # 是否可以暗杠
    def checkCanAnGang(self,seatIndex,pai):
        if pai == 31:
            return False
        # 手里有三张一样的
        player = self.playList[seatIndex]
        if player.handList.count(pai) == 3:
            player.canAnGang = True
            player.canAnGangPai = pai
            return True
        else:
            return False
    
    # 是否可以加杠
    def checkCanJiaGang(self,seatIndex,pai):
        if pai == 31 or pai == self.roomInfo.laizi:
            return False
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
        if pai == 31 or pai == self.roomInfo.laizi:
            return False
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
        if (pai >= 27 and pai <= 33) or pai == self.roomInfo.laizi:
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
        if pai%9 > 1 and pai%9 < 7:
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
        if player.handList.count(pai) > 0:
            player.handList.remove(pai)
        # 摸牌出牌
        self.currentSeatIndex = seatIndex
        self.moPai(seatIndex)
        
    # 暗杠
    def anGang(self,seatIndex):
        # 暗杠列表里添加，删除手牌，补一张牌
        player = self.playList[seatIndex]
        pai = player.canAnGangPai
        player.AnGangPai.append(pai)
        if player.handList.count(pai) > 0:
            player.handList.remove(pai)
        # 摸牌出牌
        self.currentSeatIndex = seatIndex
        self.moPai(seatIndex)

    # 加杠
    def jiaGang(self,seatIndex):
        # 暗杠列表里添加，删除对应碰牌，补一张牌
        player = self.playList[seatIndex]
        pai = player.canJiaGangPai
        player.pengPai.remove(pai)
        player.jiaGangPai.append(pai)
        # 摸牌出牌
        self.currentSeatIndex = seatIndex
        self.moPai(seatIndex)

    # 碰
    def peng(self,seatIndex):
        # 碰列表里添加，删除手牌，轮换到下一人
        player = self.playList[seatIndex]
        pai = player.canPengPai
        player.pengPai.append(pai)
        if player.handList.count(pai) > 0:
            player.handList.remove(pai)
        # 下一人
        self.nextPlayer()
        self.moPai(self.roomInfo.currentSeatIndex)

    # 吃
    def chi(self,seatIndex,paiList):
        # 吃列表里添加子列表，删除手牌，轮换到下一人
        player = self.playList[seatIndex]
        player.chiPai.append(paiList)
        for pai in paiList:
            if player.handList.count(pai) != 0:
                player.handList.remove(pai)
        # 下一人
        self.nextPlayer()
        self.moPai(self.roomInfo.currentSeatIndex)

    # 胡
    def hu(self,seatIndex):
        # 积分结算，通知胡牌类型
        pass

    # 过
    def guo(self,seatIndex):
        # 玩家出牌（手上13张），有人过，顺次检查其他玩家是否可以胡
        # 其他玩家是否可以碰杠，下家可以碰杠同时检查下家是否可以吃，自己是否可以听牌，都过则下家摸牌出牌
        currentPlayer = self.playList[self.roomInfo.currentSeatIndex]
        nextIndex = (self.roomInfo.currentSeatIndex + 1) % 4
        self.playList[seatIndex].checkGuo()

        if len(currentPlayer.handList) == 13:
            # 顺次检查其他玩家是否可以胡
            for index in range(0,4):
                if(index == self.roomInfo.currentSeatIndex or index == seatIndex):
                    continue
                player = self.playList[index]
                if self.checkCanHu(index,currentPlayer.chuPai):
                    if player.chooseHuGuo is False:
                        self.note(index)
                        return
            # 顺次检查其他玩家是否可以碰明杠,下家可以碰杠同时检查下家是否可以吃
            for index in range(0,4):
                if(index == self.roomInfo.currentSeatIndex or index == seatIndex):
                    continue
                player = self.playList[index]                
                if self.checkCanPeng(index,currentPlayer.chuPai) or self.checkCanMingGang(index,currentPlayer.chuPai):
                    if player.chooseMingGangGuo is False or player.choosePengGuo is False:
                        if(index == nextIndex):
                            self.checkCanChi(nextIndex,currentPlayer.chuPai)
                        self.note(index)
                        return
            # 检查下家是否可以吃 
            if self.checkCanChi(nextIndex,currentPlayer.chuPai):
                if self.playList[nextIndex].chooseChiGuo is False:
                    self.note(nextIndex)
                    return
            # 全部过，则下家摸牌出牌
            self.nextPlayer()
            self.moPai(self.roomInfo.currentSeatIndex)

        # 玩家摸牌（手上14张），可胡自己过，自己出牌
        if len(currentPlayer.handList) == 14:
            if currentPlayer.chooseHuGuo:
                self.noteChuPai(seatIndex)
                return
            # 玩家加杠时，其他玩家过胡，顺次检查其他玩家，最后玩家加杠，自己过，则出牌
            for index in range(0,4):
                if(index == self.roomInfo.currentSeatIndex or index == seatIndex):
                    continue
                player = self.playList[index]
                if self.checkCanHu(index,currentPlayer.moPai):
                    if player.chooseHuGuo is False:
                        self.note(index)
                        return
            # 通知玩家加杠
            if currentPlayer.chooseJiaGangGuo is False:
                if self.checkCanJiaGang(self.roomInfo.currentSeatIndex,currentPlayer.moPai):
                    self.note(self.roomInfo.currentSeatIndex)
            else:
                self.noteChuPai(self.roomInfo.currentSeatIndex)
                        