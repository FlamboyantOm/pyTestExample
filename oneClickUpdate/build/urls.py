from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from . import views, pipeline_view, e2_view,qh_view,statistics,apiview

handler400 = 'build.views.bad_request'
handler403 = 'build.views.permission_denied'
handler404 = 'build.views.error404'
handler500 = 'build.views.server_error'
app_name = 'build'
 
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^error/$', views.index_error, name='index_error'),
    url(r'^login/$', views.login_user, name='login_user'),
    url(r'^logout/$', views.logout_user, name='logout_user'),
    url(r'^e2/$', e2_view.e2_index, name='e2_index'),
    url(r'^e2-ajax/$', e2_view.e2_ajax, name='e2_ajax'),
    url(r'^history/(?P<type>[\w+ ?]+)/$', pipeline_view.build_history, name='build_history'),
    url(r'^history/ajax/(?P<type>[\w+ ?]+)/$', pipeline_view.build_history_ajax, name='build_history_ajax'),
    url(r'^build/(?P<pid>[\w\-]+)/$', pipeline_view.build_id_details, name='build_id_details'),
    url(r'^build-solo-details/ajax/$', pipeline_view.build_solo_detail_ajax, name='build_solo_detail_ajax'),
    url(r'^build-diff-details/ajax/$', pipeline_view.build_diff_detail_ajax, name='build_diff_detail_ajax'),
    url(r'^patch-file-details/$', pipeline_view.patch_file_details_ajax, name='patch_file_details_ajax'), #patch file in detail
    url(r'^build-engine/(?P<type>[\w+ ?]+)/$', pipeline_view.build_engine_mgt, name='build_engine_mgt'),
    url(r'^build-engine/ajax/(?P<type>[\w+ ?]+)/(?P<key>[0-9]+)/(?P<action>[0-9]+)/$', pipeline_view.build_engine_mgt_ajax, name='build_engine_mgt_ajax'),
    url(r'^create-job/(?P<type>[\w+ ?]+)/(?P<step>[0-9]+)/$', pipeline_view.create_job, name='create_job'),
    url(r'^fail-job/(?P<type>[\w+ ?]+)/$', pipeline_view.fail_job, name='fail_job'),
    url(r'^qh/$', qh_view.qh_index, name='qh_index'),
    url(r'^qh-ajax/$', qh_view.qh_ajax, name='qh_ajax'),
    url(r'^qh/history$',  views.qh_temp, name='qh_temp'),
    url(r'^revert/(?P<type>[\w+ ?]+)/list/$', pipeline_view.build_revert_list, name='build_revert_list'),
    url(r'^revert/(?P<type>[\w+ ?]+)/$', pipeline_view.build_revert, name='build_revert'),
    url(r'^revert-list-ajax/(?P<type>[\w+ ?]+)/$', pipeline_view.revert_list_ajax, name='revert_list_ajax'),
    url(r'^current-status-ajax/$', pipeline_view.check_current_status_ajax, name='check_current_status_ajax'),
    url(r'^previous-builds/(?P<type>[\w+ ?]+)/(?P<build_type>[\w+ ?]+)/$', pipeline_view.previous_builds, name='previous_builds'),
    url(r'^revert/ajax/(?P<type>[\w+ ?]+)/$', pipeline_view.revert_ajax, name='revert_ajax'),
    url(r'^verify-job-ajax/(?P<engine>[\w+ ?]+)/(?P<flag>[\w+ ?]+)/$', pipeline_view.verify_job_jenkins, name='verify_job_jenkins'),
    url(r'^current_job_details/$', pipeline_view.current_job_details_ajax,name='current_job_details_ajax'),
    url(r'^jenkins-log/(?P<job>[\w+ ?]+)/$$', pipeline_view.jenkins_log,name='jenkins_log'),
    url(r'^TableToCsv/$', pipeline_view.getTableToCsv, name='build_id_details'),
    #statistics
    url(r'^statistics/(?P<type>[\w+ ?]+)/$', statistics.statistics, name='statistics'),
    url(r'^api/mark-verify/$', apiview.mark_verify, name='mark_verify'),
    url(r'^api/mark-release/$', apiview.mark_release, name='mark_release'),
    url(r'^api/mark-buildengine/$', apiview.mark_buildengine, name='mark_buildengine'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler400 = 'build.views.bad_request'
handler403 = 'build.views.permission_denied'
handler404 = 'build.views.page_not_found'
handler500 = 'build.views.server_error'

