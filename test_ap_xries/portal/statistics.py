from django.shortcuts import *
from django.contrib.auth.decorators import  login_required
from . import lib,constant_data
from collections import OrderedDict
import json



@login_required(login_url='/login/')
def statistics(request):
    lib.setMetaInformation(request,[('Tag'),('tag_list')],'Statistics',OrderedDict( [('Statistics','')]))
    data = []
    return render(request, 'portal/statistics.html',{'data':data})

@login_required(login_url='/login/')
def statistic_type(request,id):
    data = {}
    data.update({"main_types":constant_data.CLUSTER_TYPE})
    sql = "select cluster.`Type`,COUNT(agerecord.Record_ID_FK) from agerecord join qh_sig_status on agerecord.Record_ID_FK = qh_sig_status.SIG_ID_FK and qh_sig_status.MARK_DELETED = 0 join cluster on agerecord.ClusterId = cluster.ClusterID  and cluster.`Status` = 1 group by cluster.`Type`"
    TypeCount = lib.db_query(sql)
    sql = "SELECT  IF(agerecord.AuthorName IS NULL or agerecord.AuthorName = '', 'OLD_RECORDS', agerecord.AuthorName), count(agerecord.Record_ID_FK) FROM agerecord JOIN qh_sig_status ON agerecord.Record_ID_FK = qh_sig_status.SIG_ID_FK AND qh_sig_status.MARK_DELETED = 0 JOIN cluster ON agerecord.ClusterId = cluster.ClusterID AND cluster.`Status` = 1 group by agerecord.AuthorName "
    UserCount = lib.db_query(sql)
    data.update({"main_types":constant_data.CLUSTER_TYPE,"TypeCount":dict(TypeCount),"UserCount":dict(UserCount)})
    if int(id) in constant_data.CLUSTER_TYPE:
        data.update({"main_types":constant_data.CLUSTER_TYPE})
    return HttpResponse(json.dumps(data), content_type='application/json')

