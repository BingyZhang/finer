from django.db import models
from vbb.models import Election

# Create your models here.

class Auxiliary(models.Model):
    election = models.ForeignKey(Election)
    randomnessA = models.FileField(upload_to='Archives', null=True, blank=True)
    rand_sigA = models.FileField(upload_to='Archives', null=True, blank=True)
    randomnessB = models.FileField(upload_to='Archives', null=True, blank=True)
    rand_sigB = models.FileField(upload_to='Archives', null=True, blank=True)
    vbb_sig = models.FileField(upload_to='Archives', null=True, blank=True)
    def_sig = models.FileField(upload_to='Archives', null=True, blank=True)
    vbb_data = models.FileField(upload_to='Archives',null=True, blank=True)
    election_def = models.FileField(upload_to='Archives',null=True, blank=True)

class AbbKey(models.Model):
    table = models.IntegerField(default=0)
    column = models.IntegerField(default=0)
    plaintext = models.CharField(max_length=2048,null=True, blank=True)
    commitment = models.CharField(max_length=2048,null=True, blank=True)
    decommitment = models.CharField(max_length=2048,null=True, blank=True)
    election = models.ForeignKey(Election)
    version = models.IntegerField(default=0)   
    def __str__(self):
        return "Table "+str(self.table)+" Ver. "+ str(self.version)
    
class AbbData(models.Model):
    table = models.IntegerField(default=0)
    column = models.IntegerField(default=0)
    length = models.IntegerField(default=0)
    ciphertext = models.TextField(null=True, blank=True)
    plaintext = models.TextField(null=True, blank=True)
    election = models.ForeignKey(Election)
    version = models.IntegerField(default=0)   
    def __str__(self):
        return "Table "+str(self.table)+" Ver. "+ str(self.version)    

class UpdateInfo(models.Model):
    table = models.IntegerField(null=True, blank=True)
    text = models.CharField(max_length=2048,null=True, blank=True)
    election = models.ForeignKey(Election)
    date = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='Archives/op_files',null=True, blank=True)
    sig = models.FileField(upload_to='Archives/signatures',null=True, blank=True)
    def __str__(self):
        return "Op: "+str(self.text)+" Date: "+ str(self.date)

class Abbinit(models.Model):
    election = models.ForeignKey(Election)
    serial = models.CharField(max_length=1024)
    codes1 = models.TextField(null=True, blank=True)
    enc1 = models.TextField(null=True, blank=True)
    codes2 = models.TextField(null=True, blank=True)
    enc2 = models.TextField(null=True, blank=True)
    cipher1 = models.TextField(null=True, blank=True)
    cipher2 = models.TextField(null=True, blank=True)
    aux = models.TextField(null=True, blank=True)
