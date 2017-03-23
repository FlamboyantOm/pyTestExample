from django.conf import settings
import datetime
from build_manage import const
WEBSITE_TITLE = 'OneClickUpdate'
from collections import OrderedDict
jenkins_url = settings.JENKINS_URL
jenkins_username = settings.JENKINS_USER
jenkins_password = settings.JENKINS_PASS
EngineType = {1:'QH',2:'E2'}
EngineTypeArr =  {'e2':2,'qh':1}

LimitToVerifyUpdateIDByType = {1 : const.QH_RELEASE_DIFF_LIMIT,2:const.E2_RELEASE_DIFF_LIMIT}
IsBuildEningine = {0:'No',1:'Yes'}
JobInfoFlag = {1:'Normal Job',2:'Manual Job',3:'Reverted Job'}
jobSteps = {1:{1:'Start',2: 'Download', 3: 'Test Update Creation', 4: 'Mark Verify', 5: 'Release Update Creation', 6: 'Mark Release'}, 3: {1:'Start',2: 'Copying Files For Revert', 5: 'Revert Release Update', 6: 'Mark Release'}}
jobStepsNextJob = {1: {1:2,2:3,3:4,4:5},3: {2:5,}}
jobStepsMannual = {1: {1,4},3: {1}}
JenkinsJobTimeOutMin = 20
typeWiseState = {1:{1:1,2:3},2:{1:1,2:3}}
JobFailedReason = {1:'No update available',2:'Test Failed',3:'Failed',6:'Completed'}
FailedReason = {1:'No update available',2:'Test Failed',3:'Other'}
UpdateType = {4:'32-bit ( UpdateID : 4 )',5:'64-bit ( UpdateID : 5 )',778:'Signatures',779:'WINDOWS32',780:'WINDOWS64',781:'Native Engine - WINDOWS32',782:'Native Engine - WINDOWS64',783:'Engine - LINUX',784:'Engine - LINUX_64',785:'Engine - MACAV',786:'2014 LINUX_32',787:'2014 LINUX_64'}
UpdateTypeOnly = {4:'32-bit',5:'64-bit',778:'Signatures',779:'WINDOWS32',780:'WINDOWS64',781:'Native Engine - WINDOWS32',782:'Native Engine - WINDOWS64',783:'Engine - LINUX',784:'Engine - LINUX_64',785:'Engine - MACAV',786:'2014 LINUX_32',787:'2014 LINUX_64',788:'INX'}
E2_PREM = {'can_create_build':{'order':1,'title':'Create E2 Job','url':'e2'},'can_create_revertbuild':{'order':2,'title':'Revert Job','url':'/revert/e2'},'can_view_buildhistory':{'order':3,'title':'View History','url':'/history/e2'},'can_view_statstics':{'order':4,'title':'Statstics','url':'/statstics/e2'}}
QH_PREM = {'can_create_build':{'order':1,'title':'Create QH Job','url':'qh'},'can_create_revertbuild':{'order':2,'title':'Revert Job','url':'/revert/qh'},'can_view_buildhistory':{'order':3,'title':'View History','url':'/history/qh'},'can_view_statstics':{'order':4,'title':'Statstics','url':'/statstics/qh'}}
permissions = {'QH':QH_PREM,'E2':E2_PREM}
jenkins_job =  {2:{1:{2:'download',3: 'create_e2_update_test',5: 'create_e2_update_release'}, 3:{2: 'revert_e2_update', 5: 'revert_e2_update'}}, 1:{1:{2:'download_qh',3: 'create_qh_update_test',5: 'create_qh_update_release'}, 3:{2: 'revert_qh_update', 5: 'revert_qh_update'}}}
jenkins_jobDist =  {2:{1:{2:'download',3: 'create_e2_update_test',5: 'create_e2_update_release'}, 3:{2: 'revert_e2_update'}}, 1:{1:{2:'download_qh',3: 'create_qh_update_test',5: 'create_qh_update_release'}, 3:{2: 'revert_qh_update'}}}
chartType = OrderedDict({'e2':OrderedDict({'E2 Build Size':{'link':'size'},'E2 Build Time':{'link':'time'},'New Vs Revert':{'link':'newVsRevert'},'Newly Added Files':{'link':'newAddedFiles'},'Total Jobs':{'link':'totalJobs'},'Active Users':{'link':'activeUsers'},})})
TemplateValues = {'running_job_ajax_time':10000,'pipeline_ajax_time':2000,'previous_builds_ajax_time':20000,'verifyJob_ajax_time':20000}
QH_UpdateID = [778,779,780,781,782,783,784,785,786,787]
UpdateID = {1:{778,779,780,781,782,783,784,785,786,787},2:{4,5}}

TypeProperty = {1:{'configFile':'configFile.ini'},}

import pymysql as mdb
def print_dstring(stringToPrint):
        if settings.DEBUG_PRINT == 0:
            return
        print('['+ str(datetime.datetime.now())+'] ',stringToPrint)
class MyDB(object):
    _db_connection = None
    _db_cur = None
    def __init__(self):
        self._db_connection = mdb.connect(settings.OCD_URL,settings.OCD_USER,settings.OCD_PASS,settings.OCD_DB)
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
                    #lastrowid = self._db_cur.lastrowid
                    print_dstring('Query : '+str(sql)+' | Return : '+str(insertID))
                    result.append(insertID)
                self._db_connection.autocommit(1)
                self._db_connection.close()
                print('Result :',result)
                return result
            except Exception as e:
                self._db_connection.rollback(1)
                self._db_connection.close()
                print("DB Error (insert): ",e);
                print("Sql (Insert Tran) : ", query)
                return 0

