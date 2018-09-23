from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import ModelForm
from editor.models import MoonImage, SelfieImage, TextureImage, PreviewImage


class SignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required. Please enter a valid email address.')
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

class MoonUploadForm(ModelForm):
    class Meta:
        model = MoonImage
        fields = ('image', 'percent_illuminated',)

class SelfieUploadForm(ModelForm):
    class Meta:
        model = SelfieImage
        fields = ('image', 'username', )

class TextureUploadForm(ModelForm):
    class Meta:
        model = TextureImage
        fields = ('image', 'username', 'description',)

class PreviewForm(ModelForm):
    class Meta:
        model = PreviewImage
        fields = ('selfie_contrast', 'foreground_transparency', 'foreground_inverted', 'background_transparency','background_inverted')
