# hierarquia/api_urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Importe TODOS os ViewSets e a view do Dashboard
from .api_views import (
    FuncionarioViewSet, 
    VagaViewSet,
    RequisicaoPessoalViewSet,
    RequisicaoDesligamentoViewSet,
    MovimentacaoPessoalViewSet,
    get_dashboard_data,
    get_setores_summary
)

# O Router cuida de tudo
router = DefaultRouter()
router.register(r'funcionarios', FuncionarioViewSet, basename='funcionario')
router.register(r'vagas', VagaViewSet, basename='vaga')
router.register(r'requisicoes-pessoal', RequisicaoPessoalViewSet, basename='requisicao-pessoal')
router.register(r'requisicoes-desligamento', RequisicaoDesligamentoViewSet, basename='requisicao-desligamento')
router.register(r'movimentacoes-pessoal', MovimentacaoPessoalViewSet, basename='movimentacao-pessoal')


urlpatterns = [
    # Endpoint do Dashboard
    path('dashboard-data/', get_dashboard_data, name='api-dashboard-data'),
    path('setores-summary/', get_setores_summary, name='api-setores-summary'),
    # Endpoints do Router (que incluem /aprovar/ e /rejeitar/ via @action)
    path('', include(router.urls)),
]

# URLs CRIADAS AUTOMATICAMENTE:
#
# GET /api/dashboard-data/
#
# GET /api/vagas/
#
# GET /api/funcionarios/
# GET /api/funcionarios/<id>/
#
# GET, POST /api/requisicoes-pessoal/
# GET /api/requisicoes-pessoal/<id>/
# POST /api/requisicoes-pessoal/<id>/aprovar/
# POST /api/requisicoes-pessoal/<id>/rejeitar/
#
# GET, POST /api/requisicoes-desligamento/
# GET /api/requisicoes-desligamento/<id>/
# POST /api/requisicoes-desligamento/<id>/aprovar/
# POST /api/requisicoes-desligamento/<id>/rejeitar/
#
# GET, POST /api/movimentacoes-pessoal/
# GET /api/movimentacoes-pessoal/<id>/
# POST /api/movimentacoes-pessoal/<id>/aprovar/
# POST /api/movimentacoes-pessoal/<id>/rejeitar/