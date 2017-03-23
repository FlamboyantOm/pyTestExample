#-------------------------------------------------------------------------------
# Name:        get_releaseable_pkg
# Purpose:     It will return the list of packages available for
#              release with full URL path and path name.
#
# Dependency:  This script is dependent on mysql.connector python library
#              and setting.py
#
# Author:      sushant.arya
#
# Created:     14/09/2016
#-------------------------------------------------------------------------------

import sys
import time,datetime
import sys
sys.path.append(sys.path[0].replace('script','build_manage'))
import settings
import pymysql as mdb

def print_dstring(stringToPrint):
        if settings.DEBUG_PRINT == 0:
            return
        print('['+ str(datetime.datetime.now())+'] ',stringToPrint)

class MyDB(object):
    _db_connection = None
    _db_cur = None
    def __init__(self):
        self._db_connection = mdb.connect('10.10.10.236',settings.OCD_USER,settings.OCD_PASS,settings.OCD_DB)
        self._db_cur = self._db_connection.cursor()
    def query(self, query,type = 0):
        try:
            results = self._db_cur.execute(query)
            print_dstring('Query : '+str(query)+' | Results : '+str(results))
            if type == 0:
                result = self._db_cur.fetchall()
            elif type == 1:
                result = self._db_cur.fetchone()
            else:
                result = self._db_cur.fetchmany(type)
            self._db_connection.autocommit(1)
            self._db_connection.close()
            return result
        except Exception as e:
            self._db_connection.autocommit(1)
            self._db_connection.close()
            print("DB Error (query) : ",e," Sql : ",query)
    def queryWithReturn(self, query,type = 0):
        try:
            results = self._db_cur.execute(query)
            print_dstring('Query : '+str(query)+' | Results : '+str(results))
            if type == 0:
                result = self._db_cur.fetchall()
            elif type == 1:
                result = self._db_cur.fetchone()
            else :
                result = self._db_cur.fetchmany(type)
            self._db_connection.autocommit(1)
            self._db_connection.close()
            return {'result': result,'rows':results}
        except Exception as e:
            print("DB Error (queryWithReturn) : ",e," Sql : ", query, " ")

    def insert(self, query,type= 0):
        if type == 0:
            try :
                result =  self._db_cur.execute(query)
                self._db_connection.autocommit(1)
                lastrowid = self._db_cur.lastrowid
                print_dstring('__________insert____________')
                print_dstring('Query : '+str(query)+' | Results : '+str(result)+' | Return : '+str(lastrowid))
                self._db_connection.close()
                return lastrowid
            except Exception as e:
                print("DB Error (insert): ",e)
                print("Sql (Insert) : ", query)
                self._db_connection.close()
                return 0
        elif type == 1:
            try :
                result = []
                print_dstring('__________insert(T)____________')
                for sql in query:
                    insertID =  self._db_cur.execute(sql)

                    lastrowid = self._db_cur.lastrowid
                    print_dstring('Query : '+str(sql)+' | Return : '+str(lastrowid))
                    result.append(lastrowid)
                self._db_connection.autocommit(1)
                self._db_connection.close()
                return result
            except Exception as e:
                self._db_connection.rollback(1)
                self._db_connection.close()
                print("DB Error (insert): ",e);
                print("Sql (Insert Tran) : ", query)
                return 0


def main():
    sys.exit(0)

import inspect
def db_query(sql,rows = 0):
    try :
        dbobj = MyDB()
        if rows == 0:
            return dbobj.query(sql)
        else :
            return dbobj.query(sql,rows)
    except Exception as e:
        print('Error in db_query : Inspect Function : ',inspect.stack()[1][3])
        print('Error in db_query : Sql ',sql,' Error ',e)
    except Warning as e:
        print('Error in db_query : Sql(Warning) ', sql, ' Error ', e)

def db_insert(sql,type=0):
    try :
         dbobj = MyDB()
         return dbobj.insert(sql,type)
    except Exception as e:
        print('Error (db_insert) Sql ',sql,' Error ',e)

def main():
    #sql = "INSERT INTO `OneClickUpdate`.`progresslog` (`JobID`, `Msg`, `LogTime`, `UpdateID`) VALUES (240, 'test', '2016-10-15 13:24:59', 4);"
    import datetime
    mydate = datetime.datetime.now().strftime("%y-%M-%d %H:%I:%S")
    mylist = []
    for i in range(8):
        print(i)
        if i == 3:
            sql = "UPDATE `OneClickUpdate`.`progresslog` SET `Msg`='dh' WHERE  `ProgressId`=3;"
        elif i == 5:
            sql = "UPDATE `OneClickUpdate`.`progresslog` SET `Msg`='fd' WHERE  `ProgressId`=56666;"
        else:
            sql = "INSERT INTO `OneClickUpdate`.`progresslog` (`JobID`, `Msg`, `LogTime`, `UpdateID`) VALUES (240, '"+str(i)+"-"+str(mydate)+"', '2016-10-15 13:24:59', 4);"
        mylist.append(sql)
    print(mylist)
    print(db_insert(mylist,1))
if __name__ == '__main__':
    main()
