from django.db import models
from django.utils import timezone
# Create your models here.


class Election(models.Model):    
	start = models.DateTimeField()
	end = models.DateTimeField()
	prepared = models.BooleanField(default=False)
	question = models.CharField(max_length=4096)
	EID = models.CharField(max_length=512)
	creator = models.CharField(max_length=256)
	c_email = models.CharField(max_length=512)
	total = models.IntegerField(default=0)
	Paffiliation = models.CharField(max_length=1024)
	title = models.CharField(max_length=1024)
	Porg = models.CharField(max_length=4096)
	def was_started(self):
		return timezone.now() >= self.start 

	def was_ended(self):
		return timezone.now() >= self.end

	def __unicode__(self):
		return self.question

class Pdfballot(models.Model):
	election = models.ForeignKey(Election)
	token = models.CharField(max_length=1024)
	pdf = models.FileField(upload_to='Archives',null=True, blank=True)
	def __unicode__(self):
                return str(self.token)

class Choice(models.Model):    
	election = models.ForeignKey(Election)
	text = models.CharField(max_length=1024)
	votes = models.IntegerField(default=0)
	def __unicode__(self):
		return self.text

class Ballot(models.Model):
	election = models.ForeignKey(Election)
	serial = models.CharField(max_length=1024)
	used = models.BooleanField(default=False)
	key = models.CharField(max_length=1024)
	codes1 = models.TextField(null=True, blank=True)
	votes1 = models.TextField(null=True, blank=True)
	rec1 = models.TextField(null=True, blank=True)
	plain1 = models.TextField(null=True, blank=True)
	plain2 = models.TextField(null=True, blank=True)
	cipher1 = models.TextField(null=True, blank=True)
	codes2 = models.TextField(null=True, blank=True)
	votes2 = models.TextField(null=True, blank=True)
	cipher2 = models.TextField(null=True, blank=True)
	rec2 = models.TextField(null=True, blank=True)
	def __unicode__(self):
		return "Serial#: "+str(self.serial)

class Assignment(models.Model):
        election = models.ForeignKey(Election)
        vID = models.CharField(max_length=1024)
        serial = models.CharField(max_length=1024)
	#ballot = models.FileField(upload_to='Archives/Ballots',null=True, blank=True)
	#qr = models.FileField(upload_to='Archives/QRs',null=True, blank=True)
        def __unicode__(self):
                return str(self.vID)

class Tokens(models.Model):
        election = models.ForeignKey(Election)
        token = models.CharField(max_length=1024)
        email = models.CharField(max_length=1024)
        def __unicode__(self):
                return str(self.token)

class Randomstate(models.Model):
        election = models.ForeignKey(Election)
        notes = models.CharField(max_length=256)
        random = models.CharField(max_length=1024)
        def __unicode__(self):
                return str(self.notes)
