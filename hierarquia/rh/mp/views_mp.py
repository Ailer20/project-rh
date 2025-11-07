from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from hierarquia.models import MovimentacaoPessoal, Funcionario, Cargo, Setor
from hierarquia.rh.mixin.views_mixin import (
    PodeVerMPMixin, PodeVerRDMixin, PodeAprovarMixin,
    Nivel5RequiredMixin, RHDPRequiredMixin, BasePermissionMixin
)
from django import forms


# --- ✅ NOVAS VIEWS PARA MOVIMENTAÇÃO PESSOAL (MP) ---

# --- View para Criar MP ---
# --- View para Criar MP ---
class MovimentacaoPessoalCreateView(Nivel5RequiredMixin, CreateView): # ADMs e superiores podem criar
    model = MovimentacaoPessoal
    template_name = 'rh/mp/mp_form.html' # <- Vamos criar este template
    # Lista de campos que o ADM preenche
    fields = [
        'funcionario_movido',
        'cargo_proposto',
        'setor_proposto',
        'salario_proposto',
        'data_efetiva',
        'justificativa',
        # 'anexo' # Descomente se adicionar anexo
    ]
    success_url = reverse_lazy('minhas_mps') # <- Nova URL

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user_func = self.funcionario_logado # Vem do BasePermissionMixin
        
        # Se não houver funcionário logado (ex: Superusuário sem perfil), não faz nada
        if not user_func or not user_func.cargo:
            return form

        user_nivel = user_func.cargo.nivel

        # --- Define o queryset base para 'funcionario_movido' ---
        funcionario_queryset = Funcionario.objects.none() # Começa vazio

        if user_nivel == 1 or self.request.user.is_superuser:
            # Nível 1 (Diretor) ou Superuser: Vê TODOS os funcionários ativos
            funcionario_queryset = Funcionario.objects.filter(ativo=True)
        
        elif user_nivel <= 4: 
            # Nível 2 (Gestor), 3 (Coordenador), 4 (Supervisor):
            # Vê funcionários do seu setor primário E dos setores pelos quais é responsável.
            
            # Constrói um filtro Q para os setores
            allowed_sectors_q = Q()
            
            # 1. Adiciona setor primário
            if user_func.setor_primario:
                allowed_sectors_q |= Q(setor_primario=user_func.setor_primario)
                
            # 2. Adiciona setores responsáveis
            setores_responsaveis = user_func.setores_responsaveis.all()
            if setores_responsaveis.exists():
                allowed_sectors_q |= Q(setor_primario__in=setores_responsaveis)
                
            if allowed_sectors_q:
                # Filtra por setores permitidos E que estejam ativos
                funcionario_queryset = Funcionario.objects.filter(allowed_sectors_q, ativo=True).distinct()
            else:
                # Se não tem setor primário nem é responsável, mostra apenas a si mesmo
                funcionario_queryset = Funcionario.objects.filter(pk=user_func.pk, ativo=True)

        else: 
            # Nível 5 (ADM) e outros:
            # Vê APENAS funcionários do seu próprio setor primário (como você pediu).
            if user_func.setor_primario:
                funcionario_queryset = Funcionario.objects.filter(
                    setor_primario=user_func.setor_primario,
                    ativo=True
                )
            # Se Nível 5 não tiver setor, o queryset continua .none() (correto)

        # ✅ --- CORREÇÃO AQUI --- ✅
        # Aplica o queryset filtrado ao campo do formulário, excluindo o próprio usuário
        form.fields['funcionario_movido'].queryset = funcionario_queryset.exclude(pk=user_func.pk).order_by('ra_nome')
        
        # --- Outros campos (manter como estava) ---
        form.fields['cargo_proposto'].queryset = Cargo.objects.order_by('nivel', 'nome')
        form.fields['setor_proposto'].queryset = Setor.objects.order_by('nome')
        form.fields['data_efetiva'].widget = forms.DateInput(attrs={'type': 'date'})
        
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Solicitar Movimentação Pessoal"
        return context

    def form_valid(self, form):
        # Associa o solicitante (quem está logado)
        form.instance.solicitante = self.funcionario_logado
        
        # Pega o funcionário selecionado para preencher dados atuais (opcional)
        funcionario_selecionado = form.cleaned_data.get('funcionario_movido')
        if funcionario_selecionado:
            form.instance.cargo_atual = funcionario_selecionado.cargo
            form.instance.setor_atual = funcionario_selecionado.setor_primario
            # form.instance.salario_atual = ... # Adicionar busca do salário atual
        
        # A lógica de 'set_initial_approver' está no método save() do model
        return super().form_valid(form)

# --- View para Listar Minhas MPs ---
class MinhasMovimentacoesListView(BasePermissionMixin, ListView):
    model = MovimentacaoPessoal
    template_name = 'rh/mp/minhas_mps_list.html' # <- Vamos criar este template
    context_object_name = 'movimentacoes'
    paginate_by = 15

    def get_queryset(self):
        # Mostra MPs solicitadas pelo usuário logado
        return MovimentacaoPessoal.objects.filter(solicitante=self.funcionario_logado).order_by('-criado_em')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Minhas Solicitações de Movimentação"
        return context

# --- View para Listar MPs para Aprovar ---
class AprovarMovimentacoesListView(BasePermissionMixin, ListView):
    model = MovimentacaoPessoal
    template_name = 'rh/mp/aprovar_mps_list.html'
    context_object_name = 'movimentacoes'
    paginate_by = 15

    def get_queryset(self):
        user_func = self.funcionario_logado
        
        # Filtro complexo:
        # 1. Onde eu sou Gestor Proposto E ainda não aprovei
        q_proposto = Q(aprovador_gestor_proposto=user_func) & Q(gestor_proposto_aprovou=False)
        
        # 2. Onde eu sou Gestor Atual E ainda não aprovei
        q_atual = Q(aprovador_gestor_atual=user_func) & Q(gestor_atual_aprovou=False)
        
        # 3. Onde eu sou Aprovador de RH E o status é 'pendente_rh'
        q_rh = Q(aprovador_rh=user_func) & Q(status='pendente_rh')
        
        # Une as condições com OR e filtra por status que não estão finalizados
        return MovimentacaoPessoal.objects.filter(
            q_proposto | q_atual | q_rh
        ).exclude(
            status__in=['aprovada', 'rejeitada']
        ).distinct().order_by('criado_em')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Movimentações Pendentes de Aprovação"
        return context
    

# --- View para Detalhar uma MP ---
class MovimentacaoPessoalDetailView(PodeVerMPMixin, DetailView):

    model = MovimentacaoPessoal
    template_name = 'rh/mp/mp_detail.html'
    context_object_name = 'mp'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mp = self.object
        user_func = self.funcionario_logado
        
        pode_aprovar = False
        pode_rejeitar = False

        # --- DEBUG PRINTS ---
        print("-" * 20)
        
        # ✅ CORRIGIDO AQUI: de .nome para .ra_nome
        print(f"DEBUG: User Func Logado: ID={user_func.id}, Nome={user_func.ra_nome}")
        
        print(f"DEBUG: MP Status: {mp.status}")
        print(f"DEBUG: Aprovador Gestor Atual: {mp.aprovador_gestor_atual}")
        print(f"DEBUG: Gestor Atual Aprovou? {mp.gestor_atual_aprovou}")
        print(f"DEBUG: Aprovador Gestor Proposto: {mp.aprovador_gestor_proposto}")
        print(f"DEBUG: Gestor Proposto Aprovou? {mp.gestor_proposto_aprovou}")
        print(f"DEBUG: Aprovador RH: {mp.aprovador_rh}")
        # --- FIM DEBUG PRINTS ---

        if mp.status == 'pendente_gestores':
            condicao_proposto = (mp.aprovador_gestor_proposto == user_func and not mp.gestor_proposto_aprovou)
            condicao_atual = (mp.aprovador_gestor_atual == user_func and not mp.gestor_atual_aprovou)
            print(f"DEBUG: Condição Proposto OK? {condicao_proposto}")
            print(f"DEBUG: Condição Atual OK? {condicao_atual}")
            if condicao_proposto or condicao_atual:
                pode_aprovar = True
                pode_rejeitar = True

        elif mp.status == 'pendente_rh':
            condicao_rh = (mp.aprovador_rh == user_func)
            print(f"DEBUG: Condição RH OK? {condicao_rh}")
            if condicao_rh:
                pode_aprovar = True
                pode_rejeitar = True
        
        context['pode_aprovar'] = pode_aprovar
        context['pode_rejeitar'] = pode_rejeitar
        context['titulo_pagina'] = f"Detalhes da Movimentação #{mp.id}"
        print(f"DEBUG: Final pode_aprovar={pode_aprovar}, pode_rejeitar={pode_rejeitar}")
        print("-" * 20)
        return context
    
# --- Função para Aprovar MP (ATUALIZADA) ---
@login_required(login_url='login')
@require_POST
def aprovar_mp_view(request, pk):
    mp = get_object_or_404(MovimentacaoPessoal, pk=pk)
    try:
        funcionario_logado = Funcionario.objects.get(usuario=request.user)
    except Funcionario.DoesNotExist:
        messages.error(request, "Funcionário não encontrado.")
        return redirect('dashboard')

    if mp.status == 'pendente_gestores':
        # Verifica se o usuário é um dos gestores pendentes
        if (funcionario_logado == mp.aprovador_gestor_proposto and not mp.gestor_proposto_aprovou) or \
           (funcionario_logado == mp.aprovador_gestor_atual and not mp.gestor_atual_aprovou):
            
            mp.aprovar(aprovador=funcionario_logado) # Chama o método de aprovação de gestor
            
            if mp.status == 'pendente_rh':
                messages.success(request, f"Aprovação registrada. A MP #{mp.id} foi encaminhada ao RH.")
            else:
                messages.success(request, f"Aprovação de gestor registrada para a MP #{mp.id}. Aguardando outra aprovação de gestor.")
        else:
            messages.error(request, "Você não tem permissão para aprovar esta etapa (Gestor).")

    elif mp.status == 'pendente_rh':
        # Verifica se é o aprovador de RH
        if funcionario_logado == mp.aprovador_rh:
            aprovado = mp.aprovar_rh(aprovador_rh=funcionario_logado)
            
            if aprovado:
                messages.success(request, f"Movimentação Pessoal #{mp.id} APROVADA com sucesso!")
                
                # --- Efetivar a Movimentação ---
                try:
                    funcionario = mp.funcionario_movido
                    funcionario.cargo = mp.cargo_proposto
                    funcionario.setor_primario = mp.setor_proposto
                    # Adicione salário se aplicável
                    # funcionario.salario = mp.salario_proposto 
                    funcionario.save()
                    messages.info(request, f"Dados do funcionário {funcionario.ra_nome} atualizados.")
                except Exception as e:
                    messages.error(request, f"Erro ao tentar efetivar a movimentação: {e}")
            else:
                 messages.error(request, "Falha ao processar aprovação do RH.")
        else:
            messages.error(request, "Você não tem permissão para aprovar esta etapa (RH).")

    else:
        messages.error(request, "Esta movimentação não está pendente de aprovação.")

    return redirect('listar_mps_para_aprovar')

# --- Função para Rejeitar MP (Verificar se está correta) ---
@login_required(login_url='login')
@require_POST
def rejeitar_mp_view(request, pk):
    mp = get_object_or_404(MovimentacaoPessoal, pk=pk)
    try:
        funcionario_logado = Funcionario.objects.get(usuario=request.user)
    except Funcionario.DoesNotExist:
        messages.error(request, "Funcionário não encontrado.")
        return redirect('dashboard')

    # --- Lógica de Permissão de Rejeição ATUALIZADA ---
    pode_rejeitar = False
    if mp.status == 'pendente_gestores':
        if (mp.aprovador_gestor_proposto == funcionario_logado and not mp.gestor_proposto_aprovou) or \
           (mp.aprovador_gestor_atual == funcionario_logado and not mp.gestor_atual_aprovou):
            pode_rejeitar = True
    elif mp.status == 'pendente_rh':
        if mp.aprovador_rh == funcionario_logado:
            pode_rejeitar = True
    
    if not pode_rejeitar:
        messages.error(request, "Você não tem permissão para rejeitar esta movimentação.")
        return redirect('detalhar_mp', pk=mp.pk)
    
    observacao = request.POST.get('observacao', '')
    if not observacao:
        messages.error(request, "A observação é obrigatória para rejeitar a movimentação.")
        return redirect('detalhar_mp', pk=mp.pk) 

    mp.rejeitar(aprovador_que_rejeitou=funcionario_logado, observacao=observacao)
    messages.warning(request, f"Movimentação Pessoal #{mp.id} REJEITADA.")

    return redirect('listar_mps_para_aprovar')


class HistoricoMPListView(BasePermissionMixin, ListView):
    """
    Mostra um histórico de MPs concluídas ('aprovada' ou 'rejeitada')
    com base no perfil do usuário logado.
    """
    model = MovimentacaoPessoal
    template_name = 'rh/mp/historico_mps_list.html' # <- Vamos criar
    context_object_name = 'movimentacoes'
    paginate_by = 20

    def get_queryset(self):
        user_func = self.funcionario_logado
        
        # Se não houver funcionário logado (ex: Superusuário sem perfil), não faz nada
        if not user_func or not user_func.cargo:
            if self.request.user.is_superuser:
                 # Superusuário sem perfil vê tudo
                 return MovimentacaoPessoal.objects.filter(status__in=['aprovada', 'rejeitada']).order_by('-criado_em')
            return MovimentacaoPessoal.objects.none()

        user_nivel = user_func.cargo.nivel
        
        # 1. Base: MPs finalizadas
        finished_qs = MovimentacaoPessoal.objects.filter(
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
        # (Lógica adaptada para os múltiplos aprovadores da MP)
        if user_nivel == 2 or user_nivel == 3:
            return finished_qs.filter(
                Q(aprovador_gestor_proposto=user_func) |
                Q(aprovador_gestor_atual=user_func) |
                Q(aprovado_por_rh=user_func) | # (Caso um gestor também seja do RH)
                Q(rejeitado_por=user_func)
            ).distinct().order_by('-criado_em')

        # REGRA 3: Solicitante (Nível 4 e 5) veem o que CRIARAM
        if user_nivel == 4 or user_nivel == 5:
            return finished_qs.filter(
                solicitante=user_func
            ).order_by('-criado_em')
        
        # Fallback
        return MovimentacaoPessoal.objects.none()
            
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Histórico de Movimentações Pessoais"
        return context