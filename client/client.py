#coding=utf8
# 运行-终端绘制

# 通过socket发送数据data(list)需要是bytes类型，json.dumps(data)之后
# 是字符串，所以需要json.dumps(data).encode(utf-8)转码

# 接收到的也是bytes类型,通过json.loads(data)得到data最原始类型(list)
# 通过data.decode("utf-8")得到字符串类型，再次json.loads(data.decode("utf-8"))仍得到最原始类型(list)

# recv会接收最大内容，如果连续发送两条或多条信息，recv时，会全部接收或者截取最大接收作为接收的bytes
# 解决方法：
# 1，重新定义消息格式，力求每次只发一条，不存在连续发送
# 2，使用正则表达式将接收到的消息切分
import socket
import clientConfig
import json
from clientLogin import ClientLogin
from clientHall import ClientHall
from clientGame import ClientGame

class Client():
    def __init__(self):
        self.id = None
        self.roomId = None
        
    def start(self):
        while True:
            if clientConfig.GAME_ADDRESS != None:
                game = ClientGame()
                game.start()
            elif clientConfig.HALL_ADDRESS != None:
                hall = ClientHall()
                clientConfig.GAME_ADDRESS = hall.start() 
            else:
                login = ClientLogin()
                clientConfig.HALL_ADDRESS = login.start()
                
            
if __name__ == "__main__":
    client = Client()
    client.start()
    