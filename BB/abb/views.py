from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, render
from django.http import HttpResponse, HttpResponseRedirect
from crypto import commitment
import time, requests, hashlib
from datetime import datetime
from django.template import RequestContext
from vbb.models import Election,Choice,Randomstate,Bba
from Crypto.Cipher import AES
from Crypto import Random
from django.utils import timezone
from abb.models import AbbKey,AbbData, UpdateInfo, Auxiliary,Abbinit
import cStringIO, zipfile, csv, copy,os, base64, random
from django.core.files import File

# Create your views here.

def pad(s):
    return s + b"\0" * (AES.block_size - len(s) % AES.block_size)

def encrypt(message, key, key_size=256):
    message = pad(message)
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return iv + cipher.encrypt(message)

def decrypt(ciphertext, key):
    iv = ciphertext[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = cipher.decrypt(ciphertext[AES.block_size:])
    return plaintext.rstrip(b"\0")




#used to create tabs in html template
class Ctuple:
    def __init__(self, o, x,y,z):
        self.opened = o
        self.plaintext = str(x)
        self.commitment = str(y)
        self.decommitment = str(z)

class DataTriple:
    def __init__(self, x,y,z):
        self.Data = x
        self.Ver = y
        self.Log = z

col_names = ['Serial #', 'Vote Code', 'Candidate Index', 'Pre-vote Audit', 'Vote Mark','Random Coin', 'Post-vote Audit']

col_mapping = {'SN&VC (comm)':1,	 'SN&VC (plain)':2,	 'SN&VC (decomm)':3,	 'PCheck (comm)':4,	 'PCheck (plain)':5,	 'PCheck (decomm)':6,	 'PossVote (comm)':7,	 'PossVote (plain)':8,	 'PossVote (decomm)':9,	 'MarkVoted (comm)':10,	 'MarkVoted (plain)':11,	 'MarkVoted (decomm)':12,	 'PreSumA (comm)':13,	 'PreSumA (plain)':14,	 'PreSumA (decomm)':15,	 'PreSumB (comm)':16,	 'PreSumB (plain)':17,	 'PreSumB (decomm)':18,	 'FinalSumA (comm)':19,	 'FinalSumA (plain)':20,	 'FinalSumA (decomm)':21,	 'FinalSumB (comm)':22,	 'FinalSumB (plain)':23,	 'FinalSumB (decomm)':24}
 
col_full_names = ['SN&VC (comm)',	 'SN&VC (plain)',	 'SN&VC (decomm)',	 'PCheck (comm)',	 'PCheck (plain)',	 'PCheck (decomm)',	 'PossVote (comm)',	 'PossVote (plain)',	 'PossVote (decomm)',	 'MarkVoted (comm)',	 'MarkVoted (plain)',	 'MarkVoted (decomm)',	 'PreSumA (comm)',	 'PreSumA (plain)',	 'PreSumA (decomm)',	 'PreSumB (comm)',	 'PreSumB (plain)',	 'PreSumB (decomm)',	 'FinalSumA (comm)',	 'FinalSumA (plain)',	 'FinalSumA (decomm)',	 'FinalSumB (comm)',	 'FinalSumB (plain)',	 'FinalSumB (decomm)']

def empty(request):
	return HttpResponse('Please specify the election ID.')





def index(request, eid = 0, tab = 0):
    try:
	e = Election.objects.get(EID=eid)
    except Election.DoesNotExist:
	return HttpResponse('The election ID is invalid!')
    if request.method == 'POST':
        response = HttpResponse(content_type="application/zip")  
        response['Content-Disposition'] = 'attachment; filename=FINER_ABB.zip'
        #empty zip
        return response
    

    else:
        Vtable = []
        #prepare ver. 1
	version = [1]
        table = []
        abb_list = e.abbinit_set.all()
        for entry in abb_list:
            enc1 = entry.enc1.split(',')
            enc2 = entry.enc1.split(',')
            elen = len(enc1)
            cipher1 = entry.cipher1.split(',')
            clen = len(cipher1)
            rowlen = clen/elen
            cipher2 = entry.cipher2.split(',')
            #fake aux column
            aux1 = entry.aux1.split(',')
            aux2 = entry.aux2.split(',')
            zeroone = entry.zeroone
            for i in range(elen):
                if i ==0:
                    s = entry.serial+" A"
                else:
                    s = ''
                temp = ",".join(cipher1[rowlen*i:rowlen*(i+1)])    
                table.append([{'bit':zeroone,'serial':s},{'enc':enc1[i],'code':""},{'cipher':temp},{'aux':aux1[i]},{'mark':""},{'rand':""},{}])
            for i in range(elen):
                if i ==0:
                    s = entry.serial+" B"
                else:
                    s = ''
                temp = ",".join(cipher1[rowlen*i:rowlen*(i+1)])     
                table.append([{'bit':zeroone,'serial':s},{'enc':enc2[i],'code':""},{'cipher':temp},{'aux':aux2[i]},{'mark':""},{'rand':""},{}])
        Vtable.append(table)
	if e.tally:# ver. 2
	    version.append(2)
	    table = []
            for entry in abb_list:
            	enc1 = entry.enc1.split(',')
            	enc2 = entry.enc1.split(',')
            	elen = len(enc1)
            	cipher1 = entry.cipher1.split(',')
            	clen = len(cipher1)
            	rowlen = clen/elen
            	cipher2 = entry.cipher2.split(',')
            	#fake aux column
            	aux1 = entry.aux1.split(',')
            	aux2 = entry.aux2.split(',')
		rand1 = entry.rand1.split(',')
		rand2 = entry.rand2.split(',')
		code1 = entry.codes1.split(',')
                code2 = entry.codes2.split(',')
		if entry.mark1:
		    mark1 = entry.mark1.split(',')
		else:
		    mark1 = [""]*elen
		if entry.mark2:
		    mark2 = entry.mark2.split(',')
		else:
                    mark2 = [""]*elen
            	zeroone = entry.zeroone
            	for i in range(elen):
                    if i ==0:
                    	s = entry.serial+" A"
                    else:
                    	s = ''
                    temp = ",".join(cipher1[rowlen*i:rowlen*(i+1)])
                    table.append([{'bit':zeroone,'serial':s},{'enc':enc1[i],'code':code1[i]},{'cipher':temp},{'aux':aux1[i]},{'mark':mark1[i]},{'rand':rand1[i]},{}])
                for i in range(elen):
                    if i ==0:
                        s = entry.serial+" B"
                    else:
                        s = ''
                    temp = ",".join(cipher1[rowlen*i:rowlen*(i+1)])
                    table.append([{'bit':zeroone,'serial':s},{'enc':enc2[i],'code':code2[i]},{'cipher':temp},{'aux':aux2[i]},{'mark':mark2[i]},{'rand':rand2[i]},{}])
            Vtable.append(table)
	#end of verion 2
        BigData={'Data':Vtable,'Ver':version} 
        return render_to_response('abb.html', {'election':e, 'BigData':BigData, 'col_names':col_names},  context_instance=RequestContext(request))         
     






def index_bak(request, eid = 0, tab = 0):
	try:
		e = Election.objects.get(EID=eid)
	except Election.DoesNotExist:
		return HttpResponse('The election ID is invalid!')
	if request.method == 'POST':#export
            flag_abb = False
            flag_vbb = False
            flag_rand = False
            flag_def = False
            #set checks
            if "abbCheck" in request.POST.keys():
                flag_abb = True
            if "randCheck" in request.POST.keys():
                flag_rand = True
            if "vbbCheck" in request.POST.keys():
                flag_vbb = True
            if "defCheck" in request.POST.keys():
                flag_def = True
            #zip everything    
            response = HttpResponse(content_type="application/zip")  
            response['Content-Disposition'] = 'attachment; filename=ABB.zip'
            z = zipfile.ZipFile(response,'w')   ## write zip to response
            aux = e.auxiliary_set.all()#at most one
            if len(aux) != 0:#has aux
                if flag_vbb and aux[0].vbb_data:#if vbb data exists
                    z.writestr("VBB_data.zip", aux[0].vbb_data.read())
                    z.writestr("Sig_vbbData.txt", aux[0].vbb_sig.read())
                if flag_rand and aux[0].randomnessA:#if randomness data exists
                    z.writestr("Randomness1.zip", aux[0].randomnessA.read())
                    z.writestr("Sig_Randomness1.txt", aux[0].rand_sigA.read())
		if flag_rand and aux[0].randomnessB:#if randomness data exists
                    z.writestr("Randomness2.zip", aux[0].randomnessB.read())
                    z.writestr("Sig_Randomness2.txt", aux[0].rand_sigB.read())
                if flag_def and aux[0].election_def:#if def data exists
                    z.writestr("Election_def.zip", aux[0].election_def.read())
                    z.writestr("Sig_electDef.txt", aux[0].def_sig.read())
                if flag_abb:#if abb data
                    #export csv and signature   
                    ulist = e.updateinfo_set.all()
                    for u in ulist:
                        z.writestr(u.file.name, u.file.read())
                        z.writestr(u.sig.name, u.sig.read())
            return response


        else:    
            BigData = []
            Adatalist = e.abbdata_set.all()
            Akeylist = e.abbkey_set.all()
            Aloglist = e.updateinfo_set.all()
            # obtain current table numbers
            table_list = Akeylist.values('table').distinct()
            tablenums = [x['table'] for x in table_list]
            tablenums.sort()
            if int(tab) in tablenums:
                tabnum = tab
            else:    
                tabnum = tablenums[0]   
            #for tabnum in tablenums:
            #obtain length
            lenlist = Adatalist.filter(table = tabnum).values('length').order_by('-length')
            length = lenlist[0]['length']
            #obtain all the versions
            verlist = Akeylist.filter(table = tabnum).values('version').distinct()
            ver = [x['version'] for x in verlist]
            ver.sort()
            Vtime = ver
            #obtain the update logs
            loglist = Aloglist.filter(table = tabnum).values('date').order_by('date')
            Vlog = [x['date'] for x in loglist]
            Vtable = []
            #for each version
            for j in ver:
                table = [] #table data = many rows
                # first row is key
                keylist = Akeylist.filter(table = tabnum,version__lt = j+1)
                data = [] #row data
                for i in range(1,9):
                    templist = keylist.filter(column = i).order_by('-version')
                    if len(templist) ==0:
                        data.append(Ctuple(False,'','',''))
                    else:
                    # non empty use latest version
                        if templist[0].plaintext:
                            data.append(Ctuple(True, templist[0].plaintext,templist[0].commitment,templist[0].decommitment))
                        else:
                            data.append(Ctuple(False,'',templist[0].commitment,''))
                table.append(data)
                #take all the column data
                datalist = Adatalist.filter(table = tabnum,version__lt = j+1)
                #8 different columns with c,p,d
                col_data = [[] for x in range(24)]
                for i in range(1,9):
                    templist = datalist.filter(column = i).order_by('-version')
                    col_data[3*(i-1)+2] = ['' for x in range(length)]
                    if len(templist) ==0:
                        col_data[3*(i-1)] = ['' for x in range(length)]
                        col_data[3*(i-1)+1] = ['' for x in range(length)]
                    else:
                        # non empty
                        if templist[0].ciphertext:
                            col_data[3*(i-1)] = templist[0].ciphertext.split(',')
                        else:
                            col_data[3*(i-1)] = ['' for x in range(length)]
                        if templist[0].plaintext:   
                            col_data[3*(i-1)+1] = templist[0].plaintext.split(',')
                        else:    
                            col_data[3*(i-1)+1] = ['' for x in range(length)]
                #prepare data    
                for l in range(length):
                    data = [] #row data
                    #for each column
                    for i in range(1,9):
                        if col_data[3*(i-1)+1][l] != '':
                            data.append(Ctuple(True,col_data[3*(i-1)+1][l],col_data[3*(i-1)][l],''))
                        else:
                            data.append(Ctuple(False,'',col_data[3*(i-1)][l],''))                                   
                    table.append(data)
                Vtable.append(table)	
            BigData.append(DataTriple(Vtable,Vtime,Vlog))
                    
            return render_to_response('abb.html', {'election':e, 'TableNum': tablenums, 'col_names':col_names, 'BigData': BigData, 'current':tabnum},  context_instance=RequestContext(request))         
                    

def handle_uploaded_file(e, zfile,reader,sig, t):
    Aabblist = e.abbdata_set.filter(table = t)
    #check current version
    verlist = Aabblist.order_by('-version').values('version').distinct()
    v = 1
    if len(verlist)>0:
        v = verlist[0]['version']+1 #latest version+1
    #update the table
    counter = 0
    datalist = ['' for x in range(9)] #first one is useless
    bitmap = [0 for x in range(9)] #first one is useless
    for row in reader:
        if counter ==2:
            # skip the first two rows
            # mapping is not implemented    
            #key row
            entries = row.split(',')
            for i in range(1,9):
                flag = 0
                q = AbbKey(table = t, version = v,column = i, election = e)
                c = entries[3*(i-1)].strip('"')#commitment
                p = entries[3*(i-1)+1].strip('"')#plaintext
                d = entries[3*(i-1)+2].strip('"')#decommitment
                if len(c)>0:
                    q.commitment = c
                    flag+=1
                if len(p)>0:
                    q.plaintext = p
                    flag+=1
                    #decrypting all the tables
                    ver_list = Aabblist.filter(column = i).values('version').distinct()
                    if len(ver_list) !=0:
                        abb_data = Aabblist.get(column = i, version = int(ver_list[0]['version']))
                        olddata = abb_data.ciphertext.split(',')
                        buffer = ''
                        for entry in olddata:
                            #decrypt and add to database
                            chunks = entry.split()
                            key = base64.b64decode(p)
                            IV = base64.b64decode(chunks[0])
                            C = base64.b64decode(chunks[1])
                            obj = AES.new(key, AES.MODE_CBC, IV)
                            m = obj.decrypt(C).rstrip('\x00')
                            # convert 0/1 to Yes/No
                            #if i == 3 and m == '1':
                            #    m = "Yes"
                            #if i == 3 and m == '0':
                            #    m = "No"
                            #convert 0/1 to Voted/Not voted
                            #if i == 4 and m == '1':
                            #    m = "Voted"
                            #if i == 4 and m == '0':
                            #    m = "Not voted"
                            if len(buffer) > 0:
                                buffer+=','
                            buffer+=m   
                        plain = AbbData(length = abb_data.length,ciphertext = abb_data.ciphertext, plaintext = buffer, table = t, version = v,column = i, election = e)
                        plain.save()
                if len(d)>0:
                    q.decommitment = d
                    flag+=1
                if flag>0:    
                    q.save()
        if counter > 2:
            #data rows
            entries = row.split(',')
            for i in range(1,9):
                temp = entries[3*(i-1)].strip('"') #cipher
                if len(temp)>0:
                    if bitmap[i] >0:
                        datalist[i]+=','
                    bitmap[i]+=1
                    datalist[i] += temp                        
        counter += 1
    #save everything
    for i in range(1,9):
        if bitmap[i]>0:
            new = AbbData(length = counter-3,ciphertext = datalist[i], table = t, version = v,column = i, election = e)
            new.save()
    return counter-1


@csrf_exempt
def upload(request, eid = 0):
    try:
	e = Election.objects.get(EID=eid)
    except Election.DoesNotExist:
	return HttpResponse('The election ID is invalid!')
    if request.method == 'POST':
        csvfile = request.POST['inputdata']
	reader = csvfile.splitlines()
	counter = -2
	serial = ""
	enc1 = ""
	enc2 = ""
	cipher1 = ""
	cipher2 = ""
	code1 = []
	code2 = []
	n = 0
	key = ""
	for temp in reader:
	    counter+=1
	    #first row n, k1
	    if counter ==-1:
		row = temp.split(',')
	        n = int(row[0])
		key = row[1]
	        new_r = Randomstate(election = e, notes = "k1",random = key)
	        new_r.save()
	    if counter%5 ==0:
		#serial key
		row = temp.split(',')
		serial = row[0]
		new_bba = Bba(election = e, serial = serial, key = row[1], n = n)
		new_bba.save()
	    if	counter%5 ==1:
		#enc1
		enc1 = temp
		row = temp.split(',')
		k = base64.b64decode(key)
		for item in row:
		    code1.append(decrypt(base64.b64decode(item),k))
            if  counter%5 ==2:
                #cipher1
                cipher1 = temp	
            if  counter%5 ==3:
                #enc2
                enc2 = temp    
                row = temp.split(',')
                k = base64.b64decode(key)
                for item in row:
                    code2.append(decrypt(base64.b64decode(item),k))
            if  counter > 0 and counter%5 ==4:
                #cipher2
                cipher2 = temp
		#random aux
		fake_aux = []
		fake_rand = []
		for i in range(n):
			fake_aux.append(base64.b64encode(os.urandom(16)))
			fake_rand.append(base64.b64encode(os.urandom(16)))
		temp1 = ",".join(fake_aux)
		temp2 = ",".join(fake_rand)
		new_abb = Abbinit(election = e, codes1 = ",".join(code1), codes2 = ",".join(code2), rand1 = temp2, rand2 = temp2 , aux1 = temp1, aux2 = temp1, zeroone = base64.b64encode(os.urandom(8)),serial = serial, enc1 = enc1, enc2 = enc2, cipher1 = cipher1, cipher2 = cipher2)
		new_abb.save()
		#clean var
		code1 = []
        	code2 = []
	return HttpResponse("Success")

    else:
        return render_to_response('404.html')


    
@csrf_exempt
def upload_bak(request, eid = 0):
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
        
        flag = 0
        if opfile == 'table':	#tables
            flag = 1    
            reader = datafile.splitlines()
            #populate BBA database handle CSV file myself
            table = reader[0].split(',')[0]
            counter = handle_uploaded_file(e, zfile, reader, sig, table)
            new_op.table = table
        new_op.save() # save the update log here, since I also table info 
        aux = e.auxiliary_set.all()#at most one
        if len(aux) == 0:#no aux
            new_aux = Auxiliary(election = e)
            new_aux.save()
            au = new_aux
        else:
            au = aux[0]    
        if opfile == 'random1':#first randomness
            flag = 1   
            au.randomnessA = zfile
            au.rand_sigA = sig
            au.save()
	elif opfile == 'random2':#second randomness
            flag = 1   
            au.randomnessB = zfile
            au.rand_sigB = sig
            au.save()
        elif opfile == 'vbb':#vbb data
            flag = 1   
            au.vbb_data = zfile
            au.vbb_sig = sig
            au.save()
        elif opfile == 'def': #election def
            flag = 1   
            au.election_def = zfile
            au.def_sig = sig
            au.save()
        if flag == 1:
            return HttpResponse('The data has been uploaded to ABB.')
        else:
            return HttpResponse('Sorry, the operation code is not recognized.')
        
    else:
        return render_to_response('404.html')


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


    
    
    

