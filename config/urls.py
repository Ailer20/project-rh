from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # REMOVA OU COMENTE AS LINHAS ABAIXO QUE ESTAVAM CAUSANDO O LOOP:
    # path('', RedirectView.as_view(url='/login/', permanent=False)),
    # path('', include('hierarquia.urls')), 
    
    # ----------------------------------------------------
    # NOVA CONFIGURAÇÃO LIMPA
    # ----------------------------------------------------
    # O acesso à raiz ('') agora usa o include do app
    # Isso assume que sua URL de login está definida como 'path('login/', ...)' 
    # dentro de hierarquia/urls.py
    path('', include('hierarquia.urls')),

    # ... Rotas da API
    path('api/', include('hierarquia.api_urls')),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
