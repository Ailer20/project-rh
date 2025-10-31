from django.db import models
# --- CORREÇÃO AQUI ---
# Garantindo que User, Permission e ContentType estão importados
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
# ---------------------
from django.http import HttpResponseForbidden
from django.core.validators import RegexValidator
from django.db.models import Q
from django.utils import timezone
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


# Modelo RequisicaoPessoal ATUALIZADO com fluxo Gestor -> RH
class RequisicaoPessoal(models.Model):
    # --- 1. STATUS ATUALIZADOS PARA O NOVO FLUXO ---
    STATUS_RP_CHOICES = [
        ('pendente_gestor', 'Pendente Gestor/Coordenador'),
        ('pendente_rh', 'Pendente RH'),
        ('em_revisao_gestor', 'Em Revisão (Edição RH)'), # Novo status para o "vai-e-volta"
        ('aprovada', 'Aprovada'),
        ('rejeitada', 'Rejeitada'),
        ('cancelada', 'Cancelada'), # Mantido
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

    # --- Campos de Identificação (Sem mudanças) ---
    vaga = models.ForeignKey(Vaga, on_delete=models.CASCADE, related_name='requisicoes', verbose_name="Vaga Solicitada")
    solicitante = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name='rps_solicitadas', verbose_name="Solicitante")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Abertura")
    atualizado_em = models.DateTimeField(auto_now=True)

    # --- Detalhes da Vaga (Sem mudanças) ---
    tipo_vaga = models.CharField(max_length=20, choices=TIPO_VAGA_CHOICES, default='nova', verbose_name="Tipo de Vaga")
    nome_substituido = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nome do Substituído", help_text="Preencher se for Substituição.")
    motivo_substituicao = models.CharField(max_length=30, choices=MOTIVO_SUBSTITUICAO_CHOICES, blank=True, null=True, verbose_name="Motivo da Substituição")
    local_trabalho = models.CharField(max_length=200, blank=True, verbose_name="Local de Trabalho")
    data_prevista_inicio = models.DateField(null=True, blank=True, verbose_name="Data Prevista para Início")
    prazo_contratacao = models.DateField(null=True, blank=True, verbose_name="Prazo Limite para Contratação")
    horario_trabalho = models.CharField(max_length=100, blank=True, verbose_name="Horário de Trabalho")
    justificativa_rp = models.TextField(verbose_name="Justificativa da Contratação", help_text="Descreva a necessidade desta contratação.")

    # --- 2. CONTROLE DE APROVAÇÃO ATUALIZADO ---
    status = models.CharField(max_length=30, choices=STATUS_RP_CHOICES, verbose_name="Status da Requisição") # Default será definido no save()
    aprovador_atual = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='rps_para_aprovar', verbose_name="Próximo Aprovador")
    
    # Campo antigo 'observacoes_aprovador' removido para evitar confusão
    
    # NOVOS CAMPOS para o fluxo "vai-e-volta"
    justificativa_edicao_rh = models.TextField(blank=True, null=True, help_text="Justificativa da edição feita pelo RH para o gestor revisar.")
    observacao_rejeicao = models.TextField(blank=True, null=True, help_text="Motivo da rejeição final.")


    # --- 3. HISTÓRICO SIMPLIFICADO ---
    # (Opcional, mas mais simples que o anterior)
    aprovado_por_gestor = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    data_aprovacao_gestor = models.DateTimeField(null=True, blank=True)
    aprovado_por_rh = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    data_aprovacao_rh = models.DateTimeField(null=True, blank=True)
    rejeitado_por = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    data_rejeicao = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        numero = f"RP #{self.id}: "
        return f"{numero}{self.vaga.titulo} por {self.solicitante.nome}"

    # --- 4. NOVA FUNÇÃO AUXILIAR ---
    def get_rh_approver(self):
        """ 
        Encontra o aprovador do RH.
        Busca qualquer funcionário ativo nos setores 'RECURSOS HUMANOS' ou 'DEPARTAMENTO PESSOAL'.
        Dá preferência para Níveis mais altos (Gestor/Coordenador/Supervisor).
        """
        # Nomes exatos dos setores, case-insensitive
        rh_sector_names = ["RECURSOS HUMANOS", "DEPARTAMENTO DE PESSOAL"]
        
        # Cria uma consulta Q para buscar em qualquer um dos nomes, ignorando maiúsculas
        q_objects = Q()
        for name in rh_sector_names:
            q_objects |= Q(setor_primario__nome__iexact=name) # __iexact = case-insensitive

        try:
            # Tenta encontrar QUALQUER funcionário ativo nesses setores
            rh_approver = Funcionario.objects.filter(
                q_objects,  # Filtra pelos setores de RH/DP
                ativo=True
            ).order_by('cargo__nivel').first() # Pega o de nível mais alto (Ex: Nível 3) primeiro

            if rh_approver:
                # --- SUCESSO! ---
                # Com base nas suas imagens, isso vai encontrar o 
                # "DIEGO WALLACE ARAUJO DA COSTA" (Nível 3) do DP.
                return rh_approver 
            
            # Fallback: Se não achar NINGUÉM no RH/DP, aí sim pega o Diretor (Nível 1)
            return Funcionario.objects.filter(cargo__nivel=1, ativo=True).first()

        except Exception:
            # Fallback final: Pega o Diretor (Nível 1) em caso de erro
            return Funcionario.objects.filter(cargo__nivel=1, ativo=True).first()

    # --- 5. LÓGICA DE APROVADOR INICIAL (CORRIGIDA) ---
    def set_initial_approver(self):
        """Define o status e o aprovador inicial ao criar a RP."""
        # Usa a função `obter_superiores()` que JÁ EXISTE E FUNCIONA
        superiores = self.solicitante.obter_superiores()
        
        # Tenta encontrar o Coordenador (Nível 3) ou Gestor (Nível 2)
        # Níveis 2=Gestor, 3=Coordenador
        gestor_ou_coordenador = superiores.filter(cargo__nivel__in=[2, 3]).order_by('cargo__nivel').first()

        if gestor_ou_coordenador:
            self.aprovador_atual = gestor_ou_coordenador
            self.status = 'pendente_gestor'
        else:
            # Se não achar Gestor (ex: um gestor abriu a RP), vai direto pro RH
            self.aprovador_atual = self.get_rh_approver()
            self.status = 'pendente_rh'

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if is_new and not self.status: # Define SÓ se for novo e o status não estiver definido
            self.set_initial_approver()
        super().save(*args, **kwargs)

    # --- 6. MÁQUINA DE ESTADOS (AVANÇAR) ---
    def avancar_aprovacao(self, aprovador_que_aprovou):
        """ Move a RP para o próximo estágio (Gestor -> RH -> Aprovada) """
        now = timezone.now()

        # Cenário 1: Gestor está aprovando (primeira vez ou re-aprovação)
        if self.status == 'pendente_gestor' or self.status == 'em_revisao_gestor':
            self.aprovado_por_gestor = aprovador_que_aprovou
            self.data_aprovacao_gestor = now
            
            # Limpa a justificativa de edição (caso seja uma re-aprovação)
            self.justificativa_edicao_rh = None 
            
            # Próximo passo: RH
            self.status = 'pendente_rh'
            self.aprovador_atual = self.get_rh_approver()

        # Cenário 2: RH está aprovando
        elif self.status == 'pendente_rh':
            self.aprovado_por_rh = aprovador_que_aprovou
            self.data_aprovacao_rh = now
            
            # Próximo passo: Fim do fluxo
            self.status = 'aprovada'
            self.aprovador_atual = None # Ninguém mais precisa aprovar

        self.save()

    # --- 7. REJEITAR (ATUALIZADO) ---
    def rejeitar(self, aprovador_que_rejeitou, observacao):
        """ Marca a RP como rejeitada. """
        self.status = 'rejeitada'
        self.rejeitado_por = aprovador_que_rejeitou
        self.data_rejeicao = timezone.now()
        self.observacao_rejeicao = observacao
        self.aprovador_atual = None
        self.save()

    # --- 8. DEVOLVER PARA GESTOR (NOVA FUNÇÃO) ---
    def devolver_para_gestor(self, rh_editor, justificativa):
        """ O RH edita e devolve para o Gestor re-aprovar. """
        if self.status != 'pendente_rh':
            # Só pode fazer isso se estiver pendente no RH
            return

        self.status = 'em_revisao_gestor'
        self.justificativa_edicao_rh = justificativa
        
        # Encontra o Gestor original (Nível 2 ou 3) do solicitante
        superiores = self.solicitante.obter_superiores()
        gestor_original = superiores.filter(cargo__nivel__in=[2, 3]).order_by('cargo__nivel').first()

        if gestor_original:
            self.aprovador_atual = gestor_original
        else:
            # Fallback: Se não achar, manda pro RH de novo (estranho, mas seguro)
            self.aprovador_atual = self.get_rh_approver()
            self.status = 'pendente_rh' # Volta pro RH
            
        self.save()


    class Meta:
        verbose_name = "Requisição Pessoal"
        verbose_name_plural = "Requisições Pessoais"
        ordering = ['-criado_em']

class MovimentacaoPessoal(models.Model):
    # --- 1. Status do Fluxo ATUALIZADOS ---
    STATUS_MP_CHOICES = [
        ('pendente_gestores', 'Pendente Gestores (Atual e Proposto)'), # Novo status inicial
        ('pendente_rh', 'Pendente RH'),
        ('aprovada', 'Aprovada'),
        ('rejeitada', 'Rejeitada'),
    ]


    # --- Dados do Solicitante e Funcionário ---
    solicitante = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name='mps_solicitadas', verbose_name="Solicitante (ADM)")
    funcionario_movido = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name='movimentacoes', verbose_name="Funcionário a ser Movido")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data da Solicitação")
    atualizado_em = models.DateTimeField(auto_now=True)

    # --- Dados Atuais ---
    cargo_atual = models.ForeignKey(Cargo, on_delete=models.PROTECT, related_name='+', verbose_name="Cargo Atual", null=True, blank=True)
    setor_atual = models.ForeignKey(Setor, on_delete=models.PROTECT, related_name='+', verbose_name="Setor Atual", null=True, blank=True)
    salario_atual = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Salário Atual")

    # --- Dados Propostos ---
    cargo_proposto = models.ForeignKey(Cargo, on_delete=models.PROTECT, related_name='+', verbose_name="Cargo Proposto")
    setor_proposto = models.ForeignKey(Setor, on_delete=models.PROTECT, related_name='+', verbose_name="Setor Proposto")
    salario_proposto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Salário Proposto")
    data_efetiva = models.DateField(verbose_name="Data Efetiva da Movimentação")
    justificativa = models.TextField(verbose_name="Justificativa da Movimentação")

    # --- 2. NOVO Controle de Aprovação (Paralelo) ---
    status = models.CharField(max_length=30, choices=STATUS_MP_CHOICES, default='pendente_gestores', verbose_name="Status da Movimentação")
    
    # Aprovadores (quem deve aprovar)
    aprovador_gestor_proposto = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='mps_para_aprovar_proposto')
    aprovador_gestor_atual = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='mps_para_aprovar_atual')
    aprovador_rh = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='mps_para_aprovar_rh')

    # Histórico (quem já aprovou)
    gestor_proposto_aprovou = models.BooleanField(default=False, verbose_name="Gestor Proposto Aprovou?")
    data_aprovacao_gestor_proposto = models.DateTimeField(null=True, blank=True)
    
    gestor_atual_aprovou = models.BooleanField(default=False, verbose_name="Gestor Atual Aprovou?")
    data_aprovacao_gestor_atual = models.DateTimeField(null=True, blank=True)
    
    aprovado_por_rh = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='mps_aprovadas_rh')
    data_aprovacao_rh = models.DateTimeField(null=True, blank=True)
    
    # Rejeição
    rejeitado_por = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='mps_rejeitadas')
    data_rejeicao = models.DateTimeField(null=True, blank=True)
    observacao_rejeicao = models.TextField(blank=True, null=True, help_text="Motivo da rejeição.")


    def __str__(self):
        return f"MP #{self.id}: {self.funcionario_movido.nome} para {self.cargo_proposto.nome}"

    # --- 3. Funções Auxiliares ATUALIZADAS (Corrigidas) ---
    def _get_gestor_setor(self, setor):
        """ 
        Encontra o Gestor (Nível 2) ou Coordenador (Nível 3) de um setor.
        Verifica 'setor_primario' E 'setores_responsaveis'.
        """
        if not setor:
            return None
        
        # Q para Nível 2 ou 3
        nivel_q = Q(cargo__nivel__in=[2, 3])
        
        # Q para Setor (Primário OU Responsável)
        setor_q = Q(setor_primario=setor) | Q(setores_responsaveis=setor)
        
        try:
            gestor = Funcionario.objects.filter(
                nivel_q, 
                setor_q,
                ativo=True
            ).distinct().order_by('-cargo__nivel').first() # Prefere Nível 2 (Gestor)
            return gestor
        except Funcionario.DoesNotExist:
            return None

    def _get_rh_approver(self):
        """ Encontra o aprovador do RH (Copiado/Adaptado de RequisicaoPessoal). """
        rh_sector_names = ["RECURSOS HUMANOS", "DEPARTAMENTO DE PESSOAL"]
        q_objects = Q()
        for name in rh_sector_names:
            q_objects |= Q(setor_primario__nome__iexact=name)
        try:
            rh_approver = Funcionario.objects.filter(q_objects, ativo=True).order_by('cargo__nivel').first()
            if rh_approver: return rh_approver
            return Funcionario.objects.filter(cargo__nivel=1, ativo=True).first()
        except Exception:
            return Funcionario.objects.filter(cargo__nivel=1, ativo=True).first()


    # --- 4. Lógica de Workflow ATUALIZADA ---

    def _check_gestor_approvals(self):
        """ Verifica se ambos os gestores aprovaram para mover ao RH. """
        if self.gestor_proposto_aprovou and self.gestor_atual_aprovou and self.status == 'pendente_gestores':
            self.status = 'pendente_rh'
            self.aprovador_rh = self._get_rh_approver()
            self.save()

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if is_new:
            # Preenche os dados atuais
            self.cargo_atual = self.funcionario_movido.cargo
            self.setor_atual = self.funcionario_movido.setor_primario
            # self.salario_atual = ... # Adicionar busca do salário atual
            
            # Encontra os aprovadores
            self.aprovador_gestor_proposto = self._get_gestor_setor(self.setor_proposto)
            self.aprovador_gestor_atual = self._get_gestor_setor(self.setor_atual)
            
            self.status = 'pendente_gestores'

            # Auto-aprova se não houver gestor (ou se for o mesmo gestor)
            if not self.aprovador_gestor_proposto:
                self.gestor_proposto_aprovou = True
            
            if not self.aprovador_gestor_atual:
                self.gestor_atual_aprovou = True
                
            # Se o gestor for o mesmo para atual e proposto
            if self.aprovador_gestor_proposto == self.aprovador_gestor_atual and self.aprovador_gestor_proposto is not None:
                # Deixa o Gestor Atual como o único a aprovar
                self.aprovador_gestor_proposto = None
                self.gestor_proposto_aprovou = True # Auto-aprova o "proposto"

        super().save(*args, **kwargs) # Salva primeiro

        if is_new:
            # Chama a verificação *depois* de salvar, caso ambos sejam auto-aprovados
            self._check_gestor_approvals()


    def aprovar(self, aprovador):
        """ Marca a aprovação de UM dos aprovadores. """
        if self.status != 'pendente_gestores':
            return # Só permite aprovação de gestor nesta etapa
        
        aprovou_algo = False
        if aprovador == self.aprovador_gestor_proposto and not self.gestor_proposto_aprovou:
            self.gestor_proposto_aprovou = True
            self.data_aprovacao_gestor_proposto = timezone.now()
            aprovou_algo = True
        
        if aprovador == self.aprovador_gestor_atual and not self.gestor_atual_aprovou:
            self.gestor_atual_aprovou = True
            self.data_aprovacao_gestor_atual = timezone.now()
            aprovou_algo = True
        
        if aprovou_algo:
            self.save()
            self._check_gestor_approvals() # Verifica se o fluxo avança para o RH
        

    def aprovar_rh(self, aprovador_rh):
        """ Aprovação final do RH. """
        if self.status != 'pendente_rh' or aprovador_rh != self.aprovador_rh:
            return False # Não pode aprovar
        
        self.aprovado_por_rh = aprovador_rh
        self.data_aprovacao_rh = timezone.now()
        self.status = 'aprovada'
        self.aprovador_gestor_proposto = None # Limpa aprovadores pendentes
        self.aprovador_gestor_atual = None
        self.aprovador_rh = None
        self.save()
        return True

    def rejeitar(self, aprovador_que_rejeitou, observacao):
        """ Marca a MP como rejeitada (qualquer aprovador pode rejeitar). """
        self.status = 'rejeitada'
        self.rejeitado_por = aprovador_que_rejeitou
        self.data_rejeicao = timezone.now()
        self.observacao_rejeicao = observacao
        self.aprovador_gestor_proposto = None # Limpa aprovadores pendentes
        self.aprovador_gestor_atual = None
        self.aprovador_rh = None
        self.save()

    class Meta:
        verbose_name = "Movimentação Pessoal"
        verbose_name_plural = "Movimentações Pessoais"
        ordering = ['-criado_em']



# --- ✅ NOVO MODELO: RequisicaoDesligamento ---
class RequisicaoDesligamento(models.Model):
    # --- Status do Fluxo ---
    STATUS_RD_CHOICES = [
        ('pendente_gestor', 'Pendente Gestor Imediato'),
        ('pendente_rh', 'Pendente RH'),
        ('aprovada', 'Aprovada (Desligamento Efetivado)'),
        ('rejeitada', 'Rejeitada'),
    ]
    TIPO_DESLIGAMENTO_CHOICES = [
        ('empresa', 'Iniciativa da Empresa'),
        ('funcionario', 'Iniciativa do Funcionário'),
    ]
    MOTIVO_CHOICES = [
        # Iniciativa da Empresa
        ('termino_contrato', 'Término de Contrato de Experiência'),
        ('reducao_quadro', 'Redução de Quadro'),
        ('baixo_desempenho', 'Baixo Desempenho'),
        ('justa_causa', 'Justa Causa'),
        # Iniciativa do Funcionário
        ('pedido_demissao', 'Pedido de Demissão'),
        ('abandono_emprego', 'Abandono de Emprego'),
        ('aposentadoria', 'Aposentadoria'),
        ('falecimento', 'Falecimento'),
        # Outros
        ('outro', 'Outro (Especificar na Justificativa)'),
    ]
    TIPO_AVISO_CHOICES = [
        ('trabalhado', 'Trabalhado'),
        ('indenizado', 'Indenizado'),
        ('dispensado', 'Dispensa de Cumprimento'),
        ('nao_se_aplica', 'Não se Aplica'),
    ]

    # --- Dados do Solicitante e Funcionário ---
    solicitante = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name='rds_solicitadas', verbose_name="Solicitante (ADM)")
    funcionario_desligado = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name='desligamentos', verbose_name="Funcionário a ser Desligado")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data da Solicitação")
    atualizado_em = models.DateTimeField(auto_now=True)

    # --- Dados Atuais (Auto-preenchidos) ---
    cargo_atual = models.ForeignKey(Cargo, on_delete=models.PROTECT, related_name='+', verbose_name="Cargo Atual", null=True, blank=True)
    setor_atual = models.ForeignKey(Setor, on_delete=models.PROTECT, related_name='+', verbose_name="Setor Atual", null=True, blank=True)
    data_admissao = models.DateField(null=True, blank=True, verbose_name="Data de Admissão")

    # --- Detalhes do Desligamento (Preenchidos pelo ADM) ---
    tipo_desligamento = models.CharField(max_length=20, choices=TIPO_DESLIGAMENTO_CHOICES, verbose_name="Tipo de Desligamento")
    motivo = models.CharField(max_length=30, choices=MOTIVO_CHOICES, verbose_name="Motivo")
    data_prevista_desligamento = models.DateField(verbose_name="Data Prevista (Último dia)")
    tipo_aviso = models.CharField(max_length=20, choices=TIPO_AVISO_CHOICES, verbose_name="Tipo de Aviso Prévio")
    havera_substituicao = models.BooleanField(default=False, verbose_name="Haverá Substituição?")
    justificativa = models.TextField(verbose_name="Justificativa / Detalhes")

    # Opcional: Entrevista de Desligamento (pode ser preenchido pelo RH depois)
    entrevista_realizada = models.BooleanField(default=False, verbose_name="Entrevista de Desligamento Realizada?")
    data_entrevista = models.DateField(null=True, blank=True, verbose_name="Data da Entrevista")

    # --- Controle de Aprovação ---
    status = models.CharField(max_length=30, choices=STATUS_RD_CHOICES, verbose_name="Status da Requisição")
    aprovador_atual = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='rds_para_aprovar', verbose_name="Próximo Aprovador")
    observacao_rejeicao = models.TextField(blank=True, null=True, help_text="Motivo da rejeição.")

    # --- Histórico ---
    aprovado_por_gestor = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    data_aprovacao_gestor = models.DateTimeField(null=True, blank=True)
    aprovado_por_rh = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    data_aprovacao_rh = models.DateTimeField(null=True, blank=True)
    rejeitado_por = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    data_rejeicao = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"RD #{self.id}: Desligamento de {self.funcionario_desligado.nome}"

    # --- Funções Auxiliares ---
    def _get_gestor_imediato(self, setor):
        """ 
        Encontra o Gestor Imediato:
        1. Tenta Coordenador (Nível 3)
        2. Se não achar, tenta Gestor (Nível 2)
        """
        if not setor:
            return None
        
        setor_q = Q(setor_primario=setor) | Q(setores_responsaveis=setor)
        
        try:
            # 1. Tenta Coordenador (Nível 3)
            coordenador = Funcionario.objects.filter(
                Q(cargo__nivel=3), 
                setor_q,
                ativo=True
            ).distinct().first()
            
            if coordenador:
                return coordenador

            # 2. Se não achar, tenta Gestor (Nível 2)
            gestor = Funcionario.objects.filter(
                Q(cargo__nivel=2), 
                setor_q,
                ativo=True
            ).distinct().first()
            
            return gestor # Retorna o gestor ou None se não encontrar
            
        except Funcionario.DoesNotExist:
            return None

    def _get_rh_approver(self):
        """ Encontra o aprovador do RH (Copiado/Adaptado). """
        rh_sector_names = ["RECURSOS HUMANOS", "DEPARTAMENTO DE PESSOAL"]
        q_objects = Q()
        for name in rh_sector_names:
            q_objects |= Q(setor_primario__nome__iexact=name)
        try:
            rh_approver = Funcionario.objects.filter(q_objects, ativo=True).order_by('cargo__nivel').first()
            if rh_approver: return rh_approver
            return Funcionario.objects.filter(cargo__nivel=1, ativo=True).first()
        except Exception:
            return Funcionario.objects.filter(cargo__nivel=1, ativo=True).first()


    # --- Lógica de Workflow ---
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if is_new:
            # Preenche os dados atuais do funcionário
            self.cargo_atual = self.funcionario_desligado.cargo
            self.setor_atual = self.funcionario_desligado.setor_primario
            self.data_admissao = self.funcionario_desligado.data_admissao
            
            # Encontra o primeiro aprovador (Gestor Imediato)
            self.aprovador_atual = self._get_gestor_imediato(self.setor_atual)
            
            if self.aprovador_atual:
                self.status = 'pendente_gestor'
            else:
                # Se não encontrar gestor/coordenador, pula direto para o RH
                self.status = 'pendente_rh'
                self.aprovador_atual = self._get_rh_approver()

        super().save(*args, **kwargs)

    def avancar_aprovacao(self, aprovador):
        """ Move a RD para o próximo estágio (Gestor -> RH -> Aprovada) """
        now = timezone.now()

        # 1. Gestor aprovou
        if self.status == 'pendente_gestor' and aprovador == self.aprovador_atual:
            self.aprovado_por_gestor = aprovador
            self.data_aprovacao_gestor = now
            # Próximo passo: RH
            self.status = 'pendente_rh'
            self.aprovador_atual = self._get_rh_approver()
            self.save()

        # 2. RH aprovou
        elif self.status == 'pendente_rh' and aprovador == self.aprovador_atual:
            self.aprovado_por_rh = aprovador
            self.data_aprovacao_rh = now
            # Próximo passo: Fim
            self.status = 'aprovada'
            self.aprovador_atual = None
            self.save()
            
            # --- AÇÃO DE DESLIGAMENTO ---
            # Desativa o funcionário no sistema
            self.funcionario_desligado.ativo = False
            self.funcionario_desligado.save()
            # --------------------------

    def rejeitar(self, aprovador_que_rejeitou, observacao):
        """ Marca a RD como rejeitada. """
        self.status = 'rejeitada'
        self.rejeitado_por = aprovador_que_rejeitou
        self.data_rejeicao = timezone.now()
        self.observacao_rejeicao = observacao
        self.aprovador_atual = None
        self.save()

    class Meta:
        verbose_name = "Requisição de Desligamento"
        verbose_name_plural = "Requisições de Desligamento"
        ordering = ['-criado_em']