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
    
# Modelo Vaga ATUALIZADO com campos do PDF
class Vaga(models.Model):
    STATUS_CHOICES = [
        ('aberta', 'Aberta'),
        ('em_processo', 'Em Processo de Seleção'),
        ('congelada', 'Congelada'),
        ('fechada', 'Fechada'),
    ]
    TIPO_CONTRATACAO_CHOICES = [
        ('clt', 'CLT'),
        ('pj', 'PJ'),
        ('estagio', 'Estágio'),
        ('temporario', 'Temporário'),
        ('terceiro', 'Terceiro'),
    ]

    titulo = models.CharField(max_length=200, verbose_name="Título da Vaga/Cargo")
    setor = models.ForeignKey(Setor, on_delete=models.PROTECT, related_name='vagas', verbose_name="Setor da Vaga")
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, related_name='vagas', verbose_name="Cargo da Vaga")
    centro_custo = models.CharField(max_length=100, blank=True, verbose_name="Centro de Custo") # Adicionado
    tipo_contratacao = models.CharField(max_length=20, choices=TIPO_CONTRATACAO_CHOICES, default='clt', verbose_name="Tipo de Contratação")
    faixa_salarial_inicial = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Faixa Salarial (Início)")
    faixa_salarial_final = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Faixa Salarial (Fim)")
    requisitos_tecnicos = models.TextField(blank=True, verbose_name="Competências Técnicas")
    requisitos_comportamentais = models.TextField(blank=True, verbose_name="Competências Comportamentais")
    principais_atividades = models.TextField(blank=True, verbose_name="Principais Responsabilidades/Atividades")
    formacao_academica = models.TextField(blank=True, verbose_name="Formação Acadêmica") # Adicionado
    beneficios = models.TextField(blank=True, verbose_name="Benefícios") # Adicionado
    justificativa = models.TextField(verbose_name="Justificativa da Vaga (RH/DP)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberta', verbose_name="Status da Vaga")
    criado_por = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, related_name='vagas_criadas', verbose_name="Criado Por (RH/DP)")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    # Adicione outros campos específicos do seu checklist se houver (Ex: Nível Idioma, etc.)

    def __str__(self):
        return f"{self.titulo} ({self.setor.nome})"

    class Meta:
        verbose_name = "Vaga"
        verbose_name_plural = "Vagas"


# Modelo RequisicaoPessoal ATUALIZADO com campos do PDF
class RequisicaoPessoal(models.Model):
    STATUS_RP_CHOICES = [
        ('pendente_nivel_4', 'Pendente Supervisor'), # Nível 4 aprova
        ('pendente_nivel_3', 'Pendente Coordenador'), # Nível 3 aprova
        ('pendente_nivel_2', 'Pendente Gerente'),     # Nível 2 aprova
        ('pendente_nivel_1', 'Pendente Diretor'),    # Nível 1 aprova
        ('aprovada', 'Aprovada (RH)'),             # Aprovado por todos
        ('rejeitada', 'Rejeitada'),
        ('cancelada', 'Cancelada'),
    ]
    TIPO_VAGA_CHOICES = [
        ('nova', 'Nova Posição'),
        ('substituicao', 'Substituição'),
    ]
    MOTIVO_SUBSTITUICAO_CHOICES = [
        ('demissao', 'Demissão'),
        ('promocao', 'Promoção'),
        ('transferencia', 'Transferência'),
        ('aposentadoria', 'Aposentadoria'),
        ('termino_contrato', 'Término de Contrato'),
        ('outro', 'Outro'),
    ]

    # --- Campos de Identificação ---
    # numero_rp = models.CharField(max_length=20, unique=True, blank=True) # Opcional: Gerar um número único
    vaga = models.ForeignKey(Vaga, on_delete=models.CASCADE, related_name='requisicoes', verbose_name="Vaga Solicitada")
    solicitante = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name='rps_solicitadas', verbose_name="Solicitante")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Abertura")
    atualizado_em = models.DateTimeField(auto_now=True)

    # --- Detalhes da Vaga (Informações da RP) ---
    tipo_vaga = models.CharField(max_length=20, choices=TIPO_VAGA_CHOICES, default='nova', verbose_name="Tipo de Vaga")
    nome_substituido = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nome do Substituído", help_text="Preencher se for Substituição.")
    motivo_substituicao = models.CharField(max_length=30, choices=MOTIVO_SUBSTITUICAO_CHOICES, blank=True, null=True, verbose_name="Motivo da Substituição")
    local_trabalho = models.CharField(max_length=200, blank=True, verbose_name="Local de Trabalho")
    data_prevista_inicio = models.DateField(null=True, blank=True, verbose_name="Data Prevista para Início")
    prazo_contratacao = models.DateField(null=True, blank=True, verbose_name="Prazo Limite para Contratação")
    horario_trabalho = models.CharField(max_length=100, blank=True, verbose_name="Horário de Trabalho")
    justificativa_rp = models.TextField(verbose_name="Justificativa da Contratação", help_text="Descreva a necessidade desta contratação.")

    # --- Controle de Aprovação ---
    status = models.CharField(max_length=30, choices=STATUS_RP_CHOICES, verbose_name="Status da Requisição") # Default será definido no save()
    aprovador_atual = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='rps_para_aprovar', verbose_name="Próximo Aprovador")
    observacoes_aprovador = models.TextField(blank=True, verbose_name="Observações do Aprovador")

    # --- Histórico de Aprovação (Opcional, mas recomendado) ---
    aprovado_por_supervisor = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    data_aprovacao_supervisor = models.DateTimeField(null=True, blank=True)
    aprovado_por_coordenador = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    data_aprovacao_coordenador = models.DateTimeField(null=True, blank=True)
    aprovado_por_gerente = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    data_aprovacao_gerente = models.DateTimeField(null=True, blank=True)
    aprovado_por_diretor = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    data_aprovacao_diretor = models.DateTimeField(null=True, blank=True)
    # Quem rejeitou (se aplicável)
    rejeitado_por = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    data_rejeicao = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        # numero = f"RP {self.numero_rp}: " if hasattr(self, 'numero_rp') and self.numero_rp else ""
        numero = f"RP #{self.id}: " # Usando o ID por enquanto
        return f"{numero}{self.vaga.titulo} por {self.solicitante.nome}"

    def _encontrar_proximo_aprovador(self, nivel_atual_aprovador=None):
        """
        Lógica interna para encontrar o próximo superior na hierarquia.
        Assume que existe o campo 'superior_imediato' no modelo Funcionario.
        Precisa ser adaptada à sua estrutura hierárquica real.
        """
        ultimo_aprovador = nivel_atual_aprovador or self.solicitante
        if not ultimo_aprovador or not hasattr(ultimo_aprovador, 'superior_imediato'):
            return None # Não há como subir na hierarquia

        superior = ultimo_aprovador.superior_imediato
        while superior and superior.cargo and superior.cargo.nivel >= ultimo_aprovador.cargo.nivel:
            # Continua subindo se o superior tem nível igual ou maior (procura alguém com nível menor)
            if not hasattr(superior, 'superior_imediato'): return None # Chegou ao topo sem achar
            superior = superior.superior_imediato
            if superior == ultimo_aprovador: break # Evita loop infinito

        return superior # Retorna o primeiro superior com nível MENOR encontrado

    def set_initial_approver(self):
        """Define o status e o aprovador inicial ao criar a RP."""
        # Encontra o primeiro superior com nível 4 (Supervisor) ou menor
        aprovador = self.solicitante
        while aprovador and aprovador.cargo and aprovador.cargo.nivel > 4:
             if not hasattr(aprovador, 'superior_imediato'):
                 aprovador = None; break
             aprovador = aprovador.superior_imediato
             if aprovador == self.solicitante: break # Evita loop

        if aprovador and aprovador.cargo and aprovador.cargo.nivel <= 4:
            self.aprovador_atual = aprovador
            # Define o status inicial baseado no nível do primeiro aprovador
            if aprovador.cargo.nivel == 4: self.status = 'pendente_nivel_4'
            elif aprovador.cargo.nivel == 3: self.status = 'pendente_nivel_3'
            elif aprovador.cargo.nivel == 2: self.status = 'pendente_nivel_2'
            elif aprovador.cargo.nivel == 1: self.status = 'pendente_nivel_1'
            else: self.status = 'pendente_nivel_1' # Segurança: cai para o diretor
        else:
            # Se não encontrar ninguém na cadeia até Nível 4, vai direto pro Diretor (Nível 1)
            try:
                diretor = Funcionario.objects.filter(cargo__nivel=1).first() # Assume que há um diretor
                self.aprovador_atual = diretor
                self.status = 'pendente_nivel_1'
            except Funcionario.DoesNotExist:
                 self.status = 'aprovada' # Ou um status de erro? Se não há diretor...
                 self.aprovador_atual = None


    def save(self, *args, **kwargs):
        is_new = self._state.adding # Verifica se é uma nova instância
        if is_new:
            # Define o status e aprovador inicial SOMENTE na criação
            self.set_initial_approver()
        super().save(*args, **kwargs) # Salva o objeto

    def avancar_aprovacao(self, aprovador_que_aprovou):
        """Move a RP para o próximo nível de aprovação."""
        now = timezone.now()
        nivel_aprovador = aprovador_que_aprovou.cargo.nivel

        # Registra quem aprovou e quando
        if nivel_aprovador == 4:
            self.aprovado_por_supervisor = aprovador_que_aprovou
            self.data_aprovacao_supervisor = now
        elif nivel_aprovador == 3:
            self.aprovado_por_coordenador = aprovador_que_aprovou
            self.data_aprovacao_coordenador = now
        elif nivel_aprovador == 2:
             self.aprovado_por_gerente = aprovador_que_aprovou
             self.data_aprovacao_gerente = now
        elif nivel_aprovador == 1:
             self.aprovado_por_diretor = aprovador_que_aprovou
             self.data_aprovacao_diretor = now

        # Encontra o próximo aprovador (alguém com nível MENOR que o atual)
        proximo_aprovador = self._encontrar_proximo_aprovador(nivel_atual_aprovador=aprovador_que_aprovou)

        if proximo_aprovador and proximo_aprovador.cargo:
            self.aprovador_atual = proximo_aprovador
            # Define o novo status pendente
            prox_nivel = proximo_aprovador.cargo.nivel
            if prox_nivel == 3: self.status = 'pendente_nivel_3'
            elif prox_nivel == 2: self.status = 'pendente_nivel_2'
            elif prox_nivel == 1: self.status = 'pendente_nivel_1'
            else: self.status = 'pendente_nivel_1' # Segurança
        else:
            # Não há mais ninguém para aprovar -> APROVADA (final do fluxo)
            self.status = 'aprovada'
            self.aprovador_atual = None

        self.save()

    def rejeitar(self, aprovador_que_rejeitou, observacao):
        """Marca a RP como rejeitada."""
        self.status = 'rejeitada'
        self.rejeitado_por = aprovador_que_rejeitou
        self.data_rejeicao = timezone.now()
        self.observacoes_aprovador = observacao
        self.aprovador_atual = None
        self.save()

    class Meta:
        verbose_name = "Requisição Pessoal"
        verbose_name_plural = "Requisições Pessoais"
        ordering = ['-criado_em']