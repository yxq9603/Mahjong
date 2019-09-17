#coding=utf8
# 对外提供数据库操作接口
# 当用户数量巨大时，如何根据积分实时显示排名 
# 当两个人同时创建房间时，如何保证房间号不一致

# 应当创建连接池，否则使用同一个连接进行大量读写时会非常耗时
# https://www.jianshu.com/p/57eaecb0c4a6
import pymysql
from DBUtils.PooledDB import PooledDB
import config
import hashlib
import uuid

class DBUtil():
    def __init__(self):
        self.hostname = config.db_host
        self.port = config.db_port
        self.dbname = config.db_dbname
        self.user = config.db_user
        self.passwd = config.db_passwd
        # setsession=['SET AUTOCOMMIT = 1']是用来设置线程池是否打开自动更新的配置
        # mincached=2, # 初始化时，链接池中至少创建的空闲的链接，0表示不创建
        # maxcached=5, # 链接池中最多闲置的链接，0和None不限制
        # maxconnections=6, # 连接池允许的最大连接数，0和None表示不限制连接数
        self.pool = PooledDB(pymysql,host=self.hostname,port=self.port,user=self.user,password=self.passwd,database=self.dbname,charset='utf8',mincached=4,maxcached=10,maxconnections=0,setsession=['SET AUTOCOMMIT=1'])
    
    # 连接数据库
    def connect_db(self):
        self.conn = self.pool.connection()
        self.cur = self.conn.cursor()

    # 关闭数据库
    def close_db(self):
        self.cur.close()
        self.conn.close()

    # 执行sql
    def execute(self,sql):
        self.connect_db()
        return self.cur.execute(sql)
    
    # 获取所有数据列表
    def select_list(self,table,fields):
        # 取出相关属性的所有记录
        sql = "SELECT %s FROM %s;"%(','.join(fields),table)
        print(sql)
        try:
            self.execute(sql)
            result = self.cur.fetchall()
            if result:
                # 每条记录里所有属性生成字典放入列表
                result = [dict((key,row[index]) for index,key in enumerate(fields)) for row in result]
            else:
                result = {}
            return result
        except:
            # util.WriteLog('db').info("Execute '%s' error: %s" % (sql, traceback.format_exc()))
            print("list查询失败")
        finally:
            self.close_db()
        
    # 获取某一条数据，返回字典(where is dict)
    def select_one(self,table,fields,where):
        if  isinstance(where,dict) and where:
            conditions = []
            for key,value in where.items():
                conditions.append("%s='%s'"%(key,value))
        sql = "SELECT %s FROM %s WHERE %s;"%(','.join(fields),table,'AND'.join(conditions))
        print(sql)
        try:
            self.execute(sql)
            result = self.cur.fetchone()
            if result:
                result = dict((key,result[index]) for index,key in enumerate(fields))
            else:
                result = {}
            return result
        except:
            print("one查询失败")
        finally:
            self.close_db()

    # 更新数据(fields and where is dict)
    def update(self,table,fields,where):
        data = ','.join(["%s='%s'"%(key,value) for key,value in fields.items()])
        if  isinstance(where,dict) and where:
            conditions = []
            for key,value in where.items():
                conditions.append("%s='%s'"%(key,value))
        sql = "UPDATE %s SET %s WHERE %s;"%(table,data,'AND'.join(conditions))
        print(sql)
        try:
            return self.execute(sql)
        except:
            print("更新失败")
        finally:
            self.close_db()

    # 添加数据(data is dict)
    def insert(self,table,data):
        fields,values = [],[]
        for key,value in data.items():
            fields.append(key)
            values.append("'%s'"%value)
        print(fields,values)
        sql = "INSERT INTO %s (%s) VALUES (%s);" % (table,','.join(fields),','.join(values))
        print(sql)
        try:
            return self.execute(sql)
            print("ok")
        except:
            print("添加失败")
        finally:
            self.close_db()

    # 删除数据
    def delete(self,table,where):
        if  isinstance(where,dict) and where:
            conditions = []
            for key,value in where.items():
                conditions.append("%s='%s'"%(key,value))
        sql = "DELETE FROM %s WHERE %s;" % (table,'AND'.join(conditions))
        print(sql)
        try:
            return self.execute(sql)
        except:
            print("删除失败")
        finally:
            self.close_db()

    # 注册，user查询账号
    def configAccount(self,account):
        result = self.select_one("USER",["ID"],{"ACCOUNT":account})
        # 账号不存在
        if result == {}:
            return False
        return True

    # 生成随机ID（如何保证唯一性？）
    def generateID(self):
        tempId = str(uuid.uuid1())
        return ''.join(tempId.split('-')) 

    # 注册，user写入账号,加密密码及生成ID，在record写入玩家ID
    def registered(self,account,passwd,name):
        hl = hashlib.md5()
        hl.update(passwd.encode("utf-8"))
        passwd = hl.hexdigest()
        id = self.generateID()
        data = {
            "ACCOUNT":account,
            "PASS"   :passwd,
            "NAME"   :name,
            "ID"     :id
        }
        print(data)
        self.insert("USER",data)
        self.insert("RECORD",{"ID":id,"SCORE":0})
    # 注册,user写入姓名
    def updateName(self,account,name):
        self.update("USER",{"NAME":name},{"ACCOUNT":account})
    
    # 登录，user查询账号密码
    def login(self,account,passwd):
        hl = hashlib.md5()
        hl.update(passwd.encode("utf-8"))
        passwd = hl.hexdigest()
        # 先看账号会否存在 ,根据账号存在和密码正确分别返回
        if self.configAccount(account):
            result = self.select_one("USER",["PASS"],{"ACCOUNT":account})
            if result != {} and passwd == result["PASS"]:
                return "login ok"
            else:
                return "pass error"
        return "account not exist"

    # 查询ID
    def selectID(self,account):
        return self.select_one("USER",["ID"],{"ACCOUNT":account})
    
    # 查询姓名
    def selectName(self,account):
        return self.select_one("USER",["NAME"],{"ACCOUNT":account})
    # 根据id查姓名
    def selectNameByID(self,id):
        return self.select_one("USER",["NAME"],{"ID":id})

    # 查询用户积分
    def select_score(self,id):
        return self.select_one("RECORD",["SCORE"],{"ID":id})

    # 查询房间号
    def select_roomID(self,roomid):
        result = self.select_one("ROOM",["*"],{"ROOMID":roomid})
        if result == {}:
            return False
        return True

    # 游戏,room写入房间号
    def insertRoomID(self,roomid,total):
        self.insert("ROOM",{"ROOMID":roomid,"TOTAL_NUM":total,"ALREADY_NUM":0})

    # 游戏,room写入玩家ID
    def roomUserID(self,roomid,num,id):
        self.update("ROOM",{"ID%d"%num:id},{"ROOMID":roomid})
    
    # 删除一条房间记录
    def delete_room(self,roomid):
        self.delete("ROOM",{"ROOMID":roomid})

    # 查询总局数和已经进行的局数
    def select_num(self,roomid):
        result = self.select_one("ROOM",["TOTAL_NUM","ALREADY_NUM"],{"ROOMID":roomid})
        if result != {}:
            return result["TOTAL_NUM"],result["ALREADY_NUM"]
    # 修改已经进行的局数
    def update_num(self,roomid,num):
        self.update("ROOM",{"ALREADY_NUM":num},{"ROOMID":roomid})
    
    # 游戏，record修改玩家积分(获取积分，加上本局积分，再写入)
    def updateRecord(self,id,score):
        result = self.select_one("RECORD",["SCORE"],{"ID":id})
        if result != {}:
            total = score + int(result["SCORE"])
            self.update("RECORD",{"SCORE":total},{"ID":id})