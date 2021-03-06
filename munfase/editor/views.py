from django.http import HttpResponse
from django.shortcuts import render, redirect
from editor.forms import SignupForm, MoonUploadForm, SelfieUploadForm, TextureUploadForm, PreviewForm, CollageForm, CaptionForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from editor.models import MoonTemplate, SelfieImage, TextureImage, PreviewImage, Collage, UserUploadedImage, InstagramUser
from django.forms import modelformset_factory
from PIL import Image, ImageOps, ImageEnhance
import os
from munfase.settings import BASE_DIR
from munfase import settings
from editor.instagram_modules.CustomInstagramAPI import CustomInstagramAPI as ig
from django.shortcuts import get_object_or_404
import datetime
import pdb
import time

# import the logging library
import logging
import traceback

# Get an instance of a logger
logger = logging.getLogger(__name__)

#for saving edited files to model
#https://stackoverflow.com/questions/32945292/how-to-save-pillow-image-object-to-django-imagefield/45907694
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from io import StringIO
from django.core.files.base import ContentFile

def about(request):
    return render(request, 'about.html')

def participate(request):
    return render(request, 'participate.html')

def watch_ad(request):
    return render(request, 'watch_ad.html')

#def signup(request):
#    if request.user.is_authenticated:
#        return redirect('/')
#    if request.method == 'POST':
#        form = SignupForm(request.POST)
#        if form.is_valid():
#            form.save()
#            username = form.cleaned_data.get('username')
#            password = form.cleaned_data.get('password1')
#            user = authenticate(username=username, password=password)
#            login(request, user)
#            return redirect('/')
#        else:
#            return render(request, 'signup.html', {'form': form})
#    else:
#        form = SignupForm()
#        return render(request, 'signup.html', {'form': form})

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
        blank_texture_image = TextureImage.objects.filter(is_blank_default=True).first()
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
            previewImage.make_final_size()
            collage = Collage.create(previewImage)
            collage.make_image(previewImage)
            return redirect('/saved/')
        elif request.method == 'POST' and 'color-values' in request.POST:
            previewForm = PreviewForm(request.POST, instance=previewImage)
        if previewForm.is_valid():
            previewImage = previewForm.save()
        previewImage.process_image_files(name=settings.MEDIA_ROOT + 'preview/' + 'temp.jpg', background_alpha=previewImage.background_transparency, foreground_alpha=previewImage.foreground_transparency )
        current_time = str(time.time())
        return render(request, 'make_post.html',
                          {'current_time': current_time,
                           'preview_form': previewForm,
                           'preview_image': previewImage,
                           'extra_info': extraInfo,
                           'moon_images': moon_images,
                           'selfie_images': selfie_images,
                           'texture_images': texture_images,
                           'blank_texture_image': blank_texture_image }
                          )
    except Exception:
        print(traceback.format_exc())
        return render(request, 'make_post.html',
                          {'current_time': current_time,
                           'preview_form': previewForm,
                           'preview_image': previewImage,
                           'extra_info': extraInfo,
                           'moon_images': moon_images,
                           'selfie_images': selfie_images,
                           'texture_images': texture_images,
                           'blank_texture_image': blank_texture_image }
                          )



@login_required(login_url='/login')
def manage_images(request):
    try:
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
            process_image_upload(selfieUploadForm)
            selfieUploadForm = SelfieUploadForm()
        elif request.method == 'POST' and "texture-upload" in request.POST:
            textureUploadForm = TextureUploadForm(request.POST, request.FILES)
            process_image_upload(textureUploadForm)
            textureUploadForm = TextureUploadForm()
        return render(request, 'upload_image.html',
                      {'moon_images': moon_images,
                       'selfie_images': selfie_images,
                       'texture_images': texture_images,
                       'moon_upload_form': moonUploadForm,
                       'selfie_upload_form': selfieUploadForm,
                       'texture_upload_form': textureUploadForm }
                     )
    except Exception:
        print(traceback.format_exc())
        return render(request, 'upload_image.html',
                      {'moon_images': moon_images,
                       'selfie_images': selfie_images,
                       'texture_images': texture_images,
                       'moon_upload_form': moonUploadForm,
                       'selfie_upload_form': selfieUploadForm,
                       'texture_upload_form': textureUploadForm }
                     )



def home(request):
    return render(request, 'home.html')

def process_image_upload(form):
    if form.is_valid():
        imageObj = form.save()
        if imageObj.instagram_post_url:
            i = ig(test=False)
            imageObj = form.save()
            image_info = i.get_image_info(imageObj.instagram_post_url)
            imageObj.media_id = image_info["media_id"]
            existing_instagram_user = InstagramUser.objects.filter(user_id=image_info['user_id'])
            if len(existing_instagram_user):
                imageObj.instagram_user = existing_instagram_user.first()
            else:
                imageObj.instagram_user = InstagramUser.objects.create(user_id=image_info['user_id'], username=image_info['username'])
            imageObj.source_url = image_info["url"]
            imageObj.save()


def log_into_instagram(request):
    previewImage = PreviewImage.objects.first()
    return render(request, 'post_confirmation.html', {'instagram_user': instagram_user})

def post_to_instagram(request, pk):
    i = ig(test=False)
    post = get_object_or_404(Collage, pk=pk)

    #get current username based on user_id
    if(post.selfie_media_id and post.selfie_media_id != 'media_id'):
        username = i.get_username(post.selfie_media_id)
        usertags = [{'user_id': post.selfie_user_id, 'position': [0.55, 0.66]}]
    else:
        username = "mun_fases"
        usertags = []

    #format the caption based on the post
    caption = "{}\n*\n{} {} {}\n*\n📷: @{}\n*\n{}".format(post.foreground_description,post.first_emoji, post.moonstate_description, post.second_emoji, username, post.hashtags)
    i.post_image(image_path=post.image.path, caption=caption, usertags=usertags)
    data = {}
    data['instagram_user'] = username
    return redirect(show_saved_collages)

def update_caption(request, pk):
    collage = get_object_or_404(Collage, pk=pk)
    collages = Collage.objects.all()
    form = CaptionForm(request.POST or None, instance = collage)
    if form.is_valid():
        form.save()
    else:
        error = "form isn't valid, silly"
    return render(request, 'saved_images.html',
                  { 'collages': collages,
                    'error': error,
                    'selected_image': collage,
                    'caption_form': form }
                  )

@login_required(login_url='/login')
def show_saved_collages(request):
    try:
        collages = Collage.objects.all()
        if request.method == "GET" and "image-selection" in request.GET:
            selectedImage = Collage.objects.filter(pk=request.GET.get('image-selection')).last()
        else:
            selectedImage = collages.last()
        captionForm = CaptionForm(instance=selectedImage)
        return render(request, 'saved_images.html',
                      { 'collages': collages,
                        'selected_image': selectedImage,
                        'caption_form': captionForm }
                      )
    except Exception:
        print(traceback.format_exc())
        return render(request, 'saved_images.html',
                      { 'collages': collages,
                        'selected_image': selectedImage,
                        'caption_form': captionForm }
                      )




def image(request, pk, image_type):
    try:
        if image_type=="SelfieImage":
            image = get_object_or_404(SelfieImage, pk=pk)
            form = SelfieUploadForm(instance=image)
        if image_type=="TextureImage":
            image = get_object_or_404(TextureImage, pk=pk)
            form = TextureUploadForm(instance=image)
        if image_type=="MoonTemplate":
            image = get_object_or_404(MoonTemplate, pk=pk)
            form = MoonUploadForm(instance=image)
        return render(request, 'image.html',
                      { 'form': form,
                        'image_type': image_type,
                        'image_pk': pk})
    except Exception:
        print(traceback.format_exc())
        return render(request, 'image.html',
                      { 'form': form,
                        'image_type': image_type,
                        'image_pk': pk})


def edit_existing_image(request, pk, image_type):
    try:
        if request.method=='POST' and image_type == 'TextureImage':
            image = get_object_or_404(TextureImage, pk=pk)
            form = TextureUploadForm(request.POST, request.FILES, instance=image)
        elif request.method=='POST' and image_type == 'SelfieImage':
            image = get_object_or_404(SelfieImage, pk=pk)
            form = SelfieUploadForm(request.POST, request.FILES, instance=image)
        elif request.method=='POST' and image_type == 'MoonTemplate':
            image = get_object_or_404(MoonTemplate, pk=pk)
            form = MoonUploadForm(request.POST, request.FILES, instance=image)
        if form.is_valid():
            item = form.save()
            return redirect(manage_images)
        else:
            return render(request, 'image.html', {'form': form })
    except Exception:
        print(traceback.format_exc())
        return render(request, 'image.html', {'form': form })

def delete_image(request, pk, template_name="edit.html"):
    try:
        image = get_object_or_404(UserUploadedImage, pk=pk)
        if request.method=='POST':
            image.delete()
            return redirect('/image-library/')
        else:
            return render(request, template_name, {'object': image})
    except Exception:
        print(traceback.format_exc())
        return render(request, template_name, {'object': image})

def my_custom_page_not_found_view(request):
    data = {}
    data['error'] = 'page not found'
    return render(request, 'errors/404.html', data)

def my_custom_error_view(request):
    data = {}
    data['error'] = 'custom error view'
    return render(request, 'errors/404.html', data)

def my_custom_permission_denied_view(request):
    data = {}
    data['error'] = 'permission denied'
    return render(request, 'errors/404.html', data)

def my_custom_bad_request_view(request):
    data = {}
    data['error'] = 'bad request'
    return render(request, 'errors/404.html', data)
