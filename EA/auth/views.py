from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, render
from django.http import HttpResponse, HttpResponseRedirect
from crypto import commitment
import time, requests, hashlib,subprocess
from datetime import datetime
from django.utils import timezone
from elect_def.forms import DefForm
from elect_def.models import Election, Choice
from django.template import RequestContext
import cStringIO, zipfile, csv, copy,os, base64, random
from django.core.files import File
from tasks import add,prepare_ballot
# Create your views here.

BB_URL = "http://tal.di.uoa.gr/ea"




def login(request):
    #handle CAS
    name = request.META['HTTP_CAS_CN_LANG_EL']
    elist = Election.objects.order_by('end')
    #constraint filter
    user_Paffiliation = request.META['HTTP_CAS_EDUPERSONPRIMARYAFFILIATION'].lower().rstrip()
    user_title = request.META['HTTP_CAS_TITLE'].lower().rstrip()
    user_Porg = request.META['HTTP_CAS_EDUPERSONPRIMARYORGUNITDN'].lower().rstrip()
    elections = []
    for e in elist:
	flag = 0    
	#check if user is a sub-string
        templist = e.Paffiliation.split(',')
	for temp in templist:
		if user_Paffiliation == temp.rstrip() or temp.rstrip() == "*":
			flag +=1
			break
	templist = e.title.split(',')
        for temp in templist:
                if user_title == temp.rstrip() or temp.rstrip() == "*":
                        flag +=10
                        break
	templist = e.Porg.split(',')
        for temp in templist:
                if temp.rstrip() in user_Porg or temp.rstrip() == "*":
                        flag +=100
                        break
	if flag ==111:
		if e.was_ended():
			ended = True
		else:
			ended = False
		elections.append({'e':e,'ended':ended})
    return render_to_response('login.html',{'name':name, 'elist':elections, 'BB_URL':BB_URL ,'user_Paffiliation':user_Paffiliation,'user_title':user_title, 'user_Porg':user_Porg})









def test(request):
    #handle CAS
    n = 10
    p = subprocess.Popen(["sh","/home/bingsheng/EC-ElGamal/test.sh", str(n)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output,err = p.communicate()
    prepare_ballot.delay(4,4)
    elist = Election.objects.values('EID').distinct()
    temp = ''
    if len(elist)>0:
	IDs = [x['EID'] for x in elist]
	temp = IDs[0]

    return HttpResponse("Hello, "+request.META['HTTP_CAS_CN_LANG_EL'])

