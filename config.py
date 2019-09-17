db_host = "localhost"
db_port = 3306
db_user = "root"
db_passwd = "ts156321"
db_dbname = "MJ"

TEST_ADDRESS = ('127.0.0.1',9009)

LOGIN_ADDRESS = ('127.0.0.1',9000)
HALL_ADDRESS = ('127.0.0.1',9001)
GAME_ADDRESS = ('127.0.0.1',9002)

# 连接池
LOGIN_CONN_POOL = {}
HALL_CONN_POOL = {}
# {roomid:{id:sockets}}
GAME_CONN_POOL = {}

# 房间池
# {房间号：[id0-id3,game]}
ROOMID = {}
