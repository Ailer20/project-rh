from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget, DateWidget, BooleanWidget
from .models import Cargo, Setor, CentroServico, Funcionario, Requisicao
from django.contrib.auth.models import User

# --- Resource para Cargos ---
class CargoResource(resources.ModelResource):
    class Meta:
        model = Cargo
        fields = ('id', 'nome', 'nivel', 'descricao',)
        export_order = ('id', 'nome', 'nivel', 'descricao',)
        # Para garantir importação correta mesmo com dados existentes
        import_id_fields = ['nome']
        skip_unchanged = True
        report_skipped = True

@admin.register(Cargo)
class CargoAdmin(ImportExportModelAdmin):
    resource_class = CargoResource
    list_display = ('nome', 'nivel', 'descricao')
    search_fields = ('nome', 'descricao')
    list_filter = ('nivel',)

# --- Resource para Setores ---
class SetorResource(resources.ModelResource):
    class Meta:
        model = Setor
        fields = ('id', 'nome', 'descricao',)
        export_order = ('id', 'nome', 'descricao',)
        # Para garantir importação correta mesmo com dados existentes
        import_id_fields = ['nome']
        skip_unchanged = True
        report_skipped = True

@admin.register(Setor)
class SetorAdmin(ImportExportModelAdmin):
    resource_class = SetorResource
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)

# --- Resource DETALHADO para Funcionários (CORRIGIDO) ---
class FuncionarioResource(resources.ModelResource):
    cargo = fields.Field(
        column_name='cargo',
        attribute='cargo',
        widget=ForeignKeyWidget(Cargo, 'nome'))

    setor = fields.Field(
        column_name='setores', # Nome da coluna no CSV
        attribute='setor',     # Nome do campo ManyToMany no Model
        widget=ManyToManyWidget(Setor, field='nome', separator=',')) # Busca por 'nome', separa por ','

    centro_servico = fields.Field(
        column_name='centro_servico',
        attribute='centro_servico',
        widget=ForeignKeyWidget(CentroServico, 'nome')) # Busca pelo nome

    usuario = fields.Field(
        column_name='usuario',
        attribute='usuario',
        widget=ForeignKeyWidget(User, User.USERNAME_FIELD)) # Busca pelo username

    data_nascimento = fields.Field(
        column_name='data_nascimento',
        attribute='data_nascimento',
        widget=DateWidget(format='%d/%m/%Y')) # Espera DD/MM/YYYY

    data_admissao = fields.Field(
        column_name='data_admissao',
        attribute='data_admissao',
        widget=DateWidget(format='%d/%m/%Y')) # Espera DD/MM/YYYY

    ativo = fields.Field(
        column_name='ativo',
        attribute='ativo',
        widget=BooleanWidget(),
        default=True) # Assume True se coluna vazia/ausente

    class Meta:
        model = Funcionario
        # Campos a serem importados/exportados
        fields = ('id', 'nome', 'cpf', 'data_nascimento', 'data_admissao', 'cargo', 'setores', 'centro_servico', 'usuario', 'ativo')
        export_order = ('id', 'nome', 'cpf', 'data_nascimento', 'data_admissao', 'cargo', 'setores', 'centro_servico', 'usuario', 'ativo')
        # Usa CPF para identificar funcionários existentes na importação
        import_id_fields = ['cpf']
        # Pula linhas que não tiveram alteração
        skip_unchanged = True
        # Informa quais linhas foram puladas
        report_skipped = True
        # Se um Cargo, Setor, CentroServico ou Usuario não for encontrado,
        # a linha inteira será pulada e um erro será mostrado na visualização.
        # Defina para False se preferir que ele crie o funcionário mesmo assim (pode dar erro de FK).
        skip_diff = True
        # Coleta erros durante a importação "seca" (dry run)
        collect_failed_rows = True


# --- Admin para Funcionários usando o Resource detalhado ---
@admin.register(Funcionario)
class FuncionarioAdmin(ImportExportModelAdmin):
    resource_class = FuncionarioResource # Usa o Resource customizado
    list_display = ('nome', 'cargo', 'get_setores', 'usuario', 'ativo')
    list_filter = ('ativo', 'setor', 'cargo')
    search_fields = ('nome', 'cpf', 'usuario__username')
    filter_horizontal = ('setor',) # Melhora seleção ManyToMany

    # Método para exibir setores na lista
    def get_setores(self, obj):
        return ", ".join([s.nome for s in obj.setor.all()])
    get_setores.short_description = 'Setores'


# --- Admin para outros modelos (sem import/export ou com config padrão) ---
@admin.register(CentroServico)
class CentroServicoAdmin(admin.ModelAdmin): # Herda de admin.ModelAdmin padrão
    list_display = ('nome', 'setor')
    list_filter = ('setor',)
    search_fields = ('nome',)
    # Se houver muitos Setores, usar raw_id_fields pode melhorar a performance
    # raw_id_fields = ('setor',)

@admin.register(Requisicao)
class RequisicaoAdmin(admin.ModelAdmin): # Herda de admin.ModelAdmin padrão
    list_display = ('titulo', 'solicitante', 'status', 'aprovador', 'criado_em')
    list_filter = ('status', 'solicitante__setor') # Filtra por setor do solicitante
    search_fields = ('titulo', 'solicitante__nome', 'aprovador__nome')
    # Melhora performance para selecionar solicitante/aprovador se houver muitos funcionários
    raw_id_fields = ('solicitante', 'aprovador')
    list_select_related = ('solicitante', 'aprovador', 'solicitante__cargo') # Otimiza consulta
    date_hierarchy = 'criado_em' # Adiciona navegação por data