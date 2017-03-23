from django.shortcuts import *
import json
from django.contrib.auth.decorators import login_required
from build.flib import jenkins_check
from . import flib,config
from django.conf import settings
from collections import OrderedDict
from build.flib import database_connection_check
from build.pipeline_view import getJobStatus

jobSteps = config.jobSteps[1]

@login_required(login_url='/login/')
@jenkins_check
@database_connection_check
def e2_index(request):
    flib.setMetaInformation(request,'Create : E2',OrderedDict([('Create Job : E2','')]))
    RefreshPage = 0
    try:
            if request.user.get_username() == settings.AUTOMATION_USER and settings.AUTOMATION_FLAG == 1:
                RefreshPage = 1
    except Exception as e:
        print('Error :', e)
    return render(request, "build/e2index.html",{'jobContent':'','type':'e2','failedTypes':config.FailedReason,'RefreshPage':RefreshPage})

@login_required(login_url='/login/')
@database_connection_check

@login_required(login_url='/login/')
@database_connection_check
def e2_ajax(request):
    if not request.is_ajax():
        return HttpResponseRedirect('/')
    sql = "SELECT * FROM %s where EngineType = 2 and Flag = 1 order by JobId desc   limit 0,1 " % ("jobinfo", )
    data_row = flib.db_query(sql,1)
    flib.automate_proccessing(request,data_row)
    if data_row == None:
        jobRunningStatus = {'status': 1, 'response': 'No job is running.'}
        jobRunningStatus = getJobStatus('e2')
        if str(jobRunningStatus['status']) == str(0):
            content = '<div><p class="list-group-item list-group-item-info"><span class="glyphicon glyphicon-alert"></span>&nbsp;Revert job is running. Please complete revert job to start a normal job.  </p></div>'
            data = {'data': content, 'status': 1, 'mannual_step': 0, 'pconsole_text': '', 'nexProgLogId': 0,'console_head': '', 'jobRunningStatus': 1}  # create json array to response json
            return HttpResponse(json.dumps(data), content_type='application/json')
        else :
            content = '<div><p class="list-group-item list-group-item-info"><span class="glyphicon glyphicon-alert"></span>&nbsp; No Active Jobs. Please start a new job to continue ! | </p></div>'
            data = {'data':content,'status':1,'mannual_step':0,'pconsole_text':'','nexProgLogId':0,'console_head':'','jobRunningStatus':0}  # create json array to response json
            return HttpResponse(json.dumps(data), content_type='application/json')
    jobRunningStatus = {'status': 1, 'response': 'No job is running.'}
    jobRunningStatus = getJobStatus('e2')
    jobId = data_row[0]
    sql = "SELECT JobState, TimeTaken, StartTime, PercentDone, JobID  FROM %s where JobID = %s order by JobState asc " % ("jobstatedetails",jobId)
    data_jobState = flib.db_query(sql)
    activeState = []
    activeStateDetails = {}
    for jState in data_jobState:
        activeState.append(jState[0])
        activeStateDetails.update({jState[0]:jState})
    jobArr = {}
    CompletedJob = -1
    for job in jobSteps:
        status = ''
        if job in activeStateDetails:
            if activeStateDetails[job][3] == 100:
                status = 'completed'
                CompletedJob += 1
        jobArr[jobSteps[job]] = {'order':job,'status':status}
    content = ''
    if activeState :
        maxActive = max(activeState)
        nextStep = maxActive + 1
    else:
        maxActive = 1
    status,mannualStep,offset = 0,0,1
    progressCounter = activeStateDetails[maxActive][3]
    if maxActive == 7 or maxActive == 6:
        status,offset = 1,0
        nextStep = 0
    elif maxActive ==  3  and progressCounter == 100:
        mannualStep = 4
        progressCounter = 0
    elif maxActive == 5 and progressCounter == 100:
        mannualStep = 6
        progressCounter = 0
    jobStatus,aniClass,flag,jbsts,jbstsname = '','',0,'','',
    if status == 0:
        content += '<table id="current-job-tbl" class="shadow-in" ><tr><th colspan="2" rowspan="2" >Active Job : #'+str(jobId)+'</th><th>Created By</th><th>Created On</th><th>Engine Type</th><th>Log</th></tr>  <tr><td>'+str(data_row[5])+'</td><td>'+str(data_row[2])+'</td><td>E2</td><td><a target="_blank" href="/jenkins-log/'+str(jobId)+'">Click Here to view Log</a></td></tr></table></div><div class="clear"></div>'
        content +='<div class="progress shadow-in">'
        progresPer = (CompletedJob*20)
        if progresPer == 0:
            progresPer = 1
        ajaxRunningJob = request.POST['running_job']
        if str(ajaxRunningJob) == str(1):
            progresPer =  progresPer + 1
            content += '<div class="progress-bar active shadow-in progress-bar-success progress-bar-striped " role="progressbar" aria-valuenow="'+str(progresPer)+'" aria-valuemin="0" aria-valuemax="100" style="width: '+str(progresPer)+'%;"> </div>'
        elif progressCounter != 100 and mannualStep == 0 :
            progresPer =  progresPer + 1
            content += '<div class="progress-bar active shadow-in progress-bar-success progress-bar-striped " role="progressbar" aria-valuenow="'+str(progresPer)+'" aria-valuemin="0" aria-valuemax="100" style="width: '+str(progresPer)+'%;"> </div>'
        elif progressCounter != 100 and mannualStep == 0 :
            progresPer =  progresPer + 1
            content += '<div class="progress-bar active shadow-in progress-bar-success progress-bar-striped " role="progressbar" aria-valuenow="'+str(progresPer)+'" aria-valuemin="0" aria-valuemax="100" style="width: '+str(progresPer)+'%;"> </div>'
        elif progressCounter == 100 and mannualStep == 0 :
            progresPer =  progresPer + 1
            content += '<div class="progress-bar active shadow-in progress-bar-success progress-bar-striped " role="progressbar" aria-valuenow="'+str(progresPer)+'" aria-valuemin="0" aria-valuemax="100" style="width: '+str(progresPer)+'%;"> </div>'
        else:
            content += '<div class="progress-bar active shadow-in progress-bar-success" role="progressbar" aria-valuenow="'+str(progresPer)+'" aria-valuemin="0" aria-valuemax="100"style="width: '+str(progresPer)+'%;"> </div>'
        content +='</div>'
        content +='<div id="pipeline">'
        for job in jobSteps:
            if job == 1:
                continue
            content +='<div class="jobs">'
            curJob = jobArr[jobSteps[job]]
            abortbtn,abortClass,jobStatusMsg,jobOtherDetails,forminput = 1,'','','',''
            if curJob['status'] == 'completed':
                jobStatus,jobStatusMsg = curJob['status'],'Completed Successfully'
                aniClass =  '<span class="glyphicon glyphicon-ok-sign"></span>'
                jobOtherDetails = '<p> Start Time  : '+format(activeStateDetails[job][2])+'</p>'
                jobOtherDetails += '<p> Time Taken  : '+str(flib.returnTimeString(activeStateDetails[job][1]*1000))+'</p>'
            elif progressCounter != 100 and job == maxActive:
                jobStatus,flag = 'running',1
                jobStatusMsg = 'Job is Running '
                aniClass =  '<span class="glyphicon glyphicon-refresh spin"></span>'
                jobOtherDetails = '<p> Start Time : '+format(activeStateDetails[maxActive][2])+'  </p>'
                mannualStep = 0
            elif progressCounter == 100 and job == nextStep:
                jobStatus,flag = 'running',1
                jobStatusMsg = 'Job is in Queue '
                aniClass =  '<span class="glyphicon glyphicon-hourglass spin"></span>'
                jobOtherDetails = '<p> Start Time : '+format(activeStateDetails[maxActive][2])+'  </p>'
                mannualStep = 0
            elif curJob['status'] == '':
                jobStatus,jobStatusMsg = '','&nbsp'
                aniClass = '<span class="glyphicon glyphicon-time"></span>'
                if mannualStep == 4 and job == 4:
                    soloDiffDetails = " '' "
                    forminput = '<h6 class="generatemv"><div class="generatemv"></div><input type="button" value="Continue" class="navbar-inverse shadow-in manualStep" onclick="create_job_process(' + str(mannualStep) + ','+str(soloDiffDetails)+','+str(jobId)+');"/></h6> '
                elif mannualStep == 6 and job == 6:
                    from . import pipeline_view
                    soloDiffDetails = pipeline_view.jobSoloDiffDetailsDict(jobId)
                    if soloDiffDetails != "":
                        soloDiffDetails = " ' " + soloDiffDetails + " ' "
                    else:
                        soloDiffDetails = " '' "
                    forminput = '<h6 class="generatemv"><input type="button" class= "manualStep navbar-inverse shadow-in" value="Continue" class="navbar-inverse shadow-in" onclick="create_job_process(' + str(mannualStep) + ','+str(soloDiffDetails)+','+str(jobId)+');"/></h6>'
            if(nextStep == job and str(ajaxRunningJob) == str(1)):
                jobStatus = ' running_ajax '
                jobStatusMsg = 'Updating Database..'
                aniClass = '<span class="glyphicon glyphicon-repeat spin"></span>'
            content += '<div   class="job  shadow-in '+jobStatus+' "  >'
            content += '<h6><b>'+ jobSteps[job] +'</b><span class="aniClass">'+aniClass+'</span> </h6>'
            if jobOtherDetails != '':
                content += jobOtherDetails
            else:
                if str(ajaxRunningJob) != str(1):
                    content += forminput
            content += '<h6> <b>'+jobStatusMsg+'</b></h6>'
            content += '</div>'
            if(len(jobSteps) > job ):
                content += '<div class=job-seprator><span class="glyphicon glyphicon-menu-right"></span></div>'
            content +='</div>'
        content +='</div>'
    else:
        ajaxRunningJob = request.POST['running_job']
        if str(ajaxRunningJob) == str(1) and maxActive != 6:
            content += '<div class="progress shadow-in"><div class="progress-bar active shadow-in progress-bar-success progress-bar-striped " role="progressbar" aria-valuenow="5" aria-valuemin="0" aria-valuemax="100"style="width:5%;"> </div></div>'
            content +='<div><p class="success-msg list-group-item list-group-item-success"><span class="glyphicon glyphicon-check"></span>&nbsp;Your request is processing. Please wait while we are creating new job...  !</p></div>'
        elif str(jobRunningStatus['status']) == str(0):
            content = '<div><p class="list-group-item list-group-item-info"><span class="glyphicon glyphicon-alert"></span>&nbsp;Revert job is running. Please complete revert job to start a normal job.  </p></div>'
            content += flib.jobBoxes(data_row,data_jobState,jobId,1)
        else:
            content +='<div><p class="list-group-item list-group-item-info" id="start_new_job"><span class="glyphicon glyphicon-alert"></span>&nbsp; No Active Jobs. Please start a new job to continue !</p></div>'
            content += flib.jobBoxes(data_row,data_jobState,jobId,1)
    if status == 0:
        if progressCounter == 100 or mannualStep != 0:
            progLogData = flib.progLog(jobId,data_row,jobSteps[nextStep],request.POST['progress_log'])
        else:
            progLogData = flib.progLog(jobId,data_row,jobSteps[maxActive],request.POST['progress_log'])
    else :
         progLogData = flib.progLog()
    data = {'jobId':jobId,'data':content,'status':status,'mannual_step':mannualStep,'pconsole_text':progLogData['pconsole_text'],'nexProgLogId':progLogData['nexProgLogId'],'console_head':progLogData['console_head'],'maxActive':maxActive,'activeStep':progLogData['activeStep'],'jobRunningStatus':jobRunningStatus}  # create json array to response json
    return HttpResponse(json.dumps(data), content_type='application/json')