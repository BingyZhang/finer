from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from vbb.forms import VoteForm, FeedbackForm
from vbb.models import Vbb, Dballot, Election, Choice, Bba
from abb.models import UpdateInfo
from django.utils import timezone
import datetime, cStringIO, zipfile, csv, copy,os, base64, random
from django.core.files import File
# Create your views here.

def empty(request):
	return HttpResponse('Please specify the election ID.')

def send_request(e):
	return True

def verify_code(e,s,c):
	codelist = []
	verified = False
	try:
		record = e.bba_set.get(serial = s)
	except Election.DoesNotExist:
		return codelist 	
        key = record.key
        #check hmac
        for i in range(2):
                pass 
	
	return codelist

	
def index(request, eid = 0):
	try:
		e = Election.objects.get(EID=eid)
	except Election.DoesNotExist:
		return HttpResponse('The election ID is invalid!')
	time = 0
	options = e.choice_set.all()
	table_data = []
	checkcode = "invalid code"
	running = 0
	if e.was_started():
		running = 1
		time = int((e.end - timezone.now()).total_seconds())
	if e.was_ended():
		running = 2
		if not e.request:
			send_request(e)
			e.request = True
			e.save()
		else:
			if e.tally:
				running = 3
	if e.pause:
                running = 10
        ######################
        #time = 99999
	#running = 1
	######################
	if request.method == 'POST':#there are two posts
		if running != 1:
			return HttpResponse("invalid code")
		if request.is_ajax():#ajax post
			form = VoteForm(request.POST) # A form bound to the POST data
			if form.is_valid(): # All validation rules pass
				s = form.cleaned_data.get('serial').lower()#request.POST['serial']
				c = form.cleaned_data.get('code').lower()#request.POST['code']
				if len(s) == 0 or len(c) ==0:
					return HttpResponse("invalid code")
				codelist = verify_code(e,s,c)
				if len(codelist) != 0:
					#add the code to DB
					new_entry = Vbb(election = e, serial = s, votecode = c)
					new_entry.save()
                                        return render_to_response('feedback.html', {'codes': codelist})
                                else:
                                        return HttpResponse("invalid code")
			else:
				return HttpResponse("invalid code")
		else:
			form = FeedbackForm(request.POST) # A form bound to the POST data
			if form.is_valid(): # All validation rules pass
				ic = form.cleaned_data.get('checkcode').lower()
				io = form.cleaned_data.get('checkoption') #request.POST['checkoption']
				if io != '--- Select an option ---':
                                        ballot = Dballot.objects.get(code = ic)
                                        ballot.value = io
                                        ballot.save()
				return render_to_response('thanks.html')
			else:
				return HttpResponse("invalid code")
	else:# no post
		data = e.vbb_set.all().order_by('-date')
		#prepare the table_data
		for item in data:
			temp_row = []
			temp_row.append(item.serial)
			temp_row.append(item.votecode)
			temp_row.append(item.date)
			unused = item.dballot_set.filter(checked = True)
			for u in unused:
                                temp_row.append(u.code)
                                if u.value:
					temp_row.append(u.value)
				else:
                                        temp_row.append(' ')
			table_data.append(temp_row)
		progress = int(e.vbb_set.count()*100/e.total+0.5)

		return render_to_response('vbb.html', {'data':table_data, 'options':options, 'time':time, 'running':running, 'election':e, 'progress':progress}, context_instance=RequestContext(request))


def export(request, eid = 0):
        try:
		e = Election.objects.get(EID=eid)
	except Election.DoesNotExist:
		return HttpResponse('The election ID is invalid!')
	response = HttpResponse(content_type="application/zip")  
        response['Content-Disposition'] = 'attachment; filename=VBB['+timezone.now().strftime('%B-%d-%Y')+'].zip'
        z = zipfile.ZipFile(response,'w')   ## write zip to response
	#export serial numbers and voted codes 
        data = e.vbb_set.all()
        output = cStringIO.StringIO() ## temp CSV file
        writerA = csv.writer(output, dialect='excel')       
        for item in data:
                writerA.writerow([item.serial,'voted', item.votecode])
                #obtain Dballots
                dballs = item.dballot_set.all()
                for d in dballs:
                        if d.value:
                                writerA.writerow([d.serial, 'check',d.code+'-'+d.value])
        z.writestr("Votes.csv", output.getvalue())  ## write votes csv file to zip
        # fake signature
        z.writestr("Sig_Votes.txt", "Fake signature. This CSV file is signed by the VBB.")  ## write signature to zip
        return response


@csrf_exempt
def upload(request, eid = 0):
    try:
	e = Election.objects.get(EID=eid)
    except Election.DoesNotExist:
	return HttpResponse('The election ID is invalid!')
    if request.method == 'POST':
        zfile = request.FILES['inputfile']
        sig = request.FILES['sig']
        ## Sanity checks...

        #processing upload files
	z = zipfile.ZipFile(zfile, 'r')
	for name in z.namelist():
                if name.endswith(".txt"):
			opfile = z.read(name)
		else:
			datafile = z.read(name)
        ## Record update log
	notes = timezone.now().isoformat(' ')+"-"+opfile
	zfile.name = notes+".zip"
	sig.name = "Sig_"+notes+".txt"
        new_op = UpdateInfo(election = e, text = notes, file = zfile, sig = sig)
        new_op.save()
        flag = 0
        if opfile == 'votecode':
                flag = 1 
                reader = datafile.splitlines()
                #populate BBA database handle CSV file myself
                for rows in reader:
                        if rows != '':
                                items = rows.split(',')
                                new_entry = Bba(election = e, serial = items[0].strip().lower(), code = items[1].strip().lower())
                                new_entry.save()
                return HttpResponse('The votecodes have been uploaded to VBB.')                
        elif opfile == 'end':
                flag = 1 
                e.end = timezone.now()
                e.save()
                return HttpResponse('The election is ended.')
        elif opfile == 'lock':
                flag = 1 
                e.pause = True
                e.save()
                return HttpResponse('The election is locked.')
        elif opfile == 'unlock':
                flag = 1 
                e.pause = False
                e.save()
                return HttpResponse('The election is unlocked.')
        if flag == 1:
            return HttpResponse('The data has been uploaded to VBB.')
        else:
            return HttpResponse('Sorry, the operation code is not recognized.')                
        
        
    else:
        return render_to_response('404.html')








