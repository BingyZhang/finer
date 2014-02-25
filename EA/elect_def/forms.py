import datetime
from django import forms
from django.forms.extras.widgets import SelectDateWidget


class DefForm(forms.Form):
    DataField = forms.DateField(widget=SelectDateWidget)
 
