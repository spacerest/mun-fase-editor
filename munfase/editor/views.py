from django.http import HttpResponse
from django.shortcuts import render, redirect
from editor.forms import SignupForm, MoonUploadForm, SelfieUploadForm, TextureUploadForm, PreviewForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from editor.models import MoonImage, SelfieImage, TextureImage, PreviewImage
from django.forms import modelformset_factory
from PIL import Image
import os
from munfase.settings import BASE_DIR
from munfase import settings

#for saving edited files to model
#https://stackoverflow.com/questions/32945292/how-to-save-pillow-image-object-to-django-imagefield/45907694
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
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

def updatePreviewObjects(request, request_name, previewImage):
    if request.method == 'POST' and request_name in request.POST:
        if request_name == "selfie-selection":
            previewImage.selfie = SelfieImage.objects.filter(pk=request.POST.get(request_name)).first()
        elif request_name == "moon-selection":
            previewImage.moon = MoonImage.objects.filter(pk=request.POST.get(request_name)).first()
        elif request_name == "foreground-selection":
            previewImage.foreground = TextureImage.objects.filter(pk=request.POST.get(request_name)).first()
        elif request_name == "background-selection":
            previewImage.background = TextureImage.objects.filter(pk=request.POST.get(request_name)).first()
        previewImage.save()
    return PreviewForm(instance=previewImage)

def process_image_files(previewImage, name=None):
    image_field = previewImage.image
    #img = Image.open(image_field)
    #new_img = img.resize((10, 10))
    buffer = BytesIO()
    #new_img.save(fp=buffer, format='PNG')

    selfie_image = Image.open(previewImage.selfie.image)
    selfie_image = selfie_image.resize((1000,1000))
    moon_mask = Image.open(previewImage.moon.image, 'r')
    moon_mask = moon_mask.convert("L")
    selfie_image.putalpha(moon_mask)
    #moon = Image.open(os.path.join(BASE_DIR, 'media/moon/77.png'), 'r')
    #moon = moon.resize((1000,1000))
    background = Image.open(previewImage.background.image, 'r')
    background = background.resize((1000,1000))
    foreground = Image.open(previewImage.foreground.image, 'r')
    foreground = foreground.resize((1000,1000))
    foreground.paste(selfie_image, (0,0), mask=selfie_image)
    foreground.save(fp=buffer, format='PNG')

    return ContentFile(buffer.getvalue())

@login_required(login_url='/login')
def edit_image(request):
    moon_images = MoonImage.objects.order_by('percent_illuminated')
    selfie_images = SelfieImage.objects.filter(used=False).order_by('date_uploaded')
    texture_images = TextureImage.objects.filter(used=False).order_by('date_uploaded')
    moonUploadForm = MoonUploadForm()
    selfieUploadForm = SelfieUploadForm()
    textureUploadForm = TextureUploadForm()
    previewImage = PreviewImage.objects.all().first()
    previewForm = PreviewForm(instance=previewImage)
    extraInfo = request.POST
    if request.method == 'POST' and "moon-upload" in request.POST:
        moonUploadForm = MoonUploadForm(request.POST, request.FILES)
        if moonUploadForm.is_valid():
            moonUploadForm.save()
            moonUploadForm = MoonUploadForm()
    elif request.method == 'POST' and "selfie-upload" in request.POST:
        selfieUploadForm = SelfieUploadForm(request.POST, request.FILES)
        if selfieUploadForm.is_valid():
            selfieUploadForm.save()
            selfieUploadForm = SelfieUploadForm()
    elif request.method == 'POST' and "texture-upload" in request.POST:
        textureUploadForm = TextureUploadForm(request.POST, request.FILES)
        if textureUploadForm.is_valid():
            textureUploadForm.save()
            textureUploadForm = TextureUploadForm()
    previewForm = updatePreviewObjects(request, "selfie-selection", previewImage)
    previewForm = updatePreviewObjects(request, "moon-selection", previewImage)
    previewForm = updatePreviewObjects(request, "background-selection", previewImage)
    previewForm = updatePreviewObjects(request, "foreground-selection", previewImage)
    pillow_image = process_image_files(previewImage, name=settings.MEDIA_ROOT + 'preview/' + 'temp.jpg' )
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

#image processing
#helpful link https://simpleisbetterthancomplex.com/tutorial/2017/03/02/how-to-crop-images-in-a-django-application.html
#how to add mask: https://stackoverflow.com/questions/38627870/how-to-paste-a-png-image-with-transparency-to-another-image-in-pil-without-white/38629258

#A mask is an Image object where the alpha value is significant, but its green, red, and blue values are ignored.

#transparency masks: http://www.leancrew.com/all-this/2013/11/transparency-with-pil/

def return_image(request):
    selfie_image = Image.open(os.path.join(BASE_DIR, 'media/selfie/yerin_pong.jpg'), 'r')
    selfie_image = selfie_image.resize((1000,1000))
    moon_mask = Image.open(os.path.join(BASE_DIR, 'media/moon/77.png'), 'r')
    moon_mask = moon_mask.convert("L")
    selfie_image.putalpha(moon_mask)
    moon = Image.open(os.path.join(BASE_DIR, 'media/moon/77.png'), 'r')
    moon = moon.resize((1000,1000))
    background = Image.open(os.path.join(BASE_DIR, 'media/texture/583_prof_1.jpg'), 'r')
    background = background.resize((1000,1000))
    foreground = Image.open(os.path.join(BASE_DIR, 'media/texture/IMG_80371.JPG'), 'r')
    foreground = foreground.resize((1000,1000))
    foreground.paste(selfie_image, (0,0), mask=selfie_image)
    response = HttpResponse(content_type="image/png")
    foreground.save(response, "PNG")
    return response
    return render(request, 'edit_image.html',
                  {'base_img': base_img,
                    'moon_upload_form': moonUploadForm,
                   'selfie_upload_form': selfieUploadForm,
                   'texture_upload_form': textureUploadForm,
                   'moon_images': moon_images,
                   'selfie_images': selfie_images,
                   'texture_images': texture_images }
                  )

