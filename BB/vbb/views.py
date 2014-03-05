from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from vbb.forms import VoteForm, FeedbackForm
from vbb.models import Vbb, Dballot, Election, Choice, Bba
from abb.models import UpdateInfo,Abbinit
from django.utils import timezone
import datetime, cStringIO, zipfile, csv, copy,os, base64, random,hmac,hashlib,binascii,subprocess
from django.core.files import File
from tasks import add
# Create your views here.

def addbars(code):
        output = ''
        for i in range(3):
                if i != 0:
                        output+="-"
                output+=code[i*4:(i+1)*4]
        return output

def removebars(code):
        return code[0:4]+code[5:9]+code[10:len(code)]

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


def empty(request):
	return HttpResponse('Please specify the election ID.')

def send_request(e):
	#tally
	votes = e.vbb_set.all()
	opts = e.choice_set.all()
	n = len(opts)
	#get all for fast disk IO
	abbs = e.abbinit_set.all()
	opt_ciphers = [[] for x in range(n)]#ElGamal
        #prepare the table_data
        for each in votes:
		feedback = each.dballot_set.filter(checked = True)
                record = abbs.get(serial = each.serial)
		codes1 = record.codes1.split(',')
		codes2 = record.codes2.split(',')
		cipher1 =record.cipher1.split(',')
		cipher2 = record.cipher2.split(',')
		mark1 = []
		mark2 = []
		for i in range(n):
			if each.votecode == codes1[i]:
				mark1.append("Voted")
				#2n*i to 2n*(i+1)-1 put ciphers
				for j in range(n):
					temp = cipher1[2*n*i+2*j].split(' ')
					for t in temp:
						opt_ciphers[j].append(t)
                                        temp = cipher1[2*n*i+2*j+1].split(' ')
                                        for t in temp:
                                                opt_ciphers[j].append(t)				
			else:
				mark1.append("")
		for i in range(n):
                        if each.votecode == codes2[i]:
                                mark2.append("Voted")
                                #2n*i to 2n*(i+1)-1 put ciphers
                                for j in range(n):
                                        temp = cipher2[2*n*i+2*j].split(' ')
                                        for t in temp:
                                                opt_ciphers[j].append(t)
					temp = cipher2[2*n*i+2*j+1].split(' ')
                                        for t in temp:
                                                opt_ciphers[j].append(t)
                        else:
                                mark2.append("")
		#mark feedbacks
                if len(feedback)!=0:
			for feed in feedback:
				for i in range(n):
                        		if feed.code == codes1[i]:
						mark1[i] = feed.value
				for i in range(n):
                                        if feed.code == codes2[i]:
                                                mark2[i] = feed.value
		#store marks
		record.mark1 = ",".join(mark1)
		record.mark2 = ",".join(mark2)
		record.save()
	#output for tally
	for i in range(n):
		temp_str = "\n".join(opt_ciphers[i])
		#f = open('/var/www/finer/EC-ElGamal/debug.txt', 'a')
		#f.write(temp_str)
		#f.write("\n\n\n")
		#f.close
		p = subprocess.Popen(["sh","/var/www/finer/EC-ElGamal/Tally.sh",temp_str],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	    	output,err = p.communicate()
		opts[i].votes = int(output)
		opts[i].save()
	#store result
	e.tally = True
	e.save()


def verify_code(e,s,vcode):
	codelist = []
	templist = []
	receipt = ""
	try:
		record = e.bba_set.get(serial = s)
	except Bba.DoesNotExist:
		return codelist,receipt
	if record.voted:
		return codelist,receipt
	checkcode = removebars(vcode)
        key = base64.b64decode(record.key)
        n = record.n
        #check hmac
        codes1 = []
        codes2 = []
        rec1 = []
        rec2 = []
	#return codelist,str(n)
        for i in range(n):
                message = bytes(s+str(0)+str(i)).encode('utf-8') 
                c = hmac.new(key, message, digestmod=hashlib.sha256).digest()
	        c1 = long(binascii.hexlify(c[0:8]), 16) #convert 64 bit string to long
	        c1 &= 0x3fffffffffffffff # 64 --> 62 bits
	        codes1.append(base36encode(c1))
	        r1 = long(binascii.hexlify(c[8:12]), 16) #convert 32 bit string to long
                r1 &= 0x7fffffff # 32 --> 31 bits
                rec1.append(base36encode(r1))
                #ballot 2
                message = bytes(s+str(1)+str(i)).encode('utf-8') 
                c = hmac.new(key, message, digestmod=hashlib.sha256).digest()
	        c2 = long(binascii.hexlify(c[0:8]), 16) #convert 64 bit string to long
	        c2 &= 0x3fffffffffffffff # 64 --> 62 bits
	        codes2.append(base36encode(c2))
	        r2 = long(binascii.hexlify(c[8:12]), 16) #convert 32 bit string to long
                r2 &= 0x7fffffff # 32 --> 31 bits
                rec2.append(base36encode(r2))
	for i in range(n):
                if codes1[i] == checkcode:
                        templist = codes2
                        receipt = rec1[i]
                        record.voted = True
                        record.save()
                        break
                if codes2[i] == checkcode:
                        templist = codes1
                        receipt = rec2[i]
                        record.voted = True
                        record.save()
                        break
	for x in templist:
		codelist.append(addbars(x))       
	return codelist,receipt



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
	if request.method == 'POST':#there are two posts
		if running != 1:
			return HttpResponse("invalid code")
		if request.is_ajax():#ajax post
			form = VoteForm(request.POST) # A form bound to the POST data
			if form.is_valid(): # All validation rules pass
				s = form.cleaned_data.get('serial').upper()#request.POST['serial']
				c = form.cleaned_data.get('code').upper()#request.POST['code']
				if len(s) == 0 or len(c) ==0:
					return HttpResponse("invalid code")
				codelist,receipt = verify_code(e,s,c)
				if receipt != "":
					#add the code to DB
					new_entry = Vbb(election = e, serial = s, votecode = c)
					new_entry.save()
					#store the dual ballot
					for i in range(len(codelist)):
						balls = Dballot(vbb = new_entry, serial = s, code = codelist[i])
						balls.save()
					#return HttpResponse(receipt)
                                        return render_to_response('feedback.html', {'codes': codelist,'options':options,'rec':receipt}, context_instance=RequestContext(request))
                                else:
                                        return HttpResponse("invalid code")
			else:
				return HttpResponse("invalid code")
		else:
			form = FeedbackForm(request.POST) # A form bound to the POST data
			if form.is_valid(): # All validation rules pass
				ic = form.cleaned_data.get('checkcode')				
				io = form.cleaned_data.get('checkoption') #request.POST['checkoption']
				if "Select" not in io and "Select" not in ic:# good feedback
                                        ball = Dballot.objects.get(code = ic)
                                        ball.value = io
					ball.checked = True
                                        ball.save()
				return render_to_response('thanks.html')
			else:
				return HttpResponse("Wrong Form")
	else:# no post
		data = e.vbb_set.all().order_by('-date')
		#prepare the table_data
		for item in data:
			temp_row = []
			temp_row.append(item.serial)
			temp_row.append(item.votecode)
			temp_row.append(item.date)
			unused = item.dballot_set.filter(checked = True)
			l = len(unused)
			if l==0:
			    temp_row.append("")
			    temp_row.append("")			

			else:
			#randomly display one
			    if l > 1:
				x = random.randrange(l)
				temp_row.append(unused[x].code)
                                temp_row.append(unused[x].value)
			    else: 
                                temp_row.append(unused[0].code)
			        temp_row.append(unused[0].value)
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
                                writerA.writerow([d.serial, 'check',d.code+' : '+d.value])
        z.writestr("Votes.csv", output.getvalue())  ## write votes csv file to zip
        # fake signature
        z.writestr("Sig_Votes.txt", "Fake signature. This CSV file is signed by the VBB.")  ## write signature to zip
        return response


@csrf_exempt
def client(request, eid = 0):
    try:
	e = Election.objects.get(EID=eid)
    except Election.DoesNotExist:
	return HttpResponse('The election ID is invalid!')
    if request.method == 'POST':
	feedback = []
        # maximum 50 options
        for i in range(1,51):
            temp = request.POST.get('feedback'+str(i),'')
            if temp != '':
                feedback.append(temp)
            else:
                break
	code = request.POST["options"].upper()
	serial = request.POST["serial"].upper()
	codelist,receipt = verify_code(e,serial,code)
        if receipt != "":
            #add the code to DB
            new_entry = Vbb(election = e, serial = serial, votecode = code)
            new_entry.save()
            #store the dual ballot feedback
            for x in feedback:
		feed = x.split(",")
		if feed[0] in codelist:
            	    balls = Dballot(vbb = new_entry, serial = serial, code = feed[0], checked = True, value = feed[1])
                    balls.save()

            return render_to_response('thanks.html')
	else:
	    return render_to_response('client_reject.html')
        
    else:
        return render_to_response('404.html')








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
                                new_entry = Bba(election = e, serial = items[0].strip().upper(), code = items[1].strip().upper())
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








