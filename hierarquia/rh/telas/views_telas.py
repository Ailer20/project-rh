from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Q, Count
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User, Permission
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from hierarquia.models import Funcionario, Cargo, Setor, CentroServico, Vaga, RequisicaoPessoal, MovimentacaoPessoal, RequisicaoDesligamento
from django.urls import reverse
import json
from datetime import datetime 
# --- Views de Telas (Dashboard, Funcionários, Setores) ---
@login_required(login_url='login')
def dashboard(request):
    try:
        funcionario = Funcionario.objects.get(usuario=request.user)
        if not funcionario.cargo:
            return render(request, 'hierarquia/sem_acesso.html', {'mensagem': 'Seu usuário não está associado a um cargo.'})
    except Funcionario.DoesNotExist:
        if request.user.is_superuser:
            funcionario = None 
        else:
            return render(request, 'hierarquia/sem_acesso.html', {'mensagem': 'Não foi encontrado um perfil de funcionário associado ao seu usuário.'})

    # --- Lógica de Superusuário (para não quebrar a view) ---
    if not funcionario:
        # Pega todos os dados do sistema para o Superuser
        setor_data = Setor.objects.annotate(num_funcionarios=Count('funcionarios_primarios'))\
                             .filter(num_funcionarios__gt=0).order_by('-num_funcionarios')
        setor_chart_labels = [s.nome for s in setor_data]
        setor_chart_data = [s.num_funcionarios for s in setor_data]
        
        req_status_data = {
            'Pendentes': RequisicaoPessoal.objects.filter(status__startswith='pendente').count() + MovimentacaoPessoal.objects.filter(status__startswith='pendente').count() + RequisicaoDesligamento.objects.filter(status__startswith='pendente').count(),
            'Aprovadas': RequisicaoPessoal.objects.filter(status='aprovada').count() + MovimentacaoPessoal.objects.filter(status='aprovada').count() + RequisicaoDesligamento.objects.filter(status='aprovada').count(),
            'Rejeitadas': RequisicaoPessoal.objects.filter(status='rejeitada').count() + MovimentacaoPessoal.objects.filter(status='rejeitada').count() + RequisicaoDesligamento.objects.filter(status='rejeitada').count(),
        }
        req_status_data = {k: v for k, v in req_status_data.items() if v > 0} # Remove zeros
              
        context = {
            'funcionario': {'ra_nome': 'Admin', 'cargo': {'nivel': 1, 'nome': 'Superuser'}},
            'total_funcionarios': Funcionario.objects.count(),
            'total_cargos': Cargo.objects.count(),
            'setores_titulo_card': "Total de Setores",
            'setores_valor_card': Setor.objects.count(),
            'is_setor_name': False,
            'vagas_abertas_count': Vaga.objects.filter(status='aberta').count(),
            'minhas_pendencias_count': 0,
            'minhas_pendencias_lista': [],
            'requisicoes_pendentes': 0,
            'setor_chart_data': json.dumps({'labels': setor_chart_labels, 'data': setor_chart_data}),
            'req_status_chart_data': json.dumps({'labels': list(req_status_data.keys()), 'data': list(req_status_data.values())}),
            'data_admissao_formatada': "N/A" # Fallback para o Superuser
        }
        return render(request, 'hierarquia/dashboard.html', context)
    
    # --- Lógica Padrão para Funcionários ---
    nivel = funcionario.cargo.nivel
    setores_titulo_card = "Informação Setor"
    setores_valor_card = "N/A"
    is_setor_name = False

    # --- Lógica de Visibilidade CORRIGIDA ---
    setores_visiveis_q = Q()
    
    if nivel == 1:
        setores_visiveis_obj = Setor.objects.all()
        funcionarios_visiveis_qs = Funcionario.objects.filter(ativo=True)
        setores_visiveis_q = Q(pk__in=setores_visiveis_obj.values_list('pk', flat=True))
        
        total_funcionarios_visiveis = funcionarios_visiveis_qs.count()
        total_cargos_visiveis = Cargo.objects.count()
        setores_titulo_card = "Total de Setores"
        setores_valor_card = setores_visiveis_obj.count()

    else:
        if funcionario.setor_primario:
            setores_visiveis_q |= Q(pk=funcionario.setor_primario.pk)
        
        setores_responsaveis = funcionario.setores_responsaveis.all()
        if setores_responsaveis.exists():
            setores_visiveis_q |= Q(pk__in=setores_responsaveis.values_list('pk', flat=True))

        setores_visiveis_obj = Setor.objects.filter(setores_visiveis_q)
        funcionarios_visiveis_qs = Funcionario.objects.filter(setor_primario__in=setores_visiveis_obj, ativo=True)
        
        total_funcionarios_visiveis = funcionarios_visiveis_qs.count()
        total_cargos_visiveis = Cargo.objects.filter(funcionarios__in=funcionarios_visiveis_qs).distinct().count()

        if nivel <= 3 and setores_responsaveis.exists():
            setores_titulo_card = "Setores Responsáveis"
            setores_valor_card = setores_responsaveis.count()
        else:
            setores_titulo_card = "Meu Setor Principal"
            setores_valor_card = funcionario.setor_primario.nome if funcionario.setor_primario else "Nenhum"
            is_setor_name = True

    # --- NOVAS VARIÁVEIS PARA O DASHBOARD ---

    # 1. Card de Vagas Abertas
    vagas_abertas_count = Vaga.objects.filter(status='aberta').count()

    # 2. Pendências Pessoais (Cards e Lista)
    q_pend_rp = Q(aprovador_atual=funcionario, status__in=['pendente_gestor', 'pendente_rh', 'em_revisao_gestor'])
    q_pend_mp = (Q(aprovador_gestor_atual=funcionario, gestor_atual_aprovou=False) |
                 Q(aprovador_gestor_proposto=funcionario, gestor_proposto_aprovou=False) |
                 Q(aprovador_rh=funcionario, status='pendente_rh'))
    q_pend_rd = Q(aprovador_atual=funcionario, status__in=['pendente_gestor', 'pendente_rh'])

    pend_rps = RequisicaoPessoal.objects.filter(q_pend_rp)
    pend_mps = MovimentacaoPessoal.objects.filter(q_pend_mp).distinct()
    pend_rds = RequisicaoDesligamento.objects.filter(q_pend_rd)

    minhas_pendencias_count = pend_rps.count() + pend_mps.count() + pend_rds.count()
    
    # 3. Lista de Pendências (para a sidebar)
    minhas_pendencias_lista = []
    for rp in pend_rps[:3]: 
        minhas_pendencias_lista.append({
            'id': rp.id, 'tipo': 'RP', 'status': rp.status,
            'descricao': rp.vaga.titulo,
            'get_status_display': rp.get_status_display(),
            'get_absolute_url': reverse('detalhar_rp', args=[rp.pk])
        })
    for mp in pend_mps[:3]:
        minhas_pendencias_lista.append({
            'id': mp.id, 'tipo': 'MP', 'status': mp.status,
            'descricao': f"Mov. de {mp.funcionario_movido.ra_nome.split()[0]}",
            'get_status_display': mp.get_status_display(),
            'get_absolute_url': reverse('detalhar_mp', args=[mp.pk])
        })
    for rd in pend_rds[:3]:
        minhas_pendencias_lista.append({
            'id': rd.id, 'tipo': 'RD', 'status': rd.status,
            'descricao': f"Deslig. de {rd.funcionario_desligado.ra_nome.split()[0]}",
            'get_status_display': rd.get_status_display(),
            'get_absolute_url': reverse('detalhar_rd', args=[rd.pk])
        })
    minhas_pendencias_lista = sorted(minhas_pendencias_lista, key=lambda x: x['id'], reverse=True)[:5]

    # 4. Dados do Gráfico de Setores (FILTRADO)
    setor_data = setores_visiveis_obj.annotate(num_funcionarios=Count('funcionarios_primarios'))\
                                     .filter(num_funcionarios__gt=0)\
                                     .order_by('-num_funcionarios')
    
    setor_chart_labels = [s.nome for s in setor_data]
    setor_chart_data = [s.num_funcionarios for s in setor_data]
    
    # 5. Dados do Gráfico de Status (FILTRADO)
    rp_visiveis = RequisicaoPessoal.objects.filter(solicitante__in=funcionarios_visiveis_qs)
    mp_visiveis = MovimentacaoPessoal.objects.filter(solicitante__in=funcionarios_visiveis_qs)
    rd_visiveis = RequisicaoDesligamento.objects.filter(solicitante__in=funcionarios_visiveis_qs)

    req_status_data = {
        'Pendentes': rp_visiveis.filter(status__startswith='pendente').count() + 
                     mp_visiveis.filter(status__startswith='pendente').count() +
                     rd_visiveis.filter(status__startswith='pendente').count(),
        'Aprovadas': rp_visiveis.filter(status='aprovada').count() + 
                     mp_visiveis.filter(status='aprovada').count() +
                     rd_visiveis.filter(status='aprovada').count(),
        'Rejeitadas': rp_visiveis.filter(status='rejeitada').count() + 
                      mp_visiveis.filter(status='rejeitada').count() +
                      rd_visiveis.filter(status='rejeitada').count(),
    }
    req_status_data = {k: v for k, v in req_status_data.items() if v > 0}

    # --- ✅ LÓGICA DE DATA CORRIGIDA ---
    data_admissao_formatada = "N/A"
    if funcionario.ra_data_admis: # Verifica se o campo não está vazio
        try:
            # Tenta o formato exato do banco: YYYY-MM-DD HH:MM:SS
            data_obj = datetime.strptime(funcionario.ra_data_admis, '%Y-%m-%d %H:%M:%S')
            data_admissao_formatada = data_obj.strftime('%d/%m/%Y')
        except ValueError:
            try:
                # Tenta o formato YYYYMMDD (Protheus)
                data_obj = datetime.strptime(funcionario.ra_data_admis, '%Y%m%d')
                data_admissao_formatada = data_obj.strftime('%d/%m/%Y')
            except ValueError:
                try:
                    # Tenta o formato YYYY-MM-DD (apenas data)
                    data_obj = datetime.strptime(funcionario.ra_data_admis, '%Y-%m-%d')
                    data_admissao_formatada = data_obj.strftime('%d/%m/%Y')
                except ValueError:
                    # Se tudo falhar, exibe o texto original
                    data_admissao_formatada = funcionario.ra_data_admis

    # --- Contexto Final ---
    context = {
        'funcionario': funcionario,
        'total_funcionarios': total_funcionarios_visiveis,
        'total_cargos': total_cargos_visiveis,
        'setores_titulo_card': setores_titulo_card,
        'setores_valor_card': setores_valor_card,
        'is_setor_name': is_setor_name,
        
        'vagas_abertas_count': vagas_abertas_count,
        'minhas_pendencias_count': minhas_pendencias_count,
        'minhas_pendencias_lista': minhas_pendencias_lista,
        
        'setor_chart_data': json.dumps({'labels': setor_chart_labels, 'data': setor_chart_data}),
        'req_status_chart_data': json.dumps({'labels': list(req_status_data.keys()), 'data': list(req_status_data.values())}),
        
        'requisicoes_pendentes': minhas_pendencias_count, 
        
        'data_admissao_formatada': data_admissao_formatada # Variável de data
    }

    return render(request, 'hierarquia/dashboard.html', context)

# views.py
# (Certifique-se que 'datetime' está importado no topo do arquivo)
from datetime import datetime

@login_required(login_url='login')
def listar_funcionarios_por_setor(request, setor_id):
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html')

    setor = get_object_or_404(Setor, id=setor_id)

    # --- Lógica de Permissão ---
    permitido = False
    if funcionario_logado.cargo.nivel == 1:
            permitido = True
    elif funcionario_logado.setor_primario == setor:
            permitido = True
    elif funcionario_logado.setores_responsaveis.filter(pk=setor.pk).exists():
            permitido = True

    if not permitido:
        return render(request, 'hierarquia/sem_permissao.html', {'mensagem': f'Você não tem permissão para ver funcionários do setor "{setor.nome}".'})

    # 1. Inicia a consulta base
    funcionarios_qs = Funcionario.objects.filter(ativo=True, setor_primario=setor)

    busca = request.GET.get('busca', '')
    # 2. Filtra a consulta SE houver busca
    if busca:
        funcionarios_qs = funcionarios_qs.filter(ra_nome__icontains=busca)

    # 3. Inicializa a lista
    funcionarios_list = []
        
    # 4. Faz o loop na consulta final (já filtrada)
    for func in funcionarios_qs.order_by('ra_nome'):
        # ✅ --- INÍCIO DO BLOCO CORRIGIDO (INDENTADO) ---
        data_admissao_formatada = "N/A"
        if func.ra_data_admis:
            try:
                # Tenta o formato exato do banco: YYYY-MM-DD HH:MM:SS
                data_obj = datetime.strptime(func.ra_data_admis, '%Y-%m-%d %H:%M:%S')
                data_admissao_formatada = data_obj.strftime('%d/%m/%Y')
            except ValueError:
                try:
                    # Tenta o formato YYYYMMDD (Protheus)
                    data_obj = datetime.strptime(func.ra_data_admis, '%Y%m%d')
                    data_admissao_formatada = data_obj.strftime('%d/%m/%Y')
                except ValueError:
                        try:
                            # Tenta o formato YYYY-MM-DD (apenas data)
                            data_obj = datetime.strptime(func.ra_data_admis, '%Y-%m-%d')
                            data_admissao_formatada = data_obj.strftime('%d/%m/%Y')
                        except ValueError:
                            # Se falhar, exibe o original (sem quebrar)
                            data_admissao_formatada = func.ra_data_admis.split(" ")[0] 

        # Adiciona o objeto original E a data formatada
        funcionarios_list.append({
            'obj': func,
            'data_admissao_formatada': data_admissao_formatada
        })
        # ✅ --- FIM DO BLOCO CORRIGIDO ---
    # --- FIM DO LOOP FOR ---

    # 5. Define o contexto (agora 'funcionarios_list' sempre existe)
    context = {
        'funcionario_logado': funcionario_logado,
        'funcionarios_list': funcionarios_list, # Passa a nova lista para o template
        'setor': setor,
        'busca': busca,
    }
    return render(request, 'hierarquia/listar_funcionarios.html', context)

@login_required(login_url='login')
def listar_setores_funcionarios(request):
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html')
    setores_visiveis = Setor.objects.none()

    if funcionario_logado.cargo.nivel == 1:
        setores_visiveis = Setor.objects.all()
    else:
        if funcionario_logado.setor_primario:
            setores_visiveis = setores_visiveis | Setor.objects.filter(pk=funcionario_logado.setor_primario.pk)

        if funcionario_logado.setores_responsaveis.exists():
            setores_visiveis = setores_visiveis | funcionario_logado.setores_responsaveis.all()

    # ✅ --- CORREÇÃO AQUI ---
    # Adiciona a contagem de funcionários ativos para cada setor
    setores_com_contagem = setores_visiveis.distinct().annotate(
        num_funcionarios=Count('funcionarios_primarios', filter=Q(funcionarios_primarios__ativo=True))
    ).order_by('nome')
    # --- FIM DA CORREÇÃO ---

    context = {
        'funcionario_logado': funcionario_logado,
        'setores': setores_com_contagem, # ✅ Usa a nova variável com a contagem
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
def detalhar_funcionario(request, pk):
    """(ATUALIZADO) View para detalhar um funcionário"""
    try:
        funcionario_logado = request.user.funcionario
    except Funcionario.DoesNotExist:
        return render(request, 'hierarquia/sem_acesso.html')

    funcionario = get_object_or_404(Funcionario, id=pk)

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
