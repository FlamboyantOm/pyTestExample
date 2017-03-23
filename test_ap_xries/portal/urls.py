from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from . import views,cluster,userview,signature,lib,tag,filterinx,statistics


handler400 = 'build.views.bad_request'
handler403 = 'build.views.permission_denied'
handler404 = 'build.views.error404'
handler500 = 'build.views.server_error'
app_name = 'portal'

urlpatterns = [

    url(r'^$', views.index, name='index'),
    url(r'^login/$', views.login_user, name='login_user'),
    url(r'^logout/$', views.logout_user, name='logout_user'),
    url(r'^user/(?P<userId>[\w+ ?]+)/$', userview.user_details, name='user_details'),
   # url(r'^users/$', userview.users, name='users'),
    url(r'^error/$', views.index_error, name='index_error'),

    url(r'^cluster/$', cluster.cluster, name='cluster'),
    url(r'^cluster/(?P<cid>[0-9]+)/$', cluster.cluster_view, name='cluster_view'),
    url(r'^cluster/list/$', cluster.cluster_list, name='cluster_list'),
    url(r'^cluster/file/$', cluster.fileUpload, name='fileUpload'),

    url(r'^ini/file/$', cluster.iniFileUpload, name='fileUpload'),

    url(r'^cluster/list/ajax/$', cluster.cluster_list_ajax, name='cluster_list_ajax'),
    url(r'^cluster_delete/(?P<cid>[0-9]+)/$', cluster.cluster_delete, name='cluster_delete'),
    url(r'^process-ini-file/$', cluster.process_ini_file, name='process_ini_file'),
    url(r'^cluster_file_delete/(?P<fid>[0-9]+)/(?P<cid>[0-9]+)/$', cluster.cluster_file_delete,name='cluster_file_delete'),
    url(r'^cluster/log/(?P<logclusterId>[0-9]+)/$', lib.getClusterUpdatedDetais, name='logcluster_view'),
    url(r'^downloadClusterFile/$', cluster.downloadClusterFile, name='downloadClusterFile'),

    url(r'^user/cluster/list/ajax/$', lib.user_cluster_list_ajax, name='user_cluster_list_ajax'),

    url(r'^signature/$', signature.signature, name='signature'),
    url(r'^signature/test$', signature.test, name='test'),
    url(r'^signature/(?P<sid>[0-9]+)/$', signature.signature_view, name='signature_view'),
    url(r'^signature/history/(?P<type>[0-9]+)/(?P<mid>[0-9]+)/(?P<rfk>[0-9]+)$', signature.malware_index_history, name='malware_index_history'),
    url(r'^signature/list/$', signature.signature_list, name='signature_list'),
    url(r'^signature/list/ajax/$', signature.signature_list_ajax, name='signature_list_ajax'),
    url(r'^signature_delete/(?P<recordId>[0-9]+)/$', signature.signature_delete, name='signature_delete'),
    url(r'^downloadIniFile/$', signature.downloadIniFile, name='downloadIniFile'),

    url(r'^tag/list/$', tag.tag_list, name='tag_list'),
    url(r'^tag/(?P<tag>[A-Za-z0-9_]+)/$', tag.tag_view, name='tag_view'),
    url(r'^tag/list/ajax/$', tag.tag_list_ajax, name='tag_list_ajax'),

    url(r'^filter_inx/$', filterinx.filter_inx, name='filter_inx'),
    url(r'^filter_inx/list/ajax/$', filterinx.filter_list_ajax, name='filter_list_ajax'),
    url(r'^filter_inx/signature/list/ajax/$', filterinx.filter_signature_list_ajax, name='filter_signature_list_ajax'),
    url(r'^filter_result/ajax/$', filterinx.filter_result_ajax, name='filter_result_ajax'),
    url(r'^downloadFilterIniFile/$', filterinx.downloadFilterIniFile, name='downloadFilterIniFile'),

    url(r'^statistics/$', statistics.statistics, name='statistics'),
    url(r'^statistics/(?P<id>[0-9]+)/$', statistics.statistic_type, name='statistic_type'),

 ]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



