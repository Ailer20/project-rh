from django.contrib import admin
# Importe os modelos REAIS do seu models.py
from .models import Cargo, Setor, CentroServico, Funcionario, Requisicao

# Registre-os
admin.site.register(Cargo)
admin.site.register(Setor)
admin.site.register(CentroServico)
admin.site.register(Funcionario)
admin.site.register(Requisicao)