from django.http import HttpResponse
from django.shortcuts import render, redirect
from editor.forms import SignupForm, MoonUploadForm, SelfieUploadForm, TextureUploadForm, PreviewForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from editor.models import MoonTemplate, SelfieImage, TextureImage, PreviewImage, Collage
from django.forms import modelformset_factory
from PIL import Image, ImageOps, ImageEnhance
import os
from munfase.settings import BASE_DIR
from munfase import settings
from editor.instagram_modules import login as ig
import datetime
import pdb


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

@login_required(login_url='/login')
def edit_image(request):
    try:
        moon_images = MoonTemplate.objects.order_by('percent_illuminated')
        selfie_images = SelfieImage.objects.filter(used=False).order_by('date_uploaded')
        texture_images = TextureImage.objects.filter(used=False).order_by('date_uploaded')
        previewImage = PreviewImage.objects.all().first() or PreviewImage()
        previewForm = PreviewForm(instance=previewImage)
        extraInfo = request.POST
        if request.method == 'POST' and "selfie-selection" in request.POST:
            previewImage.selfie = SelfieImage.objects.filter(pk=request.POST.get('selfie-selection')).first()
        elif request.method == 'POST' and "moon-selection" in request.POST:
            previewImage.moon = MoonTemplate.objects.filter(pk=request.POST.get('moon-selection')).first()
        elif request.method == 'POST' and "foreground-selection" in request.POST:
            previewImage.foreground = TextureImage.objects.filter(pk=request.POST.get('foreground-selection')).first()
        elif request.method == 'POST' and "background-selection" in request.POST:
            previewImage.background = TextureImage.objects.filter(pk=request.POST.get('background-selection')).first()
        elif request.method == 'POST' and 'color-values' in request.POST:
            previewForm = PreviewForm(request.POST, instance=previewImage)
        elif request.method == 'POST' and 'color-values' in request.POST:
            previewForm = PreviewForm(request.POST, instance=previewImage)
        if previewForm.is_valid():
            previewImage = previewForm.save()
        previewImage.process_image_files(name=settings.MEDIA_ROOT + 'preview/' + 'temp.jpg', background_alpha=previewImage.background_transparency, foreground_alpha=previewImage.foreground_transparency )
        return render(request, 'edit_image.html',
                      {'preview_form': previewForm,
                       'preview_image': previewImage,
                       'extra_info': extraInfo,
                       'moon_images': moon_images,
                       'selfie_images': selfie_images,
                       'texture_images': texture_images }
                      )
    except Exception as e:
        return render(request, 'error.html',
                      { 'error': dir(e) })

def upload_image(request):
    moonUploadForm = MoonUploadForm()
    selfieUploadForm = SelfieUploadForm()
    textureUploadForm = TextureUploadForm()
    moon_images = MoonTemplate.objects.order_by('percent_illuminated')
    selfie_images = SelfieImage.objects.filter(used=False).order_by('date_uploaded')
    texture_images = TextureImage.objects.filter(used=False).order_by('date_uploaded')
    if request.method == 'POST' and "moon-upload" in request.POST:
        moonUploadForm = MoonUploadForm(request.POST, request.FILES)
        if moonUploadForm.is_valid():
            moonTemplateObj = moonUploadForm.save()
            moonUploadForm = MoonUploadForm()
    elif request.method == 'POST' and "selfie-upload" in request.POST:
        selfieUploadForm = SelfieUploadForm(request.POST, request.FILES)
        if selfieUploadForm.is_valid():
            selfieImageObj = selfieUploadForm.save()
            selfieUploadForm = SelfieUploadForm()
    elif request.method == 'POST' and "texture-upload" in request.POST:
        textureUploadForm = TextureUploadForm(request.POST, request.FILES)
        if textureUploadForm.is_valid():
            textureImageObj = textureUploadForm.save()
            textureUploadForm = TextureUploadForm()
    return render(request, 'upload_image.html',
                  {'moon_images': moon_images,
                   'selfie_images': selfie_images,
                   'texture_images': texture_images,
                   'moon_upload_form': moonUploadForm,
                   'selfie_upload_form': selfieUploadForm,
                   'texture_upload_form': textureUploadForm }
                 )

def log_into_instagram(request):
    previewImage = PreviewImage.objects.first()
    instagram_user = ig.post_image(previewImage)
    return render(request, 'post_uploaded.html', {'instagram_user': instagram_user})
