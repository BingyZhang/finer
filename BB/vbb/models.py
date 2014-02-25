from django.db import models
from django.utils import timezone

# Create your models here.


class Election(models.Model):    
	start = models.DateTimeField()
	end = models.DateTimeField()
	question = models.CharField(max_length=4096)
	EID = models.CharField(max_length=512)
	tally = models.BooleanField(default=False)
	request = models.BooleanField(default=False)
	total = models.IntegerField(default=0)
	def was_started(self):
		return timezone.now() >= self.start 

	def was_ended(self):
		return timezone.now() >= self.end

	def __str__(self):
		return str(self.question)

class Choice(models.Model):    
	election = models.ForeignKey(Election)
	text = models.CharField(max_length=1024)
	votes = models.IntegerField(default=0)
	def __str__(self):
		return str(self.text)

class Vbb(models.Model):   
	election = models.ForeignKey(Election) 
	serial = models.CharField(max_length=1024)
	votecode = models.CharField(max_length=1024)
	date = models.DateTimeField(auto_now_add=True)
	def __str__(self):
		return "Serial#: "+str(self.serial)+" Code: "+ str(self.votecode)

class Dballot(models.Model):    
	vbb = models.ForeignKey(Vbb)
	serial = models.CharField(max_length=1024,null=True, blank=True)
	code = models.CharField(max_length=1024)
	value = models.CharField(max_length=2048,null=True, blank=True)
	def __str__(self):
		return " Code: "+ str(self.code)

class Bba(models.Model):
	election = models.ForeignKey(Election)
	serial = models.CharField(max_length=1024)
	voted = models.BooleanField(default=False)
	code = models.CharField(max_length=1024)
	def __str__(self):
		return "Serial#: "+str(self.serial)+" Code: "+ str(self.code)
