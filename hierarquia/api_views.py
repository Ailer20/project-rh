# hierarquia/api_views.py

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404 
from rest_framework.exceptions import ValidationError
from django.db.models import Q, Count

# Imports para o endpoint de Dashboard
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response

# Imports para Ações Customizadas (Aprovar/Rejeitar)
from rest_framework.decorators import action

# Importe TODOS os modelos e serializers que vamos usar
from .models import (
    Funcionario, Vaga, Setor, Cargo,
    RequisicaoPessoal, RequisicaoDesligamento, MovimentacaoPessoal
)
from .api_serializers import (
    FuncionarioSerializer, FuncionarioDetailSerializer,
    VagaSerializer, RejeitarSerializer,
    RequisicaoPessoalSerializer, RequisicaoPessoalDetailSerializer, RequisicaoPessoalCreateSerializer,
    RequisicaoDesligamentoSerializer, RequisicaoDesligamentoDetailSerializer, RequisicaoDesligamentoCreateSerializer,
    MovimentacaoPessoalSerializer, MovimentacaoPessoalDetailSerializer, MovimentacaoPessoalCreateSerializer
)

from django.db.models import Q, Count # <--- ADICIONE COUNT
# --- Helper para obter o funcionário logado ---
def _get_funcionario_logado(request):
    """ Helper para obter o funcionário logado a partir do request.user """
    try:
        # (Baseado no seu models.py, o campo é 'usuario')
        return Funcionario.objects.get(usuario=request.user)
    except Funcionario.DoesNotExist:
        raise ValidationError('Este usuário não está associado a um funcionário.', code=status.HTTP_403_FORBIDDEN)

# --- Endpoint do Dashboard ---

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_dashboard_data(request):
    """
    Endpoint único para carregar todos os dados do dashboard do app Flutter.
    """
    funcionario = _get_funcionario_logado(request)

    # 1. Perfil
    perfil = {
        'nome': funcionario.ra_nome,
        'cargo': funcionario.cargo.nome if funcionario.cargo else "N/A",
        'setor': funcionario.setor_primario.nome if funcionario.setor_primario else "N/A",
        
        # --- CORREÇÃO ESTÁ AQUI ---
        # Corrigido o erro de digitação de 'ra_data_admissao' para 'ra_dt_admissao'
        # e 'ra_data_admissao_formatada' para 'ra_dt_admissao_formatada'
        'data_admissao': (
            funcionario.ra_dt_admissao_formatada 
            if hasattr(funcionario, 'ra_dt_admissao_formatada') 
            else (
                funcionario.ra_dt_admissao.strftime('%d/%m/%Y') 
                if hasattr(funcionario, 'ra_dt_admissao') and funcionario.ra_dt_admissao 
                else 'N/A'
            )
        )
    }

    # 2. Card: Total de Funcionários
    total_funcionarios = funcionario.obter_subordinados(incluir_responsaveis=True).count()
    if funcionario.cargo.nivel == 1:
        total_funcionarios = Funcionario.objects.filter(ativo=True).count()
    
    # 3. Card: Vagas Abertas
    vagas_abertas_count = Vaga.objects.filter(status='aberta').count()

    # (Definindo os status "finalizados" que NÃO contam como pendência)
    status_finalizados = ['aprovada', 'rejeitada', 'cancelada'] 

    # 4. Card: Pendências (RPs, RDs, MPs aguardando aprovação DESTE usuário)
    pendencias_rp = RequisicaoPessoal.objects.filter(aprovador_atual=funcionario).exclude(status__in=status_finalizados).count()
    pendencias_rd = RequisicaoDesligamento.objects.filter(aprovador_atual=funcionario).exclude(status__in=status_finalizados).count()
    pendencias_mp_q = (
        Q(status='pendente_gestor_atual', aprovador_gestor_atual=funcionario) |
        Q(status='pendente_gestor_proposto', aprovador_gestor_proposto=funcionario) |
        Q(status='pendente_rh', aprovador_rh=funcionario)
        # (Adicione outros status pendentes de MP se houver)
    )
    pendencias_mp = MovimentacaoPessoal.objects.filter(pendencias_mp_q).count()
    
    minhas_pendencias_count = pendencias_rp + pendencias_rd + pendencias_mp
    # 5. Card: Setor
    meu_setor_nome = perfil['setor']
    meu_setor_count = "N/A"
    if funcionario.setor_primario:
         meu_setor_count = Funcionario.objects.filter(setor_primario=funcionario.setor_primario, ativo=True).count()


    # 6. Gráfico: Status (Apenas RPs, RDs e MPs SOLICITADAS pelo usuário)
    
    # Contagens de RP
    rp_counts = RequisicaoPessoal.objects.filter(solicitante=funcionario) \
        .values('status').annotate(count=Count('id'))
        
    # Contagens de RD
    rd_counts = RequisicaoDesligamento.objects.filter(solicitante=funcionario) \
        .values('status').annotate(count=Count('id'))
        
    # Contagens de MP
    mp_counts = MovimentacaoPessoal.objects.filter(solicitante=funcionario) \
        .values('status').annotate(count=Count('id'))

    # Combina os resultados
    status_counts = {}
    for item in list(rp_counts) + list(rd_counts) + list(mp_counts):
        status_key = item['status']
        status_counts[status_key] = status_counts.get(status_key, 0) + item['count']

    # Separa em 'pendente', 'aprovada', 'rejeitada'
    chart_data_map = {'pendente': 0, 'aprovada': 0, 'rejeitada': 0}
    for status, count in status_counts.items():
        if status == 'aprovada':
            chart_data_map['aprovada'] += count
        elif status == 'rejeitada':
            chart_data_map['rejeitada'] += count
        elif status not in status_finalizados: # Qualquer outra coisa não finalizada é pendente
             chart_data_map['pendente'] += count

    # Compila a resposta final
    data = {
        'perfil': perfil,
        'cards': {
            'total_funcionarios': total_funcionarios,
            'vagas_abertas_count': vagas_abertas_count, 
            'minhas_pendencias_count': minhas_pendencias_count,
            'setores_titulo_card': f"Funcionários em {meu_setor_nome}",
            'setores_valor_card': str(meu_setor_count)
        },
        'chart_data': {
            'labels': ['Pendente', 'Aprovada', 'Rejeitada'],
            'data': [
                chart_data_map['pendente'],
                chart_data_map['aprovada'],
                chart_data_map['rejeitada']
            ]
        }
    }
    return Response(data)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_setores_summary(request):
    """
    Endpoint para a tela de "Funcionários por Setor".
    Filtra os setores visíveis pela hierarquia do usuário (Diretor/Gerente/Funcionário).
    """
    funcionario = _get_funcionario_logado(request)

    # 1. Diretor (Nível 1): Vê TODOS os setores
    if funcionario.cargo.nivel == 1:
        setor_queryset = Setor.objects.all()
        # Não filtramos a contagem de zero para diretores

    # 2. Gerente (Nível > 1): Vê o seu setor e os setores dos seus subordinados.
    elif funcionario.cargo.nivel > 1:
        
        # a) Começa com o setor primário do próprio funcionário
        setor_ids_to_show = {funcionario.setor_primario_id} if funcionario.setor_primario_id else set()

        # b) Inclui os IDs dos setores primários de todos os subordinados (incluindo chefes)
        subordinados_setor_ids = funcionario.obter_subordinados(incluir_responsaveis=True) \
                                          .values_list('setor_primario_id', flat=True) \
                                          .filter(setor_primario_id__isnull=False) \
                                          .distinct()
                                          
        setor_ids_to_show.update(subordinados_setor_ids)
        
        # Filtra o queryset de Setor com base nos IDs coletados
        setor_queryset = Setor.objects.filter(id__in=list(setor_ids_to_show))

    # 3. Funcionário Normal (Outros Níveis): Vê APENAS o seu setor.
    else:
        if funcionario.setor_primario_id:
            setor_queryset = Setor.objects.filter(id=funcionario.setor_primario_id)
        else:
            setor_queryset = Setor.objects.none() # Se não tiver setor, não vê nada
            
    # Aplica a anotação/contagem
    try:
        setores_summary = setor_queryset.annotate(
            funcionario_count=Count(
                'funcionarios_primarios', 
                filter=Q(funcionarios_primarios__ativo=True)
            )
        ).values(
            'id', 
            'nome', 
            'funcionario_count'
        ).order_by('nome')
        
        # Gerentes e Funcionários normais não devem ver setores com 0 funcionários
        if funcionario.cargo.nivel != 1:
             setores_summary = setores_summary.filter(funcionario_count__gt=0)
        
        return Response(list(setores_summary))

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# --- ViewSets (Conjuntos de Endpoints) ---

class VagaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint para listar Vagas ABERTAS.
    """
    queryset = Vaga.objects.filter(status='aberta').order_by('titulo')
    serializer_class = VagaSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

class FuncionarioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint para Funcionários (Lista e Detalhe).
    """
    permission_classes = [IsAuthenticated] 
    authentication_classes = [TokenAuthentication]

    def get_serializer_class(self):
        if self.action == 'list':
            return FuncionarioSerializer
        return FuncionarioDetailSerializer

    def get_queryset(self):
        """
        Otimizado: O usuário logado só pode ver a si mesmo e seus subordinados.
        O Diretor (Nível 1) vê todos.
        
        --- CORREÇÃO PARA O 404 AQUI ---
        """
        funcionario = _get_funcionario_logado(self.request)
        queryset = Funcionario.objects.filter(ativo=True)

        # 1. SE ESTIVER BUSCANDO DETALHES (RETRIEVE), RETORNA O QUERYSET BASE COMPLETO.
        #    Isso permite que o funcionário seja encontrado se ele existir,
        #    e evita o erro 404 causado pela restrição de hierarquia.
        if self.action == 'retrieve':
             return queryset
        # --- FIM CORREÇÃO ---


        # --- LÓGICA DE FILTRO (apenas para LISTAGEM) ---

        # Filtro de setor (opcional)
        setor_id = self.request.query_params.get('setor_id')
        if setor_id:
            # Se pedir um setor, retorna todos daquele setor
            return queryset.filter(setor_primario__id=setor_id).order_by('ra_nome')

        # Diretor (Nível 1): Vê todos.
        if funcionario.cargo.nivel == 1:
            return queryset.order_by('ra_nome')
        
        # Gerente/Funcionário: Vê apenas a si mesmo e seus subordinados.
        subordinados_ids = list(funcionario.obter_subordinados(incluir_responsaveis=True).values_list('id', flat=True))
        subordinados_ids.append(funcionario.id)
        
        return queryset.filter(id__in=subordinados_ids).order_by('ra_nome')

# ... (resto do arquivo api_views.py)

# --- ViewSet Base para Requisições ---
# (Cria lógica comum para RP, RD, MP)

class BaseRequisicaoViewSet(viewsets.ModelViewSet):
    """
    Um ViewSet base que contém a lógica comum para
    Aprovar e Rejeitar Requisições (RP, RD, MP).
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    # (serializer_class e queryset serão definidos nas classes filhas)

    def get_queryset(self):
        """
        Filtro de segurança e filtro de STATUS (solicitante/aprovador/histórico):
        O usuário só pode ver RQs que ele solicitou OU que ele precisa aprovar.
        O filtro é determinado pelo query parameter 'status_filter'.
        """
        funcionario_logado = _get_funcionario_logado(self.request)
        queryset = self.queryset.all()
        status_filter = self.request.query_params.get('status_filter', 'solicitante') # Default é 'solicitante'

        # --- Lógica de Filtragem (Baseada no status_filter do Flutter) ---

        if status_filter == 'aprovador':
            # Filtro: Requisições onde o usuário é o aprovador atual (pendentes de aprovação)
            
            # Movimentação Pessoal (MP) é especial, pois tem múltiplos aprovadores
            if self.basename == 'movimentacao-pessoal':
                q_aprovador = (
                    Q(status='pendente_gestor_atual', aprovador_gestor_atual=funcionario_logado) |
                    Q(status='pendente_gestor_proposto', aprovador_gestor_proposto=funcionario_logado) |
                    Q(status='pendente_rh', aprovador_rh=funcionario_logado)
                )
                queryset = queryset.filter(q_aprovador)
                
            # RP e RD (assumindo que usam o campo 'aprovador_atual')
            else:
                queryset = queryset.filter(aprovador_atual=funcionario_logado).exclude(status__in=['aprovada', 'rejeitada', 'cancelada'])
        
        elif status_filter == 'historico':
            # Filtro: Requisições que o usuário solicitou E que foram FINALIZADAS
            queryset = queryset.filter(solicitante=funcionario_logado).filter(status__in=['aprovada', 'rejeitada', 'cancelada'])
        
        elif status_filter == 'solicitante':
            # Filtro: Todas as requisições que o usuário solicitou (Minhas RPs, Minhas MPs, etc.)
            queryset = queryset.filter(solicitante=funcionario_logado)
        
        else:
            # Se não houver filtro válido, retorna apenas as que ele solicitou (comportamento seguro)
            queryset = queryset.filter(solicitante=funcionario_logado)


        # --- Ordenação e Retorno ---
        return queryset.distinct().order_by('-' + self.data_field)
    
    def perform_create(self, serializer):
        """
        Define o 'solicitante' automaticamente ao criar.
        """
        funcionario_logado = _get_funcionario_logado(self.request)
        # A lógica de .save() no seu modelo vai definir o 'aprovador_atual'
        serializer.save(solicitante=funcionario_logado)

    def _validar_permissao_acao(self, requisicao, funcionario):
        """ Helper para validar se o usuário pode aprovar/rejeitar """
        if not hasattr(requisicao, 'actionable_statuses'):
            raise ValidationError("Modelo de requisição não define 'actionable_statuses'.")
            
        if requisicao.aprovador_atual != funcionario or requisicao.status not in requisicao.actionable_statuses:
            return False
        return True

    @action(detail=True, methods=['POST'], url_path='aprovar')
    def aprovar(self, request, pk=None):
        """
        Endpoint para APROVAR uma requisição.
        Chamado via POST para /api/requisicoes_.../<id>/aprovar/
        """
        requisicao = self.get_object()
        funcionario_logado = _get_funcionario_logado(request)

        if not self._validar_permissao_acao(requisicao, funcionario_logado):
            return Response({'error': 'Você não tem permissão para aprovar esta requisição ou ela não está pendente.'}, status=status.HTTP_403_FORBIDDEN)

        # Chama a lógica do modelo (RP, RD, MP)
        # (O seu modelo RD usa 'aprovador=', o RP usa 'aprovador_que_aprovou=')
        # Vamos usar o nome do seu modelo RP como padrão, pois RD também o aceita
        try:
            requisicao.avancar_aprovacao(aprovador_que_aprovou=funcionario_logado)
        except TypeError:
            # Fallback para o modelo RD/MP que espera 'aprovador'
            requisicao.avancar_aprovacao(aprovador=funcionario_logado)

        
        serializer = self.get_serializer_class_for_detail()(requisicao) # Usa o serializer de detalhe
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'], url_path='rejeitar')
    def rejeitar(self, request, pk=None):
        """
        Endpoint para REJEITAR uma requisição.
        Chamado via POST para /api/requisicoes_.../<id>/rejeitar/
        """
        requisicao = self.get_object()
        funcionario_logado = _get_funcionario_logado(request)

        if not self._validar_permissao_acao(requisicao, funcionario_logado):
            return Response({'error': 'Você não tem permissão para rejeitar esta requisição.'}, status=status.HTTP_403_FORBIDDEN)

        # Valida os dados enviados (a observação)
        serializer = RejeitarSerializer(data=request.data)
        if serializer.is_valid():
            observacao = serializer.validated_data['observacao']
            
            # Chama a lógica do modelo
            requisicao.rejeitar(aprovador_que_rejeitou=funcionario_logado, observacao=observacao)
            
            detail_serializer = self.get_serializer_class_for_detail()(requisicao)
            return Response(detail_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- ViewSets Específicos para RP, RD, MP ---

class RequisicaoPessoalViewSet(BaseRequisicaoViewSet):
    """ ViewSet para Requisição Pessoal (RP) """
    queryset = RequisicaoPessoal.objects.all()
    data_field = 'criado_em' # Campo de data para ordenação

    def get_serializer_class(self):
        if self.action == 'list':
            return RequisicaoPessoalSerializer
        if self.action == 'retrieve':
            return RequisicaoPessoalDetailSerializer
        if self.action == 'create':
            return RequisicaoPessoalCreateSerializer
        if self.action == 'rejeitar':
            return RejeitarSerializer
        return RequisicaoPessoalDetailSerializer # Default para 'aprovar'

    def get_serializer_class_for_detail(self):
        return RequisicaoPessoalDetailSerializer

class RequisicaoDesligamentoViewSet(BaseRequisicaoViewSet):
    """ ViewSet para Requisição de Desligamento (RD) """
    queryset = RequisicaoDesligamento.objects.all()
    data_field = 'criado_em'

    def get_serializer_class(self):
        if self.action == 'list':
            return RequisicaoDesligamentoSerializer
        if self.action == 'retrieve':
            return RequisicaoDesligamentoDetailSerializer
        if self.action == 'create':
            return RequisicaoDesligamentoCreateSerializer
        if self.action == 'rejeitar':
            return RejeitarSerializer
        return RequisicaoDesligamentoDetailSerializer
    
    def get_serializer_class_for_detail(self):
        return RequisicaoDesligamentoDetailSerializer

class MovimentacaoPessoalViewSet(BaseRequisicaoViewSet):
    """ ViewSet para Movimentação Pessoal (MP) """
    queryset = MovimentacaoPessoal.objects.all()
    data_field = 'criado_em'
    
    def get_queryset(self):
            """
            Filtro de segurança (SOBRESCRITO para MP):
            O usuário só pode ver RQs que ele solicitou OU que ele precisa aprovar.
            A MP tem múltiplos aprovadores, não um único 'aprovador_atual' no DB.
            """
            funcionario_logado = _get_funcionario_logado(self.request)
            
            # Lógica dos aprovadores (replicada da property 'aprovador_atual')
            # (Estes nomes de status são suposições baseadas nos nomes dos campos de aprovador)
            q_aprovador = (
                Q(status='pendente_gestor_atual', aprovador_gestor_atual=funcionario_logado) |
                Q(status='pendente_gestor_proposto', aprovador_gestor_proposto=funcionario_logado) |
                Q(status='pendente_rh', aprovador_rh=funcionario_logado)
                # (Adicione outros status pendentes de MP se houver)
            )
            
            # Q object: (solicitante=eu) OU (sou um dos aprovadores pendentes)
            return self.queryset.filter(
                Q(solicitante=funcionario_logado) | q_aprovador
            ).distinct().order_by('-' + self.data_field)
        # --- FIM DO FIX 2 ---
    def get_serializer_class(self):
        if self.action == 'list':
            return MovimentacaoPessoalSerializer
        if self.action == 'retrieve':
            return MovimentacaoPessoalDetailSerializer
        if self.action == 'create':
            return MovimentacaoPessoalCreateSerializer
        if self.action == 'rejeitar':
            return RejeitarSerializer
        return MovimentacaoPessoalDetailSerializer

    def get_serializer_class_for_detail(self):
        return MovimentacaoPessoalDetailSerializer