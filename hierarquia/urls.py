# hierarquia/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # --- Autenticação ---
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # --- Dashboard ---
    path('', views.dashboard, name='dashboard'), # Rota principal

    # --- Funcionários, Cargos, Setores (Suas rotas existentes) ---
    path('funcionarios/setor/<int:setor_id>/', views.listar_funcionarios_por_setor, name='listar_funcionarios_por_setor'),
    path('funcionarios/setores/', views.listar_setores_funcionarios, name='listar_setores_funcionarios'),
    path('funcionarios/cadastrar/', views.cadastrar_funcionario, name='cadastrar_funcionario'),
    path('funcionarios/<int:funcionario_id>/', views.detalhar_funcionario, name='detalhar_funcionario'),
    path('cargos/', views.gerenciar_cargos, name='gerenciar_cargos'), # Ajuste o nome se necessário
    path('setores/', views.gerenciar_setores, name='gerenciar_setores'), # Ajuste o nome se necessário

    # --- ✅ NOVAS ROTAS PARA VAGAS (Acesso: RH/DP) ---
    path('vagas/', views.VagaListView.as_view(), name='listar_vagas'),
    path('vagas/nova/', views.VagaCreateView.as_view(), name='criar_vaga'),
    path('vagas/<int:pk>/editar/', views.VagaUpdateView.as_view(), name='editar_vaga'),
    path('vagas/<int:pk>/', views.VagaDetailView.as_view(), name='detalhar_vaga'), # Opcional

    # --- ✅ NOVAS ROTAS PARA REQUISIÇÃO PESSOAL (RP) ---
    path('rp/nova/', views.RequisicaoPessoalCreateView.as_view(), name='criar_rp'), # Para Nível 5 criar RP p/ vaga existente
    path('rp/minhas/', views.MinhasRequisicoesListView.as_view(), name='minhas_rps'), # Solicitante vê suas RPs
    path('rp/aprovar/', views.AprovarRequisicoesListView.as_view(), name='listar_rps_para_aprovar'), # Aprovador vê RPs pendentes
    path('rp/<int:pk>/', views.RequisicaoPessoalDetailView.as_view(), name='detalhar_rp'), # Detalhes e botões Aprovar/Rejeitar
    path('rp/editar-rh/<int:pk>/', views.RequisicaoPessoalRHUpdateView.as_view(), name='editar_rp_rh'),
    # Ações de Aprovar/Rejeitar (usando views baseadas em função)
    path('rp/<int:pk>/aprovar/', views.aprovar_rp_view, name='aprovar_rp'),
    path('rp/<int:pk>/rejeitar/', views.rejeitar_rp_view, name='rejeitar_rp'),

    # --- Requisições Gerais (Verifique se são as RPs ou outras) ---
    # Se estas views forem para as RPs, você pode querer renomeá-las ou removê-las
    # Se forem para outro tipo de requisição, mantenha-as
    # path('requisicoes/', listar_requisicoes, name='listar_requisicoes'),
    # path('requisicoes/criar/', criar_requisicao, name='criar_requisicao'),
    # path('requisicoes/<int:requisicao_id>/', detalhar_requisicao, name='detalhar_requisicao'),

]