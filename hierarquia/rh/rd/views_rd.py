# hierarquia/rh/rd/views_rd.py (CORRIGIDO)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
# ✅ CORRIGIDO: Importações de modelo separadas
from hierarquia.models import RequisicaoDesligamento, Setor
from hierarquia.models_funcionario import Funcionario 
from hierarquia.rh.mixin.views_mixin import (
    PodeVerMPMixin, PodeVerRDMixin, PodeAprovarMixin,
    Nivel5RequiredMixin, RHDPRequiredMixin, BasePermissionMixin
)
from django import forms

# --- VIEWS DE REQUISIÇÃO DE DESLIGAMENTO (RD) ---

# --- View para Criar RD ---
class RequisicaoDesligamentoCreateView(Nivel5RequiredMixin, CreateView): # ADMs e superiores podem criar
    model = RequisicaoDesligamento
    template_name = 'rh/rd/rd_form.html' # <- Vamos criar este template
    # Lista de campos que o ADM preenche
    fields = [
        'funcionario_desligado',
        'tipo_desligamento',
        'motivo',
        'data_prevista_desligamento',
        'tipo_aviso',
        'havera_substituicao',
        'justificativa',
        # Campos de entrevista (só RH preenche, então não aqui)
    ]
    success_url = reverse_lazy('minhas_rds') # <- Nova URL

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user_func = self.funcionario_logado

        # --- Filtra 'funcionario_desligado' ---
        # (copiando a mesma lógica da Movimentação Pessoal)
        if not user_func or not user_func.cargo:
             return form # Superuser sem perfil vê tudo (default)
        
        user_nivel = user_func.cargo.nivel
        funcionario_queryset = Funcionario.objects.none()

        if user_nivel == 1 or self.request.user.is_superuser:
            funcionario_queryset = Funcionario.objects.filter(ativo=True)
        elif user_nivel <= 4: 
            allowed_sectors_q = Q()
            if user_func.setor_primario:
                allowed_sectors_q |= Q(setor_primario=user_func.setor_primario)
            setores_responsaveis = user_func.setores_responsaveis.all()
            if setores_responsaveis.exists():
                allowed_sectors_q |= Q(setor_primario__in=setores_responsaveis)
            if allowed_sectors_q:
                funcionario_queryset = Funcionario.objects.filter(allowed_sectors_q, ativo=True).distinct()
            else:
                funcionario_queryset = Funcionario.objects.filter(pk=user_func.pk, ativo=True)
        else: # Nível 5
            if user_func.setor_primario:
                funcionario_queryset = Funcionario.objects.filter(
                    setor_primario=user_func.setor_primario,
                    ativo=True
                )
        
        # ✅ CORRIGIDO: de 'nome' para 'ra_nome'
        form.fields['funcionario_desligado'].queryset = funcionario_queryset.exclude(pk=user_func.pk).order_by('ra_nome')
        # --- Fim do filtro ---

        form.fields['data_prevista_desligamento'].widget = forms.DateInput(attrs={'type': 'date'})
        
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Solicitar Requisição de Desligamento"
        return context

    def form_valid(self, form):
        form.instance.solicitante = self.funcionario_logado
        # A lógica de 'save()' do modelo vai preencher os dados atuais e definir o aprovador
        return super().form_valid(form)

# --- View para Listar Minhas RDs ---
class MinhasDesligamentosListView(BasePermissionMixin, ListView): # Renomeado de MinhasRDsListView
    model = RequisicaoDesligamento
    template_name = 'rh/rd/minhas_rds_list.html' # <- Vamos criar
    context_object_name = 'desligamentos'
    paginate_by = 15

    def get_queryset(self):
        # Mostra RDs solicitadas pelo usuário logado
        return RequisicaoDesligamento.objects.filter(solicitante=self.funcionario_logado).order_by('-criado_em')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Minhas Solicitações de Desligamento"
        return context

# --- View para Listar RDs para Aprovar ---
class AprovarDesligamentosListView(BasePermissionMixin, ListView): # Renomeado de AprovarRDsListView
    model = RequisicaoDesligamento
    template_name = 'rh/rd/aprovar_rds_list.html' # <- Vamos criar
    context_object_name = 'desligamentos'
    paginate_by = 15

    def get_queryset(self):
        # Mostra RDs que estão aguardando aprovação do usuário logado
        return RequisicaoDesligamento.objects.filter(
            aprovador_atual=self.funcionario_logado,
            status__in=['pendente_gestor', 'pendente_rh'] # Apenas status pendentes
        ).order_by('criado_em')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Desligamentos Pendentes de Aprovação"
        return context

# --- View para Detalhar uma RD ---
class RequisicaoDesligamentoDetailView(PodeVerRDMixin, DetailView):
    model = RequisicaoDesligamento
    template_name = 'rh/rd/rd_detail.html' # <- Vamos criar
    context_object_name = 'rd' # Usaremos 'rd' no template

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rd = self.object
        
        # Define se o usuário logado PODE aprovar/rejeitar
        pode_agir = (
            rd.aprovador_atual == self.funcionario_logado and 
            rd.status in ['pendente_gestor', 'pendente_rh']
        )
        context['pode_aprovar_rejeitar'] = pode_agir
        context['titulo_pagina'] = f"Detalhes do Desligamento #{rd.id}"
        return context

# --- Funções para Aprovar e Rejeitar RD ---
@login_required(login_url='login')
@require_POST
def aprovar_rd_view(request, pk):
    rd = get_object_or_404(RequisicaoDesligamento, pk=pk)
    try:
        funcionario_logado = Funcionario.objects.get(usuario=request.user)
    except Funcionario.DoesNotExist:
        messages.error(request, "Funcionário não encontrado.")
        return redirect('dashboard')

    # Validação rigorosa
    if rd.aprovador_atual != funcionario_logado or rd.status not in ['pendente_gestor', 'pendente_rh']:
        messages.error(request, "Você não tem permissão para aprovar esta requisição ou ela não está mais pendente.")
        return redirect('detalhar_rd', pk=rd.pk) # <- Nova URL

    # Chama o método do modelo para avançar
    rd.avancar_aprovacao(aprovador=funcionario_logado)

    if rd.status == 'aprovada':
        messages.success(request, f"Requisição de Desligamento #{rd.id} APROVADA com sucesso.")
        # ✅ CORRIGIDO: de .nome para .ra_nome
        messages.info(request, f"O funcionário {rd.funcionario_desligado.ra_nome} foi desativado do sistema.")
        # Lógica de desativação já está no método avancar_aprovacao do modelo
    else:
        # ✅ CORRIGIDO: de .nome para .ra_nome
        messages.info(request, f"Requisição #{rd.id} encaminhada para {rd.aprovador_atual.ra_nome}.")

    return redirect('listar_rds_para_aprovar') # <- Nova URL

@login_required(login_url='login')
@require_POST
def rejeitar_rd_view(request, pk):
    rd = get_object_or_404(RequisicaoDesligamento, pk=pk)
    try:
        funcionario_logado = Funcionario.objects.get(usuario=request.user)
    except Funcionario.DoesNotExist:
        messages.error(request, "Funcionário não encontrado.")
        return redirect('dashboard')

    # Validação
    if rd.aprovador_atual != funcionario_logado or rd.status not in ['pendente_gestor', 'pendente_rh']:
        messages.error(request, "Você não tem permissão para rejeitar esta requisição ou ela não está mais pendente.")
        return redirect('detalhar_rd', pk=rd.pk) # <- Nova URL

    observacao = request.POST.get('observacao', '')
    if not observacao:
        messages.error(request, "A observação é obrigatória para rejeitar a requisição.")
        return redirect('detalhar_rd', pk=rd.pk) 

    # Chama o método do modelo para rejeitar
    rd.rejeitar(aprovador_que_rejeitou=funcionario_logado, observacao=observacao)
    messages.warning(request, f"Requisição de Desligamento #{rd.id} REJEITADA.")

    return redirect('listar_rds_para_aprovar') # <- Nova URL

class HistoricoRDListView(BasePermissionMixin, ListView):
    """
    Mostra um histórico de RDs concluídas ('aprovada' ou 'rejeitada')
    com base no perfil do usuário logado.
    """
    model = RequisicaoDesligamento
    template_name = 'rh/rd/historico_rds_list.html' # <- Vamos criar
    context_object_name = 'desligamentos'
    paginate_by = 20

    def get_queryset(self):
        user_func = self.funcionario_logado
        
        if not user_func or not user_func.cargo:
            if self.request.user.is_superuser:
                 return RequisicaoDesligamento.objects.filter(status__in=['aprovada', 'rejeitada']).order_by('-criado_em')
            return RequisicaoDesligamento.objects.none()

        user_nivel = user_func.cargo.nivel
        
        # 1. Base: RDs finalizadas
        finished_qs = RequisicaoDesligamento.objects.filter(
            status__in=['aprovada', 'rejeitada']
        )

        # 2. Verifica se é RH/DP
        is_rh_dp = False
        if user_func.setor_primario:
            rh_dp_setores = ['RECURSOS HUMANOS', 'DEPARTAMENTO DE PESSOAL']
            if user_func.setor_primario.nome.upper() in [s.upper() for s in rh_dp_setores]:
                 is_rh_dp = True

        # 3. Aplicar Filtros

        # REGRA 1: RH/DP e Diretor (Nível 1) veem TUDO
        if is_rh_dp or user_nivel == 1 or self.request.user.is_superuser:
            return finished_qs.order_by('-criado_em')
        
        # REGRA 2: Gestor/Coordenador (Nível 2 e 3) veem o que APROVARAM ou REJEITARAM
        if user_nivel == 2 or user_nivel == 3:
            return finished_qs.filter(
                Q(aprovado_por_gestor=user_func) |
                Q(aprovado_por_rh=user_func) | # (Caso um gestor também seja do RH)
                Q(rejeitado_por=user_func)
            ).distinct().order_by('-criado_em')

        # REGRA 3: Solicitante (Nível 4 e 5) veem o que CRIARAM
        if user_nivel >= 4: # Nível 4 e 5
            return finished_qs.filter(
                solicitante=user_func
            ).order_by('-criado_em')
        
        # Fallback
        return RequisicaoDesligamento.objects.none()
            
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Histórico de Desligamentos"
        return context