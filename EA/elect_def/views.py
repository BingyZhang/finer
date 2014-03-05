from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, render
from django.http import HttpResponse, HttpResponseRedirect
from crypto import commitment
import time, requests, hashlib,subprocess
from datetime import datetime
from elect_def.forms import DefForm
from elect_def.models import Election, Choice
from django.template import RequestContext
import cStringIO, zipfile, csv, copy,os, base64, random,binascii
from django.core.files import File
from django.utils import timezone
from tasks import prepare_ballot
# Create your views here.

BB_URL = "http://tal.di.uoa.gr/finer/"

def base36encode(number, alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    """Converts an integer to a base36 string."""
    if not isinstance(number, (int, long)):
        raise TypeError('number must be an integer')
    base36 = ''
    sign = ''
    if number < 0:
        sign = '-'
        number = -number
    if 0 <= number < len(alphabet):
        return sign + alphabet[number]
    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36
    return sign + base36
 
def base36decode(number):
    return int(number, 36)


@csrf_exempt  # not secure, need signature or TBA
def index(request):
    name = request.META.get('HTTP_CAS_CN_LANG_EL','')
    if name == '':# for non-greek person
        name = request.META['HTTP_CAS_CN']
    if request.method == 'POST':
        q = request.POST['question']
        start = request.POST['elect_start']
        end = request.POST['elect_end']
        Paffiliation = request.POST['Paffiliation'].lower()
        title = request.POST['title'].lower()
        Porg = request.POST['Porg'].lower()
        total = request.POST['total']
        opts = []
        # maximum 50 options
        for i in range(1,51):
            temp = request.POST.get('opt'+str(i),'')
            if temp != '':
                opts.append(temp)
            else:
                break
        if Paffiliation == '':
	    Paffiliation = '*'
	if title == '':
	    title = '*'
	if Porg == '':
	    Porg = '*'
	if total == '':
	    total = "1"
	if start =='':
	    start = timezone.now().strftime("%m/%d/%Y %H:%M")
        if end =='':
            end = timezone.now().strftime("%m/%d/%Y %H:%M")
	start_time = time.strptime(start, "%m/%d/%Y %H:%M")
	end_time = time.strptime(end, "%m/%d/%Y %H:%M")
        #EID should be hash of question start and end time
        #eid = hashlib.sha1(q + start + end).hexdigest()
	eid = base36encode(long(binascii.hexlify(hashlib.sha1(q + start + end).digest()), 16))
        #first post to BB
        files = { 'question': q, 'start':start,'end':end, 'eid':eid,'total':total}
        for i in range(len(opts)):
            files["opt"+str(i)] = opts[i]
        r = requests.post(BB_URL+'/def/',data = files)
        #if r != "success":
        #    return HttpResponse(r)#('Error!')

        #create election
        new_e = Election(Paffiliation = Paffiliation, title = title, Porg = Porg, start = datetime.fromtimestamp(time.mktime(start_time)), end = datetime.fromtimestamp(time.mktime(end_time)), question = q, EID = eid, total = total)
        new_e.save()
        # store choices
        for x in opts:
            new_c = Choice(election = new_e, text = x)
            new_c.save()
        
        #confirm EA
        data = []
        data.append("Question: "+q)
        for i in range(len(opts)):
            data.append("Option "+str(i+1)+": "+opts[i])
        data.append("Start time: "+start)
        data.append("End time: "+end)
        data.append("Maximum number of voters: "+total)
        data.append("eduPersonPrimaryAffiliation: "+Paffiliation)
        data.append("Tile: "+title)
        data.append("eduPersonPrimaryOrgUnitDN: "+Porg)
	VBB_url = BB_URL+"vbb/"+eid+"/"
        ABB_url = BB_URL+"abb/"+eid+"/"
        email = request.META['HTTP_CAS_MAIL']
	#send email
	en_name = request.META['HTTP_CAS_CN']
	emailbody = "Hello "+en_name+",\n The following election is created.\n"
	emailbody+= "\n".join(data)
	emailbody+= "\nVBB_url: "+VBB_url+"\n"
	emailbody+= "ABB_url: "+ABB_url+"\n"
    	emailbody+= "\nFINER  Election Authority\n"

    	#send email         
    	p = subprocess.Popen(["sudo","/home/bingsheng/bingmail.sh","Election Definition "+eid, emailbody,email],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    	output,err = p.communicate()
	#celery prepare ballots
	prepare_ballot.delay(new_e, int(total)+1,len(opts))
        return render_to_response('confirm.html',{'name':name,'data':data, 'email':email,'VBB':VBB_url,'ABB':ABB_url})
    else:
        return render_to_response('def.html', {'name':name}, context_instance=RequestContext(request))




def vote(request, eid = 0):
    try:
        e = Election.objects.get(EID=eid)
    except Election.DoesNotExist:
        return HttpResponse('The election ID is invalid!')
    return render_to_response('vote.html')






def TBA(request, eid = 0):
    try:
	e = Election.objects.get(EID=eid)
    except Election.DoesNotExist:
	return HttpResponse('The election ID is invalid!')
    return render_to_response('def.html')
