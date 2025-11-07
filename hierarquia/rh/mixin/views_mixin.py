from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from hierarquia.models import MovimentacaoPessoal, Funcionario, Cargo, Setor
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin



# --- MIXINS DE PERMISSÃO (REUTILIZÁVEIS) ---

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
    

# --- Mixin de Permissão Específico para RD ---
class PodeVerRDMixin(BasePermissionMixin):
    """ Verifica se o usuário pode ver uma RD específica """
    permission_denied_message = 'Você não tem permissão para acessar esta requisição de desligamento.'

    def test_func(self):
        if not super().test_func(): return False
        rd = self.get_object() # Pega a RD da DetailView
        user_func = self.funcionario_logado

        is_rh_dp = False
        if user_func.setor_primario:
             rh_dp_setores = ['RECURSOS HUMANOS', 'DEPARTAMENTO DE PESSOAL']
             if user_func.setor_primario.nome.upper() in [s.upper() for s in rh_dp_setores]:
                  is_rh_dp = True

        # Permissões para VER:
        pode_ver = (
            rd.solicitante == user_func or
            rd.funcionario_desligado == user_func or
            rd.aprovador_atual == user_func or
            rd.aprovado_por_gestor == user_func or
            rd.aprovado_por_rh == user_func or
            rd.rejeitado_por == user_func or
            is_rh_dp or
            (user_func.cargo and user_func.cargo.nivel == 1)
        )
        return pode_ver
    
# --- Mixin de Permissão Específico para MP (Adaptado do PodeAprovarMixin) ---
class PodeVerMPMixin(BasePermissionMixin):
    """ Verifica se o usuário pode ver uma MP específica """
    permission_denied_message = 'Você não tem permissão para acessar esta movimentação.'

    def test_func(self):
        if not super().test_func(): return False
        mp = self.get_object() # Pega a MP da DetailView
        user_func = self.funcionario_logado

        # Permissões para VER:
        # 1. É o solicitante?
        # 2. É o funcionário sendo movido?
        # 3. É um dos APROVADORES PENDENTES (gestor prop/atual ou RH)? <<< MUDANÇA AQUI
        # 4. É um dos aprovadores anteriores?
        # 5. É do RH/DP?
        # 6. É Diretor (Nível 1)?

        is_rh_dp = False
        if user_func.setor_primario:
             rh_dp_setores = ['RECURSOS HUMANOS', 'DEPARTAMENTO DE PESSOAL']
             if user_func.setor_primario.nome.upper() in [s.upper() for s in rh_dp_setores]: # Use list comprehension para upper
                  is_rh_dp = True

        # --- ✅ LÓGICA DE VERIFICAÇÃO ATUALIZADA ---
        pode_ver = (
            mp.solicitante == user_func or
            mp.funcionario_movido == user_func or
            # Verifica se é um dos aprovadores *atuais* pendentes
            (mp.status == 'pendente_gestores' and (mp.aprovador_gestor_proposto == user_func or mp.aprovador_gestor_atual == user_func)) or
            (mp.status == 'pendente_rh' and mp.aprovador_rh == user_func) or
            # Verifica se foi um aprovador anterior ou quem rejeitou
            mp.aprovado_por_gestor_proposto == user_func or
            mp.aprovado_por_gestor_atual == user_func or
            mp.aprovado_por_rh == user_func or
            mp.rejeitado_por == user_func or
            # Permissões gerais
            is_rh_dp or
            (user_func.cargo and user_func.cargo.nivel == 1) # Adicionado check se user_func.cargo existe
        )
        # ---------------------
        return pode_ver