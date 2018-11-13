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

#for saving edited files to model
#https://stackoverflow.com/questions/32945292/how-to-save-pillow-image-object-to-django-imagefield/45907694
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from io import StringIO
from django.core.files.base import ContentFile, File
from PIL import Image, ImageOps, ImageEnhance

import os
import datetime
import pdb

#saving thumbnails
from django.db.models.signals import post_save
from django.dispatch import receiver

#saving img from url
import requests
from io import BytesIO
from urllib.request import urlopen
from tempfile import NamedTemporaryFile

# Create your models here.
#
#
def get_upload_path(cls, filename):
    return cls.__class__.__name__ + "/" + filename

class UserUploadedImage(models.Model):
    """images that are uploaded by a user, resized, and combined to make final image"""
    image = models.ImageField(upload_to=get_upload_path, null=True)
    thumbnail = models.ImageField(upload_to="thumbnails", null=True)
    date_uploaded = models.DateField(auto_now_add=True, blank=True, null=True)
    url = models.URLField(max_length=2000, blank=True, null=True)
    def save(self, image_size=(1000,1000), thumbnail_size=(100,100), *args, **kwargs):
        super(UserUploadedImage, self).save(*args, **kwargs)
        if not self.id:
            return
        if self.url and not self.image:
            img_temp = NamedTemporaryFile(delete = True)
            img_temp.write(urlopen(self.url).read())
            img_temp.flush()
            self.image.save("test_thing.jpg", File(img_temp), save=False)
        if self.image:
            image_filename = str(self.image.path)
            image = Image.open(image_filename)
            #resize the fullsize image
            image_width = self.image.width
            image_height = self.image.height
            new_width = image_size[0]
            new_height = image_size[1]
            if (image_width < image_height):
                new_height = image_size[0]
                new_width = int(image_size[1] * image_height / image_width)
            elif (image_height < image_width):
                new_width = image_size[1]
                new_height = int(image_size[0] * image_height / image_width)
            image = image.resize((new_width, new_height), Image.ANTIALIAS)
            image.save(image_filename)

            #make a separate thumbnail
            buffer = BytesIO()
            image = Image.open(self.image.path)
            image = ImageOps.fit(image, thumbnail_size, Image.ANTIALIAS)
            image.save(fp=buffer, format='PNG')
            image.seek(0)
            self.thumbnail.save(self.image.name,
                           ContentFile(buffer.getvalue()), save=False)
            image.close()
            super(UserUploadedImage, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.image:
            os.remove(os.path.join(settings.MEDIA_ROOT, self.image.name))
        if self.thumbnail:
            os.remove(os.path.join(settings.MEDIA_ROOT, self.thumbnail.name))
        super(UserUploadedImage,self).delete(*args,**kwargs)


class MoonTemplate(UserUploadedImage):
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
    percent_illuminated = models.IntegerField(default = 50)

    def __str__(self):
        return str(self.percent_illuminated)

class SelfieImage(UserUploadedImage):
    """docstring for SelfieImage"""
    media_id = models.CharField(default="", max_length=1000, blank = True, null = True)
    user_id = models.CharField(default="", max_length=1000, blank=True, null=True)
    username = models.CharField(default="", max_length=50, blank=True, null=True)
    used = models.BooleanField(default=False)
    instagram_post_url = models.URLField(max_length=1000, blank=True, null=True)
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
    def process_image_files(self, name=None, background_alpha=200, foreground_alpha=200):
        buffer = BytesIO()
        if self.selfie:
            selfie = Image.open(self.selfie.image)
            moon_shaped_selfie = Image.open(self.selfie.image)
        else:
            selfie = Image.new('RGB', (1000,1000), 'black')
            moon_shaped_selfie = Image.new('RGB', (1000,1000), 'black')
        selfie = ImageOps.fit(selfie, (1000, 1000), Image.ANTIALIAS)
        moon_shaped_selfie = ImageOps.fit(moon_shaped_selfie, (1000,1000), Image.ANTIALIAS)
        if self.moon:
            moon_mask = Image.open(self.moon.image, 'r')
            moon_mask_transparent = Image.open(self.moon.image, 'r')
        else:
            moon_mask = Image.new('RGB', (1000,1000), 'black')
            moon_mask_transparent = Image.new('RGB', (1000,1000), 'black')
        moon_mask = moon_mask.convert("L")
        moon_mask_transparent = moon_mask_transparent.point(lambda i: min(i * 25, foreground_alpha))
        moon_mask_transparent = moon_mask_transparent.convert("L")

        if self.background:
            background = Image.open(self.background.image, 'r')
            background = ImageOps.fit(background, (1000,1000), Image.ANTIALIAS)
        else:
            background= Image.new('RGB',(1000,1000),'black')

        if self.foreground:
            moon_shaped_foreground = Image.open(self.foreground.image)
            moon_shaped_foreground = ImageOps.fit(moon_shaped_foreground, (1000,1000), Image.ANTIALIAS)
        else:
            moon_shaped_foreground = Image.new('RGB', (1000,1000), 'black')
        if self.background_inverted:
            background = invert_image(background)
        if self.foreground_inverted:
            moon_shaped_foreground = invert_image(moon_shaped_foreground)
        moon_shaped_selfie.putalpha(moon_mask)
        background_mask = background.point(lambda i: background_alpha)
        background_mask = background_mask.convert("L")

        moon_shaped_foreground.putalpha(moon_mask_transparent)

        #put transparent background over selfie
        selfie.paste(background, (0,0), mask=background_mask)

        #reput moon shaped selfie on top of transparent background
        selfie.paste(moon_shaped_selfie, (0,0), mask=moon_shaped_selfie)

        #put foreground over moon
        selfie.paste(moon_shaped_foreground, (0,0), mask=moon_mask_transparent)
        selfie.save(fp=buffer, format='PNG')
        pillow_image = ContentFile(buffer.getvalue())
        self.image.save('temp.jpg', InMemoryUploadedFile(
                    pillow_image,
                    None,
                    'temp.jpg',
                    'image/jpeg',
                    pillow_image.tell,
                    None
                ))


class TempSavedImage(UserUploadedImage):
    selfie_media_id = models.CharField(default="", max_length=60)
    selfie_user_id = models.CharField(default="", max_length=60)
    background_user = models.CharField(max_length=60, null=True, blank=True)
    background_description = models.CharField(default=":)", max_length=60)
    foreground_user = models.CharField(max_length=60, null=True, blank=True)
    foreground_description = models.CharField(default=":)", max_length=60)
    percent_illuminated = models.IntegerField(default="0")
    moonstate_description = models.CharField(max_length=200,default="", null=True, blank=True)

    def __str__(self):
        return str(self.image)
    def make_image(self, previewImg):
        buffer = BytesIO()
        previewImageFile = Image.open(previewImg.image)
        previewImageFile.convert("RGB")
        previewImageFile.save(fp=buffer, format='JPEG')
        contentFile = ContentFile(buffer.getvalue())
        collageFileName = "{}_{}_{}.jpg".format(
               previewImg.moon.percent_illuminated,
               previewImg.selfie.username,
               datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
           )
        self.image.save(collageFileName, InMemoryUploadedFile(
           contentFile,
           None,
           collageFileName,
           'image/jpeg',
           contentFile.tell,
           None
        ))

    @classmethod
    def create(cls, previewImg):
        selfie_user_id = previewImg.selfie.user_id
        selfie_media_id = previewImg.selfie.media_id
        moonstate_description = "{}, {}% illuminated".format(
                previewImg.moon.moon_state,
                previewImg.moon.percent_illuminated,
            )
        if previewImg.foreground:
            foreground_description = previewImg.foreground.description
        else:
            foreground_description = "nothing"
        if previewImg.background:
            background_description = previewImg.background.description
        else:
            background_description = "nothing"
        return cls(
            image = None,
            selfie_user_id = previewImg.selfie.user_id,
            selfie_media_id = previewImg.selfie.media_id,
            background_user = previewImg.background.username,
            foreground_user = previewImg.foreground.username,
            background_description = previewImg.background.description,
            foreground_description = previewImg.foreground.description,
            percent_illuminated = previewImg.moon.percent_illuminated
        )

#image processing
#helpful link https://simpleisbetterthancomplex.com/tutorial/2017/03/02/how-to-crop-images-in-a-django-application.html
#how to add mask: https://stackoverflow.com/questions/38627870/how-to-paste-a-png-image-with-transparency-to-another-image-in-pil-without-white/38629258

#A mask is an Image object where the alpha value is significant, but its green, red, and blue values are ignored.

#transparency masks: http://www.leancrew.com/all-this/2013/11/transparency-with-pil/


#https://stackoverflow.com/questions/42045362/change-contrast-of-image-in-pil
def change_contrast(img, level):
    factor = (259 * (level + 255)) / (255 * (259 - level))
    def contrast(c):
        return 128 + factor * (c - 128)
    return img.point(contrast)

def invert_image(img):
    return ImageOps.invert(img)
