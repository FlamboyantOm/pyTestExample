from django.shortcuts import *
from build.flib import database_connection_check,jenkins_check
from django.conf import settings
import requests,json
from . import flib,config,statistics
import datetime
import csv
import inspect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from script.verify_release import verify_release
from django.views.decorators.csrf import csrf_exempt

totalJobs = ['download','create_e2_update_test','create_e2_update_release']
totalJobs = set(totalJobs)
from collections import OrderedDict
@login_required(login_url='/login/')
@database_connection_check
def create_job(request,type,step,reqType=0):
    if reqType == 0 and not request.is_ajax():
        return
    if type == 'e2':
        paramArr = {}
        if str(step) == str(1):
            try:
                currentBuild = getJobStatus(type,1)
                if currentBuild['status'] == 0:
                    data ={'status': 0, 'msg': "Unable to process your request as "+currentBuild['response']}
                    return HttpResponse(json.dumps(data), content_type='application/json')
                sql = "SELECT * FROM %s where EngineType = 2 and Flag = 1  order by JobId desc  limit 0,1 " % ("jobinfo", )
                data_row = flib.db_query(sql,1)
                if data_row is not None:
                    jobId = data_row[0]
                    if data_row[1] not in {6,7}:
                        data = {'status': 0, 'msg': 'Previous job not completed.'}
                        return HttpResponse(json.dumps(data), content_type='application/json')
                userName = request.user.get_username()
                if userName == '':
                    data = {'status': 0, 'msg': 'User name issue'}
                    return HttpResponse(json.dumps(data), content_type='application/json')
                sql = "INSERT INTO jobinfo (`JobState`,`EngineType`,`Flag`,`UserName`) VALUES ('1','2','1','"+userName+"');"
                insertId =  flib.db_insert(sql)
                sql = "INSERT INTO jobstatedetails (`JobID`, `JobState`,`PercentDone` ) VALUES ('"+str(insertId)+"', '1','100');"
                flib.db_insert(sql)
                paramArr.update({'Job_ID': str(insertId)})
                jenkinsJobProcess(request,'download',paramArr)
                data = {'status':1,'msg':'Job created successfully with Job Id  #'+str(insertId)}  # create json array to response json
                return HttpResponse(json.dumps(data), content_type='application/json')
            except Exception as e:
                print('Error (create_job at ' + str(step) + ' of Type = ' + str(type) + ')', e)
                data = {'status':0,'rmsg':'Issue in processing your request'}  # create json array to response json
                return HttpResponse(json.dumps(data), content_type='application/json')
        elif str(step) == str(2):
            try:
                sql = "SELECT * FROM %s where EngineType = 2 and Flag = 1  order by JobId desc  limit 0,1 " % ("jobinfo", )
                data_row = flib.db_query(sql,1)
                jobId = data_row[0]
                if data_row[1] != 3:
                    data =  {'status': 0, 'msg': '#2 Not able to process your request, Please try after some time'}
                    return HttpResponse(json.dumps(data), content_type='application/json')
                sqlList = ["UPDATE jobinfo  SET `JobState`='4' WHERE  JobId = '"+str(jobId)+"'  ;"]
                sqlList.append("INSERT INTO jobstatedetails (`JobID`, `JobState`,`PercentDone`) VALUES ('"+str(jobId)+"', '4', '100');")
                flib.db_insert(sqlList,1)
                paramArr.update({'Job_ID': str(jobId)})
                jenkinsJobProcess(request,'create_e2_update_release',paramArr)
                data = {'status':1,'msg':'Job #'+str(jobId)+' Mark Verified successfully and initiaing Release Update Creation !'}  # create json array to response json
                return HttpResponse(json.dumps(data), content_type='application/json')
            except Exception as e:
                print('Error (create_job at ' + str(step) + ' of Type = ' + str(type) + ')', e)
                data = {'status':1,'msg':'Job created successfully !'+str(e)}  # create json array to response json
                return HttpResponse(json.dumps(data), content_type='application/json')
        elif str(step) == str(3):
            try:
                sql = "SELECT * FROM %s where EngineType = 2 and Flag = 1 order by JobId desc  limit 0,1 " % ("jobinfo", )
                data_row = flib.db_query(sql,1)
                jobId = data_row[0]
                if data_row[1] != 5 :
                    data =  {'status': 0, 'msg': '#3 Not able to process your request, Please try after some time'}
                    return HttpResponse(json.dumps(data), content_type='application/json')
                apiResult = verify_release.get_release_status(jobId,2)
                #print('____________',apiResult,jobId)
                if str(apiResult['error_code']) == str(0) and str(apiResult['status']) == str(1):
                    data =  {'status': 2, 'msg': 'Verification Failed.'}
                    return HttpResponse(json.dumps(data), content_type='application/json')
                elif str(apiResult['error_code']) == str(0) and str(apiResult['status']) == str(0):
                    pass
                else:
                    data =  {'status': 2, 'msg': 'Error in verification script'}
                    return HttpResponse(json.dumps(data), content_type='application/json')
                vdb = apiResult['vdb']

                paramArr.update({'Job_ID': str(jobId)})
                if request.method == 'POST':
                    userName = request.user.get_username()
                    try:
                        if 'Note' in request.POST and request.POST['Note'] != '':
                            note = request.POST['Note']
                        else:
                            note = reqType['Note']
                    except Exception as e:
                        print('No note found ', e)
                        note = ''
                    sqlList = ["UPDATE jobinfo  SET `JobState`='6' WHERE  JobId = '"+str(jobId)+"'  ;"]
                    sqlList.append("INSERT INTO jobstatedetails (`JobID`, `JobState`,`PercentDone`) VALUES ('"+str(jobId)+"', '6', '100');")
                    sqlList.append("INSERT INTO releaseinfo (`JobID`, `Notes`, `VDB`, `UserName`) VALUES ('"+str(jobId)+"','"+note+"','"+str(vdb)+"', '"+str(userName)+"');")
                    sqlList.append("UPDATE qhpackagedetails  SET `PackageState`='6' WHERE  JobID = '" + str(jobId) + "' ;")
                    flib.db_insert(sqlList,1)
                    try:
                        jenkinsJobProcess(request, 'backup_e2', {"Job_ID": str(jobId), "Update_Type": "e2"})
                    except Exception as e:
                        print('Error (backup_e2 jenkins job) ', e)

                data = {'status':1,'msg':'Job #'+str(jobId)+' mark released successfully !'}  # create json array to response json
                return HttpResponse(json.dumps(data), content_type='application/json')
            except Exception as e:
                print('Error (create_job at ' + str(step) + ' of Type = ' + str(type) + ')', e)
                data = {'status':0,'msg':'Issue in processing your request'}  # create json array to response json
                return HttpResponse(json.dumps(data), content_type='application/json')
        elif str(step) == str(4):
            try:
                revertJobId = request.POST['JobId']
                sql = "SELECT * FROM %s where EngineType = 2 and Flag = 1  order by JobId desc  limit 0,1 " % ("jobinfo",)
                data_row = flib.db_query(sql, 1)
                jobId = data_row[0]
                newJobId = int(jobId)
                if data_row[1] not in {5,6, 7,1,2}:
                    data = {'status': 0, 'msg': 'Previous job not completed.'}
                    return HttpResponse(json.dumps(data), content_type='application/json')
                userName = request.user.get_username()
                sql = "INSERT INTO jobinfo (`JobState`,`EngineType`,`Flag`,`UserName`) VALUES ('1','2','3','" + userName + "');"
                insertId = flib.db_insert(sql)
                sqlList = ["INSERT INTO jobstatedetails (`JobID`, `JobState`,`PercentDone` ) VALUES ('" + str(insertId) + "', '1','100');"]
                sqlList.append("INSERT INTO jobproperty (`JobID`, `Name`,`Value`) VALUES ('" + str(insertId) + "', 'REVERTED_FROM', '"+str(revertJobId)+"');")
                flib.db_insert(sqlList,1)
                paramArr.update({'Job_ID': str(insertId)})
                jenkinsJobProcess(request,'revert_e2_update',{'Job_ID': insertId, 'Previous_Job_ID': revertJobId})
                data = {'status': 1, 'msg': 'Job created successfully with Job Id  #' + str(insertId)}  # create json array to response json
                return HttpResponse(json.dumps(data), content_type='application/json')
            except Exception as e:
                print('Error (create_job at ' + str(step) + ' of Type = ' + str(type) + ')', e)
                data = {'status': 0, 'msg': 'Issue in processing your request'}  # create json array to response json
                return HttpResponse(json.dumps(data), content_type='application/json')
        elif str(step) == str(5):
            try:
                sql = "SELECT * FROM %s where EngineType = 2 and Flag = 3 order by JobId desc limit 0,1 " % ("jobinfo",)
                data_row = flib.db_query(sql, 1)
                jobId = data_row[0]
                if data_row[1] != 5:
                    data = {'status': 0, 'msg': '#3 Not able to process your request, Please try after some time'}
                    return HttpResponse(json.dumps(data), content_type='application/json')
                # rest API check and validate
                apiResult = verify_release.get_release_status(jobId, 2)
                if str(apiResult['error_code']) == str(0) and str(apiResult['status']) == str(1):
                    data = {'status': 2, 'msg': 'Verification Failed.'}
                    return HttpResponse(json.dumps(data), content_type='application/json')
                elif str(apiResult['error_code']) == str(0) and str(apiResult['status']) == str(0):
                    vdb = apiResult['vdb']
                else:
                    data = {'status': 2, 'msg': 'Error in verification script'}
                    return HttpResponse(json.dumps(data), content_type='application/json')
                paramArr.update({'Job_ID': str(jobId)})
                if request.method == 'POST':
                    userName = request.user.get_username()
                    sqlList = ["UPDATE jobinfo  SET `JobState`='6' WHERE  JobId = '" + str(jobId) + "'  ;"]
                    sqlList.append("INSERT INTO jobstatedetails (`JobID`, `JobState`,`PercentDone`) VALUES ('" + str(jobId) + "', '6', '100');")
                    sqlList.append("INSERT INTO releaseinfo (`JobID`, `Notes`, `VDB`, `UserName`) VALUES ('" + str(jobId) + "','" + request.POST['Note'] + "','" + str(vdb) + "', '" + str(userName) + "');")
                    flib.db_insert(sqlList,1)
                    try:
                        jenkinsJobProcess(request,'backup_e2',{"Job_ID":str(jobId),"Update_Type":"e2"})
                    except Exception as e:
                        print('Error (backup_e2 jenkins job) ',e)
                data = {'status': 1, 'msg': 'Job #'+str(jobId)+' mark released successfully !'}  # create json array to response json
                return HttpResponse(json.dumps(data), content_type='application/json')
            except Exception as e:
                print('Error (create_job at ' + str(step) + ' of Type = ' + str(type) + ')', e)
                data = {'status': 0, 'msg': 'Issue in processing your request'}  # create json array to response json
                return HttpResponse(json.dumps(data), content_type='application/json')
    if type == 'qh':
        paramArr = {}
        if str(step) == str(1):
            try:
                Package_ListArray = str(request.POST['Package_List'])
                if Package_ListArray != request.POST['additional_package']:
                    Package_ListArray = Package_ListArray[1:-1].replace('"','')
                    if request.POST['additional_package'] != 'NA':
                        Package_ListArray += ","+str(request.POST['additional_package']).replace(" ","").replace("'","").replace('"','').rstrip((',')).strip()
                    print('Package_ListArray',Package_ListArray)
                if Package_ListArray == '':
                    data = {'status': 0,'msg': "No Package found"}
                    return HttpResponse(json.dumps(data), content_type='application/json')
                extensions = ('.zip','.ZIP')
                for url in Package_ListArray.split(","):
                    if not url.endswith(extensions):
                        data = {'status': 0,'msg': "Please provide URL with .Zip extension. ("+str(url)+")"}
                        return HttpResponse(json.dumps(data), content_type='application/json')

                    if len(Package_ListArray.split(",")) > settings.RELEASE_PACKAGE_LIMIT:
                        data = {'status': 0, 'msg': 'Package should not be more then'+str(settings.RELEASE_PACKAGE_LIMIT)+'.'}
                        return HttpResponse(json.dumps(data), content_type='application/json')
                Package_ListArrayWhere = ''
                cnt = 0
                for url in Package_ListArray.split(","):
                    if cnt == 0:
                        cnt = 1
                        Package_ListArrayWhere += ' ( PackageID = "'+str(url)+'" AND  PackageState = 6 ) '
                    else :
                        Package_ListArrayWhere += ' OR ( PackageID = "'+str(url)+'" AND  PackageState = 6 ) '
                sql = "SELECT * FROM qhpackagedetails where "+str(Package_ListArrayWhere)+"  order by JobID desc"
                data_row = flib.db_query(sql)
                if len(data_row) != 0:
                    arrayPackage_List = ''
                    for row in data_row:
                        arrayPackage_List = row[1]+", "+arrayPackage_List
                    arrayPackage_List = arrayPackage_List[:-1]
                    data = {'status': 0,'msg': "Unable to process your request as Package ID (" + arrayPackage_List + ") already exist in record "}
                    return HttpResponse(json.dumps(data), content_type='application/json')
                else:
                    currentBuild = getJobStatus(type,1)
                    print('currentBuild',currentBuild)
                    if currentBuild['status'] == 0:
                        data =  {'status': 0, 'msg': "Unable to process your request as "+currentBuild['response']}
                        return HttpResponse(json.dumps(data), content_type='application/json')
                    sql = "SELECT * FROM %s where EngineType = 1 and Flag = 1  order by JobId desc  limit 0,1 " % ("jobinfo", )
                    data_row = flib.db_query(sql,1)
                    if data_row is not None:
                        if data_row[1] not in {6,7}:
                            data =  {'status': 0, 'msg': 'Previous job not completed.'}
                            return HttpResponse(json.dumps(data), content_type='application/json')
                    userName = request.user.get_username()

                    sql = "INSERT INTO jobinfo (`JobState`,`EngineType`,`Flag`,`UserName`) VALUES ('1','1','1','"+userName+"');"
                    insertId = flib.db_insert(sql)
                    sql= "INSERT INTO jobstatedetails (`JobID`, `JobState`,`PercentDone` ) VALUES ('"+str(insertId)+"', '1','100');"
                    flib.db_insert(sql)
                    paramArr.update({'Job_ID': str(insertId),'Package_List':str(Package_ListArray),'Update_frequency':str(request.POST['Update_frequency'])})
                    jenkinsJobProcess(request,'download_qh',paramArr)
                    data = {'status':1,'msg':'Job Created successfully with Job Id  #'+str(insertId)}  # create json array to response json
                    return HttpResponse(json.dumps(data), content_type='application/json')
            except Exception as e:
                print('Error (create_job at ' + str(step) + ' of Type = ' + str(type) + ')', e)
                data = {'status':0,'msg':'Issue in processing your request'}  # create json array to response json
                return HttpResponse(json.dumps(data), content_type='application/json')
        elif str(step) == str(2):
            try:
                sql = "SELECT * FROM %s where EngineType = 1 and Flag = 1  order by JobId desc  limit 0,1 " % ("jobinfo", )
                data_row = flib.db_query(sql,1)
                jobId = data_row[0]
                if data_row[1] != 3:
                    data =  {'status': 0, 'msg': '#1 : Not able to process your request, Please try after some time'}
                    return HttpResponse(json.dumps(data), content_type='application/json')
                sqlList = ["UPDATE jobinfo  SET `JobState`='4' WHERE  JobId = '"+str(jobId)+"'  ;"]
                sqlList.append("INSERT INTO jobstatedetails (`JobID`, `JobState`,`PercentDone`) VALUES ('"+str(jobId)+"', '4', '100');")
                flib.db_insert(sqlList,1)

                sql = "SELECT Params FROM jobinfojenkins  where  JenkinsJobName =  'download_qh' order by JobId desc limit 0,1"
                data_row = flib.db_query(sql, 1)
                data = json.loads(data_row[0])
                paramArr.update({"Job_ID": str(jobId),"Update_frequency":str(data['Update_frequency'])})
                jenkinsJobProcess(request,'create_qh_update_release',paramArr)
                data = {'status':1,'msg':'Job #'+str(jobId)+' Mark Verified successfully and initiaing Release Update Creation !'}  # create json array to response json
                return HttpResponse(json.dumps(data), content_type='application/json')
            except Exception as e:
                print('Error (create_job at ' + str(step) + ' of Type = ' + str(type) + ')', e)
                data = {'status':1,'msg':'Job created successfully !'+str(e)}  # create json array to response json
                return HttpResponse(json.dumps(data), content_type='application/json')
        elif str(step) == str(3):
            try:
                sql = "SELECT * FROM %s where EngineType = 1 and Flag = 1 order by JobId desc  limit 0,1 " % ("jobinfo",)
                data_row = flib.db_query(sql, 1)
                jobId = data_row[0]
                if data_row[1] != 5:
                    data = {'status': 0, 'msg': '#3 Not able to process your request, Please try after some time'}
                    return HttpResponse(json.dumps(data), content_type='application/json')
                apiResult = verify_release.get_release_status(jobId, 1)
                print('addd',apiResult)
                if str(apiResult['error_code']) == str(0) and str(apiResult['status']) == str(1):
                    data = {'status': 2, 'msg': 'Verification Failed.'}
                    return HttpResponse(json.dumps(data), content_type='application/json')
                elif str(apiResult['error_code']) == str(0) and str(apiResult['status']) == str(0):
                    vdb = apiResult['vdb']
                else:
                    data = {'status': 2, 'msg': 'Error in verification script'}
                    return HttpResponse(json.dumps(data), content_type='application/json')

                paramArr.update({'Job_ID': str(jobId)})
                if request.method == 'POST':
                    note = ""
                    userName = request.user.get_username()
                    try :
                        if 'Note' in request.POST and request.POST['Note'] != '':
                            note = request.POST['Note']
                        else:
                            note = reqType['Note']
                    except Exception as e:
                        print('No note found ',e)
                        note = ''
                    sqlList = ["UPDATE jobinfo  SET `JobState`='6' WHERE  JobId = '" + str(jobId) + "' "]
                    sqlList.append("INSERT INTO jobstatedetails (`JobID`, `JobState`,`PercentDone`) VALUES ('" + str(jobId) + "', '6', '100')")
                    sqlList.append("INSERT INTO releaseinfo (`JobID`, `Notes`, `VDB`, `UserName`) VALUES ('" + str(jobId) + "','" + str(note) + "','" + str(vdb) + "', '" + str(userName) + "');")
                    #sqlList.append("UPDATE jobinfo  SET `JobState`='6' WHERE  JobId = '" + str(jobId) + "' and EngineType = 1;")
                    sqlList.append("UPDATE qhpackagedetails  SET `PackageState`='6' WHERE  JobID = '" + str(jobId) + "' ;")
                    flib.db_insert(sqlList,1)
                    try:
                        jenkinsJobProcess(request, 'backup_qh', {"Job_ID": str(jobId), "Update_Type": "qh"})
                    except Exception as e:
                        popup = 'Error :'+e
                data = {'status': 1, 'msg': 'Job #' + str( jobId) + ' mark released successfully !'}  # create json array to response json
                return HttpResponse(json.dumps(data), content_type='application/json')
            except Exception as e:
                print('Error (create_job at ' + str(step) + ' of Type = ' + str(type) + ')', e)
                data = {'status': 0, 'msg': 'Issue in processing your request'}  # create json array to response json
                return HttpResponse(json.dumps(data), content_type='application/json')
        elif str(step) == str(4):
            try:
                revertJobId = request.POST['JobId']
                sql = "SELECT * FROM %s where EngineType = 1 and Flag = 1  order by JobId desc  limit 0,1 " % ("jobinfo",)
                data_row = flib.db_query(sql, 1)
                jobId = data_row[0]
                newJobId = int(jobId)
                if data_row[1] not in {5, 6, 7}:
                    data = {'status': 0, 'msg': 'Previous job not completed.'}
                    return HttpResponse(json.dumps(data), content_type='application/json')
                userName = request.user.get_username()
                sql = "INSERT INTO jobinfo (`JobState`,`EngineType`,`Flag`,`UserName`) VALUES ('1','1','3','" + userName + "');"
                insertId = flib.db_insert(sql)
                sql = "INSERT INTO jobstatedetails (`JobID`, `JobState`,`PercentDone` ) VALUES ('" + str(insertId) + "', '1','100');"
                flib.db_insert(sql)
                paramArr.update({'Job_ID': str(insertId)})
                jenkinsJobProcess(request,'create_qh_update_release',{'Job_ID': insertId, 'Previous_Job_ID': revertJobId})
                data = {'status': 1, 'msg': 'Job created successfully with Job Id  #' + str(insertId)}  # create json array to response json
                return HttpResponse(json.dumps(data), content_type='application/json')
            except Exception as e:
                print('Error (create_job at ' + str(step) + ' of Type = ' + str(type) + ')', e)
                data = {'status': 0, 'msg': 'Issue in processing your request'}  # create json array to response json
                return HttpResponse(json.dumps(data), content_type='application/json')
        elif str(step) == str(5):
            try:
                sql = "SELECT * FROM %s where EngineType = 1 and Flag = 3 order by JobId desc  limit 0,1 " % ("jobinfo",)
                data_row = flib.db_query(sql, 1)
                jobId = data_row[0]
                if data_row[1] != 5:
                    data = {'status': 0, 'msg': '#5 Not able to process your request, Please try after some time'}
                    return HttpResponse(json.dumps(data), content_type='application/json')
                #rest API check and validate
                apiResult = verify_release.get_release_status(jobId, 1)
                if str(apiResult['error_code']) == str(0) and str(apiResult['status']) == str(1):
                    data = {'status': 2, 'msg': 'Verification Failed.'}
                    return HttpResponse(json.dumps(data), content_type='application/json')
                elif str(apiResult['error_code']) == str(0) and str(apiResult['status']) == str(0):
                    vdb = apiResult['vdb']
                else:
                    data = {'status': 2, 'msg': 'Error in verification script'}
                    return HttpResponse(json.dumps(data), content_type='application/json')

                sql = "INSERT INTO jobstatedetails (`JobID`, `JobState`,`PercentDone`) VALUES ('" + str(jobId) + "', '6', '100');"
                flib.db_insert(sql)
                paramArr.update({'Job_ID': str(jobId)})
                if request.method == 'POST':
                    userName = request.user.get_username()
                    sql = "INSERT INTO releaseinfo (`JobID`, `Notes`, `VDB`, `UserName`) VALUES ('" + str(jobId) + "','" + request.POST['Note'] + "','" + str(vdb) + "', '" + str(userName) + "');"
                    flib.db_insert(sql)

                data = {'status': 1, 'msg': 'Job #'+str(jobId)+' mark released successfully !'}  # create json array to response json
                return HttpResponse(json.dumps(data), content_type='application/json')
            except Exception as e:
                print('Error (create_job at ' + str(step) + ' of Type = '+str(type)+')', e)
                data = {'status': 0, 'msg': 'Issue in processing your request'}  # create json array to response json
                return HttpResponse(json.dumps(data), content_type='application/json')

@database_connection_check
def fail_job(request,type,reason_fail=''):
    if reason_fail == '':
        if request.POST['Note']:
            reason_fail = str(request.POST['Note'])
        else:
            reason_fail = 'Failed Mannualy by Web Interface'
    if type in config.EngineTypeArr:
        if not request.is_ajax() or request.method == 'GET':
            return HttpResponse('Invalid Request')
        return HttpResponse( json.dumps(failJobProcess(config.EngineTypeArr[type], str(reason_fail), request.user.get_username())),content_type='application/json')

@database_connection_check
def failJobProcess(engine,reason,user):
    try:
        sql = 'SELECT * FROM jobinfo where EngineType = '+str(engine)+' order by JobId desc  limit 0,1 '
        data_row = flib.db_query(sql,1)
        if data_row[1] in {6,7}:
            config.print_dstring('Already job is marked as fail or completed ie.'+str(data_row[1]))
            return {'status': 0, 'msg': 'Not able to process your request, Please try after some time'}
        jobId = data_row[0]
        sqlList = ["UPDATE jobinfo SET `JobState`= '7' where EngineType = '"+str(engine)+"' and  JobId = '"+str(jobId)+"'"]
        sqlList.append("INSERT INTO jobstatedetails (`JobID`, `JobState`) VALUES ('"+str(jobId)+"', '7');")
        sqlList.append("INSERT INTO failedjobinfo (`JobID`, `FailedReason`, `Notes`, `UserName`) VALUES ('"+str(jobId)+"','3','"+str(reason)+"','"+str(user)+"');")
        flib.db_insert(sqlList, 1)
        return  {'status': 1, 'msg': 'Marked failed successfully.'}
    except Exception as e:
        print('Error (failJobProcess)',e)
        return  {'status': 0, 'msg': 'Issue in processing your request'}

@login_required(login_url='/login/')
@database_connection_check
def build_history(request,type):
    if not type in config.EngineTypeArr:
        return HttpResponse('Invalid request')
    flib.setMetaInformation(request, 'Job History : '+type.upper(),OrderedDict([('Job History : '+type.upper(),'')]))
    typeArr =  {'e2':2,'qh':1}
    if not type in typeArr:
        return HttpResponse('Invalid request.')
    return render(request, 'build/build-history.html', {'type':type})

@login_required(login_url='/login/')
def build_history_ajax(request,type):
    if not type in config.EngineTypeArr:
        return HttpResponse('Invalid request')
    start = request.GET['start']
    length = request.GET['length']
    draw = request.GET['draw']
    search_value = request.GET['search[value]']
    sql = "SELECT count(JobId) FROM jobinfo where jobinfo.EngineType = '"+str(config.EngineTypeArr[type])+"'"
    db_obj_total_row = flib.db_query(sql,1)
    column = {0:'JobID',1:'CreatedDate',2:'Result',3:'UserName',4:'Note',5:'VDB',6:'IsBuildEngine', 7: 'Flag', 8: 'JobID'}
    order_column = column[int(request.GET['order[0][column]'])]
    order_column_dir = request.GET['order[0][dir]']
    if(search_value != ''):
        sql = "select JobID, CreatedDate, result, UserName, Note, VDB, IsBuildEngine, Flag from ( select jobinfo.JobID,  jobinfo.DateCreated as CreatedDate, 1 as result, jobinfo.UserName as UserName, releaseinfo.Notes as Note, releaseinfo.VDB as VDB, releaseinfo.IsBuildEngine as IsBuildEngine, jobinfo.Flag as Flag  from jobinfo, releaseinfo  where jobinfo.JobID = releaseinfo.JobID  and jobinfo.EngineType = '"+str(config.EngineTypeArr[type])+"' and ( jobinfo.JobId like '%"+search_value+"%' or jobinfo.UserName like '%"+search_value+"%'  or releaseinfo.Notes like '%"+search_value+"%' or jobinfo.Flag like '%"+search_value+"%')   ) as maintbl order by maintbl."+order_column+" "+order_column_dir+"  limit "+start+","+length+" "
        data_row = flib.db_query(sql)
        sql = "select count(JobID) from ( select jobinfo.JobID as JobID from jobinfo, failedjobinfo  where jobinfo.JobID = failedjobinfo.JobID  and jobinfo.EngineType = '"+str(config.EngineTypeArr[type])+"' and ( jobinfo.JobId like '%"+search_value+"%' or jobinfo.UserName like '%"+search_value+"%' or failedjobinfo.Notes like '%"+search_value+"%' )   union all select jobinfo.JobID from jobinfo, releaseinfo  where jobinfo.JobID = releaseinfo.JobID  and jobinfo.EngineType = '"+str(config.EngineTypeArr[type])+"' and ( jobinfo.JobId like '%"+search_value+"%' or releaseinfo.Notes like '%"+search_value+"%' or jobinfo.UserName like '%"+search_value+"%' )   ) as maintbl "
        db_obj_fil_total_row = flib.db_query(sql,1)
        totalRows= db_obj_fil_total_row[0]
    else:
        sql = "select JobID, CreatedDate, result, UserName, Note, VDB, IsBuildEngine, Flag, FailedReason from ( select jobinfo.JobID as JobID, jobinfo.DateCreated as CreatedDate, 0 as result, jobinfo.UserName as UserName,failedjobinfo.Notes as Note,  'NA' as VDB, 'NA' as IsBuildEngine, jobinfo.Flag as Flag, failedjobinfo.FailedReason as FailedReason from jobinfo, failedjobinfo  where jobinfo.JobID = failedjobinfo.JobID  and jobinfo.EngineType = '"+str(config.EngineTypeArr[type])+"'  union all select jobinfo.JobID,  jobinfo.DateCreated as CreatedDate, 1 as result, jobinfo.UserName as UserName, releaseinfo.Notes as Note, releaseinfo.VDB as VDB, releaseinfo.IsBuildEngine as IsBuildEngine, jobinfo.Flag as Flag, 0 as FailedReason from jobinfo, releaseinfo  where jobinfo.JobID = releaseinfo.JobID  and jobinfo.EngineType = '"+str(config.EngineTypeArr[type])+"' ) as maintbl order by maintbl."+order_column+" "+order_column_dir+"  limit "+start+","+length+" "
        data_row = flib.db_query(sql)
        totalRows= db_obj_total_row[0]
    data = []
    for row in  data_row:
        if int(row[2]) == 0:
            row2 = config.JobFailedReason[row[8]]
        else :
            row2 = 'Completed'
        Notes =  str(row[4])
        if len(str(row[4])) >25 :
            Notes = str(row[4])[:25]+'...'
        if str(row[6]) == '1':
            isBuild = 'Yes'
        elif str(row[6]) == '0':
            isBuild = 'No'
        else:
            isBuild = str(row[6])
        if str(row[7]) == '3':
            Flag = "Revert"
        else:
            Flag = "Normal"
        data.append({'JobID':str(row[0]),'CreatedDate':format(row[1]),'Result':str(row2),'UserName':str(row[3]),'Note':Notes,'VDB':format(row[5]),'IsBuildEngine':isBuild,'Flag':Flag,'Details':'<button onclick="show_details_for(' + str(row[0]) + ')" class="navbar-inverse shadow-in" style="min-width:50px"> Details </button>'})
    resp = {"draw": draw, "recordsTotal": db_obj_total_row[0], "recordsFiltered": totalRows, "data":data}
    return HttpResponse(json.dumps(resp), content_type='application/json')

@login_required(login_url='/login/')
@database_connection_check
def build_engine_mgt_ajax(request,type,key=0,action=0):

    if not type in config.EngineTypeArr:
        return HttpResponse('Invalid request')
    if str(key) != str(0):
         return HttpResponse(str(flib.markBuildEngine({request.POST['UpdateID']:str(key)},str(action),request.user.username,'')))

    start = request.GET['start']
    length = request.GET['length']
    draw = request.GET['draw']
    UpdateID = request.GET['UpdateID']
    search_value = request.GET['search[value]']
    sql = "SELECT count(JobId) FROM jobinfo where jobinfo.JobState = 6 and jobinfo.EngineType = '"+str(config.EngineTypeArr[type])+"'"
    db_obj_total_row = flib.db_query(sql,1)
    column = {0:'jobinfo.JobID',1:'jobinfo.CreatedDate',2:'jobinfo.UserName',3:'buildinfo.Notes',4:'releaseinfo.VDB',5:'buildinfo.IsBuildEngine'}
    order_column = column[int(request.GET['order[0][column]'])]
    order_column_dir = request.GET['order[0][dir]']
    if(search_value != ''):
        sql = "select jobinfo.JobID,  jobinfo.DateCreated as CreatedDate, jobinfo.UserName as UserName, releaseinfo.Notes as Notes, releaseinfo.VDB as VDB, releaseinfo.IsBuildEngine as IsBuildEngine  from jobinfo, releaseinfo  where jobinfo.JobID = releaseinfo.JobID  and jobinfo.EngineType = '"+str(config.EngineTypeArr[type])+"' and ( jobinfo.JobId like '%"+search_value+"%' or jobinfo.UserName like '%"+search_value+"%'  or releaseinfo.Notes like '%"+search_value+"%' ) order by releaseinfo."+order_column+" "+order_column_dir+"  limit "+start+","+length+" "
        #sql = "select jobinfo.JobID,  jobinfo.DateCreated as CreatedDate, jobinfo.UserName as UserName, releaseinfo.Notes as Notes, releaseinfo.VDB as VDB, releaseinfo.IsBuildEngine as IsBuildEngine  from jobinfo jobinfo LEFT JOIN releaseinfo ON releaseinfo.JobID = jobinfo.JobID LEFT JOIN buildinfo ON buildinfo.JobID = jobinfo.JobID LEFT JOIN enginemaster ON enginemaster.JobID = jobinfo.JobID  AND enginemaster.UpdateID = "+str(UpdateId)+"  where jobinfo.JobID = releaseinfo.JobID  and jobinfo.EngineType = '"+str(config.EngineTypeArr[type])+"' and ( jobinfo.JobId like '%"+search_value+"%' or jobinfo.UserName like '%"+search_value+"%'  or releaseinfo.Notes like '%"+search_value+"%' ) order by releaseinfo."+order_column+" "+order_column_dir+"  limit "+start+","+length+" "
        data_row = flib.db_query(sql)
        sql = "select count(jobinfo.JobID)from jobinfo,releaseinfo  where jobinfo.JobID = releaseinfo.JobID  and jobinfo.EngineType = '"+str(config.EngineTypeArr[type])+"' and ( jobinfo.JobId like '%"+search_value+"%' or releaseinfo.Notes like '%"+search_value+"%' or jobinfo.UserName like '%"+search_value+"%' )   "
        db_obj_fil_total_row = flib.db_query(sql,1)
        totalRows= db_obj_fil_total_row[0]
    else:
        #sql = "Select jobinfo.JobID,  jobinfo.DateCreated as CreatedDate, jobinfo.UserName as UserName, releaseinfo.Notes as Notes, releaseinfo.VDB as VDB, releaseinfo.IsBuildEngine as IsBuildEngine  from jobinfo, releaseinfo  where jobinfo.JobID = releaseinfo.JobID  and jobinfo.EngineType = '"+str(config.EngineTypeArr[type])+"' order by releaseinfo."+order_column+" "+order_column_dir+"  limit "+start+","+length+" "
        sql = "SELECT jobinfo.JobID, jobinfo.DateCreated, jobinfo.UserName, buildinfo.Notes, releaseinfo.VDB, IFNULL(buildinfo.IsBuildEngine,0) as IsBuildEngine FROM jobinfo JOIN releaseinfo ON jobinfo.JobID = releaseinfo.JobID JOIN enginemaster ON  releaseinfo.JobID = enginemaster.JobID AND enginemaster.UpdateID = '"+str(UpdateID)+"'  LEFT JOIN buildinfo on jobinfo.JobID = buildinfo.JobID AND buildinfo.UpdateID = '"+str(UpdateID)+"' WHERE  jobinfo.EngineType = '"+str(config.EngineTypeArr[type])+"'  order by "+order_column+" "+order_column_dir+"  limit "+start+","+length+" "

        data_row = flib.db_query(sql)
        totalRows= db_obj_total_row[0]
    data = []
    if data_row:
        for row in data_row:
            if row[5] == 1:
                check_row = '<input type="checkbox" class="editor-active" checked=checked onClick="triggerChecked('+str(row[0])+',0); return false;" >'
            else:
                check_row = '<input type="checkbox" class="editor-active" onClick="triggerChecked('+str(row[0])+',1); return false;" >'
            Notes =  str(row[3])
            if len(str(row[3])) >50 :
                Notes = str(row[3])[:50]+'...'
            data.append({'JobID':str(row[0]),'CreatedDate':format(row[1]),'UserName':str(row[2]),'Notes':Notes,'VDB':format(row[4]),'IsBuildEngine':check_row})
    resp = {"draw": draw, "recordsTotal": db_obj_total_row[0], "recordsFiltered": totalRows, "data":data}
    return HttpResponse(json.dumps(resp), content_type='application/json')

@login_required(login_url='/login/')
@database_connection_check
def build_engine_mgt(request,type):
    flib.setMetaInformation(request, 'Mark Build Engine For  : ' + type.upper(),OrderedDict([('Job Engine For : '+type.upper()+'','')]))
    if not type in config.EngineTypeArr:
        return HttpResponse('Invalid request')
    getUpdateID,getUpdateIDName = '',''
    if request.GET and 'UpdateID' in request.GET:
        getUpdateID = request.GET['UpdateID']
        getUpdateIDName = flib.getUpdateIdName(request, "("+str(getUpdateID)+")")
        if getUpdateIDName is None or len(getUpdateIDName) == 0:
            messages.add_message(request,messages.ERROR, "<span class='glyphicon glyphicon-info-sign'></span><b> UpdateID  " + str(getUpdateID) + " is Not Available.</b>")
            return render(request, 'build/build_engine_mgt.html')
        getUpdateIDName = getUpdateIDName[0]['update_id_str']
    UpdateIdList = getUpdateId(request,str(config.EngineTypeArr[type]), getUpdateID)
    return render(request, 'build/build_engine_mgt.html', {'type':type,'UpdateIdList':UpdateIdList,'getUpdateIDName':getUpdateIDName})

def getUpdateId(request,type,getUpdateID =''):
    sql = 'select DISTINCT(enginemaster.UpdateID) from enginemaster join releaseinfo on enginemaster.JobID = releaseinfo.JobID join jobinfo on releaseinfo.JobID = jobinfo.JobID and jobinfo.EngineType = "'+str(type)+'"'
    updateIdList = flib.db_query(sql)
    updateIdDropdown = ''
    updateIdDropdown += "<div class='col-md-4'></div><div class='text-center col-md-3'>"
    updateIdDropdown += "<select id='updateIdDropdown"+str(type)+"' class='form-control' onchange='admSelectCheck(this);'>"
    updateIdDropdown += '<option value="" selected=selected> - - Select Update ID - - </option>'
    uidArr,getUpdateIdAndName = [],''
    for uid in updateIdList:
        uidArr.append(uid[0])
    getUpdateIdAndName = flib.getUpdateIdName(request,str(tuple(uidArr)))
    for ui in getUpdateIdAndName:
        if str(getUpdateID) == str(ui['update_id']):
            selected = 'selected=selected'
        else:
            selected = ''
        updateIdDropdown += '<option ' + selected + ' value="' + str(ui['update_id']) + '" >' + str(ui['update_id_str']) + '</option>'
    updateIdDropdown += "</select>"
    updateIdDropdown += "</div>"
    return updateIdDropdown


@database_connection_check
def getJobStatus(engineType,type=0):
    if not engineType in config.EngineTypeArr:
        return {'status':0,'response':'Invalid Request'}
    where_str = '  jobinfo.EngineType = '+str(config.EngineTypeArr[engineType])
    if str(type) != str(0):
       where_str +=  ' and  jobinfo.Flag = '+str(type)
    sql = 'SELECT jobstatedetails.JobID, jobstatedetails.JobState, jobstatedetails.PercentDone  FROM jobstatedetails where jobstatedetails.JobID = (select jobinfo.JobID from jobinfo where   '+where_str+' order by jobinfo.JobID desc limit 0,1) order by JobState desc limit 1'
    data_row = flib.db_query(sql,1)
    if data_row is not None:
        if data_row[1] not in {6,7}:
            data = {'status':0,'response':'Job #'+str(data_row[0])+' is in progress.'}
        else:
            data = {'status':1,'response':'No job is running.'}
    else:
        data = {'status':1,'response':'No job is running.'}
    return data

@login_required(login_url='/login/')
@database_connection_check
def build_id_details(request,pid):
    sql = "SELECT * FROM jobinfo where JobId = "+pid+" limit 1; "
    jobInfo = flib.db_query(sql)
    if len(jobInfo) == 0:
        messages.add_message(request, messages.ERROR,"<span class='glyphicon glyphicon-info-sign'></span><b> JobID "+pid+" is Not Available.</b>")
        return render(request, 'build/build-id.html')
    flib.setMetaInformation(request, 'Job Details : #' + pid, OrderedDict([('Job History : '+config.EngineType[jobInfo[0][3]], '/history/' + config.EngineType[jobInfo[0][3]].lower() + '/'), ('Job Details : #' + pid, '')]))
    jobId,JobStatus,flag = jobInfo[0][0],jobInfo[0][1],jobInfo[0][4]
    content = '<div id="build-details">'
    content += getBuildDetailsBasic(jobInfo[0])
    content += '</div>'
    sql = 'select UpdateID from enginemaster where JobID = ' + str(jobId)
    enginemasterData = flib.db_query(sql)
    updateIDArr = {}
    for UpdateID in enginemasterData:
        updateIDArr.update({UpdateID[0]:UpdateID[0]})
    if updateIDArr:
        content += getSoloInfo(request,jobId,flag,JobStatus,updateIDArr,config.EngineType[jobInfo[0][3]])
        content += getDiffInfo(request,jobId,flag,JobStatus,updateIDArr,config.EngineType[jobInfo[0][3]])
    return render(request, 'build/build-id.html', {'selectedJobId':pid,'content':content,'JobStatus':JobStatus,'updateIDArr':updateIDArr})

@database_connection_check
def getBuildDetailsBasic(jobInfo):
    jobId = jobInfo[0]
    sql = 'select sum(jobstatedetails.TimeTaken), TIMESTAMPDIFF(SECOND,min(StartTime),max(StartTime)) as totaltime from  jobstatedetails  where  jobstatedetails.jobId = '+str(jobId)+''
    totalTime = flib.db_query(sql)
    content = ''
    content += '<div class="build-basic shadow-in detail-head " id="build-basic-head" data-toggle="" data-target="#build-basic-info" ><h4 style="width:100%">Summary<i class="build-basic-info glyphicon glyphicon-minus pull-right"></i></h4></div>';
    content += '<div id="build-basic-info"  class="build-basic detail-body  collapse in" >'
    content += '<table class="job-dtl-tbl  shadow-in" >'
    content += '<tr><th class="tblHead" colspan="2">Job Details</th></tr>'
    content += '<tr><th>JobID</th><td>'+str(jobId)+'</td></tr>'
    content += '<tr><th>Created On</th><td>'+str(jobInfo[2])+'</td></tr>'
    content += '<tr><th>Created By</th><td>'+str(jobInfo[5])+'</td></tr>'
    content += '<tr><th>EngineType</th><td>'+config.EngineType[jobInfo[3]]+'</td></tr>'
    content += '<tr><th>Job Type</th><td>'+config.JobInfoFlag[jobInfo[4]]+'  </td></tr>'
    if jobInfo[4] == 3:
        content += '<tr><th>Reverted From </th><td> '+str(flib.getRevertJobID(jobId))+' </td></tr>'
    content += '<tr><th>Total script Time</th><td>' + str(flib.returnTimeString(totalTime[0][0] * 1000)) + '</td></tr>'
    content += '<tr><th>Actual taken Time</th><td>' + str(flib.returnTimeString(totalTime[0][1] * 1000)) + '</td></tr>'
    content += '<tr><th>Log</th><td>'+'<a target="_blank" href="/jenkins-log/'+str(jobId)+'">View Log</a></td></tr>'
    content += '</table>'
    if jobInfo[1] == 6:
        sql = 'select * from releaseinfo where JobID = '+str(jobId)
        releaseinfoData = flib.db_query(sql,1)
        content += '<table class="job-dtl-tbl shadow-in">'
        content += '<tr><th class="tblHead" colspan="2">Release Information</th></tr>'
        if releaseinfoData is None:
            content += '<tr><td colspan=''2 >No data</td></tr>'
        else:
            jobSteps = config.jobSteps[jobInfo[4]]
            content += '<tr><th>VDB</th><td>'+format(releaseinfoData[1])+'</td></tr>'
            content += '<tr><th>Note</th><td>'+str(releaseinfoData[2])+'</td></tr>'
            content += '<tr><th>IsBuildEngine</th><td>'+config.IsBuildEningine[releaseinfoData[3]]+'</td></tr>'
            content += '<tr><th>Released by</th><td>'+str(releaseinfoData[4])+'</td></tr>'
        content += '</table>'
    elif jobInfo[1] == 7:
        sql = 'select * from failedjobinfo where JobID = '+str(jobId)
        failedjobinfoData = flib.db_query(sql,1)
        content += '<table class="job-dtl-tbl shadow-in" >'
        content += '<tr><th class="tblHead" colspan="2">Failed Job Information</th></tr>'
        if failedjobinfoData is None:
            content += '<tr><td colspan=''2 >No data</td></tr>'
        else:
            content += '<tr><th>Failed Reason</th><td>'+config.FailedReason[failedjobinfoData[1]]+'</td></tr>'
            content += '<tr><th>Note</th><td>'+str(failedjobinfoData[2])+'</td></tr>'
            content += '<tr><th>Failed by</th><td>'+str(failedjobinfoData[3])+'</td></tr>'
        content += '</table>'
    content += '<div class="clear"></div>'
    sql = "SELECT *  FROM jobstatedetails where JobID = "+str(jobId)+" order by JobState asc "
    jobStagesData = flib.db_query(sql)
    if jobStagesData is None:
            content += '<table class="jobSteps shadow-in "><tr><th class="tblHead" colspan="2">Job Steps</th></tr></table>'
            content += '<p>No data</p>'
    else:
        jobStageActualArr = {}
        for jobStageActual in  jobStagesData:
            jobStageActualArr.update({jobStageActual[1]:jobStageActual})
        content += '<table class="jobSteps shadow-in "><tr><th class="tblHead" colspan="2">Job Steps</th></tr></table>'
        content += '<div class="row builddtl-steps">'
        content += flib.jobBoxes(str(config.EngineType[jobInfo[3]]).lower(),jobInfo[4],jobId,0)
        content += '</div>'
    content += '</div>'
    content += '<div class="clear"></div>'
    content += '</div>'
    return content

#revert functions start
@login_required(login_url='/login/')
@database_connection_check
@jenkins_check
def build_revert_list(request,type):
    flib.setMetaInformation(request,'Revert Existing ' + type.upper()+' Job',OrderedDict( [('Revert Existing '+type.upper()+' Job','')]))
    if not type in config.EngineTypeArr:
        return HttpResponse('Invalid request')
    return render(request, 'build/revert-build-list.html', {'type':type})

@login_required(login_url='/login/')
@database_connection_check
@jenkins_check
def build_revert(request,type):
    if not type in config.EngineTypeArr:
        return HttpResponse('Invalid request')
    type_key = ''
    for key, value in config.EngineType.items():
        if value == type.upper():
            type_key = key
    sql = "select * from jobinfo where jobinfo.EngineType = %s and jobinfo.flag = 3 order by jobinfo.JobID desc limit 1 " %(str(type_key))
    jobInfo = flib.db_query(sql, 1)
    flib.setMetaInformation(request, 'Active Job : #' + str(jobInfo[0]), OrderedDict([('Revert Existing ' + type.upper()+' Job', '/revert/' + type + '/list/'), ('Active Job : #' + str(jobInfo[0]), '')]))
    return render(request, 'build/revert-build.html', {'type':str(type),'JobId':str(jobInfo[0]),'failedTypes':config.FailedReason})

@login_required(login_url='/login/')
def revert_list_ajax(request,type):
    if not type in config.EngineTypeArr:
        return HttpResponse('Invalid request')
    start = request.GET['start']
    length = request.GET['length']
    draw = request.GET['draw']
    search_value = request.GET['search[value]']
    sql = "select count(jobinfo.JobID) from jobinfo right  join releaseinfo on jobinfo.JobID = releaseinfo.JobID where jobinfo.EngineType = '"+str(config.EngineTypeArr[type])+"' "
    db_obj_total_row = flib.db_query(sql,1)
    column = {0:'JobID',1:'CreatedDate',2:'Result',3:'UserName',4:'Note',5:'VDB',6:'IsBuildEngine',7:'Flag',8:'JobID'}
    order_column = column[int(request.GET['order[0][column]'])]
    order_column_dir = request.GET['order[0][dir]']
    try:
        if(search_value != ''):
            sql = "select JobID, CreatedDate, result, UserName, Note, VDB, IsBuildEngine, Flag from ( select jobinfo.JobID,  jobinfo.DateCreated as CreatedDate, 1 as result, jobinfo.UserName as UserName, releaseinfo.Notes as Note, releaseinfo.VDB as VDB, releaseinfo.IsBuildEngine as IsBuildEngine, jobinfo.Flag as Flag  from jobinfo, releaseinfo  where jobinfo.JobID = releaseinfo.JobID  and jobinfo.EngineType = '"+str(config.EngineTypeArr[type])+"' and ( jobinfo.JobId like '%"+search_value+"%' or jobinfo.UserName like '%"+search_value+"%'  or releaseinfo.Notes like '%"+search_value+"%' or jobinfo.Flag like '%"+search_value+"%')   ) as maintbl order by maintbl."+order_column+" "+order_column_dir+"  limit "+start+","+length+" "
            data_row = flib.db_query(sql)
            sql = "select count(JobID) from ( select jobinfo.JobID from jobinfo, releaseinfo  where jobinfo.JobID = releaseinfo.JobID  and jobinfo.EngineType = '"+str(config.EngineTypeArr[type])+"' and ( jobinfo.JobId like '%"+search_value+"%' or releaseinfo.Notes like '%"+search_value+"%' or jobinfo.UserName like '%"+search_value+"%' or jobinfo.Flag like '%"+search_value+"%' )   ) as maintbl "
            db_obj_fil_total_row = flib.db_query(sql,1)
            totalRows= db_obj_fil_total_row[0]
        else:
            sql = "select JobID, CreatedDate, result, UserName, Note, VDB, IsBuildEngine,Flag from ( select jobinfo.JobID,  jobinfo.DateCreated as CreatedDate, 1 as result, jobinfo.UserName as UserName, releaseinfo.Notes as Note, releaseinfo.VDB as VDB, releaseinfo.IsBuildEngine as IsBuildEngine,jobinfo.Flag as Flag  from jobinfo, releaseinfo  where jobinfo.JobID = releaseinfo.JobID  and jobinfo.EngineType = '"+str(config.EngineTypeArr[type])+"' ) as maintbl order by maintbl."+order_column+" "+order_column_dir+"  limit "+start+","+length+" "
            data_row = flib.db_query(sql)
            totalRows= db_obj_total_row[0]

        data = []
        sql = "SELECT * FROM jobinfo where EngineType =  " + str( config.EngineTypeArr[type]) + " order by JobId desc   limit 1 "
        latestBuild = flib.db_query(sql, 1)
        if latestBuild:
            if latestBuild[1] == 6:
                latestCompletedJobID = latestBuild[0]
            else :
                sql = "select JobID from jobinfo where  jobinfo.EngineType = " + str(config.EngineTypeArr[type]) + " and JobState = '6' order by JobID desc limit 1"
                latestCompletedJobIDObj = flib.db_query(sql,1)
                latestCompletedJobID = latestCompletedJobIDObj[0]
        for row in data_row:
            row2 = 'Completed <span class="glyphicon glyphicon-ok-sign"></span>'
            event =  str(row[0])
            revertRunningId =  str(latestBuild[0])
            jobRunningId = '0'
            if latestBuild[1] in (6,7):
                revertRunningId = '0'
                jobRunningId = '0'
            if latestBuild[4] == 1 and not latestBuild[1] in (6,7):
                revertRunningId = '0'
                jobRunningId = str(latestBuild[0])
            isBuild = ''
            if str(row[6]) == '1':
                isBuild = 'Yes'
            elif str(row[6]) == '0':
                isBuild = 'No'
            else:
                isBuild = str(row[6])
            Notes = str(row[4])
            if len(str(row[4])) > 25:
                Notes = str(row[4])[:25] + '...'
            if row[0] == latestCompletedJobID :
                revertBtn = ''
            else :
                revertBtn = '<button onclick="job_process_confirm(' + event + ',' + revertRunningId + ',' + jobRunningId + ');" class="navbar-inverse shadow-in" >Revert</button>'
            data.append({'JobID': str(row[0]), 'CreatedDate': format(row[1]), 'UserName': str(row[3]), 'Note': Notes,'VDB': format(row[5]), 'IsBuildEngine': isBuild, 'Flag': str(config.JobInfoFlag[row[7]]),'Revert': revertBtn})
    except Exception as e:
        print('Error(DB): ',e)
    resp = {"draw": draw, "recordsTotal": db_obj_total_row[0], "recordsFiltered": totalRows, "data":data}
    return HttpResponse(json.dumps(resp), content_type='application/json')

@login_required(login_url='/login/')
@database_connection_check
def previous_builds(request,type,build_type=1):
    offset,perPage = 1,10
    if 'jobid' not in request.POST or request.POST['jobid'] == 0:
        latestId = str(0)
    else :
        latestId = str(request.POST['jobid'])
    sql = "select jobinfo.JobID from jobinfo where jobinfo.JobID >= '"+str(latestId)+"' and jobinfo.EngineType = '"+str(config.EngineTypeArr[type])+"' order by jobinfo.JobID desc "
    JobCount = flib.db_query(sql)
    if str(len(JobCount)) == str(1) :
        data = {'jobid':str(JobCount[0][0])}
    else:
        previous_buildHtml,maxJobID = flib.previousBuildHtml(str(type),str(build_type),str(offset), str(15),request)
        content = '<div class="previous-builds">' + previous_buildHtml + '</div>'
        print(content)
        if len(JobCount) == 0 :
            JobCount = 0
        else:
            JobCount = str(JobCount[0][0])
        data = {'data': content, 'show':'completed','jobid':str(JobCount)}
    return HttpResponse(json.dumps(data), content_type='application/json')

#render diff Details
@login_required(login_url='/login/')
@database_connection_check
def build_diff_detail_ajax(request):
    start = request.GET['start']
    length = request.GET['length']
    draw = request.GET['draw']
    selectedJobId = request.GET['selectedJobId']
    updateID = request.GET['updateID']
    sqlTotal = "select COUNT(*) from diffdetails  where JobID = "+str(selectedJobId)+" and UpdateID = "+ str(updateID)
    total_data_row = flib.db_query(sqlTotal)
    if total_data_row is None:
        resp = {"draw": draw, "data": "", "recordsTotal": "0", "recordsFiltered": "0"}
        return HttpResponse(json.dumps(resp), content_type='application/json')
    sql = 'select UpdateID from enginemaster where JobID = '+str(selectedJobId) +" and UpdateID = "+ str(updateID)
    enginemasterData = flib.db_query(sql)
    if not enginemasterData :
        resp = {"draw": draw, "data": "", "recordsTotal": "0", "recordsFiltered": "0"}
        return HttpResponse(json.dumps(resp), content_type='application/json')
    engineTypeWhere = ''
    for engineType in enginemasterData:
            engineTypeWhere += 'UpdateID = '+str(engineType[0])
    column = {0: 'PatchFileName', 1: 'PatchFileMD5', 2: 'PatchFileSize ', 3: 'Version', 4: 'FromVersion',5: 'FileCount'}
    order_column = column[int(request.GET['order[0][column]'])]
    order_column_dir = request.GET['order[0][dir]']
    total_rows = str(total_data_row[0][0])
    sql = "select JobID,UpdateID,PatchFileName as pfn,PatchFileMD5,PatchFileSize,FromVersion, Version, (SELECT COUNT(PatchFileName) FROM diffdetails dd, diffpatchdetails dp WHERE dd.PatchFileName = pfn AND dd.FromVersion = dp.FromVersion AND dp.UpdateID="+str(engineType[0])+" AND dd.JobID=dp.JobID AND dp.UpdateID=dd.UpdateID) as FileCount from diffdetails WHERE JobID = "+str(selectedJobId)+" and "+str(engineTypeWhere)+" order by "+order_column+" "+order_column_dir+" limit "+str(start)+","+str(length)+" "
    data_row = flib.db_query(sql)
    data,PatchFileName,UpdateID = [],'',''
    if data_row:
        for row in data_row:
            UpdateID = row[1]
    UpdateID = flib.getUpdateIdName(request,"("+str(UpdateID)+")" )
    if data_row:
        for row in data_row:
            PatchFileName = "<a href='#' role='button' onClick='getPatchFileNameTarget("'"'+str(row[0])+'","'+str(row[1])+'","'+row[2]+'"'")'>"+str(row[2])+"</a>"
            data.append({'JobID': str(row[0]), 'UpdateID': UpdateID[0]['update_id_str'], 'PatchFileName': PatchFileName, 'PatchFileMD5': str(row[3]), 'PatchFileSize': flib.getFileSize(int(row[4])), 'FromVersion': str(row[5]), 'Version': str(row[6]), 'FileCount': str(row[7])})
    resp = {"draw": draw, "data": data, "recordsTotal": total_rows, "recordsFiltered": total_rows}
    return HttpResponse(json.dumps(resp), content_type='application/json')

def patch_file_details_ajax(request):
    patchFileDetails, SoloSizeTotal, SoloSizeTtl, DiffSizeTotal,solodetailsData,PercentChange = [], 0, '', '','',''
    if 'patchFileName' in request.POST:
        patchFileName = request.POST['patchFileName']
        job_id = request.POST['job_id']
        update_id = request.POST['update_id']
        sql = "SELECT diffpatchdetails.DefID, deffileinfo.FileName,diffpatchdetails.OldFileSize,(diffpatchdetails.NewFileSize),diffpatchdetails.DiffSize, (SELECT defsize FROM solodetails WHERE defid = diffpatchdetails.DefID AND updateid = "+update_id+" AND jobid = ( SELECT MAX(solodetails.jobid) FROM solodetails  INNER JOIN releaseinfo  ON solodetails.JobID = releaseinfo.JobID WHERE solodetails.defid = diffpatchdetails.DefID AND solodetails.jobid < "+job_id+") ) as soloTotal  FROM diffpatchdetails INNER JOIN diffdetails ON diffdetails.JobID = diffpatchdetails.JobID AND diffdetails.UpdateID = diffpatchdetails.UpdateID AND diffdetails.FromVersion = diffpatchdetails.FromVersion INNER JOIN deffileinfo ON deffileinfo.DefID=diffpatchdetails.DefID AND deffileinfo.UpdateID=diffpatchdetails.UpdateID WHERE diffdetails.PatchFileName = '" + str(patchFileName) + "' ORDER BY diffpatchdetails.DefID DESC"
        data_row = flib.db_query(sql)
        if data_row:
            for row in data_row:
                patchFileDetails.append({ 'DefID': str(row[0]), 'PatchFileName': str(row[1]), 'OldFileSize':flib.getFileSizeKb(int(row[2])),'NewFileSize': flib.getFileSizeKb(int(row[3])),'DiffSize':flib.getFileSizeKb(int(row[4]))})
                if row[5] is not None:
                    SoloSizeTotal += int(row[5])
            sql = "SELECT DISTINCT SUM(diffpatchdetails.DiffSize) as Diff_Size_count FROM diffpatchdetails INNER JOIN diffdetails ON diffdetails.JobID = diffpatchdetails.JobID AND diffdetails.UpdateID = diffpatchdetails.UpdateID AND diffdetails.FromVersion = diffpatchdetails.FromVersion WHERE diffdetails.PatchFileName = '" + str(patchFileName) + "' ORDER BY PatchFileName DESC"
            DiffSizeTotal = flib.db_query(sql)

            DiffSizeTotal = '<b>'+flib.getFileSizeKbMb(int(DiffSizeTotal[0][0])) + '</b>'
            SoloSizeTotal = '<b>'+flib.getFileSizeKbMb(int(SoloSizeTotal)) + '</b> '
            try:
                sql = 'select UpdateID,count(*),sum(FileSize) from solodetails where JobID = ' + str(job_id) + ' group by UpdateID '
                solodetailsData = flib.db_query(sql)
                if not solodetailsData:
                    return ''
                updateIDArr = {}
                for updateIDinSolo in solodetailsData:
                    updateIDArr.update({updateIDinSolo[0]: updateIDinSolo})
                sql = 'select FromVersion,PatchFileSize from diffdetails where JobID = ' + str(job_id) + ' and UpdateID = ' + str(update_id) + ' order by PatchFileSize asc '
                diffdetailsData = flib.db_query(sql)
                PercentChange = flib.getPercentChange(diffdetailsData[0][1], updateIDArr[int(update_id)][2],1)
            except Exception as e:
                print("Error",e," SQL: ",sql)
    if SoloSizeTotal == 0:
        SoloSizeTotal = "<b>No data available</b>"
    if len(PercentChange) == 0:
        PercentChange = "Reduce by <b>No data available</b>"
    if len(DiffSizeTotal) == 0:
        DiffSizeTotal = "<b>No data available</b>"
    resp = {"data": patchFileDetails,'SoloSizeTotal':str(SoloSizeTotal),'DiffSizeTotal':str(DiffSizeTotal),'PercentChange':str(PercentChange)}
    return HttpResponse(json.dumps(resp), content_type='application/json')

@database_connection_check
def getDiffBuildDetailsDownload(request,jobId,updateId,updateIDArr,engineType):
    update_id_str = ''
    update_id_str  = flib.getUpdateIdName(request, "("+str(updateId)+")")
    content = '<div class="build-details"><div class="build-basic build-summary shadow-in detail-head "><h5>' + str(update_id_str[0]['update_id_str']) + ' <a href="/TableToCsv/?jobId='+str(jobId)+'&engineType='+engineType+'&table=buildDiffDetails&updatetype='+updateId+'""  class="pull-right navbar-inverse shadow-in  extractCSV" ><span class="glyphicon glyphicon-export" ></span></a> <a data-toggle="collapse" data-target="#buildDiffDetails'+str(updateId)+'Table" id="buildDiffDetails'+str(updateId)+'Target" class="floatRight navbar-inverse shadow-in historyBtn">Show Table</a></h5></div>';
    content += '<div id="build-basic-info"  class="build-basic detail-body"><div class="row myrow" ><div class="subtblCol">'
    content += '<table class="subtbl">'
    try:
        sql = 'select FromVersion,count(JobID) as filecount from diffpatchdetails where JobID = ' + str(jobId) + ' and UpdateID = ' + str(updateId) + ' group by FromVersion order by filecount asc '
        diffpatchdetailsData = flib.db_query(sql)
        if diffpatchdetailsData:
            content += '<tr class="odd"><td rowspan="2"><b>Minimum Files</b></td><td>Version </td><td>' + str(format(int(diffpatchdetailsData[0][0]), '02X')) + '</td></tr>'
            content += '<tr class="odd"><td>Files</td><td>' + str(diffpatchdetailsData[0][1]) + ' Files   </td></tr>'
            content += '<tr><td rowspan="2" ><b>Maximum Files</b></td><td>Version </td><td>' + str(format(int(diffpatchdetailsData[len(diffpatchdetailsData) - 1][0]), '02X')) + '</td></tr>'
            content += '<tr><td> Files</td><td> ' + str(diffpatchdetailsData[len(diffpatchdetailsData) - 1][1]) + ' Files   </td></tr>'
            sql = 'select FromVersion,PatchFileSize from diffdetails where JobID = ' + str(jobId) + ' and UpdateID = ' + str(updateId) + ' order by PatchFileSize asc '
            diffdetailsData = flib.db_query(sql)
            content += '<tr class="odd"><td rowspan="3" ><b>Minimum Patch Size</b></td><td>Version </td> <td> ' + str(format(int(diffdetailsData[0][0]), '02X')) + '</td></tr>'
            content += '<tr class="odd"><td>Size</td><td> ' + flib.getFileSize(diffdetailsData[0][1]) + '</td></tr>'
            content += '<tr class="odd"><td>Change in Size </td><td> ' + flib.getPercentChange(diffdetailsData[0][1], updateIDArr[int(updateId)][2]) + '</td></tr>'
            content += '<tr></tr>'
        else:
            content += ''
    except Exception as e:
        content += '<tr><td colspan=3>No data</td></tr>'
        print('Error (getDiffBuildDetailsDownload)', e)
    content += '</table></div></div><div class="clear"></div></div></div>'
    return content

@login_required(login_url='/login/')
@database_connection_check
def build_solo_detail_ajax(request):
    selectedJobId = request.GET['selectedJobId']
    start = request.GET['start']
    length = request.GET['length']
    draw = request.GET['draw']
    updateID = request.GET['updateID']
    sqlTotal = "SELECT count(*)  FROM %s  where JobID = %s and UpdateID = %s"   % ( "solodetails", selectedJobId,updateID)
    column = {0:'JobID', 1: 'UpdateID', 2: 'FileState', 3: 'FileMD5', 4: 'FileSize ', 5: 'DefID', 6: 'DefSize', 7: 'FileName'}
    column = {0: 'DefID' ,1: 'DefSize',2:'FileState',3: 'FileSize',4: 'FileName', 5: 'FileMD5'}
    total_rows = flib.db_query(sqlTotal)
    order_column = column[int(request.GET['order[0][column]'])]
    order_column_dir = request.GET['order[0][dir]']
    if total_rows is None:
        resp = {"draw": draw, "data": "", "recordsTotal": "0", "recordsFiltered": "0"}
        return HttpResponse(json.dumps(resp), content_type='application/json')
    sql = 'select UpdateID from enginemaster where JobID = '+str(selectedJobId) +' and UpdateID = '+updateID+''
    enginemasterData = flib.db_query(sql)
    if not enginemasterData :
        resp = {"draw": draw, "data": "", "recordsTotal": "0", "recordsFiltered": "0"}
        return HttpResponse(json.dumps(resp), content_type='application/json')
    engineTypeWhere = ''
    for engineType in enginemasterData:
        if engineTypeWhere == '':
            engineTypeWhere += "(solodetails.UpdateID = "+str(engineType[0])+" AND deffileinfo.UpdateID = "+str(engineType[0])+")"
        sql = "SELECT solodetails.*, deffileinfo.FileName FROM solodetails LEFT JOIN deffileinfo ON deffileinfo.DefID = solodetails.DefID AND (solodetails.UpdateID = deffileinfo.UpdateID) WHERE solodetails.JobID = "+str(selectedJobId)+" AND "+engineTypeWhere+" ORDER BY "+order_column+" "+order_column_dir+" LIMIT "+str(start)+","+str(length)+""
        data_row = flib.db_query(sql)
        data = []
        for row in data_row:
            update_id_str = flib.getUpdateIdName(request, "(" + str(row[1]) + ")")
            data.append({'JobID': str(row[0]), 'UpdateID': str(update_id_str[0]['update_id_str']), 'FileState': str(row[2]), 'FileMD5': str(row[3]), 'FileSize': flib.getFileSize(int(row[4])), 'DefID': str(format(int(row[5]), '02X')), 'DefSize': flib.getFileSize(int(row[6])), 'FileName': str(row[7])})
        resp = {"draw": draw, "data": data, "recordsTotal":total_rows,"recordsFiltered":total_rows}
    return HttpResponse(json.dumps(resp), content_type='application/json')

def getSoloBuildDetailsDownload(request,jobId,updateId,updateIDArr,engineType,version):
    update_id_str = ''
    update_id_str = flib.getUpdateIdName(request, "(" + str(updateId) + ")")
    content = ''
    content += '<br/><div class="build-details" id="u_'+str(updateId)+'" ><div class="build-basic build-summary shadow-in detail-head "><h5>'+str(update_id_str[0]['update_id_str']) +'  <a href="/TableToCsv/?jobId='+str(jobId)+'&engineType='+str(engineType)+'&table=soloBuildDetails&updatetype='+str(updateId)+'" class="pull-right navbar-inverse shadow-in extractCSV" ><span class="glyphicon glyphicon-export"></span> </a> <a data-toggle="collapse" data-target="#soloBuildDetails'+str(updateId)+'Table" id="soloBuildDetails'+str(updateId)+'Target" class="pull-right navbar-inverse shadow-in historyBtn">Show Table</a></h5></div>';
    content += '<div id="build-basic-info"  class="build-basic detail-body">'
    content += '<table class="job-sum-tbl  shadow-in" >'
    content += '</table>'
    content += '<div class="row myrow" >'
    content += '<div class="subtblCol">'
    content += '<table class="subtbl">'
    content += '<tr><th class="subHead shadow-in"  rowspan="4">' + str(update_id_str[0]['update_id_str']) + '</th>'
    content += '<tr><th>Version</th><td>'+format(int(version), '02X')+'</td></tr>'
    content += '<th>Files</th><td>' + str(updateIDArr[int(updateId)][1]) + ' Files </td></tr>'
    content += '<tr><th>Total File size</th><td>'+  flib.getFileSize(updateIDArr[int(updateId)][2]) + '</td></tr>'
    content += '</table>'
    content += '</div>'
    content += '</div>'
    content += '<div class="clear"></div>'
    content += '</div>'
    content += '<div class="clear"></div></div><br/>'
    return content

@database_connection_check
def getSoloInfo(request,jobId,flag,JobStatus,updateIDArr,engineType):
    content = ''
    content += '<h4 data-toggle="collapse" data-target="#soloBuildDetailsDiv" id="solo-detail-head" class="shadow-in">Solo Details <i id="soloDetails" class="soloBuildDetailsDiv glyphicon glyphicon-minus pull-right"></i></h4>'
    content += '<div class="" id="soloBuildDetailsDiv" ><div  class="solo-build-details"> '
    sql = 'select UpdateID,count(*),sum(FileSize) from solodetails where JobID = ' + str(jobId) + ' group by UpdateID '
    solodetailsData = flib.db_query(sql)
    if not solodetailsData:
        return ''
    updateIDArr,onlyUpdateIDArr = {},[]
    for updateIDinSolo in solodetailsData:
        updateIDArr.update({updateIDinSolo[0]: updateIDinSolo})
    for updatetype in updateIDArr:
        onlyUpdateIDArr.append(updatetype)
    onlyUpdateIDArr = tuple(onlyUpdateIDArr)
    UpdateIdWiseVersion = flib.getJobVersion(jobId, onlyUpdateIDArr)
    cnt = 0
    if UpdateIdWiseVersion and UpdateIdWiseVersion is not None:
        for updatetype in updateIDArr:
            content += '<div id="soloSummary">'
            content += getSoloBuildDetailsDownload(request,jobId, str(updatetype),updateIDArr,engineType,UpdateIdWiseVersion[cnt])
            content += getSoloHtml(str(jobId),updatetype)
            content += '</div>'
            cnt += 1
    content += '</div></div>'
    return content

@database_connection_check
def getDiffInfo(request,jobId,flag,JobStatus,updateIDArr,engineType):
    content = ''
    content += '<h4 data-toggle="collapse" data-target="#buildDiffDetailsDiv" id="diff-detail-head" class="shadow-in">Differential Details <i class="buildDiffDetailsDiv glyphicon glyphicon-minus pull-right" ></i></h4>' \
               '<div class="" id="buildDiffDetailsDiv" ><div  class="diff-build-details">'
    sql = 'select UpdateID,count(*),sum(FileSize) from solodetails where JobID = ' + str(jobId) + ' group by UpdateID '
    solodetailsData = flib.db_query(sql)
    if not solodetailsData:
        return ''
    updateIDArr = {}
    for updateIDinSolo in solodetailsData:
        updateIDArr.update({updateIDinSolo[0]: updateIDinSolo})
    for updatetype in updateIDArr:
        content += '<div id="soloSummary">'
        content += getDiffBuildDetailsDownload(request,jobId, str(updatetype),updateIDArr,engineType)
        content += getDiffHtml(str(jobId),updatetype)
        content += '</div>'
    content += '</div></div>'
    return content

def getSoloHtml(jobId,updatetype):
    content = '<div class=-"collapse in soloBuildDetailsTable"  id="soloBuildDetails' + str(updatetype) + 'Table"><table id="soloBuildDetails' + str(updatetype) +'" class="soloBuildDetails display shadow-in" cellspacing="0" style="width:100%" ><thead class="detail-head"><tr><th>Def ID</th><th>Def Size</th>  <th>File State</th><th>File Size</th><th>File Name</th><th>File MD5</th></tr> </thead></table></div>'
    return content

def getDiffHtml(jobId,updatetype):
    content = '<div class=-"collapse in buildDiffDetailsTable"  id="buildDiffDetails'+str(updatetype)+'Table"><table id="buildDiffDetails' +str(updatetype)+ '" class="buildDiffDetails display shadow-in" cellspacing="0" style="width:100%" ><thead class="detail-head"><tr> <th>Patch File Name</th> <th>Patch File MD5</th> <th> Update min size</th><th>Previous Version</th><th>Current Version</th><th>File Count</th>  </tr></thead></table></div>'
    return content

@login_required(login_url='/login/')
@database_connection_check
def verify_job_jenkins(request,engine,flag):
    engineType = config.EngineTypeArr[engine]
    sql = 'select jobinfo.JobId, jobinfo.JobState from jobinfo where jobinfo.EngineType = '+str(config.EngineTypeArr[engine])+' and Flag = '+str(flag)+'  order by jobinfo.JobID desc limit 1'
    jobinfo_Data = flib.db_query(sql,1)
    if not jobinfo_Data:
        return HttpResponse(json.dumps({'status':0,'response':'No data found.'}), content_type='application/json')
    sql = 'select JobState,PercentDone,ROUND(time_to_sec((TIMEDIFF(NOW(),StartTime))) / 60)  from jobstatedetails where JobId  = '+str(jobinfo_Data[0])+' order by JobState desc limit 1'
    jobstatedetails_Data = flib.db_query(sql,1)
    if jobstatedetails_Data[2] < (config.JenkinsJobTimeOutMin):
        config.print_dstring('No need to go for verification'+str(jobstatedetails_Data[2]))
        return HttpResponse(json.dumps({'status':0,'response':'No data found.'}), content_type='application/json')
    sql = 'select round(time_to_sec(TIMEDIFF(Now(),LogTime)))/60 from progresslog where JobId=' + str(jobinfo_Data[0]) + ' order by LogTime desc limit 1'
    jobLogTime = flib.db_query(sql,1)
    if jobLogTime != None and  jobLogTime[0] < config.JenkinsJobTimeOutMin:
        config.print_dstring('There is some activity in progress log. Verificiation is skipped')
        return HttpResponse(json.dumps({'status':1, 'response': 'There is some activity in progress log. Verificiation is skipped'}), content_type='application/json')
    if jobinfo_Data[1] in config.jenkins_job[engineType][int(flag)] :
        if str(jobstatedetails_Data[1]) == str(100):
            if jobinfo_Data[1] in config.jobStepsNextJob[int(flag)]:
                if config.jobStepsNextJob[int(flag)][jobinfo_Data[1]] in config.jobStepsMannual[int(flag)]:
                    return HttpResponse(json.dumps({'status':0,'response':'Manual stage, validation not required'}), content_type='application/json')
                if flib.jenkinsJobStatus(config.jenkins_job[engineType][int(flag)][config.jobStepsNextJob[int(flag)][jobinfo_Data[1]]]) == False :
                    data = failJobProcess(engineType,'#E1: Job Failed by Automated Verfication(Jenkins Job was not started)',request.user.get_username())
                    if data['status'] ==  1:
                        return HttpResponse(json.dumps({'status':1,'response':'#E1: Job Failed by Automated Verfication(Jenkins Job was not started)'}), content_type='application/json')
                else:
                    return HttpResponse(json.dumps({'status':1,'response':'Verified Job #'+str(jobinfo_Data[0])+' is running/que(next job)'}), content_type='application/json')
            return HttpResponse(json.dumps({'status':0,'response':'Job is completed. Awaiting for User input.'}), content_type='application/json')
        else:
            if flib.jenkinsJobStatus(config.jenkins_job[engineType][int(flag)][jobinfo_Data[1]]) == False :
                return HttpResponse(json.dumps({'status':1,'response':'Verified Job #'+str(jobinfo_Data[0])+' is running/que'}), content_type='application/json')
            else:
                return HttpResponse(json.dumps({'status':0,'response':'Jenkins job is running !'}), content_type='application/json')
    else:
        if jobinfo_Data[1] in config.jobStepsMannual[int(flag)]:
            if str(jobstatedetails_Data[1]) == str(100):
                if jobinfo_Data[1] in config.jobStepsNextJob[int(flag)]:
                    if flib.jenkinsJobStatus(config.jenkins_job[engineType][int(flag)][config.jobStepsNextJob[int(flag)][jobinfo_Data[1]]]) == False :
                        data = failJobProcess(engineType,'#E1: Job Failed by Automated Verfication(Jenkins Job was not started)',request.user.get_username())
                        if data['status'] ==  1:
                            return HttpResponse(json.dumps({'status':1,'response':'#4 Job Failed by Automated Verfication(Jenkins Job was not started)'}), content_type='application/json')
            return HttpResponse(json.dumps({'status':0,'response':'Manual stage, no validation not required'}), content_type='application/json')
    return HttpResponse(json.dumps({'status':0}), content_type='application/json')

def currentJobDetails(pid):
    sql = "select UserName ,DateCreated , EngineType , Flag,JobState from jobinfo where jobinfo.JobID = %s" % (str(pid))
    jobInfo = flib.db_query(sql, 1)
    table_data = '<div id="active_job_details" class="details">'
    table_data += '<div><div class="active_job_div"><table class="active_job_table shadow-in">'
    table_data += '<tr><th> Engine Type </th><th>Created By</th><th>Job Type</th><th>Created Date</th></tr>'
    table_data += '<tr><td>' + str(config.EngineType[jobInfo[2]]) + '&nbsp;</td><td>' + jobInfo[0] + '&nbsp;</td><td>' + str(config.JobInfoFlag[jobInfo[3]]) + '&nbsp;</td><td>' + str(jobInfo[1]) + '&nbsp;</td></tr>'
    table_data += '</table></div></div>'
    table_data += '<h4>Job Steps</h4>'+flib.jobBoxesNotification(pid)
    return table_data

@database_connection_check
def jobSoloDiffDetailsDict(pid):
    sql = "select UpdateId,(sum(FileSize)) , count(FileMD5) from solodetails where solodetails.JobID =%s group by UpdateId order by UpdateId asc;" %(str(pid));
    soloDetails = flib.db_query(sql)
    if len(soloDetails) == 0:
        return ""
    soloDetailsDict = {}
    for soloDetail in soloDetails:
        soloDetailsDict.update({soloDetail[0]:{'File Size':flib.getFileSize(soloDetail[1]),'Total Files':soloDetail[2]}})
    sql = "select UpdateId,(sum(DiffSize)),count(*) as filecount from diffpatchdetails where JobID = %s group by FromVersion,UpdateId order by filecount asc,UpdateId asc limit 2; "%(str(pid))
    diffDetails = flib.db_query(sql)
    diffDetailsDict = {}
    for diffDetail in diffDetails:
        diffDetailsDict.update({diffDetail[0]: {'Min File Size': flib.getFileSize(diffDetail[1]), 'Min Files':diffDetail[2]}})
    table = jobSoloDiffDetails(soloDetailsDict,diffDetailsDict)
    return table

def jobSoloDiffDetails(solo,diff):
    table_solo_diff = '<div id=solo_diff_details class=details>'
    table_solo_diff += '<div class=solo_details><h4>Solo Details</h4><table class=solo_diff_table><tr><th>Update Id</th><th>File Size</th><th>Total Files</th><tr>'
    for key,values in solo.items():
        table_solo_diff += '<td>'+str(config.UpdateType[int(key)])+'</td>'
        for key, values in sorted(values.items()):
            table_solo_diff += '<td>'+str(values)+'</td>'
        table_solo_diff += '</tr>'
    table_solo_diff += '</tr></table></div>'
    table_solo_diff += '<div class=diff_details><h4>Differential Details </h4><table class=solo_diff_table><tr><th>Update Id</th><th>Diff Update Min Size</th><th>Min Files</th><tr>'
    for key, values in diff.items():
        table_solo_diff += '<td>' + str(config.UpdateType[int(key)]) + '</td>'
        for key, values in sorted(values.items()):
            table_solo_diff += '<td>' + str(values) + '</td>'
        table_solo_diff += '</tr>'
    table_solo_diff += '</tr></table></div>'
    table_solo_diff += '</div>'
    return table_solo_diff

@login_required(login_url='/login/')
@database_connection_check
@csrf_exempt
def check_current_status_ajax(request):
    try:
        sql = "SELECT * FROM jobinfo where JobState not in (6,7)  GROUP BY EngineType,JobId order by JobId desc limit 2"
        totalJobInfo =  flib.db_query(sql, 2)
        qhRunningDetails,e2RunningDetails,runningDetails,cnt = {},{},[],0
        for jobInfo in totalJobInfo:
            if jobInfo[1] != 6 and jobInfo[1] != 7 :
                if jobInfo[3] == 1:
                    qhRunningDetails.update({'id': jobInfo[0], 'processType': jobInfo[4], 'jobType': str(config.EngineType[jobInfo[3]])})
                else:
                    e2RunningDetails.update({'id': jobInfo[0], 'processType': jobInfo[4], 'jobType': str(config.EngineType[jobInfo[3]])})
            cnt = cnt + 1
        runningDetails = (qhRunningDetails, e2RunningDetails)
        return HttpResponse(json.dumps(runningDetails), content_type='application/json')
    except Exception as e:
        return HttpResponse(json.dumps(runningDetails), content_type='application/json')
        print('Error (Data not Found in Table)', e)

def getSuccessBuildInfo(type,limit = 10):
    sql = 'select JobId from jobinfo WHERE EngineType ='+str(type)+' and JobState = 6 order by JobID desc limit 0,'+str(limit)+''
    rowData = flib.db_query(sql)
    for Jobdetails in rowData:
        Jobdetails
    return Jobdetails

@login_required(login_url='/login/')
def current_job_details_ajax(request):
    return HttpResponse(json.dumps(currentJobDetails(request.POST['selectedJobId'])), content_type='application/json')

@login_required(login_url='/login/')
@database_connection_check
def revert_ajax(request,type):
    if not type in config.EngineTypeArr:
        return HttpResponse('Invalid request')
    if not request.is_ajax():
        return HttpResponseRedirect('/')
    content = ''
    jobRevertSteps = {1:'Start',2: 'Copying files for revert', 5: 'Revert Release Update', 6: 'Mark Release'}
    sql = "SELECT * FROM %s where EngineType = %s and Flag = 3  order by JobId desc   limit 0,1 " % ("jobinfo",str(config.EngineTypeArr[type]))
    data_row = flib.db_query(sql,1)
    if data_row == None:
        content += '<div class="selected-job">'
        content += '<div><p class="list-group-item list-group-item-info"><span class="glyphicon glyphicon-alert"></span>&nbsp; No Active Jobs.  </p></div>'
        content += '</div>'
        data = {'data': content, 'status': 1, 'mannual_step': 0,  'console_head': ''}
        return HttpResponse(json.dumps(data), content_type='application/json')
    sql = "SELECT JobState,TimeTaken,StartTime,PercentDone,JobID  FROM %s where JobID = %s order by JobState asc " % ("jobstatedetails", data_row[0])
    stateDetails = flib.db_query(sql)
    revrtJobInfo = {}
    CompletedJob = 1
    for state in stateDetails:
            revrtJobInfo.update({(state[0]): state})
    maxActive = max(revrtJobInfo)
    for job in revrtJobInfo:
        if job in revrtJobInfo[job]:
            if revrtJobInfo[job][3] == 100:
                CompletedJob += 1
    currentStageProgress = revrtJobInfo[maxActive][3]
    if maxActive == 5 and currentStageProgress == 100:
        mannual_step, nextStep = 6, 6
    elif maxActive == 1 and currentStageProgress == 100:
        mannual_step, nextStep = 0, 2
    else:
        status,mannual_step, nextStep = 1, 0,0
    status = 0
    if maxActive == 7 or maxActive == 6:
        status = 1
    jobId = data_row[0]
    if status == 0:
        content += '<table id="current-job-tbl" class="shadow-in" ><tr><th colspan="2" rowspan="2" >Active Job : #'+str(jobId)+'' \
                   '<br></th><th>Created By</th><th>Created On</th><th>Engine Type</th><th>Job Type</th><th>Reverted From</th></tr>  <tr><td>'+str(data_row[5])+'</td><td>'+str(data_row[2])+'</td><td>'+type.upper()+'</td><td>Reverted Job  </td> <td>'+str(flib.getRevertJobID(jobId))+'</td></tr></table></div><div class="clear"></div>'
        content += '<div class="progress shadow-in revertProgress">'
        if CompletedJob == 2:
            progresPer = (CompletedJob * 2)
        elif CompletedJob == 3:
            progresPer = (CompletedJob * 11)
        elif CompletedJob == 4:
            progresPer = (CompletedJob * 17)
        else:
            progresPer = (CompletedJob * 20)
        ajaxRunningJob = request.POST['running_job']
        if str(ajaxRunningJob) == str(1):
            content += '<div class="progress-bar active shadow-in progress-bar-success progress-bar-striped " role="progressbar" aria-valuenow="' + str(progresPer) + '" aria-valuemin="0" aria-valuemax="100"style="width: ' + str(progresPer) + '%;"> </div>'
        elif currentStageProgress == 0 and mannual_step == 0:
            progresPer = progresPer + 10
            content += '<div class="progress-bar active shadow-in progress-bar-success progress-bar-striped " role="progressbar" aria-valuenow="' + str(progresPer) + '" aria-valuemin="0" aria-valuemax="100"style="width: ' + str(progresPer) + '%;"> </div>'
        elif currentStageProgress == 100 and mannual_step == 0 and progresPer != 100 and CompletedJob != 2:
            progresPer = progresPer + 5
            content += '<div class="progress-bar active shadow-in progress-bar-success progress-bar-striped" role="progressbar" aria-valuenow="' + str(progresPer) + '" aria-valuemin="0" aria-valuemax="100"style="width: ' + str(progresPer) + '%;"> </div>'
        elif currentStageProgress == 100 and mannual_step == 0 and progresPer == 4:
            content += '<div class="progress-bar active shadow-in progress-bar-success progress-bar-striped" role="progressbar" aria-valuenow="' + str(progresPer) + '" aria-valuemin="0" aria-valuemax="100"style="width: ' + str(progresPer) + '%;"> </div>'
        else:
            content += '<div class="progress-bar active shadow-in progress-bar-success" role="progressbar" aria-valuenow="' + str(progresPer) + '" aria-valuemin="0" aria-valuemax="100"style="width: ' + str(progresPer) + '%;"> </div>'
        content += '</div>'
        content += '<div class="selected-job">'
        for jobStep in jobRevertSteps:
            if jobStep == 1:
                continue
            css_class,jobDtails,jobStatusMsg,jobStatusm,aniClass,jobStatus = '','','','','',''
            if jobStep in revrtJobInfo and revrtJobInfo[jobStep][3] == 100:
                jobStatus, jobStatusMsg = '', '&nbsp'
                aniClass = '<span class="glyphicon glyphicon-ok"></span>'
                css_class = 'success'
                jobDtails = ''
                jobDtails += '<p> Start Time : ' + format(revrtJobInfo[jobStep][2]) + '</p>'
                jobDtails += '<p>Time Taken : ' + str(flib.returnTimeString(revrtJobInfo[jobStep][1]*1000)) + '</p>'
                jobDtails += '<h6><p><b> Completed Successfully</b></p></h6>'
            elif nextStep == jobStep and currentStageProgress == 100 and mannual_step == 0:
                css_class = 'queue'
                jobDtails = ''
                if jobStep == 2:
                    startTime = format(revrtJobInfo[jobStep - 1][2])
                elif jobStep == 5:
                    startTime = format(revrtJobInfo[jobStep-3][2])
                else:
                    startTime = ''
                jobDtails += '<p> Start Time : ' + startTime + '</p>'
                jobDtails += '<h6><p> <b> Job is in queue</b></p></h6>'
                aniClass = '<span class="glyphicon glyphicon-hourglass spin"></span>'
            elif currentStageProgress != 100 and mannual_step == 0 and jobStep == maxActive:
                css_class = 'running'
                jobDtails = ''
                jobDtails += '<p>Start Time : ' + format(revrtJobInfo[jobStep][2]) + '</p>'
                jobDtails += '<h6><p> <b> Job is running</b></p></h6>'
                aniClass = '<span class="glyphicon glyphicon-refresh spin"></span>'
            elif jobStep == 6  and mannual_step == 6 :
                jobDtails = '<h6 class="generatemr"><br/><input type="button" class= "manualStep navbar-inverse shadow-in" value="Continue" id="LastStepBtn" onclick="create_job_process(' + str(jobStep) + ','+str(jobId)+');"/></h6>'
            elif (nextStep == job and ajaxRunningJob == str(1)):
                css_class = 'running_ajax'
                jobDtails = ''
                jobDtails += 'Updating Database..'
                aniClass = '<span class="glyphicon glyphicon-repeat spin"></span>'
            elif maxActive == 7:
                css_class = 'failedJob'
                jobDtails += '<h6><p><b>Job is Failed</b></p></h6>'
            content += '<div class="shadow-in revert-job-step ' + css_class + ' '+jobStatus+' ">'
            content += '<h5>' + jobRevertSteps[jobStep] + '<span class="aniClass">'+aniClass+'</span> </h5>'
            content += jobDtails
            content += '</div>'
            if jobStep != 6 :
                content += '<div class=selected-revert-job-seprator><span class="glyphicon glyphicon-menu-right"></span></div>'
        content += '</div>'
        progLogData = flib.progLog(jobId, data_row, config.jobSteps[3][job], request.POST['progress_log'])
        data = {'data': content, 'status': 1, 'mannual_step': mannual_step,
                'pconsole_text': progLogData['pconsole_text'], 'nexProgLogId': progLogData['nexProgLogId'],
                'console_head': progLogData['console_head'],'activeStep':progLogData['activeStep'],'JobId':progLogData['JobId']}  # create json array to response json
        return HttpResponse(json.dumps(data), content_type='application/json')
    else:
            jobStep = data_row[1]
            ajaxRunningJob = str(request.POST['running_job'])
            if str(ajaxRunningJob) == str(1) and jobStep != 6 :
                content += '<div><p class="success-msg list-group-item list-group-item-success"><span class="glyphicon glyphicon-check"></span>&nbsp;Your request is processing. Please wait while we are creating new job...  !</p></div>'
            else:
                content += '<br/><div><p class="list-group-item list-group-item-info"><span class="glyphicon glyphicon-alert"></span>&nbsp; No Active Revert Jobs. Please go back and start a new job to continue !</p></div>'
                content += flib.jobBoxes(type, 3, jobId, 1)
    data = {'data':content,'status':1,'mannual_step':mannual_step,'pconsole_text':'','nexProgLogId':'','console_head':''}  # create json array to response json
    return HttpResponse(json.dumps(data), content_type='application/json')

@login_required(login_url='/login/')
@database_connection_check
@jenkins_check
def jenkins_log(request,job):
    jobId = str(job);
    data = flib.db_query('SELECT JobID, JobState,EngineType, Flag, UserName,DateCreated from jobinfo WHERE JobID = '+str(jobId),1)
    output = '<div id="active_job_details" class="details">'
    output += '<div><div class="active_job_div"><table class="active_job_table shadow-in">'
    output += '<tr><th> JobID </th><th> Engine Type </th><th>Created By</th><th>Job Type</th><th>Created Date</th></tr>'
    output += '<tr><td>'+str(job)+'</td><td>' + str(config.EngineType[data[2]]) + '&nbsp;</td><td>' + data[4] + '&nbsp;</td><td>' + str(config.JobInfoFlag[data[3]]) + '&nbsp;</td><td>' + str(data[5]) + '&nbsp;</td></tr>'
    output += '</table></div></div>'
    output += flib.jobBoxes(config.EngineType[data[2]].lower(),data[3],jobId)
    output += '<div class="clear paddingTop10px"></div>'
    sql = 'select JobID, JenkinsJobName, BuildID, Node, DateCreated from jobinfojenkins where JobID = '+str(jobId)+' limit 6'
    dataJenkins = flib.db_query(sql)
    if len(dataJenkins) == 0:
        output += '<div class="clear paddingTop10px"></div>'
        output += '<p><pre class="shadow-in">No data found.</pre></p>'
        output += '<div class="clear paddingTop10px"></div>'
    else :
        menu_output = '<ul id=floating_menu class="nav navbar-nav shadow-in"><li class="heading" >Jenkins Jobs <span class="glyphicon glyphicon-remove" ></span> </li>'
        for jItem in dataJenkins:
            output += '<div  class="clear paddingTop10px"></div>'
            output += '<div  id="active_job_details" class="details">'
            output += '<div id='+str(jItem[1])+' ><div  class="active_job_div"><table class="active_job_table shadow-in">'
            output += '<tr><th> JobID </th><th> Jenkins Job Name </th><th>Jenkins BuildID</th><th>Node</th><th>TimeStamp</th></tr>'
            output += '<tr><td>' + jobId + '&nbsp;</td><td>'+jItem[1]+' </td><td>' + str(jItem[2]) + '&nbsp;</td><td>' + str(jItem[3]) + '&nbsp;</td><td>' + format(jItem[4]) + '&nbsp;</td></tr>'
            output += '</table></div></div>'
            output += '<div class="clear paddingTop10px"></div>'
            output += "<pre class='shadow-in'>"+getJenkinsBuildLog(jItem[1],jItem[2])+"</pre>"
            menu_output += '<li><a href="#'+str(jItem[1])+'">'+str(jItem[1])+'</a>'
        menu_output += '</ul>'
        output += menu_output
    flib.setMetaInformation(request,'Log for Job #'+str(jobId),OrderedDict([('Log for Job #'+str(jobId)+'','')]))
    return render(request, "build/jenkins_log.html",{'content':output})

def getJenkinsBuildLog(jobName,buildId):
    if buildId:
        try:
            url =  settings.JENKINS_URL+"/job/"+jobName+"/"+str(buildId)+"/consoleText"
            resp = requests.post(url, auth=(settings.JENKINS_USER, settings.JENKINS_PASS),verify=True)
            return resp.text
        except Exception as e:
            print('Error (getJenkinsBuildLog)',e)
    else:
        return 'No Data'

@login_required(login_url='/login/')
@database_connection_check
def getTableToCsv(request):
    response = HttpResponse(content_type='text/csv')
    time = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
    jobId, tableType, updatetype,update_id_str = '', '', '',''
    if request.method == 'GET' and 'jobId' in request.GET and 'table' in request.GET and 'updatetype' in request.GET:
        if request.GET['table'] and request.GET['updatetype'] :
            jobId =  request.GET['jobId']
            engineType =  request.GET['engineType']
            tableType = request.GET['table']
            updatetype = request.GET['updatetype']
            update_id_str = flib.getUpdateIdName(request, "("+str(updatetype)+")")
        if (tableType == 'soloBuildDetails'):
            engineTypeWhere = ''
            engineTypeWhere += "(solodetails.UpdateID = " + str(engineType[0]) + " AND deffileinfo.UpdateID = " + str(engineType[0]) + ")"
            sql = "SELECT solodetails.*, deffileinfo.FileName FROM solodetails  LEFT JOIN deffileinfo ON deffileinfo.DefID = solodetails.DefID and solodetails.UpdateID = deffileinfo.UpdateID WHERE solodetails.DefID = deffileinfo.DefID AND solodetails.JobID = " +jobId+ " AND solodetails.UpdateID =  "+updatetype+" ORDER BY solodetails.DefID DESC"
            data_row = flib.db_query(sql)
            count = len(data_row)
            response['Content-Disposition'] = 'attachment; filename="'+str(jobId)+'_'+str(engineType)+'_'+str(tableType)+'_'+str(update_id_str[0]['update_id_str'])+'_('+str(count)+')_records_'+time+'.csv"'
            writer = csv.writer(response)
            writer.writerow( ['Def ID', 'Def Size', 'File State', 'File Size', 'File Name', 'File MD5'])
            for row in data_row:
                writer.writerow([str(row[5]),flib.getFileSize(int(row[6])),str(row[2]),flib.getFileSize(int(row[4])),str(row[7]), str(row[3])])
            return response
        else:
            sql = "select JobID,UpdateID,PatchFileName,PatchFileMD5,PatchFileSize,FromVersion, Version from diffdetails WHERE JobID = " + str(jobId)+ " and UpdateID = " +str(updatetype)  + "  order by PatchFileName desc"
            data_row = flib.db_query(sql)
            content = '<table id="' + str(tableType) + '" ><thead class="detail-head"><tr><th>PatchFileName</th><th>PatchFileMD5</th>  <th>PatchFileSize</th><th>FromVersion</th><th>Version</th></tr> </thead><tbody class="detail-body">'
            count = len(data_row)
            response['Content-Disposition'] = 'attachment; filename="' + str(jobId) + '_' + str(engineType) + '_'+str(tableType)+'_' + str(update_id_str[0]['update_id_str']) + '_(' + str(count) + ')_records_' + time + '.csv"'
            writer = csv.writer(response)
            writer.writerow(['PatchFileName', 'PatchFileMD5', 'PatchFileSize', 'PreviousVersion', 'CurrentVersion', ])
            for row in data_row:
                writer.writerow([str(row[2]),str(row[3]), flib.getFileSize(int(row[4])),  str(row[6]),str(row[5])])
            return response
    else:
        return render(request, "/", context_instance=RequestContext(request))

def jenkinsJobProcess(request,jobName,paramArr):
    try:
        import jenkins
        server = jenkins.Jenkins(config.jenkins_url, username=config.jenkins_username, password=config.jenkins_password)
        server.build_job(jobName,paramArr)
    except Exception as e:
        print('Error (jenkinsJobProcess)',e)
        fail_job(request,'e2','Jenkins Error :'+str(e))