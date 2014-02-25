from django.contrib import admin
from elect_def.models import Election, Choice


# Register your models here.

class ElectionAdmin(admin.ModelAdmin):
    list_display = ('question', 'start', 'end')
    list_filter = ['question']
    search_fields = ['question']

class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['text']
    list_filter = ['text']
    search_fields = ['text']

admin.site.register(Election, ElectionAdmin)
admin.site.register(Choice, ChoiceAdmin)


