# from django.test import TestCase,Client
# user = 'pratima'
# password = 'admin@123'
#
# from django.contrib.auth.models import User
#
# class UrlVerification(TestCase):
#
#     def test_check_cluster_url(self):
#         c = Client()
#         login = c.login(username=user, password=password)
#         self.assertIs(login,True,'Unable to login')
#         request = c.post('/cluster/list/')
#         perm = User.objects.get(username=user).get_all_permissions()
#         print(perm)
#         self.assertIn('portal.can_manage_cluster',perm)
#         self.assertEqual(request.status_code, 200)
#
#
# from django.urls import resolve
# from .views import logout_user,login_user
# class UrlTest(TestCase):
#
#     def test_url(self):
#
#         print('in test_url')
#         found = resolve('/login/')
#         self.assertEqual(found.func, login_user)
#         self.assertEqual(found.func, logout_user)
# #
# # from selenium import webdriver
#
# class seleniumTest():
#     def test_driver(self):
#         driver = webdriver.Chrome
#         url =driver.current_url
#         browser = webdriver.Firefox()
#         browser.get('http://www.google.com')
#         print(browser.current_url)
#         print(url)


import urllib.parse
getVars = {'cluster': 'cluster','v2':12133,'var2': 1337}
url = ' http://10.10.10.206:8005/'

#print(url + urllib.parse.urlencode(getVars))



base_url = '10.10.10.206:8005/'
from posixpath import join as urljoin

def create_url(para='',action=''):
    para = '/'.join(para)
    print(urljoin(base_url, para,urllib.parse.urlencode(action)))
    url = urljoin(para,urllib.parse.urlencode(action))
    #print(url)


# create_url(['cluster', '11'], {'?action': 'view'})
# create_url(['cluster', '11'])
# create_url(['cluster','list'])
# create_url(['signature'],{'action': 'add','id':12})
# create_url(['signature'],{'action': 'add','id':12,'mid':1212})
#

def create_url_patterns(paralist='',para='',view='',name=''):
    paralist = '/'.join(paralist)
    newPara = ''
    for key,val in para.items():
        if type(val) == int:
            newPara += '(?P<'+str(key)+'>[0-9]+)/'
        if type(val) == str:
            newPara += '(?P<' + str(key) + '>[\w+ ?]+)/'
    #print(urljoin(paralist,newPara))
    return "url(r'^"+str(urljoin(paralist,newPara))+"$', "+str(view)+", name='"+str(name)+")"

from collections import OrderedDict
from django.shortcuts import *

def geturlPatterns(request):
    #print(request.META.get('HTTP_HOST'))
    urlpatterns = []
    url=create_url_patterns(['cluster_file_delete'],OrderedDict([('fid',12),('cid','1')]))
    urlpatterns.append(url)

    url=create_url_patterns(['signature','history'],OrderedDict([('type',12),('mid','1'),('rfk',12)]),'signature.malware_index_history','malware_index_history')
    urlpatterns.append(url)
    #print(urlpatterns)
    return HttpResponse(urlpatterns)



#temp----
from urllib.request import urlopen, Request
def tempurl(request):
    theurl = 'http://10.10.10.206:8005/filter_inx1/'
    req = Request(theurl)
    try:
        handle = urlopen(req)
        print('in')
    except IOError as e :
        if hasattr(e.headers, 'code'):
            if IOError.code != 401:
                print('We got another error')
                print(IOError.code)
            else:
                print(IOError)
        print(e.headers,e)
        print(e.headers['www-authenticate'])
    return HttpResponse(IOError)

from django.contrib.auth.models import Group,Permission,User
from django.contrib.contenttypes.models import ContentType
content_type = ContentType.objects.get(app_label='portal',model='ApexUser')
print(content_type)