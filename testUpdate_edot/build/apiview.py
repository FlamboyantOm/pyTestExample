from django.http import HttpResponse
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.decorators import  permission_classes,api_view,authentication_classes
from rest_framework.permissions import IsAuthenticated,IsAdminUser,AllowAny
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.response import Response
from . import config,flib
from build.pipeline_view import create_job,failJobProcess
import json

@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def mark_verify(request):
    if int(request.data['EngineType']) not in config.EngineType:
        return Response({'status':0,'response':'Invalid EngineType'})
    if int(request.data['IsVerifed']) not in [0,1]:
        return Response({'status':0,'response':'Invalid IsVerifed'})
    sql = 'select jobinfo.JobID from jobinfo left join  jobstatedetails on jobinfo.JobID = jobstatedetails.JobID where EngineType = "'+str(request.data['EngineType'])+'" and jobinfo.JobState = 3 and jobstatedetails.JobState = 3 and jobstatedetails.PercentDone = 100 order by jobinfo.JobID desc limit 1'
    LatestJobId = flib.db_query(sql,1)
    if LatestJobId == None:
        return Response({'status':0,'response':'No JobID available.'})
    if not request.data['JobID'] or  str(LatestJobId[0]) != str(request.data['JobID']):
        return Response({'status':0,'response':'Invalid JobID'})
    if not request.data['IsVerifed'] or 1 != int(request.data['IsVerifed']):
        failJobProcess(request,int(request.data['EngineType']),str(request.data['Note']),str(request.user))
        return Response({'status':3,'response':'Mark Failed'})
    else:
        create_job(request,str(config.EngineType[int(request.data['EngineType'])]).lower(),2,1)
        return Response({'status':1,'response':'Mark Verified'})

@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def mark_release(request):
    if int(request.data['EngineType']) not in config.EngineType:
        return Response({'status':0,'response':'Invalid EngineType'})
    if int(request.data['IsReleased']) not in [0,1]:
        return Response({'status':0,'response':'Invalid IsReleased'})
    sql = 'select jobinfo.JobID from jobinfo left join  jobstatedetails on jobinfo.JobID = jobstatedetails.JobID where EngineType = "'+str(request.data['EngineType'])+'" and jobinfo.JobState = 5 and jobstatedetails.JobState = 5 and jobstatedetails.PercentDone = 100 order by jobinfo.JobID desc limit 1'
    LatestJobId = flib.db_query(sql,1)

    if LatestJobId == None:
        return Response({'status':0,'response':'No JobID available.'})
    if not request.data['JobID'] or  str(LatestJobId[0]) != str(request.data['JobID']):
        return Response({'status':0,'response':'Invalid JobID'})

    if not request.data['IsReleased'] or 1 != int(request.data['IsReleased']):
        failJobProcess(request,int(request.data['EngineType']),str(request.data['Note']),str(request.user))
        return Response({'status':3,'response':'Mark Failed'})
    else:
        data = create_job(request,str(config.EngineType[int(request.data['EngineType'])]).lower(),3, {'Note':request.data['Note']})
        resData = json.loads(data._container[0].decode("utf-8"))
        return Response({'status':str(resData['status']),'response':str(resData['msg'])})

@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def mark_buildengine(request):
    if int(request.data['isMark']) not in [0,1]:
        return Response({'status':0,'response':'Invalid IsMark'})
    UpdateArray  =eval(request.data['UpdateArray'])
    jobids = ""
    for jobid in UpdateArray.values():
        jobids += str(jobid)+","
    jobids = jobids[:-1]
    sql = 'SELECT jobinfo.JobID, releaseinfo.IsBuildEngine FROM jobinfo JOIN releaseinfo on releaseinfo.JobID = jobinfo.JobID WHERE  jobinfo.JobID in ('+str(jobids)+')   and jobinfo.JobState = 6  order by jobinfo.JobID desc limit 1'
    SelectedJob = flib.db_query(sql,1)
    if SelectedJob == None :
        return Response({'status':0,'response':'No Completed job found.'})
    else:
        status  = flib.markBuildEngine(request,UpdateArray,int(request.data['isMark']),request.data['Note'])
        if status == 1:
            return Response({'status':1,'response':'Successfully Marked build engine'})
        else :
            return Response({'status':2,'response':'Verificaton failed.'})