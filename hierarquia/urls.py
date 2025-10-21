# hierarquia/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('funcionarios/setores/', views.listar_setores_funcionarios, name='listar_setores_funcionarios'),

    path('funcionarios/setor/<int:setor_id>/', views.listar_funcionarios_por_setor, name='listar_funcionarios_por_setor'),
    path('funcionarios/cadastrar/', views.cadastrar_funcionario, name='cadastrar_funcionario'),
    path('funcionarios/<int:funcionario_id>/', views.detalhar_funcionario, name='detalhar_funcionario'),
    path('requisicoes/', views.listar_requisicoes, name='listar_requisicoes'),
    path('requisicoes/criar/', views.criar_requisicao, name='criar_requisicao'),
    path('requisicoes/<int:requisicao_id>/', views.detalhar_requisicao, name='detalhar_requisicao'),
    path('cargos/', views.gerenciar_cargos, name='gerenciar_cargos'),
    path('setores/', views.gerenciar_setores, name='gerenciar_setores'),
]