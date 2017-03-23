from django.shortcuts import *
from . import constant_data, lib,permissions
from collections import OrderedDict
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User,Group

@login_required(login_url='/login/')
def user_details(request,userId):
   # lib.setMetaInformation(request, ['user'], 'User :  ' + constant_data.WEBSITE_TITLE, OrderedDict([('User', '/users/'), (str(userId), '')]))
    lib.setMetaInformation(request, ['user'], 'User :  ' + constant_data.WEBSITE_TITLE, OrderedDict([(str(userId), '')]))

    where_txt = ''
    Perm_Type_Arr = permissions.checkclusterTypePermission(request)
    if len(Perm_Type_Arr):
        if len(Perm_Type_Arr) == 1:
            Perm_Type_Arr = "(" + str(Perm_Type_Arr[0]) + ")"
        else:
            Perm_Type_Arr = tuple(Perm_Type_Arr)
        where_txt = 'and cluster.Type in '+str(Perm_Type_Arr)
    else:
        data = userObj()
        setattr(data, 'userId', request.user)
        setattr(data, 'cluster', 0)
        setattr(data, 'signature',0)
        return render(request, "portal/user_details.html", {'data': data})

    sqlDataCluster = "Select count(ClusterID) from cluster where CreatedBy = '"+str(userId)+"' and status = '1 ' "+str(where_txt)
    dataCluster = lib.db_query(sqlDataCluster,1)

    sqlDataAssign = "Select count(ClusterID) from cluster where ClusterAssignedTo = '"+str(userId)+"' and status = '1 ' "+str(where_txt)

    dataAssign = lib.db_query(sqlDataAssign,1)

    data = userObj()
    setattr(data,'cluster', dataCluster[0])
    setattr(data,'clusterAssign', dataAssign[0])
    setattr(data,'userId', userId)

    # last_login = ''
    # if str(userId) in User.objects.all():
    #     last_login = User.objects.get(username=str(userId)).last_login
    #     if last_login == None:
    #         last_login = ''
    #     else:
    #         last_login = "{:%d/%m/%Y %H:%M:%S}".format(last_login)


    # state priority details
    statecreateUserDict = lib.cluster_state_priority(userId, Perm_Type_Arr, 'CreatedBy')
    #stateAssignUserDict = lib.cluster_state_priority(userId, Perm_Type_Arr,'ClusterAssignedTo')

    if statecreateUserDict:
        stateValues = statecreateUserDict
        hasStateVal = sum(dict(stateValues).values())
        setattr(data, 'hasStateVal', hasStateVal)
        setattr(data, 'statecreateUserDict', statecreateUserDict)

    #setattr(data, 'prioritycreateUserDict', prioritycreateUserDict)
   # setattr(data, 'priorityAssignUserDict', priorityAssignUserDict)


    return render(request, "portal/user_details.html",{'data':data})

@login_required(login_url='/login/')
def users(request):
    if 'view' in request.GET and request.GET['view'].replace('/', '') == 'cluster' :
        #lib.setMetaInformation(request,['users','users_cluster'], 'Users : Cluster Manager ',OrderedDict([('Users','/users/'),('Cluster Managers','')]))
        lib.setMetaInformation(request,['users','users_cluster'], 'Users : Cluster Manager ',OrderedDict([('Cluster Managers','')]))
        clusterManagerGroup = Group.objects.get(name='ClusterManager')
        clusterManagers = clusterManagerGroup.user_set.all()
        usr = {}
        for user in clusterManagers:
            usr[user] = {'name':user,'cluster':lib.is_memeber('ClusterManager',user),'signature':True}
        return render(request, "portal/users.html",{'type':'cluster','data':usr})

    elif 'view' in request.GET and request.GET['view'].replace('/', '') == 'signature' :
        #lib.setMetaInformation(request,['users','users_signature'], 'Users : Signature Manager ',OrderedDict([('Users','/users/'),('Signature Managers','')]))
        lib.setMetaInformation(request,['users','users_signature'], 'Users : Signature Manager ',OrderedDict([('Signature Managers','')]))
        SignatureManagerGroup = Group.objects.get(name='SignatureManager')
        SignatureManagers = SignatureManagerGroup.user_set.all()
        usr = {}
        for user in SignatureManagers:
            usr[user] = {'name':user,'cluster':True,'signature':lib.is_memeber('SignatureManager',user)}
        return render(request, "portal/users.html",{'type':'signature','data':usr})
    else:
        lib.setMetaInformation(request,['users','users_main'], 'Users - All ',OrderedDict([('Users (All)','')]))
        users = User.objects.all()
        usr = {}
        for user in users:
            usr[user] = {'name':user,'cluster':lib.is_memeber('ClusterManager',user),'signature':lib.is_memeber('SignatureManager',user)}
        return render(request, "portal/users.html",{'data':usr})

class userObj(object):
    name = ''
    cluster = ''
    signature = ''


