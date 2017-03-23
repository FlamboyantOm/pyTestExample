#-------------------------------------------------------------------------------
# Name:        rest_api.py
# Purpose:     RESTful API to iniatiate, verify and release jobs
# Note :
#		1). Constant.py must have web sergver deetails
#	Dependencies : requests,json,constant.py
# Author:      Kamesh Jungi
# Created:     21-09-2015
# Copyright:   (c) "Quick Heal Technologies Ltd." 2016
# Licence:     "Quick Heal Technologies Ltd."
#-------------------------------------------------------------------------------

import constant
import requests,json

#*****************************************************************
#Function to Mark Verify
#Arguments :
#   JobID : JobId which need to be verified/failed
#   EngineType : 1 (QH) OR 2 (E2)
#   IsVerifed : 1 (Mark Verify) or 0 (Mark Fail)
#   Note (optional) : Note incase marking fail
#Return (dictionary type with following attribute) :
#   Status : RESTful API able connect and run successfully (1 for successfully worked, 0 for failed)
#   response_code : Response code from Web Server (Refere RESPONSE_CODE from constant.py for further details)

#*****************************************************************
def mark_verify(JobID,EngineType,IsVerifed,Note):
    data = '{"JobID":"'+str(JobID)+'","EngineType":"'+str(EngineType)+'","IsVerifed":'+str(IsVerifed)+',"Note":"'+str(Note)+'"}'
    url = 'http://'+str(constant.WEB_USER)+':'+str(constant.WEB_PASS)+'@'+str(constant.WEB_URL)+'/build/api/mark-verify/'
    headers = {'Content-Type': 'application/json'}
    response = requests.post( url,data = data,headers=headers)
    if(constant.DEBUG_PRINT == 1):
        print("code:"+ str(response.status_code))
        print("******************")
        print("headers:"+ str(response.headers))
        print("******************")
        print("content:"+ str(response.text))

    if (int(response.status_code) == 200):
        result = json.loads(response.text)
        return {'status':1,'response_code':result['status']}
    else :
         return {'status':0,'response_code':0}

#*****************************************************************
#Function to Mark Release
#Arguments :
#   JobID : JobId which need to be verified/failed
#   EngineType : 1 (QH) OR 2 (E2)
#   IsReleased : 1 (Mark Release) or 0 (Mark Fail)
#   VDB : VDB value in YYYY-MM-DD HH:MM:SS formate Eg. 2012-09-08 17:53:00
#   Note (optional) : Note incase marking fail
#Return (dictionary type with following attribute) :
#   Status : RESTful API able connect and run successfully
#   response_code : Response code from Web Server (Refere RESPONSE_CODE from constant.py for further details)
#*****************************************************************
def mark_release(JobID,EngineType,IsReleased,Note):
    data = '{"JobID":"'+str(JobID)+'","EngineType":"'+str(EngineType)+'","IsReleased":'+str(IsReleased)+',"Note":"'+str(Note)+'"}'

    url = 'http://'+str(constant.WEB_USER)+':'+str(constant.WEB_PASS)+'@'+str(constant.WEB_URL)+'/build/api/mark-release/'
    print(url)
    headers = {'Content-Type': 'application/json'}
    response = requests.post( url,data = data,headers=headers)
    if constant.DEBUG_PRINT == 1:
        print ("code:"+ str(response.status_code))
        print("******************")
        print("headers:"+ str(response.headers))
        print("******************")
        print("content:"+ str(response.text))
    if (int(response.status_code) == 200):
        result = json.loads(response.text)
        return {'status':1,'response_code':result['status']}
    else :
         return {'status':0,'response_code':0}

#*****************************************************************
#Function to mark buildengine
#Arguments :
#   UpdateArray : Dictionary array with update id and job id e.g. {4:1,5:1} where 4 and 5 are update id and 1 is job id
#   isMark : 1 (Mark build engine) or 0 (Unmark build engine )
#   Note (optional) : Note if any thing needed to add
#Return (dictionary type with following attribute) :
#   Status : RESTful API able connect and run successfully
#   response_code : Response code from Web Server (Refere RESPONSE_CODE from constant.py for further details)
#*****************************************************************
def mark_buildengine(UpdateArray,isMark,Note=''):
    data = '{"UpdateArray":"'+str(UpdateArray)+'","isMark":'+str(isMark)+',"Note":"'+str(Note)+'"}'
    url = 'http://'+str(constant.WEB_USER)+':'+str(constant.WEB_PASS)+'@'+str(constant.WEB_URL)+'/build/api/mark-buildengine/'
    headers = {'Content-Type': 'application/json'}
    response = requests.post( url,data = data,headers=headers)
    if constant.DEBUG_PRINT == 1 :
        print ("code:"+ str(response.status_code))
        print("******************")
        print("headers:"+ str(response.headers))
        print("******************")
        print("content:"+ str(response.text))
    if (int(response.status_code) == 200):
        result = json.loads(response.text)
        return {'status':1,'response_code':result['status']}
    else :
         return {'status':0,'response_code':0}
UpdateArray = {4:139}
mark_buildengine(UpdateArray,1,'kamesh test')
#retValue = mark_verify(26,2,1,"This is test by manoj")
#print('Return :',retValue['status'],retValue['response_code'])
#print(mark_verify(148,2,1,"This is test by manoj"))
#print(mark_release(188,2,1,"This manoj test"))


