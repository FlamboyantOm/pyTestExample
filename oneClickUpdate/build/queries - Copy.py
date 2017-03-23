from . import flib, config
#State Queries
def stat_summeryDetails(EngineType,checkDate,updateID = ''):
    if updateID:
        #query = "select count(JobID), sum(UpdateType = '1'), sum(UpdateType = '3'), (SELECT min(SoloSize) from stat_solo_diff_details where UpdateID = %s),max(SoloSize),User,UpdateID from stat_solo_diff_details where EngineType = %s %s  group by UpdateID,User order by count(JobID)" % (updateID, EngineType, checkDate)
        query = "SELECT COUNT(JobID), SUM(UpdateType = '1'), SUM(UpdateType = '3'),(SELECT MIN(SoloSize) FROM stat_solo_diff_details WHERE UpdateID = "+str(updateID)+" AND EngineType = "+EngineType+" "+checkDate+") AS mindif, (SELECT MAX(SoloSize) FROM stat_solo_diff_details WHERE UpdateID = "+str(updateID)+" AND EngineType = "+EngineType+" "+checkDate+") AS Maxdif ,User,UpdateID FROM stat_solo_diff_details s1 WHERE EngineType = 1 "+checkDate+" GROUP BY UpdateID"
    else:
        query = "select count(JobID), sum(UpdateType = '1'), sum(UpdateType = '3'), min(SoloSize),max(SoloSize),User,UpdateID from stat_solo_diff_details where EngineType = %s %s group by UpdateID,User order by count(JobID)" % (EngineType,checkDate)
    result = flib.db_query(query)
    return result

def get_LatestJobID(EngineType):
    query = "select JobID from stat_solo_diff_details where EngineType = %s group by JobID order by JobID desc limit 0,1" % (EngineType)
    return flib.db_query(query)[0][0]

def stat_UpdateIDwiseMinMax(EngineType,checkDate):
    query = "SELECT s1.UpdateID," \
            "(SELECT JobID FROM stat_solo_diff_details WHERE UpdateID = s1.UpdateID and  EngineType = "+(EngineType)+" "+checkDate+"  ORDER BY SoloSize DESC LIMIT 1) AS solo_max_id, MAX(SoloSize) AS max_SoloSize," \
            "(SELECT JobID FROM stat_solo_diff_details WHERE UpdateID = s1.UpdateID and  EngineType = "+(EngineType)+" "+checkDate+"  ORDER BY SoloSize LIMIT 1) AS solo_min_id,MIN(SoloSize) AS min_SoloSize," \
            "(SELECT JobID FROM stat_solo_diff_details WHERE UpdateID = s1.UpdateID and  EngineType = "+(EngineType)+" "+checkDate+"  ORDER BY MinDiffSize DESC LIMIT 1) AS Max_diff_id, MAX(MinDiffSize) AS max_diff," \
            "(SELECT JobID FROM stat_solo_diff_details WHERE UpdateID = s1.UpdateID and  EngineType = "+(EngineType)+" "+checkDate+"  ORDER BY MinDiffSize LIMIT 1) AS min_diff__id,MIN(MinDiffSize) AS min_diff " \
            "FROM stat_solo_diff_details s1 WHERE EngineType = "+(EngineType)+" "+checkDate+"  group by UpdateID "
    result = flib.db_query(query)
    return result

def stat_scripttime(EngineType,checkDate):
    query = "select JobId,ScriptTime,ActualTimeTaken,UpdateType,JobDate from stat_scripttime where  EngineType = %s %s  group by JobID,ScriptTime,ActualTimeTaken,UpdateType,JobDate order by JobID asc" % (EngineType,checkDate)
    result = flib.db_query(query)
    return result

def stat_sizeArray(EngineType,checkDate):
    if EngineType == '2':
        e2For32Bit = "SELECT JobID, SoloSize,User,UpdateType,JobDate, MinDiffSize,MaxDiffSize FROM stat_solo_diff_details WHERE UpdateID = 4 AND EngineType = " + EngineType + " " + checkDate + "  ORDER BY UpdateID,JobID"
        e2For32BitData = flib.db_query(e2For32Bit)
        e2For64Bit = "SELECT JobID, SoloSize,User,UpdateType,JobDate, MinDiffSize,MaxDiffSize FROM stat_solo_diff_details WHERE UpdateID = 5 AND EngineType = " + EngineType + " " + checkDate + "  ORDER BY UpdateID,JobID"
        e2For64BitData = flib.db_query(e2For64Bit)
        return {'e2For32Bit':e2For32BitData,'e2For64Bit': e2For64BitData}
    else:
        qh_updateid_size = []
       # for QH_UpdateID in config.QH_UpdateID:
        #    e2For32Bit = "SELECT JobID, SoloSize,User,UpdateType,JobDate, MinDiffSize,MaxDiffSize FROM stat_solo_diff_details WHERE UpdateID = " + str(QH_UpdateID) + " AND EngineType = " + EngineType + " " + checkDate + "  ORDER BY UpdateID,JobID"
        #    SizeData = flib.db_query(e2For32Bit)
        #    qh_updateid_size.append({'UpdateID': QH_UpdateID, 'SizeData': SizeData})
        return {'qh_updateid_size': qh_updateid_size}

def frequentFileData(checkDate,updateID):
    query = ''
    if updateID == 4:
        query = "SELECT FileName, COUNT(JobID) as cnt FROM ( SELECT deffileinfo.FileName FileName, jobinfo.JobID FROM solodetails INNER JOIN jobinfo ON jobinfo.JobID=solodetails.JobID INNER JOIN deffileinfo ON (solodetails.DefID = deffileinfo.DefID AND solodetails.UpdateID = deffileinfo.UpdateID) WHERE jobinfo.JobState = 6 AND deffileinfo.FileName != 'update.txt'  "+str(checkDate)+"  AND solodetails.UpdateID = "+str(updateID)+" ) AS FileTable GROUP BY FileName  "
    if updateID == 5:
        query = "SELECT FileName, COUNT(JobID) as cnt FROM ( SELECT deffileinfo.FileName FileName, jobinfo.JobID FROM solodetails INNER JOIN jobinfo ON jobinfo.JobID=solodetails.JobID INNER JOIN deffileinfo ON (solodetails.DefID = deffileinfo.DefID AND solodetails.UpdateID = deffileinfo.UpdateID) WHERE jobinfo.JobState = 6 AND deffileinfo.FileName != 'update.txt'  "+str(checkDate)+"  AND solodetails.UpdateID = "+str(updateID)+" ) AS FileTable GROUP BY FileName "
    result = flib.db_query(query)
    return result

def newlyIntroducedFileData(checkDate,updateID):
    query = ''
    if updateID == 4:
        query = "select FileName,count(*) from (SELECT deffileinfo.FileName FileName, jobinfo.JobID FROM solodetails INNER JOIN jobinfo ON jobinfo.JobID=solodetails.JobID INNER JOIN deffileinfo ON  (solodetails.DefID = deffileinfo.DefID and solodetails.UpdateID = deffileinfo.UpdateID) WHERE jobinfo.JobState = 6 AND  solodetails.FileState = 1 "+str(checkDate)+"  AND solodetails.UpdateID = "+str(updateID)+" ) as FileTable group by FileName "
    if updateID == 5:
        query = "select FileName,count(*) from (SELECT deffileinfo.FileName FileName, jobinfo.JobID FROM solodetails INNER JOIN jobinfo ON jobinfo.JobID=solodetails.JobID INNER JOIN deffileinfo ON  (solodetails.DefID = deffileinfo.DefID and solodetails.UpdateID = deffileinfo.UpdateID) WHERE jobinfo.JobState = 6 AND  solodetails.FileState = 1 "+str(checkDate)+"  AND solodetails.UpdateID = "+str(updateID)+" ) as FileTable group by FileName "
    result = flib.db_query(query)
    return result



# QH Queries
def EngineType_UpdateID(type,checkDate=''):
    query = ''
    try:
        query = "SELECT DISTINCT UpdateID FROM stat_solo_diff_details WHERE stat_solo_diff_details.EngineType = "+str(type)+" " + str(checkDate) + " ORDER BY UpdateID "
        result = flib.db_query(query)
    except Exception as e:
        print('Error(QH_UpdateID): ',e)
    return result

def qhSoloDiffPkgDetails(checkDate,updateID,type):
    query = ''
    query = "SELECT stat_solo_diff_details.JobID, stat_solo_diff_details.JobDate, stat_solo_diff_details.SoloSize, stat_solo_diff_details.PkgType,stat_solo_diff_details.PkgSize, stat_solo_diff_details.MinDiffSize,stat_solo_diff_details.MaxDiffSize, stat_solo_diff_details.UpdateID, stat_solo_diff_details.FileCount, stat_solo_diff_details.version FROM stat_solo_diff_details WHERE stat_solo_diff_details.UpdateID in ("+str(updateID)+") AND stat_solo_diff_details.EngineType = "+type+" "+str(checkDate)+" ORDER BY stat_solo_diff_details.UpdateID, stat_solo_diff_details.JobID DESC"
    result = flib.db_query(query)
    return result

def qhStat_UpdateIDwiseMinMax(EngineType,checkDate,UpdateID):
    query = "SELECT  MIN(SoloSize), AVG(SoloSize), MAX(SoloSize),(SELECT MIN(MinDiffSize)FROM stat_solo_diff_details WHERE MinDiffSize <> 0  AND UpdateID = "+UpdateID+" AND EngineType = "+EngineType+" "+checkDate+") AS MIN_MinDiffSize,( SELECT AVG(MinDiffSize) FROM stat_solo_diff_details WHERE MinDiffSize <> 0 AND UpdateID = "+UpdateID+" AND EngineType = "+EngineType+" "+checkDate+") AS AVG_MinDiffSize,(SELECT MAX(MinDiffSize) FROM stat_solo_diff_details WHERE MinDiffSize <> 0 AND UpdateID = "+UpdateID+" AND EngineType = "+EngineType+" "+checkDate+") AS MAX_MinDiffSize,( SELECT MIN(MaxDiffSize) FROM stat_solo_diff_details WHERE MaxDiffSize  <> 0   AND UpdateID = "+UpdateID+" AND EngineType = "+EngineType+" "+checkDate+") AS MIN_MaxDiffSize,( SELECT AVG(MaxDiffSize) FROM stat_solo_diff_details WHERE MaxDiffSize <> 0 AND UpdateID = "+UpdateID+" AND EngineType = "+EngineType+" "+checkDate+") AS AVG_MaxDiffSize,( SELECT MAX(MaxDiffSize) FROM stat_solo_diff_details WHERE MaxDiffSize <> 0 AND UpdateID = "+UpdateID+" AND EngineType = "+EngineType+" "+checkDate+") AS MAX_MaxDiffSize, MIN(PkgSize), AVG(PkgSize),MAX(PkgSize),MIN(FileCount), AVG(FileCount), MAX(FileCount) FROM stat_solo_diff_details s1 WHERE UpdateID = "+UpdateID+" AND EngineType = "+EngineType+" "+checkDate
    result = flib.db_query(query)
    return result