from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, render
from django.http import HttpResponse, HttpResponseRedirect
from crypto import commitment
import time, requests, hashlib,subprocess
from datetime import datetime
from django.utils import timezone
from elect_def.forms import DefForm
from elect_def.models import Election, Choice, Assignment
from django.template import RequestContext
import cStringIO, zipfile, csv, copy,os, base64, random
from django.core.files import File
from tasks import add,prepare_ballot
# Create your views here.

BB_URL = "http://tal.di.uoa.gr/ea"
ABB_URL = "http://tal.di.uoa.gr/finer"



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
    return render_to_response('login.html',{'name':name, 'elist':elections, 'BB_URL':BB_URL, 'a':user_Paffiliation,'b':user_title,'c':user_Porg})









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

def vote(request, eid = 0):
    try:
        e = Election.objects.get(EID=eid)
    except Election.DoesNotExist:
        return HttpResponse('The election ID is invalid!')
    time = 0
    options = e.choice_set.values('text')
    opts = [x['text'] for x in options]
    running = 0
    if e.was_started():
	running = 1
	time = int((e.end - timezone.now()).total_seconds())
    if e.was_ended():
	running = 2
    #assigne ballot
    name = request.META['HTTP_CAS_CN_LANG_EL']
    ID = request.META['HTTP_CAS_UID']
    email = request.META['HTTP_CAS_MAIL'] 
    first_time = False
    try:
        assign = e.assignment_set.get(vID=ID)
	b = e.ballot_set.get(serial = assign.serial)
    except Assignment.DoesNotExist:
        #assign one
	first_time = True
	b = e.ballot_set.filter(used = False)[0]
	assign = Assignment(election = e, vID = ID, serial = b.serial)
	assign.save()
    #get codes and options
    codes1 = b.codes1.split(',')
    codes2 = b.codes2.split(',')
    perm1 = b.votes1.split(',')
    perm2 = b.votes2.split(',')
    #sort according to perm1
    sorted1 = [x for (y,x) in sorted(zip(perm1,codes1))]
    sorted2 = [x for (y,x) in sorted(zip(perm2,codes2))]
    ballot1 = zip(sorted1,opts)
    ballot2 = zip(sorted2,opts)
    #only send email for the first time
    if first_time:	
    	#there is something wrong with Greek name
    	en_name = request.META['HTTP_CAS_CN']
    	emailbody = "Hello "+en_name+",\nHere is your ballot.\n"
	emailbody+= "==========================================\nSerial Number: "+b.serial+"\n"
	emailbody+= "==========================================\nBallot A: \n"
	for i in range(len(options)):
		emailbody+= sorted1[i]+"   "+opts[i]+"\n"
        emailbody+= "==========================================\nBallot B: \n"
        for i in range(len(options)):
                emailbody+= sorted2[i]+"   "+opts[i]+"\n"
	emailbody+= "==========================================\n"
    	emailbody+= "\nVBB_url: "+ABB_URL+"/vbb/"+eid+"/\n"
    	emailbody+= "ABB_url: "+ABB_URL+"/abb/"+eid+"/\n"
    	emailbody+= "\nFINER Ballot Distribution Server\n"
    	#send email		
    	p = subprocess.Popen(["sudo","/home/bingsheng/bingmail.sh","Ballot for Election "+eid, emailbody,email],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    	output,err = p.communicate()




    return render_to_response('vote.html',{'options':opts, 'time':time, 'running':running, 'election':e, 'name':name, 'email':email})
