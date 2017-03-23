import os,json,inspect
from django.shortcuts import *
from . import constant_data, lib,dropdown,validation,permissions
from collections import OrderedDict
from django.urls import reverse
from django.contrib import messages
from apex import settings
from .lib import handle_uploaded_file,database_connection_check
from django.contrib.auth.decorators import  login_required
from django.views.decorators.csrf import csrf_exempt


@database_connection_check
@login_required(login_url='/login/')
def cluster(request):
    clusterRequest = {}
    if permissions.accessPermission(request,'can_manage_cluster') == 0 and  permissions.accessPermission(request, 'can_manage_signature') == 0:
        messages.error(request, 'No access permission available for cluster & signature management ')
        return HttpResponseRedirect("/")

   # stateArr = permissions.checkStatePermission(request)

    clusterTypePermArr = permissions.checkclusterTypePermission(request)
    allPerm = permissions.getUserGroupPermission(request)
    userGroup = permissions.checkUserGroup(request)

    # if stateArr == 0:
    #     messages.error(request, 'Cluster state permission not available')
    #     return HttpResponseRedirect("/")

    SignatureManagers = lib.users_with_perms(['role_manager','role_reviewer'])


    if len(clusterTypePermArr):
        clusterTypeArr = constant_data.CLUSTER_TYPE
        for type in list(clusterTypeArr.keys()):
            if type not in clusterTypePermArr:
                clusterTypeArr.pop(type)
    else:
        messages.error(request, 'Cluster type permission not available')
        return HttpResponseRedirect("/")

    if not request.POST:
       # stateArr = dropdown.clusterStateDropDown(1,constant_data.NEW_CLUSTER_STATE)
        lib.setMetaInformation(request, [('cluster'), ('cluster_new')], 'New Cluster',OrderedDict([('Cluster', '/cluster/list/'), ('New Cluster', '')]))
        setattr(request.POST, 'SignatureManagers', SignatureManagers)

        clusterDetails = {}
        clusterDetails.update({'drop_manager':dropdown.getMultiSelectData(request,0,1)})
        clusterDetails.update({'drop_reviewer':dropdown.getMultiSelectData(request,0,2)})
        clusterDetails.update({'drop_qa':dropdown.getMultiSelectData(request,0,3)})

        clusterRequest['clusterDetails'] = clusterDetails

        clusterTypeDropDown = dropdown.clusterTypeDropDown(sorted(clusterTypeArr.items()))

        clusterRequest['clusterProgressDropDown'] = dropdown.clusterProgressDropDown()
        clusterRequest['clusterSourceDropDown'] = dropdown.clusterSourceDropDown()
       # clusterRequest['clusterStateDropDown'] = stateArr
        clusterRequest['clusterTypeDropDown'] = clusterTypeDropDown
        clusterRequest['clusterPriorityDropDown'] = dropdown.clusterPriorityDropDown()
        clusterRequest['clusterAssigneeToDropDown'] = dropdown.clusterAssigneeToDropDown(SignatureManagers)


        return render(request, 'portal/cluster-new.html', {'data': clusterRequest})
        #return render(request, 'portal/cluster-new.html', {'data': request.POST,'clusterProgressDropDown': dropdown.clusterProgressDropDown(),'clusterTypeDropDown':clusterTypeDropDown,'clusterPriorityDropDown':dropdown.clusterPriorityDropDown(),'clusterStateDropDown':stateArr,'clusterSourceDropDown':dropdown.clusterSourceDropDown(),'clusterAssigneeToDropDown':dropdown.clusterAssigneeToDropDown(SignatureManagers)})

    #update
    elif 'ClusterId' in request.POST and request.POST['ClusterId']:
        permision_type = str(constant_data.CLUSTER_TYPE[int(request.POST['Type'])]).lower()

        if constant_data.CLUSTERID != request.POST['ClusterId'] :
            messages.success(request, "Invalid cluster id try again")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        if 'can_edit_' +str(permision_type) not in allPerm:
            if 'Manager' not in userGroup.keys():
                messages.error(request, 'Edit permission not available for '+str(permision_type))
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        # if stateArr == 0 or request.POST['State'] in [6, 7] :
        #   if 'Manager' not in userGroup.keys():
        #     messages.error(request, 'Cluster state permission not available')
        #     return HttpResponseRedirect("/cluster/" + request.POST['ClusterId'] + "/?action=view")

        error_message, data = lib.clusterAdd(request)
        if error_message != 0:
            ClusterName = data['ClusterName']
            lib.setMetaInformation(request, [('cluster')], 'Updating Cluster : ' + str(ClusterName), OrderedDict([('Cluster', '/cluster/list/'), (str(ClusterName), '/cluster/' + str(request.POST['ClusterId']) + '/?action=view'),('Updating ' + str(ClusterName), '')]))
            sql = 'select ClusterFileID,FileName,AddedBy,CreatedDate from clusterfile where clusterfile.ClusterID = ' + str(request.POST['ClusterId']) + ' and clusterfile.status = 1;'
            clusterFiles = lib.db_query(sql)
            record = clusterFiles
            recordData = []
            for record in record:
                FileName = lib.trimString(str(record[1]), 20)
                record = list(record)
                record[1] = FileName
                recordData.append(record)
            clusterFiles = recordData

            clusterRequest['clusterDetails'] = request.POST

            clusterRequest['clusterProgressDropDown'] = dropdown.clusterProgressDropDown(str(request.POST['Progress']))
            clusterRequest['clusterSourceDropDown'] = dropdown.clusterSourceDropDown(str(data['source']))
           # clusterRequest['clusterStateDropDown'] = dropdown.clusterStateDropDown(str(request.POST['State']),stateArr)
            clusterRequest['clusterTypeDropDown'] =  dropdown.clusterTypeDropDown(sorted(clusterTypeArr.items()),request.POST['Type'])
            clusterRequest['clusterPriorityDropDown'] = dropdown.clusterPriorityDropDown(str(request.POST['Priority']))
            clusterRequest['clusterAssigneeToDropDown'] = dropdown.clusterAssigneeToDropDown(SignatureManagers,str(request.POST['ClusterAssignedTo']))
            clusterRequest['clusterFiles'] = clusterFiles
            return render(request, 'portal/cluster-new.html', {'data': clusterRequest})
            #return render(request, 'portal/cluster-new.html', {'data': data,'clusterProgressDropDown': dropdown.clusterProgressDropDown(str(request.POST['Progress'])),'clusterStateDropDown':stateArr,'clusterTypeDropDown':dropdown.clusterTypeDropDown(sorted(constant_data.TYPE.items()), str(request.POST['Type'])),'clusterPriorityDropDown':dropdown.clusterPriorityDropDown(str(request.POST['Priority'])),'clusterSourceDropDown':dropdown.clusterSourceDropDown(str(data['source'])),'clusterAssigneeToDropDown': dropdown.clusterAssigneeToDropDown(SignatureManagers,data['assignto']),'clusterFiles':clusterFiles})

        source = data.get('source')
        if source == "0":
            source = data.get('otherSource')
        returnId = request.POST['ClusterId']
        if request.FILES.get('zipFile'):
            handle_uploaded_file(request,request.FILES['zipFile'], str(returnId),str(inspect.stack()[0][3]))
        sql = "select ClusterName, ClusterNotes, CreatedBy, ClusterAssignedTo,Source, Priority,Type,Progress from cluster where  ClusterID = " + str(request.POST['ClusterId']) + " and Status = 1"
        data = lib.db_query(sql, 1)

        if data == None:
            messages.success(request, "Invalid cluster try again")
            return HttpResponseRedirect("/cluster/" + request.POST['ClusterId'] + "/?action=view")

        clusterDetails = {'ClusterName': str(data[0]), 'ClusterNotes': str(data[1]), 'CreatedBy': str(data[2]),'Assignto': str(data[3]), 'Source': str(data[4]), 'Priority': str(data[5]),'Type':str(data[6]),'Progress':str(data[7])}
       # clusterUpdatedDetails = {'ClusterName': str(request.POST['ClusterName']), 'ClusterNotes': str(request.POST['ClusterNotes']), 'CreatedBy': str(request.user),'Assignto': str(request.POST['ClusterAssignedTo']), 'Source': str(source),'Priority': str(request.POST['Priority']),'Type':str(request.POST['Type']),'State':str(request.POST['State']),'Progress':str(request.POST['Progress'])}
        clusterUpdatedDetails = {'ClusterName': str(request.POST['ClusterName']), 'ClusterNotes': str(request.POST['ClusterNotes']), 'CreatedBy': str(request.user),'Assignto': str(request.POST['ClusterAssignedTo']), 'Source': str(source),'Priority': str(request.POST['Priority']),'Type':str(request.POST['Type']),'Progress':str(request.POST['Progress'])}


        sql = 'select cluster_options.OptionID,cluster_options.OptionValue from cluster_options join cluster on cluster.ClusterID = cluster_options.ClusterID and cluster.`Status`=1 where cluster_options.ClusterID=' + str(request.POST['ClusterId']) + ';'
        clusteroptionDetails = lib.db_query(sql)


        manager,reviewer,qa =[],[],[]
        multioption = {1:manager,2:reviewer,3:qa}

        for option in clusteroptionDetails:
            option = list(option)
            arr = multioption[option[0]]
            arr.append(option[1])

        clusterOption = {'Manager': manager, 'Reviewer': reviewer, 'QA Team': qa}
        clusterOptionUpdatedDetails = {'Manager':sorted(list(request.POST.getlist('dropClusterOption_1'))),'Reviewer':request.POST.getlist('dropClusterOption_2'),'QA Team':request.POST.getlist('dropClusterOption_3')}


        clusterDetails.update(clusterOption)
        clusterUpdatedDetails.update(clusterOptionUpdatedDetails)

        updateArr = {}
        for key, value in clusterDetails.items():
            if value != clusterUpdatedDetails[key]:
                updateArr.update({str(key): {'old': str(value), 'new': str(clusterUpdatedDetails[key])}})

        if updateArr or request.POST['cluster_file_ids']:
            details = str(updateArr)
            if len(updateArr):
               # lib.log_entry('log_cluster', request.POST['ClusterId'], str(request.user), constant_data.ACTIONTYPE[2], str(json.dumps(details)), request.POST['Type'], request.POST['Progress'], request.POST['State'])
                lib.log_entry('log_cluster', request.POST['ClusterId'], str(request.user), constant_data.ACTIONTYPE[2], str(json.dumps(details)), request.POST['Type'], request.POST['Progress'])
            messages.success(request,"#" + str(returnId) + " - cluster " + str(lib.trimString(str(request.POST['ClusterName']), 70)) + " is updated successfully.")
       # sql = "UPDATE cluster SET cluster.ClusterName='" + str(request.POST['ClusterName']) + "',ClusterNotes='" + str(request.POST['ClusterNotes']) + "',CreatedBy='" + str(request.user) + "',ClusterAssignedTo='" + str(request.POST['ClusterAssignedTo']) + "',Source='" + str(source) + "',Priority ='" + str(request.POST['Priority']) + "',Type ='" + str(request.POST['Type']) + "',State ='" + str(request.POST['State']) + "',Progress ='" + str(request.POST['Progress']) + "'  where cluster.ClusterID ='" + returnId + "'"
        sql = "UPDATE cluster SET cluster.ClusterName='" + str(request.POST['ClusterName']) + "',ClusterNotes='" + str(request.POST['ClusterNotes']) + "',CreatedBy='" + str(request.user) + "',ClusterAssignedTo='" + str(request.POST['ClusterAssignedTo']) + "',Source='" + str(source) + "',Priority ='" + str(request.POST['Priority']) + "',Type ='" + str(request.POST['Type']) + "',Progress ='" + str(request.POST['Progress']) + "'  where cluster.ClusterID ='" + returnId + "'"
        lib.db_query(sql, 1)

        #manager insert
        sql = ["delete from cluster_options where cluster_options.ClusterID = "+str(returnId)+" "]
        for option in constant_data.MultiOption:
            for item in request.POST.getlist('dropClusterOption_'+str(option)):
                sql.append("INSERT INTO cluster_options (`ClusterID`, `OptionID`, `OptionValue`) VALUES ("+str(returnId)+", "+str(option)+", '"+str(item)+"')")
        lib.db_insert(sql,1)
        if request.POST['cluster_file_ids']:
            clusterFileIds = request.POST['cluster_file_ids']
            clusterFileIds = "(" + str(clusterFileIds) + ")"
            sql = "UPDATE clusterfile SET clusterfile.ClusterID='" + str(returnId) + "'  where ClusterFileID in " + str(clusterFileIds)
            lib.db_query(sql)
        return HttpResponseRedirect("/cluster/" + request.POST['ClusterId'] + "/?action=view")
    else:

        lib.setMetaInformation(request, [('cluster'), ('cluster_new')], 'New Cluster',OrderedDict([('Cluster', '/cluster/list/'), ('New Cluster', '')]))
        error_message,data = lib.clusterAdd(request)

        source = dict(data).get('source')
        if source == "0":
            source = data.get('otherSource')

        if error_message != 0:
            #stateArr = dropdown.clusterStateDropDown(str(request.POST['State']), stateArr)
            clusterRequest['clusterDetails'] = data
            clusterRequest['clusterProgressDropDown'] = dropdown.clusterProgressDropDown(str(request.POST['Progress']))
            clusterRequest['clusterSourceDropDown'] = dropdown.clusterSourceDropDown(str(source))
           # clusterRequest['clusterStateDropDown'] = stateArr
            #clusterRequest['clusterFiles'] = clusterFiles
            clusterRequest['clusterTypeDropDown'] = dropdown.clusterTypeDropDown(sorted(clusterTypeArr.items()), str(data['Type']))
            clusterRequest['clusterPriorityDropDown'] =  dropdown.clusterPriorityDropDown(str(request.POST['Priority']))
            clusterRequest['clusterAssigneeToDropDown'] = dropdown.clusterAssigneeToDropDown(SignatureManagers,data['assignto'])
            return render(request, 'portal/cluster-new.html', {'data': clusterRequest})
        #sql = "INSERT INTO cluster(`ClusterName`, `ClusterNotes`, `CreatedBy`, `ClusterAssignedTo`, `Source`,`Priority`,`Type`,`State`,`Progress`) VALUES ('" + str(request.POST['ClusterName']) + "','" + str(request.POST['ClusterNotes']) + "','" + str(request.user) + "','" + str(request.POST['ClusterAssignedTo']) + "','" + str(source) + "','" + str(request.POST['Priority']) + "','" + str(request.POST['Type']) + "','" + str(request.POST['State']) + "','" + str(request.POST['Progress']) + "' ) "
        sql = "INSERT INTO cluster(`ClusterName`, `ClusterNotes`, `CreatedBy`, `ClusterAssignedTo`, `Source`,`Priority`,`Type`,`Progress`) VALUES ('" + str(request.POST['ClusterName']) + "','" + str(request.POST['ClusterNotes']) + "','" + str(request.user) + "','" + str(request.POST['ClusterAssignedTo']) + "','" + str(source) + "','" + str(request.POST['Priority']) + "','" + str(request.POST['Type']) + "','" + str(request.POST['Progress']) + "' ) "
        returnId = lib.db_insert(sql)
        addClusterArr = {'ClusterId': str(returnId), 'ClusterName': str(request.POST['ClusterName'])}
        details = str(addClusterArr)
        #lib.log_entry('log_cluster', str(returnId), str(request.user), constant_data.ACTIONTYPE[1], str(json.dumps(details)), str(request.POST['Type']), str(request.POST['Progress']), str(request.POST['State']))
        lib.log_entry('log_cluster', str(returnId), str(request.user), constant_data.ACTIONTYPE[1], str(json.dumps(details)), str(request.POST['Type']), str(request.POST['Progress']))

        # manager insert
        sql = ["delete from cluster_options where cluster_options.ClusterID = " + str(returnId) + " "]
        for option in constant_data.MultiOption:
            for item in request.POST.getlist('dropClusterOption_' + str(option)):
                sql.append("INSERT INTO cluster_options (`ClusterID`, `OptionID`, `OptionValue`) VALUES (" + str(returnId) + ", " + str(option) + ", '" + str(item) + "')")
        lib.db_insert(sql, 1)

        messages.success(request,"#" + str(returnId) + " - cluster " + str(lib.trimString(str(request.POST['ClusterName']), 70)) + " is added successfully.")
        if 'cluster_file_ids' in request.POST and request.POST['cluster_file_ids'] != '':
            cluster_file_ids = request.POST['cluster_file_ids']
            sql = "UPDATE clusterfile SET clusterfile.ClusterID=" + str(returnId) + "  where ClusterFileID in (" + cluster_file_ids+")"
            lib.db_query(sql)
    return HttpResponseRedirect("/cluster/" + str(returnId) + "/?action=view")

@login_required(login_url='/login/')
def cluster_view(request,cid):
    clusterRequest = {}
    if permissions.accessPermission(request, 'can_manage_cluster') == 0 and permissions.accessPermission(request, 'can_manage_signature') == 0:
        messages.error(request,'No access permission available for cluster & signature management')
        return HttpResponseRedirect("/")

    userGroupPerm = permissions.getUserGroupPermission(request)
    userGroup = permissions.checkUserGroup(request)
    constant_data.CLUSTERID = cid
    sql = "select ClusterID, ClusterName, ClusterNotes, CreatedBy, ClusterAssignedTo, CreatedDate, ModifiedDate, Source, Priority,Type,Progress from cluster where  ClusterID = "+str(cid)+" and Status = 1"
    data = lib.db_query(sql,1)


    if data is None:
        messages.info(request,"Cluster is removed or invalid request.")
        return HttpResponseRedirect(reverse('portal:cluster_list'))

    permision_type = str(constant_data.CLUSTER_TYPE[data[9]]).lower()

    if 'can_view_' + str(permision_type) not in userGroupPerm:
        if 'Manager' not in userGroup.keys():
            messages.error(request, 'View permission not available for ' + str(permision_type).upper())
            return HttpResponseRedirect(reverse('portal:cluster_list'))

    ClusterName = lib.trimString(str(data[1]), 45)
    lib.setMetaInformation(request,[('cluster')],'Cluster : '+str(ClusterName),OrderedDict( [('Cluster','/cluster/list/'),(str(ClusterName),'')]))
    ClusterData = data
    Notes = lib.trimString(str(ClusterData[2]),70)
    Source = lib.trimString(str(ClusterData[7]), 15)
    update_data = list(ClusterData)
    update_data[1] = ClusterName
    update_data[2] = Notes
    if str(Source) in constant_data.CLUSTER_SOURCE:
        Source = str(constant_data.CLUSTER_SOURCE[str(Source)])
    update_data[7] = str(Source)
   # update_data[9] = str(constant_data.STATE[data[9]])
   # clusterState = data[9]
    update_data[9] = str(constant_data.CLUSTER_TYPE[ClusterData[9]])
    ClusterData = tuple(update_data)

    if request.GET and 'action' in request.GET:
        recentActivities = lib.clusterLogData(str(1000),'where log_cluster.ClusterID ='+str(data[0]))
        sql = 'select ClusterFileID,FileName,AddedBy,CreatedDate from clusterfile where clusterfile.ClusterID = '+str(data[0])+' and clusterfile.status = 1;'
        clusterFiles = lib.db_query(sql)
        record = clusterFiles
        recordData = []
        for record in record:
            FileName = lib.trimString(str(record[1]),50)
            record = list(record)
            record[1] = FileName
            record[3] = "{:%Y/%m/%d}".format(record[3])
            recordData.append(record)
        clusterFiles = recordData

        typePerm = 0
        editPerm = 0
      #  stateArr = permissions.checkStatePermission(request)

      #  if 'can_edit_' +str(permision_type) not in userGroupPerm or clusterState in [6,7] or permissions.accessPermission(request,'can_manage_signature') == 0:
        if 'can_edit_' +str(permision_type) not in userGroupPerm  or permissions.accessPermission(request,'can_manage_signature') == 0:
                typePerm  = 1

       # if 'can_edit_' +str(permision_type) not in userGroupPerm or clusterState not in stateArr or clusterState in [6,7]:
        if 'can_edit_' +str(permision_type) not in userGroupPerm:
                 editPerm =1

        if 'Manager' in userGroup.keys():
            typePerm = editPerm = 0

        clusterRequest['ClusterData'] = ClusterData
        clusterRequest['ClusterId'] = data[0]
        clusterRequest['recentActivities'] = recentActivities
        clusterRequest['clusterFiles'] = clusterFiles
        clusterRequest['typePerm'] = typePerm
        clusterRequest['editPerm'] = editPerm
        clusterRequest['clusterType'] = data[9]
        sql = "select cluster_options.OptionID, cluster_options.OptionValue from cluster_options where cluster_options.ClusterID = '"+str(data[0])+"'  order by cluster_options.OptionID asc "
        clusterOptData = lib.db_query(sql)

        clusterOpt = {}
        for item in clusterOptData:
            clusterOpt.setdefault(constant_data.MultiOption[item[0]]['lable'],[]).append(item[1])
        clusterRequest['clusterOpt'] = clusterOpt

        return render(request, 'portal/cluster-view.html',{'data':clusterRequest})


    SignatureManagers = lib.users_with_perms(['role_manager','role_reviewer'])

    dataobj = request.POST
    setattr(dataobj, 'SignatureManagers', SignatureManagers)
    zip_file = ''
    zip_dir = settings.UPLOAD_FILE_PATH + 'cluster_files\\'+str(data[0] )+ '.zip'
    if os.path.exists(zip_dir):
        zip_file = open(zip_dir)
        zip_file = zip_file.name.split('/')[-1]

    if str(data[7]) in constant_data.CLUSTER_SOURCE.keys() or str(data[7]) in constant_data.CLUSTER_SOURCE.values():
        clusterDetails = {'ClusterId': data[0], 'ClusterName': str(data[1]), 'ClusterNotes': str(data[2]),'source': str(data[7]), 'priority': data[8], 'assignto': data[4],'SignatureManagers': SignatureManagers, 'zipFile': str(zip_file),'otherSource': '','Type':data[9],'Progress':data[10]}
    else:
        clusterDetails = {'ClusterId': data[0], 'ClusterName': str(data[1]), 'ClusterNotes': str(data[2]),'source':"0", 'priority': data[8], 'assignto': data[4],'SignatureManagers': SignatureManagers, 'zipFile': str(zip_file),'otherSource': data[7],'Type':data[9],'Progress':data[10]}

    if not dataobj:

        if permissions.accessPermission(request, 'can_manage_cluster') == 0 and  permissions.accessPermission(request, 'can_manage_signature') == 0:
            messages.error(request,'Cluster management permission not available')
            return HttpResponseRedirect("/cluster/" + str(data[0]) + "/?action=view")

        #if 'Edit ' + str(permision_type) not in userGroupPerm:
        if 'can_edit_' + str(permision_type) not in userGroupPerm:
            if 'Manager' not in userGroup.keys():
                messages.error(request, 'Edit permission not available for '+str(permision_type))
                return HttpResponseRedirect("/cluster/" + str(data[0]) + "/?action=view")

        # if data[9] in [6,7]:
        #     if 'Manager' not in userGroup.keys():
        #         messages.error(request, 'Unable to edit permission not available')
        #         return HttpResponseRedirect("/cluster/" + str(data[0]) + "/?action=view")

      #  stateArr = permissions.checkStatePermission(request)
        clusterTypeArr = permissions.checkclusterTypePermission(request)

        if str(data[1]):
            ClusterName = lib.trimString(str(data[1]), 15)
            lib.setMetaInformation(request, [('cluster')], 'Updating Cluster : ' + str(ClusterName),OrderedDict([('Cluster', '/cluster/list/'), (str(ClusterName), '/cluster/'+str(data[0])+'/?action=view'),('Updating '+str(ClusterName),'')]))
        else:
            lib.setMetaInformation(request, [('cluster')], 'Updating Cluster : #' + str(data[0]),OrderedDict([('Cluster', '/cluster/list/'), (str(data[0]), '/cluster/'+str(data[0])+'/?action=view'),('Updating '+str(data[0]),'')]))

        sql = 'select ClusterFileID,FileName,AddedBy,CreatedDate from clusterfile where clusterfile.ClusterID = '+str(data[0])+' and clusterfile.status = 1;'
        clusterFiles = lib.db_query(sql)
        record = clusterFiles

        recordData = []
        for record in record:
            FileName = lib.trimString(str(record[1]),20)
            record = list(record)
            record[1] = FileName
            recordData.append(record)
        clusterFiles = recordData

        # if clusterDetails['State'] not in stateArr.keys() or clusterDetails['Type'] not in clusterTypeArr:
        #     messages.error(request,'Unable to update permission not available')
        #     return HttpResponseRedirect("/cluster/" + str(data[0]) + "/?action=view")

        clusterTypeDropDown = dropdown.clusterTypeDropDown(sorted(constant_data.CLUSTER_TYPE.items()), clusterDetails['Type'])
      #  clusterStateDropDown = dropdown.clusterStateDropDown(clusterDetails['State'],stateArr)
        clusterPriorityDropDown = dropdown.clusterPriorityDropDown(clusterDetails['priority'])
        clusterProgressDropDown = dropdown.clusterProgressDropDown(clusterDetails['Progress'])
        clusterSourceDropDown = dropdown.clusterSourceDropDown(str(clusterDetails['source']))
        clusterAssigneeToDropDown = dropdown.clusterAssigneeToDropDown(SignatureManagers,clusterDetails['assignto'])

        sql = "select cluster_options.OptionID, cluster_options.OptionValue from cluster_options where cluster_options.ClusterID = '"+str(data[0])+"'"
        clusterOptData = lib.db_query(sql)
        clusterOpt = {}
        for item in clusterOptData:
            clusterOpt.setdefault(item[0], []).append(item[1])

        clusterDetails.update({'drop_manager':dropdown.getMultiSelectData(request,data[0],1,clusterOpt)})
        clusterDetails.update({'drop_reviewer':dropdown.getMultiSelectData(request,data[0],2,clusterOpt)})
        clusterDetails.update({'drop_qa':dropdown.getMultiSelectData(request,data[0],3,clusterOpt)})

        clusterRequest['clusterDetails'] = clusterDetails
        clusterRequest['clusterProgressDropDown'] = clusterProgressDropDown
        clusterRequest['clusterSourceDropDown'] = clusterSourceDropDown
       # clusterRequest['clusterStateDropDown'] = clusterStateDropDown
        clusterRequest['clusterFiles'] = clusterFiles
        clusterRequest['clusterTypeDropDown'] = clusterTypeDropDown
        clusterRequest['clusterPriorityDropDown'] = clusterPriorityDropDown
        clusterRequest['clusterAssigneeToDropDown'] = clusterAssigneeToDropDown

        return render(request, 'portal/cluster-new.html',{'data':clusterRequest})
        #return render(request, 'portal/cluster-new.html',{'data': clusterDetails, 'clusterProgressDropDown': clusterProgressDropDown,'clusterSourceDropDown': clusterSourceDropDown, 'clusterStateDropDown': clusterStateDropDown,'clusterFiles': clusterFiles, 'clusterTypeDropDown': clusterTypeDropDown,'clusterPriorityDropDown': clusterPriorityDropDown,'clusterAssigneeToDropDown': clusterAssigneeToDropDown})
    return HttpResponseRedirect(reverse('portal:cluster_list'))


@login_required(login_url='/login/')
def cluster_list(request):
    lib.setMetaInformation(request,[('cluster'),('cluster_list')],'Cluster List',OrderedDict( [('Cluster List','')]))
    data = lib.db_query('select ClusterName from cluster')
    return render(request, 'portal/cluster-list.html',{'data':data})

@login_required(login_url='/login/')
def cluster_delete(request,cid):
    if permissions.accessPermission(request, 'can_manage_cluster') == 0:
        messages.error(request,'Cluster management permission not available')
        return HttpResponseRedirect("/cluster/"+cid+"/?action=view")

    sql = "select  ClusterName,CreatedBy,Type,Progress from cluster  where cluster.ClusterID ='" + cid + "'"
    data = lib.db_query(sql, 1)

    if data is None:
        messages.info(request, "Cluster is removed or invalid request.")
        return HttpResponseRedirect(reverse('portal:cluster_list'))

    permision_type = str(constant_data.CLUSTER_TYPE[data[2]]).lower()

    #if 'Edit ' + str(permision_type) not in permissions.getUserGroupPermission(request):
    if 'can_edit_' + str(permision_type) not in permissions.getUserGroupPermission(request):
        messages.error(request, ' Delete permission not available for' + str(permision_type).upper())
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    sql = "UPDATE cluster SET cluster.Status = 0  where cluster.ClusterID ='" + cid + "'"
    lib.db_query(sql,1)
    messages.info(request,"#" + str(cid) + " - cluster " + " is deleted successfully.")
    deleteArr = {'ClusterId':str(cid),'ClusterName':str(data[0]),'CreatedBy':str(data[1])}
    details = str(deleteArr)
    lib.log_entry('log_cluster', cid, str(request.user), constant_data.ACTIONTYPE[3], json.dumps(details), data[2], data[3])
    return HttpResponseRedirect(reverse('portal:cluster_list'))

def cluster_list_ajax(request):
    start = request.GET['start']
    length = request.GET['length']
    draw = request.GET['draw']
   # columns = ['cluster.ClusterID','cluster.ClusterName','cluster.CreatedBy','cluster.ClusterAssignedTo','cluster.CreatedDate','cluster.ModifiedDate','cluster.Source','cluster.Priority','cluster.State','cluster_cnt.SigCnt','cluster.Progress','chsum_sigtype.SIG_TYPE_NAME']
    columns = ['cluster.ClusterID','cluster.ClusterName','cluster.CreatedBy','cluster.ClusterAssignedTo','cluster.CreatedDate','cluster.ModifiedDate','cluster.Source','cluster.Priority','cluster_cnt.SigCnt','cluster.Progress','chsum_sigtype.SIG_TYPE_NAME']
    searchColArr,i,orderString = [],0,''
    where_text = ' where cluster.Status = 1 '


    clusterTypePerm = permissions.checkclusterTypePermission(request)

    if clusterTypePerm:
        if len(clusterTypePerm) == 1:
            Perm_Type_Arr = "(" + str(clusterTypePerm[0]) + ")"
        else:
            Perm_Type_Arr = tuple(clusterTypePerm)
        where_text += ' and cluster.Type in '+str(Perm_Type_Arr)
    else:
        resp = {"draw": draw, "recordsTotal": 0, "recordsFiltered": 0, "data": ''}
        return HttpResponse(json.dumps(resp), content_type='application/json')

    tblClusterCnt = 'SELECT cluster.ClusterId AS ClusterId, COUNT(qh_sig_status.MARK_DELETED) AS SigCnt FROM cluster LEFT JOIN agerecord on cluster.ClusterID = agerecord.ClusterId LEFT JOIN qh_sig_status ON agerecord.Record_ID_FK = qh_sig_status.SIG_ID_FK and qh_sig_status.MARK_DELETED = 0 GROUP BY cluster.ClusterId'
 #   revState = dict(zip(constant_data.STATELIST.values(), constant_data.STATELIST.keys()))
    revSource = dict(zip(constant_data.CLUSTER_SOURCE.values(), constant_data.CLUSTER_SOURCE.keys()))
    for col in columns:
        if request.GET['columns['+str(i)+'][search][value]'] :
            if  i == 6:
                if str(request.GET['columns['+str(i)+'][search][value]']).title() in  revSource:
                    searchColArr.append({'column':col,'value':str(revSource[str(request.GET['columns['+str(i)+'][search][value]']).title()]),'operator': 1})
                else:
                    searchColArr.append({'column': col, 'value':str(request.GET['columns['+str(i)+'][search][value]']).title(), 'operator': 1})

            elif i == 0 or i== 2 or i == 10 or i == 11 or i == 3 or i == 7  or i == 8 or i == 9 :
                searchColArr.append({'column':col,'value':request.GET['columns['+str(i)+'][search][value]'],'operator':1})

            elif i == 4 or i == 5: #for created and modified date
                searchColArr.append({'column': col, 'value': str(request.GET['columns[' + str(i) + '][search][value]']).title(),'operator': 3})
            else :
                searchColArr.append({'column':col,'value':request.GET['columns['+str(i)+'][search][value]'],'operator':2})

        if 'order[0][column]' in  request.GET :
            if str(request.GET['order[0][column]']) == str(i):
                orderString = ' order by '+str(col)+' '+str(request.GET['order[0][dir]'])
        i += 1
    i = len(searchColArr)

    if len(searchColArr) > 0:
        where_text += " and  "

    for searchString in searchColArr:
        i -= 1
        if 'default' in request.GET and request.GET['default'] ==  searchString['column'] :
            where_text += searchString['column'] + ' like "' + searchString['value'] + '" '
        elif searchString['operator'] == 1:
            where_text += searchString['column'] + ' =  "'+ searchString['value'] + '" '

        elif searchString['operator'] == 3: #for created and modified date
            dateTypeArr = ['YEAR','MONTH','DAY']
            dateArr =list(filter(None, searchString['value'].split('-')))
            j=1
            for d in dateArr:
                   if j == len(dateArr):
                       if dateTypeArr[j - 1] == 'DAY':
                           where_text += dateTypeArr[j - 1] + '(' + searchString['column'] + ') =  "' + d + '%" '
                       else:
                           where_text += dateTypeArr[j-1]+'('+searchString['column']+') like  "'+ d + '%" '
                   else:
                       where_text += dateTypeArr[j - 1] + '(' + searchString['column'] + ') like  "' + d + '%" and '
                   j += 1
            print(where_text)
        else:
            where_text += searchString['column'] + ' like "%' + searchString['value'] + '%" '
        if i != 0:
            where_text += ' and '

    sqlCount = 'SELECT count(cluster.ClusterId) FROM cluster JOIN ( '+tblClusterCnt+') AS cluster_cnt ON cluster.ClusterID = cluster_cnt.ClusterId  LEFT JOIN chsum_sigtype on cluster.Type = chsum_sigtype.SIG_TYPE  '

    if len(Perm_Type_Arr):
        DataCountTotal = lib.db_query(sqlCount+" where cluster.Status = 1 and cluster.Type in "+str(Perm_Type_Arr),1)
    else:
        DataCountTotal = lib.db_query(sqlCount+" where cluster.Status = 1 ",1)


    if len(searchColArr):
        sqlFilCount = sqlCount+where_text
        DataCountFilTotal = lib.db_query(sqlFilCount,1)
    else:
        DataCountFilTotal = DataCountTotal

   # sql = 'SELECT cluster.ClusterId,cluster.ClusterName,cluster.CreatedBy,cluster.ClusterAssignedTo,cluster.CreatedDate,cluster.ModifiedDate,cluster.Source, STATUS,Priority,State,Progress,cluster_cnt.SigCnt,chsum_sigtype.SIG_TYPE_NAME FROM cluster Join ('+tblClusterCnt+' ) as cluster_cnt on cluster.ClusterID = cluster_cnt.ClusterId LEFT JOIN chsum_sigtype on cluster.Type = chsum_sigtype.SIG_TYPE '+where_text+' '+orderString+' limit '+start+','+length
    sql = 'SELECT cluster.ClusterId,cluster.ClusterName,cluster.CreatedBy,cluster.ClusterAssignedTo,cluster.CreatedDate,cluster.ModifiedDate,cluster.Source, STATUS,Priority,Progress,cluster_cnt.SigCnt,chsum_sigtype.SIG_TYPE_NAME FROM cluster Join ('+tblClusterCnt+' ) as cluster_cnt on cluster.ClusterID = cluster_cnt.ClusterId LEFT JOIN chsum_sigtype on cluster.Type = chsum_sigtype.SIG_TYPE '+where_text+' '+orderString+' limit '+start+','+length
    clusters = lib.db_query(sql)

    data = []
    for cluster in clusters:
        viewBtn = '<a href="/cluster/'+str(cluster[0])+'?action=view" class="label label-primary">View</a>'

        if str(cluster[6]) in constant_data.CLUSTER_SOURCE:
            source = constant_data.CLUSTER_SOURCE[str(cluster[6])]
        else:
            source = cluster[6]
        clusterSource = source
        ClusterSource= lib.trimString(str(clusterSource),9)

        # if cluster[9] not in constant_data.STATELIST:
        #     State = "<span class='state_span' >" + str(constant_data.STATELIST[2]) + "</span>"
        # else:
        #     State =  "<span class='state_span' >"+str(constant_data.STATELIST[cluster[9]]) + "</span>"

        SignatureCount = str(cluster[10])
        Progress =  "<span class='state_span' >"+str(cluster[9]) + "</span>"
        cluster_name = str(cluster[1])
        ClusterName = lib.trimString(str(cluster[1]), 8)
        data.append({'ClusterID':str(cluster[0]),'ClusterName':"<font role='button' alt="+str(cluster_name)+" title='"+str(cluster_name)+"'>"+ClusterName+"</font>" ,'CreatedBy':"<a href='/user/"+str(cluster[2])+"'>"+str(cluster[2])+"</a>",'ClusterAssignedTo':"<a href='/user/"+str(cluster[3])+"'>"+ str(cluster[3])+"</a>",'CreatedDate':"{:%Y-%m-%d}".format(cluster[4]),'ModifiedDate':"{:%Y-%m-%d}".format(cluster[5]),'Source': "<font role='button' alt='"+str(source)+"' title='"+str(source)+"'>"+str(ClusterSource)+"</font>",'Priority':"<center>"+str(cluster[8])+"</center>",'SignatureCount':str(SignatureCount),'Progress':str(Progress),'Type':cluster[11],'View':viewBtn })
    recordsTotal= 0
    recordsFiltered=0
    if DataCountTotal:
        recordsTotal = DataCountTotal[0]
    if DataCountFilTotal:
        recordsFiltered = DataCountFilTotal[0]
    resp = {"draw": draw, "recordsTotal": recordsTotal, "recordsFiltered": recordsFiltered, "data":data}

    return HttpResponse(json.dumps(resp), content_type='application/json')

@csrf_exempt
def fileUpload(request):
    # if 'type' in  request.GET:
    #     for key,val in request.GET.items():
    #         print('ke : ',key,"--- val :",val)
    # else:
    #     print('this is main request')
    uploaded_files = request.FILES.get('myfile')
    error_message = 0
    error_message += validation.fileExtension(request, str(uploaded_files),str(inspect.stack()[0][3]))
    if error_message != 0:
        resp = {'error_message':error_message}
        return HttpResponse(json.dumps(resp), content_type='application/json')
    sql = "insert into clusterfile(`FileName`,`AddedBy`) values('"+str(uploaded_files)+"','"+str(request.user)+"')"
    returnId = lib.db_insert(sql)
    lib.handle_uploaded_file(request,uploaded_files, str(returnId),str(inspect.stack()[0][3]))
    resp = {'success':True,"response":returnId,"name":str(uploaded_files)}
    return HttpResponse(json.dumps(resp), content_type='application/json')

@csrf_exempt
def iniFileUpload(request):

    returnId = request.POST['upload_id']

    # if 'type' in request.GET:
    #     for key, val in request.GET.items():
    #         print('ke : ', key, "--- val :", val)
    # else:
    #     print('this is main request')

    uploaded_files = request.FILES.get('myfile')

    error_message = 0
    error_message += validation.fileExtension(request, str(uploaded_files),str(inspect.stack()[0][3]))
    if error_message != 0:
        resp = {'error_message': error_message}
        return HttpResponse(json.dumps(resp), content_type='application/json')
    try:
        directory_path = settings.UPLOAD_FILE_PATH +'bulk_ini\\'+ str(returnId)

        if not os.path.exists(directory_path):
            os.makedirs(directory_path,mode=0o777)
            os.chmod(directory_path, 0o777)
        f = open(directory_path+'.ini','a')
        from socket import gethostname, gethostbyname
        print(gethostbyname(gethostname()))
        f.write('/r/n'+str(gethostbyname(gethostname())))
    except Exception as e:
        print(' creating directory: ',e)
    lib.handle_uploaded_file(request,uploaded_files, directory_path,str(inspect.stack()[0][3]))
    resp = {'success': True, "response": returnId, "name": str(uploaded_files)}

    return HttpResponse(json.dumps(resp), content_type='application/json')


def process_ini_file(request):
    try:
        directory_path = r'' + settings.UPLOAD_FILE_PATH + 'bulk_ini\\' + str(request.POST['folderID'])
        data,cnt = [],0
        sql = 'select ClusterID,Type from cluster where Status = 1 and ClusterID = '+str(request.POST['clusterId'])+' limit 1'
        ClusterData = lib.db_query(sql,1)
        ClusterType = ClusterData[1]

        try:
            rowResult = lib.runTool(ClusterType,directory_path, 'add',request.POST['clusterId'])
            lib.debugLog(rowResult,request.user)
        except Exception as e:
            print(e)
        result = "{" + rowResult['data'].strip()[:-1] + "}";
        resultSet = json.loads(result)

        sectionIds,fetchResult = [],[]
        resultValidateArr = lib.progressIniOutput(request,result)

        for set in resultSet:
            sectionIds.append(set)
            result = resultValidateArr[cnt]['response']
            type = resultValidateArr[cnt]['type']

            respClass = resultValidateArr[cnt]['class']

            for secId in sectionIds:
                sectionId = lib.trimString(str(secId), 50)
                MalwareIndex =  lib.trimString(str(resultSet[secId]['MalwareIndex']),50)
                response = str(resultSet[secId]['response'])
            cnt = cnt + 1
            fetchResult.append({'secId':sectionId,'MalwareIndex': str(MalwareIndex), 'type': str(type), 'result': str(result), 'response': str(response),'respClass':respClass})

        return HttpResponse(json.dumps(fetchResult), content_type='application/json')
    except Exception as e:
        print('Error in processing: ', e)
        return HttpResponse(json.dumps(e), content_type='application/json')

@login_required(login_url='/login/')
def cluster_file_delete(request,fid,cid):
    sql = 'select cluster.Type from cluster where cluster.ClusterID = '+str(cid)
    clusterType = lib.db_query(sql,1)

    permision_type = str(constant_data.CLUSTER_TYPE[clusterType[0]]).lower()

    if 'can_edit_' + str(permision_type) not in permissions.getUserGroupPermission(request):
        messages.error(request, 'Delete cluster file permission not available for ' + str(permision_type).upper() + ' cluster')
        return HttpResponseRedirect("/cluster/" + cid)

    sql = "update clusterfile set clusterfile.Status = 0 where clusterfile.ClusterFileID=" +fid+" and clusterfile.ClusterID =" + cid
    lib.db_query(sql)
    messages.info(request,"#" + str(fid) + " - cluster file " + "deleted successfully.")
    return HttpResponseRedirect("/cluster/" + cid)

@login_required(login_url='/login/')
def downloadClusterFile(request):
    if request.GET.get('file'):
        sql = 'select FileName from clusterfile where clusterfile.ClusterFileID = '+str(request.GET.get('file'))
        fileName = lib.db_query(sql,1)
        zip_file = settings.UPLOAD_FILE_PATH + 'cluster_files\\'+str(request.GET.get('file'))+'.zip'
        if(os.path.exists(zip_file)):
            with open(zip_file,'rb') as file:
                clusterFile = file.read()
            response = HttpResponse(clusterFile,content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="'+str(fileName[0])+'"'
            return response
        else:
            return HttpResponse('Cluster file not found',content_type='application/json')
    else:
        return HttpResponse('Invalid request',content_type='application/json')