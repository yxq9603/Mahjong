#coding=utf8
# 连接数据库,数据库生成语句
# 创建三张表
# 表一：user记录玩家注册的账号密码姓名，以及系统分配的唯一ID，主键账号，外键ID
# 表二：record记录玩家ID，积分，ID为主键
# 表三：room记录房间号，房间内玩家ID，房间号为主键，玩家ID为外键

import pymysql
# 打开数据库连接，
db = pymysql.connect("localhost","root","ts156321","MJ")
# 使用 cursor() 方法创建一个游标对象 cursor
cursor = db.cursor()
# 创建表1 user
sql = """CREATE TABLE IF NOT EXISTS USER(
        ACCOUNT VARCHAR(20) NOT NULL PRIMARY KEY COMMENT '用户自建账户',
        PASS VARCHAR(200) NOT NULL COMMENT '用户密码',
        NAME VARCHAR(20) COMMENT '用户姓名',
        ID VARCHAR(200) COMMENT '系统分配ID') 
        """
cursor.execute(sql)

# 创建表2 record
sql = """CREATE TABLE IF NOT EXISTS RECORD(
        ID VARCHAR(200) NOT NULL PRIMARY KEY COMMENT '系统分配ID',
        SCORE VARCHAR(20) DEFAULT '0' NOT NULL COMMENT '玩家总积分') 
        """
cursor.execute(sql)

# 创建表3 room
sql = """CREATE TABLE IF NOT EXISTS ROOM(
        ROOMID INT(20) NOT NULL PRIMARY KEY COMMENT '创建的房间ID',
        TOTAL_NUM INT(20) COMMENT '房间总局数',
        ALREADY_NUM INT(20) COMMENT '已经进行的局数',
        ID0 VARCHAR(200) COMMENT '玩家ID',
        ID1 VARCHAR(200) COMMENT '玩家ID',
        ID2 VARCHAR(200) COMMENT '玩家ID',
        ID3 VARCHAR(200) COMMENT '玩家ID')
        """
cursor.execute(sql)

db.close()