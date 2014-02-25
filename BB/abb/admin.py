from django.contrib import admin
from abb.models import Abb, UpdateInfo


# Register your models here.
class AbbAdmin(admin.ModelAdmin):
    list_display = ('table', 'version','serial_codes', 'ballot_check', 'possible_votes', 'marked_as_voted')
    list_filter = ['table']
    search_fields = ['table']

class UpdateInfoAdmin(admin.ModelAdmin):
    list_display = ('table', 'version', 'date')
    list_filter = ['table']
    search_fields = ['table']

admin.site.register(Abb, AbbAdmin)
admin.site.register(UpdateInfo, UpdateInfoAdmin)
