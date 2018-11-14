from django.db import models
 
 
class ExceptionLog(models.Model):
    """
    Models any error occuring on the server.
    """
    timestamp = models.DateTimeField('Time Stamp')
    view = models.CharField('View', max_length=30)
    exceptionclass = models.CharField('Exception Class', max_length=60)
    message = models.CharField('Exception Message', max_length=100)
