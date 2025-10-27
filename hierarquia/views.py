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