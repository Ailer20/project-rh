# hierarquia/templatetags/rh_tags.py

from django import template

register = template.Library()

# Lista de nomes dos setores de RH/DP (case-insensitive)
RH_DP_SETORES = ['RECURSOS HUMANOS', 'DEPARTAMENTO DE PESSOAL']

@register.simple_tag
def is_rh_or_dp(funcionario):
    """
    Verifica se o funcionário pertence a um dos setores de RH ou DP.
    Retorna True se pertence, False caso contrário.
    """
    if funcionario and funcionario.setor_primario:
        # Compara ignorando maiúsculas/minúsculas
        if funcionario.setor_primario.nome.upper() in (s.upper() for s in RH_DP_SETORES):
            return True
    return False

# Você pode adicionar outras tags/filtros aqui se precisar no futuro