from django.contrib import admin
# Importe a classe da biblioteca
from import_export.admin import ImportExportModelAdmin
# Importe seus modelos
from .models import Cargo, Setor, CentroServico, Funcionario, Requisicao

# Crie classes de Admin que herdam de ImportExportModelAdmin
@admin.register(Cargo)
class CargoAdmin(ImportExportModelAdmin):
    list_display = ('nome', 'nivel', 'descricao')
    search_fields = ('nome', 'descricao')
    list_filter = ('nivel',)

@admin.register(Setor)
class SetorAdmin(ImportExportModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)

# Registre os outros modelos normalmente (ou use o decorator @admin.register)
@admin.register(CentroServico)
class CentroServicoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'setor')
    list_filter = ('setor',)

@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cargo', 'setor', 'ativo')
    list_filter = ('ativo', 'setor', 'cargo')
    search_fields = ('nome', 'cpf')

@admin.register(Requisicao)
class RequisicaoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'solicitante', 'status', 'criado_em')
    list_filter = ('status',)
    search_fields = ('titulo', 'solicitante__nome')