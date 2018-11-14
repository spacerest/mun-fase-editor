from django.contrib import admin
from debug.models import ExceptionLog
 
 
class ExceptionLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'view', 'exceptionclass',
                    'message')
    list_filter = ('view', 'timestamp')
    search_fields = ['message', 'exceptionclass', 'view']
 
admin.site.register(ExceptionLog, ExceptionLogAdmin)
