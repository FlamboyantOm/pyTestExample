from django.conf import settings
import random, datetime, time, json
from collections import OrderedDict
from django.contrib.auth.decorators import login_required
from django.shortcuts import *
from . import flib, config
from datetime import datetime as datea
from django.shortcuts import render_to_response
from django.contrib import messages
from django.core.urlresolvers import reverse

@login_required(login_url='/login/')
def statistics(request, type):
    processStat()
    #return HttpResponse('22')

    statRequest = flib.statRequest(request, type)
    query = 'select count(jobinfo.jobId) FROM jobinfo where jobinfo.EngineType = ' + str(config.EngineTypeArr[type]) + ' and jobinfo.JobState = 6'
    data_row = flib.db_query(query)
    if data_row:
        if data_row[0][0] < 2:
            data = 'Insufficiant Data'
            flib.setMetaInformation(request, 'Dashboard : ' + type.upper(),OrderedDict([('Dashboard : ' + type.upper(), '')]))
            return render(request, 'build/comingSoon.html', {'data': data})

    if not type in config.EngineTypeArr:
        return HttpResponse('Invalid request')
    updateIdDropdown = "<select id='updateIdDropdown' class='input-style' >"
    updatIds = flib.getUpdateIdNames(config.EngineTypeArr[type])
    for uid in updatIds:
        if str(statRequest['update_id']) == str(uid):
            updateIdDropdown += "<option value="+str(uid)+" selected>"+str(uid)+" - "+str( updatIds[uid])+"</option>"
            statRequest['update_id_str'] = str(updatIds[uid]) + ' ( ' + hex(uid)[2:].upper() + ' )'
        else :
            updateIdDropdown += "<option value="+str(uid)+" >"+str(uid)+" - "+str( updatIds[uid])+"</option>"
    updateIdDropdown += "</select>"
    flib.setMetaInformation(request, 'Dashboard : ' + type.upper(),OrderedDict([('Dashboard : ' + type.upper(), '')]))
    #sql = "SELECT stat_solo_diff_details.JobID, stat_solo_diff_details.EngineType, stat_solo_diff_details.UpdateType, UpdateID, SoloSize, stat_solo_diff_details.JobDate, USER, FileCount, VERSION, Vdb, FirstDef,IFNULL(stat_scripttime.ActualTimeTaken, 0),LastDef FROM stat_solo_diff_details  left join stat_scripttime on stat_solo_diff_details.JobID = stat_scripttime.JobID where stat_solo_diff_details.UpdateID = '"+str(statRequest['update_id'])+"' and stat_solo_diff_details.JobDate BETWEEN '"+str(statRequest['from_date'])+" 00:00:00' AND '"+str(statRequest['to_date'])+" 23:59:59'"


    processItems = ''
    sql = "SELECT stat_solo_diff_details.*, IFNULL(stat_scripttime.ActualTimeTaken, 0) FROM stat_solo_diff_details  left join stat_scripttime on stat_solo_diff_details.JobID = stat_scripttime.JobID where stat_solo_diff_details.UpdateID = '" + str(statRequest['update_id']) + "' and stat_solo_diff_details.JobDate BETWEEN '" + str(statRequest['from_date']) + " 00:00:00' AND '" + str(statRequest['to_date']) + " 23:59:59'"

    StatData = flib.db_query(sql)
    statRequest['updateIdDropdown'] = updateIdDropdown
    statRequest['layout'] = 'build/statistics/dashboard.html'
    if len(StatData) == 0:
        messages.add_message(request, messages.ERROR,"<span class='glyphicon glyphicon-info-sign'></span><b> No record available. Please select different date range.</b>")
        return render(request, 'build/statistics/statistics.html', {'type': str(type), 'data': statRequest})
    StatProcessedData, CompareDataMin, CompareDataMax, CompareDataAvg, StatlineChartData = [], {}, {}, {}, []
    CompareDataAvg[0], CompareDataAvg[1], CompareDataAvg[2], CompareDataAvg[3], CompareDataAvg[4], i = 0, 0, 0, 0, 0, 0
    for item in StatData:
        #processItems = [item[0], item[5], item[8], item[7], flib.getFileSizeMb(item[4]), flib.getFileSizeKb(item[10]),flib.returnTimeStringSec(item[11]), flib.getFileSizeMb(item[12])]
        processItems = [item[0], item[4], item[7], item[8],item[9],flib.getFileSizeMb(item[10]),item[11],item[12],flib.getFileSizeMb(item[13]),item[14],flib.getFileSizeMb(item[15]),item[16],item[17],flib.returnTimeStringSec(item[18]),]


    #sql = "SELECT stat_solo_diff_details_.JobID, stat_solo_diff_details_.EngineType, stat_solo_diff_details_.UpdateType, UpdateID, SoloSize, stat_solo_diff_details_.JobDate, USER, FileCount, VERSION, Vdb, FirstDef,IFNULL(stat_scripttime.ActualTimeTaken, 0),LastDef FROM stat_solo_diff_details_  left join stat_scripttime on stat_solo_diff_details_.JobID = stat_scripttime.JobID where stat_solo_diff_details_.UpdateID = '"+str(statRequest['update_id'])+"' and stat_solo_diff_details_.JobDate BETWEEN '"+str(statRequest['from_date'])+" 00:00:00' AND '"+str(statRequest['to_date'])+" 23:59:59'"
    sql = "SELECT stat_solo_diff_details.*, IFNULL(stat_scripttime.ActualTimeTaken, 0) FROM stat_solo_diff_details  left join stat_scripttime on stat_solo_diff_details.JobID = stat_scripttime.JobID where stat_solo_diff_details.UpdateID = '" + str(statRequest['update_id']) + "' and stat_solo_diff_details.JobDate BETWEEN '" + str(statRequest['from_date']) + " 00:00:00' AND '" + str(statRequest['to_date']) + " 23:59:59'"




    StatData  = flib.db_query(sql)
    statRequest['updateIdDropdown'] = updateIdDropdown
    statRequest['layout'] = 'build/statistics/dashboard.html'
    if len(StatData) == 0:
        messages.add_message(request, messages.ERROR,"<span class='glyphicon glyphicon-info-sign'></span><b> No record available. Please select different date range.</b>")
        return render(request, 'build/statistics/statistics.html',{'type': str(type), 'data': statRequest})
    StatProcessedData,CompareDataMin,CompareDataMax,CompareDataAvg,StatlineChartData = [],{},{},{},[]
    CompareDataAvg[0],CompareDataAvg[1],CompareDataAvg[2],CompareDataAvg[3],CompareDataAvg[4],i = 0,0,0,0,0,0
    for item in StatData:
        #processItem = [item[0],item[5],item[8],item[7],flib.getFileSizeMb(item[4]),flib.getFileSizeKb(item[10]),flib.returnTimeStringSec(item[11]),flib.getFileSizeMb(item[12])]
        processItem = [item[0], item[4], item[7], item[8],flib.getFileSizeMb(item[9]),item[10],item[11],flib.getFileSizeMb(item[12]),item[13],item[14],flib.getFileSizeMb(item[15]),item[16],item[17],flib.returnTimeStringSec(item[18]),]

        lineChart = [item[0], str(item[5]), item[4], item[10]]
        if i == 0 :
            i = 1
            CompareDataMin[0],CompareDataMin[1],CompareDataMin[2],CompareDataMin[3],CompareDataMin[4] = item[9],item[10],item[12],item[7],item[11]
            CompareDataMax[0],CompareDataMax[1],CompareDataMax[2],CompareDataMax[3],CompareDataMax[4] = item[9],item[10],item[12],item[7],item[11]
        else:
            if item[9] < CompareDataMin[0]:CompareDataMin[0] = item[9]
            if item[10] < CompareDataMin[1]:CompareDataMin[1] = item[10]
            if item[12] < CompareDataMin[2]:CompareDataMin[2] = item[12]
            if item[7] < CompareDataMin[3]:CompareDataMin[3] = item[7]
            if item[11] < CompareDataMin[4]:CompareDataMin[4] = item[11]

            if item[9] > CompareDataMax[0]:CompareDataMax[0] = item[9]
            if item[10] > CompareDataMax[1]:CompareDataMax[1] = item[10]
            if item[12] > CompareDataMax[2]:CompareDataMax[2] = item[12]
            if item[7] > CompareDataMax[3]:CompareDataMax[3] = item[7]
            if item[11] > CompareDataMax[4]:CompareDataMax[4] = item[11]
        CompareDataAvg[0]+=item[9]
        CompareDataAvg[1]+=item[10]
        CompareDataAvg[2]+=item[12]
        CompareDataAvg[3]+=item[7]
        CompareDataAvg[4]+=item[11]
        StatProcessedData.append(processItem)
        StatlineChartData.append(lineChart)
    #print('raw',CompareDataAvg)
    for DataCompareIndex in CompareDataAvg:
        if DataCompareIndex == 0:
            CompareDataAvg[DataCompareIndex] = flib.getFileSizeMb(CompareDataAvg[DataCompareIndex] / len(StatData))
            CompareDataMin[DataCompareIndex] = flib.getFileSizeMb(CompareDataMin[DataCompareIndex])
            CompareDataMax[DataCompareIndex] = flib.getFileSizeMb(CompareDataMax[DataCompareIndex])
        elif DataCompareIndex == 1:
            CompareDataAvg[DataCompareIndex] = flib.getFileSizeKb(CompareDataAvg[DataCompareIndex] / len(StatData))
            CompareDataMin[DataCompareIndex] = flib.getFileSizeKb(CompareDataMin[DataCompareIndex])
            CompareDataMax[DataCompareIndex] = flib.getFileSizeKb(CompareDataMax[DataCompareIndex])
        elif DataCompareIndex == 2:
            CompareDataAvg[DataCompareIndex] = flib.getFileSizeKb(CompareDataAvg[DataCompareIndex] / len(StatData))
            CompareDataMin[DataCompareIndex] = flib.getFileSizeKb(CompareDataMin[DataCompareIndex])
            CompareDataMax[DataCompareIndex] = flib.getFileSizeKb(CompareDataMax[DataCompareIndex])
        elif DataCompareIndex == 3:
            CompareDataAvg[DataCompareIndex] = str(round(CompareDataAvg[DataCompareIndex] / len(StatData)))+' Files'
            CompareDataMin[DataCompareIndex] = str(CompareDataMin[DataCompareIndex])+' Files'
            CompareDataMax[DataCompareIndex] = str(CompareDataMax[DataCompareIndex])+' Files'
        elif DataCompareIndex == 4:
            CompareDataAvg[DataCompareIndex] = flib.returnTimeStringSec(CompareDataAvg[DataCompareIndex] / len(StatData))
            CompareDataMin[DataCompareIndex] = flib.returnTimeStringSec(CompareDataMin[DataCompareIndex])
            CompareDataMax[DataCompareIndex] = flib.returnTimeStringSec(CompareDataMax[DataCompareIndex])
    CompareData = {1:CompareDataMin,2:CompareDataMax,3:CompareDataAvg}
    CompareDataMatrix = {0: {0: '****', 1: 'Solo Def Size', 2: 'First Def Size', 3: 'Last Def Size', 4: 'No of Files', 5: 'Actual Time',}}
    for i in range(1,4):
        for j in range(0,5):
            if j == 0:
                if i == 1:
                    CompareDataMatrix.setdefault(i,[]).append('Min')
                elif i == 2:
                    CompareDataMatrix.setdefault(i,[]).append('Max')
                elif i == 3:
                    CompareDataMatrix.setdefault(i,[]).append('Avg')
            CompareDataMatrix.setdefault(i,[]).append(CompareData[i][j])
    statRequest['statData'] = StatProcessedData
    statRequest['lineChartData'] = StatlineChartData
    statRequest['processItems'] = processItems
    return render(request, 'build/statistics/statistics.html',{'type': str(type),'data':statRequest,'CompareData':CompareDataMatrix})

def processStat():
    try:
        data = flib.db_query("select JobID from stat_solo_diff_details order by JobID desc limit 1 ")
        if len(data) == 0 :
            lastJobID = 0
        else:
            lastJobID = data[0][0]
        sql = "SELECT jobinfo.JobID, jobinfo.DateCreated, jobinfo.EngineType, jobinfo.Flag, jobinfo.UserName, enginemaster.UpdateID, solo_details.SoloDefSize,solo_details.SoloVersion,solo_details.SoloFileCount,releaseinfo.vdb FROM jobinfo JOIN releaseinfo ON jobinfo.JobID = releaseinfo.JobID JOIN enginemaster ON jobinfo.JobID = enginemaster.JobID JOIN (SELECT solodetails.JobID JobID,solodetails.UpdateID UpdateID, SUM(solodetails.DefSize) SoloDefSize,downloaddetails.Version as SoloVersion,count(solodetails.DefID) as SoloFileCount FROM solodetails JOIN downloaddetails ON downloaddetails.JobID = solodetails.JobID AND downloaddetails.UpdateID = solodetails.UpdateID GROUP BY solodetails.JobID,solodetails.UpdateID )solo_details on solo_details.JobID = enginemaster.JobID and  solo_details.UpdateID = enginemaster.UpdateID  WHERE jobinfo.JobState = 6 HAVING jobinfo.JobID > "+str(lastJobID)+";"
        data = flib.db_query(sql)
        sql = 'select diffdtl.jobid,diffdtl.updateid,max(diffdtl.FromVersion) FirstPatchFromVersion,min(diffdtl.FromVersion) LastPatchFromVersion,(soloAddedFiles.soloAddedFileSum +(SELECT diffdetails.PatchFileSize FROM diffdetails WHERE diffdetails.jobid = diffdtl.jobid AND diffdetails.updateid =  diffdtl.updateid AND diffdetails.FromVersion = max(diffdtl.FromVersion)) ) as FirstPatch, (SELECT diffdetails.PatchFileSize FROM diffdetails WHERE diffdetails.jobid = diffdtl.jobid AND diffdetails.updateid =  diffdtl.updateid AND diffdetails.FromVersion = min(diffdtl.FromVersion) ) as LastPatch, soloAddedFiles.soloAddedFileSum  from ( 	SELECT diffdetails.JobID,diffdetails.UpdateID,diffdetails.FromVersion, sum(diffdetails.PatchFileSize) as sumPatch 	FROM diffdetails 	join releaseinfo on releaseinfo.jobid =   diffdetails.JobID group by diffdetails.JobID,diffdetails.UpdateID,diffdetails.FromVersion 	order by diffdetails.JobID desc,diffdetails.UpdateID,diffdetails.FromVersion desc 	) as diffdtl left join (SELECT solodetails.JobID,solodetails.UpdateID, SUM(solodetails.DefSize) AS soloAddedFileSum FROM solodetails WHERE solodetails.FileState = 1 group by solodetails.JobId,solodetails.UpdateId) as soloAddedFiles on  diffdtl.jobid = soloAddedFiles.jobid and diffdtl.updateid = soloAddedFiles.updateid group by diffdtl.jobid,diffdtl.updateid '
        dataDiff = flib.db_query(sql)
        if len(data) > 0 :
            cnt = 0
            #print(dataDiff)
            dataDiffArr = {}
            for item in dataDiff:
                dataDiffArr.setdefault(item[0],{})[item[1]] = item[4]
            sql = 'INSERT INTO `stat_solo_diff_details` (`JobID`, `EngineType`, `UpdateType`, `UpdateID`, `SoloSize`, `JobDate`,`User`,`FileCount`,`Version`,`Vdb`,`FirstDef`,`LastDef`) VALUES '
            for result in data:
                solodetails = str(result[6])
                try:
                    FirstDiff = dataDiffArr[result[0]][result[5]]
                except Exception as e:
                    FirstDiff = 0

                sql += '("'+str(result[0])+'","'+str(result[2])+'"," '+str(result[3])+'"," '+str(result[5])+'"," '+str(solodetails)+'","'+format(result[1])+'","'+str(result[4])+'","'+str(result[8])+'", "'+str(result[7])+'", "'+format(result[9])+'","'+str(FirstDiff)+'","'+str(flib.lastDiff(result[0],result[5]))+'"),'
                cnt = cnt + 1
            sql = sql[:-1]
            flib.db_insert(sql)
        data = flib.db_query("select JobID from stat_scripttime order by JobID desc limit 1 ")#for job time stat
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