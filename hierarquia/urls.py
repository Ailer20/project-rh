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
    path('rp/historico/', views.HistoricoRPListView.as_view(), name='historico_rps'),
    # Ações de Aprovar/Rejeitar (usando views baseadas em função)
    path('rp/<int:pk>/aprovar/', views.aprovar_rp_view, name='aprovar_rp'),
    path('rp/<int:pk>/rejeitar/', views.rejeitar_rp_view, name='rejeitar_rp'),

    # --- ✅ NOVAS URLs PARA MOVIMENTAÇÃO PESSOAL (MP) ---
    path('mp/nova/', views.MovimentacaoPessoalCreateView.as_view(), name='criar_mp'),
    path('mp/minhas/', views.MinhasMovimentacoesListView.as_view(), name='minhas_mps'),
    path('mp/aprovar/', views.AprovarMovimentacoesListView.as_view(), name='listar_mps_para_aprovar'),
    path('mp/<int:pk>/', views.MovimentacaoPessoalDetailView.as_view(), name='detalhar_mp'),
    path('mp/historico/', views.HistoricoMPListView.as_view(), name='historico_mps'),
    # Funções de ação MP
    path('mp/<int:pk>/aprovar/post/', views.aprovar_mp_view, name='aprovar_mp'),
    path('mp/<int:pk>/rejeitar/post/', views.rejeitar_mp_view, name='rejeitar_mp'),
    # ---------------------------------------------------

    # --- ✅ NOVAS URLs PARA REQUISIÇÃO DE DESLIGAMENTO (RD) ---
    path('rd/nova/', views.RequisicaoDesligamentoCreateView.as_view(), name='criar_rd'),
    path('rd/minhas/', views.MinhasDesligamentosListView.as_view(), name='minhas_rds'),
    path('rd/aprovar/', views.AprovarDesligamentosListView.as_view(), name='listar_rds_para_aprovar'),
    path('rd/<int:pk>/', views.RequisicaoDesligamentoDetailView.as_view(), name='detalhar_rd'),
    # Funções de ação RD
    path('rd/<int:pk>/aprovar/post/', views.aprovar_rd_view, name='aprovar_rd'),
    path('rd/<int:pk>/rejeitar/post/', views.rejeitar_rd_view, name='rejeitar_rd'),
    path('rd/historico/', views.HistoricoRDListView.as_view(), name='historico_rds'),
    # -----------------------------------------------------------

    # --- Requisições Gerais (Verifique se são as RPs ou outras) ---
    # Se estas views forem para as RPs, você pode querer renomeá-las ou removê-las
    # Se forem para outro tipo de requisição, mantenha-as
    # path('requisicoes/', listar_requisicoes, name='listar_requisicoes'),
    # path('requisicoes/criar/', criar_requisicao, name='criar_requisicao'),
    # path('requisicoes/<int:requisicao_id>/', detalhar_requisicao, name='detalhar_requisicao'),

]