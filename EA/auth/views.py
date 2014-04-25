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
    name = request.META.get('HTTP_CAS_CN_LANG_EL','')
    if name == '':# for non-greek person
	name = request.META['HTTP_CAS_CN']
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
		if e.was_started():
			started = True
		else:
			started = False
		elections.append({'e':e,'started':started,'ended':ended})
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
    if not e.prepared:
	return HttpResponse('The ballots are not prepared yet.')
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
    name = request.META.get('HTTP_CAS_CN_LANG_EL','')
    if name == '':# for non-greek person
        name = request.META['HTTP_CAS_CN']
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
	#mark as used
	b.used = True
	b.save()
    #get codes and options
    codes1 = b.codes1.split(',')
    codes2 = b.codes2.split(',')
    rec1 = b.rec1.split(',')
    rec2 = b.rec2.split(',')
    perm1 = b.votes1.split(',')
    perm2 = b.votes2.split(',')
    #sort according to perm1
    sorted1 = sorted(zip(perm1,codes1,rec1))
    sorted2 = sorted(zip(perm2,codes2,rec2))
    ballot_code1 = [y for (x,y,z) in sorted1]
    ballot_code2 = [y for (x,y,z) in sorted2]
    ballot_rec1 = [z for (x,y,z) in sorted1]
    ballot_rec2 = [z for (x,y,z) in sorted2]

    #only send email for the first time
    if first_time:	
    	#there is something wrong with Greek name
    	en_name = request.META['HTTP_CAS_CN']
    	emailbody = "Hello "+en_name+",\n\nHere is your ballot.\n"
	emailbody+= "================================================\nSerial Number: "+b.serial+"\n"
	emailbody+= "================================================\nBallot A: \n"
	for i in range(len(options)):
		emailbody+= "Votecode: "+ballot_code1[i]+"  Receipt: "+ballot_rec1[i]+ "  Option: "+opts[i]+"\n"
        emailbody+= "================================================\nBallot B: \n"
        for i in range(len(options)):
                emailbody+= "Votecode: "+ballot_code2[i]+"  Receipt: "+ballot_rec2[i]+ "  Option: "+opts[i]+"\n"
	emailbody+= "================================================\n"
    	emailbody+= "\nVBB_url: "+ABB_URL+"/vbb/"+eid+"/\n"
    	emailbody+= "ABB_url: "+ABB_URL+"/abb/"+eid+"/\n"
    	emailbody+= "\nFINER Ballot Distribution Server\n"
    	#send email		
    	p = subprocess.Popen(["sudo","/var/www/finer/bingmail.sh","Ballot for Election: "+e.question, emailbody,email],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    	output,err = p.communicate()


    return render_to_response('vote.html',{'bb_url':ABB_URL, 'serial':b.serial , 'time':time, 'running':running, 'election':e, 'name':name, 'email':email,'c1':zip(ballot_code1,opts),'c2':zip(ballot_code2,opts)}, context_instance=RequestContext(request))

def client(request, eid = 0,token = 0):
    try:
        e = Election.objects.get(EID=eid)
    except Election.DoesNotExist:
        return HttpResponse('The election ID is invalid!')
    #fetch ballot
    try:
        record = e.tokens_set.get(token=token)
    except Tokens.DoesNotExist:
	return HttpResponse('The token is invalid!')
    name = "Email Voter"    
    options = e.choice_set.values('text')
    opts = [x['text'] for x in options]
    running = 0
    if e.was_started():
	running = 1
	time = int((e.end - timezone.now()).total_seconds())
    if e.was_ended():
	running = 2
    #get ballot
    assign = e.assignment_set.get(vID=record.token+record.email)
    b = e.ballot_set.get(serial = assign.serial)
    #get codes and options
    codes1 = b.codes1.split(',')
    codes2 = b.codes2.split(',')
    rec1 = b.rec1.split(',')
    rec2 = b.rec2.split(',')
    perm1 = b.votes1.split(',')
    perm2 = b.votes2.split(',')
    #sort according to perm1
    sorted1 = sorted(zip(perm1,codes1,rec1))
    sorted2 = sorted(zip(perm2,codes2,rec2))
    ballot_code1 = [y for (x,y,z) in sorted1]
    ballot_code2 = [y for (x,y,z) in sorted2]
    ballot_rec1 = [z for (x,y,z) in sorted1]
    ballot_rec2 = [z for (x,y,z) in sorted2]
    return render_to_response('vote.html',{'bb_url':ABB_URL, 'serial':b.serial , 'time':time, 'running':running, 'election':e, 'name':name, 'email':record.email,'c1':zip(ballot_code1,opts),'c2':zip(ballot_code2,opts)}, context_instance=RequestContext(request))


def pdfballot(request, eid = 0,token = 0):
    try:
        e = Election.objects.get(EID=eid)
    except Election.DoesNotExist:
        return HttpResponse('The election ID is invalid!')
    #fetch ballot
    try:
        record = e.pdfballot_set.get(token=token)
    except Pdfballot.DoesNotExist:
        return HttpResponse('The token is invalid!')
    name = "Email Voter"
    options = e.choice_set.values('text')
    opts = [x['text'] for x in options]
    running = 0
    if e.was_started():
        running = 1
        time = int((e.end - timezone.now()).total_seconds())
    if e.was_ended():
        running = 2
    #get ballot
    assign = e.assignment_set.get(vID=record.token+record.email)
    b = e.ballot_set.get(serial = assign.serial)
    #get codes and options
    codes1 = b.codes1.split(',')
    codes2 = b.codes2.split(',')
    rec1 = b.rec1.split(',')
    rec2 = b.rec2.split(',')
    perm1 = b.votes1.split(',')
    perm2 = b.votes2.split(',')
    #sort according to perm1
    sorted1 = sorted(zip(perm1,codes1,rec1))
    sorted2 = sorted(zip(perm2,codes2,rec2))
    ballot_code1 = [y for (x,y,z) in sorted1]
    ballot_code2 = [y for (x,y,z) in sorted2]
    ballot_rec1 = [z for (x,y,z) in sorted1]
    ballot_rec2 = [z for (x,y,z) in sorted2]
    return render_to_response('vote.html',{'bb_url':ABB_URL, 'serial':b.serial , 'time':time, 'running':running})


