from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, render
from django.http import HttpResponse, HttpResponseRedirect
from crypto import commitment
import time, requests, hashlib
from datetime import datetime
from django.template import RequestContext
from vbb.models import Election, Choice
from abb.models import Abb, UpdateInfo
import cStringIO, zipfile, csv, copy,os, base64, random
from django.core.files import File

# Create your views here.

#used to create tabs in html template
class Ctuple:
    def __init__(self, o, x,y,z):
        self.opened = o
        self.plaintext = str(x)
        self.commitment = str(y)
        self.decommitment = str(z)

class DataPair:
    def __init__(self, x,y):
        self.Data = x
        self.Ver = y  

col_names = ['Serial # & Vote Code', 'Possible Vote', 'Ballot Check',  'Marked As Voted']

col_full_names = ['SN&VC(Comm)','SN&VC(Plain)','SN&VC(Decom)', 'BCheck(Comm)','BCheck(Plain)','BCheck(Decom)','PVote(Comm)','PVote(Plain)','PVote(Decom)','MarkV(Comm)','MarkV(Plain)','MarkV(Decom)']
   

def empty(request):
	return HttpResponse('Please specify the election ID.')



def index(request, eid = 0):
	try:
		e = Election.objects.get(EID=eid)
	except Election.DoesNotExist:
		return HttpResponse('The election ID is invalid!')
	#test debug	
	#firstadd(e)
	#BDadd(e)
	BigData = []
	# obtain current table numbers
	table_list = e.abb_set.values('table').distinct()
	tablenums = [x['table'] for x in table_list]
	tablenums.sort()
	for i in tablenums:
		verlist = e.abb_set.filter(table = i).values('version').distinct()
		ver = [x['version'] for x in verlist]
		ver.sort()
		Vtime = [e.updateinfo_set.get(table = i, version = j) for j in ver]
		Vtable = []
		for j in ver:
			table = []
			Abb_list = e.abb_set.filter(table = i,version = j)
			for x in Abb_list:
				data = []
				if x.serial_codes:
					data.append(Ctuple(True, x.serial_codes,x.Cserial_codes,x.Dserial_codes))
				else:
					if x.Cserial_codes:
						data.append(Ctuple(False,'',x.Cserial_codes,''))
					else:
						data.append(Ctuple(False,'','',''))
				if x.possible_votes:
					data.append(Ctuple(True,x.possible_votes,x.Cpossible_votes,x.Dpossible_votes))
				else:
					if x.Cpossible_votes:
						data.append(Ctuple(False,'',x.Cpossible_votes,''))
					else:
						data.append(Ctuple(False,'','',''))
				if x.ballot_check:
					data.append(Ctuple(True,x.ballot_check,x.Cballot_check,x.Dballot_check))
				else:
					if x.Cballot_check:
						data.append(Ctuple(False,'',x.Cballot_check,''))
					else:
						data.append(Ctuple(False,'','',''))
				
				if x.marked_as_voted:
					data.append(Ctuple(True,x.marked_as_voted,x.Cmarked_as_voted,x.Dmarked_as_voted))
				else:
					if x.Cmarked_as_voted:
						data.append(Ctuple(False,'',x.Cmarked_as_voted,''))
					else:
						data.append(Ctuple(False,'','',''))
                                table.append(data)
                        Vtable.append(table)
		BigData.append(DataPair(Vtable,Vtime))
	return render_to_response('abb.html', {'election':e, 'TableNum': tablenums, 'col_names':col_names, 'BigData': BigData})

def export(request, eid = 0, table = 0, ver = 0):
        try:
		e = Election.objects.get(EID=eid)
	except Election.DoesNotExist:
		return HttpResponse('The election ID is invalid!')
        Tnum = int(table)-1
        Vnum = int(ver)
        response = HttpResponse(content_type="application/zip")  
        response['Content-Disposition'] = 'attachment; filename=ABB.zip'
        z = zipfile.ZipFile(response,'w')   ## write zip to response
        # obtain current table numbers
        table_list = e.abb_set.values('table').distinct()
        tablenums = [x['table'] for x in table_list]
        tablenums.sort()
        if Tnum == -1 and Vnum == 0:
        #export current tables 
                for tab in tablenums:
                        output = cStringIO.StringIO() ## temp output file
                        writer = csv.writer(output, dialect='excel')
                        verlist = e.updateinfo_set.filter(table = tab).order_by('-version').values('version').distinct()
                        v = [x['version'] for x in verlist]
                        Abb_list = e.abb_set.filter(table = tab, version = v[0])
                        writer.writerow(col_full_names)
                        for item in Abb_list:
                                writer.writerow([item.Cserial_codes, item.serial_codes, item.Dserial_codes,  item.Cballot_check, item.ballot_check, item.Dballot_check, item.Cpossible_votes, item.possible_votes,  item.Dpossible_votes,  item.Cmarked_as_voted,  item.marked_as_voted,  item.Dmarked_as_voted])
                        z.writestr("Table_"+str(tab)+".csv", output.getvalue())  ## write csv file to zip        
        else:#export csv and signature
                if Tnum not in range(len(tablenums)):
                        return render_to_response('404.html')
                else:
                        verlist = e.updateinfo_set.filter(table = tablenums[Tnum]).values('version').distinct()
                        v = [x['version'] for x in verlist]
                if Vnum not in v:
                        return render_to_response('404.html')
                else:
                        u = e.updateinfo_set.get(table = tablenums[Tnum], version = Vnum)
                        z.writestr("Table_"+str(tablenums[Tnum])+"_Ver_"+ver+".csv", u.csv.read())
                        z.writestr("Sig_Table_"+str(tablenums[Tnum])+"_Ver_"+ver+".txt", u.sig.read())
        return response

@csrf_exempt
def init(request):
    if request.method == 'POST':# only accept post
        q = request.POST['question']
        start = request.POST['start']
        end = request.POST['end']
        eid = request.POST['eid']
        total = request.POST['total']
        opts = []
        # maximum 50 options
        for i in range(0,50):
            temp = request.POST.get('opt'+str(i),'')
            if temp != '':
                opts.append(temp)
            else:
                break
        #create election
        start_time = time.strptime(start, "%m/%d/%Y %H:%M")
        end_time = time.strptime(end, "%m/%d/%Y %H:%M")
        new_e = Election(start = datetime.fromtimestamp(time.mktime(start_time)), end = datetime.fromtimestamp(time.mktime(end_time)), question = q, EID = eid, total = total)
        new_e.save()
        # store choices
        for x in opts:
            new_c = Choice(election = new_e, text = x)
            new_c.save()
        return HttpResponse('success')   
    else:
        return render_to_response('404.html')
    
    
    
