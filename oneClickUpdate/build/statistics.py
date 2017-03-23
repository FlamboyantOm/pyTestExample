from django.conf import settings
import random, datetime, time, json
from collections import OrderedDict
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import *
from . import flib, config
from datetime import datetime as datea
from django.shortcuts import render_to_response
from django.contrib import messages
from django.core.urlresolvers import reverse


@login_required(login_url='/login/')
def statistics(request, type):
    processStat(request)
    statRequest = flib.statRequest(request, type)
    query = 'SELECT count(jobinfo.jobId) FROM jobinfo where jobinfo.EngineType = ' + str(config.EngineTypeArr[type]) + ' and jobinfo.JobState = 6'
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
    sql = "SELECT stat_solo_diff_details.*, IFNULL(stat_scripttime.ActualTimeTaken, 0) FROM stat_solo_diff_details  left join stat_scripttime on stat_solo_diff_details.JobID = stat_scripttime.JobID where stat_solo_diff_details.UpdateID = '" + str(statRequest['update_id']) + "' and stat_solo_diff_details.JobDate BETWEEN '" + str(statRequest['from_date']) + " 00:00:00' AND '" + str(statRequest['to_date']) + " 23:59:59'"
    StatData  = flib.db_query(sql)
    statRequest['updateIdDropdown'] = updateIdDropdown
    statRequest['layout'] = 'build/statistics/dashboard.html'
    if len(StatData) == 0:
        messages.add_message(request, messages.ERROR,"<span class='glyphicon glyphicon-info-sign'></span><b> No record available. Please select different date range.</b>")
        return render(request, 'build/statistics/statistics.html',{'type': str(type), 'data': statRequest})
    StatProcessedData,CompareDataMin,CompareDataMax,CompareDataAvg,StatlineChartData = [],{},{},{},[]
    CompareDataAvg[0],CompareDataAvg[1],CompareDataAvg[2],CompareDataAvg[3],CompareDataAvg[4],CompareDataAvg[5],CompareDataAvg[6],CompareDataAvg[7],i = 0,0,0,0,0,0,0,0,0
    for item in StatData:
        firstChangeBy,lastChangeBy = 0,0
        if item[12] != 0 and item[9] != 0 and item[17] != 0 and item[14] != 0:
            firstChangeBy = format(100 - (item[12] / item[9]) * 100, '.2f')
            lastChangeBy = format(100 - (item[17] / item[14]) * 100, '.2f')
        processItem = [item[0], item[4], item[7], item[8],flib.getFileSizeMb(item[9]),item[10],item[11],flib.getFileSizeMb(item[12]),item[13],flib.getFileSizeMb(item[14]),item[15],item[16],flib.getFileSizeMb(item[17]),flib.returnTimeStringSec(item[18]),firstChangeBy,lastChangeBy,]
        lineChart = [item[0], str(item[5]), item[12], item[9]]
        print(item[0],item[4], str(item[5]), item[12], item[9])
        if i == 0 :
            i = 1
            CompareDataMin[0],CompareDataMin[1],CompareDataMin[2],CompareDataMin[3],CompareDataMin[4],CompareDataMin[5],CompareDataMin[6],CompareDataMin[7] = item[9],item[14],item[10],item[12],item[13],item[18],item[8],item[17]
            CompareDataMax[0],CompareDataMax[1],CompareDataMax[2],CompareDataMax[3],CompareDataMax[4],CompareDataMax[5],CompareDataMax[6],CompareDataMax[7] = item[9],item[14],item[10],item[12],item[13],item[18],item[8],item[17]
        else:
            if item[9] < CompareDataMin[0]:CompareDataMin[0] = item[9]
            if item[14] < CompareDataMin[1]:CompareDataMin[1] = item[14]
            if item[10] < CompareDataMin[2]:CompareDataMin[2] = item[10]
            if item[12] < CompareDataMin[3]:CompareDataMin[3] = item[12]
            if item[13] < CompareDataMin[4]:CompareDataMin[4] = item[13]
            if item[18] < CompareDataMin[5]:CompareDataMin[5] = item[18]
            if item[8] < CompareDataMin[6]:CompareDataMin[6] = item[8]
            if item[17] < CompareDataMin[7]:CompareDataMin[7] = item[17]

            if item[9] > CompareDataMax[0]:CompareDataMax[0] = item[9]
            if item[14] > CompareDataMax[1]:CompareDataMax[1] = item[14]
            if item[10] > CompareDataMax[2]:CompareDataMax[2] = item[10]
            if item[12] > CompareDataMax[3]:CompareDataMax[3] = item[12]
            if item[13] > CompareDataMax[4]:CompareDataMax[4] = item[13]
            if item[18] > CompareDataMax[5]:CompareDataMax[5] = item[18]
            if item[8] > CompareDataMax[6]:CompareDataMax[6] = item[8]
            if item[17] > CompareDataMax[7]:CompareDataMax[7] = item[17]

        CompareDataAvg[0]+=item[9]
        CompareDataAvg[1]+=item[14]
        CompareDataAvg[2]+=item[10]
        CompareDataAvg[3]+=item[12]
        CompareDataAvg[4]+=item[13]
        CompareDataAvg[5]+=item[18]
        CompareDataAvg[6]+=item[8]
        CompareDataAvg[7]+=item[17]
        StatProcessedData.append(processItem)
        StatlineChartData.append(lineChart)
    #print('raw',CompareDataAvg)
    for DataCompareIndex in CompareDataAvg:
        if DataCompareIndex == 0:
            #First Update Details - Solo Size
            CompareDataAvg[DataCompareIndex] = flib.getFileSizeMb(CompareDataAvg[DataCompareIndex] / len(StatData))
            CompareDataMin[DataCompareIndex] = flib.getFileSizeMb(CompareDataMin[DataCompareIndex])
            CompareDataMax[DataCompareIndex] = flib.getFileSizeMb(CompareDataMax[DataCompareIndex])
        elif DataCompareIndex == 1:
            #Last Update Details -  	Solo Size
            CompareDataAvg[DataCompareIndex] = flib.getFileSizeMb(CompareDataAvg[DataCompareIndex] / len(StatData))
            CompareDataMin[DataCompareIndex] = flib.getFileSizeMb(CompareDataMin[DataCompareIndex])
            CompareDataMax[DataCompareIndex] = flib.getFileSizeMb(CompareDataMax[DataCompareIndex])
        elif DataCompareIndex == 2:
            #first solo size kb
            CompareDataAvg[DataCompareIndex] = flib.getFileSizeKb(CompareDataAvg[DataCompareIndex] / len(StatData))
            CompareDataMin[DataCompareIndex] = flib.getFileSizeKb(CompareDataMin[DataCompareIndex])
            CompareDataMax[DataCompareIndex] = flib.getFileSizeKb(CompareDataMax[DataCompareIndex])
        elif DataCompareIndex == 3:
            #First Update Details -  	Diff Size
            CompareDataAvg[DataCompareIndex] =  flib.getFileSizeMb(CompareDataAvg[DataCompareIndex] / len(StatData))
            CompareDataMin[DataCompareIndex] =  flib.getFileSizeMb(CompareDataMin[DataCompareIndex])
            CompareDataMax[DataCompareIndex] = flib.getFileSizeMb(CompareDataMax[DataCompareIndex])
        elif DataCompareIndex == 4:
            #Last Update Details - File Count
            CompareDataAvg[DataCompareIndex] = str(round(CompareDataAvg[DataCompareIndex] / len(StatData)))+' Files'
            CompareDataMin[DataCompareIndex] = str(CompareDataMin[DataCompareIndex])+' Files'
            CompareDataMax[DataCompareIndex] = str(CompareDataMax[DataCompareIndex])+' Files'
        elif DataCompareIndex == 5:
            # Actual time taken
            CompareDataAvg[DataCompareIndex] = flib.returnTimeStringSec(CompareDataAvg[DataCompareIndex] / len(StatData))
            CompareDataMin[DataCompareIndex] =  flib.returnTimeStringSec(CompareDataMin[DataCompareIndex])
            CompareDataMax[DataCompareIndex] = flib.returnTimeStringSec(CompareDataMax[DataCompareIndex])
        elif DataCompareIndex == 6:
            # First Update Details - first file count
            CompareDataAvg[DataCompareIndex] = str(round(CompareDataAvg[DataCompareIndex] / len(StatData)))+' Files'
            CompareDataMin[DataCompareIndex] = str(CompareDataMin[DataCompareIndex])+' Files'
            CompareDataMax[DataCompareIndex] = str(CompareDataMax[DataCompareIndex])+' Files'
        elif DataCompareIndex == 7:
            #Last Update Details -  	Diff Size
            CompareDataAvg[DataCompareIndex] =  flib.getFileSizeMb(CompareDataAvg[DataCompareIndex] / len(StatData))
            CompareDataMin[DataCompareIndex] =  flib.getFileSizeMb(CompareDataMin[DataCompareIndex])
            CompareDataMax[DataCompareIndex] = flib.getFileSizeMb(CompareDataMax[DataCompareIndex])
    CompareData = {1:CompareDataMin,2:CompareDataMax,3:CompareDataAvg}
    CompareDataMatrix = {0: {0: '****', 1: 'Solo First Def  22Size', 2: 'Solo Last Def Size', 3: 'First Def Size', 4: 'Last Def Size', 5: 'No of Files', 6: 'Actual Time',}}
    CompareDataMatrix = {}
    for i in range(1,4):
        for j in range(0,8):
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
    return render(request, 'build/statistics/statistics.html',{'type': str(type),'data':statRequest,'CompareData':CompareDataMatrix})


@user_passes_test(lambda u: u.groups.filter(name='ViewAndWrite'), login_url='/')
def processStat(request):
    try:
        data = flib.db_query("SELECT JobID from stat_solo_diff_details order by JobID desc limit 1 ")
        if len(data) == 0 :
            lastJobID = 0
        else:
            lastJobID = data[0][0]
        #lastJobID = 140
        sql = "SELECT jobinfo.JobID, jobinfo.EngineType, jobinfo.Flag, enginemaster.UpdateID,jobinfo.DateCreated,  jobinfo.UserName,  releaseinfo.vdb, solo_details.SoloVersion FROM jobinfo JOIN releaseinfo ON jobinfo.JobID = releaseinfo.JobID JOIN enginemaster ON jobinfo.JobID = enginemaster.JobID JOIN (SELECT solodetails.JobID JobID,solodetails.UpdateID UpdateID, SUM(solodetails.DefSize) SoloDefSize,downloaddetails.Version as SoloVersion,count(solodetails.DefID) as SoloFileCount FROM solodetails JOIN downloaddetails ON downloaddetails.JobID = solodetails.JobID AND downloaddetails.UpdateID = solodetails.UpdateID GROUP BY solodetails.JobID,solodetails.UpdateID )solo_details on solo_details.JobID = enginemaster.JobID and  solo_details.UpdateID = enginemaster.UpdateID  WHERE jobinfo.JobState = 6 HAVING jobinfo.JobID > "+str(lastJobID)+";"
        data = flib.db_query(sql)
        if len(data) > 0 :
            cnt = 0
            sql = 'SELECT statdtl.jobid, statdtl.updateid,soloFirstFileCnt,soloFirstDefSize, statdtl.FirstPatchFromVersion, (( SELECT COUNT(diffpatchdetails.DefID) FROM diffpatchdetails WHERE diffpatchdetails.JobId = statdtl.jobid AND diffpatchdetails.UpdateId = statdtl.updateid AND diffpatchdetails.FromVersion = FirstPatchFromVersion)+soloAddedFileCnt) AS FirstDefFileCnt, statdtl.FirstPatch, statdtl.LastPatchFromVersion  FROM ( SELECT diffdtl.jobid,diffdtl.updateid, MAX(diffdtl.FromVersion) FirstPatchFromVersion, MIN(diffdtl.FromVersion) LastPatchFromVersion, 	soloAddedFileCnt, 	(soloAddedFiles.soloAddedFileSum +( SELECT diffdetails.PatchFileSize FROM diffdetails WHERE diffdetails.jobid = diffdtl.jobid AND diffdetails.updateid = diffdtl.updateid AND diffdetails.FromVersion = MAX(diffdtl.FromVersion))) AS FirstPatch, soloFirstFileCnt,soloFirstDefSize FROM ( SELECT diffdetails.JobID,diffdetails.UpdateID,diffdetails.FromVersion, SUM(diffdetails.PatchFileSize) AS sumPatch FROM diffdetails JOIN releaseinfo ON releaseinfo.jobid = diffdetails.JobID and releaseinfo.JobID > "'+str(lastJobID)+'" GROUP BY diffdetails.JobID,diffdetails.UpdateID,diffdetails.FromVersion ORDER BY diffdetails.JobID DESC,diffdetails.UpdateID,diffdetails.FromVersion DESC 	) AS diffdtl LEFT JOIN ( SELECT solodetails.JobID,solodetails.UpdateID, SUM(solodetails.DefSize) AS soloAddedFileSum, COUNT(solodetails.DefID) soloAddedFileCnt FROM solodetails WHERE solodetails.FileState = 1 GROUP BY solodetails.JobId,solodetails.UpdateId) AS soloAddedFiles ON diffdtl.jobid = soloAddedFiles.jobid AND diffdtl.updateid = soloAddedFiles.updateid LEFT JOIN ( SELECT solodetails.JobID, solodetails.UpdateID, COUNT(solodetails.DefID) soloFirstFileCnt,  SUM(solodetails.DefSize) soloFirstDefSize FROM solodetails where solodetails.FileState > 0  group by solodetails.JobID, solodetails.UpdateID ) soloDefDtl ON diffdtl.jobid = soloDefDtl.jobid AND diffdtl.updateid = soloDefDtl.updateid  GROUP BY diffdtl.jobid,diffdtl.updateid ) AS statdtl  '
            dataDiff = flib.db_query(sql)
            dataDiffArr = {}
            for item in dataDiff:
                dataDiffArr.setdefault(item[0],{})[item[1]] = item
            sql = 'INSERT INTO `stat_solo_diff_details` (`JobID`, `EngineType`, `UpdateType`, `UpdateID`,`JobDate`,`User`,`Vdb`,`SoloVersion` ,`SoloFirstFileCnt` ,`SoloFirstDefSize` ,`DefFirstVersion` ,`DefFirstFileCnt` ,`DefFirstDefSize` ,`SoloLastFileCnt` ,`SoloLastDefSize` ,`DefLastVersion` ,`DefLastFileCnt` ,`DefLastDefSize`) VALUES '
            for result in data:
                try :
                    curResult = dataDiffArr[result[0]][result[3]]
                except Exception as E:
                    print("err",E)
                    print("err",result[0],result[3],result)
                    continue
                SoloLastDefSize, LastDiffFileCnt = flib.lastSoloDiffDtl(result[0],result[3])
                lastDiffSize,LastDiffVer = flib.lastDiffSize(result[0],result[3])
                sql += '("'+str(result[0])+'","'+str(result[1])+'"," '+str(result[2])+'"," '+str(result[3])+'", " '+str(result[4])+'", " '+str(result[5])+'", " '+str(result[6])+'" , " '+str(result[7])+'"," '+str(curResult[2])+'"," '+str(curResult[3])+'"," '+str(curResult[4])+'"," '+str(curResult[5])+'"," '+str(curResult[6])+'", "'+LastDiffFileCnt+'","'+str(SoloLastDefSize)+'"," '+str(LastDiffVer)+'", "'+str(LastDiffFileCnt)+'","'+str(lastDiffSize)+'" ),'
                cnt = cnt + 1
            sql = sql[:-1]
            flib.db_insert(sql)
        data = flib.db_query("SELECT JobID from stat_scripttime order by JobID desc limit 1 ")#for job time stat
        if len(data) == 0:
            lastJobID = 0
        else:
            lastJobID = data[0][0]
        sql = "SELECT jobstatedetails.JobId,jobinfo.EngineType, jobinfo.Flag, TIMESTAMPDIFF(SECOND,min(StartTime),max(StartTime)) as totaltime, sum(jobstatedetails.TimeTaken) as script, jobinfo.DateCreated from jobstatedetails,jobinfo where jobinfo.JobID = jobstatedetails.JobID  and jobinfo.JobState = 6 and jobinfo.JobID > "+str(lastJobID)+" group by jobinfo.JobID  order by jobinfo.JobID asc"
        data = flib.db_query(sql)
        if data != None and len(data) > 0:
            sql='INSERT INTO `stat_scripttime` (`JobID`, `EngineType`, `UpdateType`, `ActualTimeTaken`, `ScriptTime`, `JobDate`) VALUES '
            for result in data:
                sql += '(' + str(result[0]) + ',' + str(result[1]) + ', ' + str(result[2]) + ', ' + str(result[3]) + ', ' + str(result[4]) + ',"' + format(result[5]) + '"),'
            sql = sql[:-1]
            flib.db_insert( sql)
    except Exception as e:
        print ("Error(processStat): ",e)