# hierarquia/admin.py
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget, DateWidget, BooleanWidget
from .models import Cargo, Setor, CentroServico, Funcionario, Requisicao
from django.contrib.auth.models import User

# --- Resources para Cargo e Setor (sem mudanças) ---
class CargoResource(resources.ModelResource):
    class Meta: model = Cargo; fields = ('id', 'nome', 'nivel', 'descricao',); export_order = fields; import_id_fields = ['nome']; skip_unchanged = True; report_skipped = True
@admin.register(Cargo)
class CargoAdmin(ImportExportModelAdmin): resource_class = CargoResource; list_display = ('nome', 'nivel', 'descricao'); search_fields = ('nome', 'descricao'); list_filter = ('nivel',)

class SetorResource(resources.ModelResource):
    class Meta: model = Setor; fields = ('id', 'nome', 'descricao',); export_order = fields; import_id_fields = ['nome']; skip_unchanged = True; report_skipped = True
@admin.register(Setor)
class SetorAdmin(ImportExportModelAdmin): resource_class = SetorResource; list_display = ('nome', 'descricao'); search_fields = ('nome',)

# --- Resource ATUALIZADO para Funcionários (sem mudanças nesta parte) ---
class FuncionarioResource(resources.ModelResource):
    cargo = fields.Field(column_name='cargo', attribute='cargo', widget=ForeignKeyWidget(Cargo, 'nome'))
    setor_primario = fields.Field(column_name='setor_primario', attribute='setor_primario', widget=ForeignKeyWidget(Setor, 'nome'))
    setores_responsaveis = fields.Field(column_name='setores_responsaveis', attribute='setores_responsaveis', widget=ManyToManyWidget(Setor, field='nome', separator=','))
    centro_servico = fields.Field(column_name='centro_servico', attribute='centro_servico', widget=ForeignKeyWidget(CentroServico, 'nome'))
    usuario = fields.Field(column_name='usuario', attribute='usuario', widget=ForeignKeyWidget(User, User.USERNAME_FIELD))
    data_nascimento = fields.Field(column_name='data_nascimento', attribute='data_nascimento', widget=DateWidget(format='%d/%m/%Y'))
    data_admissao = fields.Field(column_name='data_admissao', attribute='data_admissao', widget=DateWidget(format='%d/%m/%Y'))
    ativo = fields.Field(column_name='ativo', attribute='ativo', widget=BooleanWidget(), default=True)

    class Meta:
        model = Funcionario
        fields = ('id', 'nome', 'cpf', 'data_nascimento', 'data_admissao', 'cargo', 'setor_primario', 'setores_responsaveis', 'centro_servico', 'usuario', 'ativo')
        export_order = fields
        import_id_fields = ['cpf']
        skip_unchanged = True
        report_skipped = True
        skip_diff = True
        collect_failed_rows = True

    def before_import_row(self, row, **kwargs):
        if 'setores_responsaveis' in row and row['setores_responsaveis'] is None:
            row['setores_responsaveis'] = ''


# --- Admin ATUALIZADO para Funcionários (COM CORREÇÕES) ---
@admin.register(Funcionario)
class FuncionarioAdmin(ImportExportModelAdmin):
    resource_class = FuncionarioResource
    list_display = ('nome', 'cargo', 'setor_primario', 'get_setores_responsaveis', 'usuario', 'ativo')
    # --- CORREÇÃO AQUI ---
    list_filter = ('ativo', 'setor_primario', 'cargo', 'setores_responsaveis') # Trocado 'setor' por 'setor_primario' e 'setores_responsaveis'
    search_fields = ('nome', 'cpf', 'usuario__username', 'setor_primario__nome')
    # --- CORREÇÃO AQUI ---
    filter_horizontal = ('setores_responsaveis',) # Trocado 'setor' por 'setores_responsaveis'
    raw_id_fields = ('usuario', 'centro_servico', 'cargo', 'setor_primario') # Adicionado cargo e setor_primario

    def get_setores_responsaveis(self, obj):
        return ", ".join([s.nome for s in obj.setores_responsaveis.all()])
    get_setores_responsaveis.short_description = 'Setores Responsáveis'


# --- Admin para outros modelos (sem mudanças significativas) ---
@admin.register(CentroServico)
class CentroServicoAdmin(admin.ModelAdmin): list_display = ('nome', 'setor'); list_filter = ('setor',); search_fields = ('nome',); raw_id_fields = ('setor',)

# --- Admin ATUALIZADO para Requisição (COM CORREÇÃO) ---
@admin.register(Requisicao)
class RequisicaoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'solicitante', 'get_solicitante_setor', 'status', 'aprovador', 'criado_em')
    # --- CORREÇÃO AQUI ---
    list_filter = ('status', 'solicitante__setor_primario') # Trocado 'solicitante__setor' por 'solicitante__setor_primario'
    search_fields = ('titulo', 'solicitante__nome', 'aprovador__nome')
    raw_id_fields = ('solicitante', 'aprovador')
    list_select_related = ('solicitante', 'aprovador', 'solicitante__cargo', 'solicitante__setor_primario')
    date_hierarchy = 'criado_em'

    def get_solicitante_setor(self, obj):
        if obj.solicitante and obj.solicitante.setor_primario:
            return obj.solicitante.setor_primario.nome
        return "-"
    get_solicitante_setor.short_description = 'Setor Solicitante'
    get_solicitante_setor.admin_order_field = 'solicitante__setor_primario'