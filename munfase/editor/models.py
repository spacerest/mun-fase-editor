from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from editor.storage import OverwriteStorage
from django.db.models.signals import post_delete
from .utils.utilities import file_cleanup
import os
from munfase import settings

# Create your models here.

class MoonTemplate(models.Model):
    """docstring for Moon"""
    image = models.ImageField(upload_to="moon")
    thumbnail = models.ImageField(upload_to="thumbnails", null=True, blank=True)
    percent_illuminated = models.IntegerField(default = 50)
    def __str__(self):
        return str(self.percent_illuminated)
    def delete(self, *args, **kwargs):
        if self.image:
            os.remove(os.path.join(settings.MEDIA_ROOT, self.image.name))
        if self.thumbnail:
            os.remove(os.path.join(settings.MEDIA_ROOT, self.thumbnail.name))
        super(MoonTemplate,self).delete(*args,**kwargs)

def get_upload_path(cls, filename):
    return cls.__class__.__name__ + "/" + filename

class UserUploadedImage(models.Model):
    """images that are uploaded by a user, resized, and combined to make final image"""
    image = models.ImageField(upload_to=get_upload_path)
    thumbnail = models.ImageField(upload_to="thumbnails", null=True, blank=True)
    date_uploaded = models.DateField(auto_now_add=True)
    def delete(self, *args, **kwargs):
        if self.image:
            os.remove(os.path.join(settings.MEDIA_ROOT, self.image.name))
        if self.thumbnail:
            os.remove(os.path.join(settings.MEDIA_ROOT, self.thumbnail.name))
        super(UserUploadedImage,self).delete(*args,**kwargs)

class SelfieImage(UserUploadedImage):
    """docstring for SelfieImage"""
    username = models.CharField(default="", max_length=50)
    used = models.BooleanField(default=False)
    def __str__(self):
        return self.username

class TextureImage(UserUploadedImage):
    """docstring for TextureImage"""
    username = models.CharField(default="none", max_length=50)
    used = models.BooleanField(default=False)
    description = models.TextField(max_length = 400, null=True, blank=True)
    def __str__(self):
        return self.username

class PreviewImage(models.Model):
    image = models.ImageField(upload_to="preview", editable=True, null=True, blank=True, storage=OverwriteStorage())
    selfie = models.ForeignKey(SelfieImage, blank=True, null=True, on_delete=models.CASCADE)
    selfie_contrast = models.IntegerField(default=1, blank=True, null=True)
    moon = models.ForeignKey(MoonTemplate, blank=True, null=True, on_delete=models.CASCADE)
    foreground = models.ForeignKey(TextureImage, blank=True, null=True, on_delete=models.CASCADE, related_name='foreground')
    background = models.ForeignKey(TextureImage, blank=True, null=True, on_delete=models.CASCADE, related_name='background')
    foreground_transparency = models.IntegerField(default=255)
    background_transparency = models.IntegerField(default=255)
    foreground_inverted = models.BooleanField(default=False)
    background_inverted = models.BooleanField(default=False)

class SavedImage(models.Model):
    image = models.ImageField(upload_to="final")
    selfie_user = models.CharField(default="@mun_fases", max_length=60)
    background_user = models.CharField(max_length=60, null=True, blank=True)
    background_description = models.CharField(default=":)", max_length=60)
    foreground_user = models.CharField(max_length=60, null=True, blank=True)
    foreground_description = models.CharField(default=":)", max_length=60)
    percent_illuminated = models.IntegerField()
    def __str__(self):
        return str(self.image)
    @classmethod
    def create(cls, previewImg):
        return cls(
            image = previewImg.image,
            selfie_user = previewImg.selfie.username,
            background_user = previewImg.background.username,
            foreground_user = previewImg.foreground.username,
            background_description = previewImg.background.description,
            foreground_description = previewImg.foreground.description,
            percent_illuminated = previewImg.moon.percent_illuminated
        )
