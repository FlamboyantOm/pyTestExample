from . import lib,constant_data

def getMultiSelectData(request,clusterId,type,data={}):
    MultiOption = constant_data.MultiOption[type]
    if int(type) in data:
        optionSelected = data[int(type)]
    else :
        optionSelected = []
    dropOption  = lib.users_with_perm(MultiOption['perm'] )
    fileTypeSelect = ' <label for="State">'+str(MultiOption['lable'])+'</label>'
    fileTypeSelect += '<div ><select name="dropClusterOption_'+str(type)+'" class="selectpicker"  id="dropClusterOption_'+str(type)+'"  multiple data-selected-text-format="count">'
    for item in dropOption:
        if str(item) in optionSelected:
            fileTypeSelect += '<option value="'+str(item)+'" selected="selected">'+str(item)+'</option>'
        else:
            fileTypeSelect += '<option value="'+str(item)+'" >'+str(item)+' </option>'
    fileTypeSelect += '</select></div>'
    return fileTypeSelect

# def clusterSelectDropDown(request,ClusterId=''):
#     if request.GET.get('cid'):
#         ClusterId = int(request.GET.get('cid'))
#     else:
#         ClusterId = ClusterId
#     clusterDropDown = '<select name="ClusterId" id="ClusterId" class="form-control">'
#     clusterDropDown += '<option value="">--Select Cluster--</option>'
#     clusterDropDown += '<option value='+str(ClusterId)+' class="col-xs-4 " selected="selected" ><p class="col-xs-4">'+str(ClusterId)+' :</p>&nbsp;<p class="col-xs-4">'+str(ClusterId)+'</p></option>'
#     clusterDropDown += "</select>"
#     return clusterDropDown

def malwareIndexDropDown(threatName=''):
    sql = 'select malwarenames.MAL_NAME from malwarenames'
    malwareName = lib.db_query(sql)
    malwareList = []
    malwareDropDown = '<input type="text" name="ThreatName"  class="form-control autocomplete" id="ThreatName" value="'+str(threatName)+'" placeholder="Enter ThreatName" autocomplete="on" list="malwareDatalist" >'
    malwareDropDown +='<datalist id="malwareDatalist">'
    for malwareName in malwareName:
        malwareList.append(malwareName[0])
        malwareDropDown += '<option value="'+str(malwareName[0])+'"></option>'
    malwareDropDown += '</datalist>'

    return malwareDropDown


def clusterDropDown(arrList,id,name,label,required=0,selectedValue='',event=''):
    dropDown = ''
    if arrList:
        if required == 1:
            dropDown = "<label for='"+str(label)+"'>"+str(label)+"<span style='color:red;'> *</span></label>"
        else:
            dropDown =  "<label for='"+str(label)+"'>"+str(label)+"</label>"

        dropDown += "<select name='" + str(name) + "' class='form-control' id='" + str(id) + "' " + str(event) + ">"
        if selectedValue != '':
            for key, value in arrList:
                if str(selectedValue) == str(key):
                    dropDown += "<option selected='selected' value=" + str(key) + " >" + str(value) + "</option>"
                else:
                    if label != 'Type':
                        dropDown += "<option value=" + str(key) + " >" + str(value) + "</option>"
            dropDown += "</select>"
        else:
            dropDown += "<option value=''>--Select--</option>"
            for key, value in arrList:
                dropDown += "<option value=" + str(key) + " >" + str(value) + "</option>"
            dropDown += "</select>"
    return dropDown

def clusterTypeDropDown(TypeArr,selectedType=''):
    # if TypeArr:
    #     clusterType = "<label for='Type'>Type<span style='color:red;'> *</span></label>"
    #     if selectedType != '':
    #         if int(selectedType) in constant_data.TYPE.keys():
    #             clusterType += "<select name='Type' class='form-control' id='Type'>"
    #             for key, value in TypeArr:
    #                 if str(selectedType) == str(key):
    #                     clusterType += "<option selected='selected' value=" + str(key) + " >" + str(value) + "</option>"
    #             clusterType += "</select>"
    #     else:
    #         clusterType += "<select name='Type' class='form-control' id='Type' >"
    #         clusterType +=  "<option value=''>--Select--</option>"
    #         for key,value in TypeArr:
    #              clusterType += "<option value="+str(key)+" >"+str(value)+"</option>"
    #         clusterType += "</select>"
    # else:
    #     clusterType = ''
    clusterType = clusterDropDown(TypeArr, 'Type','Type' ,'Type', 1, selectedType,'')
    return clusterType

def clusterPriorityDropDown(selectedPriority=''):
    priorityArr = constant_data.CLUSTER_PRIORITY
    if selectedPriority == '':
        selectedPriority = 5
    # clusterPriority = '<label for="priority">Cluster Priority<span style="color:red;"> *</span></label>'
    # clusterPriority += '<select name="Priority" class="form-control" id="priority" >'
    # for key,value in sorted(priorityArr.items()):
    #     if str(selectedPriority) == str(value):
    #         clusterPriority += "<option  selected='selected'  value="+str(value)+">"+str(key)+"</option>"
    #     else:
    #         clusterPriority += "<option value=" + str(value) + ">" + str(key) + "</option>"
    # clusterPriority += "</select>"
    arr = dict(map(reversed, sorted(priorityArr.items())))
    clusterPriority = clusterDropDown(sorted(arr.items()), 'priority','Priority' ,'priority',1,selectedPriority,'')
    return clusterPriority

def clusterProgressDropDown(selectedProgress=''):
    ProgressArr = sorted(constant_data.CLUSTER_PROGRESS.items())
    if selectedProgress == '':
        selectedProgress = 0
    # clusterProgress = '<label for="Progress">Progress in %<span style="color:red;"> *</span></label>'
    # clusterProgress += '<select name="Progress" class="form-control" id="Progress">'
    # for key,value in ProgressArr:
    #     if str(key) == str(selectedProgress):
    #           clusterProgress += '<option selected="selected" value='+str(key)+' >'+str(value)+'</option>'
    #     else:
    #         clusterProgress += '<option value='+str(key)+' >'+str(value)+'</option>'
    # clusterProgress += '</select>'
    clusterProgress = clusterDropDown(ProgressArr, 'Progress', 'Progress', 'Progress in %',1, selectedProgress,'')
    return clusterProgress

def clusterStateDropDown(selectedState='',stateArrr=''):
    if stateArrr:
        StateArr = dict(stateArrr).items()
    else:
        StateArr = sorted(constant_data.SIG_STATE.items())
    # clusterState = ' <label for="State">State<span style="color:red;"> *</span></label>'
    # clusterState += '<select name="State" id="State" class="form-control">'
    # for key,value in StateArr:
    #             if key == 1 or str(key) == str(selectedState):
    #                 clusterState += '<option selected="selected" value='+str(key)+'>'+str(value)+'</option>'
    #             else:
    #                 clusterState += '<option value='+str(key)+' >'+str(value)+'</option>'
    # clusterState +='</select>'
    if selectedState == '':
        selectedState = 1
    clusterState = clusterDropDown(StateArr, 'State', 'State', 'State',1, selectedState,'')
    return clusterState

def clusterSourceDropDown(selectedSource=''):
    sourceArr = sorted(constant_data.CLUSTER_SOURCE.items(), reverse=True)
    # clusterSource = ' <label for="source">Cluster Source<span style="color:red;"> *</span></label>'
    # clusterSource += '<select name="Source" class="form-control" id="Source" onchange="showOtherSource();">'
    # clusterSource += '<option value="">--Select--</option>'
    # for key,value in sourceArr:
    #     if str(key) == str(selectedSource) or str(value) == str(selectedSource):
    #         clusterSource += '<option selected="selected" value='+str(key)+'>'+str(value)+'</option>'
    #     else:
    #         clusterSource += '<option  value=' + str(key) + '>' + str(value) + '</option>'
    # clusterSource += '</select>'

    clusterSource = clusterDropDown(sourceArr, 'Source', 'Source', 'Cluster Source',1, selectedSource,"onchange = 'showOtherSource();'")
    return clusterSource


def clusterAssigneeToDropDown(SignatureManager,selectedAssignUser=''):
    SignatureManager=[str(i) for i in SignatureManager]
    clusterAssignTo = ' <label for="ClusterAssignedTo">Cluster Assigned to<span style="color:red;"> *</span></label>'
    clusterAssignTo += '<select name="ClusterAssignedTo" class="form-control" id="ClusterAssignedTo" >'

    if selectedAssignUser not in SignatureManager and selectedAssignUser != '':
        SignatureManager.append(selectedAssignUser)
        SignatureManager = list(set(SignatureManager))

    clusterAssignTo += '<option value="">--Select--</option>'
    for SignatureManager in SignatureManager:
        if str(SignatureManager) == str(selectedAssignUser):
            clusterAssignTo += '<option selected="selected" value='+str(SignatureManager)+'>'+str(SignatureManager)+'</option>'
        else:
            clusterAssignTo += '<option value=' + str(SignatureManager) + '>' + str(SignatureManager) + '</option>'
    clusterAssignTo += '</select>'

    return clusterAssignTo

def signatureCleanUpTypeDropDown(type,fileTotal=0):
    CleanUpArr = lib.getFileRule('', int(type), 'CleanupType')
    CleanUpArr = map(lambda x: x, list(CleanUpArr.items()))
    cleanTypeAvailable = lib.getFileRule(int(fileTotal), int(type), 'CleanupType')
    signatureCleanUpType = ' <label for="CleanUpType">CleanUpType</label>'
    signatureCleanUpType += '<select name="CleanUpType" id="CleanUpType" class="form-control">'
    CleanUpArr = sorted(CleanUpArr,reverse=True)
    for key,value in CleanUpArr:
        if value in cleanTypeAvailable:
            signatureCleanUpType += '<option selected="selected" value=' + value + '>' + str(key).upper() + '</option>'
        else:
            signatureCleanUpType += '<option value=' + value + ' >' + str(key).upper() + '</option>'
    signatureCleanUpType += '</select>'
    return signatureCleanUpType

def signatureLocationIdDropDown(type,fileTotal=0):
    locTypeArr = lib.getFileRule('', int(type), 'SigLocationId')
    locTypeArr = map(lambda x: x, list(locTypeArr.items()))
    locTypeAvailable = lib.getFileRule(int(fileTotal), int(type), 'SigLocationId')
    signatureLocationId = ' <label for="LocationId">Location Id</label>'
    signatureLocationId += '<select name="LocationId" id="LocationId" class="form-control">'
    for key,value in locTypeArr:
        if value in locTypeAvailable:
            signatureLocationId += '<option selected="selected" value=' + value + '>' + str(key).upper() + '</option>'
        else:
            signatureLocationId += '<option value=' + value + ' >' + str(key).upper() + '</option>'
    signatureLocationId += '</select>'
    return signatureLocationId

def signatureFilterFieldDropDown(type,selectedFilter=''):
    fileTypeArr = lib.getFileSectionDetails(int(type),'FilterField')
    fileTypeArr = map(lambda x: x.upper(), list(fileTypeArr.keys()))
    fileTypeAvailable = lib.getFileRule(int(selectedFilter), int(type),'FilterField')
    fileTypeSelect = '<select name="FilterFieldDropDown"  id="FilterField" class="form-control">'
    fileTypeSelect += '<option value="" selected="selected"> -- Filter Field -- </option>'
    for value in fileTypeArr:
        if value in fileTypeAvailable:
            fileTypeSelect += '<option value="' + str(value) + '" selected="selected">' + str(value) + '</option>'
        else:
            fileTypeSelect += '<option value="' + str(value) + '">' + str(value) + '</option>'
    fileTypeSelect += '</select>'
    return fileTypeSelect

def signatureFilterOperationDropDown(type,selectedFilter=''):
    fileTypeArr = lib.getFileSectionDetails(int(type),'FilterOperation')
    fileTypeAvailable = lib.getFileRule(int(selectedFilter), int(type),'FilterOperation')
    fileTypeSelect = '<select name="FilterOperationDropDown"  id="FilterOperation" class="form-control">'
    fileTypeSelect += '<option value="" selected="selected"> -- Filter Operation -- </option>'
    for value,key in fileTypeArr.items() :
        if value in fileTypeAvailable:
            fileTypeSelect += '<option value="' + str(value).upper() + '" selected="selected">' + str(constant_data.FILTER_OPERATION_TYPE_SYM[key]).upper() + '</option>'
        else:
            fileTypeSelect += '<option value="' + str(value).upper() + '">' + str(constant_data.FILTER_OPERATION_TYPE_SYM[key]).upper() + '</option>'
    fileTypeSelect += '</select>'
    return fileTypeSelect
    return fileTypeSelect

def getFileDropDown(type,fileTotal=0):
    fileTypeArr = lib.getFileRule('',int(type),'FileType')
    fileTypeArr = map(lambda x: x.upper(), list(fileTypeArr.keys()))
    fileTypeAvailable = lib.getFileRule(int(fileTotal),int(type),'FileType')
    fileTypeSelect = '<select name="FileType" class="selectpicker"  id="FileTypeSelect"  multiple data-selected-text-format="count">'
    for value in fileTypeArr:
        if value in fileTypeAvailable:
            fileTypeSelect += '<option value="' + str(value) + '" selected="selected">' + str(value) + '</option>'
        else:
            fileTypeSelect += '<option value="' + str(value) + '">' + str(value) + '</option>'
    fileTypeSelect += '</select>'
    return fileTypeSelect

def signatureTag():
    sql = 'select record_tag.TagID,record_tag.TagName from record_tag; '
    tagResult = lib.db_query(sql)
    tagInput = {}
    if tagResult:
        for tagResult in tagResult:
            tagInput.update({tagResult[0]:tagResult[1]})
    return tagInput