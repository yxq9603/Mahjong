LOGIN_ADDRESS = ('127.0.0.1',9000)
HALL_ADDRESS = None
GAME_ADDRESS = None

ACCOUNT = None
NAME = None
SCORE = None
ROOMID= None

class Player():
    def __init__(self,seat,name):
        self.name = name
        self.seat = seat
        self.handList = []
        self.choose = []
        self.chooseList = {}
        self.chuPai = -1
        self.moPai = -1
        self.mySelf = False
        self.flod = []

    def clear(self):
        self.handList = []
        self.choose = []
        self.chooseList = {}
        self.chuPai = -1
        self.moPai = -1
        self.flod = []