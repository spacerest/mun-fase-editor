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

#data uri
import base64

# Create your models here.
#
#
def get_upload_path(cls, filename):
    return cls.__class__.__name__ + "/" + filename

class CurrentMoonPhase(models.Model):
    """the current moon phase, based on date and a query to a website"""
    images_website = models.URLField(max_length=2000)
    image = models.ImageField(upload_to = get_upload_path, null = True, blank = True)
    current_date = models.DateField()
    percent_illumination = models.IntegerField(default=0)
    mask = models.ImageField(upload_to = get_upload_path, null = True, blank = True)



class UserUploadedImage(models.Model):
    """images that are uploaded by a user, resized, and combined to make final image"""
    image = models.ImageField(upload_to=get_upload_path, null=True, blank=True)
    thumbnail = models.ImageField(upload_to="thumbnails", null=True)
    date_uploaded = models.DateField(auto_now_add=True, blank=True, null=True)
    source_url = models.URLField(max_length=2000, blank=True, null=True)
    def get_type(self):
        return self.__name__
    def save(self, image_size=(1000,1000), thumbnail_size=(100,100), *args, **kwargs):
        super(UserUploadedImage, self).save(*args, **kwargs)
        if not self.id:
            return
        if self.source_url and not self.image:
            image_filename = "{}.jpg".format(
               datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
           )
            img_temp = NamedTemporaryFile(delete = True)
            img_temp.write(urlopen(self.source_url).read())
            img_temp.flush()
            self.image.save(image_filename, File(img_temp), save=False)
        if self.image:
            image_filename = str(self.image.path)
            image = Image.open(image_filename)
            #resize the fullsize image
            image_width = self.image.width
            image_height = self.image.height
            new_width = image_size[0]
            new_height = image_size[1]
            if (image_width <= image_height):
                ratio = image_size[0] / image_width
            elif (image_height <= image_width):
                ratio = image_size[1] / image_height
            new_width = int(image_width * ratio)
            new_height = int(image_height * ratio)
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
        ("waxing crescent", "waxing crescent"),
        ("first quarter", "first quarter"),
        ("waxing gibbous", "waxing gibbous"),
        ("full moon", "full moon"),
        ("waning gibbous", "waning gibbous"),
        ("last quarter", "last quarter"),
        ("waning crescent", "waning crescent"),
        ("new moon", "new moon")
    )
    moon_state = models.CharField(
        max_length = 50,
        choices = STATE_CHOICES,
        default = "new_moon"
    )
    percent_illuminated = models.IntegerField(default = 50)
    hashtags = models.CharField(max_length=1000, blank=True, null=True)
    def __str__(self):
        return str(self.percent_illuminated)

class InstagramUser(models.Model):
    user_id = models.CharField(default="", max_length=50)
    username = models.CharField(default="", max_length=50, null=True, blank=True)
    def __str__(self):
        return str(self.user_id)

class SelfieImage(UserUploadedImage):
    """docstring for SelfieImage"""
    media_id = models.CharField(default="", max_length=1000, blank = True, null = True)
    username = models.CharField(default="", max_length=50, blank=True, null=True)
    used = models.BooleanField(default=False)
    instagram_user = models.ForeignKey(InstagramUser, null=True, blank=True, on_delete = models.CASCADE)
    instagram_post_url = models.URLField(max_length=1000, blank=True, null=True)
    hashtags = models.CharField(max_length=1000, blank=True, null=True)
    def save(self, image_size=(1000,1000), thumbnail_size=(100,100), *args, **kwargs):
        super(UserUploadedImage, self).save(*args, **kwargs)
        if not self.id:
            return
        if self.source_url and not self.image:
            image_filename = "{}.jpg".format(
               datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
           )
            img_temp = NamedTemporaryFile(delete = True)
            img_temp.write(urlopen(self.source_url).read())
            img_temp.flush()
            self.image.save(image_filename, File(img_temp), save=False)
        if self.image:
            image_filename = str(self.image.path)
            image = Image.open(image_filename)
            white_image = Image.new('RGB', (1000,1000), 'white')
            #resize the fullsize image
            image_width = self.image.width
            image_height = self.image.height
            new_width = image_size[0]
            new_height = image_size[1]
            if (image_width <= image_height):
                ratio = image_size[1] / image_height
            elif (image_height <= image_width):
                ratio = image_size[0] / image_width
            new_width = int(image_width * ratio)
            new_height = int(image_height * ratio)
            image = image.resize((new_width, new_height), Image.ANTIALIAS)
            white_image.paste(image, (int((image_size[0] - new_width)/2),int((image_size[1] - new_height)/2)))
            white_image.save(image_filename)

            #make a separate thumbnail
            buffer = BytesIO()
            image = Image.open(self.image.path)
            image = ImageOps.fit(image, thumbnail_size, Image.ANTIALIAS)
            image.save(fp=buffer, format='PNG')
            image.seek(0)
            self.thumbnail.save(self.image.name,
                           ContentFile(buffer.getvalue()), save=False)

            #make a data uri
            if (image.width <= image.height):
                ratio = 50.0 / image.width
            elif (image.height <= image.width):
                ratio = 50.0 / image.height
            new_width = int(image.width * ratio)
            new_height = int(image.height * ratio)
            image = image.resize((new_width,new_height), Image.ANTIALIAS)
            buffered = BytesIO()
            image.save(fp=buffered, format='PNG')
            im_data = buffered.getvalue()
            self.image_data_uri = 'data:image/png;base64,' + base64.b64encode(im_data).decode(encoding="utf-8", errors="strict")

            image.close()
            super(UserUploadedImage, self).save(*args, **kwargs)


    def __str__(self):
        if self.instagram_user:
            return self.instagram_user.username
        elif self.username:
            return self.username
        else:
            return "unknown username"

class TextureImage(UserUploadedImage):
    """docstring for TextureImage"""
    username = models.CharField(default="", max_length=50, blank=True, null=True)
    used = models.BooleanField(default=False)
    description = models.TextField(max_length = 400, null=True, blank=True)
    instagram_post_url = models.URLField(max_length=1000, blank=True, null=True)
    media_id = models.CharField(default="", max_length=1000, blank = True, null = True)
    instagram_user = models.ForeignKey(InstagramUser, null=True, blank=True, on_delete=models.CASCADE)
    hashtags = models.CharField(max_length=1000, blank=True, null=True)
    is_blank_default=models.BooleanField(default=False)
    def __str__(self):
        if self.description:
            return self.description
        else:
            return "unknown image"

class PreviewImage(models.Model):
    image = models.ImageField(upload_to="preview", editable=True, null=True, blank=True, storage=OverwriteStorage())
    selfie = models.ForeignKey(SelfieImage, blank=True, null=True, on_delete=models.CASCADE)
    moon = models.ForeignKey(MoonTemplate, blank=True, null=True, on_delete=models.CASCADE)
    foreground = models.ForeignKey(TextureImage, blank=True, null=True, on_delete=models.CASCADE, related_name='foreground')
    background = models.ForeignKey(TextureImage, blank=True, null=True, on_delete=models.CASCADE, related_name='background')
    image_data_uri = models.CharField(null=True, blank=True, default="", max_length=100000000)
    small_image = models.ImageField(upload_to="preview", editable=True, null=True, blank=True, storage=OverwriteStorage())

    #caption
    #image transformation settings
    selfie_contrast = models.IntegerField(default=1, blank=True, null=True)
    foreground_transparency = models.IntegerField(default=125)
    background_transparency = models.IntegerField(default=125)
    foreground_inverted = models.BooleanField(default=False)
    background_inverted = models.BooleanField(default=False)

    selfie_top_border = models.IntegerField(default = 50)
    selfie_right_border = models.IntegerField(default = 50)
    selfie_left_border = models.IntegerField(default = 50)
    selfie_bottom_border = models.IntegerField(default = 50)

    def __str__(self):
        return "User-edited image"
    def make_final_size(self, name=None, background_alpha=200, foreground_alpha=200, top_border=0, right_border=0, bottom_border=0, left_border=0):
        make_collage(self, file_name="temp.jpg", dim=1000, name=None)
    def process_image_files(self, name=None, background_alpha=200, foreground_alpha=200, top_border=0, right_border=0, bottom_border=0, left_border=0):
        make_collage(self, file_name="small_temp.jpg", dim=450, name=None)
        #make data uri
        try:
            image = Image.open(self.small_image.path)
            if (image.width <= image.height):
                ratio = 50.0 / image.width
            elif (image.height <= image.width):
                ratio = 50.0 / image.height
            new_width = int(image.width * ratio)
            new_height = int(image.height * ratio)

            image = image.resize((new_width,new_height), Image.ANTIALIAS)
            buffered = BytesIO()
            image.save(fp=buffered, format='PNG')
            im_data = buffered.getvalue()
            self.image_data_uri = 'data:image/png;base64,' + base64.b64encode(im_data).decode(encoding="utf-8", errors="strict")
        except Exception:
            pass

class Collage(UserUploadedImage):
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

    selfie_media_id = models.CharField(default="", max_length=60, null=True, blank=True)
    selfie_user_id = models.CharField(default="", max_length=60, null=True, blank=True)
    selfie_username = models.CharField(default="", max_length=60, null=True, blank=True)
    background_user = models.CharField(max_length=60, null=True, blank=True)
    background_description = models.CharField(default=":)", max_length=60)
    foreground_user = models.CharField(max_length=60, null=True, blank=True)
    foreground_description = models.CharField(default=":)", max_length=60, null=True, blank=True)
    percent_illuminated = models.IntegerField(default="0")
    moonstate_description = models.CharField(max_length=200,default="", null=True, blank=True)
    hashtags = models.CharField(max_length=1000, default="", null=True, blank=True)
    def __str__(self):
        return str(self.image)
    def make_image(self, previewImg):
        buffer = BytesIO()
        previewImg.selfie.used = True
        previewImg.selfie.save()
        previewImg.foreground.used = True
        previewImg.foreground.save()
        previewImg.background.used = True
        previewImg.background.save()
        previewImageFile = Image.open(previewImg.image)
        previewImageFile = previewImageFile.convert("RGB")
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
        if previewImg.selfie.instagram_user:
            selfie_user_id = previewImg.selfie.instagram_user.user_id
            selfie_media_id = previewImg.selfie.media_id
        else:
            selfie_user_id = 0
            selfie_media_id = 0
        hashtags = "{} {} {} {}".format(previewImg.moon.hashtags, previewImg.selfie.hashtags, previewImg.foreground.hashtags, previewImg.background.hashtags)
        moonstate_description = "{}, {}% illuminated".format(
                previewImg.moon.moon_state,
                previewImg.moon.percent_illuminated,
            )
        if previewImg.foreground:
            foreground_description = previewImg.foreground.description
            foreground_user = previewImg.background.username
        else:
            foreground_description = "nothing"
            foreground_user = ""
        if previewImg.background:
            background_description = previewImg.background.description
            background_user = previewImg.background.username
        else:
            background_description = "nothing"
            background_user = ""
        return cls(
            image = None,
            selfie_user_id = selfie_user_id,
            selfie_media_id = selfie_media_id, 
            background_user = background_user,
            foreground_user = foreground_user,
            background_description = background_description,
            foreground_description = foreground_description,
            moonstate_description = moonstate_description
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

def make_collage(self, dim=1000, file_name="small_temp.jpg", name=None):
    img_size = (dim, dim)
    buffer = BytesIO()
    if self.selfie:
        selfie = Image.open(self.selfie.image)
        selfie = selfie.resize(img_size, Image.ANTIALIAS)
        moon_shaped_selfie = Image.open(self.selfie.image)
        moon_shaped_selfie = moon_shaped_selfie.resize(img_size, Image.ANTIALIAS)
    else:
        selfie = Image.new('RGB', img_size, 'black')
        moon_shaped_selfie = Image.new('RGB', img_size, 'black')

    #give the selfie image the requested white borders
    white_background = Image.new('RGB', img_size, "white")

    selfie = ImageOps.fit(selfie, img_size, Image.ANTIALIAS)
    moon_shaped_selfie = ImageOps.fit(moon_shaped_selfie, img_size, Image.ANTIALIAS)

    if self.moon:
        moon_mask = Image.open(self.moon.image, 'r')
        moon_mask = moon_mask.resize(img_size, Image.ANTIALIAS)
        moon_mask_transparent = Image.open(self.moon.image, 'r')
        moon_mask_transparent = moon_mask_transparent.resize(img_size, Image.ANTIALIAS)
    else:
        moon_mask = Image.new('RGB', img_size, 'black')
        moon_mask_transparent = Image.new('RGB', img_size, 'black')

    moon_mask = moon_mask.convert("L")
    moon_mask_transparent = moon_mask_transparent.point(lambda i: min(i * 25, self.foreground_transparency))
    moon_mask_transparent = moon_mask_transparent.convert("L")

    if self.background:
        background = Image.open(self.background.image, 'r')
        background = ImageOps.fit(background, img_size, Image.ANTIALIAS)
    else:
        background= Image.new('RGB',img_size,'black')

    if self.foreground:
        moon_shaped_foreground = Image.open(self.foreground.image)
        moon_shaped_foreground = ImageOps.fit(moon_shaped_foreground, img_size, Image.ANTIALIAS)
    else:
        moon_shaped_foreground = Image.new('RGB', img_size, 'black')

    if self.background_inverted:
        background = invert_image(background)
    if self.foreground_inverted:
        moon_shaped_foreground = invert_image(moon_shaped_foreground)

    moon_shaped_selfie.putalpha(moon_mask)
    background_mask = background.point(lambda i: self.background_transparency)
    background_mask = background_mask.convert("L")
    moon_shaped_foreground.putalpha(moon_mask_transparent)

    #put transparent background over selfie
    selfie.paste(background, (0,0), mask=background_mask)

    #reput moon shaped selfie on top of transparent background
    selfie.paste(moon_shaped_selfie, (0,0), mask=moon_shaped_selfie)

    #put foreground over moon
    selfie.paste(moon_shaped_foreground, (0,0), mask=moon_mask_transparent)

    selfie = selfie.resize(img_size, Image.ANTIALIAS)
    selfie.save(fp=buffer, format='PNG')
    pillow_image = ContentFile(buffer.getvalue())
    if dim < 1000:
        self.small_image.save(file_name, InMemoryUploadedFile(
                    pillow_image,
                    None,
                    file_name,
                    'image/jpeg',
                    pillow_image.tell,
                    None
        ))
    else:
        self.image.save(file_name, InMemoryUploadedFile(
                    pillow_image,
                    None,
                    file_name,
                    'image/jpeg',
                    pillow_image.tell,
                    None
        ))


