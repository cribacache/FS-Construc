"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
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
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.static import serve

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('', include('website.urls')),
]

# Local fallback only: when photos are stored in Cloud Storage (GS_BUCKET_NAME
# set), MEDIA_URL points straight at storage.googleapis.com and Django never
# needs to serve these files itself.
if not settings.GS_BUCKET_NAME:
    urlpatterns.append(
        path(
            f'{settings.MEDIA_URL.lstrip("/")}<path:path>',
            serve,
            {'document_root': settings.MEDIA_ROOT},
        )
    )
