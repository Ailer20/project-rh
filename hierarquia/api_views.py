# hierarquia/api_views.py

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Funcionario
from .api_serializers import FuncionarioSerializer
from rest_framework.authentication import TokenAuthentication # <--- Adicione esta linha

class FuncionarioViewSet(viewsets.ModelViewSet):
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer
    permission_classes = [IsAuthenticated] # Apenas usuários autenticados podem acessar
    authentication_classes = [TokenAuthentication] # <--- Adicione esta linha
