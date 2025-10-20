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
    # Define o recurso de import/export
    resource_class = None # Usa o padrão

@admin.register(Setor)
class SetorAdmin(ImportExportModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)
    # Define o recurso de import/export
    resource_class = None # Usa o padrão

# Registre os outros modelos
@admin.register(CentroServico)
class CentroServicoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'setor')
    list_filter = ('setor',)
    search_fields = ('nome',)

@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    # Use 'get_setores' em vez de 'setor' no list_display
    list_display = ('nome', 'cargo', 'get_setores', 'usuario', 'ativo')
    list_filter = ('ativo', 'setor', 'cargo') # 'setor' funciona bem em list_filter
    search_fields = ('nome', 'cpf', 'usuario__username')
    
    # --- MUDANÇA IMPORTANTE ---
    # Isso cria uma caixa de seleção "arrasta e solta" muito melhor
    # para campos ManyToMany, como o "setor" e as permissões de usuário
    filter_horizontal = ('setor',)

    # Método customizado para exibir os setores
    def get_setores(self, obj):
        # Pega todos os nomes dos setores e os une com ", "
        return ", ".join([s.nome for s in obj.setor.all()])
    
    # Dá um nome amigável para a coluna
    get_setores.short_description = 'Setores'

@admin.register(Requisicao)
class RequisicaoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'solicitante', 'status', 'aprovador', 'criado_em')
    list_filter = ('status', 'solicitante__setor')
    search_fields = ('titulo', 'solicitante__nome', 'aprovador__nome')
    raw_id_fields = ('solicitante', 'aprovador') # Melhora a performance