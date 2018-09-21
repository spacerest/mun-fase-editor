from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from editor.storage import OverwriteStorage

# Create your models here.

class MoonImage(models.Model):
    """docstring for Moon"""
    image = models.ImageField(upload_to="moon")
    percent_illuminated = models.IntegerField(default = 50)
    def __str__(self):
        return str(self.percent_illuminated)

class SelfieImage(models.Model):
    """docstring for SelfieImage"""
    image = models.ImageField(upload_to="selfie")
    username = models.CharField(default="", max_length=50)
    date_uploaded = models.DateField(auto_now_add=True)
    used = models.BooleanField(default=False)
    def __str__(self):
        return self.username

class TextureImage(models.Model):
    """docstring for TextureImage"""
    image = models.ImageField(upload_to="texture")
    username = models.CharField(default="none", max_length=50)
    date_uploaded = models.DateField(auto_now_add=True)
    used = models.BooleanField(default=False)
    description = models.TextField(max_length = 400, null=True, blank=True)
    def __str__(self):
        return self.username

class PreviewImage(models.Model):
    image = models.ImageField(upload_to="preview", editable=True, null=True, blank=True, storage=OverwriteStorage())
    selfie = models.ForeignKey(SelfieImage, blank=True, null=True, on_delete=models.CASCADE)
    moon = models.ForeignKey(MoonImage, blank=True, null=True, on_delete=models.CASCADE)
    foreground = models.ForeignKey(TextureImage, blank=True, null=True, on_delete=models.CASCADE, related_name='foreground')
    background = models.ForeignKey(TextureImage, blank=True, null=True, on_delete=models.CASCADE, related_name='background')

class SavedImage(models.Model):
    image = models.ImageField(upload_to="final")
    selfie_user = models.CharField(default="@mun_fases", max_length=60)
    background_user = models.CharField(max_length=60, null=True, blank=True)
    background_description = models.CharField(default=":)", max_length=60)
    foreground_user = models.CharField(max_length=60, null=True, blank=True)
    foreground_description = models.CharField(default=":)", max_length=60)
    percent_illuminated = models.IntegerField()

    def __str__(self):
        return self.selfie_user + self.percent_illuminated