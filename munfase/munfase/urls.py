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
    path('signup/', editor.views.signup),
    path('login/', editor.views.login_user),
    path('logout/', editor.views.logout_user),
    path('edit/', editor.views.edit_image),
    path('saved/', editor.views.show_saved_images),
    path('', editor.views.index),
    path('instagram-login/', editor.views.log_into_instagram),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

