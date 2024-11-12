from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.models import User
from django.utils import timezone
import random, string, smtplib, base64, json, requests, os
from django.shortcuts import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from email.message import EmailMessage
from datetime import datetime, timedelta
from django.db.models import Q
from django.db.models.functions import ( ExtractDay, ExtractHour, ExtractMinute, ExtractMonth, ExtractSecond, ExtractWeek, ExtractWeekDay, ExtractYear )
from django.utils.html import format_html
from .models import UserProfile
from django.utils.encoding import smart_str
import environ

months = {
    '01':'Jan',
    '02':'Feb',
    '03':'Mar',
    '04':'Apr',
    '05':'May',
    '06':'Jun',
    '07':'Jul',
    '08':'Aug',
    '09':'Sep',
    '10':'Oct',
    '11':'Nov',
    '12':'Dec'
}

env = environ.Env()
environ.Env.read_env()

def get_token():
    url_login = "https://residential-api.oxylabs.io/v1/login"
    username = "rjpdigitechsol"
    password = "eN2nczdDdT"
    userpass = username + ':' + password
    encoded_u = "Basic " + base64.b64encode(userpass.encode()).decode()
    headers = {"accept":"application/json","Authorization" : encoded_u}
    resp = requests.post(url_login,headers=headers)
    token=resp.json()['token']
    user_id=resp.json()['user_id']
    return token,user_id

def get_subusers():    
    token, user_id = get_token()
    url_subusers = "https://residential-api.oxylabs.io/v1/users/"+ user_id +"/sub-users"    
    headers = {"accept":"application/json","Authorization" : "Bearer "+token}    
    resp = requests.get(url_subusers,headers=headers)
    return resp.json()

def create_subuser(username,password,email,traffic_limit=None,lifetime=False,auto_disable=True):
    token, user_id = get_token()
    url_subusers = "https://residential-api.oxylabs.io/v1/users/"+ user_id +"/sub-users"    
    headers = {"accept":"application/json","Authorization" : "Bearer "+token}    
    data = {
        "username": username,
        "password": password,
        "traffic_limit": traffic_limit,
        "lifetime": lifetime,
        "auto_disable": auto_disable
    }
    data = json.dumps(data)    
    resp = requests.post(url_subusers,headers=headers,data=data)
    response = resp.json()
    print(response)
    if resp.status_code == 201:
        user = User.objects.create_user(username=username,password=password,email=email)
        userprofile = UserProfile.objects.get(user=user)
        userprofile.lifetime = lifetime
        userprofile.user_name = username
        userprofile.auto_disable = auto_disable
        userprofile.traffic_limit = traffic_limit
        userprofile.userid = str(response['id'])
        userprofile.data_used = '0'
        userprofile.send = str(password)
        userprofile.save()
    return response

def update_user(sub_user,password=None,traffic_limit=None,lifetime=False,auto_disable=True,status='active'):
    token, user_id = get_token()
    url_subusers = "https://residential-api.oxylabs.io/v1/users/"+ user_id +"/sub-users/"+sub_user  
    headers = {"accept":"application/json","Authorization" : "Bearer "+token}    
    data = {        
        "password": password,
        "traffic_limit": traffic_limit,
        "lifetime": lifetime,
        "status": status,
        "auto_disable": auto_disable
    }
    data = json.dumps(data)    
    resp = requests.patch(url_subusers,headers=headers,data=data)
    if resp.status_code == 201:
        user = UserProfile.objects.get(userid=sub_user)
        if password != None:
            user.send = password
        if status == 'active':
            user.diabled = False
        elif status == 'disabled':
            user.diabled = True    
        user.save()
    return resp.json()


def delete_user(sub_user):
    token, user_id = get_token()
    url_subusers = "https://residential-api.oxylabs.io/v1/users/"+ user_id +"/sub-users/"+sub_user  
    headers = {"accept":"application/json","Authorization" : "Bearer "+token}        
    resp = requests.delete(url_subusers,headers=headers)
    if resp.status_code == 204:
        up = UserProfile.objects.get(userid=sub_user)
        user = User.objects.get(username=up.user.username)
        user.delete()
    return resp

def get_details(sub_user):
    token, user_id = get_token()
    url_subusers = "https://residential-api.oxylabs.io/v1/users/"+ user_id +"/sub-users/"+sub_user+"?type=month"    
    headers = {"accept":"application/json","Authorization" : "Bearer "+token}    
    resp = requests.get(url_subusers,headers=headers)
    respz = resp.json()
    if sub_user != "False" and resp.status_code == 200:
        user = UserProfile.objects.get(userid=sub_user)
        user.data_used = respz['traffic']
        user.save()
    return respz
    
def get_previous_day_data(sub_user):
    token, user_id = get_token()
    url_subusers = "https://residential-api.oxylabs.io/v1/users/"+ user_id +"/sub-users/"+sub_user+"?type=24h"    
    headers = {"accept":"application/json","Authorization" : "Bearer "+token}    
    resp = requests.get(url_subusers,headers=headers)
    respz = resp.json() 
    #respdict = json.load(respz)
    data = list(respz['trafficByPeriod'].values())
    return data    

class Home(LoginRequiredMixin,View):
    template_name='homepage.html'
    def get(self, *args, **kwargs):     
        if self.request.user.is_superuser:   
            users = UserProfile.objects.all()     
            for i in users:
                _ = get_details(i.userid)
                if i.diabled:
                    i.status = "Disabled"
                else:
                    i.status = "Active"
            context = {'users':users}
            return render(self.request,self.template_name,context=context)
        return redirect('core:index')                

class Usercreation(LoginRequiredMixin,View):
    template_name='createuser.html'
    def get(self, *args, **kwargs):
        if self.request.user.is_superuser:                        
            return render(self.request,self.template_name)
        return redirect('core:index')                        
    def post(self, *args, **kwargs):
        if self.request.user.is_superuser:        
            username = self.request.POST.get('username')
            password = self.request.POST.get('password')
            email = self.request.POST.get('email')
            _ = create_subuser(username, password, email=email)        
            return redirect('core:home')
        return redirect('core:index')

class UserUpdateView(LoginRequiredMixin,View):
    template_name='edituser.html'
    def get(self, *args, **kwargs):
        if self.request.user.is_superuser:
            user = UserProfile.objects.get(userid=self.kwargs["userid"])
            context={ 'user':user }
            return render(self.request,self.template_name,context=context)
        return redirect('core:index')
    def post(self, *args, **kwargs):               
        if self.request.user.is_superuser:
            password = self.request.POST.get('password')
            disabled = self.request.POST.get('status', None)        
            if disabled:
                status = "disabled"
            if not disabled:
                status = "active"        
            userid = self.kwargs['userid']
            token = update_user(sub_user=userid,password=password,status=status)
            return redirect('core:home')     
        return redirect('core:index')   

def make_downlodable(path,name):
    path = path
    zipfile =  open(path, 'rb')
    response = HttpResponse(zipfile, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=%s' % name
    response['Content-Length'] = os.path.getsize(path)
    zipfile.close()
    return response

@login_required
def chrome_download(request):
    response = make_downlodable('static/extensions/chrome.zip', 'chrome-ext.zip')
    return response

@login_required
def firefox_download(request):
    response = make_downlodable('static/extensions/firefox.zip', 'firefox-ext.zip')
    # response = make_downlodable(f'{env("EXTENSIONS_BASE_PATH")}/firefox.zip','firefox-ext.zip')
    return response

@login_required
def chrome_bot_download(request):
    response = make_downlodable('static/extensions/chrome-bot.zip', 'chrome-bot-ext.zip')
    #response = make_downlodable(f'{env("EXTENSIONS_BASE_PATH")}/chrome-bot.zip','chrome-bot-ext.zip')
    return response

@login_required
def firefox_bot_download(request):
    response = make_downlodable('static/extensions/firefox-bot.zip', 'firefox-bot-ext.zip')
    #response = make_downlodable(f'{env("EXTENSIONS_BASE_PATH")}/firefox-bot.zip','firefox-bot-ext.zip')
    return response

class GeneralPage(LoginRequiredMixin,View):
    template_name = "index.html"
    def get(self,*args,**kwargs):
        max_age = 1 * 24 * 60 * 60 
        send = self.request.user.userprofile.send
        data = get_previous_day_data(self.request.user.userprofile.userid)[0]
        response = render(self.request,self.template_name,context={'pdata':data})
        response.set_cookie("username",self.request.user.userprofile.user_name,max_age=max_age)
        response.set_cookie("receive",send,max_age=max_age)        
        response.set_cookie("data",data,max_age=max_age)
        return response         

        
class userstastics(LoginRequiredMixin,View):
    template_name='home.html'
    def get(self, *args, **kwargs):
        if self.request.user.is_superuser:
            token = get_details(self.kwargs['userid'])
            data_usage = token['trafficByPeriod']
            data = list(data_usage.values())
            dates = list(data_usage.keys())
            users = UserProfile.objects.all()     
            a = len(data)
            for i in range(a):
                parts = dates[i].split('-')
                month = parts[1]
                date = parts[2]
                month_by_name = months[month]
                dates[i] = month_by_name+' '+date            
            data_dict = {dates[i]:data[i] for i in range(a)}
            json_data_dict = json.dumps(data_dict)
            zipped = zip(dates,data)
            context={ 'token':token, 'data_used':json_data_dict, 'users':users, 'zipped':zipped }        
            return render(self.request,self.template_name,context=context)
        return redirect('core:index')        
    def post(self, *args, **kwargs):        
        if self.request.user.is_superuser:
            username = self.request.POST.get('username')
            password = self.request.POST.get('password')
            email = self.request.POST.get('email')                
            return redirect('core:home')
        return redirect('core:index')


class single_userstastics(LoginRequiredMixin,View):
    template_name='stats.html'
    def get(self, *args, **kwargs):              
        token = get_details(self.request.user.userprofile.userid)
        data_usage = token['trafficByPeriod']
        data = list(data_usage.values())
        dates = list(data_usage.keys())           
        a = len(data)
        for i in range(a):
            parts = dates[i].split('-')
            month = parts[1]
            date = parts[2]
            month_by_name = months[month]
            dates[i] = month_by_name+' '+date            
        data_dict = {dates[i]:data[i] for i in range(a)}
        json_data_dict = json.dumps(data_dict)
        zipped = zip(dates,data)
        context={ 'token':token, 'data_used':json_data_dict, 'zipped':zipped }        
        return render(self.request,self.template_name,context=context)         

class Delete_user(LoginRequiredMixin,View):
    def get(self,*args,**kwargs):
        if self.request.user.is_superuser:
            token = delete_user(self.kwargs['userid'])
            return redirect('core:home')                
        return redirect('core:index')