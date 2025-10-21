from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q
from .models import Funcionario, Cargo, Setor, CentroServico, Requisicao
from datetime import datetime
from django.contrib.auth.models import User, Permission 

# Adicione esta linha inteira
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
def listar_funcionarios_por_setor(request, setor_id): # Nome e parâmetro alterados
    """View para listar funcionários DE UM SETOR ESPECÍFICO."""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html')

    # Pega o setor específico ou retorna erro 404 se não existir
    setor = get_object_or_404(Setor, id=setor_id)

    # Verifica permissão: Diretor pode ver qualquer setor,
    # outros só podem ver setores aos quais pertencem.
    setores_permitidos = funcionario_logado.setor.all()
    if funcionario_logado.cargo.nivel > 1 and setor not in setores_permitidos:
         return render(request, 'hierarquia/sem_permissao.html', {'mensagem': f'Você não tem permissão para ver funcionários do setor "{setor.nome}".'})

    # Filtra funcionários ATIVOS e DO SETOR específico
    funcionarios = Funcionario.objects.filter(ativo=True, setor=setor)

    # Aplica busca por nome, se houver
    busca = request.GET.get('busca', '')
    if busca:
        funcionarios = funcionarios.filter(nome__icontains=busca)

    context = {
        'funcionario_logado': funcionario_logado,
        'funcionarios': funcionarios.order_by('nome'), # Ordena por nome
        'setor': setor, # Passa o objeto setor para o template
        'busca': busca,
    }

    return render(request, 'hierarquia/listar_funcionarios.html', context)

@login_required(login_url='login')
def listar_setores_funcionarios(request):
    """View para listar os setores que o usuário pode ver."""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html')

    # Determina quais setores mostrar
    if funcionario_logado.cargo.nivel == 1: # Diretor vê todos
        setores = Setor.objects.all().order_by('nome')
    else: # Outros níveis veem apenas os seus setores
        setores = funcionario_logado.setor.all().order_by('nome')

    context = {
        'funcionario_logado': funcionario_logado, # Passa para o base.html
        'setores': setores,
    }

    return render(request, 'hierarquia/listar_setores.html', context)


@login_required(login_url='login')
def cadastrar_funcionario(request):
    """View para cadastrar novo funcionário"""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html')
    
    # --- CORREÇÃO 2 (Permissão) ---
    # Trocamos a verificação de "nível 1" pela permissão real
    # que definimos no models.py. (Níveis 1-4 terão ela)
    if not request.user.has_perm('hierarquia.add_funcionario'):
        return render(request, 'hierarquia/sem_permissao.html')
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        data_nascimento = request.POST.get('data_nascimento')
        cpf = request.POST.get('cpf')
        data_admissao = request.POST.get('data_admissao')
        cargo_id = request.POST.get('cargo')
        
        # --- CORREÇÃO 3 (Lógica ManyToMany) ---
        # 1. Pegamos uma LISTA de IDs do formulário
        setores_ids = request.POST.getlist('setor')
        centro_servico_id = request.POST.get('centro_servico')
        
        try:
            cargo = Cargo.objects.get(id=cargo_id)
            # 2. Buscamos TODOS os objetos Setor que estavam na lista
            setores = Setor.objects.filter(id__in=setores_ids)
            
            centro_servico = None
            if centro_servico_id:
                centro_servico = CentroServico.objects.get(id=centro_servico_id)
            
            # 3. Criamos o funcionário SEM o setor
            funcionario = Funcionario.objects.create(
                nome=nome,
                data_nascimento=data_nascimento if data_nascimento else None,
                cpf=cpf,
                data_admissao=data_admissao,
                cargo=cargo,
                # 'setor' não pode ser passado no create()
                centro_servico=centro_servico,
            )
            
            # 4. Adicionamos os setores DEPOIS de criar o objeto
            funcionario.setor.set(setores)
            
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
    
    # --- CORREÇÃO 4 (Lógica ManyToMany) ---
    # Verificar permissão de visualização
    
    # 1. Pega os setores do gestor
    setores_do_gestor = funcionario_logado.setor.all()
    
    # 2. Verifica se o funcionário detalhado compartilha PELO MENOS UM setor com o gestor
    #    Usamos .values_list('id', flat=True) para performance
    pertence_aos_setores = funcionario.setor.filter(
        id__in=setores_do_gestor.values_list('id', flat=True)
    ).exists()
    
    # 3. Se não for diretor E não compartilhar setores, bloqueia
    if funcionario_logado.cargo.nivel > 1 and not pertence_aos_setores:
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
        # (O método obter_subordinados() já foi corrigido no models.py)
        subordinados = funcionario_logado.obter_subordinados()
        requisicoes = Requisicao.objects.filter(
            Q(solicitante=funcionario_logado) | Q(solicitante__in=subordinados)
        ).distinct()
    
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
    
    # Verifica se o solicitante é o próprio logado OU está na lista de subordinados
    pode_ver = (
        requisicao.solicitante == funcionario_logado or 
        subordinados.filter(id=requisicao.solicitante.id).exists()
    )
    
    if not pode_ver and funcionario_logado.cargo.nivel > 1: # Diretor pode ver tudo
        return render(request, 'hierarquia/sem_permissao.html')
    
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
        'nivel_choices': Cargo.NIVEL_CHOICES
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