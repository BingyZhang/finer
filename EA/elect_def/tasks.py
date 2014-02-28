from __future__ import absolute_import

from celery import shared_task
from django.utils import timezone
from elect_def.models import Election, Ballot,Randomstate
import hashlib,hmac,base64,os,binascii,subprocess, cStringIO, csv, zipfile, requests
from Crypto.Cipher import AES
from Crypto import Random

BB_URL = "http://tal.di.uoa.gr/finer/abb/"

#the size of hamc and AES
RSIZE = 32
KSIZE = 16

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


@shared_task
def prepare_ballot(e, total, n):
    #print "test...creating ballot.."
    #create ballots
    for v in range(100,total+100):
        serial = str(v)
        key = os.urandom(RSIZE)
	skey = base64.b64encode(key)
        codes = ["",""]
        recs = ["",""]
	votes = ["",""]
	ciphers = ["",""]
        for ab in range(2):
	    p = subprocess.Popen(["sh","/var/www/finer/EC-ElGamal/GenPerm.sh", str(n)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	    output,err = p.communicate()
	    votes[ab] = output
	    #read from the disk file for ciphers
	    f = open('/var/www/finer/EC-ElGamal/EC_cipher.txt')
	    lines = f.readlines()
	    f.close()
	    flag = 0
	    i = 0
	    for enc in lines:
		i+=1
		if i >= 2:
		    if i%2 == 0:
			ciphers[ab]+=" "	
		    else: #" " and "," alternating
			ciphers[ab]+=","	
		ciphers[ab]+=enc.strip()
	    for i in range(n):
    	        message = bytes(serial+str(ab)+str(i)).encode('utf-8')
    	        c = hmac.new(key, message, digestmod=hashlib.sha256).digest()
	        c1 = long(binascii.hexlify(c[0:8]), 16) #convert 64 bit string to long
	        c1 &= 0x3fffffffffffffff # 64 --> 62 bits
	        sc1 = base36encode(c1)
	        r1 = long(binascii.hexlify(c[8:12]), 16) #convert 32 bit string to long
                r1 &= 0x7fffffff # 32 --> 31 bits
                sr1 = base36encode(r1)
                if i > 0:
		    codes[ab]+=","
		    recs[ab]+=","
	        codes[ab]+=addbars(sc1)
	        recs[ab]+=sr1
	new_b = Ballot(election = e, serial = serial, key = skey, votes1 = votes[0],votes2 = votes[1],cipher1 = ciphers[0],cipher2 = ciphers[1], codes1 = codes[0],codes2 = codes[1],rec1 = recs[0],rec2 = recs[1])
        new_b.save()
    #send ABB CSV data
    #random key for column 1
    k1 = os.urandom(KSIZE)
    sk1 = base64.b64encode(k1)
    new_r = Randomstate(election = e, notes = "k1",random = sk1)
    new_r.save()
    #create csv file and encrypt the codes
    output = cStringIO.StringIO() ## temp output file
    writer = csv.writer(output, dialect='excel')
    #first row n, k1.
    writer.writerow([str(n),sk1])
    #get all the ballots
    all_ballots = Ballot.objects.filter(election = e)
    for each in all_ballots:
	writer.writerow([each.serial,each.key])#second row serial , key.
	#encrypt codes
	temp_list = each.codes1.split(',')
	enc_list = []
	for temp in temp_list:
	    enc_list.append(base64.b64encode(encrypt(temp,k1,key_size=128)))	
	writer.writerow(enc_list)
	#write cipher
	temp_list = each.cipher1.split(',')
	writer.writerow(temp_list)
	#do the same for ballot 2
        #encrypt codes
        temp_list = each.codes2.split(',')
        enc_list = []
        for temp in temp_list:
            enc_list.append(base64.b64encode(encrypt(temp,k1,key_size=128)))
        writer.writerow(enc_list)
        #write cipher
        temp_list = each.cipher2.split(',')
        writer.writerow(temp_list)
    #post
    reply = requests.post(BB_URL+e.EID+'/upload/',data = {'inputdata':output.getvalue()})
    return reply






