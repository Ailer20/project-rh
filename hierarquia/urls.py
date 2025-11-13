# hierarquia/urls.py
from django.urls import path
from . import views    

urlpatterns = [
    # ------------------------------------------------------------------
    # 🎯 1. ROTA RAIZ (PONTO DE ENTRADA) E AUTENTICAÇÃO
    # ------------------------------------------------------------------
    
    # Rota raiz ('/'): Aponta para a view de login, garantindo que o usuário veja o login 
    # ao acessar o endereço base do site (http://127.0.0.1:8000/).
    # No entanto, após logar, o Django irá para 'dashboard'.
    path('', views.login_view, name='root'), 
    
    # Login e Logout
    path('login/', views.login_view, name='rh_login'),
    path('logout/', views.logout_view, name='rh_logout'),

    # --- Dashboard ---
    # A rota do dashboard deve ter um caminho explícito (ex: /dashboard/)
    # para evitar conflitos com a rota raiz.
    path('dashboard/', views.dashboard, name='dashboard'), 

    # ------------------------------------------------------------------
    # 2. ROTAS DE GERENCIAMENTO (Funcionários, Cargos, Setores)
    # ------------------------------------------------------------------
    
    path('funcionarios/setor/<int:setor_id>/', views.listar_funcionarios_por_setor, name='listar_funcionarios_por_setor'),
    path('funcionarios/setores/', views.listar_setores_funcionarios, name='listar_setores_funcionarios'),
    path('funcionarios/cadastrar/', views.cadastrar_funcionario, name='cadastrar_funcionario'),
    path('funcionarios/<int:pk>/', views.detalhar_funcionario, name='detalhar_funcionario'),
    path('cargos/', views.gerenciar_cargos, name='gerenciar_cargos'),
    path('setores/', views.gerenciar_setores, name='gerenciar_setores'),

    # ------------------------------------------------------------------
    # 3. ROTAS PARA VAGAS (Gestão e Criação)
    # ------------------------------------------------------------------
    
    path('vagas/', views.VagaListView.as_view(), name='listar_vagas'),
    path('vagas/nova/', views.VagaCreateView.as_view(), name='criar_vaga'),
    path('vagas/<int:pk>/editar/', views.VagaUpdateView.as_view(), name='editar_vaga'),
    path('vagas/<int:pk>/', views.VagaDetailView.as_view(), name='detalhar_vaga'),

    # ------------------------------------------------------------------
    # 4. ROTAS PARA REQUISIÇÃO PESSOAL (RP)
    # ------------------------------------------------------------------
    
    path('rp/nova/', views.RequisicaoPessoalCreateView.as_view(), name='criar_rp'),
    path('rp/minhas/', views.MinhasRequisicoesListView.as_view(), name='minhas_rps'),
    path('rp/aprovar/', views.AprovarRequisicoesListView.as_view(), name='listar_rps_para_aprovar'),
    path('rp/<int:pk>/', views.RequisicaoPessoalDetailView.as_view(), name='detalhar_rp'),
    path('rp/editar-rh/<int:pk>/', views.RequisicaoPessoalRHUpdateView.as_view(), name='editar_rp_rh'),
    path('rp/historico/', views.HistoricoRPListView.as_view(), name='historico_rps'),
    # Ações de Aprovar/Rejeitar
    path('rp/<int:pk>/aprovar/', views.aprovar_rp_view, name='aprovar_rp'),
    path('rp/<int:pk>/rejeitar/', views.rejeitar_rp_view, name='rejeitar_rp'),

    # ------------------------------------------------------------------
    # 5. ROTAS PARA MOVIMENTAÇÃO PESSOAL (MP)
    # ------------------------------------------------------------------
    
    path('mp/nova/', views.MovimentacaoPessoalCreateView.as_view(), name='criar_mp'),
    path('mp/minhas/', views.MinhasMovimentacoesListView.as_view(), name='minhas_mps'),
    path('mp/aprovar/', views.AprovarMovimentacoesListView.as_view(), name='listar_mps_para_aprovar'),
    path('mp/<int:pk>/', views.MovimentacaoPessoalDetailView.as_view(), name='detalhar_mp'),
    path('mp/historico/', views.HistoricoMPListView.as_view(), name='historico_mps'),
    # Funções de ação MP
    path('mp/<int:pk>/aprovar/post/', views.aprovar_mp_view, name='aprovar_mp'),
    path('mp/<int:pk>/rejeitar/post/', views.rejeitar_mp_view, name='rejeitar_mp'),
    
    # ------------------------------------------------------------------
    # 6. ROTAS PARA REQUISIÇÃO DE DESLIGAMENTO (RD)
    # ------------------------------------------------------------------
    
    path('rd/nova/', views.RequisicaoDesligamentoCreateView.as_view(), name='criar_rd'),
    path('rd/minhas/', views.MinhasDesligamentosListView.as_view(), name='minhas_rds'),
    path('rd/aprovar/', views.AprovarDesligamentosListView.as_view(), name='listar_rds_para_aprovar'),
    path('rd/<int:pk>/', views.RequisicaoDesligamentoDetailView.as_view(), name='detalhar_rd'),
    path('rd/historico/', views.HistoricoRDListView.as_view(), name='historico_rds'),
    # Funções de ação RD
    path('rd/<int:pk>/aprovar/post/', views.aprovar_rd_view, name='aprovar_rd'),
    path('rd/<int:pk>/rejeitar/post/', views.rejeitar_rd_view, name='rejeitar_rd'),
]