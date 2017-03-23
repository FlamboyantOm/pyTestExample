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
    uidArr, UpdateId, UpdateIdName = [], '', ''
    try:
        qhstatdata = flib.getQhStatdata(request, type)
        rowData = EngineType_UpdateID(str(config.EngineTypeArr[type]), qhstatdata['checkDate'])
        if rowData:
            UpdateId = rowData[1][0]
        for uid in rowData:
            uidArr.append(uid[0])
        if 'u' in request.GET:
            UpdateId = request.GET['u']
    except Exception as e:
        t = ''
        print('Error', e)
    if type == 'qh':
        class data:
            pass
        query = 'select count(jobinfo.jobId) FROM jobinfo where jobinfo.EngineType = ' + str(config.EngineTypeArr[type]) + ' and jobinfo.JobState = 6'
        data_row = flib.db_query(query)
        if data_row:
            if data_row[0][0] < 2:
                data = 'Insufficiant Data'
                flib.setMetaInformation(request, 'Dashboard : ' + type.upper(),OrderedDict([('Dashboard : ' + type.upper(), '')]))
                return render(request, 'build/comingSoon.html', {'data': data})
        jobArry, dashboardData = [], []
        if not type in config.EngineTypeArr:
            return HttpResponse('Invalid request')
        updateIdDropdown = "<select id='updateIdDropdown'>"
        if qhstatdata is not None:
            update_id_string = flib.getUpdateIdName(str(tuple(uidArr)))
            
            if update_id_string:
                for uid in update_id_string:
                    if str(qhstatdata['update_id']) == str(uid['update_id']):
                        updateIdDropdown += '<option selected=selected value="' + str(uid['update_id']) + '" >' + str(uid['update_id_str']) + '</option>'
                        UpdateIdName = str(uid['update_id_str']) + '  ( ' + str(uid['update_id']) + ' )'
                    else:
                        updateIdDropdown += '<option value="' + str(uid['update_id']) + '" >' + str(uid['update_id_str']) + '</option>'
            else:
                updateIdDropdown += '<option value="" >( No Date Found )</option>'
            updateIdDropdown += "</select>"
            if qhstatdata['update_id'] == '' or UpdateIdName == '':
                messages.add_message(request, messages.WARNING,"<span class='glyphicon glyphicon-info-sign'></span><b> NO DATA FOUND.  Please select different date range</b>")
            elif 'u' in request.GET and request.GET['u'] == '' or UpdateIdName == '':
                messages.add_message(request, messages.WARNING,"<span class='glyphicon glyphicon-info-sign'></span><b> Please select UpdateID from dropdown</b>")
            else:
                dashboardData.append({'getQhDetails': JobDetails.getjobDetails(request, qhstatdata['checkDate'], str(UpdateId),str(config.EngineTypeArr[type])), 'details': UpdateidMinAvgMax(str(config.EngineTypeArr[type]), qhstatdata['checkDate'],str(UpdateId)), })


        flib.setMetaInformation(request, 'Dashboard : ' + type.upper(),OrderedDict([('Dashboard : ' + type.upper(), '')]))
        setattr(data,'updateIdDropdown',updateIdDropdown)
        setattr(data,'layout','build/statistics/qh/qh_dashboard.html')
        setattr(data,'report_date',qhstatdata)
        setattr(data,'update_id',UpdateIdName)
        setattr(data, 'from', qhstatdata['fromdate'])
        setattr(data, 'to', qhstatdata['todate'])
        return render(request, 'build/statistics/statistics_qh.html',{'type': str(type),'data':data,'dashboardData':dashboardData})
    if type == 'e2':
        class data:
            pass
        query = 'select count(jobinfo.jobId) FROM jobinfo where jobinfo.EngineType = ' + str(config.EngineTypeArr[type]) + ' and jobinfo.JobState = 6'
        data_row = flib.db_query(query)
        if data_row:
            if data_row[0][0] < 2:
                data = 'Insufficiant Data'
                flib.setMetaInformation(request, 'Dashboard : ' + type.upper(),OrderedDict([('Dashboard : ' + type.upper(), '')]))
                return render(request, 'build/comingSoon.html', {'data': data})
        jobArry, dashboardData = [], []
        if not type in config.EngineTypeArr:
            return HttpResponse('Invalid request')
        updateIdDropdown = "<select id='updateIdDropdown'>"
        if qhstatdata is not None:
            update_id_string = flib.getUpdateIdName( str(tuple(uidArr)))
            if update_id_string:
                for uid in update_id_string:
                    if str(qhstatdata['update_id']) == str(uid['update_id']):
                        updateIdDropdown += '<option selected=selected value="' + str(uid['update_id']) + '" >' + str(uid['update_id_str']) + '</option>'
                        UpdateIdName = str(uid['update_id_str']) + '  ( ' + str(uid['update_id']) + ' )'
                    else:
                        updateIdDropdown += '<option value="' + str(uid['update_id']) + '" >' + str(uid['update_id_str']) + '</option>'
            else:
                updateIdDropdown += '<option value="" > No Date Found </option>'
            updateIdDropdown += "</select>"
            if qhstatdata['update_id'] == '' or UpdateIdName == '':
                messages.add_message(request,messages.WARNING,"<span class='glyphicon glyphicon-info-sign'></span><b> NO DATA FOUND.  Please select different date range</b>")
            elif 'u' in request.GET and request.GET['u'] == '':
                messages.add_message(request,messages.WARNING,"<span class='glyphicon glyphicon-info-sign'></span><b> Please select UpdateID from dropdown</b>")
            else:
                dashboardData.append({'getE2Details': JobDetails.getjobDetails(request, qhstatdata['checkDate'], str(UpdateId), str(config.EngineTypeArr[type])),'e2Details': UpdateidMinAvgMax(str(config.EngineTypeArr[type]), qhstatdata['checkDate'], str(UpdateId)),})
        flib.setMetaInformation(request, 'Dashboard : ' + type.upper(),OrderedDict([('Dashboard : ' + type.upper(), '')]))
        setattr(data, 'updateIdDropdown', updateIdDropdown)
        setattr(data, 'layout', 'build/statistics/e2/e2_dashboard.html')
        setattr(data, 'report_date', qhstatdata)
        setattr(data, 'update_id', UpdateIdName)
        setattr(data, 'from', str(qhstatdata['fromdate']))
        setattr(data, 'to', str(qhstatdata['todate']))
        return render(request, 'build/statistics/statistics_e2.html',{'type': str(type), 'data': data,  'dashboardData': dashboardData})

class JobDetails:
    @staticmethod
    def SoloDiffPkgDetails(checkDate,UpdateId,type):
        try:
            rowData = getSoloDiffPkgDetails(checkDate,UpdateId,type)
            return rowData
        except Exception as e:
            print('Error(JobDetails.SoloDiffPkgDetails): ', e)

    def getjobDetails(request, checkDate, UpdateId, type):
        try:
            jobArray, SoloSize, PkgSize, MinDiffSize, MaxDiffSize, version,updateIDArr,scriptTime = [], '', '', '', '', '',{},''
            rowData = JobDetails.SoloDiffPkgDetails(checkDate,UpdateId,type)
            #scriptTime = stat_scripttime(str(config.EngineTypeArr[type]), qhstatdata['checkDate'])
            cnt = 0
            for qhRow in rowData:
                print(scriptTime[cnt])
                SoloSize = flib.getFileSizeMb(qhRow[2])
                if qhRow[5] != 0 and qhRow[6] != 0:
                    MinDiffSize,MaxDiffSize = flib.getFileSizeKb(qhRow[5]),flib.getFileSizeKb(qhRow[6])
                else:
                    MinDiffSize,MaxDiffSize = '-1','-1'
                version = str(qhRow[9])
                #version = str(qhRow[9]) + " (" + str(format(int(qhRow[9]), '02X')) + ")"
                noOfFiles = int(qhRow[8])
                jobArray.append({'JobID': str(qhRow[0]), 'JobDate': str(qhRow[1]), 'SoloSize': (SoloSize),'PkgType': str(qhRow[3]), 'PkgSize': str(qhRow[4]), 'MinDiffSize': (MinDiffSize),'MaxDiffSize': (MaxDiffSize), 'version': str(version), 'noOfFiles': noOfFiles})
                cnt += 1
            return jobArray
        except Exception as e:
            print('Error(JobDetails.getjobDetails): ', e)

    def getLineChartDetails(request, checkDate, UpdateId, type):
        try:
            jobArray, SoloSize, PkgSize, MinDiffSize, MaxDiffSize, version, updateIDArr = [], '', '', '', '', '', {}
            rowData = JobDetails.SoloDiffPkgDetails(checkDate, UpdateId, type)
            if rowData:
                for qhRow in rowData:
                    jobArray.append({ 'JobDate': qhRow[1], 'SoloSize': str(qhRow[2])})
                return jobArray
        except Exception as e:
            print('Error(JobDetails.getLineChartDetails): ', e)

def UpdateidMinAvgMax(type,checkDate,UpdateId):
    resultArr = {}
    result = qhStat_UpdateIDwiseMinMax(type, checkDate, UpdateId)
    if result:
        resultArr.update({'MIN_soloMin': flib.getFileSizeMb(result[0][0]),
                          'AVG_soloAvg': flib.getFileSizeMb(result[0][1]),
                          'MAX_soloMax': flib.getFileSizeMb(result[0][2]),
                          'MIN_MinDiff': flib.getFileSizeKb(result[0][3]),
                          'AVG_MinDiff': flib.getFileSizeKb(result[0][4]),
                          'MAX_MinDiff': flib.getFileSizeKb(result[0][5]),
                          'MIN_MaxDiff': flib.getFileSizeKb(result[0][6]),
                          'AVG_MaxDiff': flib.getFileSizeKb(result[0][7]),
                          'MAX_MaxDiff': flib.getFileSizeKb(result[0][8]),
                          'MIN_Makeupg': flib.getFileSizeKb(result[0][9]),
                          'AVG_Makeupg': flib.getFileSizeKb(result[0][10]),
                          'MAX_Makeupg': flib.getFileSizeKb(result[0][11]),
                          'MIN_NoOfFiles': int(round(result[0][12])),
                          'AVG_NoOfFiles': int(round(result[0][13])),
                          'MAX_NoOfFiles': int(round(result[0][14])),
                          })
    return resultArr

def processStat():
    try:
        data = flib.db_query("select JobID from stat_solo_diff_details order by JobID desc limit 1 ")
        if len(data) == 0 :
            lastJobID = 0
        else:
            lastJobID = data[0][0]
        #sql = "SELECT jobinfo.JobID, jobinfo.DateCreated, jobinfo.EngineType, jobinfo.Flag, jobinfo.UserName, enginemaster.UpdateID,solofilesum.FileSize,diffsizes.minPatchFileSize,diffsizes.maxPatchFileSize,downloaddetails.Version,solofilecnt.FileCount,releaseinfo.vdb FROM jobinfo JOIN releaseinfo ON jobinfo.JobID = releaseinfo.JobID LEFT JOIN enginemaster ON jobinfo.JobID = enginemaster.JobID JOIN ( SELECT solodetails.JobID JobID,solodetails.UpdateID UpdateID, SUM(solodetails.FileSize) FileSize FROM solodetails GROUP BY solodetails.JobID,solodetails.UpdateID) solofilesum ON solofilesum.UpdateID = enginemaster.UpdateID AND solofilesum.JobID = jobinfo.JobID JOIN ( SELECT solodetails.JobID JobID,solodetails.UpdateID UpdateID, COUNT(solodetails.JobID) FileCount FROM solodetails GROUP BY solodetails.JobID,solodetails.UpdateID) solofilecnt ON solofilecnt.UpdateID = enginemaster.UpdateID AND solofilecnt.JobID = jobinfo.JobID LEFT JOIN ( SELECT diffdetails.JobID,diffdetails.UpdateID, MIN(diffdetails.PatchFileSize) minPatchFileSize, MAX(diffdetails.PatchFileSize) maxPatchFileSize FROM diffdetails GROUP BY diffdetails.JobID,diffdetails.UpdateID) AS diffsizes ON diffsizes.UpdateID = enginemaster.UpdateID AND diffsizes.JobID = jobinfo.JobID LEFT JOIN downloaddetails ON downloaddetails.JobID = jobinfo.JobID AND downloaddetails.UpdateID = enginemaster.UpdateID WHERE jobinfo.JobState = 6  HAVING jobinfo.JobID > "+str(lastJobID)+";"
        sql = "SELECT jobinfo.JobID, jobinfo.DateCreated, jobinfo.EngineType, jobinfo.Flag, jobinfo.UserName, enginemaster.UpdateID,solofilesum.DefSize,diffsizes.minPatchFileSize,diffsizes.maxPatchFileSize,downloaddetails.Version,solofilecnt.FileCount,releaseinfo.vdb FROM jobinfo JOIN releaseinfo ON jobinfo.JobID = releaseinfo.JobID LEFT JOIN enginemaster ON jobinfo.JobID = enginemaster.JobID JOIN ( SELECT solodetails.JobID JobID,solodetails.UpdateID UpdateID, SUM(solodetails.DefSize) DefSize FROM solodetails GROUP BY solodetails.JobID,solodetails.UpdateID) solofilesum ON solofilesum.UpdateID = enginemaster.UpdateID AND solofilesum.JobID = jobinfo.JobID JOIN ( SELECT solodetails.JobID JobID,solodetails.UpdateID UpdateID, COUNT(solodetails.JobID) FileCount FROM solodetails GROUP BY solodetails.JobID,solodetails.UpdateID) solofilecnt ON solofilecnt.UpdateID = enginemaster.UpdateID AND solofilecnt.JobID = jobinfo.JobID LEFT JOIN ( SELECT diffdetails.JobID,diffdetails.UpdateID, MIN(diffdetails.PatchFileSize) minPatchFileSize, MAX(diffdetails.PatchFileSize) maxPatchFileSize FROM diffdetails GROUP BY diffdetails.JobID,diffdetails.UpdateID) AS diffsizes ON diffsizes.UpdateID = enginemaster.UpdateID AND diffsizes.JobID = jobinfo.JobID LEFT JOIN downloaddetails ON downloaddetails.JobID = jobinfo.JobID AND downloaddetails.UpdateID = enginemaster.UpdateID WHERE jobinfo.JobState = 6 HAVING jobinfo.JobID > "+str(lastJobID)+";"
        data = flib.db_query(sql)
        PkgSize,MinDiffSize,MaxDiffSize = 0,0,0
        if len(data) > 0 :
            cnt = 0
            sql = 'INSERT INTO `stat_solo_diff_details` (`JobID`, `EngineType`, `UpdateType`, `UpdateID`, `SoloSize`,`MinDiffSize`,`MaxDiffSize`, `JobDate`,`User`,`PkgType`,`PkgSize`,`FileCount`,`Version`,`Vdb`) VALUES '
            for result in data:
                solodetails = str(result[6])
                PkgSize = 0
                PkgType = ''
                if result[7] is not None:
                    MinDiffSize = result[7]
                if result[8] is not None:
                    MaxDiffSize = result[8]
                sql += '("'+str(result[0])+'","'+str(result[2])+'"," '+str(result[3])+'"," '+str(result[5])+'"," '+str(solodetails)+'", "'+str(MinDiffSize)+'", "'+str(MaxDiffSize)+'", "'+format(result[1])+'","'+str(result[4])+'"," '+str(PkgType)+'", "'+str(PkgSize)+'", "'+str(result[10])+'", "'+str(result[9])+'", "'+format(result[11])+'"),'
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

# Queries
def EngineType_UpdateID(type,checkDate=''):
    query = ''
    try:
        query = "SELECT DISTINCT UpdateID FROM stat_solo_diff_details WHERE stat_solo_diff_details.EngineType = "+str(type)+" " + str(checkDate) + " ORDER BY UpdateID "
        result = flib.db_query(query)
    except Exception as e:
        print('Error(QH_UpdateID): ',e)
    return result

def getSoloDiffPkgDetails(checkDate,updateID,type):
    sql = 'SELECT  stat_solo_diff_details.JobID, stat_solo_diff_details.JobDate, stat_solo_diff_details.SoloSize, stat_solo_diff_details.PkgType,stat_solo_diff_details.PkgSize,stat_solo_diff_details.MinDiffSize,stat_solo_diff_details.MaxDiffSize,stat_solo_diff_details.UpdateID,stat_solo_diff_details.FileCount,stat_solo_diff_details.version FROM stat_solo_diff_details WHERE stat_solo_diff_details.UpdateID = "'+str(updateID)+'" and stat_solo_diff_details.EngineType =  "'+str(type)+'" '+str(checkDate)+'  ORDER BY stat_solo_diff_details.UpdateID, stat_solo_diff_details.JobID DESC'
    result = flib.db_query(sql)
    return result

def qhStat_UpdateIDwiseMinMax(EngineType,checkDate,UpdateID):
    query = "SELECT  MIN(SoloSize), AVG(SoloSize), MAX(SoloSize),(SELECT MIN(MinDiffSize)FROM stat_solo_diff_details WHERE MinDiffSize <> 0  AND UpdateID = "+UpdateID+" AND EngineType = "+EngineType+" "+checkDate+") AS MIN_MinDiffSize,( SELECT AVG(MinDiffSize) FROM stat_solo_diff_details WHERE MinDiffSize <> 0 AND UpdateID = "+UpdateID+" AND EngineType = "+EngineType+" "+checkDate+") AS AVG_MinDiffSize,(SELECT MAX(MinDiffSize) FROM stat_solo_diff_details WHERE MinDiffSize <> 0 AND UpdateID = "+UpdateID+" AND EngineType = "+EngineType+" "+checkDate+") AS MAX_MinDiffSize,( SELECT MIN(MaxDiffSize) FROM stat_solo_diff_details WHERE MaxDiffSize  <> 0   AND UpdateID = "+UpdateID+" AND EngineType = "+EngineType+" "+checkDate+") AS MIN_MaxDiffSize,( SELECT AVG(MaxDiffSize) FROM stat_solo_diff_details WHERE MaxDiffSize <> 0 AND UpdateID = "+UpdateID+" AND EngineType = "+EngineType+" "+checkDate+") AS AVG_MaxDiffSize,( SELECT MAX(MaxDiffSize) FROM stat_solo_diff_details WHERE MaxDiffSize <> 0 AND UpdateID = "+UpdateID+" AND EngineType = "+EngineType+" "+checkDate+") AS MAX_MaxDiffSize, MIN(PkgSize), AVG(PkgSize),MAX(PkgSize),MIN(FileCount), AVG(FileCount), MAX(FileCount) FROM stat_solo_diff_details s1 WHERE UpdateID = "+UpdateID+" AND EngineType = "+EngineType+" "+checkDate
    result = flib.db_query(query)
    return result


def stat_scripttime(EngineType,checkDate):
    query = "select JobId,ScriptTime,ActualTimeTaken from stat_scripttime where  EngineType = "+str(EngineType)+" "+str(checkDate)+" ORDER BY JobID DESC"
    result = flib.db_query(query)
    return result
