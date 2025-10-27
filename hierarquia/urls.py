# hierarquia/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # --- Autenticação ---
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # --- Dashboard ---
    path('', dashboard, name='dashboard'), # Rota principal

    # --- Funcionários, Cargos, Setores (Suas rotas existentes) ---
    path('funcionarios/setor/<int:setor_id>/', listar_funcionarios_por_setor, name='listar_funcionarios_por_setor'),
    path('funcionarios/setores/', listar_setores_funcionarios, name='listar_setores_funcionarios'),
    path('funcionarios/cadastrar/', cadastrar_funcionario, name='cadastrar_funcionario'),
    path('funcionarios/<int:funcionario_id>/', detalhar_funcionario, name='detalhar_funcionario'),
    path('cargos/', gerenciar_cargos, name='gerenciar_cargos'), # Ajuste o nome se necessário
    path('setores/', gerenciar_setores, name='gerenciar_setores'), # Ajuste o nome se necessário

    # --- ✅ NOVAS ROTAS PARA VAGAS (Acesso: RH/DP) ---
    path('vagas/', VagaListView.as_view(), name='listar_vagas'),
    path('vagas/nova/', VagaCreateView.as_view(), name='criar_vaga'),
    path('vagas/<int:pk>/editar/', VagaUpdateView.as_view(), name='editar_vaga'),
    path('vagas/<int:pk>/', VagaDetailView.as_view(), name='detalhar_vaga'), # Opcional

    # --- ✅ NOVAS ROTAS PARA REQUISIÇÃO PESSOAL (RP) ---
    path('rp/nova/', RequisicaoPessoalCreateView.as_view(), name='criar_rp'), # Para Nível 5 criar RP p/ vaga existente
    path('rp/minhas/', MinhasRequisicoesListView.as_view(), name='minhas_rps'), # Solicitante vê suas RPs
    path('rp/aprovar/', AprovarRequisicoesListView.as_view(), name='listar_rps_para_aprovar'), # Aprovador vê RPs pendentes
    path('rp/<int:pk>/', RequisicaoPessoalDetailView.as_view(), name='detalhar_rp'), # Detalhes e botões Aprovar/Rejeitar
    # Ações de Aprovar/Rejeitar (usando views baseadas em função)
    path('rp/<int:pk>/aprovar/', aprovar_rp_view, name='aprovar_rp'),
    path('rp/<int:pk>/rejeitar/', rejeitar_rp_view, name='rejeitar_rp'),

    # --- Requisições Gerais (Verifique se são as RPs ou outras) ---
    # Se estas views forem para as RPs, você pode querer renomeá-las ou removê-las
    # Se forem para outro tipo de requisição, mantenha-as
    # path('requisicoes/', listar_requisicoes, name='listar_requisicoes'),
    # path('requisicoes/criar/', criar_requisicao, name='criar_requisicao'),
    # path('requisicoes/<int:requisicao_id>/', detalhar_requisicao, name='detalhar_requisicao'),

]