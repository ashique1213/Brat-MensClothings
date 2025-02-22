"""
URL configuration for bratmensclothing project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'salesreport'

urlpatterns = [
   
    path('view_salesreport/', views.view_salesreport, name='view_salesreport'),  
    path('download_pdf/', views.download_pdf, name='download_pdf'),  
    path('download_excel/', views.download_excel, name='download_excel'),  
   
 
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
