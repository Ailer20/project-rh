from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from django.contrib.auth.models import User
from .resources import FuncionarioResource
# --- Importação dos Modelos ---
from .models import (
    Cargo, Setor, CentroServico, Vaga, 
    RequisicaoPessoal, MovimentacaoPessoal, RequisicaoDesligamento
    )
from .models_funcionario import Funcionario 


# --- Resources para Cargo e Setor (sem mudanças) ---
class CargoResource(resources.ModelResource):
    class Meta: 
        model = Cargo; fields = ('id', 'nome', 'nivel', 'descricao',); export_order = fields
        import_id_fields = ['nome']; skip_unchanged = True; report_skipped = True
@admin.register(Cargo)
class CargoAdmin(ImportExportModelAdmin): 
    resource_class = CargoResource; list_display = ('nome', 'nivel', 'descricao')
    search_fields = ('nome', 'descricao'); list_filter = ('nivel',)

class SetorResource(resources.ModelResource):
    class Meta: 
        model = Setor; fields = ('id', 'nome', 'descricao',); export_order = fields
        import_id_fields = ['nome']; skip_unchanged = True; report_skipped = True
@admin.register(Setor)
class SetorAdmin(ImportExportModelAdmin): 
    resource_class = SetorResource; list_display = ('nome', 'descricao'); search_fields = ('nome',)



# Pega a lista de campos do Protheus (como você já fez)
protheus_fields = [f.name for f in Funcionario._meta.fields if f.name.startswith('ra_')]

# --- ADMIN DO FUNCIONÁRIO (COM MELHORIAS) ---
@admin.register(Funcionario)
class FuncionarioAdmin(ImportExportModelAdmin):
    # Usa o Resource completo do 'resources.py'
    resource_class = FuncionarioResource
    
    # Configuração da lista (sem mudança)
    list_display = ('ra_mat', 'ra_nome', 'ra_filial', 'cargo', 'setor_primario','ra_centro_custo', 'ativo')
    search_fields = ('ra_mat', 'ra_nome', 'ra_cpf')
    list_filter = ('ra_filial', 'ra_centro_custo', 'ativo')
    
    # --- MELHORIA 1: 'usuario' adicionado ao raw_id_fields ---
    # Deixa o campo 'usuario' consistente com 'cargo' e 'setor_primario'
    raw_id_fields = ('usuario', 'cargo', 'setor_primario')
    
    # --- MELHORIA 2: 'filter_horizontal' adicionado ---
    # Isso corrige o problema da sua imagem, criando um seletor "caixa dupla"
    filter_horizontal = ('setores_responsaveis',)
    
    # --- MELHORIA 3: Fieldsets reorganizados ---
    # Mais limpo, com 'salario_bruto_calculado' em readonly e Protheus recolhido
    fieldsets = (
        ('Vínculo com Aplicativo', {
            'fields': ('usuario', 'ativo')
        }),
        ('Hierarquia e Responsabilidades (App)', {
            'fields': ('cargo', 'setor_primario', 'setores_responsaveis')
        }),
        ('Dados do App (Somente Leitura)', {
            'fields': ('salario_bruto_calculado',)
        }),
        ('Dados do Protheus (Somente Leitura)', {
            # 'collapse' faz esta seção gigante começar recolhida
            'classes': ('collapse',), 
            'fields': protheus_fields 
        }),
    )
    
    # --- MELHORIA 4: Lista de readonly_fields atualizada ---
    # Adicionamos o 'salario_bruto_calculado' para que não seja editável
    readonly_fields = ['salario_bruto_calculado'] + protheus_fields
# --- Admin para outros modelos ---
class CentroServicoResource(resources.ModelResource):
    """
    Ensina o django-import-export a importar/exportar CentroServico.
    """
    
    # Mapeia a coluna 'setor_nome' da planilha para o campo 'setor' (ForeignKey)
    setor = fields.Field(
        column_name='setor_nome', # Nome da coluna na sua planilha
        attribute='setor',
        widget=ForeignKeyWidget(Setor, 'nome') # Procura o Setor pelo campo 'nome'
    )
    
    class Meta:
        model = CentroServico
        # Define os campos que você quer importar/exportar
        fields = ('id', 'nome', 'setor',)
        export_order = fields
        # Usa o campo 'nome' para identificar registros existentes
        import_id_fields = ['nome'] 
        skip_unchanged = True
        report_skipped = True
        
        # Para o widget de Setor funcionar, precisamos buscar o Setor
        # antes de salvar o CentroServico
        use_transactions = True

# --- ✅ ADMIN DO CENTROSERVICO ATUALIZADO ---
@admin.register(CentroServico)
class CentroServicoAdmin(ImportExportModelAdmin): # 1. Mudei para ImportExportModelAdmin
    resource_class = CentroServicoResource      # 2. Adicionei esta linha
    
    # Suas configurações originais (sem mudança)
    list_display = ('nome', 'setor'); 
    list_filter = ('setor',); 
    search_fields = ('nome',); 
    raw_id_fields = ('setor',)

    
@admin.register(Vaga)
class VagaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'setor', 'cargo', 'status')
    list_filter = ('status', 'setor', 'cargo')
    search_fields = ('titulo',)
    raw_id_fields = ('setor', 'cargo', 'criado_por')

# --- ✅ Admin ATUALIZADO para RequisicaoPessoal (COM CORREÇÃO) ---
@admin.register(RequisicaoPessoal)
class RequisicaoPessoalAdmin(admin.ModelAdmin):
    # ✅ CORRIGIDO: usa os campos corretos do modelo RP
    list_display = ('id', 'vaga', 'solicitante', 'status', 'aprovador_atual', 'aprovado_por_gestor', 'aprovado_por_rh')
    list_filter = ('status',)
    search_fields = ('vaga__titulo', 'solicitante__ra_nome')
    # ✅ CORRIGIDO: usa os campos corretos do modelo RP
    raw_id_fields = ('vaga', 'solicitante', 'aprovador_atual', 'aprovado_por_gestor', 'aprovado_por_rh', 'rejeitado_por')

@admin.register(MovimentacaoPessoal)
class MovimentacaoPessoalAdmin(admin.ModelAdmin):
    list_display = ('id', 'funcionario_movido', 'solicitante', 'setor_atual', 'setor_proposto', 'status')
    list_filter = ('status', 'setor_atual', 'setor_proposto')
    search_fields = ('funcionario_movido__ra_nome', 'solicitante__ra_nome') 
    raw_id_fields = ('solicitante', 'funcionario_movido', 'cargo_atual', 'setor_atual', 'cargo_proposto', 'setor_proposto', 'aprovador_gestor_proposto', 'aprovador_gestor_atual', 'aprovador_rh', 'rejeitado_por')

@admin.register(RequisicaoDesligamento)
class RequisicaoDesligamentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'funcionario_desligado', 'solicitante', 'setor_atual', 'tipo_desligamento', 'status')
    list_filter = ('status', 'tipo_desligamento', 'setor_atual')
    search_fields = ('funcionario_desligado__ra_nome', 'solicitante__ra_nome')
    raw_id_fields = ('solicitante', 'funcionario_desligado', 'cargo_atual', 'setor_atual', 'aprovador_atual', 'aprovado_por_gestor', 'aprovado_por_rh', 'rejeitado_por')