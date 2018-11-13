from django.http import HttpResponse
from django.shortcuts import render, redirect
from editor.forms import SignupForm, MoonUploadForm, SelfieUploadForm, InstagramSelfieUploadForm, TextureUploadForm, PreviewForm, TempSavedImageForm, CaptionForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from editor.models import MoonTemplate, SelfieImage, TextureImage, PreviewImage, TempSavedImage, UserUploadedImage
from django.forms import modelformset_factory
from PIL import Image, ImageOps, ImageEnhance
import os
from munfase.settings import BASE_DIR
from munfase import settings
from editor.instagram_modules.CustomInstagramAPI import CustomInstagramAPI as ig
from django.shortcuts import get_object_or_404
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
    elif request.method == 'POST' and 'save-image' in request.POST:
        previewForm = PreviewForm(request.POST, instance=previewImage)
        collage = TempSavedImage.create(previewImage)
        collage.make_image(previewImage)
        return redirect('/saved/')
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

@login_required(login_url='/login')
def manage_images(request):
    moonUploadForm = MoonUploadForm()
    selfieUploadForm = SelfieUploadForm()
    textureUploadForm = TextureUploadForm()
    instagramSelfieUploadForm = InstagramSelfieUploadForm()
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
    elif request.method == 'POST' and 'instagram-selfie-upload' in request.POST:
        i = ig(test=True)
        instagramSelfieUploadForm = InstagramSelfieUploadForm(request.POST)
        if instagramSelfieUploadForm.is_valid():
            selfieImageObj = instagramSelfieUploadForm.save()
            image_info = i.get_image_info(selfieImageObj.instagram_post_url)
            selfieImageObj.media_id = image_info["media_id"]
            selfieImageObj.user_id = image_info["user_id"]
            selfieImageObj.url = image_info["url"]
            selfieImageObj.save()
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
                   'instagram_selfie_upload_form': instagramSelfieUploadForm,
                   'texture_upload_form': textureUploadForm }
                 )

@login_required(login_url='/login')
def home(request):
    return render(request, 'home.html')

def log_into_instagram(request):
    previewImage = PreviewImage.objects.first()
    return render(request, 'post_confirmation.html', {'instagram_user': instagram_user})

def delete_image(request, pk, template_name="upload_image.html"):
    image = get_object_or_404(UserUploadedImage, pk=pk)
    if request.method=='POST':
        image.delete()
        return redirect('/image-library/')
    else:
        return render(request, template_name, {'object': image})

def post_to_instagram(request, pk):
    i = ig(test=True)
    post = get_object_or_404(TempSavedImage, pk=pk)

    #get current username based on user_id
    if(post.selfie_media_id != 'media_id'):
        username = i.get_username(post.selfie_media_id)
        usertags = [{'user_id': post.selfie_user_id, 'position': [0.55, 0.66]}]
    else:
        username = "mun_fases"
        usertags = []

    #format the caption based on the post
    caption = "{}\n*\n📷: @{}\n*\n{}\n*\n{}".format(post.moonstate_description, username, post.background_description, post.foreground_description)
    i.post_image(image_path=post.image.path, caption=caption, usertags=usertags)
    data = {}
    data['instagram_user'] = username
    return render(request, 'post_confirmation.html', {'data': data})

def update_caption(request, pk):
    collage = get_object_or_404(TempSavedImage, pk=pk)
    collages = TempSavedImage.objects.all()
    form = CaptionForm(request.POST or None, instance = collage)
    if form.is_valid():
        form.save()
    return render(request, 'saved_images.html',
                  { 'collages': collages,
                    'selected_image': collage,
                    'caption_form': form }
                  )

def saved_images(request):
    collages = TempSavedImage.objects.all()
    if request.method == "GET" and "image-selection" in request.GET:
        selectedImage = TempSavedImage.objects.filter(pk=request.GET.get('image-selection')).last()
    else:
        selectedImage = collages.last()
    captionForm = CaptionForm(instance=selectedImage)
    return render(request, 'saved_images.html',
                  { 'collages': collages,
                    'selected_image': selectedImage,
                    'caption_form': captionForm }
                  )


