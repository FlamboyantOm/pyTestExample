import json,html,datetime
from django.shortcuts import *
from . import lib,constant_data,dropdown,permissions
from collections import OrderedDict
from django.urls import reverse
from django.contrib import messages
from apex import settings
from .lib import database_connection_check
from django.contrib.auth.decorators import  user_passes_test,login_required

@database_connection_check
@login_required(login_url='/login/')
@user_passes_test(lambda u: u.has_perm('portal.can_manage_signature'),login_url='/login/')
def test(request):
    data = {}
    data['record_name'] = 'test_1'
    #data['sig'] ={'A':'FF ?? ?? ?? FF F2 F2 FF C0 C0 FF ?? ?? C0 60 60 FF 60','B':'EB ?? 4A 2D ?? ?? D? ?? E3 ?? 58 4E A0 ??','C':'DB ?? DA 2D ?? ?? ?? ?? E3 ?? 58 4E A0 ??'}
    data['sig'] ={'A':'FF ?? ?? ?? FF F2 F2 FF C0 C0 FF ?? ?? C0 60 60 FF 60','B':'EB ?? 4A 2D ?? ?? D? ?? E3 ?? 58 4E A0 ??'}
    data['ClusterId'] = '1200'
    data['ThreatName'] = '1111.1200'
    data['MalwareIndex'] = '1200'
    data['Type'] = 'Primary'
    data['Status'] = 'Non-Silent'
    data['FileType'] = 'AGE_FILETYPE_FLAG_DLL'
    data['SigntureType'] = 'Disasm'
    data['SignatureCrcs'] = {'A':'BCD00D22','B':'B4D10D40','C':'B4DF3D22'}
    data['Key1'] = 'Val1'
    data['Key2'] = 'Val2'
    text = str(lib.processData(data))
    return HttpResponse("<pre>"+text+"<pre>")

@login_required(login_url='/login/')
def signature(request):
    if  permissions.accessPermission(request,'can_manage_signature') == 0:
        messages.error(request, 'Signature management permission not available')
        return HttpResponseRedirect("/signature/list/")

    allPerm = permissions.getUserGroupPermission(request)
    userGroup = permissions.checkUserGroup(request)

    stateArr = permissions.checkStatePermission(request)
    if stateArr == 0:
        messages.error(request, 'State permission not available')
        return HttpResponseRedirect("/signature/list/")
    #add new
    if not request.POST and 'id' not in request.GET:
        class data:
            pass
        lib.setMetaInformation(request, [('signature'), ('signature_new')], 'New Signature', OrderedDict([('Signature', '/signature/list/'), ('New Signature', '')]))
        if 'cid' in request.GET:

            sql = 'select ClusterID,Type from cluster where Status = 1 and ClusterID = '+str(request.GET['cid'])+' limit 1'
            ClusterData = lib.db_query(sql,1)

            permision_type = str(constant_data.CLUSTER_TYPE[ClusterData[1]]).lower()

            if 'can_edit_' + str(permision_type) not in allPerm:
                messages.error(request, 'Permission not available for ' + str(permision_type).upper())
                return HttpResponseRedirect("/cluster/" + str(request.GET['cid']) + "/?action=view")

            ClusterType = ClusterData[1]
            ClusterFieldAllowed= constant_data.TypeFieldArry[ClusterType]
            setattr(data,'ClusterFieldAllowed',ClusterFieldAllowed)


            if 'FILE_TYPE' in ClusterFieldAllowed:
                setattr(data,'fileTypeSelect',dropdown.getFileDropDown(ClusterType,0))

            if 'CLEANUP_TYPE' in ClusterFieldAllowed:
                setattr(data,'signatureCleanUpTypeDropDown',dropdown.signatureCleanUpTypeDropDown(ClusterType,0))

            if 'LOCATION_ID' in ClusterFieldAllowed:
                setattr(data, 'signatureLocationIdDropDown', dropdown.signatureLocationIdDropDown(ClusterType,0))

            if 'FILTER' in ClusterFieldAllowed:
                setattr(data,'signatureFilterFieldDropDown',dropdown.signatureFilterFieldDropDown(ClusterType,0))
                setattr(data,'signatureFilterOperationDropDown',dropdown.signatureFilterOperationDropDown(ClusterType,0))

            setattr(data,'ClusterId',request.GET['cid'])
           # setattr(data,'clusterDropDown',dropdown.clusterSelectDropDown(request))
            setattr(data,'malwareDropDown',dropdown.malwareIndexDropDown())
            setattr(data,'clusterType',constant_data.CLUSTER_TYPE[ClusterData[1]])
            setattr(data,'signatureType',{'normalised': lib.getConfigValue(ClusterData[1], 'PATTERN', 'NORMALISED')})
            sigTag = dropdown.signatureTag().values()
            setattr(data, 'signatureTag', list(sigTag))


            setattr(data, 'stateArr', dropdown.clusterStateDropDown(1, constant_data.NEW_CLUSTER_STATE))
            return render(request, 'portal/signature-new.html',{'data':data})
        else:
            messages.info(request, "Cluster id not found.")
            return HttpResponseRedirect(reverse('portal:signature_list'))
    elif 'id' in request.GET and request.GET['id']:
            class data:
                pass
            lib.setMetaInformation(request, [('signature'), ('signature_new')],"Updating Signature : " + str(request.GET['id']), OrderedDict([('Signature', '/signature/list/'), (str(request.GET['id']), '/signature/'+str(request.GET['id'])+'/?action=view'),('Edit - '+str(request.GET['id']),'')]))
            sql = 'SELECT agerecord.Record_ID_FK, agerecord.MalwareIndex,agerecord.ClusterId, agerecord.FileType, agerecord.PolyFuncIndex,agerecord.ScanRule, chsum_sigtype.SIG_TYPE_NAME,malwarenames.MAL_NAME,sig_master.SIG_TYPE_FK,agerecord.ScanRuleSusp,agerecord.RecCheckFlags,agerecord.RecComment,agerecord.SigState from sig_master LEFT Join chsum_sigtype on sig_master.SIG_TYPE_FK = chsum_sigtype.SIG_TYPE LEFT Join malwarenames on sig_master.MAL_NAME_INDEX_FK = malwarenames.MAL_NAME_INDEX Join qh_sig_status on sig_master.SIG_ID = qh_sig_status.SIG_ID_FK AND qh_sig_status.MARK_DELETED = 0 Join agerecord on sig_master.SIG_ID = agerecord.Record_ID_FK JOIN cluster ON agerecord.ClusterId = cluster.ClusterID AND cluster.Status = 1 WHERE sig_master.SIG_ID = "'+str(request.GET['id'])+'"'
            recordData = lib.db_query(sql,1)

            if recordData is None:
                messages.info(request, "Signature record is removed or invalid request.")
                return HttpResponseRedirect(reverse('portal:signature_list'))

            permision_type = str(recordData[6]).lower()

            if 'can_edit_' + str(permision_type) not in allPerm or recordData[12] not in permissions.checkStatePermission(request) or recordData[12] in [6,7]:
                if 'Manager' not in userGroup.keys():
                    messages.error(request,'Unable to edit permission not available')
                    return HttpResponseRedirect('/signature/' + str(request.GET['id'])+ '/?action=view')

            sql = 'select Sig,`Offset`,LocId,BuffSize,CleanupType,StartToken,EndToken,SigCheckFlags,SigComment,Distance from agesig where Record_ID_FK = "'+str(request.GET['id'])+'" order by AgeSig_ID '
            sigRecordData = lib.db_query(sql)
            ClusterFieldAllowed = constant_data.TypeFieldArry[recordData[8]]
            signatures,buffer,i,sigPattern,Comment,Distance = {},{},65,'','',''

            if 'CLEANUP_TYPE' in ClusterFieldAllowed:
                cleanTypeAvailable = lib.getFileRule('', int(recordData[8]), 'CleanupType')
                cleanTypeAvailable = dict(zip(cleanTypeAvailable.values(), cleanTypeAvailable.keys()))
            for item in sigRecordData:
                if 'WEAK_SIG' in ClusterFieldAllowed:
                   WeakSig  =0;
                   if lib.checkFlag(item[7],lib.gen_inx_weak_sig):
                       WeakSig = 1;
                else:
                    WeakSig = item[7]
                CleanupType = item[4]
                LocId = item[2]
                if 'CLEANUP_TYPE' in ClusterFieldAllowed:
                    CleanupType = '-'
                    if item[4] != '':
                        CleanupType =  cleanTypeAvailable[str(item[4])]
                if 'LOCATION_ID' in ClusterFieldAllowed:
                    LocId = ''.join(lib.getFileRule(item[2], int(recordData[8]), 'SigLocationId'))
                if item[8] != 'None':
                    Comment = str(item[8])
                if 'DISTANCE' in ClusterFieldAllowed:
                    Distance = item[9]
                signatures.update({chr(i): { 'pattern' : str(item[0]), 'offset': str(item[1]),'LocId':LocId,'BuffSize':str(item[3]),'CleanupType':str(CleanupType).upper,'StartToken':str(item[5]),'EndToken':str(item[6]),'WeakSig':WeakSig,'Comment':Comment,'Distance':Distance}})
                sigPattern += chr(i) + ":" + str(item[0])+','
                i += 1
            sigPattern =  sigPattern[:-1]

            setattr(data, 'ClusterFieldAllowed', ClusterFieldAllowed)
            if 'FILTER' in ClusterFieldAllowed:
                sql = 'select FilterID,Oprt,OprdVal from agefilter where Record_ID_FK = "'+str(request.GET['id'])+'" order by Filter_ID '
                filterRecordData = lib.db_query(sql)
                filterRecord, i = [], 1
                fileTypeArr = lib.getFileSectionDetails(recordData[8], 'FilterField')
                FilterOperationTypeArr = lib.getFileSectionDetails(recordData[8], 'FilterOperation')

                for item in filterRecordData:
                    for key, value in fileTypeArr.items():
                        if value == str(item[0]):
                            FilterFieldData = key
                    for key, value in FilterOperationTypeArr.items():
                        if value == str(item[1]):
                            FilterOperationData = constant_data.FILTER_OPERATION_TYPE_SYM[value]
                    filterRecord.append({'id': int(i), 'FilterField': FilterFieldData.upper(), 'FilterOperation': FilterOperationData.upper(),'FilterFieldInput': str(item[2])})
                    i += 1
                setattr(data,'filterRecord',filterRecord)

            sql = 'select record_tag.TagName from  record_tag join tag_list on record_tag.TagID = tag_list.TagID where tag_list.SigID =' +str(request.GET['id'])
            tagResultData = lib.db_query(sql)

            if tagResultData:
                  setattr(data, 'tagResult', getTagResult(tagResultData))

            setattr(data, 'clusterType', constant_data.CLUSTER_TYPE[recordData[8]])
            setattr(data,'MalwareIndex',recordData[1])
            setattr(data,'sigid',str(request.GET['id']))
            setattr(data,'ClusterFieldAllowed',ClusterFieldAllowed)
            setattr(data,'signatures',sorted(signatures.items()))
            setattr(data,'sigPattern',sigPattern)

            sigTag = dropdown.signatureTag().values()
            setattr(data, 'signatureTag',list(sigTag))

            if recordData[5] != "NULL" and 'SCAN_RULE' in ClusterFieldAllowed:
                setattr(data,'ScanRule',recordData[5])

            if recordData[9] != "NULL" and 'SCAN_RULE_SUSP' in ClusterFieldAllowed:
                setattr(data,'ScanRuleSusp',recordData[9])

            if 'POLYFUNC' in ClusterFieldAllowed:
                setattr(data,'PolyFuncIndex',recordData[4])

            if 'LOCATION_ID' in ClusterFieldAllowed:
                setattr(data, 'signatureLocationIdDropDown',dropdown.signatureLocationIdDropDown(recordData[8],0))
            if 'FILE_TYPE' in ClusterFieldAllowed:
                setattr(data,'fileTypeSelect',dropdown.getFileDropDown(recordData[8],recordData[3]))
            if 'CLEANUP_TYPE' in ClusterFieldAllowed:
                setattr(data,'signatureCleanUpTypeDropDown',dropdown.signatureCleanUpTypeDropDown(recordData[8],0))
            if 'FILTER' in ClusterFieldAllowed:
                setattr(data,'signatureFilterFieldDropDown',dropdown.signatureFilterFieldDropDown(recordData[8],0))
                setattr(data,'signatureFilterOperationDropDown',dropdown.signatureFilterOperationDropDown(recordData[8],0))

            if 'SUS_WEAK_DETECTION' in ClusterFieldAllowed:
                susWeakDetection = 0
                if lib.checkFlag(recordData[10],lib.gen_inx_flag_weak_detection):
                    susWeakDetection = 1
                setattr(data,'susWeakDetection',susWeakDetection)

            if 'STATUS' in ClusterFieldAllowed:
                status = 0
                if lib.checkFlag(recordData[10], lib.gen_inx_flag_silent):
                    status = 1
                setattr(data, 'status', status)

            ScanRuleSequence = 0
            if lib.checkFlag(recordData[10], lib.gen_inx_flag_sequence):
                ScanRuleSequence = 1
            setattr(data, 'ScanRuleSequence',ScanRuleSequence)

            if recordData[11]:
                 setattr(data,'RecordComment',str(recordData[11]))

            setattr(data,'ClusterId',recordData[2])
            #setattr(data,'clusterDropDown',dropdown.clusterSelectDropDown(request,recordData[2]))
            setattr(data,'malwareDropDown',dropdown.malwareIndexDropDown(recordData[7]))
            setattr(data,'signatureType',{'normalised': lib.getConfigValue(recordData[8], 'PATTERN', 'NORMALISED')})
            setattr(data, 'SigId', request.GET['id'])
            setattr(data, 'stateArr', dropdown.clusterStateDropDown(recordData[12], stateArr))
            return render(request, 'portal/signature-new.html',{'data':data})

    elif request.POST:
        error_message, data = lib.signatureValidation(request)
        if error_message != 0:
            if request.POST['Update']:
                return HttpResponseRedirect('/signature/?action=add&id='+str(request.POST['SigId']))
            else:
                return HttpResponseRedirect('/')
        else:
            sigData,sig,requestData,keyValueData,patternComm,pattentComment,cleanupType,patterncleanUpType={},{},{},{},{},{},{},{}
            patternBufferSizeDict,patternOffsetDict,patternLocationIdDict,LocationIdDict,OffsetDict,BufferSizeDict,patternDistanceDict,DistanceDict,patternWeakSig,weakSig,patternStartTokenData,startToken,patternEndTokenData,endToken = {},{},{},{},{},{},{},{},{},{},{},{},{},{}
            if 'ClusterId' in request.POST:
                sql = 'select ClusterID,Type from cluster where Status = 1 and ClusterID = '+str(request.POST['ClusterId'])+' limit 1'

                ClusterData = lib.db_query(sql,1)
                if ClusterData == None:
                    messages.error(request,"#E1 Cluster id not found")
                    return HttpResponseRedirect('/')
            else:
                messages.error(request,"#E2 Cluster id not found")
                return HttpResponseRedirect('/')
            ClusterType = ClusterData[1]
            ClusterFieldAllowed = constant_data.TypeFieldArry[ClusterType]


            for key in request.POST :
                if key in ['Key','Value','csrfmiddlewaretoken','Signature','FileType','ThreatName','SignatureData','PatternCommentData','WeakDetection','ScanRuleSequence','FilterOperation','FilterFieldInput','FilterField'] :
                    continue
                requestData.update({key:request.POST[key]})

            data = requestData

            if 'RecordComment' in request.POST and request.POST['RecordComment']:
                data.update({'Comment': request.POST['RecordComment']})

            if 'SUS_WEAK_DETECTION' in ClusterFieldAllowed :
                if 'WeakDetection' in request.POST and request.POST.get('WeakDetection'):
                    WeakDetection = request.POST.get('WeakDetection')
                    data.update({'WeakDetection': WeakDetection})

            if 'LOCATION_ID'  in ClusterFieldAllowed and 'PatternLocationId' in request.POST:
                PatternLocationId = request.POST['PatternLocationId'].split(',')
                print(PatternLocationId)
                LocationIdAvailable = lib.getFileRule('', int(ClusterType), 'SigLocationId')
                LocationIdAvailable = dict(zip(LocationIdAvailable.keys(), LocationIdAvailable.values()))

                for LocationId in PatternLocationId:
                            key, val = LocationId.split(':')
                            if val:
                                val = val.lower()
                                val = ''.join(lib.getFileRule(int(LocationIdAvailable[str(val)]), int(ClusterType), 'SigLocationId'))
                                LocationIdDict.update({key: str(val)})
                patternLocationIdDict.update({'patternLocationIdDict': LocationIdDict})
                data.update(patternLocationIdDict)


            if 'PatternOffset' in request.POST and 'OFFSET' in ClusterFieldAllowed:
                PatternOffset = request.POST['PatternOffset'].split(',')
                for Offset in PatternOffset:
                    if len(Offset) >1:
                        key, val = Offset.split(':')
                        OffsetDict.update({key: str(val)})
                patternOffsetDict.update({'patternOffsetDict': OffsetDict})
                data.update(patternOffsetDict)

            if 'PatternBufferSize' in request.POST and 'BUFFER' in ClusterFieldAllowed:
                PatternBufferSize = request.POST['PatternBufferSize'].split(',')
                for BufferSize in PatternBufferSize:
                    if len(BufferSize) >1:
                        key, val = BufferSize.split(':')
                        BufferSizeDict.update({key: str(val)})
                patternBufferSizeDict.update({'patternBufferSizeDict': BufferSizeDict})
                data.update(patternBufferSizeDict)

            if 'PatternDistance' in request.POST and 'DISTANCE' in ClusterFieldAllowed:
                PatternDistance = request.POST['PatternDistance'].split(',')
                for Distance in PatternDistance:
                    if len(Distance) >1:
                        key, val = Distance.split(':')
                        DistanceDict.update({key: str(val)})
                patternDistanceDict.update({'Distance': DistanceDict})
                data.update(patternDistanceDict)

            if 'WEAK_SIG' in ClusterFieldAllowed and 'PatternWeakSigData' in request.POST:
                PatternWeakSigData = request.POST['PatternWeakSigData'].split(',')
                for WeakSig in PatternWeakSigData:
                    if len(WeakSig) > 1:
                        key, val = WeakSig.split(':')
                        weakSig.update({key: str(val)})
                patternWeakSig.update({'patternWeakSig': weakSig})
                data.update(patternWeakSig)

            if 'CLEANUP_TYPE' in ClusterFieldAllowed  and 'PatternCleanUpType' in request.POST:
                cleanTypeAvailable = lib.getFileRule('', int(ClusterType), 'CleanupType')
                cleanTypeAvailable = dict(zip(cleanTypeAvailable.keys(), cleanTypeAvailable.values()))
                PatternCleanUpType = request.POST['PatternCleanUpType'].split(',')
                for cleanUpType in PatternCleanUpType:
                        key, val = cleanUpType.split(':')
                        val = val.lower()
                        val = ''.join(lib.getFileRule(int(cleanTypeAvailable[str(val)]), int(ClusterType), 'CleanupType'))
                        cleanupType.update({key: val})
                patterncleanUpType.update({'patterncleanUpType': cleanupType})
                data.update(patterncleanUpType)

                PatternStartTokenData = request.POST['PatternStartTokenData'].split(',')
                for startTokenData in PatternStartTokenData:
                    key, val = startTokenData.split(':')
                    startToken.update({key: val})
                patternStartTokenData.update({'StartToken': startToken})
                data.update(patternStartTokenData)

                PatternEndTokenData = request.POST['PatternEndTokenData'].split(',')
                for endTokenData in PatternEndTokenData:
                    key, val = endTokenData.split(':')
                    endToken.update({key: val})
                patternEndTokenData.update({'EndToken': endToken})
                data.update(patternEndTokenData)

            if 'PatternComments' in request.POST:
                key = 65
                PatternComment = request.POST.getlist('PatternComments')
                for comment in PatternComment:
                    if comment != '':
                        patternComm.update({chr(key): str(comment)})
                    key += 1
                pattentComment.update({'Comment': patternComm})
                data.update(pattentComment)

            signature = request.POST['SignatureData'].split(',')
            for pattern in signature:
                key,val = pattern.split(':')
                sig.update({key:str(val)})
            sigData.update({'sig': sig})
            data.update(sigData)

            if 'Key' in request.POST and len(request.POST['Key']) != 0:
                Sigkeys = request.POST.getlist('Key')
                Sigvalue = request.POST.getlist('Value')
                for idx,key in enumerate(Sigkeys):
                    keyValueData[str(key)] = Sigvalue[idx]
                data.update(keyValueData)

            fileType = request.POST.getlist('FileType')
            fileType = lib.fileTypeJoin(fileType)

            if 'FILTER' in ClusterFieldAllowed and 'FilterField' in request.POST and request.POST['FilterField'] != '':
                FilterField = request.POST['FilterField'].split(",")
                FilterOperation = request.POST['FilterOperation'].split(",")
                FilterFieldInput = request.POST['FilterFieldInput'].split(",")
                filterDict = {}

                FILTER_OPERATION_TYPE_SYM = dict(zip(constant_data.FILTER_OPERATION_TYPE_SYM.values(),constant_data.FILTER_OPERATION_TYPE_SYM.keys()))

                filterTypeArr = lib.getFileSectionDetails(int(ClusterType), 'FilterOperation')
                filterTypeArr = dict(zip(filterTypeArr.values(),filterTypeArr.keys()))

                for filterItem in range(len(FilterField)):
                    FilterFieldKey, FilterFieldVal = FilterField[filterItem].split(':')
                    FilterOperationKey, FilterOperationVal = FilterOperation[filterItem].split(':')
                    FilterFieldInputKey, FilterFieldInputVal = FilterFieldInput[filterItem].split(':')

                    if FilterOperationVal != 'OPER_CHECKFLAGS' and FilterOperationVal != 'OPER_NA':
                        FilterOperationVal = html.unescape(FilterOperationVal)
                        FilterOperationVal = filterTypeArr[FILTER_OPERATION_TYPE_SYM[str(FilterOperationVal)]]
                    else:
                        FilterOperationVal = str(FilterOperationVal).lower()
                        FilterOperationVal = filterTypeArr[FILTER_OPERATION_TYPE_SYM[FilterOperationVal]]
                    filterDict.update({FilterFieldKey: {'field': FilterFieldVal, 'oprt':FilterOperationVal,'value': FilterFieldInputVal}})
                data.update({'FILTER':filterDict})

            if 'FILE_TYPE' in ClusterFieldAllowed:
                data.update({'FileType':fileType})

            data.update({'AuthorName':str(request.user)})
            data.update({'SignatureCrcs': 'crc'})

            if 'THREAT_NAME' in ClusterFieldAllowed:
                data.update({'ThreatName': request.POST['ThreatName']})
            if 'SCAN_RULE' in ClusterFieldAllowed and request.POST['ScanRule']:
                data.update({'ScanRule': request.POST['ScanRule']})
            if 'SCAN_RULE_SUSP' in ClusterFieldAllowed and request.POST['ScanRuleSusp']:
                data.update({'ScanRuleSusp': request.POST['ScanRuleSusp']})

            if 'SCAN_RULE' in ClusterFieldAllowed or 'SCAN_RULE_SUSP' in ClusterFieldAllowed:
                ScanRuleSequence = 0
                if 'ScanRuleSequence' in request.POST :
                        if request.POST.get('ScanRuleSequence') :
                            ScanRuleSequence = 1
                data.update({'Sequence': ScanRuleSequence})

            if 'PolyFunIndex' in request.POST and request.POST['PolyFunIndex'] and 'POLYFUNC' in ClusterFieldAllowed:
                data.update({'PolyFunIndex': request.POST['PolyFunIndex']})

            if 'tagsinput' in request.POST and request.POST['tagsinput']:
                data.update({'Tag':request.POST['tagsinput']})

            if 'STATUS' in ClusterFieldAllowed:
                if 'sigStatus' in request.POST and request.POST.get('sigStatus'):
                    data.update({'status': 'silent'})

            if 'State' in request.POST and request.POST['State']:
                data.update({'State':request.POST['State']})

            result = lib.processOutput(request,lib.processData(request,data,ClusterType,ClusterFieldAllowed))
            if 'type' in result and result['type'] == 4:
                return HttpResponseRedirect('/signature/list/')
            elif 'SigId' in result and result['SigId']:
                     if 'State' in request.POST and request.POST['State']:
                         sql = 'update agerecord set agerecord.SigState ='+str(request.POST['State'])+' where agerecord.Record_ID_FK='+str(result['SigId'])
                         lib.db_query(sql)
                     return HttpResponseRedirect('/signature/' + str(result['SigId']) + '/?action=view')
            elif 'SigId' in data and data['SigId']:
                 return HttpResponseRedirect('/signature/'+str(data['SigId'] )+'/?action=view')
            else :
                return HttpResponseRedirect('/signature/list/')

@login_required(login_url='/login/')
def signature_view(request,sid):
    if permissions.accessPermission(request, 'can_manage_signature') == 0 and permissions.accessPermission(request,'can_manage_cluster') == 0:
        messages.error(request, 'No access permission available for cluster & signature management ')
        return HttpResponseRedirect("/logout/")

    allPerm = permissions.getUserGroupPermission(request)
    userGroup = permissions.checkUserGroup(request)
    if request.GET and 'action' in request.GET and request.GET['action'] == 'view':
        sql = 'SELECT agerecord.Record_ID_FK, agerecord.MalwareIndex,agerecord.ClusterId, agerecord.FileType, agerecord.PolyFuncIndex,agerecord.ScanRule, chsum_sigtype.SIG_TYPE_NAME,malwarenames.MAL_NAME,sig_master.SIG_TYPE_FK, cluster.ClusterName,cluster.CreatedBy,cluster.Priority,agerecord.ScanRuleSusp,agerecord.RecCheckFlags,agerecord.RecComment,agerecord.SigState,agerecord.AuthorName from sig_master LEFT Join chsum_sigtype on sig_master.SIG_TYPE_FK = chsum_sigtype.SIG_TYPE LEFT Join malwarenames on sig_master.MAL_NAME_INDEX_FK = malwarenames.MAL_NAME_INDEX Join qh_sig_status on sig_master.SIG_ID = qh_sig_status.SIG_ID_FK AND qh_sig_status.MARK_DELETED = 0 Join agerecord on sig_master.SIG_ID = agerecord.Record_ID_FK JOIN cluster ON agerecord.ClusterId = cluster.ClusterID AND cluster.Status = 1 WHERE sig_master.SIG_ID = "'+str(sid)+'"'
        recordData = lib.db_query(sql,1)

        if recordData is None:
            messages.info(request, "Signature record is removed or invalid request.")
            return HttpResponseRedirect(reverse('portal:signature_list'))

        permision_type = str(recordData[6]).lower()
        if 'can_view_'+str(permision_type) not in allPerm:
            if 'Manager' not in userGroup.keys():
                messages.error(request, 'View permission not available for ' + str(permision_type).upper())
                return HttpResponseRedirect(reverse('portal:signature_list'))

        if len(recordData) == 0 or recordData is None:
            messages.info(request, "Signature record is removed or invalid request.")
            return HttpResponseRedirect(reverse('portal:signature_list'))
        class data:
            pass

        sql = 'select Sig,`Offset`,LocId,BuffSize,CleanupType,SigCheckFlags,SigComment,Distance,StartToken,EndToken  from agesig where Record_ID_FK = "'+str(sid)+'" order by AgeSig_ID '
        sigRecordData = lib.db_query(sql)

        ClusterFieldAllowed = constant_data.TypeFieldArry[recordData[8]]

        CleanupType,locId,Offset,BuffSize,signatures,i,Comment = 0,'','','',{},65,'-'
        startToken, endToken = '', ''
        for item in sigRecordData:
                if 'CLEANUP_TYPE' in ClusterFieldAllowed:

                    CleanupType = ''.join(lib.getFileRule(int(item[4]), int(recordData[8]), 'CleanupType'))
                    if CleanupType == '':
                        CleanupType = 'None'
                    if item[8] != 'NULL' or item[9] != 'NULL':
                        startToken = str(item[8])
                        endToken = str(item[9])
                if 'LOCATION_ID' in ClusterFieldAllowed and item[2] != 0:
                    locId = ''.join(lib.getFileRule(item[2], int(recordData[8]), 'SigLocationId'))
                if 'OFFSET' in ClusterFieldAllowed:
                    Offset = str(item[1])
                if 'BUFFER' in ClusterFieldAllowed:
                    BuffSize = str(item[3])
                if 'DISTANCE' in ClusterFieldAllowed:
                         Distance = str(item[7])
                if item[6] != 'None' or item[6] != "NULL" or item[6]!= '':
                    Comment = item[6]
                if 'WEAK_SIG' in ClusterFieldAllowed:
                    WeakSig = 'Disabled';
                    if lib.checkFlag(item[5],lib.gen_inx_weak_sig):
                        WeakSig = 'Enabled';
                else:
                    WeakSig = item[5]
                signatures.update({chr(i): {'pattern':str(item[0]),'Offset':str(Offset),'LocId':str(locId),'BuffSize':str(BuffSize),'CleanupType':str(CleanupType),'startToken':startToken,'endToken':endToken,'WeakSig':WeakSig,'Comment':Comment,'Distance':Distance}})
                i += 1

        if 'FILTER' in ClusterFieldAllowed:
            sql = 'select FilterID,Oprt,OprdVal from agefilter where Record_ID_FK = "' + str(sid) + '" order by Filter_ID '
            filterRecordData = lib.db_query(sql)
            filterRecord, i = [], 1
            fileTypeArr = lib.getFileSectionDetails(recordData[8], 'FilterField')
            FilterOperationTypeArr = lib.getFileSectionDetails(recordData[8], 'FilterOperation')
            for item in filterRecordData:
                for key, value in fileTypeArr.items():
                    if value == str(item[0]):
                        FilterFieldData = key
                for key, value in FilterOperationTypeArr.items():
                    if value == str(item[1]):
                        FilterOperationData = constant_data.FILTER_OPERATION_TYPE_SYM[value]
                filterRecord.append({'id': int(i), 'FilterField': FilterFieldData.upper(), 'FilterOperation': FilterOperationData.upper(),'FilterFieldInput': str(item[2])})
                i += 1
            setattr(data, 'filterRecord', filterRecord)

        setattr(data, 'ClusterFieldAllowed', ClusterFieldAllowed)
        fileType = lib.getFileRule(recordData[3],recordData[8],'FileType')
        lib.setMetaInformation(request,[('signature')],"Signature : "+str(sid),OrderedDict( [('Signature','/signature/list/'),(str(sid),'')]))
        setattr(data,'MalwareIndex',recordData[1])

        setattr(data,'sid',sid)
        setattr(data,'signatures',OrderedDict(sorted(signatures.items())))

        if 'THREAT_NAME' in ClusterFieldAllowed:
            setattr(data,'ThreatName',recordData[7])
        if 'FILE_TYPE' in ClusterFieldAllowed:
            setattr(data,'fileType',fileType)
        if 'SCAN_RULE' in ClusterFieldAllowed:
            setattr(data,'ScanRule',recordData[5])
        if 'SCAN_RULE_SUSP' in ClusterFieldAllowed:
            setattr(data,'ScanRuleSusp',recordData[12])
        if 'POLYFUNC' in ClusterFieldAllowed:
            setattr(data,'PolyFuncIndex',recordData[4])

        ScanRuleSequence = 'Disabled'
        if lib.checkFlag(int(recordData[13]),lib.gen_inx_flag_sequence):
            ScanRuleSequence = 'Enabled'
        setattr(data, 'ScanRuleSequence', ScanRuleSequence)

        if 'SUS_WEAK_DETECTION' in ClusterFieldAllowed:
            susWeakDetection = 'Disabled'
            if lib.checkFlag(recordData[13], lib.gen_inx_flag_weak_detection):
                susWeakDetection = 'Enabled'
            setattr(data, 'susWeakDetection', susWeakDetection)

        if 'STATUS' in ClusterFieldAllowed:
            status = 'Disabled'
            if lib.checkFlag(recordData[13], lib.gen_inx_flag_silent):
                status = 'Enabled'
            setattr(data, 'status', status)
        setattr(data, 'clusterType', recordData[8])

        setattr(data, 'State', constant_data.SIG_STATE[recordData[15]])
        setattr(data, 'AuthorName', str(recordData[16]))


        if recordData[14] != None:
            recordComment = str(recordData[14])
            setattr(data, 'RecordComment', recordComment)
        setattr(data,'cluster',{'id':recordData[2],'cluster_name':recordData[9],'cluster_createdby':recordData[10],'cluster_priority':recordData[11],'type':recordData[6]})

        #Malware index history
        sql = 'select agerecord.Record_ID_FK,malwarenames.MAL_NAME, agerecord.SigCnt, agerecord.TimeStamp, agerecord.AuthorName from sig_master join qh_sig_status on sig_master.SIG_ID = qh_sig_status.SIG_ID_FK join malwarenames on sig_master.MAL_NAME_INDEX_FK = malwarenames.MAL_NAME_INDEX join agerecord on sig_master.SIG_ID = agerecord.Record_ID_FK where sig_master.SIG_TYPE_FK ='+str(recordData[8])+' and agerecord.MalwareIndex ='+str(recordData[1])+' and qh_sig_status.DATE_DELETED is not NULL order by  agerecord.TimeStamp desc ; '
        malwareIndexHistory  = lib.db_query(sql,10)
        setattr(data, 'malwareIndexHistory',malwareIndexHistory)

        #tag input
        sql = 'select record_tag.TagName from  record_tag inner join tag_list on record_tag.TagID = tag_list.TagID where  tag_list.SigID=' + str(sid)
        tagResultData = lib.db_query(sql)
        if tagResultData:
            setattr(data, 'tagResult', getTagResult(tagResultData))

        editPerm = 0
        if 'can_edit_' + str(permision_type) not in allPerm or recordData[15] not in permissions.checkStatePermission(request) or recordData[15] in [6,7] or permissions.accessPermission(request, 'can_manage_signature') == 0:
                editPerm = 1
        if 'Manager' in userGroup.keys():
            editPerm = 0

        setattr(data, 'editPerm', editPerm)
        return render(request, 'portal/signature-view.html',{'data': data})
    else:
        return HttpResponseRedirect('/signature/list/')

@login_required(login_url='/login/')
def signature_list(request):
    lib.setMetaInformation(request,[('signature'),('signature_list')],'Signature List',OrderedDict( [('Signature List','')]))
    data = lib.db_query('select MalwareIndex from agerecord')
    return render(request, 'portal/signature-list.html',{'data':data})


@login_required(login_url='/login/')
def signature_delete(request,recordId):
    if permissions.accessPermission(request,'can_manage_signature') == 0:
        messages.error(request,'Signature management permission not available')
        return HttpResponseRedirect("/signature/"+recordId+"/?action=view")

    userGroup = permissions.checkUserGroup(request)
    sql = 'select sig_master.SIG_TYPE_FK from sig_master where sig_master.SIG_ID='+str(recordId)
    sigType = lib.db_query(sql,1)
    if sigType:
        permision_type = str(constant_data.CLUSTER_TYPE[sigType[0]]).lower()
        if 'can_edit_' + str(permision_type) not in permissions.getUserGroupPermission(request):
            if 'Manager' not in userGroup.keys():
                messages.error(request, 'Delete permission not available for ' + str(permision_type).upper())
                return HttpResponseRedirect('/signature/' + str(recordId) + '/?action=view')
    filePath =settings.DATA_FOLDER+"delete_ini\\"+str("{:%Y%m%d_%H%M%S}".format(datetime.datetime.now()))+str('_delete.txt')
    file = open(filePath,'w')
    file.write(recordId)
    file.close()
    lib.runTool(filePath,filePath,'del')
    return HttpResponseRedirect('/signature/list/')

def signature_list_ajax(request):

    Perm_Type_Arr = permissions.checkclusterTypePermission(request)
    start = request.GET['start']
    length = request.GET['length']
    draw = request.GET['draw']
    actualColumns = ['agerecord.Record_ID_FK','agerecord.MalwareIndex','malwarenames.MAL_NAME','agerecord.SigCnt','chsum_sigtype.SIG_TYPE_NAME','cluster.ClusterName','agerecord.SigState','agerecord.AuthorName']
    sigType = tuple(constant_data.CLUSTER_TYPE.keys())

    if len(Perm_Type_Arr):
        if len(Perm_Type_Arr) == 1:
            sigType = "(" + str(Perm_Type_Arr[0]) + ")"
        else:
            sigType = tuple(Perm_Type_Arr)
    else:
        resp = {"draw": draw, "recordsTotal": 0, "recordsFiltered": 0, "data": ''}
        return HttpResponse(json.dumps(resp), content_type='application/json')
    if 'ClusterId' in request.GET and request.GET['ClusterId']:
        ClusterId = request.GET['ClusterId']
        sql = 'SELECT  count(sig_master.SIG_ID) from sig_master join qh_sig_status on sig_master.SIG_ID = qh_sig_status.SIG_ID_FK join malwarenames on sig_master.MAL_NAME_INDEX_FK = malwarenames.MAL_NAME_INDEX join agerecord on sig_master.SIG_ID = agerecord.Record_ID_FK join cluster on  agerecord.ClusterID = cluster.ClusterID JOIN chsum_sigtype ON sig_master.SIG_TYPE_FK = chsum_sigtype.SIG_TYPE   where agerecord.ClusterID='+str(ClusterId)+' and sig_master.SIG_TYPE_FK in '+str(sigType)+' and qh_sig_status.MARK_DELETED = 0 and cluster.Status = 1 '

    elif 'tid' in request.GET and request.GET['tid']:

        tid = str(request.GET['tid'])
        sql = 'select tag_list.SigID from tag_list where tag_list.TagID = "'+str(tid)+'" '
        tData = lib.db_query(sql)

        tDataString = ''
        for sigid in tData:
            tDataString += str(sigid[0])+","
        tDataString = tDataString[0:-1]
        sql = 'SELECT  count(sig_master.SIG_ID) from sig_master join qh_sig_status on sig_master.SIG_ID = qh_sig_status.SIG_ID_FK join malwarenames on sig_master.MAL_NAME_INDEX_FK = malwarenames.MAL_NAME_INDEX join agerecord on sig_master.SIG_ID = agerecord.Record_ID_FK join cluster on  agerecord.ClusterID = cluster.ClusterID JOIN chsum_sigtype ON sig_master.SIG_TYPE_FK = chsum_sigtype.SIG_TYPE   where agerecord.Record_ID_FK in ('+str(tDataString)+')  and qh_sig_status.MARK_DELETED = 0 and cluster.Status = 1 '
        if Perm_Type_Arr:
            sql += 'and sig_master.SIG_TYPE_FK in '+str(sigType)
    else:
        sql = 'SELECT  count(sig_master.SIG_ID) from sig_master join qh_sig_status on sig_master.SIG_ID = qh_sig_status.SIG_ID_FK join malwarenames on sig_master.MAL_NAME_INDEX_FK = malwarenames.MAL_NAME_INDEX join agerecord on sig_master.SIG_ID = agerecord.Record_ID_FK join cluster on  agerecord.ClusterID = cluster.ClusterID JOIN chsum_sigtype ON sig_master.SIG_TYPE_FK = chsum_sigtype.SIG_TYPE  where sig_master.SIG_TYPE_FK in '+str(sigType)+' and qh_sig_status.MARK_DELETED = 0 and cluster.Status = 1 '

    signatureRecordAge = lib.db_query(sql,1)

    searchColArr,i,orderString,where_text =[],0,'',''

    revState = dict(zip(constant_data.SIG_STATELIST.values(), constant_data.SIG_STATELIST.keys()))
    for col in actualColumns:
        if request.GET['columns['+str(i)+'][search][value]'] :
            if i == 4 or i == 7:
                searchColArr.append({'column': col, 'value': str(str(request.GET['columns[' + str(i) + '][search][value]'])),'operator': 1})
            elif i == 6:
                if str(request.GET['columns[' + str(i) + '][search][value]']) in revState:
                  searchColArr.append({'column': col, 'value': str(revState[str(request.GET['columns[' + str(i) + '][search][value]'])]), 'operator': 1})
                else:
                    searchColArr.append({'column': col, 'value': str(str(request.GET['columns[' + str(i) + '][search][value]']))})
            else:
                searchColArr.append({'column':col,'value':request.GET['columns['+str(i)+'][search][value]']})
        if 'order[0][column]' in  request.GET :
            if str(request.GET['order[0][column]']) == str(i):
                orderString = ' order by '+str(col)+' '+str(request.GET['order[0][dir]'])
        i += 1
    i = len(searchColArr)

    if len(searchColArr) > 0:
        where_text += " and  "
    for searchString in  searchColArr:
        i -= 1
        if i == 0:
            if 'operator' in searchString and searchString['operator'] == 1:
                where_text += searchString['column'] + ' =  "' + searchString['value'] + '" '
            else:
                where_text += searchString['column'] + ' like "%' + searchString['value'] + '%" '
        else :
            if 'operator' in searchString and searchString['operator'] == 1:
                where_text += searchString['column'] + ' =  "' + searchString['value'] + '" and '
            else:
                where_text += searchString['column'] + ' like "%' + searchString['value'] + '%" and '

    if len(searchColArr):
        sqlFilCount = sql+where_text
        DataCountFilTotal = lib.db_query(sqlFilCount,1)
    else:
        DataCountFilTotal = signatureRecordAge

    if 'ClusterId' in request.GET and request.GET['ClusterId']:
        ClusterId = request.GET['ClusterId']
        sql = 'select agerecord.Record_ID_FK , agerecord.MalwareIndex,malwarenames.MAL_NAME,agerecord.SigCnt,cluster.ClusterName,cluster.ClusterID,chsum_sigtype.SIG_TYPE_NAME,agerecord.SigState,agerecord.AuthorName  from sig_master join qh_sig_status on sig_master.SIG_ID = qh_sig_status.SIG_ID_FK join malwarenames on sig_master.MAL_NAME_INDEX_FK = malwarenames.MAL_NAME_INDEX join agerecord on sig_master.SIG_ID = agerecord.Record_ID_FK join cluster on  agerecord.ClusterID = cluster.ClusterID JOIN chsum_sigtype ON sig_master.SIG_TYPE_FK = chsum_sigtype.SIG_TYPE  where  agerecord.ClusterID ='+str(ClusterId)+' and sig_master.SIG_TYPE_FK in '+str(sigType)+' and qh_sig_status.MARK_DELETED = 0 and cluster.Status = 1  ' + str(where_text) + '  ' + orderString + ' limit ' + start + ',' + length
    elif 'tid' in request.GET and request.GET['tid']:
        if Perm_Type_Arr:
               where_text += ' and sig_master.SIG_TYPE_FK in ' + str(sigType)
        sql = 'select agerecord.Record_ID_FK , agerecord.MalwareIndex,malwarenames.MAL_NAME,agerecord.SigCnt,cluster.ClusterName,cluster.ClusterID,chsum_sigtype.SIG_TYPE_NAME,agerecord.SigState,agerecord.AuthorName   from sig_master join qh_sig_status on sig_master.SIG_ID = qh_sig_status.SIG_ID_FK join malwarenames on sig_master.MAL_NAME_INDEX_FK = malwarenames.MAL_NAME_INDEX join agerecord on sig_master.SIG_ID = agerecord.Record_ID_FK join cluster on  agerecord.ClusterID = cluster.ClusterID JOIN chsum_sigtype ON sig_master.SIG_TYPE_FK = chsum_sigtype.SIG_TYPE  where  agerecord.Record_ID_FK in ('+str(tDataString)+')  and qh_sig_status.MARK_DELETED = 0 and cluster.Status = 1  ' + str(where_text) + '  ' + orderString + ' limit ' + start + ',' + length
    else:
        sql = 'select agerecord.Record_ID_FK,agerecord.MalwareIndex,malwarenames.MAL_NAME,agerecord.SigCnt,cluster.ClusterName,cluster.ClusterID,chsum_sigtype.SIG_TYPE_NAME,agerecord.SigState,agerecord.AuthorName   from sig_master join qh_sig_status on sig_master.SIG_ID = qh_sig_status.SIG_ID_FK join malwarenames on sig_master.MAL_NAME_INDEX_FK = malwarenames.MAL_NAME_INDEX join agerecord on sig_master.SIG_ID = agerecord.Record_ID_FK join cluster on  agerecord.ClusterID = cluster.ClusterID JOIN chsum_sigtype ON sig_master.SIG_TYPE_FK = chsum_sigtype.SIG_TYPE  where sig_master.SIG_TYPE_FK in '+str(sigType)+' and qh_sig_status.MARK_DELETED = 0 and cluster.Status = 1  '+str(where_text)+'  '+orderString+' limit '+start+','+length
    recordList = lib.db_query(sql)

    data = []
    for record in recordList:
            viewBtn = '<a href="/signature/'+str(record[0])+'?action=view" class="label label-primary">View</a>'
            data.append({"RecordId":str(record[0]), "MalwareIndex":str(record[1]), "MalwareName": str(lib.trimString(record[2],18)),"SigCount": str(record[3]),'Type':str(record[6]),"ClusterName":"<a href='/cluster/"+str(record[5])+"?action=view'>"+str(lib.trimString(record[4],20))+"</a>",'State':constant_data.SIG_STATELIST[record[7]],'AddedBy':"<a href='/user/"+str(record[8])+"'>"+str(record[8])+"</a>",'view':viewBtn})
    recordsTotal = signatureRecordAge[0]
    recordsFiltered = DataCountFilTotal[0]
    resp = {"draw": draw, "recordsTotal": recordsTotal, "recordsFiltered": recordsFiltered, "data":data}
    return HttpResponse(json.dumps(resp), content_type='application/json')

@login_required(login_url='/login/')
def malware_index_history(request,type,mid,rfk):
    lib.setMetaInformation(request, [('signature')],' History For '+str(constant_data.CLUSTER_TYPE[int(type)])+' TRR_ID : ' +str(mid),OrderedDict([('Signature', '/signature/list/'), ('history - '+str(rfk),'')]))

    sql = 'SELECT Sig,`Offset`,LocId,BuffSize,CleanupType,StartToken,EndToken,SigCheckFlags,Distance,SigComment FROM agesig WHERE Record_ID_FK = "'+str(rfk)+'" ORDER BY AgeSig_ID'
    malwareIndexHistory = lib.db_query(sql)

    sql = 'SELECT malwarenames.MAL_NAME,cluster.ClusterName,agerecord.ClusterId,cluster.Status,agerecord.TimeStamp,qh_sig_status.DATE_DELETED,cluster.CreatedBy,agerecord.ScanRule,agerecord.ScanRuleSusp,agerecord.PolyFuncIndex,cluster.Type,agerecord.RecCheckFlags,agerecord.RecComment,agerecord.FileType FROM sig_master LEFT JOIN chsum_sigtype ON sig_master.SIG_TYPE_FK = chsum_sigtype.SIG_TYPE LEFT JOIN malwarenames ON sig_master.MAL_NAME_INDEX_FK = malwarenames.MAL_NAME_INDEX JOIN qh_sig_status ON sig_master.SIG_ID = qh_sig_status.SIG_ID_FK AND qh_sig_status.MARK_DELETED = 1 JOIN agerecord ON sig_master.SIG_ID = agerecord.Record_ID_FK JOIN cluster ON agerecord.ClusterId = cluster.ClusterID WHERE sig_master.SIG_ID = '+str(rfk)
    historyRecord = lib.db_query(sql, 1)

    ClusterFieldAllowed = constant_data.TypeFieldArry[int(type)]

    if len(malwareIndexHistory) < 1 and len(historyRecord) < 1:
        messages.info(request, "Malware index record is removed or invalid request.")
        return HttpResponseRedirect(reverse('portal:signature_list'))

    class data:
        pass

    historyrecord = {'ThreatName': str(historyRecord[0]), 'ClusterName': lib.trimString(str(historyRecord[1]), 20),
                     'ClusterId': str(historyRecord[2]), 'ClusterStatus': historyRecord[3],
                     'CreatedDate': historyRecord[4], 'DeletedDate': historyRecord[5],
                     'AuthorName': str(historyRecord[6]), 'ScanRule': str(historyRecord[7]),
                     'ScanRuleSusp': str(historyRecord[8]), 'PolyFunIndex': historyRecord[9],
                     'ClusterType': constant_data.CLUSTER_TYPE[historyRecord[10]], 'Comment': str(historyRecord[12])
                     }
    FileType = ''
    if historyRecord[13]:
        FileType = lib.getFileRule(historyRecord[13], int(type), 'FileType')
    if 'SCAN_RULE_SUSP' in ClusterFieldAllowed or 'SCAN_RULE' in ClusterFieldAllowed:
        ScanRuleSequence = 'Disabled'
        if lib.checkFlag(int(historyRecord[11]), lib.gen_inx_flag_sequence):
            ScanRuleSequence = 'Enabled'
        setattr(data, 'ScanRuleSequence', ScanRuleSequence)

    if 'SUS_WEAK_DETECTION' in ClusterFieldAllowed:
        susWeakDetection = 'Disabled'
        if lib.checkFlag(int(historyRecord[11]), lib.gen_inx_flag_weak_detection):
            susWeakDetection = 'Enabled'
        setattr(data, 'susWeakDetection', susWeakDetection)

    if 'STATUS' in ClusterFieldAllowed:
        status = 'Disabled'
        if lib.checkFlag(int(historyRecord[11]), lib.gen_inx_flag_silent):
            status = 'Enabled'
        setattr(data, 'status', status)

    setattr(data, 'ClusterFieldAllowed',ClusterFieldAllowed)

    malwareHistory = malwareIndexHistory
    signatures,i ={},65
    cleanUpType,startToken,endToken,WeakSig,locId='','','','',''
    for record in malwareHistory:
        if 'LOCATION_ID' in ClusterFieldAllowed:
            locId = record[2]
        if 'CLEANUP_TYPE' in ClusterFieldAllowed:
          #  cleanUpType = record[4]
            cleanUpType = ''.join(lib.getFileRule(int(record[4]), int(type), 'CleanupType'))
            if record[5] != 'NULL' and endToken != 'NULL':
                startToken = record[5]
                endToken = record[6]

        if 'WEAK_SIG' in ClusterFieldAllowed:
            WeakSig = 'Disabled';
            if lib.checkFlag(record[7], lib.gen_inx_weak_sig):
                WeakSig = 'Enabled';
        signatures.update({chr(i): {'pattern': str(record[0]), 'offset': str(record[1]), 'LocId': locId,
                                    'BuffSize': str(record[3]), 'CleanupType': str(cleanUpType).upper,
                                    'StartToken': str(startToken), 'EndToken': str(endToken), 'WeakSig': WeakSig,
                                    'Comment': record[9], 'Distance': record[8]}})
        i += 1

    sql = 'select record_tag.TagName from record_tag inner join tag_list on record_tag.TagID = tag_list.TagID where tag_list.SigID=' + str(rfk)
    tagResultData = lib.db_query(sql)

    if tagResultData:
        setattr(data, 'tagresult', getTagResult(tagResultData))

    setattr(data, 'historyrecord', historyrecord)
    setattr(data, 'FileType', FileType)
    setattr(data, 'signatures', sorted(signatures.items()))
    setattr(data, 'ClusterFieldAllowed',ClusterFieldAllowed)

    return render(request, 'portal/malware_index_history.html', {'data':data})

@login_required(login_url='/login/')
def downloadIniFile(request):
    iniData = {}
    sql = 'SELECT agerecord.Record_ID_FK, agerecord.MalwareIndex,agerecord.ClusterId, agerecord.FileType, agerecord.PolyFuncIndex,agerecord.ScanRule, chsum_sigtype.SIG_TYPE_NAME,malwarenames.MAL_NAME,sig_master.SIG_TYPE_FK, cluster.ClusterName,cluster.CreatedBy,cluster.Priority,agerecord.ScanRuleSusp,agerecord.RecCheckFlags,agerecord.RecComment,agerecord.SigState from sig_master LEFT Join chsum_sigtype on sig_master.SIG_TYPE_FK = chsum_sigtype.SIG_TYPE LEFT Join malwarenames on sig_master.MAL_NAME_INDEX_FK = malwarenames.MAL_NAME_INDEX Join qh_sig_status on sig_master.SIG_ID = qh_sig_status.SIG_ID_FK AND qh_sig_status.MARK_DELETED = 0 Join agerecord on sig_master.SIG_ID = agerecord.Record_ID_FK JOIN cluster ON agerecord.ClusterId = cluster.ClusterID AND cluster.Status = 1 WHERE sig_master.SIG_ID = ' + str(request.GET.get('id'))
    data = lib.db_query(sql,1)
    print(sql)

    ClusterFieldAllowed = constant_data.TypeFieldArry[data[8]]

    if data == None:
        return HttpResponse('Invalid Record')
    sql = 'select Sig,`Offset`,LocId,BuffSize,CleanupType,StartToken,EndToken,SigCheckFlags,SigComment,Distance from agesig where Record_ID_FK = "'+str(request.GET['id'])+'" order by AgeSig_ID '
    sigRecordData = lib.db_query(sql)

    iniData.update({'SigId':str(request.GET['id'])})
    iniData.update({'MalwareIndex':data[1]})

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
    if data[15]:
        iniData.update({'State': constant_data.SIG_STATE[data[15]]})
    signatures,i,offset,buffsize,locId,cleanUpType,startToken,endToken,WeakSig,Comment= {},65,'','','','','','','',''
    for pettern in sigRecordData:
        pattern = pettern[0]
        if 'OFFSET' in ClusterFieldAllowed:
            offset = pettern[1]
        if 'BUFFER' in ClusterFieldAllowed:
            buffsize = pettern[3]
        if 'LOCATION_ID' in ClusterFieldAllowed:
            locId = pettern[2]
        if 'CLEANUP_TYPE' in ClusterFieldAllowed:
            cleanUpType = pettern[4]
            startToken = pettern[5]
            endToken = pettern[6]
        if 'WEAK_SIG' in ClusterFieldAllowed:
            WeakSig = 0;
            if lib.checkFlag(pettern[7], lib.gen_inx_weak_sig):
                WeakSig = 1;
        if pettern[8] != 'None':
            Comment = pettern[8]
        if 'DISTANCE' in ClusterFieldAllowed:
            Distance = pettern[9]
        signatures.update({chr(i): {'pattern': pattern, 'offset': offset, 'buffsize':buffsize,'locId': locId, 'cleanUpType': cleanUpType,'startToken':startToken,'endToken':endToken,'WeakSig':WeakSig,'Distance':Distance,'Comment':Comment}})
        i += 1
        iniData.update({'sig':signatures,'clusterType':data[8]})

    if 'FILE_TYPE' in ClusterFieldAllowed:
        FileType = lib.fileTypeJoin(lib.getFileRule(data[3],data[8],'FileType'))
        iniData.update({'FileType':FileType})
    if 'FILTER' in ClusterFieldAllowed:
        sql = 'select FilterID,Oprt,OprdVal from agefilter where agefilter.Record_ID_FK = '+str(request.GET.get('id'))
        filterRecord = lib.db_query(sql)
        if filterRecord != None:
            FilterFieldArrRev = lib.getFileSectionDetails(constant_data.CLUSTER_TYPE_NAME[constant_data.CLUSTER_TYPE[data[8]]], 'FilterField')
            FilterFieldArr = dict(zip(FilterFieldArrRev.values(), FilterFieldArrRev.keys()))
            FilterOperationArrRev = lib.getFileSectionDetails(constant_data.CLUSTER_TYPE_NAME[constant_data.CLUSTER_TYPE[data[8]]], 'FilterOperation')
            FilterOperationArr = dict(zip(FilterOperationArrRev.values(), FilterOperationArrRev.keys()))
            FilterFieldValues = {}
            i = 1
            for filterItem in filterRecord:
                FilterFieldValues.update({i: {'field': FilterFieldArr[str(filterItem[0])], 'oprt': FilterOperationArr[str(filterItem[1])],'value': filterItem[2]}})
                i += 1
            iniData.update({'FILTER':FilterFieldValues})

    sql = 'select record_tag.TagName from record_tag inner join tag_list on record_tag.TagID = tag_list.TagID where tag_list.SigID=' + str(request.GET['id'])
    tagResultData = lib.db_query(sql)
    if tagResultData:
        iniData.update({'tagResult':  getTagResult(tagResultData)})

    response = HttpResponse(lib.createSignatureIni(iniData), content_type='application/plain')
    fileName = str(data[7])+"_"+str(request.GET['id'])+"_"+str(data[1])
    response['Content-Disposition'] = 'attachment; filename="' + str(fileName) + '.ini"'
    return response

def getTagResult(tagResultData):
    tagResult = ''
    for tag in tagResultData:
        tagResult += str(tag[0]) + ','
    tagResult = tagResult[:-1]
    return tagResult