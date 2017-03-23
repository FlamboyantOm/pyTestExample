
import constant

def mark_buildengine(JobID,EngineType,isMark,buidEngineArr,VDB,Note):
    data = '{"JobID":"'+str(JobID)+'","EngineType":"'+str(EngineType)+'","isMark":'+str(isMark)+'","buidEngineArr":'+str(buidEngineArr)+'}'
    url = 'http://' + str(constant.WEB_USER) + ':' + str(constant.WEB_PASS) + '@' + str(constant.WEB_URL) + '/build/api/mark-buildengine/'
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=data, headers=headers)
    if constant.DEBUG_PRINT == 1:
        print("code:" + str(response.status_code))
        print("******************")
        print("headers:" + str(response.headers))
        print("******************")
        print("content:" + str(response.text))
    if (int(response.status_code) == 200):
        result = json.loads(response.text)
        return {'status': 1, 'response_code': result['status']}
    else:
        return {'status': 0, 'response_code': 0}



JobID = 15
EngineType = 1
isMark = 1
buidEngineArr = {778:10,779:8,880:9,881:7}
VDB = '2012-09-08 17:53:00'
Note = 'test Note'


print(mark_buildengine(JobID,EngineType,isMark,buidEngineArr,VDB,Note))

























status = 0
packagelistname = ['pkg_140916181040833_224_5093.zip', 'pkg_140916182023284_225_5093.zip', 'pkg_160916131649505_230_5096.zip','pkg_160916154525749_238_5111.zip', 'pkg_160922114650047_287_5359.zip']
packagelist = ['http://10.10.3.152:8080/Bin_Server//temp/ENGINE_CONFIG_BUILD/engine/trunk/pkg_140916181040833_224_5093.zip','http://10.10.3.152:8080/Bin_Server//temp/ENGINE_CONFIG_BUILD/engine/trunk/pkg_140916182023284_225_5093.zip','http://10.10.3.152:8080/Bin_Server//temp/ENGINE_CONFIG_BUILD/engine/trunk/pkg_160916131649505_230_5096.zip','http://10.10.3.152:8080/Bin_Server//temp/ENGINE_CONFIG_BUILD/engine/trunk/pkg_160916154525749_238_5111.zip','http://10.10.3.152:8080/Bin_Server//branch2015/engine/pkg_160922114650047_287_5359.zip'], ['http://10.10.3.152:8080/Bin_Server//temp/ENGINE_CONFIG_BUILD/engine/trunk/pkg_140916181040833_224_5093.zip','http://10.10.3.152:8080/Bin_Server//temp/ENGINE_CONFIG_BUILD/engine/trunk/pkg_140916182023284_225_5093.zip','http://10.10.3.152:8080/Bin_Server//temp/ENGINE_CONFIG_BUILD/engine/trunk/pkg_160916131649505_230_5096.zip','http://10.10.3.152:8080/Bin_Server//temp/ENGINE_CONFIG_BUILD/engine/trunk/pkg_160916154525749_238_5111.zip','http://10.10.3.152:8080/Bin_Server//branch2015/engine/pkg_160922114650047_287_5359.zip']
html = ''
if status is not None:
    if status== 1:
        html += '<div class="alert alert-danger"> Error in release package file. </div>'
        print(html)
    if status == 2:
        html += '<div class="alert alert-warning"> No release package found. </div>'
    html += '<table class=lastStepTbl><tr><td><h4>Select Package :</h4></td><td>'
    eachPckLimit = 512
    cnt = 0
    for packege_item in packagelist[0]:
       # print('Name: ---',packagelistname[cnt],' |||||   Link: ---',packege_item)
        if len(packege_item) < eachPckLimit:
            html += '<label><input class="packageListCheck"   type="checkbox"  value="'+str(packege_item)+'" checked> &nbsp;'+str(packagelistname[cnt])+'</label>'
            cnt = cnt + 1
        else:
            html += '<label class="alert alert-warning"> &nbsp;' + str(packagelistname[cnt]) + ' <br> is having more then ' + str(eachPckLimit) + ' characters</label>'
    html += '</td><tr/></table>'

