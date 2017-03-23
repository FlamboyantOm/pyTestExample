from . import constant_data
from django.contrib.auth.models import Permission,Group


def accessPermission(request,permission):
    userGroupArr = checkUserGroup(request)
    if 'Manager' in userGroupArr:
        return 1
    elif permission in getUserGroupPermission(request):
         return 1
    return 0

def checkUserGroup(request,user=''): #get user group list
    groupArr=[]
    if user:
        groupArr = [(x.name,x.id) for x in Group.objects.filter(user=user)]
    else:
        groupArr = [(x.name,x.id) for x in Group.objects.filter(user=request.user)]
    if groupArr:
        return dict(groupArr)
    return groupArr


def checkclusterTypePermission(request,user=''):
    Perm_Type_Arr = []
    allPerm = getUserGroupPermission(request,user)

    for perm in constant_data.TYPE_PERMISSION.keys():
        if perm in allPerm:
            Perm_Type_Arr.append(constant_data.TYPE_PERMISSION[perm])

    return Perm_Type_Arr;

def checkStatePermission(request):
    allPerm = getUserGroupPermission(request)
    if  'manager_state' in allPerm:
        stateArr = constant_data.SIG_STATE_PERMISSION[constant_data.SIG_STATE_GROUP['manager_state']]
        return stateArr
    elif 'signature_manager_state' in allPerm:
        stateArr = constant_data.SIG_STATE_PERMISSION[constant_data.SIG_STATE_GROUP['signature_manager_state']]
        return stateArr
    elif 'cluster_manager_state' in allPerm:
        stateArr = constant_data.SIG_STATE_PERMISSION[constant_data.SIG_STATE_GROUP['cluster_manager_state']]
        return stateArr
    else:
        return 0


def getUserGroupPermission(request,user=''):

    allPerm,groupPerm,userPerm = [],[],[]
    userGroupArr = checkUserGroup(request,user)
    userPerm = getuserAllPermission(request,user)

    if userGroupArr:
        groupPerm = getgroupAllPermission(userGroupArr.values())
    allPerm = list(set(userPerm+groupPerm))

    return allPerm

def getuserAllPermission(request,user=''):
    perm_tuple = [];
    if user:
        #perm_tuple = [(x.name) for x in Permission.objects.filter(user=user)]
        userPerm = Permission.objects.filter(user=user)
    elif request:
        #perm_tuple = [(x.name) for x in Permission.objects.filter(user=request.user)]
        userPerm = Permission.objects.filter(user=request.user)
    else:
        pass
    for perm in userPerm:
        perm_tuple.append(perm.codename)

    return perm_tuple

def getgroupAllPermission(userGroupArr):
    groupPerm = []
    groupAllPerm =[]
    for id in userGroupArr:
      #group_perm += [(x.name) for x in Permission.objects.filter(group=id)]
      groupPerm += Permission.objects.filter(group=id)
    for perm in groupPerm:
        groupAllPerm.append(perm.codename)
    return groupAllPerm


def checkUserPermission(request,permission,msg=''):
    if not request.user.has_perm(permission):
        return 0;
    return 1;

