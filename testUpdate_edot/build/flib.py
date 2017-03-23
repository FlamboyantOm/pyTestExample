import json,requests
from django.conf import settings
from build_manage import const
from jenkinsapi.jenkins import Jenkins
from . import config,statistics
import time,datetime
from django.http import HttpResponseRedirect
from script import get_releaseable_pkg

from django.contrib.auth.decorators import login_required,user_passes_test
from configparser import ConfigParser

def get_server_instance():
    try:
        server = Jenkins(config.jenkins_url, username=config.jenkins_username, password=config.jenkins_password)
    except:
        return
    return server

def returnTimeString(miliSec=0):
     if miliSec == None or miliSec == '' :
         return 0
     s, ms = divmod(int(miliSec),1000)
     m, s = divmod(s, 60)
     h, m = divmod(m, 60)
     returnVal = "%d:%02d:%02d" % (h, m, s)
     if returnVal == '0:00:00':
         returnVal = 'N/A'
     return returnVal

def returnTimeStringSec(sec=0):
     if sec == None or sec == '' :
         return 0
     m, s = divmod(int(sec), 60)
     h, m = divmod(m, 60)
     returnVal = "%d:%02d:%02d" % (h, m, s)
     if returnVal == '0:00:00':
         returnVal = 'N/A'
     return returnVal

def returnTimeStringOnly(miliSec):
    try:
        returnVal = "%d" % (  ((miliSec / 1000) / 60) )
        if returnVal == '0':
            returnVal = 'N/A'
        return returnVal
    except Exception as e:
        print('Error(returnTimeStringOnly): ', e)

def getFileSize(fileSizeInBytes=0):
    try:
        if  fileSizeInBytes == 0:
            return str('-')
        if fileSizeInBytes is None:
            return str('None')
        fileInKb = int(fileSizeInBytes/1024)
        if fileInKb == 0:
            return str(fileSizeInBytes)+' Bytes'
        fileInMb = format(fileInKb/1024,'.2f')
        finalResult  = str(fileInMb) + ' MB'
        return str(finalResult)
    except Exception as e:
        print('Error(getFileSize): ', e)

def getFileSizeKbMb(fileSizeInBytes=0):
    if fileSizeInBytes == 0:
        return str('0 Bytes')
    if fileSizeInBytes is None:
        return str('None')
    fileInKb = int(fileSizeInBytes/ 1024)
    if fileInKb == 0:
        return format(fileSizeInBytes, '.0f') + ' Bytes'
    fileInMb = format(fileInKb / 1024, '.2f')
    finalResult = str(fileInMb) + " MB (" + str(fileInKb) + " KB)"
    return str(finalResult)

def getFileSizeKb(fileSizeInBytes=0):
    if fileSizeInBytes == 0:
        return str('0')
    if fileSizeInBytes is None:
        return str('-1')
    finalResult = '{0:.2f} KB'.format(float(fileSizeInBytes)/float(1024))
    return str(finalResult)

def getFileSizeMb(fileSizeInBytes=0):
    if  fileSizeInBytes == 0:
        return str('0')
    if fileSizeInBytes is None:
        return str('-1')
    finalResult = '{0:.2f} MB'.format(float(format(float(fileSizeInBytes) / float(1024)) )/ float(1024))
    return str(finalResult)

def getPercentChange(value=0,outOf=100,flag = ''):
    if value > outOf :
        if flag:
            return ' Increased by  <b>' + format(((value / outOf) * 100) - 100, '.2f') + '%' + '</b> ( <b>' + format(outOf / value,'.2f') + '</b> times increased ) '
        return '<span class="glyphicon glyphicon-triangle-top error"></span> Increased by  <b>'+format(((value/outOf)*100)-100,'.2f')+'%'+'</b> ( <b>'+format(outOf/value,'.2f')+'</b> times increased ) '
    else:
        if flag:
            return 'Reduce by <b>' + format(100 - (value / outOf) * 100, '.2f') + '%' + '</b> ( <b>' + format(outOf / value,'.2f') + '</b> times reduced ) '
        return '<span class="success glyphicon glyphicon-triangle-bottom "></span> Reduce by <b>'+format(100-(value/outOf)*100,'.2f')+'%'+'</b> ( <b>'+format(outOf/value,'.2f')+'</b> times reduced ) '

def get_user_permissions(user):
    userAccess = {}
    for group in user.groups.all():
        params = group.permissions.all()
        paramArr =[]
        for param in params:
            if param.codename in config.permissions[str(group)]:
                paramArr.append(config.permissions[str(group)][param.codename])
        paramArr = sorted(paramArr, key=lambda k: k['order'])
        userAccess.update({str(group): paramArr})
    return userAccess

def progLog(jobId=0,data=0,activeStep=0,progress_offset=0):
    try :
        if not jobId:
            return {'nexProgLogId':0,'pconsole_text':'','console_head':'','activeStep':'','JobId':''}
        nexProgLogId,pconsole_text = 0,''
        if progress_offset == 0:
            psql = 'select ProgressId,Msg,LogTime,UpdateId from progresslog where JobID ="'+str(jobId)+'" order by ProgressId desc limit 1000'
        else:
            psql = 'select ProgressId,Msg,LogTime,UpdateId from progresslog where JobID ="'+str(jobId)+'" and ProgressId > '+str(progress_offset)+' order by ProgressId desc limit 1000'
        consolepLogData = db_query(psql)
        if consolepLogData is None:
            return {'nexProgLogId':0,'pconsole_text':'','console_head':'','activeStep':'','JobId':''}
        console_head = "<p class='console-heading' >Progress Log for Job #"+str(jobId)+" | Job Start Time : "+format(data[2])+" |  Active Step : "+activeStep+"  </p>"
        if activeStep:
            activeStep = ' - ' +activeStep
        else:
            activeStep = ''

        if str(progress_offset) == str(0):
            for plog in consolepLogData:
                if nexProgLogId < plog[0]:
                    nexProgLogId = plog[0]
                pconsole_text += '<p>['+format(plog[2])+'] '+str(plog[1])+'</p>'
        elif len(consolepLogData) == 0:
            pconsole_text = ''
            nexProgLogId = progress_offset
        else:
            for plog in consolepLogData:
                if nexProgLogId < plog[0]:
                    nexProgLogId = plog[0]
            pconsole_text += '<p>['+format(plog[2])+'] '+str(plog[1])+'</p>'
        return {'nexProgLogId':nexProgLogId,'pconsole_text':pconsole_text,'console_head':console_head,'activeStep':activeStep,'JobId':str(jobId)}
    except Exception as e:
        print("Error (progLog) : ",e)

def previousBuildHtml(engine,buildtype,offset=0,builds = 5,request=''):
    engineType = config.EngineTypeArr[engine]
    if request.POST['checkedValue'] == '':
        checkValArr = ['1','2','3','6']
    else:
        checkValArr = request.POST['checkedValue'].split(',')
    failCase = [1,2,3]
    sqlArr = []
    if str(6) in checkValArr :
        sqlArr.append('(select releaseinfo.JobID as JobID, jobinfo.DateCreated, jobinfo.JobState, jobinfo.UserName, "6" as type, releaseinfo.Notes AS Note, releaseinfo.VDB  from releaseinfo left join jobinfo on releaseinfo.JobID = jobinfo.JobID where jobinfo.EngineType = '+str(engineType)+' and jobinfo.Flag = '+str(buildtype)+' order by jobinfo.JobID desc limit 15)')
    failItemActual = ''
    for failItem in failCase:
        if str(failItem)  in checkValArr:
            failItemActual += str(failItem)+","
    if failItemActual != '':
        failItemActual = failItemActual[:-1]
        sqlArr.append('(select failedjobinfo.JobID as JobID, jobinfo.DateCreated, jobinfo.JobState, jobinfo.UserName,failedjobinfo.FailedReason as type,  failedjobinfo.Notes, "-" as VDB from failedjobinfo left join jobinfo on failedjobinfo.JobID = jobinfo.JobID where failedjobinfo.FailedReason in ('+failItemActual+') and jobinfo.EngineType = '+str(engineType)+' and jobinfo.Flag = '+str(buildtype)+' order by jobinfo.JobID desc limit 15)')
    cnt,sql = 1,''
    for i in sqlArr:
        sql += i
        if cnt != len(sqlArr):
            sql += ' UNION  '
            cnt = cnt+1
    finalSql = 'SELECT unitbl.*,jd.TimeTaken,TIMESTAMPDIFF(SECOND,unitbl.datecreated,jdmax.StartTime) as totaltime from ('+sql+') as unitbl, (select JobID, sum(TimeTaken) as TimeTaken from jobstatedetails group by JobID ) as jd, (SELECT JobID, JobState,StartTime as StartTime  FROM   jobstatedetails where  jobstatedetails.jobstate in (6,7)  )   AS jdmax where  (unitbl.jobid = jd.jobid and unitbl.jobid = jdmax.jobid)  order by  unitbl.JobID  desc limit 15'
    data_row = db_query(finalSql)
    content = ''
    status = 'Status'
    if data_row:
        content += '<style>.previous-build td{min-height:10%;}</style><table class="previous-build shadow-in" style="width:100%;"><tr><th>Job Id</th><th>Created Date</th><th>'+status+'</th><th>Created By</th><th>Note</th><th>VDB</th><th>Total Script Time</th><th>Actual Time</th><th>Log</th></tr>'
        for data in data_row:
            Notes =  str(data[5])
            if len(str(data[5])) >25 :
                Notes = str(data[5])[:25]+'...'
            content += '<tr><td>'+str(data[0])+'</td><td>'+format(data[1])+'</td><td>'+config.JobFailedReason[int(data[4])]+'</td><td>'+str(data[3])+'</td><td>'+Notes+'</td><td>'+format(data[6])+'</td><td>'+returnTimeString(data[7]*1000)+'</td><td>'+returnTimeString(data[8]*1000)+'  </td><td><a target="_blank" href="/jenkins-log/'+str(str(data[0]))+'">View Log</a></td></tr>'
    else:
        content += '<p>No Records found</p>'
    content += '</table>'
    if len(data_row) == 0:
        return content, 1
    if data_row[0][0]:
        return content,data_row[0][0]
    else:
        return content,1

def jobBoxes(jobData,jobStages,jobId,previousJob=0):
    content = ''
    jobInfo = {}
    for jobstep in jobStages:
            if (jobstep[0]) != 7 :
                jobInfo.update({(jobstep[0]):jobstep})
    content += '<div class="prev-job">'
    isCompleted  = 0
    if jobData[1] in [6,7]:
        isCompleted = 1
    if jobStages[len(jobStages)-1][0] ==  7:
        isCompleted = 7
        failedStep = jobStages[len(jobStages)-2][0]
        if jobStages[len(jobStages)-2][3] == 100:
            failedStep = failedStep +1
    if str(previousJob)== str(1):
        job_status = ' | Started Time : '+format(jobData[2])+ ' | Created by : '+jobData[5]
        if jobData[1] == 6 :
            isCompleted = 6
            job_status += ' | Status : Completed <span class="glyphicon glyphicon-ok-sign"></span>'
        elif jobData[1] == 7 :
            job_status += ' | Status : Failed <span class="glyphicon glyphicon-remove-sign"></span>'
        content += '<h4>Previous Job : #'+str(jobId)+'  '+job_status+' </h4>'
    jobSteps = config.jobSteps[jobData[4]]
    for jobStep in jobSteps:
        if jobStep == 1:
            continue
        if jobStep in jobInfo:
            css_class = 'success'
            otherDtl = '<p>Start Time : '+format(jobInfo[jobStep][2])+'</p>'
            otherDtl += '<p>Time Taken : '+str(returnTimeString(jobInfo[jobStep][1]*1000))+'</p>'
            if jobInfo[jobStep][3] == 100 :
                otherDtl += '<p>Status : Completed </p>'
            else:
                if isCompleted == 7:
                    css_class = 'failed'
                    reasonForFail = db_query('select  FailedReason  from failedjobinfo where JobID = ' + str(jobId) + " limit 1", 1)
                    otherDtl = '<p>Status : '+str(config.JobFailedReason[reasonForFail[0]])+'  </p>'
                else :
                    otherDtl = '<p>Status : Running </p>'
        else:

            if isCompleted == 7 and failedStep == jobStep:
                css_class = 'failed'
                reasonForFail = db_query('select  FailedReason  from failedjobinfo where JobID = ' + str(jobId) + " limit 1", 1)
                otherDtl = '<p>Status : '+str(config.JobFailedReason[reasonForFail[0]])+'  </p>'
            else:
                css_class = 'not-completed'
                otherDtl = '<p>Status : Not Performed </p>'
        content += '<div class=" shadow-in job-step '+css_class+'  ">'
        content += '<h5>'+str(jobSteps[jobStep])+'</h5>'
        if otherDtl != '':
            content += otherDtl
        content += '</div>'
        if jobStep != 6:
            content += '<div class=prev-job-seprator><span class="glyphicon glyphicon-menu-right"></span></div>'
    content += '</div>'
    return content

def jobBoxesNotification(jobId,activeStage=0):
    sql = "SELECT * FROM jobinfo where JobID = "+str(jobId)
    jobData = db_query(sql,1)
    if not jobData:
        return ''
    sql = "SELECT JobState,TimeTaken,StartTime,PercentDone,JobID  FROM jobstatedetails where JobID = "+str(jobId)+" order by JobState asc "
    box_count=0
    jobStages = db_query(sql)
    if not jobStages:
        return ''
    content = ''
    jobInfo = {}
    for jobstep in jobStages:
            box_count += 1
            if (jobstep[0]) != 7 :
                jobInfo.update({(jobstep[0]):jobstep})
    content += '<div class=popmsg-stage>'
    jobSteps = config.jobSteps[jobData[4]]
    cnt = 1
    for jobStep in jobSteps:
        if jobStep == 1:
            continue
        cnt = cnt + 1
        if jobStep in jobInfo:
            css_class = 'success'
            otherDtl = '<p>Time  : '+str(returnTimeString(jobInfo[jobStep][1]*1000))+'</p>'
            otherDtl += '<p>Status : Completed </p>'
        else:
            css_class = ''
            otherDtl = '<p>Status : Not Performed </p>'
        content += '<div class= '+css_class+' >'
        content += '<h5>'+str(jobSteps[jobStep])+'</h5>'
        if otherDtl != '':
            content += otherDtl
        content += '</div>'
    content += '</div>'
    return content

def setMetaInformation(request,name,breadcrumb={''}):
    try :
        setattr(request, 'title',name)
        setattr(request, 'meta_title',name+' - '+config.WEBSITE_TITLE)
        setattr(request, 'logo_heading',config.WEBSITE_TITLE)
        setattr(request, 'config',config.TemplateValues)

        if not breadcrumb:
            setattr(request, 'breadcrumb','')
        else:
            setattr(request, 'breadcrumb',breadcrumb)
    except Exception as e:
        print('Error (setMetaInformation)',e)
        pass

@user_passes_test(lambda u: u.groups.filter(name='ViewAndWrite'), login_url='/')
def jenkinsJobStatus(jobName='',cnt=5,status=False):
    if cnt == 0 :
        return status
    else:
        cnt = cnt - 1
        time.sleep(5)
    print('FLib::jenkinsJobStatus Verification cnt:'+str(cnt))
    if jobName == '':
        print('jenkinsJobStatus: Job name is not there. Returning False. Attemp : ',str(cnt))
        return jenkinsJobStatus(jobName,cnt,False)
    resp = requests.post(config.jenkins_url+'/job/'+str(jobName)+'/api/json?tree=inQueue,lastBuild[number]', auth=(config.jenkins_username,config.jenkins_password),verify=False)
    json_data = json.loads(resp.text)
    lastBuild  = json_data['lastBuild']['number']
    inQueue = json_data['inQueue']
    if inQueue == True:
        print('jenkinsJobStatus: Build is in que.',cnt)
        return True
    elif inQueue == False :
        resp = requests.post(config.jenkins_url+'/job/'+str(jobName)+'/'+str(lastBuild)+'/api/json?tree=building', auth=(config.jenkins_username,config.jenkins_password),verify=False)
        jsonDataLastBuild = json.loads(resp.text)
        building = jsonDataLastBuild['building']
        if building == True:
            print('jenkinsJobStatus: Job is building in jenkins',cnt)
            return True
        else:
            print('jenkinsJobStatus: Job is not building. Makring fail cnt :',cnt)

            print('Response Text',resp.text)
            print('Response headers',resp.headers)
            print('Response status_code',resp.status_code)
            return jenkinsJobStatus(jobName,cnt,False)
    print('jenkinsJobStatus:  :Job is not in que and not building so its returning false',str(cnt))
    print('Response Text',resp.text)
    print('Response headers',resp.headers)
    print('Response status_code',resp.status_code)
    return jenkinsJobStatus(jobName,cnt,False)

import inspect
def db_query(sql,rows = 0):
    try :
        #print('test : Inspect Function : ',inspect.stack()[1][3])
        dbobj = config.MyDB()
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
         dbobj = config.MyDB()
         return dbobj.insert(sql,type)
    except Exception as e:
        print('Error (db_insert) Sql ',sql,' Error ',e)

def getJobVersion(jobID,onlyUpdateIDArr):
    rowdata = db_query('select Version from downloaddetails where JobID = '+str(jobID)+' and UpdateID = '+str(onlyUpdateIDArr)+' order by UpdateID')
    if rowdata == None:
        return ''
    updateIdArr = []
    for row in rowdata:
        updateIdArr.append(row[0])
    return tuple(updateIdArr)
def checkJenkinsServer():
    jenkings_server = get_server_instance();
    if jenkings_server is None:
        return False
    else:
        return True

def jenkins_check(function=None):
    def _dec(view_func):
        def jenkins_view(request, *args, **kwargs):
            if checkJenkinsServer():
                return view_func(request, *args, **kwargs)
            else:
                config.print_dstring('Unable to connect to jenkins server. So redicrecting to errorpage')
                return HttpResponseRedirect('/error/?type=2')
        return jenkins_view
    if function is None:
        return _dec
    else:
        return _dec(function)

def database_connection_check(function):
    def _decorator(fun):
        def database_view(request, *args, **kwargs):
                return fun(request, *args, **kwargs)
        return database_view
    if function is None:
        return _decorator
    else:
        return _decorator(function)

def fileAutoTest(jobID):
    handle = open(settings.AUTOMATION_FILE_PATH, 'r+')
    lists = handle.read().split("\n")
    for string in lists:
        key = string.split(",")
        from datetime import datetime
        format = "%Y-%m-%d %H-%M-%S"
        datetime = datetime.strptime(key[1], format)
        if jobID == int(key[0]):
            datetime
            break
    return datetime

def automate_proccessing(request,data):
    try:
        if settings.AUTOMATION_FLAG:
            if request.user.get_username() != settings.AUTOMATION_USER:
                return
            from .pipeline_view import create_job
            if data[1] in [6, 7]:
                create_job(request, 'e2', 1, 2)
            elif data[1] == 3:
                sql = "SELECT JobState, PercentDone, JobID  FROM %s where JobID = %s order by JobState desc limit 1 " % (
                "jobstatedetails", data[0])
                data_jobState = db_query(sql)
                if data_jobState[0][0] == 3 and data_jobState[0][1] == 100:
                    create_job(request, 'e2', 2, 1)
            elif data[1] == 5:
                sql = "SELECT JobState, PercentDone, JobID  FROM %s where JobID = %s order by JobState desc limit 1 " % (
                "jobstatedetails", data[0])
                data_jobState = db_query(sql)
                if data_jobState[0][0] == 5 and data_jobState[0][1] == 100:
                    if str(fileAutoTest(data[0])):
                        create_job(request, 'e2', 3,
                                   {'VDB': str(fileAutoTest(data[0])), 'NOTES': "Automated Script Verified"})
                    else:
                        return create_job(request, 'e2', 3, 0)
    except Exception as e:
        print('Error :', e)
        return 0

def getRevertJobID(jobId):
    sql = 'Select jobproperty.Value from jobproperty Where jobproperty.JobID = "'+str(jobId)+'" and Name = \'REVERTED_FROM\' limit 1'
    jobProperty = db_query(sql,0)
    if len(jobProperty) == 1:
        return jobProperty[0][0]
    else:
        return ''

def getPackegeList():
    print(get_releaseable_pkg.RetrieveToBeReleasePkgList(),'__________________________')
    return
    html,eachPckLimit,packagelinkArr = '',512,''
    status, packagelistname, packagelist ,urls  = get_releaseable_pkg.RetrieveToBeReleasePkgList()

    packageList = dict(zip(packagelist,packagelistname))
    packageListUrl = dict(zip(packagelist,urls))
    if status is not None:
        if str(status) == str(1):
            html += '<div class="alert alert-danger"> Error in release package file. </div>'
        elif str(status) == str(2):
            html += '<div class="alert alert-warning"> No release package found. </div>'
            print('package script 1 ',status, packagelistname, packagelist)
        elif packagelist is not None:
            html += '<table class=lastStepTbl id="packagebox"><tr><td><h4>Select Package :</h4><p><label><input type="checkbox" id="checkAll" name="checkAll" onclick="checkAllids(this);" checked> Check All</lable></p></td><td>'
            for packege_item in packageList:
                html += '<label><input class="packageListCheck"   type="checkbox"  value="' + str(packege_item).strip() + '" checked> &nbsp;' + str(packageList[packege_item]) + '  <a href="'+str(packageListUrl[packege_item]).strip()+'"  target="_blank"  > View </a> </label>'
            html += '</td><tr/></table>'
    else:
        print('package script 2 ',status, packagelistname, packagelist)
        html += '<div class="alert alert-danger">Error in release package file. </div>'
    return html

def getUpdateTypeList(type=1,selectedFilter=''):
    fileTypeArr =  const.QH_SIG_TYPE_LIST
    fileTypeSelect = '<span class="sigTypespan"><select id="SigTypeSelect" multiple="multiple">'
    for value in fileTypeArr:
        fileTypeSelect += '<option value="' + str(value) + '">' + str(value.upper()) + '</option>'
    fileTypeSelect += '</select></span>'
    fileTypeSelect += '<script>jQuery("span.sigTypespan select").multipleSelect({ placeholder: "-- Select Sig Type --"});</script>'
    return fileTypeSelect

import random,string
def id_generator(size=15, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
def geturls(num=10):
    urls = ''
    for item in range(num):
        urls += "http://"+id_generator(10,'abcdefghihlklnopqrstuvwzy')+".com/"+id_generator(10,'abcdefghihlklnopqrstuvwzy ')+".zip, "
    urls = urls.strip().replace(' ','')
    print('sent',urls)
    return urls[:-1]

def statRequest(request,type):
    try:
        data = {}
        if 'from' in request.GET :
            data['from_date'] = request.GET['from']
        else :
            lastMonth = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
            data['from_date'] = lastMonth.strftime("%Y-%m") + '-' + str(datetime.datetime.now().day)
        if 'to' in request.GET :
            data['to_date'] = request.GET['to']
        else :
            data['to_date'] = datetime.datetime.now().strftime("%Y-%m-%d")
        if 'u' in request.GET:
            data['update_id'] = request.GET['u']
        else:
            if type == 'e2':
                data['update_id'] = 4
            else:
                data['update_id'] = 779
        return data
    except Exception as e:
        print('Error (getQhStatdata)', e)

@user_passes_test(lambda u: u.groups.filter(name='ViewAndWrite'), login_url='/')
def markBuildEngine(request,data,mark=1,notes=''):
    user = request.user
    if str(mark) == str(1):
        sql = 'SELECT UpdateID,EngineType from updateidinfo'
        UpdateIDArr = dict(db_query(sql))
        for item in data:
            updateType= int(item)
            sql = "SELECT releaseinfo.JobID from releaseinfo join enginemaster on enginemaster.JobID =  releaseinfo.JobID and enginemaster.UpdateID = '"+str(item)+"' order by releaseinfo.VDB desc limit "+str(int(const.CUSTOM_JOBS_LIMIT)+int(config.LimitToVerifyUpdateIDByType[UpdateIDArr[int(item)]][int(updateType)]))
            latestUpdateIds = db_query(sql)
            if len(latestUpdateIds) == 0:
                return 0
            elif(len(list( filter(lambda x:str(x[0]) ==str(data[item]),latestUpdateIds))) != 1):
                return  0

    try :
        for item in data.items():
            count = db_query('SELECT COUNT(UpdateID) FROM buildinfo WHERE buildinfo.UpdateID = "'+str(item[0])+'" AND buildinfo.JobID = "'+str(item[1])+'"',1)
            if count[0] > 0:
                if str(mark) == str(1):
                    sql = 'UPDATE buildinfo SET buildinfo.IsBuildEngine = 1,DateAdded = CURRENT_TIMESTAMP, AddedBy = "'+str(user)+'",`Notes`= "'+str(notes)+'"    WHERE buildinfo.UpdateID = "'+str(item[0])+'" AND buildinfo.JobID = "'+str(item[1])+'"'
                else :
                    sql = 'UPDATE buildinfo SET buildinfo.IsBuildEngine = 0,DateRemoved  = CURRENT_TIMESTAMP, RemovedBy = "'+str(user)+'",`Notes`= "'+str(notes)+'"    WHERE buildinfo.UpdateID = "'+str(item[0])+'" AND buildinfo.JobID = "'+str(item[1])+'"'
            else :
                if str(mark) == str(1) :
                    sql = 'INSERT INTO buildinfo (`UpdateID`, `JobID`, `IsBuildEngine`, `DateAdded`, `AddedBy`,`Notes`) VALUES ("'+str(item[0])+'", "'+str(item[1])+'", 1,CURRENT_TIMESTAMP,"'+str(user)+'","'+str(notes)+'" );'
                else :
                    sql = 'INSERT INTO buildinfo (`UpdateID`, `JobID`, `IsBuildEngine`, `DateRemoved`,`RemovedBy`,`Notes`) VALUES ("'+str(item[0])+'", "'+str(item[1])+'", 0,CURRENT_TIMESTAMP,"'+str(user)+'","'+str(notes)+'" );'
            db_insert(sql)
        return 1
    except Exception as e:
        print('Error in markBuildEngine',e)
        return 0

def getUpdateIdNames(EngineType=0):
    sql = "SELECT EngineType,UpdateId,UpdateID_Str from updateidinfo "
    result = db_query(sql)
    EngineTypeArray = {}
    for updateId in result:
        EngineTypeArray.setdefault(updateId[0],[]).append((updateId[1],updateId[2]))
    if EngineType == 0:
        return EngineTypeArray
    else:
        return dict(EngineTypeArray[EngineType])

def random(randomvalue):
    randomvalue =  randomvalue + 100/2

def lastDiffSize(jobId,updateId):
    sql = 'SELECT (solominusdiffsum + ( SELECT diffdetails.PatchFileSize FROM diffdetails  join enginemaster on enginemaster.Version = diffdetails.FromVersion and enginemaster.JobID not in (select buildinfo.JobID from buildinfo where buildinfo.UpdateID = "'+str(updateId)+'" and  buildinfo.IsBuildEngine = 1)   WHERE diffdetails.JobID = " '+str(jobId)+' " AND diffdetails.updateid = "'+str(updateId)+'" ORDER BY diffdetails.FromVersion ASC LIMIT 1)) AS finalsum FROM ( SELECT SUM(solodeffdtl.defsize) solominusdiffsum FROM 	( SELECT defids.defid, ( SELECT solodetails.DefSize FROM solodetails WHERE solodetails.UpdateID = " '+str(updateId)+' " AND solodetails.JobID <= " '+str(jobId)+' " AND solodetails.DefID = defids.defid ORDER BY solodetails.JobID DESC LIMIT 1	) defsize, ( SELECT solodetails.Filestate FROM solodetails WHERE solodetails.UpdateID = " '+str(updateId)+' " AND solodetails.JobID <= " '+str(jobId)+' " AND solodetails.DefID = defids.defid ORDER BY solodetails.JobID DESC LIMIT 1) filestate FROM 	( SELECT DISTINCT(solodetails.DefID) FROM solodetails JOIN releaseinfo ON solodetails.JobID = releaseinfo.JobID WHERE solodetails.UpdateID = " '+str(updateId)+' " AND solodetails.JobID <= " '+str(jobId)+' " AND solodetails.JobID > ( SELECT enginemaster.JobID FROM enginemaster WHERE enginemaster.UpdateID = " '+str(updateId)+' " AND enginemaster.Version = 	( SELECT diffpatchdetails.FromVersion FROM diffpatchdetails JOIN enginemaster ON enginemaster.Version = diffpatchdetails.FromVersion AND enginemaster.JobID NOT IN (  SELECT buildinfo.JobID FROM buildinfo WHERE buildinfo.UpdateID =  '+str(updateId)+'  AND buildinfo.IsBuildEngine = 1)    WHERE diffpatchdetails.JobID = " '+str(jobId)+' " AND diffpatchdetails.UpdateID = " '+str(updateId)+' " ORDER BY diffpatchdetails.FromVersion ASC LIMIT 1)  ) ) AS defids ) AS solodeffdtl WHERE  solodeffdtl.filestate > 0 AND solodeffdtl.defid NOT IN ( SELECT diffpatchdetails.defid FROM diffpatchdetails WHERE diffpatchdetails.JobID = " '+str(jobId)+' " AND diffpatchdetails.updateid = " '+str(updateId)+' " AND diffpatchdetails.FromVersion = (	 SELECT diffpatchdetails.FromVersion FROM diffpatchdetails WHERE diffpatchdetails.JobID = " '+str(jobId)+' " AND diffpatchdetails.updateid = " '+str(updateId)+' " ORDER BY diffpatchdetails.fromversion ASC  LIMIT 1 ) ) ) solominusdiff '
    lastDiffResult = db_query(sql,1)
    if lastDiffResult is None or lastDiffResult[0] is None:
        return 0,0
    else:
        sql = 'SELECT diffdetails.PatchFileSize,diffdetails.FromVersion,diffdetails.Version FROM diffdetails join enginemaster on enginemaster.Version = diffdetails.FromVersion and enginemaster.JobID not in (select buildinfo.JobID from buildinfo where buildinfo.UpdateID = "'+str(updateId)+'" and  buildinfo.IsBuildEngine = 1) WHERE diffdetails.JobID = "'+str(jobId)+'"  AND diffdetails.updateid = "'+str(updateId)+'" ORDER BY diffdetails.FromVersion ASC limit 1 '
        lastVersion = db_query(sql,1)
        if lastVersion is None or lastVersion[1] is None :
            lastVersionVal = 0
        else:
            lastVersionVal = lastVersion[1]
        return lastDiffResult[0],lastVersionVal
def lastSoloDiffDtl(jobId,updateId):
    sql = 'SELECT SUM(defsize), COUNT(defid) FROM ( SELECT defids.defid, (SELECT solodetails.DefSize FROM solodetails WHERE solodetails.UpdateID = "'+str(updateId)+'" AND solodetails.JobID <= "'+str(jobId)+'" AND solodetails.DefID = defids.defid ORDER BY solodetails.JobID DESC LIMIT 1 ) defsize, ( SELECT solodetails.Filestate FROM solodetails WHERE solodetails.UpdateID = "'+str(updateId)+'" AND solodetails.JobID <= "'+str(jobId)+'" AND solodetails.DefID = defids.defid ORDER BY solodetails.JobID DESC LIMIT 1) filestate FROM ( SELECT DISTINCT(solodetails.DefID) FROM solodetails JOIN releaseinfo ON solodetails.JobID = releaseinfo.JobID WHERE solodetails.UpdateID = "'+str(updateId)+'" AND solodetails.JobID <= "'+str(jobId)+'" AND solodetails.JobID > ( SELECT enginemaster.JobID FROM enginemaster WHERE enginemaster.UpdateID = "'+str(updateId)+'" AND enginemaster.Version = ( SELECT diffpatchdetails.FromVersion FROM diffpatchdetails  JOIN enginemaster ON enginemaster.Version = diffpatchdetails.FromVersion AND enginemaster.JobID NOT IN (  SELECT buildinfo.JobID FROM buildinfo WHERE buildinfo.UpdateID =  "'+str(updateId)+'"  AND buildinfo.IsBuildEngine = 1)  WHERE diffpatchdetails.JobID = "'+str(jobId)+'" AND diffpatchdetails.UpdateID = "'+str(updateId)+'" ORDER BY diffpatchdetails.FromVersion ASC LIMIT 1) ) ) AS defids ) AS defids WHERE defids.filestate > 0'
    lastDiffCntResult = db_query(sql,1)

    if lastDiffCntResult is None :
        return str(0),str(0)
    else:
        if lastDiffCntResult[0] is None:
            defsizeTotal = 0
        else :
            defsizeTotal = lastDiffCntResult[0]
        if lastDiffCntResult[1] is None:
            defsizeCnt = 0
        else :
            defsizeCnt = lastDiffCntResult[1]
        return str(defsizeTotal),str(defsizeCnt)

def getUpdateSize(jobId,updateId,version):
    getSoloUpdateSizeSql = 'SELECT SUM(defsize), COUNT(defid) FROM ( SELECT defids.defid, ( SELECT solodetails.DefSize FROM solodetails WHERE solodetails.UpdateID = "'+str(updateId)+'" AND solodetails.JobID <= "'+str(jobId)+'"  AND solodetails.DefID = defids.defid ORDER BY solodetails.JobID DESC LIMIT 1) defsize, ( SELECT solodetails.Filestate FROM solodetails WHERE solodetails.UpdateID = "'+str(updateId)+'" AND solodetails.JobID <= "'+str(jobId)+'"  AND solodetails.DefID = defids.defid ORDER BY solodetails.JobID DESC LIMIT 1) filestate FROM ( SELECT DISTINCT(solodetails.DefID) FROM solodetails JOIN releaseinfo ON solodetails.JobID = releaseinfo.JobID WHERE solodetails.UpdateID = "'+str(updateId)+'" AND solodetails.JobID <= "'+str(jobId)+'"  AND solodetails.JobID > ( SELECT enginemaster.JobID FROM enginemaster WHERE enginemaster.UpdateID = "'+str(updateId)+'" AND enginemaster.Version = "'+str(version)+'")) AS defids) AS defids WHERE defids.filestate > 0'
    getDiffUpdateSizeSql = 'SELECT (solominusdiffsum + ( SELECT diffdetails.PatchFileSize FROM diffdetails WHERE diffdetails.JobID = "'+str(jobId)+'" AND diffdetails.updateid = "'+str(updateId)+'" AND diffdetails.FromVersion = "'+str(version)+'" LIMIT 1)) AS finalsum FROM ( SELECT SUM(solodeffdtl.defsize) solominusdiffsum FROM 	( SELECT defids.defid, ( SELECT solodetails.DefSize FROM solodetails WHERE solodetails.UpdateID = "'+str(updateId)+'" AND solodetails.JobID <= "'+str(jobId)+'" AND solodetails.DefID = defids.defid ORDER BY solodetails.JobID DESC LIMIT 1	) defsize, ( SELECT solodetails.Filestate FROM solodetails WHERE solodetails.UpdateID = "'+str(updateId)+'" AND solodetails.JobID <= "'+str(jobId)+'" AND solodetails.DefID = defids.defid ORDER BY solodetails.JobID DESC LIMIT 1) filestate FROM 	( SELECT DISTINCT(solodetails.DefID) FROM solodetails JOIN releaseinfo ON solodetails.JobID = releaseinfo.JobID WHERE solodetails.UpdateID = "'+str(updateId)+'" AND solodetails.JobID <= "'+str(jobId)+'" AND solodetails.JobID > ( SELECT enginemaster.JobID FROM enginemaster WHERE enginemaster.UpdateID = "'+str(updateId)+'" AND enginemaster.Version = "'+str(version)+'") ) AS defids) AS solodeffdtl WHERE solodeffdtl.filestate > 0 AND solodeffdtl.defid NOT IN ( SELECT diffpatchdetails.defid FROM diffpatchdetails WHERE diffpatchdetails.JobID = "'+str(jobId)+'" AND diffpatchdetails.updateid = "'+str(updateId)+'" AND diffpatchdetails.FromVersion = ( "'+str(version)+'"))) solominusdiff'
    SoloUpdateSizeData = db_query(getSoloUpdateSizeSql,1)
    DiffUpdateSizeData = db_query(getDiffUpdateSizeSql,1)
    if SoloUpdateSizeData is None or SoloUpdateSizeData[0] is None :
        SoloUpdateSize,SoloUpdateCnt = 0,0
    else :
        SoloUpdateSize,SoloUpdateCnt = SoloUpdateSizeData[0],SoloUpdateSizeData[1]
    if DiffUpdateSizeData is None or DiffUpdateSizeData[0] is None :
        DiffUpdateSize = 0
    else :
        DiffUpdateSize = DiffUpdateSizeData[0]
    return  SoloUpdateSize,SoloUpdateCnt,DiffUpdateSize

