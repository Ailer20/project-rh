# hierarquia/api_serializers.py

from rest_framework import serializers
from .models import Funcionario

class FuncionarioSerializer(serializers.ModelSerializer):
    # 1. Defina explicitamente os campos de relacionamento como PrimaryKeyRelatedField
    # Isso garante que apenas o ID do objeto relacionado seja usado.
    cargo = serializers.PrimaryKeyRelatedField(read_only=True)
    setor_primario = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Funcionario
        fields = [
            'id', 
            'ra_nome', 
            'cargo', 
            'setor_primario', 
        ]
    