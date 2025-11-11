from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('hierarquia.urls')),
    
    # Rotas da API para o aplicativo Flutter
    path('api/', include('hierarquia.api_urls')), # Rotas de dados (Funcionários, etc.)
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')), # Rotas de login/logout
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
