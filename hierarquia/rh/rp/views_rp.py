from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from hierarquia.models import RequisicaoPessoal, Funcionario, Cargo, Setor, CentroServico, Vaga # Ajuste nas importações
from hierarquia.rh.mixin.views_mixin import (
    PodeVerMPMixin, PodeVerRDMixin, PodeAprovarMixin,
    Nivel5RequiredMixin, RHDPRequiredMixin, BasePermissionMixin
)
from django import forms
from django.http import HttpResponseForbidden

# --- ✅ NOVAS VIEWS PARA REQUISIÇÃO PESSOAL (RP) ---

class RequisicaoPessoalCreateView(Nivel5RequiredMixin, CreateView):
    model = RequisicaoPessoal
    template_name = 'rh/rp/rp_form.html' # Criar este template
    fields = [ # Campos que o solicitante (Nível <=5) preenche
        'vaga', 'tipo_vaga', 'nome_substituido', 'motivo_substituicao',
        'local_trabalho', 'data_prevista_inicio', 'prazo_contratacao',
        'horario_trabalho', 'justificativa_rp'
    ]
    success_url = reverse_lazy('minhas_rps')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Passa apenas vagas ABERTAS para o formulário
        context['form'].fields['vaga'].queryset = Vaga.objects.filter(status='aberta').order_by('titulo')
        context['titulo_pagina'] = "Abrir Nova Requisição Pessoal"
        return context

    def form_valid(self, form):
        form.instance.solicitante = self.funcionario_logado # Usa o funcionário do Mixin
        # A lógica de 'set_initial_approver' está no método save() do model
        return super().form_valid(form)

class MinhasRequisicoesListView(BasePermissionMixin, ListView):
    model = RequisicaoPessoal
    template_name = 'rh/rp/minhas_rps_list.html' # Criar este template
    context_object_name = 'requisicoes'

    def get_queryset(self):
        return RequisicaoPessoal.objects.filter(solicitante=self.funcionario_logado).order_by('-criado_em')

class AprovarRequisicoesListView(BasePermissionMixin, ListView):
    model = RequisicaoPessoal
    template_name = 'rh/rp/aprovar_rps_list.html'
    context_object_name = 'requisicoes'

    def get_queryset(self):
        # --- ✅ CORREÇÃO APLICADA AQUI ---
        
        # Lista de TODOS os status que significam "aguardando ação do aprovador"
        actionable_statuses = [
            'pendente_gestor',    # Aguardando Gestor (1ª vez)
            'pendente_rh',        # Aguardando RH
            'em_revisao_gestor'   # Aguardando Gestor (após edição do RH)
        ]

        # Mostra RPs que estão esperando aprovação do usuário logado E 
        # que tenham um dos status da lista acima.
        return RequisicaoPessoal.objects.filter(
            aprovador_atual=self.funcionario_logado,
            status__in=actionable_statuses  # Trocamos 'startswith' por '__in'
        ).order_by('criado_em')

class RequisicaoPessoalDetailView(PodeAprovarMixin, DetailView): # Usa o Mixin de permissão
    model = RequisicaoPessoal
    template_name = 'rh/rp/rp_detail.html'
    context_object_name = 'rp'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rp = self.object
        # O Mixin já garante que temos 'self.funcionario_logado'

        # --- ✅ CORREÇÃO APLICADA AQUI ---
        
        # Lista de TODOS os status que significam "aguardando ação"
        actionable_statuses = [
            'pendente_gestor',
            'pendente_rh',
            'em_revisao_gestor'
        ]

        # Verifica se o usuário logado é o aprovador atual E se a RP está em um status de ação.
        context['pode_aprovar_rejeitar'] = (
            rp.aprovador_atual == self.funcionario_logado and
            rp.status in actionable_statuses  # Usamos 'in' em vez de 'startswith'
        )
        return context

# Views baseadas em função para APROVAR e REJEITAR
@login_required(login_url='login')
@require_POST # Garante que só aceita POST
def aprovar_rp_view(request, pk):
    rp = get_object_or_404(RequisicaoPessoal, pk=pk)
    try:
        funcionario_logado = Funcionario.objects.get(usuario=request.user)
    except Funcionario.DoesNotExist:
        messages.error(request, "Funcionário não encontrado.")
        return redirect('dashboard') # Ou outra página

    # --- ✅ CORREÇÃO APLICADA AQUI ---
    actionable_statuses = ['pendente_gestor', 'pendente_rh', 'em_revisao_gestor']
    
    # Validação rigorosa
    if rp.aprovador_atual != funcionario_logado or rp.status not in actionable_statuses:
        messages.error(request, "Você não tem permissão para aprovar esta requisição ou ela não está mais pendente.")
        return redirect('detalhar_rp', pk=rp.pk)

    # Chama o método do modelo para avançar
    rp.avancar_aprovacao(aprovador_que_aprovou=funcionario_logado)

    if rp.status == 'aprovada':
        messages.success(request, f"Requisição Pessoal #{rp.id} aprovada com sucesso!")
        # Notificar RH/DP?
    else:
        messages.info(request, f"Requisição Pessoal #{rp.id} encaminhada para {rp.aprovador_atual.nome}.")
        # Notificar próximo aprovador?

    # --- ✅ CORREÇÃO DE REDIRECT (BÔNUS) ---
    # Removido a URL "hardcoded" 'rh/listar_rps_para_aprovar'
    return redirect('listar_rps_para_aprovar')

@login_required(login_url='login')
@require_POST
def rejeitar_rp_view(request, pk):
    rp = get_object_or_404(RequisicaoPessoal, pk=pk)
    try:
        funcionario_logado = Funcionario.objects.get(usuario=request.user)
    except Funcionario.DoesNotExist:
        messages.error(request, "Funcionário não encontrado.")
        return redirect('dashboard')

    # --- ✅ CORREÇÃO APLICADA AQUI ---
    actionable_statuses = ['pendente_gestor', 'pendente_rh', 'em_revisao_gestor']

    # Validação
    if rp.aprovador_atual != funcionario_logado or rp.status not in actionable_statuses:
        messages.error(request, "Você não tem permissão para rejeitar esta requisição ou ela não está mais pendente.")
        return redirect('detalhar_rp', pk=rp.pk)

    observacao = request.POST.get('observacao', '') # Pega a observação do formulário no rp_detail.html
    if not observacao:
        messages.error(request, "A observação é obrigatória para rejeitar a requisição.")
        # Idealmente, retornar para rp_detail com o erro no formulário
        return redirect('detalhar_rp', pk=rp.pk) 

    # Chama o método do modelo para rejeitar
    # --- ✅ CORREÇÃO DE CAMPO DE OBSERVAÇÃO ---
    # Atualizado para 'observacao_rejeicao' (o novo campo no models.py)
    rp.rejeitar(aprovador_que_rejeitou=funcionario_logado, observacao=observacao)
    messages.warning(request, f"Requisição Pessoal #{rp.id} rejeitada.")
    # Notificar solicitante?

    # --- ✅ CORREÇÃO DE REDIRECT (BÔNUS) ---
    return redirect('listar_rps_para_aprovar')


class RequisicaoPessoalRHUpdateView(RHDPRequiredMixin, UpdateView):
    """
    View exclusiva para o RH editar uma RP e APROVAR ou DEVOLVER ao Gestor.
    """
    model = RequisicaoPessoal
    template_name = 'rh/rp/rp_form_rh_edit.html' 
    context_object_name = 'rp' # No template, use 'object' ou 'rp'
    
    # --- ✅ LISTA DE CAMPOS ATUALIZADA ---
    # Inclui todos os campos da RP que o RH pode querer ajustar
    fields = [
        # Detalhes da Requisição (editáveis pelo RH)
        'tipo_vaga', 
        'nome_substituido', 
        'motivo_substituicao',
        'local_trabalho', 
        'data_prevista_inicio', 
        'prazo_contratacao',
        'horario_trabalho', 
        'justificativa_rp', # Justificativa ORIGINAL (RH pode ajustar/complementar?)

        # Campo específico do RH para devolver ao gestor
        'justificativa_edicao_rh' 
    ]
    # ------------------------------------
    # CAMPOS EXCLUÍDOS INTENCIONALMENTE:
    # - vaga: Mudar a vaga associada pode quebrar o contexto. Melhor cancelar e criar outra.
    # - solicitante: Não pode ser alterado.
    # - criado_em, atualizado_em: Automáticos.
    # - status, aprovador_atual: Gerenciados pela lógica de aprovação.
    # - observacao_rejeicao: Usado apenas na rejeição final.
    # - aprovado_por_*, data_aprovacao_*: Histórico automático.
    # - rejeitado_por, data_rejeicao: Histórico automático.
    
    success_url = reverse_lazy('listar_rps_para_aprovar') 

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Ajusta o campo de justificativa da edição
        just_field = form.fields.get('justificativa_edicao_rh')
        if just_field:
            just_field.required = False # Não é obrigatório se for aprovar direto
            just_field.widget.attrs.update({'rows': 3}) # Menor que a justificativa principal
            just_field.help_text = "Preencha APENAS se for 'Salvar e Devolver ao Gestor'."
        
        # Opcional: Ajustar widgets de outros campos se necessário
        # Ex: Tornar datas DateInput
        date_fields = ['data_prevista_inicio', 'prazo_contratacao']
        for field_name in date_fields:
            if field_name in form.fields:
                 form.fields[field_name].widget = forms.DateInput(attrs={'type': 'date'})

        return form

    # (O resto da view test_func, post continua igual...)
    def test_func(self):
        # Garante que é do RH e que a RP está pendente no RH
        if not super().test_func():
            return False
        # Correção: A instância é self.get_object(), não rp
        rp_instance = self.get_object() 
        return rp_instance.status == 'pendente_rh'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        
        # Validação extra: Só o aprovador atual (do RH) pode mexer
        if self.object.aprovador_atual != self.funcionario_logado:
             return HttpResponseForbidden("Você não é o aprovador atual desta requisição.")

        if 'aprovar' in request.POST:
            # --- Se o RH clicar em "APROVAR" ---
            # Primeiro, salva quaisquer edições feitas no formulário
            if form.is_valid():
                form.save()
            else:
                 # Se houver erro de validação ao tentar aprovar direto, mostra o erro
                 return self.form_invalid(form) 
            
            # Então, avança a aprovação
            self.object.avancar_aprovacao(aprovador_que_aprovou=self.funcionario_logado)
            messages.success(request, f"Requisição Pessoal #{self.object.id} APROVADA com sucesso.")
            return redirect(self.get_success_url())

        elif 'editar_e_devolver' in request.POST:
            # --- Se o RH clicar em "EDITAR E DEVOLVER" ---
            if form.is_valid():
                justificativa = form.cleaned_data.get('justificativa_edicao_rh')
                if not justificativa:
                    form.add_error('justificativa_edicao_rh', 'A justificativa é obrigatória para devolver ao gestor.')
                    return self.form_invalid(form)
                
                # Salva as mudanças feitas no formulário
                form.save() 
                
                # Chama a função do modelo para devolver
                self.object.devolver_para_gestor(
                    rh_editor=self.funcionario_logado,
                    justificativa=justificativa
                )
                messages.info(request, f"Requisição #{self.object.id} atualizada e devolvida para revisão do Gestor.")
                return redirect(self.get_success_url())
            else:
                return self.form_invalid(form)
        
        # Se nenhum botão foi clicado (improvável com POST), volta para o detalhe
        return redirect('detalhar_rp', pk=self.object.pk)


class HistoricoRPListView(BasePermissionMixin, ListView):
    """
    Mostra um histórico de RPs concluídas ('aprovada' ou 'rejeitada')
    com base no perfil do usuário logado.
    """
    model = RequisicaoPessoal
    template_name = 'rh/rp/historico_rps_list.html' # <- Vamos criar este template
    context_object_name = 'requisicoes'
    paginate_by = 20 # Opcional: para paginar a lista

    def get_queryset(self):
        user_func = self.funcionario_logado
        user_nivel = user_func.cargo.nivel
        
        # 1. Define a base de RPs: apenas as finalizadas
        finished_qs = RequisicaoPessoal.objects.filter(
            status__in=['aprovada', 'rejeitada']
        )

        # 2. Verifica se o usuário é do RH/DP
        is_rh_dp = False
        if user_func.setor_primario:
            # Use .upper() para ser case-insensitive
            rh_dp_setores = ['RECURSOS HUMANOS', 'DEPARTAMENTO DE PESSOAL']
            if user_func.setor_primario.nome.upper() in rh_dp_setores:
                 is_rh_dp = True

        # 3. Aplica a lógica de filtro
        
        # REGRA DO RH/DP e DIRETOR (Nível 1): Vêem TUDO
        if is_rh_dp or user_nivel == 1:
            return finished_qs.order_by('-criado_em')
        
        # REGRA DO GESTOR/COORDENADOR (Níveis 2 e 3): Vêem o que eles APROVARAM ou REJEITARAM
        if user_nivel == 2 or user_nivel == 3:
            return finished_qs.filter(
                # Filtra RPs onde o usuário logado está no campo 'aprovado_por_gestor'
                # OU no campo 'rejeitado_por'
                Q(aprovado_por_gestor=user_func) | Q(rejeitado_por=user_func)
            ).distinct().order_by('-criado_em')

        # REGRA DO SUPERVISOR/ADM (Níveis 4 e 5): Vêem o que eles CRIARAM
        if user_nivel == 4 or user_nivel == 5:
            return finished_qs.filter(
                solicitante=user_func
            ).order_by('-criado_em')
        
        # Fallback: Se não for nenhum dos acima, não mostra nada
        return RequisicaoPessoal.objects.none()
            
    def get_context_data(self, **kwargs):
        # Adiciona um título para a página
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Histórico de Requisições Pessoais"
        return context
    