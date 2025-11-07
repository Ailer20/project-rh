# views.py (Arquivo principal que importa as views dos submódulos)

from .rh.login.views_login import login_view, logout_view

from .rh.telas.views_telas import (
    dashboard, listar_funcionarios_por_setor, listar_setores_funcionarios,
    cadastrar_funcionario, detalhar_funcionario,  
    gerenciar_cargos, gerenciar_setores, VagaListView, 
    VagaCreateView, VagaUpdateView, VagaDetailView
)
from .rh.rp.views_rp import (
    RequisicaoPessoalCreateView, MinhasRequisicoesListView, AprovarRequisicoesListView,
    RequisicaoPessoalDetailView, aprovar_rp_view, rejeitar_rp_view,
    RequisicaoPessoalRHUpdateView, HistoricoRPListView
)

from .rh.mp.views_mp import (
    MovimentacaoPessoalCreateView, MinhasMovimentacoesListView, AprovarMovimentacoesListView,
    MovimentacaoPessoalDetailView, aprovar_mp_view, rejeitar_mp_view,
    HistoricoMPListView
)
from .rh.rd.views_rd import (
    RequisicaoDesligamentoCreateView,
    RequisicaoDesligamentoDetailView, aprovar_rd_view, rejeitar_rd_view,
    HistoricoRDListView, MinhasDesligamentosListView, AprovarDesligamentosListView
)

# Se o arquivo original views.py estava dentro de uma pasta 'rh',
# esta importação pode precisar ser ajustada para refletir a estrutura do projeto.
# Assumindo que este novo views.py está no mesmo nível do diretório 'rh'.
