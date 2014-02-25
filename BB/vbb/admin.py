from django.contrib import admin
from vbb.models import Election, Choice, Vbb, Dballot, Bba


# Register your models here.
class VbbAdmin(admin.ModelAdmin):
    list_display = ('serial', 'votecode','date')
    list_filter = ['serial']
    search_fields = ['serial']

class DballotAdmin(admin.ModelAdmin):
    list_display = ('serial', 'code', 'value')
    list_filter = ['serial']
    search_fields = ['serial']

class ElectionAdmin(admin.ModelAdmin):
    list_display = ('question', 'start', 'end')
    list_filter = ['question']
    search_fields = ['question']

class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['text']
    list_filter = ['text']
    search_fields = ['text']

class BbaAdmin(admin.ModelAdmin):
    list_display = ['serial','code']
    list_filter = ['serial']
    search_fields = ['serial']

admin.site.register(Vbb, VbbAdmin)
admin.site.register(Bba, BbaAdmin)
admin.site.register(Election, ElectionAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Dballot, DballotAdmin)
