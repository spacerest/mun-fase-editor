from django.http import HttpResponse
from django.shortcuts import render, redirect
from editor.forms import SignupForm, MoonUploadForm, SelfieUploadForm, TextureUploadForm, PreviewForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from editor.models import MoonImage, SelfieImage, TextureImage, PreviewImage, SavedImage
from django.forms import modelformset_factory
from PIL import Image, ImageOps, ImageEnhance
import os
from munfase.settings import BASE_DIR
from munfase import settings
from editor.instagram_modules import login as ig
import datetime


#for saving edited files to model
#https://stackoverflow.com/questions/32945292/how-to-save-pillow-image-object-to-django-imagefield/45907694
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from io import StringIO
from django.core.files.base import ContentFile

def signup(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'signup.html', {'form': form})
    else:
        form = SignupForm()
        return render(request, 'signup.html', {'form': form})

def login_user(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'login.html', {'form': form})
    else:
        form = AuthenticationForm()
        return render(request, 'login.html', {'form': form})

def logout_user(request):
    logout(request)
    return redirect('/login')

def updatePreviewObjects(request, previewImage):

    if request.method == 'POST' and "selfie-selection" in request.POST:
        previewImage.selfie = SelfieImage.objects.filter(pk=request.POST.get('selfie-selection')).first()
    elif request.method == 'POST' and "moon-selection" in request.POST:
        previewImage.moon = MoonImage.objects.filter(pk=request.POST.get('moon-selection')).first()
    elif request.method == 'POST' and "foreground-selection" in request.POST:
        previewImage.foreground = TextureImage.objects.filter(pk=request.POST.get('foreground-selection')).first()
    elif request.method == 'POST' and "background-selection" in request.POST:
        previewImage.background = TextureImage.objects.filter(pk=request.POST.get('background-selection')).first()
    elif request.method == 'POST' and 'color-values' in request.POST:
        previewForm = PreviewForm(request.POST, instance=previewImage)
        if previewForm.is_valid():
            previewForm.save()
    elif request.method == 'POST' and 'save-image' in request.POST:
        previewForm = PreviewForm(request.POST)
        if previewForm.is_valid():
            save_new_image(previewImage)
        previewImage.save()
    return PreviewForm(instance=previewImage)

def save_new_image(previewImage):
     buffer = BytesIO()
     previewImageFile = Image.open(previewImage.image)
     previewImageFile.save(fp=buffer, format='PNG')
     contentFile = ContentFile(buffer.getvalue())
     savedImage = SavedImage.create(previewImage)
     savedImageFileName = "{}_{}_{}.jpg".format(
            previewImage.moon.percent_illuminated,
            previewImage.selfie.username,
            datetime.date.today().strftime("%Y%m%d")
        )
     savedImage.image.save(savedImageFileName, InMemoryUploadedFile(
        contentFile,
        None,
        savedImageFileName,
        'image/jpeg',
        contentFile.tell,
        None
    ))




def process_image_files(previewImage, name=None, background_alpha=200, foreground_alpha=200):
    buffer = BytesIO()
    if previewImage.selfie:
        selfie = Image.open(previewImage.selfie.image)
        moon_shaped_selfie = Image.open(previewImage.selfie.image)
    else:
        selfie = Image.new('RGB', (1000,1000), 'black')
        moon_shaped_selfie = Image.new('RGB', (1000,1000), 'black')
    selfie = ImageOps.fit(selfie, (1000, 1000), Image.ANTIALIAS)
    moon_shaped_selfie = ImageOps.fit(moon_shaped_selfie, (1000,1000), Image.ANTIALIAS)
    if previewImage.moon:
        moon_mask = Image.open(previewImage.moon.image, 'r')
        moon_mask_transparent = Image.open(previewImage.moon.image, 'r')
    else:
        moon_mask = Image.new('RGB', (1000,1000), 'black')
        moon_mask_transparent = Image.new('RGB', (1000,1000), 'black')
    moon_mask = moon_mask.convert("L")
    moon_mask_transparent = moon_mask_transparent.point(lambda i: min(i * 25, foreground_alpha))
    moon_mask_transparent = moon_mask_transparent.convert("L")

    if previewImage.background:
        background = Image.open(previewImage.background.image, 'r')
        background = ImageOps.fit(background, (1000,1000), Image.ANTIALIAS)
    else:
        background= Image.new('RGB',(1000,1000),'black')

    if previewImage.foreground:
        moon_shaped_foreground = Image.open(previewImage.foreground.image)
        moon_shaped_foreground = ImageOps.fit(moon_shaped_foreground, (1000,1000), Image.ANTIALIAS)
    else:
        moon_shaped_foreground = Image.new('RGB', (1000,1000), 'black')
    if previewImage.background_inverted:
        background = invert_image(background)
    if previewImage.foreground_inverted:
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
    return ContentFile(buffer.getvalue())

#https://stackoverflow.com/questions/42045362/change-contrast-of-image-in-pil
def change_contrast(img, level):
    factor = (259 * (level + 255)) / (255 * (259 - level))
    def contrast(c):
        return 128 + factor * (c - 128)
    return img.point(contrast)

def invert_image(img):
    return ImageOps.invert(img)

@login_required(login_url='/login')
def edit_image(request):
    try:
        moon_images = MoonImage.objects.order_by('percent_illuminated')
        selfie_images = SelfieImage.objects.filter(used=False).order_by('date_uploaded')
        texture_images = TextureImage.objects.filter(used=False).order_by('date_uploaded')
        moonUploadForm = MoonUploadForm()
        selfieUploadForm = SelfieUploadForm()
        textureUploadForm = TextureUploadForm()
        previewImage = PreviewImage.objects.all().first() or PreviewImage()
        print(previewImage)
        previewForm = PreviewForm(instance=previewImage)
        extraInfo = request.POST
        if request.method == 'POST' and "moon-upload" in request.POST:
            moonUploadForm = MoonUploadForm(request.POST, request.FILES)
            if moonUploadForm.is_valid():
                moonImageObj = moonUploadForm.save()
                make_thumbnail(moonImageObj)
                moonUploadForm = MoonUploadForm()
        elif request.method == 'POST' and "selfie-upload" in request.POST:
            selfieUploadForm = SelfieUploadForm(request.POST, request.FILES)
            if selfieUploadForm.is_valid():
                selfieImageObj = selfieUploadForm.save()
                make_thumbnail(selfieImageObj)
                selfieUploadForm = SelfieUploadForm()
        elif request.method == 'POST' and "texture-upload" in request.POST:
            textureUploadForm = TextureUploadForm(request.POST, request.FILES)
            if textureUploadForm.is_valid():
                textureImageObj = textureUploadForm.save()
                make_thumbnail(textureImageObj)
                textureUploadForm = TextureUploadForm()
        previewForm = updatePreviewObjects(request, previewImage)
        pillow_image = process_image_files(previewImage, name=settings.MEDIA_ROOT + 'preview/' + 'temp.jpg', background_alpha=previewImage.background_transparency, foreground_alpha=previewImage.foreground_transparency )
        previewImage.image.save('temp.jpg', InMemoryUploadedFile(
            pillow_image,
            None,
            'temp.jpg',
            'image/jpeg',
            pillow_image.tell,
            None
        ))
        return render(request, 'edit_image.html',
                      {'moon_upload_form': moonUploadForm,
                       'selfie_upload_form': selfieUploadForm,
                       'texture_upload_form': textureUploadForm,
                       'preview_form': previewForm,
                       'preview_image': previewImage,
                       'extra_info': extraInfo,
                       'moon_images': moon_images,
                       'selfie_images': selfie_images,
                       'texture_images': texture_images }
                      )
    except Exception as e:
        return render(request, 'error.html',
                      { 'error': e })

#image processing
#helpful link https://simpleisbetterthancomplex.com/tutorial/2017/03/02/how-to-crop-images-in-a-django-application.html
#how to add mask: https://stackoverflow.com/questions/38627870/how-to-paste-a-png-image-with-transparency-to-another-image-in-pil-without-white/38629258

#A mask is an Image object where the alpha value is significant, but its green, red, and blue values are ignored.

#transparency masks: http://www.leancrew.com/all-this/2013/11/transparency-with-pil/

def make_thumbnail(obj):
    buffer = BytesIO()
    image = Image.open(obj.image)
    image = ImageOps.fit(image, (100, 100), Image.ANTIALIAS)
    image.save(fp=buffer, format='PNG')
    thumbnailBuffer = ContentFile(buffer.getvalue())
    obj.thumbnail.save(obj.image.name,
                        InMemoryUploadedFile(
                            thumbnailBuffer,
                            None,
                            obj.image.name,
                            'image/jpeg',
                            thumbnailBuffer.tell,
                            None
                        ))

def log_into_instagram(request):
    previewImage = PreviewImage.objects.first()
    instagram_user = ig.post_image(previewImage)
    return render(request, 'post_uploaded.html', {'instagram_user': instagram_user})
