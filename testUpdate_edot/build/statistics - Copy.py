from django.conf import settings
import random, datetime, time, json
from collections import OrderedDict
from django.contrib.auth.decorators import login_required
from django.shortcuts import *
from . import flib, config, queries
from datetime import datetime as datea
from django.shortcuts import render_to_response
from django.contrib import messages
from django.core.urlresolvers import reverse


@login_required(login_url='/login/')
def statistics(request, type):
    processStat()
    try:
        toDate = datetime.datetime.now().strftime("%Y-%m-%d")
        toTime = datetime.datetime.now().strftime("%H:%M:%S")
        first = datetime.date.today().replace(day=1)
        lastMonth = first - datetime.timedelta(days=1)
        fromDate = lastMonth.strftime("%Y-%m") + '-' + str(datetime.datetime.now().day)
        if request.method == 'GET' and request.GET['t']:
            checkDate = "AND (JobDate BETWEEN '" + fromDate + " 00:00:00' AND '" + toDate + " 23:59:59') "
            checkDateJobinfo = "AND (jobinfo.DateCreated BETWEEN '" + fromDate + " 00:00:00' AND '" + toDate + " 23:59:59') "
        if request.method == 'GET' and len(request.GET.keys()) > 1:
            fromDate, toDate = str(request.GET['from']), str(request.GET['to'])
        if request.method == 'GET' and request.GET['t']:
            checkDate = "AND (JobDate BETWEEN '" + fromDate + " 00:00:00' AND '" + toDate + " 23:59:59') "
            checkDateJobinfo = "AND (jobinfo.DateCreated BETWEEN '" + fromDate + " 00:00:00' AND '" + toDate + " 23:59:59') "
    except Exception as e:
        print('Error (statistics)', e)

    if type == 'qh':
        class data:
            pass
        query = 'select count(jobinfo.jobId) FROM jobinfo where jobinfo.EngineType = ' + str(config.EngineTypeArr[type]) + ' and jobinfo.JobState = 6'
        data_row = flib.db_query(query)
        if data_row[0][0] < 2:
            data = 'Insufficiant Data'
            flib.setMetaInformation(request, 'Dashboard : ' + type.upper(),OrderedDict([('Dashboard : ' + type.upper(), '')]))
            return render(request, 'build/comingSoon.html', {'data': data})
        jobArray, jobArry, dashboardData = [], [], []
        if not type in config.EngineTypeArr:
            return HttpResponse('Invalid request')
        try:
            if request.method == 'GET' and 't' in request.GET:
                t = request.GET['t']
                if 'u' in request.GET:
                    UpdateId = request.GET['u']
                else:
                    rowData = queries.QH_UpdateID(checkDate)
                    UpdateId =  rowData[1][0] #default update ID
                if t == 'dashboard':
                    chartLayout = 'dashboard'
            #jobArray =  qhSummery(request, type,checkDate,checkDateJobinfo)

        except Exception as e:
            t = ''
            print('Error', e)
        updateIdDropdown = "<select id='updateIdDropdown'>"
        qhstatdata = flib.getQhStatdata(request)
        UpdateIdName = ''
        if qhstatdata is not None:
            uidArr = []
            for uid in queries.QH_UpdateID(checkDate):
                uidArr.append(uid[0])
            update_id_string = flib.getUpdateIdName(request,str(tuple(uidArr)))
            for uid in update_id_string:
                if int(qhstatdata['update_id']) == int(uid['update_id']):
                    updateIdDropdown += '<option selected=selected value="' + str(uid['update_id']) + '" >' + str(uid['update_id_str']) + '</option>'
                    UpdateIdName = str(uid['update_id_str']) + '  ( ' + str(uid['update_id']) + ' )'
                else:
                    updateIdDropdown += '<option value="' + str(uid['update_id']) + '" >' + str(uid['update_id_str']) + '</option>'
            updateIdDropdown += "</select>"
            dashboardData.append({'getQhDetails': getjobDetails(request, checkDate, str(UpdateId),str(config.EngineTypeArr[type])), 'details': UpdateidMinAvgMax(str(config.EngineTypeArr[type]), checkDate,str(UpdateId)), 'sizeArray': e2size(request, type, checkDate), })

        flib.setMetaInformation(request, 'Dashboard : ' + type.upper(),OrderedDict([('Dashboard : ' + type.upper(), '')]))
        setattr(data,'updateIdDropdown',updateIdDropdown)
        setattr(data,'layout','build/statstics/qh_dashboard.html')
        setattr(data,'report_date',qhstatdata)
        setattr(data,'update_id',UpdateIdName)

        return render(request, 'build/statistics_qh.html',{'type': str(type),'data':data,'pageName': t,'dashboardData':dashboardData,'jobArray':jobArray})
    if type == 'e2':

        query = 'select count(jobinfo.jobId) FROM jobinfo where jobinfo.EngineType = ' + str(config.EngineTypeArr[type]) + ' and jobinfo.JobState = 6'
        data_row = flib.db_query(query)
        if data_row[0][0] < 2:
            data = 'Insufficiant Data'
            flib.setMetaInformation(request, 'Dashboard : ' + type.upper(),OrderedDict([('Dashboard : ' + type.upper(), '')]))
            return render(request, 'build/comingSoon.html', {'data':data})

        UpdateIdName = (str(config.UpdateTypeOnly[int(4)])   + '  ( ' +str(4) + ' )',str(config.UpdateTypeOnly[int(5)]) + '  ( ' + str(5) + ' )')
        jobArray, jobArry,dashboardData = [], [],[]
        if not type in config.EngineTypeArr:
            return HttpResponse('Invalid request')
        chartTypes = config.chartType[type]
        t, chartLayout, chartTitle,chart_data,= '', 'dashboard', '','',
        try:
            if request.method == 'GET' and 't' in request.GET:
                t = request.GET['t']
                if t == 'dashboard':
                    chartLayout = 'dashboard'
                    jobArray =  summery(request, type,checkDate,checkDateJobinfo)
                    if jobArray is not None:
                        dashboardData.append({'timeArray':e2time(request,type,checkDate),
                                              'sizeArray':e2size(request, type,checkDate),
                                              'frequentFilefun32':frequentFilefun32(request,checkDateJobinfo),
                                              'frequentFilefun64':frequentFilefun64(request,checkDateJobinfo),
                                              'newlyIntroducedFilefun64':newlyIntroducedFilefun64(request,checkDateJobinfo),
                                              'newlyIntroducedFilefun32':newlyIntroducedFilefun32(request,checkDateJobinfo),
                                              'getE2Details32':getjobDetails(request, checkDate, '4',str(config.EngineTypeArr[type])),'32details': UpdateidMinAvgMax(str(config.EngineTypeArr[type]), checkDate,'4'),
                                              'getE2Details64': getjobDetails(request, checkDate, '5',str(config.EngineTypeArr[type])),'64details': UpdateidMinAvgMax(str(config.EngineTypeArr[type]), checkDate,'5'),'UpdateIdName':UpdateIdName
                                              })
                    else:
                         messages.error(request,"<span class='glyphicon glyphicon-warning-sign'></span><b> No DATA FOUND</b>")
                         return render(request, 'build/statistics.html')
        except Exception as e:
            t = ''
            print('Error', e)
        sideBarLinks = '<ul class="nav nav-bar menu">'
        sideBarLinks += '<li><a href = "?t=dashboard" class="menu_item" > Dashboard </a></li>'
        for link in chartTypes:
            chartObj = chartTypes[link]
            if t == chartObj['link']:
                chartLayout = chartObj['link']
                chartTitle = " : Chart For " + link
                sideBarLinks += '<li><a class="active menu_item" href="?t=' + chartObj['link'] + '">' + link + '</a></li>'
            else:
                sideBarLinks += '<li><a href="?t=' + chartObj['link'] + '" class="menu_item">' + link + '</a></li>'
        sideBarLinks += '</ul>'
        chartLayout = 'build/statstics/' + str(chartLayout) + '.html'
        flib.setMetaInformation(request, 'Statistic of : ' + type.upper(), OrderedDict([('Statistic of : ' + type.upper() + '', '')]))

        data = {'type': str(type), 'failedTypes': config.FailedReason, 'data': jobArray,'sideBarLinks': sideBarLinks, 'chartLayout': chartLayout, 'pageName': t,'from':fromDate,'to':toDate,'dashboardData':dashboardData}
        return render(request, 'build/statistics_e2.html',data)
    # return render(request, 'build/statistics.html', {'type':str(type),'failedTypes':config.FailedReason,'sideBarLinks':sideBarLinks,'chartLayout':chartLayout,    return render(request, 'build/statistics.html', {'type':str(type),'failedTypes':config.FailedReason,'sideBarLinks':sideBarLinks,'chartLayout':chartLayout,'jobStateArr':jobArray })
def summery(request, type,checkDate,checkDateJobinfo):
    try:
        data = queries.stat_summeryDetails(str(config.EngineTypeArr[type]),checkDate)
        if len(data) != 0:
            summeryArray, timeArray, sizeArray = [], [], []
            TotalJobs, NewJobs, RevertJobs, MinSize, MaxSize = 0, 0, 0, 0, 0
            for row in data:
                updateID = row[6]
                if row[6] == data[0][6]:
                    TotalJobs = TotalJobs + row[0]
                    NewJobs = NewJobs + row[1]
                    RevertJobs = RevertJobs + row[2]
                MinSize = row[3]
                MaxSize = row[4]
                User = row[5]

            data = queries.stat_UpdateIDwiseMinMax(str(config.EngineTypeArr[type]),checkDate)
            LatestJobID = queries.get_LatestJobID(str(config.EngineTypeArr[type]))
            summeryArray.append(({'TotalJobs': TotalJobs, 'NewJobs': NewJobs, 'RevertJobs': RevertJobs,
                                   'IDsolo32MinSize': data[0][3],'solo32MinSize': flib.getFileSize(int(data[0][4])),'IDsolo32MaxSize':data[0][1], 'solo32MaxSize': flib.getFileSize(int(data[0][2])),
                                  'IDsolo64MinSize': data[0][3],'solo64MinSize': flib.getFileSize(int(data[1][4])),'IDsolo64MaxSize': data[0][1], 'solo64MaxSize': flib.getFileSize(int(data[1][2])),
                                  'IDdiff32MinSize': data[0][7],'diff32MinSize': flib.getFileSize(int(data[0][8])),'IDdiff32MaxSize': data[0][5], 'diff32MaxSize': flib.getFileSize(int(data[0][6])),
                                  'IDdiff64MinSize': data[0][7],'diff64MinSize': flib.getFileSize(int(data[1][8])),'IDdiff64MaxSize': data[0][5], 'diff64MaxSize': flib.getFileSize(int(data[1][6])),
                                  'User': User,'LatestJobID':LatestJobID}))
            data = {'summeryArray': summeryArray}
            return data

    except Exception as e:
        print('Error(summery): ',e)

def e2time(request,type,checkDate):
    try:
        jobArray = []
        rowData = queries.stat_scripttime(str(config.EngineTypeArr[type]),checkDate)
        for timeWise in rowData:
                jobArray.append({'id': timeWise[0], 'scriptTime': str(flib.returnTimeStringOnly(timeWise[1]*1000)), 'TotalTime': str(flib.returnTimeStringOnly(timeWise[2]*1000)), 'UpdateType': str(config.JobInfoFlag[timeWise[3]]), 'JobDate': timeWise[4]})
        return jobArray
    except Exception as e:
        print('Error(time): ', e)
def e2size(request,type,checkDate):
    try:
        if str(type) == 'e2':
            jobArray,jobArry = [],[]
            e2Details = queries.stat_sizeArray(str(config.EngineTypeArr[type]), checkDate)
            cnt = 0
            for row in e2Details['e2For32Bit']:
                diffFirstLine =format( row[5]/1024, '.2f')
                diffSecondLine = format( e2Details['e2For64Bit'][cnt][5]/1024, '.2f')
                jobArray.append({'id': str(row[0]),
                                'firstLine': str(flib.getFileSizeMb(row[1])),
                                'secondLine': str(flib.getFileSizeMb(e2Details['e2For64Bit'][cnt][1])),
                                'user': str(row[2]),
                                'updateType': str(config.JobInfoFlag[row[3]]),
                                'dateCreated': row[4],
                                #'diffFirstLine': str(flib.getFileSizeMb(row[5)),
                                'diffFirstLine': str(diffFirstLine),
                                #'diffSecondLine': str(flib.getFileSizeMb(e2Details['e2For64Bit'][cnt][5])),
                                'diffSecondLine': str(diffSecondLine),
                                'maxDiffFirstLine': str(flib.getFileSizeMb(row[6])),
                                'maxDiffSecondLine': str(flib.getFileSizeMb(e2Details['e2For64Bit'][cnt][6]))
                })
                cnt = cnt + 1
            return jobArray
        elif str(type) == 'qh':
            qhSizeDetails = queries.stat_sizeArray(str(config.EngineTypeArr[type]), checkDate)
           # print(qhSizeDetails) omkar


    except Exception as e:
        print('Error(size): ', e)

def frequentFilefun32(request,checkDate):
    try:
        jobArray = []
        rowData32 = queries.frequentFileData(checkDate,4)
        for freqFile in rowData32:
            jobArray.append({'FileName4': str(freqFile[0]), 'TotalCount4': str(freqFile[1])})
        return jobArray
    except Exception as e:
        print('Error(frequentFilefun32): ', e)

def frequentFilefun64(request,checkDate):
    try:
        jobArray = []
        rowData64 = queries.frequentFileData(checkDate, 5)
        for freqFile in rowData64:
            jobArray.append({'FileName5': str(freqFile[0]), 'TotalCount5': str(freqFile[1])})
        return jobArray
    except Exception as e:
        print('Error(frequentFilefun64): ', e)
def newlyIntroducedFilefun32(request,checkDate):
    try:
        jobArray = []
        rowData32 = queries.newlyIntroducedFileData(checkDate,4)
        for freqFile in rowData32:
            jobArray.append({ 'FileName4': str(freqFile[0]), 'TotalCount4': str(freqFile[1])})
        return jobArray
    except Exception as e:
        print('Error(newlyIntroducedFilefun32): ', e)
def newlyIntroducedFilefun64(request,checkDate):
    try:
        jobArray = []
        rowData64 = queries.newlyIntroducedFileData(checkDate,5)
        for freqFile in rowData64:
            jobArray.append({ 'FileName5': str(freqFile[0]), 'TotalCount5': str(freqFile[1])})
        return jobArray
    except Exception as e:
        print('Error(newlyIntroducedFilefun64): ', e)



# QH related functions

def qhSummery(request, type,checkDate,checkDateJobinfo):
    try:
        if 'u' in request.GET:
            getUpdateId = request.GET['u']
        else:
            rowData = queries.QH_UpdateID(checkDate)
            getUpdateId = rowData[0][0]

        data = queries.stat_summeryDetails(str(config.EngineTypeArr[type]),checkDate,getUpdateId)
        if len(data) != 0:
            summeryArray, timeArray, sizeArray = [], [], []
            TotalJobs, NewJobs, RevertJobs, MinSize, MaxSize = 0, 0, 0, 0, 0
            for row in data:
                updateID = row[6]
                if str(updateID) == str(getUpdateId):
                    TotalJobs = TotalJobs + row[0]
                    NewJobs = NewJobs + row[1]
                    RevertJobs = RevertJobs + row[2]
                if row[6] is None and row[8] is None:
                    MinSize = 0
                    MaxSize = 0
                MinSize = row[3]
                MaxSize = row[4]
                User = row[5]

            data = queries.stat_UpdateIDwiseMinMax(str(config.EngineTypeArr[type]),checkDate)
            LatestJobID = queries.get_LatestJobID(str(config.EngineTypeArr[type]))
            summeryArray.append(({'TotalJobs': TotalJobs, 'NewJobs': NewJobs, 'RevertJobs': RevertJobs,
                                   'IDsolo32MinSize': data[0][3],'solo32MinSize': flib.getFileSize(int(data[0][4])),'IDsolo32MaxSize':data[0][1], 'solo32MaxSize': flib.getFileSize(int(data[0][2])),
                                  'IDsolo64MinSize': data[0][3],'solo64MinSize': flib.getFileSize(int(data[1][4])),'IDsolo64MaxSize': data[0][1], 'solo64MaxSize': flib.getFileSize(int(data[1][2])),
                                  'IDdiff32MinSize': str(data[0][7]),'diff32MinSize': str(flib.getFileSize(int(data[0][8]))),'IDdiff32MaxSize': str(data[0][5]), 'diff32MaxSize': str(flib.getFileSize(int(data[0][6]))),
                                  'IDdiff64MinSize': str(data[0][7]),'diff64MinSize': str(flib.getFileSize(int(data[1][8]))),'IDdiff64MaxSize': str(data[0][5]), 'diff64MaxSize': str(flib.getFileSize(int(data[1][6]))),
                                  'User': User,'LatestJobID':LatestJobID}))
            data = {'summeryArray': summeryArray}
            return data

    except Exception as e:
        print('Error(qhsummery): ',e)


def getjobDetails(request,checkDate,UpdateId,type):
    try:
        jobArray,SoloSize,PkgSize,MinDiffSize,MaxDiffSize,version = [],'','','','',''
        rowData = queries.qhSoloDiffPkgDetails(checkDate,UpdateId,type)
        updateIDArr = {}
        for qhRow in rowData:
            SoloSize = flib.getFileSizeKbMb(qhRow[2])
            PkgSize = flib.getFileSizeKbMb(qhRow[4])
            if qhRow[5] != 0 and qhRow[6] != 0:
                MinDiffSize = flib.getFileSizeKbMb(qhRow[5])
                MaxDiffSize = flib.getFileSizeKbMb(qhRow[5])
            else:
                MinDiffSize = 'None'
                MaxDiffSize = 'None'
            version = str(qhRow[9])+" ("+str(format(int(qhRow[9]), '02X'))+")"
            noOfFiles = int(qhRow[8])
            jobArray.append({ 'JobID': str(qhRow[0]), 'JobDate': str(qhRow[1]), 'SoloSize': str(SoloSize),'PkgType': str(qhRow[3]), 'PkgSize': PkgSize, 'MinDiffSize': str(MinDiffSize), 'MaxDiffSize': str(MaxDiffSize),'version':str(version),'noOfFiles':noOfFiles})
        return jobArray
    except Exception as e:
        print('Error(newlyIntroducedFilefun64): ', e)



def UpdateidMinAvgMax(type,checkDate,UpdateId):
    resultArr = {}
    result = queries.qhStat_UpdateIDwiseMinMax(type, checkDate, UpdateId)
    resultArr.update({'MIN_soloMin': flib.getFileSizeKbMb(result[0][0]),
                      'AVG_soloAvg': flib.getFileSizeKbMb(result[0][1]),
                      'MAX_soloMax': flib.getFileSizeKbMb(result[0][2]),
                      'MIN_MinDiff': flib.getFileSizeKbMb(result[0][3]),
                      'AVG_MinDiff': flib.getFileSizeKbMb(result[0][4]),
                      'MAX_MinDiff': flib.getFileSizeKbMb(result[0][5]),
                      'MIN_MaxDiff': flib.getFileSizeKbMb(result[0][6]),
                      'AVG_MaxDiff': flib.getFileSizeKbMb(result[0][7]),
                      'MAX_MaxDiff': flib.getFileSizeKbMb(result[0][8]),
                      'MIN_Makeupg': flib.getFileSizeKbMb(result[0][9]),
                      'AVG_Makeupg': flib.getFileSizeKbMb(result[0][10]),
                      'MAX_Makeupg': flib.getFileSizeKbMb(result[0][11]),
                      'MIN_NoOfFiles': result[0][12],
                      'AVG_NoOfFiles': result[0][13],
                      'MAX_NoOfFiles': result[0][14],
                      })
    return resultArr


def processStat():
    try:
        data = flib.db_query("select JobID from stat_solo_diff_details order by JobID desc limit 1 ")
        if len(data) == 0 :
            lastJobID = 0
        else:
            lastJobID = data[0][0]
        #sql = "SELECT solodetails.JobID, jobinfo.DateCreated, jobinfo.EngineType, jobinfo.Flag, jobinfo.UserName, enginemaster.UpdateID, ( SELECT SUM(FileSize) FROM solodetails WHERE UpdateID = enginemaster.UpdateID AND JobID = jobinfo.JobID) AS soloSize, MIN(diffdetails.PatchFileSize), MAX(diffdetails.PatchFileSize), upgenginemaster.PkgType, upgenginemaster.PkgSize,( SELECT COUNT(JobID) FROM solodetails WHERE UpdateID = enginemaster.UpdateID AND JobID = jobinfo.JobID) AS filecount,downloaddetails.Version FROM solodetails LEFT JOIN jobinfo ON solodetails.JobID = jobinfo.JobID AND jobinfo.JobState = 6 LEFT JOIN downloaddetails ON downloaddetails.JobID = jobinfo.JobID AND downloaddetails.UpdateID = solodetails.UpdateID LEFT JOIN enginemaster ON solodetails.JobID = enginemaster.JobID AND solodetails.UpdateID = enginemaster.UpdateID LEFT JOIN diffdetails ON solodetails.JobID = diffdetails.JobID AND solodetails.UpdateID = diffdetails.UpdateID LEFT JOIN upgenginemaster ON upgenginemaster.JobID = solodetails.JobID AND upgenginemaster.UpdateID = solodetails.UpdateID WHERE jobinfo.JobID = solodetails.JobID AND jobinfo.JobState = 6 AND jobinfo.JobID > "+str(lastJobID)+" GROUP BY jobinfo.JobID, solodetails.UpdateID ORDER BY jobinfo.JobID ASC"
        sql = "SELECT jobinfo.JobID, jobinfo.DateCreated, jobinfo.EngineType, jobinfo.Flag, jobinfo.UserName, enginemaster.UpdateID,solofilesum.FileSize,diffsizes.minPatchFileSize,diffsizes.maxPatchFileSize,upgenginemaster.PkgType,upgenginemaster.PkgSize,downloaddetails.Version,solofilecnt.FileCount,releaseinfo.vdb FROM jobinfo JOIN releaseinfo ON jobinfo.JobID = releaseinfo.JobID LEFT JOIN enginemaster ON jobinfo.JobID = enginemaster.JobID JOIN (SELECT solodetails.JobID JobID,solodetails.UpdateID UpdateID,SUM(solodetails.FileSize) FileSize   from solodetails group by solodetails.JobID,solodetails.UpdateID) solofilesum ON solofilesum.UpdateID = enginemaster.UpdateID AND solofilesum.JobID = jobinfo.JobID JOIN (SELECT solodetails.JobID JobID,solodetails.UpdateID UpdateID,COUNT(solodetails.JobID) FileCount   from solodetails group by solodetails.JobID,solodetails.UpdateID) solofilecnt ON solofilecnt.UpdateID = enginemaster.UpdateID AND solofilecnt.JobID = jobinfo.JobID LEFT JOIN upgenginemaster ON upgenginemaster.UpdateID = enginemaster.UpdateID AND upgenginemaster.JobID = jobinfo.JobID LEFT JOIN (select diffdetails.JobID,diffdetails.UpdateID,min(diffdetails.PatchFileSize) minPatchFileSize,max(diffdetails.PatchFileSize) maxPatchFileSize    from diffdetails group by diffdetails.JobID,diffdetails.UpdateID) AS diffsizes ON diffsizes.UpdateID = enginemaster.UpdateID AND diffsizes.JobID = jobinfo.JobID LEFT JOIN downloaddetails ON downloaddetails.JobID = jobinfo.JobID AND downloaddetails.UpdateID = enginemaster.UpdateID WHERE  jobinfo.JobState = 6 AND jobinfo.JobID > "+str(lastJobID)+" GROUP BY jobinfo.JobID, enginemaster.UpdateID"
        data = flib.db_query(sql)
        if len(data) > 0 :
            cnt = 0
            sql = 'INSERT INTO `stat_solo_diff_details` (`JobID`, `EngineType`, `UpdateType`, `UpdateID`, `SoloSize`,`MinDiffSize`,`MaxDiffSize`, `JobDate`,`User`,`PkgType`,`PkgSize`,`FileCount`,`Version`,`Vdb`) VALUES '
            for result in data:
                solodetails = str(result[6])
                sql += '("'+str(result[0])+'","'+str(result[2])+'"," '+str(result[3])+'"," '+str(result[5])+'"," '+str(solodetails)+'", "'+str(result[7])+'", "'+str(result[8])+'", "'+format(result[1])+'","'+str(result[4])+'"," '+str(result[9])+'", "'+str(result[10])+'", "'+str(result[11])+'", "'+str(result[12])+'", "'+format(result[13])+'"),'
                cnt = cnt + 1
            sql = sql[:-1]
            flib.db_insert(sql)
        #for job time stat
        data = flib.db_query("select JobID from stat_scripttime order by JobID desc limit 1 ")
        if len(data) == 0:
            lastJobID = 0
        else:
            lastJobID = data[0][0]
        sql = "select jobstatedetails.JobId,jobinfo.EngineType, jobinfo.Flag, TIMESTAMPDIFF(SECOND,min(StartTime),max(StartTime)) as totaltime, sum(jobstatedetails.TimeTaken) as script, jobinfo.DateCreated from jobstatedetails,jobinfo where jobinfo.JobID = jobstatedetails.JobID  and jobinfo.JobState = 6 and jobinfo.JobID > "+str(lastJobID)+" group by jobinfo.JobID  order by jobinfo.JobID asc"
        data = flib.db_query(sql)
        if data != None and len(data) > 0:
            sql='INSERT INTO `stat_scripttime` (`JobID`, `EngineType`, `UpdateType`, `ActualTimeTaken`, `ScriptTime`, `JobDate`) VALUES '
            for result in data:
                sql += '(' + str(result[0]) + ',' + str(result[1]) + ', ' + str(result[2]) + ', ' + str(result[3]) + ', ' + str(result[4]) + ',"' + format(result[5]) + '"),'
            sql = sql[:-1]
            flib.db_insert( sql)
    except Exception as e:
        print ("Error(processStat): ",e)



