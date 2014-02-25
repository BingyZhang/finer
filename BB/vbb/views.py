from django.shortcuts import render_to_response, render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from vbb.forms import VoteForm, FeedbackForm
from vbb.models import Vbb, Dballot, Election, Choice
from django.utils import timezone
import datetime, random
# Create your views here.

def empty(request):
	return HttpResponse('Please specify the election ID.')

def send_request(e):
	return True

def verify_code(e,s,c):
	codelist = []
	verified = False
	codes = e.bba_set.filter(serial__startswith = s[:len(s)-1])
	if len(codes) == 0:
		return codelist 	
	for x in codes:
		#check if voted
		if x.voted:
			break
		if x.serial == s and x.code == c:
			verified = True
			break
	if verified:
		#set as voted
		for x in codes:
			x.voted = True
			x.save()
		ser = ''
		if s[len(s)-1] == 'a':
			ser = s[:len(s)-1]+'b'
		else:
			ser = s[:len(s)-1]+'a'
		codelist.append(ser)		
		for y in codes:
			if y.serial == ser:
				codelist.append(y.code)
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
	if request.method == 'POST':#there are two posts
		if running <1:
			return HttpResponse('Sorry, this election has not started yet.')
		if running >=2:
			return HttpResponse('Sorry, this election is already closed.')
		if request.is_ajax():#ajax post
			form = VoteForm(request.POST) # A form bound to the POST data
			if form.is_valid(): # All validation rules pass
				s = form.cleaned_data.get('serial').lower()#request.POST['serial']
				c = form.cleaned_data.get('code').lower()#request.POST['code']
				codelist = verify_code(e,s,c)
				if len(codelist) != 0:
					#add the code to DB
					new_entry = Vbb(election = e, serial = s, votecode = c)
					new_entry.save()
					#store the dual ballot
					for i in range(1,len(codelist)):
						ballot = Dballot(vbb = new_entry, serial = codelist[0], code = codelist[i])
						ballot.save()
					#randomly select one code
					r = random.SystemRandom().randint(1, len(codelist)-1)
					checkcode = codelist[r]
				return HttpResponse(checkcode)
			else:
				return HttpResponse('Wrong form.')
		else:
			form = FeedbackForm(request.POST) # A form bound to the POST data
			if form.is_valid(): # All validation rules pass
				ic = form.cleaned_data.get('checkcode').lower()
				io = form.cleaned_data.get('checkoption') #request.POST['checkoption']
				ballot = Dballot.objects.get(code = ic)
				ballot.value = io
				ballot.save()
				return render_to_response('thanks.html')
			else:
				return HttpResponse('Wrong form.')
	else:# no post
		data = e.vbb_set.all().order_by('-date')
		#prepare the table_data
		for item in data:
			temp_row = []
			temp_row.append(item.serial)
			temp_row.append(item.votecode)
			temp_row.append(item.date)
			unused = item.dballot_set.order_by('code')
			for u in unused:
				temp_row.append(u.code)
				if u.value:
					temp_row.append(u.value)
				else:
					temp_row.append(' ')
			table_data.append(temp_row)
		progress = int(e.vbb_set.count()*100/e.total+0.5)
		return render_to_response('vbb.html', {'data':table_data, 'options':options, 'time':time, 'running':running, 'election':e, 'progress':progress}, context_instance=RequestContext(request))

