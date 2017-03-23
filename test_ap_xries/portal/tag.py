import json
from django.shortcuts import *
from . import lib,permissions
from .userview import userObj
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from collections import OrderedDict


@login_required(login_url='/login/')
def tag_list(request):
    lib.setMetaInformation(request,[('Tag'),('tag_list')],'Tag List',OrderedDict( [('Tag List','')]))
    data = ''
    return render(request, 'portal/tag-list.html',{'data':data})


def tag_list_ajax(request):
    start = request.GET['start']
    length = request.GET['length']
    draw = request.GET['draw']
    actualColumns = ['record_tag.TagName','COUNT(tag_list.TagID)']


    Perm_Type_Arr = permissions.checkclusterTypePermission(request)
    if Perm_Type_Arr:
        if len(Perm_Type_Arr) == 1:
            Perm_Type_Arr = "(" + str(Perm_Type_Arr[0]) + ")"
        else:
            Perm_Type_Arr = tuple(Perm_Type_Arr)
    else:
        resp = {"draw": draw, "recordsTotal": 0, "recordsFiltered": 0, "data": ''}
        return HttpResponse(json.dumps(resp), content_type='application/json')

    sql = 'select count(DISTINCT(record_tag.TagID))  from tag_list join qh_sig_status on tag_list.SigID = qh_sig_status.SIG_ID_FK AND qh_sig_status.MARK_DELETED=0 join sig_master on tag_list.SigID = sig_master.SIG_ID join chsum_sigtype on sig_master.SIG_TYPE_FK = chsum_sigtype.SIG_TYPE join record_tag on tag_list.TagID = record_tag.TagID where sig_master.SIG_TYPE_FK in '+str(Perm_Type_Arr)
    signatureRecordAge = lib.db_query(sql,1)

    searchColArr,i,orderString,where_text =[],0,'',''
    cnt = 0
    for col in actualColumns:
        if request.GET['columns['+str(cnt)+'][search][value]'] :
            searchColArr.append({'column':col,'value':request.GET['columns['+str(cnt)+'][search][value]']})
        if 'order[0][column]' in  request.GET :
            if str(request.GET['order[0][column]']) == str(cnt):
                orderString = ' order by '+str(col)+' '+str(request.GET['order[0][dir]'])
        cnt = cnt + 1
    i = len(searchColArr)

    having_cnt = ''

    for searchString in  searchColArr:
        i -= 1
        if searchString['column'] == 'COUNT(tag_list.TagID)':
            having_cnt = "having "+searchString['column'] + ' = ' + searchString['value']

        else :
            where_text += searchString['column'] + ' like "%' + searchString['value'] + '%" and '

    if where_text != '':
        where_text = ' where '+where_text[:-4]


    if len(where_text) and len(Perm_Type_Arr):
        where_text += ' and sig_master.SIG_TYPE_FK in '+str(Perm_Type_Arr)
    else:
        where_text = 'where sig_master.SIG_TYPE_FK in '+str(Perm_Type_Arr)

    sql = 'select tag_list.TagID,record_tag.TagName,COUNT(tag_list.TagID) tagcnt from tag_list join qh_sig_status on tag_list.SigID = qh_sig_status.SIG_ID_FK AND qh_sig_status.MARK_DELETED=0 join sig_master on tag_list.SigID = sig_master.SIG_ID join chsum_sigtype on sig_master.SIG_TYPE_FK = chsum_sigtype.SIG_TYPE join record_tag on tag_list.TagID = record_tag.TagID   '+str(where_text)+'  GROUP BY record_tag.TagID '+having_cnt+' '+orderString+' limit '+start+','+length
    recordList = lib.db_query(sql)

    DataCountFilTotal = 0
    recordsTotal = 0
    sql = 'select tag_list.TagID,COUNT(tag_list.TagID) tagcnt from tag_list join qh_sig_status on tag_list.SigID = qh_sig_status.SIG_ID_FK AND qh_sig_status.MARK_DELETED=0 join sig_master on tag_list.SigID = sig_master.SIG_ID join chsum_sigtype on sig_master.SIG_TYPE_FK = chsum_sigtype.SIG_TYPE join record_tag on tag_list.TagID = record_tag.TagID   '+str(where_text)+'  GROUP BY record_tag.TagID '+having_cnt+' '+orderString
    recordListFull = lib.db_query(sql)

    if recordListFull:
        DataCountFilTotal = len(recordListFull)


    data = []
    if recordList:
        for record in recordList:
                viewBtn = '<a href="/tag/'+str(record[1])+'" class="label label-primary">View</a>'
                data.append({"Tag":str(record[1]), "TagCount":str(record[2]),"View":viewBtn})

    if signatureRecordAge:
        recordsTotal = signatureRecordAge[0]
    recordsFiltered = DataCountFilTotal
    resp = {"draw": draw, "recordsTotal": recordsTotal, "recordsFiltered": recordsFiltered, "data":data}
    return HttpResponse(json.dumps(resp), content_type='application/json')


@login_required(login_url='/login/')
def tag_view(request,tag):

    Perm_Type_Arr = permissions.checkclusterTypePermission(request)
    if len(Perm_Type_Arr):
        if len(Perm_Type_Arr) == 1:
            Perm_Type_Arr = "(" + str(Perm_Type_Arr[0]) + ")"
        else:
            Perm_Type_Arr = tuple(Perm_Type_Arr)

    sql = 'select TagID,TagName,DateAdded from record_tag where record_tag.TagName = "'+str(tag)+'"'

    tagData = lib.db_query(sql,1)

    if tagData is None:
        messages.info(request, "Invalid Tag !!")
        return HttpResponseRedirect(reverse('portal:tag_list'))

    sql = 'SELECT chsum_sigtype.SIG_TYPE_NAME,count(tag_list.SigID) cnt FROM record_tag  JOIN tag_list ON record_tag.TagID = tag_list.TagID AND record_tag.TagName = "'+str(tag)+'" JOIN qh_sig_status ON tag_list.SigID = qh_sig_status.SIG_ID_FK AND qh_sig_status.MARK_DELETED=0 JOIN sig_master ON tag_list.SigID = sig_master.SIG_ID JOIN chsum_sigtype ON sig_master.SIG_TYPE_FK = chsum_sigtype.SIG_TYPE  group by chsum_sigtype.SIG_TYPE_NAME order by cnt desc'

    if len(Perm_Type_Arr):
        sql = 'SELECT chsum_sigtype.SIG_TYPE_NAME,count(tag_list.SigID) cnt FROM record_tag  JOIN tag_list ON record_tag.TagID = tag_list.TagID AND record_tag.TagName = "' + str(tag) + '" JOIN qh_sig_status ON tag_list.SigID = qh_sig_status.SIG_ID_FK AND qh_sig_status.MARK_DELETED=0 JOIN sig_master ON tag_list.SigID = sig_master.SIG_ID JOIN chsum_sigtype ON sig_master.SIG_TYPE_FK = chsum_sigtype.SIG_TYPE  where sig_master.SIG_TYPE_FK in ' + str(Perm_Type_Arr) +'group by chsum_sigtype.SIG_TYPE_NAME order by cnt desc'

    tagRecData = lib.db_query(sql)

    if tagRecData is None:
        messages.info(request, "No Records found !!")
        return HttpResponseRedirect(reverse('portal:tag_list'))
    #sql = ' select type,count(sigid) as  cnt from taglist where tid = "'+str(tagData[0])+'" and status = 1 group by type order by cnt desc'

    #typeData = list(zip(list(map(lambda x:constant_data.TYPE[int(x[0])],tagRecData)),list( map(lambda x:x[1],tagRecData))))
    typeData = {}
    lib.setMetaInformation(request,[('Tag'),('tag_')],str(tag).title(),OrderedDict( [("Tag List",'/tag/list/'),("Tag : "+str(tag),'')]))
  #  data =  {'name':str(tag),'addedon':str(tagData[2]),'id':tagData[0],'TypeCount':tagRecData}

    data = userObj()
    setattr(data, 'name', str(tag))
    setattr(data, 'addedon', str(tagData[2]))
    setattr(data, 'id', tagData[0])
    setattr(data, 'TypeCount', tagRecData)
    return render(request, 'portal/tag-view.html',{'data':data})

