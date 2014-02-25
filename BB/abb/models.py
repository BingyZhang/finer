from django.db import models
from vbb.models import Election

# Create your models here.

class Abb(models.Model):
    table = models.IntegerField(default=0)
    serial_codes = models.CharField(max_length=2048,null=True, blank=True)
    ballot_check = models.CharField(max_length=2048,null=True, blank=True)
    possible_votes = models.CharField(max_length=2048,null=True, blank=True)
    marked_as_voted = models.CharField(max_length=2048,null=True, blank=True)
    Cserial_codes = models.CharField(max_length=2048,null=True, blank=True)
    Cballot_check = models.CharField(max_length=2048,null=True, blank=True)
    Cpossible_votes = models.CharField(max_length=2048,null=True, blank=True)
    Cmarked_as_voted = models.CharField(max_length=2048,null=True, blank=True)
    Dserial_codes = models.CharField(max_length=2048,null=True, blank=True)
    Dballot_check = models.CharField(max_length=2048,null=True, blank=True)
    Dpossible_votes = models.CharField(max_length=2048,null=True, blank=True)
    election = models.ForeignKey(Election)
    Dmarked_as_voted = models.CharField(max_length=2048,null=True, blank=True)
    version = models.IntegerField(default=0)
##    class Meta:
##        ordering = ["table","-version"]
##    
    def __str__(self):
        return "Table "+str(self.table)+" Ver. "+ str(self.version)

class UpdateInfo(models.Model):    
    table = models.IntegerField(default=0)
    election = models.ForeignKey(Election)
    version = models.IntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True)
    csv = models.FileField(upload_to='Archives/csv_files')
    sig = models.FileField(upload_to='Archives/signatures')

##    class Meta:
##        ordering = ["table","-version"]
##        
    def __str__(self):
        return "Table "+str(self.table)+" Ver. "+ str(self.version)
