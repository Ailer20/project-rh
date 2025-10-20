from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q
from .models import Funcionario, Cargo, Setor, CentroServico, Requisicao
from datetime import datetime


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
    """View principal do dashboard"""
    try:
        funcionario = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html')
    
    # Dados para o dashboard
    context = {
        'funcionario': funcionario,
        'total_funcionarios': Funcionario.objects.filter(ativo=True).count(),
        'total_cargos': Cargo.objects.count(),
        'total_setores': Setor.objects.count(),
        'requisicoes_pendentes': Requisicao.objects.filter(status='pendente').count(),
    }
    
    return render(request, 'hierarquia/dashboard.html', context)


@login_required(login_url='login')
def listar_funcionarios(request):
    """View para listar funcionários"""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html')
    
    # Filtrar funcionários baseado na hierarquia
    funcionarios = Funcionario.objects.filter(ativo=True)
    
    # Se não for diretor, filtra por setor
    if funcionario_logado.cargo.nivel > 1:
        funcionarios = funcionarios.filter(setor=funcionario_logado.setor)
    
    # Busca por nome
    busca = request.GET.get('busca', '')
    if busca:
        funcionarios = funcionarios.filter(nome__icontains=busca)
    
    context = {
        'funcionario_logado': funcionario_logado,
        'funcionarios': funcionarios,
        'busca': busca,
    }
    
    return render(request, 'hierarquia/listar_funcionarios.html', context)


@login_required(login_url='login')
def cadastrar_funcionario(request):
    """View para cadastrar novo funcionário"""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html')
    
    # Apenas admin pode cadastrar
    if funcionario_logado.cargo.nivel != 1:
        return render(request, 'hierarquia/sem_permissao.html')
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        data_nascimento = request.POST.get('data_nascimento')
        cpf = request.POST.get('cpf')
        data_admissao = request.POST.get('data_admissao')
        cargo_id = request.POST.get('cargo')
        setor_id = request.POST.get('setor')
        centro_servico_id = request.POST.get('centro_servico')
        
        try:
            cargo = Cargo.objects.get(id=cargo_id)
            setor = Setor.objects.get(id=setor_id)
            centro_servico = None
            
            if centro_servico_id:
                centro_servico = CentroServico.objects.get(id=centro_servico_id)
            
            funcionario = Funcionario.objects.create(
                nome=nome,
                data_nascimento=data_nascimento if data_nascimento else None,
                cpf=cpf,
                data_admissao=data_admissao,
                cargo=cargo,
                setor=setor,
                centro_servico=centro_servico,
            )
            
            return redirect('listar_funcionarios')
        except Exception as e:
            context = {
                'funcionario_logado': funcionario_logado,
                'cargos': Cargo.objects.all(),
                'setores': Setor.objects.all(),
                'centros_servico': CentroServico.objects.all(),
                'error': str(e),
            }
            return render(request, 'hierarquia/cadastrar_funcionario.html', context)
    
    context = {
        'funcionario_logado': funcionario_logado,
        'cargos': Cargo.objects.all(),
        'setores': Setor.objects.all(),
        'centros_servico': CentroServico.objects.all(),
    }
    
    return render(request, 'hierarquia/cadastrar_funcionario.html', context)


@login_required(login_url='login')
def detalhar_funcionario(request, funcionario_id):
    """View para detalhar um funcionário"""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html')
    
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    
    # Verificar permissão de visualização
    if funcionario_logado.cargo.nivel > 1 and funcionario.setor != funcionario_logado.setor:
        return render(request, 'hierarquia/sem_permissao.html')
    
    context = {
        'funcionario_logado': funcionario_logado,
        'funcionario': funcionario,
        'superiores': funcionario.obter_superiores(),
        'subordinados': funcionario.obter_subordinados(),
    }
    
    return render(request, 'hierarquia/detalhar_funcionario.html', context)


@login_required(login_url='login')
def listar_requisicoes(request):
    """View para listar requisições"""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html')
    
    # Filtrar requisições baseado na hierarquia
    if funcionario_logado.cargo.nivel == 1:  # Diretor
        requisicoes = Requisicao.objects.all()
    else:
        # Mostra suas próprias requisições e as de seus subordinados
        subordinados = funcionario_logado.obter_subordinados()
        requisicoes = Requisicao.objects.filter(
            Q(solicitante=funcionario_logado) | Q(solicitante__in=subordinados)
        )
    
    # Filtrar por status
    status = request.GET.get('status', '')
    if status:
        requisicoes = requisicoes.filter(status=status)
    
    context = {
        'funcionario_logado': funcionario_logado,
        'requisicoes': requisicoes,
        'status_filter': status,
    }
    
    return render(request, 'hierarquia/listar_requisicoes.html', context)


@login_required(login_url='login')
def criar_requisicao(request):
    """View para criar nova requisição"""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html')
    
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
    
    return render(request, 'hierarquia/criar_requisicao.html', context)


@login_required(login_url='login')
def detalhar_requisicao(request, requisicao_id):
    """View para detalhar uma requisição"""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html')
    
    requisicao = get_object_or_404(Requisicao, id=requisicao_id)
    
    # Verificar permissão
    subordinados = funcionario_logado.obter_subordinados()
    if (requisicao.solicitante != funcionario_logado and 
        requisicao.solicitante not in subordinados and
        funcionario_logado.cargo.nivel > 1):
        return render(request, 'hierarquia/sem_permissao.html')
    
    if request.method == 'POST':
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
        'pode_aprovar': (requisicao.status == 'pendente' and 
                        (requisicao.solicitante in subordinados or funcionario_logado.cargo.nivel == 1)),
    }
    
    return render(request, 'hierarquia/detalhar_requisicao.html', context)


@login_required(login_url='login')
def gerenciar_cargos(request):
    """View para gerenciar cargos"""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html')
    
    # Apenas admin pode gerenciar
    if funcionario_logado.cargo.nivel != 1:
        return render(request, 'hierarquia/sem_permissao.html')
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        nivel = request.POST.get('nivel')
        descricao = request.POST.get('descricao')
        
        cargo = Cargo.objects.create(
            nome=nome,
            nivel=nivel,
            descricao=descricao,
        )
        
        return redirect('gerenciar_cargos')
    
    cargos = Cargo.objects.all()
    
    context = {
        'funcionario_logado': funcionario_logado,
        'cargos': cargos,
    }
    
    return render(request, 'hierarquia/gerenciar_cargos.html', context)


@login_required(login_url='login')
def gerenciar_setores(request):
    """View para gerenciar setores"""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html')
    
    # Apenas admin pode gerenciar
    if funcionario_logado.cargo.nivel != 1:
        return render(request, 'hierarquia/sem_permissao.html')
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao')
        
        setor = Setor.objects.create(
            nome=nome,
            descricao=descricao,
        )
        
        return redirect('gerenciar_setores')
    
    setores = Setor.objects.all()
    
    context = {
        'funcionario_logado': funcionario_logado,
        'setores': setores,
    }
    
    return render(request, 'hierarquia/gerenciar_setores.html', context)
