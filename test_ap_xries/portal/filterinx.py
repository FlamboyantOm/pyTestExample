from django.shortcuts import *
from django.contrib.auth.decorators import login_required
from . import lib,constant_data,permissions
from .userview import userObj
from collections import OrderedDict
import json,datetime,os,subprocess,re
from ast import literal_eval
from apex import settings


@login_required(login_url='/login/')
def filter_inx(request):
    lib.setMetaInformation(request, [('Export'), ('inx_view')], 'Filter Signature', OrderedDict([('Filter Signature', '')]))

    Perm_Type_Arr = permissions.checkclusterTypePermission(request)

    clusterType = constant_data.CLUSTER_TYPE

    data = userObj()
    setattr(data, 'clusterType', clusterType)

    if len(Perm_Type_Arr):
        for key in list(clusterType.keys()):
            if key not in Perm_Type_Arr:
                clusterType.pop(key)
    else:
        setattr(data, 'noTypePerm', 1)
        return render(request, 'portal/filter_report.html',{ 'data':data})

    return render(request, 'portal/filter_report.html',{ 'data':data})


def filter_list_ajax(request):

    if int(request.POST['Type']) not in permissions.checkclusterTypePermission(request):
        data = ''
        return HttpResponse(json.dumps(data), content_type='application/json')

    source = sorted(constant_data.CLUSTER_SOURCE.items())
    progress = sorted(constant_data.CLUSTER_PROGRESS.items())

    state = sorted(constant_data.SIG_STATE.items())

    status = [[1,'silent'], [0,'non-silent']]
    priority = sorted(constant_data.CLUSTER_PRIORITY.items())

    sql ='select DISTINCT tag_list.TagID,record_tag.TagName from tag_list join qh_sig_status on qh_sig_status.SIG_ID_FK = tag_list.SigID and qh_sig_status.SIG_TYPE_FK='+request.POST['Type']+' AND qh_sig_status.MARK_DELETED=0 join record_tag on record_tag.TagID=tag_list.TagID ORDER BY tag_list.TagID;'

    sigTags = lib.db_query(sql)

    sql  ='select DISTINCT cluster.CreatedBy,cluster.ClusterAssignedTo,agerecord.AuthorName from cluster JOIN agerecord ON agerecord.ClusterId = cluster.ClusterID  AND cluster.Status = 1  JOIN qh_sig_status ON qh_sig_status.SIG_ID_FK=agerecord.Record_ID_FK AND qh_sig_status.MARK_DELETED = 0 where cluster.`Type` = '+request.POST['Type']+';'
    clusterSigUser = lib.db_query(sql)

    createdUser = []
    assignUser = []
    sigAddedUser = []
    if clusterSigUser:
        for user in clusterSigUser:
            if user[0] not in createdUser:
                createdUser.append(user[0])
            if user[1] not in assignUser:
                assignUser.append(user[1])
            if user[2] not in sigAddedUser and user[2]:
                sigAddedUser.append(user[2])

    data = {'tags':sigTags,'createdUser':createdUser,'assignUser':assignUser,'source':source,'progress':progress,'state':state,'status':status,'priority':priority,'sigAddedUser':sigAddedUser,'totalRecord':len(clusterSigUser)}
    return HttpResponse(json.dumps(data), content_type='application/json')

def filter_signature_list_ajax(request):

    if int(request.POST['Type']) not in permissions.checkclusterTypePermission(request):
        return HttpResponse(json.dumps({'sigAddedUser': ''}),content_type='application/json')

    filterData = {}
    where_txt = 'WHERE qh_sig_status.SIG_TYPE_FK='+str(request.POST['Type'])

    if request.POST.get('createdUser'):
         createdUser = "(" + str(request.POST.get('createdUser').split(','))[1:-1]+ ")"
         where_txt += ' AND cluster.CreatedBy IN '+str(createdUser)
         filterData.update({'createdUser': createdUser})
    if request.POST.get('assignUser'):
        assignUser = "(" + str(request.POST.get('assignUser').split(','))[1:-1]+ ")"
        where_txt += ' AND cluster.ClusterAssignedTo IN '+str(assignUser)
        filterData.update({'assignUser': assignUser})

    if request.POST.get('source'):
        source = "(" + str(request.POST.get('source').split(','))[1:-1]+ ")"
        where_txt += ' AND cluster.Source IN '+str(source)
        filterData.update({'source': source})
    if request.POST.get('progress'):
        progress = "(" + str(request.POST.get('progress').split(','))[1:-1]+ ")"
        where_txt += ' AND cluster.Progress IN '+str(progress)
        filterData.update({'progress': progress})
    if request.POST.get('priority'):
        priority = "(" + str(request.POST.get('priority').split(','))[1:-1]+ ")"
        where_txt += ' AND cluster.Priority IN '+str(priority)
        filterData.update({'priority': priority})
    if request.POST.get('clusterDate'):
        if len(request.POST.get('clusterDate').split(' to ')) == 2:
            filterData.update({'startDate': request.POST.get('clusterDate').split(' to ')[0],'endDate': request.POST.get('clusterDate').split(' to ')[1]})
            where_txt += ' AND CAST(cluster.CreatedDate as DATE) BETWEEN "' +request.POST.get('clusterDate').split(' to ')[0] + '" AND "' + request.POST.get('clusterDate').split(' to ')[1] + '"'

    # if request.POST.get('state'):
    #     state = "(" + str(request.POST.get('state').split(','))[1:-1] + ")"
    #     where_txt += ' AND agerecord.SigState IN ' + str(state)
    #     filterData.update({'state': state})

    # if request.POST.get('sigAddedUser'):
    #     AuthorName = "(" + str(request.POST.get('sigAddedUser').split(','))[1:-1] + ")"
    #     where_txt += ' AND agerecord.AuthorName IN ' + str(AuthorName)
    #     filterData.update({'AuthorName': AuthorName})
    #sql = 'SELECT DISTINCT tag_list.TagID, record_tag.TagName,tag_list.SigID,agerecord.SigState FROM tag_list JOIN qh_sig_status ON qh_sig_status.SIG_ID_FK = tag_list.SigID AND qh_sig_status.MARK_DELETED=0 JOIN record_tag ON record_tag.TagID=tag_list.TagID JOIN agerecord ON agerecord.Record_ID_FK=qh_sig_status.SIG_ID_FK JOIN cluster ON cluster.ClusterID = agerecord.ClusterId AND cluster.Status = 1 '+where_txt + ' ORDER BY tag_list.TagID;'

    sql = 'SELECT tag_list.TagID, record_tag.TagName,tag_list.SigID,agerecord.SigState,agerecord.AuthorName FROM agerecord JOIN qh_sig_status ON qh_sig_status.SIG_ID_FK = agerecord.Record_ID_FK AND qh_sig_status.MARK_DELETED=0 LEFT JOIN tag_list ON tag_list.SigID = agerecord.Record_ID_FK LEFT JOIN record_tag ON record_tag.TagID=tag_list.TagID JOIN cluster ON cluster.ClusterID = agerecord.ClusterId AND cluster.Status = 1 '+where_txt + ';'
    result = lib.db_query(sql)

    sigTag = []
    sigId = []
    stateArr = {}
    sigAddedUser = []
    if result:
        for res in result:
            if res[0] and res[1]:
                tag = [res[0],res[1]]
                if tag not in sigTag:
                    sigTag.append(tag)
            sigId.append(res[2])
            if res[3]:
                stateArr.update({res[3]:constant_data.SIG_STATELIST[res[3]]})
            if res[4] and res[4] not in sigAddedUser:
                sigAddedUser.append(res[4])
    data = {'state':sorted(stateArr.items()),'status':[[1, 'silent'], [0, 'non-silent']],'tags':sigTag,'sigId':sigId,'filterData':str(filterData),'sigAddedUser':sigAddedUser}
    return HttpResponse(json.dumps(data), content_type='application/json')

def filter_result_ajax(request):
    start = request.POST['start']
    length = request.POST['length']
    draw = request.POST['draw']

    if int(request.POST['Type']) not in permissions.checkclusterTypePermission(request):
        resp = {"draw": draw, "recordsTotal": 0, "recordsFiltered": 0, "data": '','filterData': ''}
        return HttpResponse(json.dumps(resp), content_type='application/json')

    filterData = {}
    actualColumns = ['agerecord.Record_ID_FK', 'agerecord.MalwareIndex', 'malwarenames.MAL_NAME', 'agerecord.AuthorName','agerecord.SigCnt','agerecord.SigState', 'cluster.ClusterName']

    searchColArr, i, orderString, where_text = [], 0, '', ''

    where_txt = ' where sig_master.SIG_TYPE_FK =' + str(request.POST['Type'])
    filterData.update({'type': str(request.POST['Type'])})
    if request.POST.get('createdUser'):
        createdUser = "(" + str(request.POST.get('createdUser').split(','))[1:-1] + ")"
        where_txt += ' AND cluster.CreatedBy IN ' + str(createdUser)
        filterData.update({'createdUser':createdUser})
    if request.POST.get('assignUser'):
        assignUser = "(" + str(request.POST.get('assignUser').split(','))[1:-1] + ")"
        where_txt += ' AND cluster.ClusterAssignedTo IN ' + str(assignUser)
        filterData.update({'assignUser': assignUser})

    if request.POST.get('source'):
        source = "(" + str(request.POST.get('source').split(','))[1:-1] + ")"
        where_txt += ' AND cluster.Source IN ' + str(source)
        filterData.update({'source': source})
    if request.POST.get('progress'):
        progress = "(" + str(request.POST.get('progress').split(','))[1:-1] + ")"
        where_txt += ' AND cluster.Progress IN ' + str(progress)
        filterData.update({'progress': progress})
    if request.POST.get('priority'):
        priority = "(" + str(request.POST.get('priority').split(','))[1:-1] + ")"
        where_txt += ' AND cluster.Priority IN ' + str(priority)
        filterData.update({'priority': priority})
    if request.POST.get('clusterDate'):
        if len(request.POST.get('clusterDate').split(' to ')) == 2:
            filterData.update({'startDate':request.POST.get('clusterDate').split(' to ')[0],'endDate':request.POST.get('clusterDate').split(' to ')[1]})
            where_txt += ' AND CAST(cluster.CreatedDate as DATE) BETWEEN "' + request.POST.get('clusterDate').split(' to ')[0] + '" AND "' + request.POST.get('clusterDate').split(' to ')[1] + '"'

    if request.POST.get('state'):
        state = "(" + str(request.POST.get('state').split(','))[1:-1] + ")"
        where_txt += ' AND agerecord.SigState IN ' + str(state)
        filterData.update({'state': state})

    if request.POST.get('sigAddedUser'):
        AuthorName = "(" + str(request.POST.get('sigAddedUser').split(','))[1:-1] + ")"
        where_txt += ' AND agerecord.AuthorName IN ' + str(AuthorName)
        filterData.update({'AuthorName': AuthorName})

    if request.POST.get('tags'):
        tags = "(" + str(request.POST.get('tags').split(','))[1:-1] + ")"
        filterData.update({'tags': tags})
        where_txt += ' AND tag_list.TagID IN  ' + str(tags)
    if request.POST.get('signatureDate') :
        if len(request.POST.get('signatureDate').split(' to ')) == 2:
            filterData.update({'sigStartDate': request.POST.get('signatureDate').split(' to ')[0],'sigEndDate':request.POST.get('signatureDate').split(' to ')[1]})
            #where_txt += ' AND agerecord.TimeStamp BETWEEN STR_TO_DATE("' + request.POST.get('sigStartDate') + '","%d-%m-%Y") AND STR_TO_DATE("' + request.POST.get('sigEndDate') + '","%d-%m-%Y")'
            #where_txt += ' AND agerecord.TimeStamp >="' + request.POST.get('sigStartDate') + '" AND agerecord.TimeStamp <="' + request.POST.get('sigEndDate') + '"'
            where_txt += ' AND CAST(agerecord.TimeStamp as DATE) BETWEEN "' + request.POST.get('signatureDate').split(' to ')[0] + '" AND "' + request.POST.get('signatureDate').split(' to ')[1] + '"'

    sql = 'SELECT  count(distinct sig_master.SIG_ID) from sig_master join qh_sig_status on sig_master.SIG_ID = qh_sig_status.SIG_ID_FK AND qh_sig_status.MARK_DELETED = 0  join malwarenames on sig_master.MAL_NAME_INDEX_FK = malwarenames.MAL_NAME_INDEX join agerecord on sig_master.SIG_ID = agerecord.Record_ID_FK join cluster on  agerecord.ClusterID = cluster.ClusterID AND cluster.Status = 1 JOIN chsum_sigtype ON sig_master.SIG_TYPE_FK = chsum_sigtype.SIG_TYPE LEFT JOIN tag_list ON tag_list.SigID = sig_master.SIG_ID '
    sqlCnt = sql + where_txt

    signatureRecordAge = lib.db_query(sqlCnt, 1)

    revState = dict(zip(constant_data.SIG_STATELIST.values(), constant_data.SIG_STATELIST.keys()))
    for col in actualColumns:
        if request.POST['columns[' + str(i) + '][search][value]']:
            if i == 5:
                if str(request.POST['columns[' + str(i) + '][search][value]']) in revState.keys():
                    filterData.update({col: revState[str(request.POST['columns[' + str(i) + '][search][value]'])]})
                    searchColArr.append({'column': col, 'value': str(revState[str(request.POST['columns[' + str(i) + '][search][value]'])]), 'operator': 1})
                else:
                    searchColArr.append({'column': col, 'value': str(request.POST['columns[' + str(i) + '][search][value]'])})
            elif i == 3 or i == 4:
                searchColArr.append({'column': col, 'value': request.POST['columns[' + str(i) + '][search][value]'],'operator':1})
                filterData.update({col: request.POST['columns[' + str(i) + '][search][value]']})
            else:
                searchColArr.append({'column': col, 'value': request.POST['columns[' + str(i) + '][search][value]']})
                filterData.update({col:request.POST['columns[' + str(i) + '][search][value]']})
        if 'order[0][column]' in request.POST:
            if str(request.POST['order[0][column]']) == str(i):
                orderString = ' order by ' + str(col) + ' ' + str(request.POST['order[0][dir]'])
        i += 1
    i = len(searchColArr)
    if len(searchColArr) > 0:
        where_txt += " and  "
    for searchString in searchColArr:
        i -= 1
        if i == 0:
            if 'operator' in searchString and searchString['operator'] == 1:
                where_txt += searchString['column'] + ' = "' + searchString['value'] + '" '
            else:
                 where_txt += searchString['column'] + ' like "%' + searchString['value'] + '%" '
        else:
            if 'operator' in searchString and searchString['operator'] == 1:
                where_txt += searchString['column'] + ' = "' + searchString['value'] + '" and '
            else:
                where_txt += searchString['column'] + ' like "%' + searchString['value'] + '%" and '

    sqlFilCount = sql + where_txt

    if len(searchColArr):
        DataCountFilTotal = lib.db_query(sqlFilCount, 1)
    else:
        DataCountFilTotal = signatureRecordAge

    sql = 'SELECT distinct agerecord.Record_ID_FK,agerecord.MalwareIndex,malwarenames.MAL_NAME,agerecord.SigCnt,cluster.ClusterName,cluster.ClusterID,chsum_sigtype.SIG_TYPE_NAME,agerecord.AuthorName,agerecord.SigState FROM sig_master JOIN qh_sig_status ON sig_master.SIG_ID = qh_sig_status.SIG_ID_FK  AND qh_sig_status.MARK_DELETED = 0 JOIN malwarenames ON sig_master.MAL_NAME_INDEX_FK = malwarenames.MAL_NAME_INDEX JOIN agerecord ON sig_master.SIG_ID = agerecord.Record_ID_FK JOIN cluster ON agerecord.ClusterID = cluster.ClusterID AND cluster.Status = 1 JOIN chsum_sigtype ON sig_master.SIG_TYPE_FK = chsum_sigtype.SIG_TYPE LEFT JOIN tag_list ON tag_list.SigID = sig_master.SIG_ID ' + where_txt + ' ' +orderString + ' limit '+start+','+length
    result = lib.db_query(sql)

    data = []
    for record in result:
        viewBtn = '<a href="/signature/' + str(record[0]) + '?action=view" class="label label-primary">View</a>'
        export = '<a href="/downloadIniFile/?id='+str(record[0])+'" id="inipath" target="_blank"  data-toggle="tooltip" data-placement="bottom" title="Export ini"><span class="glyphicon glyphicon-export"></span></a>'
        data.append({"RecordId": str(record[0]), "MalwareIndex": str(record[1]), "MalwareName": str(lib.trimString(record[2], 20)),
                     "SigCount": str(record[3]), 'Type': str(record[6]),"ClusterName": "<a href='/cluster/" + str(record[5]) + "?action=view'>" + str(lib.trimString(record[4], 20)) + "</a>",'AddedBy':"<a href='/user/"+str(record[7])+"'>"+str(record[7])+"</a>",'State':str(constant_data.SIG_STATELIST[record[8]]),'view': viewBtn,'export':export})

    recordsTotal = signatureRecordAge[0]
    recordsFiltered = DataCountFilTotal[0]

    resp = {"draw": draw, "recordsTotal": recordsTotal, "recordsFiltered": recordsFiltered, "data": data,'filterData':filterData}
    return HttpResponse(json.dumps(resp), content_type='application/json')


@login_required(login_url='/login/')
def downloadFilterIniFile(request):
    actualColumns = ['agerecord.Record_ID_FK', 'agerecord.MalwareIndex', 'malwarenames.MAL_NAME','agerecord.AuthorName', 'agerecord.SigCnt', 'agerecord.SigState', 'cluster.ClusterName']

    if 'filterData' in request.GET:
        filterData = literal_eval(request.GET['filterData'])

    if 'clusterExport' in request.GET:
        filterData = {'type': str(request.GET['type']),'clusterId':str(request.GET['clusterId'])}

    finalData = {}

    if 'type' in filterData and filterData['type']:
        clusterType = filterData['type']
        where_txt = 'where sig_master.SIG_TYPE_FK = ' + str(clusterType)
        if 'clusterId' in filterData and filterData['clusterId']:
            where_txt += ' and agerecord.ClusterId = ' + str(request.GET['clusterId'])

    if 'progress' in filterData and filterData['progress']:
        where_txt += ' and cluster.progress in ' + str(filterData['progress'])

    if 'createdUser' in filterData and filterData['createdUser']:
        where_txt += ' AND cluster.CreatedBy IN ' + str(filterData['createdUser'])
    if 'assignUser' in filterData and filterData['assignUser']:
        where_txt += ' AND cluster.ClusterAssignedTo IN ' + str(filterData['assignUser'])

    if 'source' in filterData and filterData['source']:
        where_txt += ' AND cluster.Source IN ' + str(filterData['source'])
    if 'progress' in filterData and filterData['progress']:
        where_txt += ' AND cluster.Progress IN ' + str(filterData['progress'])
    if 'priority' in filterData and filterData['priority']:
        where_txt += ' AND cluster.Priority IN ' + str(filterData['priority'])
    if ('startDate' in filterData and filterData['startDate']) and ('endDate' in filterData and filterData['endDate']):
        startDate = "'" + filterData['startDate'] + "'"
        endDate = "'" + filterData['endDate'] + "'"
        where_txt += ' AND cluster.CreatedDate >= ' + startDate + ' AND  cluster.CreatedDate <=' + endDate
    if 'tags' in filterData and filterData['tags']:
        where_txt += ' AND tag_list.TagID IN ' + str(filterData['tags'])
    if ('sigStartDate' in filterData and filterData['sigStartDate']) and ('sigEndDate' in filterData and filterData['sigEndDate']):
        sigStartDate = "'" +filterData['sigStartDate'] + "'"
        sigEndDate = "'" +filterData['sigEndDate'] + "'"
        where_txt += ' AND agerecord.TimeStamp >= ' + sigStartDate + ' AND  agerecord.TimeStamp <=' + sigEndDate
    if 'state' in filterData and filterData['state'] and actualColumns[5] not in filterData:
        where_txt += ' AND agerecord.SigState IN ' + str(filterData['state'])


    for col in actualColumns:
        if col in filterData:
            index = actualColumns.index(col)
            if index == 3 or index == 4 or index == 5:
                where_txt += ' AND ' + str(col) + ' = "' + str(filterData[col])+'"'
            else:
                where_txt += ' AND '+str(col)+ ' like "%' + str(filterData[col]) + '%" '

    #get sig ids
    sql = 'SELECT distinct agerecord.Record_ID_FK FROM sig_master JOIN qh_sig_status ON sig_master.SIG_ID = qh_sig_status.SIG_ID_FK AND qh_sig_status.MARK_DELETED = 0 JOIN malwarenames ON sig_master.MAL_NAME_INDEX_FK = malwarenames.MAL_NAME_INDEX JOIN agerecord ON sig_master.SIG_ID = agerecord.Record_ID_FK JOIN cluster ON agerecord.ClusterID = cluster.ClusterID AND cluster.Status = 1 JOIN chsum_sigtype ON sig_master.SIG_TYPE_FK = chsum_sigtype.SIG_TYPE LEFT JOIN tag_list ON tag_list.SigID = sig_master.SIG_ID ' + where_txt
    sigResult = lib.db_query(sql)

    sigIds = []
    for id in sigResult:
        sigIds.append(id[0])

    sigIds = sorted(sigIds)

    ClusterFieldAllowed = constant_data.TypeFieldArry[int(filterData['type'])]
    recordIds = "("+str(sigIds)[1:-1]+")"

    #get agerecord for all sigids
    sql = 'SELECT agerecord.Record_ID_FK, agerecord.MalwareIndex,agerecord.ClusterId, agerecord.FileType, agerecord.PolyFuncIndex,agerecord.ScanRule, chsum_sigtype.SIG_TYPE_NAME,malwarenames.MAL_NAME,sig_master.SIG_TYPE_FK, cluster.ClusterName,cluster.CreatedBy,cluster.Priority,agerecord.ScanRuleSusp,agerecord.RecCheckFlags,agerecord.RecComment,agerecord.SigState from sig_master LEFT Join chsum_sigtype on sig_master.SIG_TYPE_FK = chsum_sigtype.SIG_TYPE LEFT Join malwarenames on sig_master.MAL_NAME_INDEX_FK = malwarenames.MAL_NAME_INDEX Join qh_sig_status on sig_master.SIG_ID = qh_sig_status.SIG_ID_FK AND qh_sig_status.MARK_DELETED = 0 Join agerecord on sig_master.SIG_ID = agerecord.Record_ID_FK JOIN cluster ON agerecord.ClusterId = cluster.ClusterID AND cluster.Status = 1 WHERE sig_master.SIG_ID in ' + str(recordIds)
    agerecordData = lib.db_query(sql)

    #get pattern details
    sql = 'select Record_ID_FK,Sig,`Offset`,LocId,BuffSize,CleanupType,StartToken,EndToken,SigCheckFlags,SigComment,Distance from agesig where Record_ID_FK in ' + str(recordIds) + ' order by AgeSig_ID '
    sigRecordData = lib.db_query(sql)

    if 'FILTER' in ClusterFieldAllowed:
        sql = 'select agefilter.Record_ID_FK,FilterID,Oprt,OprdVal from agefilter where agefilter.Record_ID_FK in ' + str(recordIds)
        filterRecord = lib.db_query(sql)

    #get sig tag record
    tagRecord ={}
    sql = 'select tag_list.SigID,record_tag.TagName from record_tag inner join tag_list on record_tag.TagID = tag_list.TagID where tag_list.SigID in ' + str(recordIds)
    tagResultData = lib.db_query(sql)
    if tagResultData:
        for tag in tagResultData:
            tagArr = []
            if tag[0] not in tagRecord:
                tagArr.append(tag[1])
                tagRecord.update({tag[0]:tagArr})
            else:
                tagArr = tagRecord[tag[0]]
                tagArr.append(tag[1])
                tagRecord.update({tag[0]: tagArr})


    for data in agerecordData:
        iniData = {}
        iniData.update({'SigId':str(data[0])})
        iniData.update({'MalwareIndex':data[1]})
        iniData.update({'State':str(constant_data.SIG_STATE[data[15]])})

        if 'POLYFUNC' in ClusterFieldAllowed:
            iniData.update({'PolyFunIndex': data[4]})

        if 'THREAT_NAME' in ClusterFieldAllowed :
            iniData.update({'ThreatName':data[7]})
        iniData.update({'Type':constant_data.CLUSTER_TYPE[data[8]]})
        iniData.update({'ClusterId':data[2]})

        if 'SCAN_RULE' in ClusterFieldAllowed:
            if data[5]:
                iniData.update({'ScanRule':data[5]})

        if 'SCAN_RULE_SUSP' in ClusterFieldAllowed:
            if data[12]:
                iniData.update({'ScanRuleSusp':data[12]})
        if 'SCAN_RULE_SUSP' in ClusterFieldAllowed or 'SCAN_RULE' in ClusterFieldAllowed:
            ScanRuleSequence = 0
            if lib.checkFlag(data[13], lib.gen_inx_flag_sequence):
                ScanRuleSequence = 1
            iniData.update({'ScanRuleSequence': ScanRuleSequence})

        if 'SUS_WEAK_DETECTION' in ClusterFieldAllowed:
            susWeakDetection = 0
            if lib.checkFlag(data[13], lib.gen_inx_flag_weak_detection):
                susWeakDetection =1
            iniData.update({'susWeakDetection': susWeakDetection})

        if 'STATUS' in ClusterFieldAllowed:
                if lib.checkFlag(data[13], lib.gen_inx_flag_silent):
                    status = 'silent'
                    iniData.update({'status': status})

        if data[14] != None:
            recordComment = str(data[14])
            iniData.update({'RecordComment': recordComment})

        signatures,i,offset,buffsize,locId,cleanUpType,startToken,endToken,WeakSig,Comment= {},65,'','','','','','','',''

        if sigRecordData:
            for pettern in sigRecordData:
                if pettern[0] == data[0]:
                    pattern = pettern[1]
                    if 'OFFSET' in ClusterFieldAllowed:
                        offset = pettern[2]
                    if 'BUFFER' in ClusterFieldAllowed:
                        buffsize = pettern[4]
                    if 'LOCATION_ID' in ClusterFieldAllowed:
                        locId = pettern[3]
                    if 'CLEANUP_TYPE' in ClusterFieldAllowed:
                        cleanUpType = pettern[5]
                        startToken = pettern[6]
                        endToken = pettern[7]
                    if 'WEAK_SIG' in ClusterFieldAllowed:
                        WeakSig = 0;
                        if lib.checkFlag(pettern[8], lib.gen_inx_weak_sig):
                            WeakSig = 1;
                    if pettern[9] != 'None':
                        Comment = pettern[9]
                    if 'DISTANCE' in ClusterFieldAllowed:
                        Distance = pettern[10]
                    signatures.update({chr(i): {'pattern': pattern, 'offset': offset, 'buffsize':buffsize,'locId': locId, 'cleanUpType': cleanUpType,'startToken':startToken,'endToken':endToken,'WeakSig':WeakSig,'Distance':Distance,'Comment':Comment}})
                    i += 1
                    iniData.update({'sig':signatures,'clusterType':data[8]})

        if 'FILE_TYPE' in ClusterFieldAllowed:
            FileType = lib.fileTypeJoin(lib.getFileRule(data[3],data[8],'FileType'))
            iniData.update({'FileType':FileType})


        if 'FILTER' in ClusterFieldAllowed:
                if filterRecord != None:
                    FilterFieldArrRev = lib.getFileSectionDetails(constant_data.CLUSTER_TYPE_NAME[constant_data.CLUSTER_TYPE[int(filterData['type'])]], 'FilterField')
                    FilterFieldArr = dict(zip(FilterFieldArrRev.values(), FilterFieldArrRev.keys()))
                    FilterOperationArrRev = lib.getFileSectionDetails(constant_data.CLUSTER_TYPE_NAME[constant_data.CLUSTER_TYPE[int(filterData['type'])]], 'FilterOperation')
                    FilterOperationArr = dict(zip(FilterOperationArrRev.values(), FilterOperationArrRev.keys()))
                    FilterFieldValues = {}
                    i = 1
                    for filterItem in filterRecord:
                        if filterItem[0] == data[0]:
                            FilterFieldValues.update({i: {'field': FilterFieldArr[str(filterItem[1])], 'oprt': FilterOperationArr[str(filterItem[2])],'value': filterItem[3]}})
                            i += 1
                            iniData.update({'FILTER_'+str(data[0]):FilterFieldValues})

        finalData.update({data[0]: iniData})

        if data[0] in tagRecord:
           tagresult = tuple(tagRecord[data[0]])
           iniData.update({'tagResult':  getTagResult(tagresult)})

        finalData.update({data[0]: iniData})

    #fileName = str(str(data[7])+"_"+str(sigIds[0])+"_"+str(sigIds[len(sigIds)-1])+"_"+str(data[1])).replace(" ","")

    fileName = str(constant_data.CLUSTER_TYPE[int(filterData['type'])])+"_"+str(sigIds[0])+"_"+str(sigIds[len(sigIds)-1])

    if not request.session.session_key:
        request.session.save()
    fileName += request.session.session_key

    if 'inx' in request.GET and request.GET['inx']:
        if not os.path.exists(settings.DATA_FOLDER + 'temp_ini\\'):
            os.makedirs(settings.DATA_FOLDER + 'temp_ini\\', exist_ok=True)

        fileName = re.sub('[^A-Za-z0-9]+', '_', fileName)
        ini_file = open(settings.DATA_FOLDER + 'temp_ini\\' + str(fileName) + '.ini', "w")
        ini_file.write(createSignatureIni(finalData, sigResult))
        ini_file.close()

        if hasattr(settings, 'CREATE_INX_PATH'):
            p=subprocess.Popen("python "+ settings.CREATE_INX_PATH + "inx_file.py " + settings.DATA_FOLDER + "temp_ini\\" + str(fileName) + ".ini "+ settings.DATA_FOLDER + "temp_ini\\inx\\")
            p.communicate()

            if os.path.exists(settings.DATA_FOLDER + "temp_ini\\inx\\"+str(fileName)+".ini"):
                inx_file = open(settings.DATA_FOLDER + "temp_ini\\inx\\"+str(fileName)+".ini",'r')
                inx_file_data = inx_file.read()
                inx_file.close()

                inx_file_data = inx_file_data.replace('\n\n','\n')
               # rmtree(settings.DATA_FOLDER+"temp_ini",ignore_errors=True)

                response = HttpResponse(inx_file_data, content_type='application/plain')
                response['Content-Disposition'] = 'attachment; filename="' + str(fileName) + '.inx'
            else:
                response = HttpResponse('INX File Not Found', content_type='application/json')
        else:
            response = HttpResponse('INX Path Not Found', content_type='application/json')
    else:
        response = HttpResponse(createSignatureIni(finalData, sigResult), content_type='application/plain')
        response['Content-Disposition'] = 'attachment; filename="' + str(fileName) + '.ini"'
    return response

def createSignatureIni(finalData,sidId):
    iniFileString = ""
    #cnt = 0
    for sigid in sidId:
        sigid = sigid[0]
        if sigid in finalData:
            data = finalData[sigid]
           # cnt +=1
            #iniFileString += "Cnt__" + str(cnt)+"\r\n"
            CreatedDate = str(datetime.datetime.now())
            iniFileString += "#start_"+str(sigid)+" \r\n"
            iniFileString += "[" +datetime.datetime.now().strftime("%Y%m%d_%H%I%S")+"_"+ data['SigId'] + "]\r\n"
            iniFileString += lib.addData('MalwareIndex', data)
            iniFileString += lib.addData('State', data)
            iniFileString += lib.addData('ClusterId', data)
            iniFileString += lib.addData('Type', data)

            if 'sig' in data:
                sig = sorted(data['sig'].items())
                if sig:
                    for alph, signature in sig:
                        iniFileString += lib.addDataItem(alph + ".Sig", signature['pattern']);
                        if 'buffsize' in signature and signature['buffsize'] != '':
                            iniFileString += lib.addDataItem(alph + ".BufferSize", signature['buffsize']);
                        if 'offset' in signature and signature['offset'] != '':
                            iniFileString += lib.addDataItem(alph + ".Offset", signature['offset']);
                        if 'Distance' in signature and signature['Distance'] != '':
                            iniFileString += lib.addDataItem(alph + ".Distance", signature['Distance']);
                        if 'locId' in signature and signature['locId'] != '':
                            LocId = ''.join(lib.getFileRule(signature['locId'], int(data['clusterType']), 'SigLocationId'))
                            iniFileString += lib.addDataItem(alph + ".LocationId", LocId);
                        if 'cleanUpType' in signature and signature['cleanUpType'] != 0 and signature['cleanUpType'] != '':
                            CleanupType = ''.join(lib.getFileRule(int(signature['cleanUpType']), int(data['clusterType']), 'CleanupType'))
                            iniFileString += lib.addDataItem(alph + ".CleanupType", CleanupType);
                            if 'startToken' in signature and signature['startToken'] != '' and signature['startToken'] != 'NULL':
                                iniFileString += lib.addDataItem(alph + ".StartToken", signature['startToken']);
                            if 'endToken' in signature and signature['endToken'] != ''  and signature['endToken'] != 'NULL':
                                iniFileString += lib.addDataItem(alph + ".EndToken", signature['endToken']);
                        if 'WeakSig' in signature and signature['WeakSig'] != '':
                            iniFileString += lib.addDataItem(alph + ".WeakSig", signature['WeakSig']);
                        if 'Comment' in signature and signature['Comment'] != '':
                            iniFileString += lib.addDataItem(alph + ".Comment", signature['Comment']);
                        #iniFileString += "\r\n"

            if 'FILTER_'+str(sigid) in data :
                filterData = OrderedDict(sorted(data['FILTER_'+str(sigid)].items()))
                for filDataIdx in filterData:
                    iniFileString += "Filter"+str(filDataIdx)+".field="+filterData[filDataIdx]['field']+"\r\n"
                    iniFileString += "Filter"+str(filDataIdx)+".oprt="+filterData[filDataIdx]['oprt']+"\r\n"
                    iniFileString += "Filter"+str(filDataIdx)+".value="+str(filterData[filDataIdx]['value'])+"\r\n"

            if 'ThreatName' in data and data['ThreatName']:
                iniFileString += lib.addData('ThreatName', data)

            if 'FileType' in data and data['FileType']:
                iniFileString += lib.addData('FileType', data)

            if 'ScanRule' in data and data['ScanRule'] != 'NULL':
                iniFileString += lib.addData('ScanRule', data)

            if 'ScanRuleSusp' in data and data['ScanRuleSusp'] != 'NULL':
                iniFileString += lib.addData('ScanRuleSusp', data)

            if 'ScanRuleSequence' in data and  data['ScanRuleSequence']:
                iniFileString += lib.addDataItem("Sequence", data['ScanRuleSequence']);

            if 'susWeakDetection' in data and data['susWeakDetection']:
                iniFileString += lib.addDataItem("WeakDetection", data['susWeakDetection']);

            if 'status' in data and data['status']:
                iniFileString += lib.addDataItem("status", data['status']);

            if 'PolyFunIndex' in data and data['PolyFunIndex'] != '':
                iniFileString += lib.addData('PolyFunIndex', data)

            if 'RecordComment' in data and data['RecordComment']:
                iniFileString += lib.addDataItem("Comment", data['RecordComment']);

            if 'tagResult' in data and data['tagResult']:
                 iniFileString += "Tags="+str(data['tagResult']) +"\r\n"
            iniFileString += "#CreatedDate:" +str(CreatedDate) +"\r\n"
            iniFileString += "#end_"+str(sigid)+"\r\n\r\n"

    iniFileString += "\r\n"
    return iniFileString


def getTagResult(tagResultData):
    tagResult = ''
    for tag in tagResultData:
        tagResult += str(tag) + ','
    tagResult = tagResult[:-1]
    return tagResult