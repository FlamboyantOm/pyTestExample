from django.shortcuts import *
from . import constant_data, lib,permissions
from collections import OrderedDict
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from portal.lib import database_connection_check
from . import userview

@database_connection_check
@login_required(login_url='/login/')
def index(request):
    if permissions.accessPermission(request, 'can_manage_signature') == 0 and permissions.accessPermission(request,'can_manage_cluster') == 0:
        messages.error(request, 'No access permission re-login with other user')
        return HttpResponseRedirect("/logout/")

    userId = request.user
    lib.setMetaInformation(request, ['home'], 'Welcome to ' + constant_data.WEBSITE_TITLE, OrderedDict([('Main Menu', '')]))

    where_txt = ''
    Perm_Type_Arr = permissions.checkclusterTypePermission(request)
    if len(Perm_Type_Arr):
        if len(Perm_Type_Arr) == 1:
            Perm_Type_Arr = "(" + str(Perm_Type_Arr[0]) + ")"
        else:
            Perm_Type_Arr = tuple(Perm_Type_Arr)
        where_txt = 'and cluster.Type in ' + str(Perm_Type_Arr)
    else:
        data = userview.userObj()
        setattr(data, 'userId', userId)
        setattr(data, 'cluster', 0)
        setattr(data, 'signature', 0)
        return render(request, "portal/index.html", {'data': data})

    sqlDataCluster = "Select count(ClusterID) from cluster where CreatedBy = '" + str(userId) + "' and status = '1' "+str(where_txt)
    dataCluster = lib.db_query(sqlDataCluster, 1)

    sqlDataAssign = "Select count(ClusterID) from cluster where ClusterAssignedTo = '" + str(userId) + "' and status = '1' "+str(where_txt)
    dataAssign = lib.db_query(sqlDataAssign, 1)


    data = userview.userObj()
    setattr(data, 'cluster', dataCluster[0])
    setattr(data, 'clusterAssign', dataAssign[0])
    setattr(data, 'userId', userId)

    setattr(data, 'clusterRecentActivities', lib.clusterRecentActivities(str(5), 'where UserName = "' + str(userId) + '"',data.userId))
    setattr(data, 'signatureRecentActivities', lib.signatureRecentActivities(str(5),' agerecord.AuthorName = "' + str(userId) + '"',data.userId))

    # state priority details
    statecreateUserDict = lib.cluster_state_priority(userId, Perm_Type_Arr, 'CreatedBy')
    #statecreateUserDict = lib.cluster_state_priority(userId, Perm_Type_Arr, 'ClusterAssignedTo')

    if statecreateUserDict:
        stateValues = statecreateUserDict
        hasStateVal = sum(dict(stateValues).values())
        setattr(data, 'hasStateVal', hasStateVal)
        setattr(data, 'statecreateUserDict', statecreateUserDict)
   # setattr(data, 'prioritycreateUserDict', prioritycreateUserDict)
    #setattr(data, 'priorityAssignUserDict', priorityAssignUserDict)
    return render(request, "portal/index.html", {'data': data})

def index_error(request):
    error = ''
    if request.method == 'GET' and 'type' in request.GET:
        type = request.GET['type']
        if type == '1':
            error = 'Not able to connect with Database. Kindly contact Administrator.'
        if type == '2':
            error = 'Access Denied'
    else:
        error = 'Something is wrong. Kindly contact Administrator.'
    lib.setMetaInformation(request,'Error in processing your request' ,'Error Page')
    return render(request, "portal/index_error.html", {"error": error})

def logout_user(request):
    lib.setMetaInformation(request,['login'], 'Logout',OrderedDict([('Logout', '/logout/')]))
    logout(request)
    return render(request, "portal/logout.html")

def login_user(request): # pragma : no cover
    lib.setMetaInformation(request,['login'], 'Login', OrderedDict([('Login', '/login/')]))
    username, password, state = '','',"Please login to access "+str(constant_data.WEBSITE_TITLE)
    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')
        if username == '' or password == '':
            messages.error(request, "<span class='glyphicon glyphicon-warning-sign'></span> Username/Password Cannot Be Blank.")
            return HttpResponseRedirect('/')
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                if request.POST['next']:
                    return HttpResponseRedirect(request.POST['next'])
                else:
                    return HttpResponseRedirect('/')
            else:
               messages.error(request,"<span class='glyphicon glyphicon-warning-sign'></span><b> Your Account Is not Active, Please Contact The Site Admin.</b>")
        else:
            messages.error(request,"<span class='glyphicon glyphicon-warning-sign'></span><b> Your Username and/or Password Were Incorrect.</b>")
            lib.setMetaInformation(request, 'Invalid Login',{})
    return render(request, "portal/auth.html", {'username': username})

