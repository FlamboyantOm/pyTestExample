from django.shortcuts import *
from django.template import RequestContext
from django.shortcuts import render_to_response, render
from django.contrib.auth import authenticate, login, logout
from . import flib, config
from collections import OrderedDict
from build.flib import database_connection_check

def logout_user(request):
    flib.setMetaInformation(request, 'Logout',OrderedDict([('Logout', '/logout/')]))
    logout(request)
    return render(request, "build/logout.html")

def login_user(request):
    flib.setMetaInformation(request, 'Login', OrderedDict([('Login', '/login/')]))
    username, password, state = '','',"Please login to access "+str(config.WEBSITE_TITLE)
    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                if request.POST['next']:
                    return HttpResponseRedirect(request.POST['next'])
                else:
                    return HttpResponseRedirect('/')
            else:
                state = "Your account is not active, please contact the site admin."
        else:
            state = "Your username and/or password were incorrect."
            flib.setMetaInformation(request, 'Invalid Login',{})
    return render(request, "build/auth.html", {'state': state, 'username': username})

@database_connection_check
def index(request):
    flib.setMetaInformation(request,'Welcome To ' + config.WEBSITE_TITLE,'')
    if request.user.is_authenticated():
        user_perm = flib.get_user_permissions(request.user)
        content = ''
        for group in user_perm:
            content +'<table class="shadow-in qh-menu-table">'
            content +'</div>'
        msg = ''
        return render(request, "build/main.html", { 'user_perm':user_perm,'msg':msg})
    else:
        flib.setMetaInformation(request, 'Login','')
        return render(request, "build/auth.html",{'state':"Please login to access"+ " "+str(config.WEBSITE_TITLE)})

def index_error(request):
    error = ''
    if request.method == 'GET' and 'type' in request.GET:
        type = request.GET['type']
        if type == '1':
            error = 'Not able to connect with Database. Kindly contact Administrator.'
        if type == '2':
            error = 'Not able to connect with Jenkins server. Kindly contact Administrator.'
    else:
        error = 'Something is wrong. Kindly contact Administrator.'
    flib.setMetaInformation(request,'Error in processing your request' ,OrderedDict([('Error','')]))
    return render(request, "build/index_error.html", {"error": error})

def bad_request(request):
    response = render_to_response('build/index_error.html',context_instance=RequestContext(request))
    response.status_code = 400
    return response

def qh_temp(request):
    msg = "Coming Soon..."
    return render(request, 'build/qhindex.html', {'msg': msg})