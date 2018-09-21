from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(MoonImage)
admin.site.register(TextureImage)
admin.site.register(SelfieImage)
admin.site.register(PreviewImage)

