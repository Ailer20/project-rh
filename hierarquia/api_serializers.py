# hierarquia/api_serializers.py

from rest_framework import serializers
from .models import (
    Funcionario, Vaga, Cargo, Setor, 
    RequisicaoPessoal, RequisicaoDesligamento, MovimentacaoPessoal
)

# --- Serializers Auxiliares (para mostrar nomes) ---

class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = ['nome', 'nivel']

class SetorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setor
        fields = ['nome']

class VagaSerializer(serializers.ModelSerializer):
    """
    Serializer para a lista de Vagas (usado no dropdown de 'Criar RP')
    """
    class Meta:
        model = Vaga
        fields = ['id', 'titulo', 'status']

# --- Serializers de Funcionário (Lista vs. Detalhe) ---

class FuncionarioSerializer(serializers.ModelSerializer):
    """ Serializer para a LISTA de funcionários (simples) """
    # (Corrigido para usar os nomes dos campos do seu modelo)
    cargo_nome = serializers.CharField(source='cargo.nome', read_only=True)
    setor_nome = serializers.CharField(source='setor_primario.nome', read_only=True)
    
    class Meta:
        model = Funcionario
        fields = ['id', 'ra_nome', 'cargo_nome', 'setor_nome']

class FuncionarioDetailSerializer(serializers.ModelSerializer):
    """ Serializer para os DETALHES de um funcionário (completo) """
    
    # --- CORREÇÃO DEFINITIVA: Usando SerializerMethodField para total segurança contra NULL ---
    # Estes campos serão preenchidos pelos métodos get_cargo_nome, etc.
    cargo_nome = serializers.SerializerMethodField(read_only=True)
    setor_nome = serializers.SerializerMethodField(read_only=True)
    centro_servico_nome = serializers.SerializerMethodField(read_only=True)

    # Métodos de segurança para lidar com relacionamentos nulos (ForeignKey)
    def get_cargo_nome(self, obj):
        # Tenta acessar obj.cargo.nome. Se obj.cargo for nulo, retorna 'N/A'.
        return getattr(getattr(obj, 'cargo', None), 'nome', 'N/A')
    
    def get_setor_nome(self, obj):
        # Tenta acessar obj.setor_primario.nome. Se obj.setor_primario for nulo, retorna 'N/A'.
        return getattr(getattr(obj, 'setor_primario', None), 'nome', 'N/A')

    def get_centro_servico_nome(self, obj):
        # Tenta acessar obj.centro_servico.nome. Se obj.centro_servico for nulo, retorna 'N/A'.
        return getattr(getattr(obj, 'centro_servico', None), 'nome', 'N/A')
    
    # Garantindo que campos de propriedade (como os formatados) também sejam seguros
    ra_dt_admissao_formatada = serializers.CharField(
        read_only=True, 
        default='N/A'
    )
    ra_cpf_formatado = serializers.CharField(
        read_only=True, 
        default='N/A'
    )
    
    class Meta:
        model = Funcionario
        fields = [
            'id', 'ra_nome', 'ativo',
            'cargo_nome', 
            'setor_nome',
            'centro_servico_nome',
            'ra_dt_admissao_formatada',
            'ra_cpf_formatado'
        ]

# --- Serializer Genérico para Ações ---

class RejeitarSerializer(serializers.Serializer):
    """
    Serializer para a ação de Rejeitar (exige uma observação).
    """
    observacao = serializers.CharField(write_only=True, required=True, style={'base_template': 'textarea.html'})

# --- Serializers de Requisição Pessoal (RP) ---

class RequisicaoPessoalSerializer(serializers.ModelSerializer):
    """ Serializer para a LISTA de RPs """
    solicitante_nome = serializers.CharField(source='solicitante.ra_nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    vaga_titulo = serializers.CharField(source='vaga.titulo', read_only=True)

    class Meta:
        model = RequisicaoPessoal
        fields = ['id', 'vaga_titulo', 'solicitante_nome', 'status_display', 'criado_em']

class RequisicaoPessoalDetailSerializer(serializers.ModelSerializer):
    """ Serializer para os DETALHES de uma RP """
    solicitante = FuncionarioSerializer(read_only=True)
    aprovador_atual = FuncionarioSerializer(read_only=True)
    vaga = VagaSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    aprovado_por_gestor = serializers.CharField(source='aprovado_por_gestor.ra_nome', read_only=True, allow_null=True)
    aprovado_por_rh = serializers.CharField(source='aprovado_por_rh.ra_nome', read_only=True, allow_null=True)
    rejeitado_por = serializers.CharField(source='rejeitado_por.ra_nome', read_only=True, allow_null=True)

    class Meta:
        model = RequisicaoPessoal
        fields = '__all__' # Mostra todos os campos do modelo

class RequisicaoPessoalCreateSerializer(serializers.ModelSerializer):
    """ Serializer usado APENAS para criar uma nova RP (o POST) """
    class Meta:
        model = RequisicaoPessoal
        # (Baseado na sua 'views_rp.py')
        fields = [
            'vaga', 'tipo_vaga', 'nome_substituido', 'motivo_substituicao',
            'local_trabalho', 'data_prevista_inicio', 'prazo_contratacao',
            'horario_trabalho', 'justificativa_rp'
        ]

# --- Serializers de Requisição Desligamento (RD) ---

class RequisicaoDesligamentoSerializer(serializers.ModelSerializer):
    """ Serializer para a LISTA de RDs """
    
    # --- CORREÇÃO: Tratamento de Nulos para funcionário e solicitante ---
    solicitante_nome = serializers.CharField(
        source='solicitante.ra_nome', 
        read_only=True, 
        allow_null=True, 
        default='N/A'
    )
    funcionario_nome = serializers.CharField(
        source='funcionario_desligado.ra_nome', 
        read_only=True,
        allow_null=True, 
        default='N/A'
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = RequisicaoDesligamento
        fields = ['id', 'funcionario_nome', 'solicitante_nome', 'status_display', 'data_solicitacao']

class RequisicaoDesligamentoDetailSerializer(serializers.ModelSerializer):
    """ Serializer para os DETALHES de uma RD """
    solicitante = FuncionarioSerializer(read_only=True)
    funcionario_desligado = FuncionarioSerializer(read_only=True)
    aprovador_atual = FuncionarioSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = RequisicaoDesligamento
        fields = '__all__'

class RequisicaoDesligamentoCreateSerializer(serializers.ModelSerializer):
    """ Serializer usado APENAS para criar uma nova RD (o POST) """
    class Meta:
        model = RequisicaoDesligamento
        # (Baseado na sua 'views_rd.py')
        fields = [
            'funcionario_desligado', 'tipo_desligamento', 'data_prevista_desligamento',
            'motivo', 'observacoes_solicitante', 'substituicao_necessaria'
        ]

# --- Serializers de Movimentação Pessoal (MP) ---

class MovimentacaoPessoalSerializer(serializers.ModelSerializer):
    """ Serializer para a LISTA de MPs """
    
    # --- CORREÇÃO: Tratamento de Nulos para funcionário e solicitante ---
    solicitante_nome = serializers.CharField(
        source='solicitante.ra_nome', 
        read_only=True, 
        allow_null=True, 
        default='N/A'
    )
    funcionario_nome = serializers.CharField(
        source='funcionario_movimentado.ra_nome', 
        read_only=True, 
        allow_null=True, 
        default='N/A'
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MovimentacaoPessoal
        fields = ['id', 'funcionario_nome', 'tipo_movimentacao', 'solicitante_nome', 'status_display', 'data_solicitacao']

class MovimentacaoPessoalDetailSerializer(serializers.ModelSerializer):
    """ Serializer para os DETALHES de uma MP """
    solicitante = FuncionarioSerializer(read_only=True)
    funcionario_movimentado = FuncionarioSerializer(read_only=True)
    aprovador_atual = FuncionarioSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MovimentacaoPessoal
        fields = '__all__'

class MovimentacaoPessoalCreateSerializer(serializers.ModelSerializer):
    """ Serializer usado APENAS para criar uma nova MP (o POST) """
    class Meta:
        model = MovimentacaoPessoal
         # (Baseado na sua 'views_mp.py')
        fields = [
            'funcionario_movimentado', 'tipo_movimentacao', 'data_prevista_movimentacao',
            'justificativa', 'cargo_atual', 'setor_atual', 'centro_servico_atual',
            'cargo_proposto', 'setor_proposto', 'centro_servico_proposto'
        ]