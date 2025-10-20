from django.db import models
# --- CORREÇÃO AQUI ---
# Garantindo que User, Permission e ContentType estão importados
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
# ---------------------
from django.core.validators import RegexValidator

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
    setor = models.ManyToManyField(Setor, related_name='funcionarios')
    centro_servico = models.ForeignKey(CentroServico, on_delete=models.SET_NULL, null=True, blank=True, related_name='funcionarios')
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['nome']
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
    
    def __str__(self):
        return f"{self.nome} - {self.cargo.nome}"

    def save(self, *args, **kwargs):
        """ 
        (LÓGICA DE PERMISSÃO)
        Sobrescreve o 'save' para dar permissões de admin baseadas no cargo 
        """
        # Salva o funcionário primeiro
        super().save(*args, **kwargs)

        # Se este funcionário está ligado a um usuário de login
        if self.usuario:
            # Níveis 1 a 4 (Diretor, Gestor, Coordenador, Supervisor)
            pode_gerenciar_equipe = self.cargo.nivel <= 4 
            
            # Dá acesso ao /admin/
            self.usuario.is_staff = pode_gerenciar_equipe
            
            try:
                # Pega as permissões do modelo "Funcionario"
                # (Agora ContentType e Permission estão importados)
                content_type = ContentType.objects.get_for_model(Funcionario)
                perm_add = Permission.objects.get(content_type=content_type, codename='add_funcionario')
                perm_change = Permission.objects.get(content_type=content_type, codename='change_funcionario')
                perm_view = Permission.objects.get(content_type=content_type, codename='view_funcionario')
                
                if pode_gerenciar_equipe:
                    self.usuario.user_permissions.add(perm_add, perm_change, perm_view)
                else:
                    self.usuario.user_permissions.remove(perm_add, perm_change, perm_view)
                
                self.usuario.save()

            except (Permission.DoesNotExist, ContentType.DoesNotExist):
                # Isso pode falhar na primeira migração. É seguro ignorar.
                pass
    
    def obter_nivel_hierarquico(self):
        return self.cargo.nivel
    
    def obter_superiores(self):
        """ (CORRIGIDO) Retorna todos os superiores hierárquicos (em qualquer setor do funcionário) """
        setores_do_funcionario = self.setor.all()
        
        superiores = Funcionario.objects.filter(
            setor__in=setores_do_funcionario,
            cargo__nivel__lt=self.cargo.nivel,
            ativo=True
        ).distinct().order_by('cargo__nivel')
        
        if self.centro_servico:
            superiores = superiores.filter(centro_servico=self.centro_servico)
        
        return superiores
    
    def obter_subordinados(self):
        """ (CORRIGIDO) Retorna todos os subordinados hierárquicos (em qualquer setor do funcionário) """
        setores_do_funcionario = self.setor.all()
        
        subordinados = Funcionario.objects.filter(
            setor__in=setores_do_funcionario,
            cargo__nivel__gt=self.cargo.nivel,
            ativo=True
        ).distinct().order_by('cargo__nivel')
        
        if self.centro_servico:
            subordinados = subordinados.filter(centro_servico=self.centro_servico)
            
        return subordinados
    
    def obter_subordinados_diretos(self):
        """ (CORRIGIDO) Retorna apenas os subordinados diretos (um nível abaixo) """
        nivel_esperado = self.cargo.nivel + 1
        setores_do_funcionario = self.setor.all()
        
        subordinados = Funcionario.objects.filter(
            setor__in=setores_do_funcionario,
            cargo__nivel=nivel_esperado,
            ativo=True
        ).distinct().order_by('nome')
        
        if self.centro_servico:
            subordinados = subordinados.filter(centro_servico=self.centro_servico)
            
        return subordinados


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