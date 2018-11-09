"""collaborapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import editor.views

urlpatterns = [
    path('live/', admin.site.urls),
    path('', editor.views.home, name="home"),
    path('signup/', editor.views.signup, name="signup"),
    path('login/', editor.views.login_user, name="login"),
    path('logout/', editor.views.logout_user, name="logout"),
    path('edit/', editor.views.edit_image, name="edit_image"),
    path('image-library/', editor.views.manage_images, name="image_library"),
    path('saved/', editor.views.saved_images, name="saved_images"),
    path('delete/<int:pk>', editor.views.delete_image, name="delete_image"),
    path('post/', editor.views.post_to_instagram, name="post_to_instagram"),
    path('instagram-login/', editor.views.log_into_instagram),
    path('update-caption/<int:pk>', editor.views.update_caption, name="update_caption")
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

