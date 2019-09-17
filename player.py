#coding=utf8
# 玩家类
# 存储玩家：手牌、
class Player():
    def __init__(self,seatIndex,id):
        # id
        self.id = id
        # 本局序号
        self.seatIndex = seatIndex
        self.init()

    
    # 新开局的初始化
    def init(self):
        # 手牌
        self.handList = []
        # 听的牌
        self.tingPai = []
        # 听牌和胡牌字典
        self.tingHuType = {}
        # 听牌(手牌)序列
        self.tingList = []
        # 当前正在出牌True或摸牌False
        self.chuMo = False
        
        # 当前局番数
        self.fanShu = 0
        # 当前局分数
        self.scoer = 0
        # 当前局罚分
        self.penalty = 0
        
        # 可以听
        self.canTing = False
        # 可以胡
        self.canHu = False
        # 可以碰
        self.canPeng = False
        # 可以吃
        self.canChi = False
        # 可以暗杠
        self.canAnGang = False
        # 可以明杠
        self.canMingGang = False
        # 可以加杠
        self.canJiaGang = False
        
        # 可以碰的牌
        self.canPengPai = None
        # 可以吃的牌
        self.canChiPai = []
        # 可以暗杠的牌
        self.canAnGangPai = []
        # 可以明杠的牌
        self.canMingGangPai = None
        # 可以加杠的牌
        self.canJiaGangPai = None
        # 可以胡的牌
        self.canHuPai = None

        # 碰的牌
        self.pengPai = []
        # 吃的牌
        self.chiPai = []
        # 暗杠的牌
        self.anGangPai = []
        # 明杠的牌
        self.mingGangPai = []
        # 加杠的牌
        self.jiaGangPai = []

        # 胡的牌
        self.huPai = -1

        # 选择了过
        self.chooseGuo = False
        self.chooseJiaGangGuo = False

        # 出的牌
        self.chuPai = None
        # 摸的牌
        self.moPai = None

        # 组成不同顺子，拆分后的牌的整理列表
        self.splitList = []

    # 清除可以吃碰杠以及对应的牌
    def clearCan(self):
        # 可以胡
        self.canHu = False
        # 可以碰
        self.canPeng = False
        # 可以吃
        self.canChi = False
        # 可以暗杠
        self.canAnGang = False
        # 可以明杠
        self.canMingGang = False
        # 可以加杠
        self.canJiaGang = False

        # 可以碰的牌
        self.canPengPai = None
        # 可以吃的牌
        self.canChiPai = []
        # 可以暗杠的牌
        self.canAnGangPai = []
        # 可以明杠的牌
        self.canMingGangPai = None
        # 可以加杠的牌
        self.canJiaGangPai = None

        # 出的牌
        self.chuPai = None
        # 摸的牌
        self.moPai = None

        self.chooseJiaGangGuo = False
        self.chooseGuo = False
    
    # 检查针对什么选项选了过
    def checkGuo(self):
        if self.canJiaGang:
            self.chooseJiaGangGuo = True
        if self.canChi or self.canPeng or self.canAnGang or self.canMingGang or self.canJiaGang or self.canHu:
           self.chooseGuo = True

    def resetTingHuType(self):
        self.tingHuType.clear()
        self.tingPai = []
        self.tingList = []
