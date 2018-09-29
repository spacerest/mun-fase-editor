from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from editor.storage import OverwriteStorage
from django.db.models.signals import post_delete
import os
from munfase import settings
from PIL import Image, ImageOps, ImageEnhance
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile

# Create your models here.

class MoonTemplate(models.Model):
    """docstring for Moon"""
    STATE_CHOICES = (
        ("waxing_crescent", "waxing_crescent"),
        ("first_quarter", "first quarter"),
        ("waxing_gibbous", "waxing gibbous"),
        ("full_moon", "full moon"),
        ("waning_gibbous", "waning gibbous"),
        ("last_quarter", "last quarter"),
        ("waning_crescent", "waning crescent"),
        ("new_moon", "new moon")
    )
    moon_state = models.CharField(
        max_length = 50,
        choices = STATE_CHOICES,
        default = "new_moon"
    )
    image = models.ImageField(upload_to="moon")
    thumbnail = models.ImageField(upload_to="thumbnails", null=True, blank=True)
    percent_illuminated = models.IntegerField(default = 50)

    def __str__(self):
        return str(self.percent_illuminated)
    def save(self, image_size=(1000,1000), thumbnail_size=(100,100)):
        super(MoonTemplate, self).save()
        if not self.id:
            return
        image_width = self.image.width
        image_height = self.image.height
        new_width = image_size[0]
        new_height = image_size[1]
        image_filename = str(self.image.path)
        image = Image.open(image_filename)
        if (image_width < image_height):
            new_width = image_size[0]
            new_height = int(image_size[1] * image_height / image_width)
        elif (image_height < image_width):
            new_height = image_size[1]
            new_width = int(image_size[0] * image_height / image_width)
        image = image.resize((new_width, new_height), Image.ANTIALIAS)
        image.save(image_filename)
        if not self.thumbnail:
            buffer = BytesIO()
            image = Image.open(self.image.path)
            image = ImageOps.fit(image, thumbnail_size, Image.ANTIALIAS)
            image.save(fp=buffer, format='PNG')
            image.seek(0)
            self.thumbnail.save(self.image.name,
                           ContentFile(buffer.getvalue()), save=True)
            image.close()
        return False

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
    def save(self, image_size=(1000,1000), thumbnail_size=(100,100)):
        super(UserUploadedImage, self).save()
        if not self.id:
            return
        image_width = self.image.width
        image_height = self.image.height
        new_width = image_size[0]
        new_height = image_size[1]
        image_filename = str(self.image.path)
        image = Image.open(image_filename)

        if (image_width < image_height):
            new_width = image_size[0]
            new_height = int(image_size[1] * image_height / image_width)
        elif (image_height < image_width):
            new_height = image_size[1]
            new_width = int(image_size[0] * image_height / image_width)

        image = image.resize((new_width, new_height), Image.ANTIALIAS)
        image.save(image_filename)

        if not self.thumbnail:
            buffer = BytesIO()
            image = Image.open(self.image.path)
            image = ImageOps.fit(image, thumbnail_size, Image.ANTIALIAS)
            image.save(fp=buffer, format='PNG')
            image.seek(0)

            self.thumbnail.save(self.image.name,
                           ContentFile(buffer.getvalue()), save=True)
            image.close()
        return False

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
    moon = models.ForeignKey(MoonTemplate, blank=True, null=True, on_delete=models.CASCADE)
    foreground = models.ForeignKey(TextureImage, blank=True, null=True, on_delete=models.CASCADE, related_name='foreground')
    background = models.ForeignKey(TextureImage, blank=True, null=True, on_delete=models.CASCADE, related_name='background')

    #caption
    #image transformation settings
    selfie_contrast = models.IntegerField(default=1, blank=True, null=True)
    foreground_transparency = models.IntegerField(default=125)
    background_transparency = models.IntegerField(default=125)
    foreground_inverted = models.BooleanField(default=False)
    background_inverted = models.BooleanField(default=False)


class SavedImage(models.Model):
    image = models.ImageField(upload_to="final", null=True, blank=True)
    selfie_user = models.CharField(default="@mun_fases", max_length=60)
    background_user = models.CharField(max_length=60, null=True, blank=True)
    percent_illuminated = models.IntegerField(null=True, blank=True)
    caption = models.TextField(default=";)", max_length = 400)
    date_created = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    #caption
    ZODIAC_OPTIONS = (
        ("♒", "aquarius" ),
        ("♓", "pisces"),
        ("♈","aries"),
        ("♉","taurus"),
        ("♊","gemini"),
        ("♋","cancer"),
        ("♌","leo"),
        ("♍","virgo"),
        ("♎","libra"),
        ("♏","scorpio"),
        ("♐","sagittarius"),
        ("♑","capricorn"),
    )
    first_emoji = models.CharField(max_length = 50, choices = ZODIAC_OPTIONS, default = "aquarius", null=True, blank=True)
    second_emoji = models.CharField(max_length = 50, choices = ZODIAC_OPTIONS, default = "aquarius", null=True, blank=True)
    moon_state_description = models.CharField(max_length = 100, default="", null=True, blank=True)
    selfie_username = models.CharField(max_length = 100, default = "", null=True, blank=True)
    foreground_description = models.CharField(max_length = 100, default = "", null=True, blank=True)
    background_description = models.CharField(max_length = 100, default = "", null=True, blank=True)

    def __str__(self):
        return str(self.image)
    @classmethod
    def create(cls, previewImg):
        return cls(
            image = previewImg.image,
            selfie_username = previewImg.selfie.username,
            percent_illuminated = previewImg.moon.percent_illuminated,
            moon_state_description = "{}% {}".format(
                previewImg.moon.percent_illuminated,
                previewImg.moon.moon_state
            ),
            foreground_description = previewImg.foreground.description,
            background_description = previewImg.background.description
        )
