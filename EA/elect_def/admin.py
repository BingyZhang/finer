from django.contrib import admin
from elect_def.models import Election, Choice, Tokens


# Register your models here.

class ElectionAdmin(admin.ModelAdmin):
    list_display = ('question', 'start', 'end')
    list_filter = ['question']
    search_fields = ['question']

class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['text']
    list_filter = ['election']
    search_fields = ['text']

class TokensAdmin(admin.ModelAdmin):
    list_display = ['token','email']
    list_filter = ['election']
    search_fields = ['email']

admin.site.register(Election, ElectionAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Tokens, TokensAdmin)

