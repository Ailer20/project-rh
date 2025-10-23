from django.db import models
# --- CORREÇÃO AQUI ---
# Garantindo que User, Permission e ContentType estão importados
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
# ---------------------
from django.core.validators import RegexValidator
from django.db.models import Q
# Validadores
cpf_validator = RegexValidator(
    regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$',
    message='CPF deve estar no formato: XXX.XXX.XXX-XX',
    code='invalid_cpf'
)


class Cargo(models.Model):
    """Modelo para representar cargos na hierarquia"""
    NIVEL_CHOICES = [
        (1, 'Diretor'),
        (2, 'Gestor'),
        (3, 'Coordenador'),
        (4, 'Supervisor'),
        (5, 'ADM/Analista'), # E outros níveis operacionais
    ]
    
    nome = models.CharField(max_length=255, unique=True)
    nivel = models.IntegerField(choices=NIVEL_CHOICES)
    descricao = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['nivel', 'nome']
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'
    
    def __str__(self):
        return f"{self.nome} (Nível {self.nivel})"


class Setor(models.Model):
    """Modelo para representar setores/centros de custo"""
    nome = models.CharField(max_length=255, unique=True)
    descricao = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['nome']
        verbose_name = 'Setor'
        verbose_name_plural = 'Setores'
    
    def __str__(self):
        return self.nome


class CentroServico(models.Model):
    """Modelo para representar centros de serviço (opcional)"""
    nome = models.CharField(max_length=255)
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE, related_name='centros_servico')
    descricao = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['nome']
        verbose_name = 'Centro de Serviço'
        verbose_name_plural = 'Centros de Serviço'
        unique_together = ['nome', 'setor']
    
    def __str__(self):
        return f"{self.nome} ({self.setor.nome})"


class Funcionario(models.Model):
    """Modelo para representar funcionários"""
    usuario = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='funcionario')
    nome = models.CharField(max_length=255)
    data_nascimento = models.DateField(blank=True, null=True)
    cpf = models.CharField(max_length=14, unique=True, validators=[cpf_validator])
    data_admissao = models.DateField()
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, related_name='funcionarios')

    # --- NOVOS CAMPOS DE SETOR ---
    setor_primario = models.ForeignKey(
        Setor,
        on_delete=models.PROTECT, # Protege contra exclusão de setor com funcionários
        related_name='funcionarios_primarios', # Nome para acesso reverso
        verbose_name='Setor Principal',
        null=True, # TEMPORARIAMENTE True para facilitar migração inicial, depois pode ser False
        blank=True # TEMPORARIAMENTE True
        # Considere null=False, blank=False depois que tudo estiver ajustado
    )
    setores_responsaveis = models.ManyToManyField(
        Setor,
        related_name='responsaveis', # Permite Setor.responsaveis.all()
        blank=True, # Muitos funcionários não serão responsáveis por nenhum setor
        verbose_name='Setores Responsáveis'
    )
    # --- FIM DOS NOVOS CAMPOS ---

    centro_servico = models.ForeignKey(CentroServico, on_delete=models.SET_NULL, null=True, blank=True, related_name='funcionarios')
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'

    def __str__(self):
         # Mostra setor primário se existir
        setor_str = f" - {self.setor_primario.nome}" if self.setor_primario else ""
        return f"{self.nome} - {self.cargo.nome}{setor_str}"

    # --- LÓGICA DE PERMISSÕES (mantida) ---
    def save(self, *args, **kwargs):
        is_new = self._state.adding # Verifica se é um novo objeto
        super().save(*args, **kwargs)
        if self.usuario:
            pode_gerenciar_equipe = self.cargo.nivel <= 4
            self.usuario.is_staff = pode_gerenciar_equipe
            try:
                content_type = ContentType.objects.get_for_model(Funcionario)
                perm_add = Permission.objects.get(content_type=content_type, codename='add_funcionario')
                perm_change = Permission.objects.get(content_type=content_type, codename='change_funcionario')
                perm_view = Permission.objects.get(content_type=content_type, codename='view_funcionario')

                if pode_gerenciar_equipe:
                    self.usuario.user_permissions.add(perm_add, perm_change, perm_view)
                elif not is_new: # Só remove se não for novo (evita erro na criação)
                     self.usuario.user_permissions.remove(perm_add, perm_change, perm_view)

                # Salva o usuário apenas se houve mudança ou se é novo e precisa de permissão
                if is_new or self.usuario.is_staff != pode_gerenciar_equipe:
                     self.usuario.save()

            except (Permission.DoesNotExist, ContentType.DoesNotExist):
                pass # Ignora se permissões não existem (primeira migração)

    # --- MÉTODOS HIERÁRQUICOS ATUALIZADOS ---
    def obter_nivel_hierarquico(self):
        return self.cargo.nivel

    def obter_superiores(self):
        """
        (CORRIGIDO NOVAMENTE) Retorna superiores hierárquicos:
        1. Superiores (nível < atual) DENTRO do mesmo Setor Principal.
        2. Superiores (nível < atual) que são RESPONSÁVEIS pelo Setor Principal do funcionário.
        3. SEMPRE inclui Diretores (nível 1) ativos.
        """
        if not self.setor_primario:
            # Se o funcionário não tem setor primário, apenas Diretores podem ser superiores.
            return Funcionario.objects.filter(cargo__nivel=1, ativo=True).exclude(pk=self.pk).distinct().order_by('cargo__nivel')

        # Condição 1: Superior no mesmo setor primário E nível menor
        condicao_mesmo_setor = Q(
            setor_primario=self.setor_primario,
            cargo__nivel__lt=self.cargo.nivel,
            ativo=True
        )

        # --- NOVA CONDIÇÃO ---
        # Condição 2: Superior é RESPONSÁVEL pelo setor primário deste funcionário E tem nível menor
        condicao_responsavel = Q(
            setores_responsaveis=self.setor_primario, # Verifica se o setor_primario DESTE func está na lista M2M do OUTRO
            cargo__nivel__lt=self.cargo.nivel,
            ativo=True
        )
        # ---------------------

        # Condição 3: É um Diretor (Nível 1) ativo
        condicao_diretor = Q(
            cargo__nivel=1,
            ativo=True
        )

        # Combina as condições: (Mesmo Setor OU Responsável OU Diretor)
        superiores = Funcionario.objects.filter(
            condicao_mesmo_setor | condicao_responsavel | condicao_diretor
        ).exclude(pk=self.pk).distinct().order_by('cargo__nivel')

        # --- REMOÇÃO DO FILTRO DE CENTRO DE SERVIÇO ---
        # O filtro por centro_servico aqui provavelmente não faz sentido,
        # pois um gerente responsável ou um diretor não necessariamente
        # compartilharão o mesmo centro de serviço. Removendo para clareza.
        # Se precisar reintroduzir com lógica específica, pode ser feito.
        # if self.centro_servico:
        #     superiores = superiores.filter(centro_servico=self.centro_servico)
        # -----------------------------------------------

        return superiores

    def obter_subordinados(self, incluir_responsaveis=True):
        """
        Retorna subordinados:
        1. Com nível maior DENTRO do Setor Principal do funcionário.
        2. Se incluir_responsaveis=True (padrão), também inclui todos os funcionários
           cujo Setor Principal seja um dos Setores Responsáveis por este funcionário.
        """
        subordinados = Funcionario.objects.none() # QuerySet vazio inicial

        # 1. Subordinados no setor primário
        if self.setor_primario:
            subordinados_primario = Funcionario.objects.filter(
                setor_primario=self.setor_primario,
                cargo__nivel__gt=self.cargo.nivel,
                ativo=True
            )
            subordinados = subordinados | subordinados_primario

        # 2. Subordinados nos setores responsáveis (se houver e incluir_responsaveis=True)
        if incluir_responsaveis and self.setores_responsaveis.exists():
            setores_resp = self.setores_responsaveis.all()
            subordinados_responsaveis = Funcionario.objects.filter(
                setor_primario__in=setores_resp,
                # Não filtra por nível aqui, pois o gestor pode ser responsável por pares/superiores em outros setores?
                # Vamos filtrar por nível > atual para consistência por enquanto.
                cargo__nivel__gt=self.cargo.nivel,
                ativo=True
            ).exclude(pk=self.pk) # Garante não incluir a si mesmo
            subordinados = subordinados | subordinados_responsaveis

        # Aplica filtro de centro de serviço, se houver
        if self.centro_servico:
             subordinados = subordinados.filter(centro_servico=self.centro_servico)

        return subordinados.distinct().order_by('setor_primario__nome', 'cargo__nivel', 'nome')

class Requisicao(models.Model):
    """Modelo para representar requisições no sistema"""
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovada', 'Aprovada'),
        ('rejeitada', 'Rejeitada'),
        ('concluida', 'Concluída'),
    ]
    
    titulo = models.CharField(max_length=255)
    descricao = models.TextField()
    solicitante = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='requisicoes_solicitadas')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    aprovador = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='requisicoes_aprovadas')
    data_aprovacao = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Requisição'
        verbose_name_plural = 'Requisições'
    
    def __str__(self):
        return f"{self.titulo} - {self.status}"