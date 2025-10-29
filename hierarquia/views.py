from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q
from .models import Funcionario, Cargo, Setor, CentroServico, Requisicao, Vaga, RequisicaoPessoal
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.decorators.http import require_POST
from datetime import datetime
from django.contrib.auth.models import User, Permission 
# Adicione esta linha inteira
from django import forms
from django.contrib.contenttypes.models import ContentType

def login_view(request):
    """View para login de usuários"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'hierarquia/login.html', {
                'error': 'Usuário ou senha inválidos'
            })
    
    return render(request, 'hierarquia/login.html')


def logout_view(request):
    """View para logout de usuários"""
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def dashboard(request):
    try:
        funcionario = Funcionario.objects.get(usuario=request.user)
        if not funcionario.cargo:
            return render(request, 'hierarquia/sem_acesso.html', {'mensagem': 'Seu usuário não está associado a um cargo.'})
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html', {'mensagem': 'Não foi encontrado um perfil de funcionário associado ao seu usuário.'})

    nivel = funcionario.cargo.nivel

    total_funcionarios_visiveis = 0
    total_cargos_visiveis = 0
    setores_titulo_card = "Informação Setor"
    setores_valor_card = "N/A"
    requisicoes_pendentes_count = 0
    is_setor_name = False

    if nivel == 1:
        total_funcionarios_visiveis = Funcionario.objects.count()
        total_cargos_visiveis = Cargo.objects.count() # Diretor vê todos os cargos
        setores_titulo_card = "Total de Setores"
        setores_valor_card = Setor.objects.count()
        requisicoes_pendentes_count = Requisicao.objects.filter(status='pendente').count()

    elif nivel <= 3:
        setores_responsabilidade = funcionario.setores_responsaveis.all()
        if setores_responsabilidade.exists():
            setores_titulo_card = "Setores Responsáveis"
            setores_valor_card = setores_responsabilidade.count()
            total_funcionarios_visiveis = Funcionario.objects.filter(setor_primario__in=setores_responsabilidade).count()
            # ✅ CORREÇÃO APLICADA AQUI: Filtra Cargo via Funcionarios nos setores responsáveis
            total_cargos_visiveis = Cargo.objects.filter(
                funcionarios__setor_primario__in=setores_responsabilidade
            ).distinct().count()
            requisicoes_pendentes_count = Requisicao.objects.filter(
                solicitante__setor_primario__in=setores_responsabilidade, status='pendente'
            ).count()
        else: # Sem setores responsáveis, usa o próprio setor
            setores_titulo_card = "Meu Setor Principal"
            meu_setor = funcionario.setor_primario
            if meu_setor:
                setores_valor_card = meu_setor.nome
                is_setor_name = True
                total_funcionarios_visiveis = Funcionario.objects.filter(setor_primario=meu_setor).count()
                # ✅ CORREÇÃO APLICADA AQUI: Filtra Cargo via Funcionarios no setor primário
                total_cargos_visiveis = Cargo.objects.filter(
                    funcionarios__setor_primario=meu_setor
                ).distinct().count()
                requisicoes_pendentes_count = Requisicao.objects.filter(solicitante=funcionario, status='pendente').count()
            else: # Sem setor primário
                setores_valor_card = "Nenhum"; is_setor_name = True
                total_funcionarios_visiveis = 1; total_cargos_visiveis = 1 # Apenas o próprio funcionário/cargo
                requisicoes_pendentes_count = Requisicao.objects.filter(solicitante=funcionario, status='pendente').count()

    else: # Níveis 4+
        setores_titulo_card = "Meu Setor Principal"
        meu_setor = funcionario.setor_primario
        if meu_setor:
            setores_valor_card = meu_setor.nome
            is_setor_name = True
            total_funcionarios_visiveis = Funcionario.objects.filter(setor_primario=meu_setor).count()
            # ✅ CORREÇÃO APLICADA AQUI: Filtra Cargo via Funcionarios no setor primário
            total_cargos_visiveis = Cargo.objects.filter(
                funcionarios__setor_primario=meu_setor
            ).distinct().count()
        else:
            setores_valor_card = "Nenhum"; is_setor_name = True
            total_funcionarios_visiveis = 1; total_cargos_visiveis = 1
        requisicoes_pendentes_count = Requisicao.objects.filter(solicitante=funcionario, status='pendente').count()

    context = {
        'funcionario': funcionario,
        'total_funcionarios': total_funcionarios_visiveis,
        'total_cargos': total_cargos_visiveis,
        'setores_titulo_card': setores_titulo_card,
        'setores_valor_card': setores_valor_card,
        'requisicoes_pendentes': requisicoes_pendentes_count,
        'is_setor_name': is_setor_name,
    }

    return render(request, 'hierarquia/dashboard.html', context)

@login_required(login_url='login')
def listar_funcionarios_por_setor(request, setor_id):
    """(ATUALIZADO) View para listar funcionários de um setor específico."""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html')

    setor = get_object_or_404(Setor, id=setor_id)

    # (ATUALIZADO) Verifica permissão: Diretor, ou se é setor primário ou responsável
    permitido = False
    if funcionario_logado.cargo.nivel == 1:
        permitido = True
    elif funcionario_logado.setor_primario == setor:
        permitido = True
    elif funcionario_logado.setores_responsaveis.filter(pk=setor.pk).exists():
        permitido = True

    if not permitido:
         return render(request, 'hierarquia/sem_permissao.html', {'mensagem': f'Você não tem permissão para ver funcionários do setor "{setor.nome}".'})

    # (ATUALIZADO) Filtra funcionários ATIVOS cujo SETOR PRIMÁRIO é o setor específico
    funcionarios = Funcionario.objects.filter(ativo=True, setor_primario=setor)

    busca = request.GET.get('busca', '')
    if busca:
        funcionarios = funcionarios.filter(nome__icontains=busca)

    context = {
        'funcionario_logado': funcionario_logado,
        'funcionarios': funcionarios.order_by('nome'),
        'setor': setor,
        'busca': busca,
    }
    return render(request, 'hierarquia/listar_funcionarios.html', context)

@login_required(login_url='login')
def listar_setores_funcionarios(request):
    """(ATUALIZADO) View para listar os setores que o usuário pode ver."""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html')

    setores_visiveis = Setor.objects.none() # Começa vazio

    if funcionario_logado.cargo.nivel == 1: # Diretor vê todos
        setores_visiveis = Setor.objects.all()
    else:
        # Inclui o setor primário do usuário (se tiver)
        if funcionario_logado.setor_primario:
            setores_visiveis = setores_visiveis | Setor.objects.filter(pk=funcionario_logado.setor_primario.pk)

        # Inclui os setores pelos quais o usuário é responsável
        if funcionario_logado.setores_responsaveis.exists():
            setores_visiveis = setores_visiveis | funcionario_logado.setores_responsaveis.all()

    context = {
        'funcionario_logado': funcionario_logado,
        # Ordena e garante setores únicos
        'setores': setores_visiveis.distinct().order_by('nome'),
    }
    return render(request, 'hierarquia/listar_setores.html', context)


@login_required(login_url='login')
def cadastrar_funcionario(request):
    """(ATUALIZADO) View para cadastrar novo funcionário."""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html')

    if not request.user.has_perm('hierarquia.add_funcionario'):
        return render(request, 'hierarquia/sem_permissao.html')

    if request.method == 'POST':
        # ... (pega nome, cpf, datas, cargo_id)
        nome = request.POST.get('nome')
        data_nascimento = request.POST.get('data_nascimento')
        cpf = request.POST.get('cpf')
        data_admissao = request.POST.get('data_admissao')
        cargo_id = request.POST.get('cargo')
        # --- MUDANÇA ---
        setor_primario_id = request.POST.get('setor_primario') # Pega o ID do setor primário
        setores_responsaveis_ids = request.POST.getlist('setores_responsaveis') # Opcional: Se adicionar campo no form
        centro_servico_id = request.POST.get('centro_servico')
        usuario_username = request.POST.get('usuario') # Opcional: Se adicionar campo no form

        try:
            cargo = Cargo.objects.get(id=cargo_id)
            # --- MUDANÇA ---
            setor_primario = Setor.objects.get(id=setor_primario_id) # Busca o setor primário
            setores_responsaveis = Setor.objects.filter(id__in=setores_responsaveis_ids) # Busca setores responsáveis
            centro_servico = CentroServico.objects.get(id=centro_servico_id) if centro_servico_id else None
            usuario = User.objects.get(username=usuario_username) if usuario_username else None

            # --- MUDANÇA ---
            funcionario = Funcionario.objects.create(
                nome=nome,
                data_nascimento=data_nascimento if data_nascimento else None,
                cpf=cpf,
                data_admissao=data_admissao,
                cargo=cargo,
                setor_primario=setor_primario, # Associa setor primário
                centro_servico=centro_servico,
                usuario=usuario
                # Ativo é default=True
            )
            # Associa setores responsáveis DEPOIS de criar
            if setores_responsaveis.exists():
                funcionario.setores_responsaveis.set(setores_responsaveis)

            # Redireciona para a lista do setor recém-criado
            return redirect('listar_funcionarios_por_setor', setor_id=setor_primario.id)

        except (Cargo.DoesNotExist, Setor.DoesNotExist, CentroServico.DoesNotExist, User.DoesNotExist, Exception) as e:
            # ...(código de tratamento de erro, recarregando o form com os dados)
             context = {
                'funcionario_logado': funcionario_logado,
                'cargos': Cargo.objects.all(),
                'setores': Setor.objects.all(), # Para os selects
                'centros_servico': CentroServico.objects.all(),
                'error': f"Erro ao cadastrar: {e}", # Mensagem de erro mais clara
                # Passar os valores submetidos de volta para o form é uma boa prática
                'form_values': request.POST
            }
             return render(request, 'hierarquia/cadastrar_funcionario.html', context)

    # GET request
    setor_preselecionado_id = request.GET.get('setor_id') # Pega ID da URL se veio do botão "+ Novo"
    context = {
        'funcionario_logado': funcionario_logado,
        'cargos': Cargo.objects.all().order_by('nivel', 'nome'),
        'setores': Setor.objects.all().order_by('nome'),
        'centros_servico': CentroServico.objects.all().order_by('nome'),
        'setor_preselecionado_id': setor_preselecionado_id, # Passa para o template
    }
    return render(request, 'hierarquia/cadastrar_funcionario.html', context)


@login_required(login_url='login')
def detalhar_funcionario(request, funcionario_id):
    """(ATUALIZADO) View para detalhar um funcionário"""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html')

    funcionario = get_object_or_404(Funcionario, id=funcionario_id)

    # (ATUALIZADO) Verificar permissão de visualização
    permitido = False
    if funcionario_logado.cargo.nivel == 1: # Diretor vê tudo
        permitido = True
    elif funcionario.setor_primario: # Se o funcionário visualizado tem setor primário...
        if funcionario_logado.setor_primario == funcionario.setor_primario: # ...e é o mesmo do logado
             permitido = True
        elif funcionario_logado.setores_responsaveis.filter(pk=funcionario.setor_primario.pk).exists(): # ...ou o logado é responsável por ele
             permitido = True
    elif funcionario == funcionario_logado: # Permite ver a si mesmo
        permitido = True


    if not permitido:
        return render(request, 'hierarquia/sem_permissao.html', {'mensagem': f'Você não tem permissão para ver detalhes de {funcionario.nome}.'})

    context = {
        'funcionario_logado': funcionario_logado,
        'funcionario': funcionario,
        'superiores': funcionario.obter_superiores(),
        # Passa False para não incluir subordinados de setores responsáveis aqui, talvez?
        # Ou True para mostrar todos que ele gerencia. Decidi por True.
        'subordinados': funcionario.obter_subordinados(incluir_responsaveis=True),
    }
    return render(request, 'hierarquia/detalhar_funcionario.html', context)


@login_required(login_url='login')
def listar_requisicoes(request):
    """(REVISAR/ATUALIZAR) View para listar requisições"""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html')

    requisicoes = Requisicao.objects.none()

    if funcionario_logado.cargo.nivel == 1:
        requisicoes = Requisicao.objects.all()
    else:
        # Mostra suas próprias requisições
        requisicoes = requisicoes | Requisicao.objects.filter(solicitante=funcionario_logado)
        # Mostra requisições de subordinados (incluindo dos setores responsáveis)
        subordinados = funcionario_logado.obter_subordinados(incluir_responsaveis=True)
        if subordinados.exists():
            requisicoes = requisicoes | Requisicao.objects.filter(solicitante__in=subordinados)

    status = request.GET.get('status', '')
    if status:
        requisicoes = requisicoes.filter(status=status)

    context = {
        'funcionario_logado': funcionario_logado,
        'requisicoes': requisicoes.distinct().order_by('-criado_em'),
        'status_filter': status,
    }
    return render(request, 'hierarquia/listar_requisicoes.html', context)
    

@login_required(login_url='login')
def criar_requisicao(request):
    """View para criar nova requisição"""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'rh/sem_acesso.html')
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        
        requisicao = Requisicao.objects.create(
            titulo=titulo,
            descricao=descricao,
            solicitante=funcionario_logado,
        )
        
        return redirect('listar_requisicoes')
    
    context = {
        'funcionario_logado': funcionario_logado,
    }
    
    return render(request, 'criar_requisicao.html', context)


@login_required(login_url='login')
def detalhar_requisicao(request, requisicao_id):
    """View para detalhar uma requisição"""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'rh/sem_acesso.html')
    
    requisicao = get_object_or_404(Requisicao, id=requisicao_id)
    
    # Verificar permissão
    subordinados = funcionario_logado.obter_subordinados()
    
    # Verifica se o solicitante é o próprio logado OU está na lista de subordinados
    pode_ver = (
        requisicao.solicitante == funcionario_logado or 
        subordinados.filter(id=requisicao.solicitante.id).exists()
    )
    
    if not pode_ver and funcionario_logado.cargo.nivel > 1: # Diretor pode ver tudo
        return render(request, 'rh/sem_permissao.html')
    
    # Define se o usuário pode aprovar
    pode_aprovar = (
        requisicao.status == 'pendente' and
        (subordinados.filter(id=requisicao.solicitante.id).exists() or funcionario_logado.cargo.nivel == 1)
    )

    if request.method == 'POST' and pode_aprovar:
        acao = request.POST.get('acao')
        
        if acao == 'aprovar':
            requisicao.status = 'aprovada'
            requisicao.aprovador = funcionario_logado
            requisicao.data_aprovacao = datetime.now()
            requisicao.save()
        elif acao == 'rejeitar':
            requisicao.status = 'rejeitada'
            requisicao.aprovador = funcionario_logado
            requisicao.data_aprovacao = datetime.now()
            requisicao.save()
        
        return redirect('listar_requisicoes')
    
    context = {
        'funcionario_logado': funcionario_logado,
        'requisicao': requisicao,
        'pode_aprovar': pode_aprovar,
    }
    
    return render(request, 'detalhar_requisicao.html', context)


@login_required(login_url='login')
def gerenciar_cargos(request):
    """View para gerenciar cargos"""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'rh/sem_acesso.html')
    
    # Apenas admin pode gerenciar
    if funcionario_logado.cargo.nivel != 1:
        return render(request, 'rh/sem_permissao.html')
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        nivel = request.POST.get('nivel')
        descricao = request.POST.get('descricao')
        
        cargo = Cargo.objects.create(
            nome=nome,
            nivel=nivel,
            descricao=descricao,
        )
        
        return redirect('hierarquia/gerenciar_cargos')
    
    cargos = Cargo.objects.all()
    
    context = {
        'funcionario_logado': funcionario_logado,
        'cargos': cargos,
        'nivel_choices': Cargo.NIVEL_CHOICES
    }
    
    return render(request, 'hierarquia/gerenciar_cargos.html', context)


@login_required(login_url='login')
def gerenciar_setores(request):
    """View para gerenciar setores"""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'rh/sem_acesso.html')
    
    # Apenas admin pode gerenciar
    if funcionario_logado.cargo.nivel != 1:
        return render(request, 'rh/sem_permissao.html')
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao')
        
        setor = Setor.objects.create(
            nome=nome,
            descricao=descricao,
        )
        
        return redirect('hierarquia/gerenciar_setores')
    
    setores = Setor.objects.all()
    
    context = {
        'funcionario_logado': funcionario_logado,
        'setores': setores,
    }
    
    return render(request, 'hierarquia/gerenciar_setores.html', context)

# --- MIXINS DE PERMISSÃO (REUTILIZÁVEIS) ---

class BasePermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin base para verificar se o usuário tem um funcionário associado."""
    login_url = reverse_lazy('login')

    def handle_no_permission(self):
        # Redireciona para login ou página de erro
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        # Se está autenticado mas não tem permissão/funcionário
        return render(self.request, 'rh/sem_acesso.html', {'mensagem': getattr(self, 'permission_denied_message', 'Acesso negado.')})

    def test_func(self):
        try:
            self.funcionario_logado = Funcionario.objects.get(usuario=self.request.user)
            return True
        except Funcionario.DoesNotExist:
            self.permission_denied_message = 'Não foi encontrado um perfil de funcionário associado ao seu usuário.'
            return False

class RHDPRequiredMixin(BasePermissionMixin):
    """ Garante que o usuário logado pertence ao RH ou DP """
    permission_denied_message = 'Acesso restrito ao RH/Departamento Pessoal.'
    def test_func(self):
        if not super().test_func(): return False # Verifica se tem funcionário
        # Verifica se o setor primário existe e se o nome é RH ou DP
        return self.funcionario_logado.setor_primario and self.funcionario_logado.setor_primario.nome in ['RECURSOS HUMANOS', 'DEPARTAMENTO DE PESSOAL']

class Nivel5RequiredMixin(BasePermissionMixin):
    """ Garante que o usuário logado tem nível 5 (ADM/Analista) ou superior (1 a 4)"""
    permission_denied_message = 'Acesso restrito a Administradores/Analistas ou superiores.'
    def test_func(self):
        if not super().test_func(): return False
        # Permite Nível 5 e também níveis superiores (1 a 4), pois eles também podem iniciar RPs
        return self.funcionario_logado.cargo and self.funcionario_logado.cargo.nivel <= 5

class PodeAprovarMixin(BasePermissionMixin):
    """ Verifica se o usuário pode ver/interagir com uma RP específica """
    permission_denied_message = 'Você não tem permissão para acessar esta requisição.'

    def test_func(self):
        if not super().test_func(): return False
        rp = self.get_object() # Pega a RP da DetailView ou UpdateView
        
        # Condições para ver:
        # 1. É o solicitante?
        # 2. É o aprovador atual?
        # 3. É um superior hierárquico (Nível 1, 2, 3) do solicitante? (Simplificado aqui)
        # 4. Pertence ao RH/DP (podem ver todas?) - Adicionar essa regra se necessário
        
        e_solicitante = (rp.solicitante == self.funcionario_logado)
        e_aprovador_atual = (rp.aprovador_atual == self.funcionario_logado)
        
        # Lógica básica de superior (pode precisar ser mais robusta)
        e_superior = False
        if rp.solicitante.cargo and self.funcionario_logado.cargo:
            e_superior = self.funcionario_logado.cargo.nivel < rp.solicitante.cargo.nivel
            # Idealmente, verificar se está na cadeia hierárquica do solicitante

        return e_solicitante or e_aprovador_atual or e_superior or self.funcionario_logado.cargo.nivel == 1


# --- ✅ NOVAS VIEWS PARA VAGAS ---

class VagaListView(RHDPRequiredMixin, ListView):
    model = Vaga
    template_name = 'rh/vaga_list.html' # Criar este template
    context_object_name = 'vagas'
    ordering = ['-criado_em']

class VagaCreateView(RHDPRequiredMixin, CreateView):
    model = Vaga
    template_name = 'rh/vaga_form.html' # Criar este template
    fields = [ # Liste os campos do seu modelo Vaga
        'titulo', 'setor', 'cargo', 'centro_custo', 'tipo_contratacao',
        'faixa_salarial_inicial', 'faixa_salarial_final', 'requisitos_tecnicos',
        'requisitos_comportamentais', 'principais_atividades', 'formacao_academica',
        'beneficios', 'justificativa', 'status',
    ]
    success_url = reverse_lazy('listar_vagas')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Criar Nova Vaga"
        return context

class VagaUpdateView(RHDPRequiredMixin, UpdateView):
    model = Vaga
    template_name = 'rh/vaga_form.html'
    fields = [ # Mesmos campos do CreateView
        'titulo', 'setor', 'cargo', 'centro_custo', 'tipo_contratacao',
        'faixa_salarial_inicial', 'faixa_salarial_final', 'requisitos_tecnicos',
        'requisitos_comportamentais', 'principais_atividades', 'formacao_academica',
        'beneficios', 'justificativa', 'status',
    ]
    success_url = reverse_lazy('listar_vagas')

    def form_valid(self, form):
        messages.success(self.request, f"Vaga '{form.instance.titulo}' atualizada com sucesso.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Editar Vaga"
        return context

class VagaDetailView(RHDPRequiredMixin, DetailView):
    model = Vaga
    template_name = 'rh/vaga_detail.html' # Criar este template (Opcional)
    context_object_name = 'vaga'

# --- ✅ NOVAS VIEWS PARA REQUISIÇÃO PESSOAL (RP) ---

class RequisicaoPessoalCreateView(Nivel5RequiredMixin, CreateView):
    model = RequisicaoPessoal
    template_name = 'rh/rp_form.html' # Criar este template
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
        messages.success(self.request, "Requisição Pessoal aberta e enviada para aprovação.")
        return super().form_valid(form)

class MinhasRequisicoesListView(BasePermissionMixin, ListView):
    model = RequisicaoPessoal
    template_name = 'rh/minhas_rps_list.html' # Criar este template
    context_object_name = 'requisicoes'

    def get_queryset(self):
        return RequisicaoPessoal.objects.filter(solicitante=self.funcionario_logado).order_by('-criado_em')

class AprovarRequisicoesListView(BasePermissionMixin, ListView):
    model = RequisicaoPessoal
    template_name = 'rh/aprovar_rps_list.html'
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
    template_name = 'rh/rp_detail.html'
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
    template_name = 'rh/rp_form_rh_edit.html' 
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
    template_name = 'rh/historico_rps_list.html' # <- Vamos criar este template
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