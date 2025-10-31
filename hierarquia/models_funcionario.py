# hierarquia/models_funcionario.py

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.validators import RegexValidator

# NOTA: Não importamos mais Cargo e Setor diretamente daqui

class Funcionario(models.Model):
    """
    Modelo ATUALIZADO para representar funcionários, mesclando
    a lógica do app (usuario, cargo, setores) com a estrutura
    completa da tabela SRA (Protheus).
    Movido para seu próprio arquivo para organização.
    """
    
    # --- 1. CAMPOS ESSENCIAIA PARA A LÓGICA DO APP (MANTIDOS) ---
    usuario = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='funcionario')
    
    # --- ✅ ALTERAÇÃO: Links para Cargo/Setor agora usam strings ---
    cargo = models.ForeignKey(
        'hierarquia.Cargo', 
        on_delete=models.PROTECT, 
        related_name='funcionarios', 
        verbose_name="Cargo (App)", 
        null=True, blank=True
    )
    setor_primario = models.ForeignKey(
        'hierarquia.Setor',
        on_delete=models.PROTECT,
        related_name='funcionarios_primarios',
        verbose_name='Setor Principal (App)',
        null=True, blank=True
    )
    setores_responsaveis = models.ManyToManyField(
        'hierarquia.Setor',
        related_name='responsaveis',
        blank=True,
        verbose_name='Setores Responsáveis (App)'
    )
    # --- Fim da Alteração ---

    ativo = models.BooleanField(default=True, verbose_name="Ativo (App)")

    # --- 2. NOVO CAMPO DE SALÁRIO CALCULADO ---
    salario_bruto_calculado = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Salário Bruto (Calculado)")


    # --- 3. CAMPOS DO PROTHEUS (SRA) - 226 CAMPOS ---
    ra_filial = models.CharField(max_length=2, blank=True, null=True, verbose_name="Filial")
    ra_mat = models.CharField(max_length=6, unique=True, verbose_name="Matricula") # Chave principal
    ra_nome = models.CharField(max_length=40, blank=True, null=True, verbose_name="Nome do Funcionario")
    ra_barra = models.CharField(max_length=13, blank=True, null=True, verbose_name="Codigo de Barras")
    ra_inativo = models.CharField(max_length=1, blank=True, null=True, verbose_name="Inativo")
    ra_dataini = models.CharField(max_length=8, blank=True, null=True, verbose_name="Inicio do Periodo")
    ra_datafim = models.CharField(max_length=8, blank=True, null=True, verbose_name="Fim do Periodo")
    ra_horario = models.CharField(max_length=3, blank=True, null=True, verbose_name="Horario Padrao")
    ra_sexo = models.CharField(max_length=1, blank=True, null=True, verbose_name="Sexo")
    ra_dtnasc = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data de Nascimento")
    ra_estcivi = models.CharField(max_length=1, blank=True, null=True, verbose_name="Estado Civil")
    ra_grinst = models.CharField(max_length=1, blank=True, null=True, verbose_name="Grau de Instrucao")
    ra_naciona = models.CharField(max_length=3, blank=True, null=True, verbose_name="Nacionalidade")
    ra_anocheg = models.CharField(max_length=4, blank=True, null=True, verbose_name="Ano de Chegada")
    ra_tipovst = models.CharField(max_length=1, blank=True, null=True, verbose_name="Tipo de Visto")
    ra_dtvencv = models.CharField(max_length=8, blank=True, null=True, verbose_name="Vencimento do Visto")
    ra_natural = models.CharField(max_length=20, blank=True, null=True, verbose_name="Naturalidade")
    ra_ufnatu = models.CharField(max_length=2, blank=True, null=True, verbose_name="UF Naturalidade")
    ra_codpais = models.CharField(max_length=5, blank=True, null=True, verbose_name="Cod. Pais Nascim.")
    ra_codmunic = models.CharField(max_length=5, blank=True, null=True, verbose_name="Municipio Nasc.")
    ra_mudou = models.CharField(max_length=1, blank=True, null=True, verbose_name="Mudou Endereco")
    ra_bairro = models.CharField(max_length=20, blank=True, null=True, verbose_name="Bairro")
    ra_tipo = models.CharField(max_length=3, blank=True, null=True, verbose_name="Tipo de Logradouro")
    ra_logra = models.CharField(max_length=40, blank=True, null=True, verbose_name="Logradouro")
    ra_numero = models.CharField(max_length=6, blank=True, null=True, verbose_name="Numero")
    ra_complem = models.CharField(max_length=15, blank=True, null=True, verbose_name="Complemento")
    ra_estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="Estado")
    ra_codmuni = models.CharField(max_length=5, blank=True, null=True, verbose_name="Cod. de Municipio")
    ra_munic = models.CharField(max_length=20, blank=True, null=True, verbose_name="Municipio")
    ra_cep = models.CharField(max_length=8, blank=True, null=True, verbose_name="CEP")
    ra_email = models.CharField(max_length=40, blank=True, null=True, verbose_name="E-Mail")
    ra_ddd = models.CharField(max_length=3, blank=True, null=True, verbose_name="DDD")
    ra_telefon = models.CharField(max_length=15, blank=True, null=True, verbose_name="Telefone")
    ra_numres = models.CharField(max_length=6, blank=True, null=True, verbose_name="Numero")
    ra_tipores = models.CharField(max_length=3, blank=True, null=True, verbose_name="Tipo de Logradouro")
    ra_reslog = models.CharField(max_length=40, blank=True, null=True, verbose_name="Logradouro")
    ra_rescomp = models.CharField(max_length=15, blank=True, null=True, verbose_name="Complemento")
    ra_resbai = models.CharField(max_length=20, blank=True, null=True, verbose_name="Bairro")
    ra_resmunic = models.CharField(max_length=20, blank=True, null=True, verbose_name="Municipio")
    ra_resuf = models.CharField(max_length=2, blank=True, null=True, verbose_name="Estado")
    ra_rescep = models.CharField(max_length=8, blank=True, null=True, verbose_name="CEP")
    ra_resddd = models.CharField(max_length=3, blank=True, null=True, verbose_name="DDD")
    ra_restel = models.CharField(max_length=15, blank=True, null=True, verbose_name="Telefone")
    ra_celula = models.CharField(max_length=15, blank=True, null=True, verbose_name="Celular")
    ra_tipocel = models.CharField(max_length=1, blank=True, null=True, verbose_name="Tipo Celular")
    ra_apvdesc = models.CharField(max_length=6, blank=True, null=True, verbose_name="Aprov. Desconto")
    ra_admissa = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data de Admissao")
    ra_codfunc = models.CharField(max_length=5, blank=True, null=True, verbose_name="Funcao")
    ra_cbocod = models.CharField(max_length=6, blank=True, null=True, verbose_name="CBO")
    ra_viemrai = models.CharField(max_length=1, blank=True, null=True, verbose_name="Vinculo Empregaticio")
    ra_tipoadm = models.CharField(max_length=1, blank=True, null=True, verbose_name="Tipo de Admissao")
    ra_postatu = models.CharField(max_length=6, blank=True, null=True, verbose_name="Posto de Trabalho")
    ra_dtrecon = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data de Reconducao")
    ra_dtexpv = models.CharField(max_length=8, blank=True, null=True, verbose_name="Venc. Exp. 1")
    ra_dtexpv2 = models.CharField(max_length=8, blank=True, null=True, verbose_name="Venc. Exp. 2")
    ra_contrpr = models.CharField(max_length=2, blank=True, null=True, verbose_name="Dias Exp. 1")
    ra_contrpr2 = models.CharField(max_length=2, blank=True, null=True, verbose_name="Dias Exp. 2")
    ra_opsindic = models.CharField(max_length=1, blank=True, null=True, verbose_name="Optante Sindical")
    ra_sindica = models.CharField(max_length=3, blank=True, null=True, verbose_name="Sindicato")
    ra_catsind = models.CharField(max_length=2, blank=True, null=True, verbose_name="Categoria Sindical")
    ra_cc = models.CharField(max_length=9, blank=True, null=True, verbose_name="Centro de Custo")
    ra_ctdp = models.CharField(max_length=5, blank=True, null=True, verbose_name="Codigo Departamento")
    ra_nivfunc = models.CharField(max_length=3, blank=True, null=True, verbose_name="Nivel")
    ra_estabil = models.CharField(max_length=1, blank=True, null=True, verbose_name="Estabilidade")
    ra_dtdesl = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Estabilidade")
    ra_demissa = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data de Demissao")
    ra_caudem = models.CharField(max_length=2, blank=True, null=True, verbose_name="Causa da Demissao")
    ra_obsmot = models.TextField(blank=True, null=True, verbose_name="Obs. Motivo Demissao") # Mapeado para TextField
    ra_avsopag = models.CharField(max_length=1, blank=True, null=True, verbose_name="Aviso Previo")
    ra_diaprid = models.CharField(max_length=2, blank=True, null=True, verbose_name="Dias Aviso Previo")
    ra_dtabspg = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Aviso Previo")
    ra_tipopgt = models.CharField(max_length=1, blank=True, null=True, verbose_name="Tipo de Pagamento")
    ra_formpgt = models.CharField(max_length=1, blank=True, null=True, verbose_name="Forma de Pagamento")
    ra_banco = models.CharField(max_length=3, blank=True, null=True, verbose_name="Banco")
    ra_agencia = models.CharField(max_length=5, blank=True, null=True, verbose_name="Agencia")
    ra_conta = models.CharField(max_length=12, blank=True, null=True, verbose_name="Conta Corrente")
    ra_tipoconta = models.CharField(max_length=1, blank=True, null=True, verbose_name="Tipo de Conta")
    ra_digcta = models.CharField(max_length=1, blank=True, null=True, verbose_name="Digito da Conta")
    ra_digag = models.CharField(max_length=1, blank=True, null=True, verbose_name="Digito da Agencia")
    ra_dtpag = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Pagto. Credito")
    ra_bancpa = models.CharField(max_length=3, blank=True, null=True, verbose_name="Banco Pagamento")
    ra_agencpa = models.CharField(max_length=5, blank=True, null=True, verbose_name="Agencia Pagamento")
    ra_contapa = models.CharField(max_length=12, blank=True, null=True, verbose_name="Conta Pagamento")
    ra_digcpa = models.CharField(max_length=1, blank=True, null=True, verbose_name="Digito Cta Pagto.")
    ra_digapa = models.CharField(max_length=1, blank=True, null=True, verbose_name="Digito Ag. Pagto.")
    ra_valet = models.CharField(max_length=1, blank=True, null=True, verbose_name="Recebe Vale Transp.")
    ra_numvtic = models.CharField(max_length=10, blank=True, null=True, verbose_name="Cartao VT")
    ra_codmova = models.CharField(max_length=2, blank=True, null=True, verbose_name="Motivo do Ponto")
    ra_pontac = models.CharField(max_length=1, blank=True, null=True, verbose_name="Ponto")
    ra_numcp = models.CharField(max_length=7, blank=True, null=True, verbose_name="Carteira Profiss.")
    ra_sercp = models.CharField(max_length=5, blank=True, null=True, verbose_name="Serie C.P.")
    ra_dtcp = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Exp. C.P.")
    ra_ufcp = models.CharField(max_length=2, blank=True, null=True, verbose_name="UF C.P.")
    ra_zonasec = models.CharField(max_length=3, blank=True, null=True, verbose_name="Zona")
    ra_titular = models.CharField(max_length=12, blank=True, null=True, verbose_name="Titulo de Eleitor")
    ra_secao = models.CharField(max_length=4, blank=True, null=True, verbose_name="Secao")
    ra_pis = models.CharField(max_length=11, blank=True, null=True, verbose_name="PIS")
    ra_dtcadpi = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Cadast. PIS")
    ra_bancopi = models.CharField(max_length=3, blank=True, null=True, verbose_name="Banco PIS")
    ra_agpis = models.CharField(max_length=5, blank=True, null=True, verbose_name="Agencia PIS")
    ra_endpis = models.CharField(max_length=30, blank=True, null=True, verbose_name="Endereco Banco PIS")
    ra_cic = models.CharField(max_length=11, blank=True, null=True, verbose_name="CPF")
    ra_rg = models.CharField(max_length=15, blank=True, null=True, verbose_name="RG")
    ra_dtexprg = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Exp. RG")
    ra_orgemrg = models.CharField(max_length=10, blank=True, null=True, verbose_name="Orgao Emissor RG")
    ra_ufrg = models.CharField(max_length=2, blank=True, null=True, verbose_name="UF RG")
    ra_ctdtem = models.CharField(max_length=1, blank=True, null=True, verbose_name="Contrib. Sindical")
    ra_certres = models.CharField(max_length=15, blank=True, null=True, verbose_name="Cert. Reservista")
    ra_catres = models.CharField(max_length=3, blank=True, null=True, verbose_name="Categoria Reserv.")
    ra_sreser = models.CharField(max_length=5, blank=True, null=True, verbose_name="Serie Reservista")
    ra_regprof = models.CharField(max_length=20, blank=True, null=True, verbose_name="Reg. Profissional")
    ra_dtregpr = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Reg. Prof.")
    ra_orgreg = models.CharField(max_length=10, blank=True, null=True, verbose_name="Orgao Reg. Prof.")
    ra_cartmot = models.CharField(max_length=11, blank=True, null=True, verbose_name="Carteira Motorista")
    ra_cathab = models.CharField(max_length=5, blank=True, null=True, verbose_name="Categoria Habilit.")
    ra_habven = models.CharField(max_length=8, blank=True, null=True, verbose_name="Venc. Habilitacao")
    ra_regmtr = models.CharField(max_length=11, blank=True, null=True, verbose_name="No. Reg. MTE")
    ra_prorrog = models.CharField(max_length=1, blank=True, null=True, verbose_name="Prorrogacao CNH")
    ra_nomepai = models.CharField(max_length=40, blank=True, null=True, verbose_name="Nome do Pai")
    ra_nomemae = models.CharField(max_length=40, blank=True, null=True, verbose_name="Nome da Mae")
    ra_conjug = models.CharField(max_length=40, blank=True, null=True, verbose_name="Nome do Conjuge")
    ra_nacioc = models.CharField(max_length=3, blank=True, null=True, verbose_name="Nacional. Conjuge")
    ra_nfilhos = models.FloatField(default=0, verbose_name="No. de Filhos")
    ra_filhom = models.FloatField(default=0, verbose_name="No. Filhos Menores")
    ra_filhomai = models.FloatField(default=0, verbose_name="No. Filhos Maiores")
    ra_ultnasc = models.CharField(max_length=8, blank=True, null=True, verbose_name="Nasc. Ultimo Filho")
    ra_salario = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Salario Base (RA_SALARIO)")
    ra_hisalul = models.CharField(max_length=8, blank=True, null=True, verbose_name="Ult. Altera Salar.")
    ra_perinsa = models.FloatField(default=0, verbose_name="% Insalubridade")
    ra_perper = models.FloatField(default=0, verbose_name="% Periculosidade")
    ra_adcinte = models.CharField(max_length=1, blank=True, null=True, verbose_name="Adic. Tempo Serv.")
    ra_sbase = models.CharField(max_length=3, blank=True, null=True, verbose_name="Sindicato Base")
    ra_peradit = models.FloatField(default=0, verbose_name="% Adic. T. Serv.")
    ra_prevpri = models.CharField(max_length=1, blank=True, null=True, verbose_name="Prev. Privada")
    ra_codprev = models.CharField(max_length=6, blank=True, null=True, verbose_name="Codigo Prev.")
    ra_catprev = models.CharField(max_length=2, blank=True, null=True, verbose_name="Categ. Prev.")
    ra_valprev = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Valor Prev.")
    ra_vlrbase = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Valor Base Prev.")
    ra_matprev = models.CharField(max_length=15, blank=True, null=True, verbose_name="Matricula Prev.")
    ra_segvid = models.CharField(max_length=1, blank=True, null=True, verbose_name="Seguro de Vida")
    ra_codseg = models.CharField(max_length=6, blank=True, null=True, verbose_name="Codigo Seguro")
    ra_catseg = models.CharField(max_length=2, blank=True, null=True, verbose_name="Categoria Seguro")
    ra_valseg = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Valor Seguro")
    ra_vbseg = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Valor Base Seguro")
    ra_matseg = models.CharField(max_length=15, blank=True, null=True, verbose_name="Matricula Seguro")
    ra_assmed = models.CharField(max_length=1, blank=True, null=True, verbose_name="Assist. Medica")
    ra_codmed = models.CharField(max_length=6, blank=True, null=True, verbose_name="Codigo Ass. Med.")
    ra_catmed = models.CharField(max_length=2, blank=True, null=True, verbose_name="Categoria Ass. Med.")
    ra_valmed = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Valor Ass. Med.")
    ra_vbmed = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Valor Base Ass. Med.")
    ra_matmed = models.CharField(max_length=15, blank=True, null=True, verbose_name="Matricula Ass. Med.")
    ra_nmedica = models.CharField(max_length=6, blank=True, null=True, verbose_name="No. Plano Saude")
    ra_tippla = models.CharField(max_length=1, blank=True, null=True, verbose_name="Tipo Plano")
    ra_dtinic = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Ini. Cobranca")
    ra_dtexcl = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Exc. Cobranca")
    ra_descont = models.CharField(max_length=1, blank=True, null=True, verbose_name="Desconto")
    ra_valadds = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Valor Adic. Saude")
    ra_dtreadm = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Readmissao")
    ra_afastad = models.CharField(max_length=1, blank=True, null=True, verbose_name="Afastado")
    ra_dtafas = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Afastamento")
    ra_codafas = models.CharField(max_length=2, blank=True, null=True, verbose_name="Cod. Afastamento")
    ra_dtreaf = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Ret. Afast.")
    ra_numdias = models.FloatField(default=0, verbose_name="No. Dias Afastado")
    ra_ultfech = models.CharField(max_length=8, blank=True, null=True, verbose_name="Ult. Fech. Ponto")
    ra_situaca = models.CharField(max_length=1, blank=True, null=True, verbose_name="Situacao")
    ra_memcalc = models.TextField(blank=True, null=True, verbose_name="Memo de Calculo")
    ra_ferprot = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Prot. Ferias")
    ra_fervenc = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Venc. Ferias")
    ra_ferprep = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Prep. Ferias")
    ra_fervcta = models.CharField(max_length=8, blank=True, null=True, verbose_name="Venc. 1a. Parc.")
    ra_fervctb = models.CharField(max_length=8, blank=True, null=True, verbose_name="Venc. 2a. Parc.")
    ra_ferlim = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Lim. Ferias")
    ra_fprotes = models.CharField(max_length=8, blank=True, null=True, verbose_name="Prot. Ferias Esc.")
    ra_fprepes = models.CharField(max_length=8, blank=True, null=True, verbose_name="Prep. Ferias Esc.")
    ra_fvctaes = models.CharField(max_length=8, blank=True, null=True, verbose_name="Venc. 1a. Esc.")
    ra_fvctbes = models.CharField(max_length=8, blank=True, null=True, verbose_name="Venc. 2a. Esc.")
    ra_flimes = models.CharField(max_length=8, blank=True, null=True, verbose_name="Lim. Ferias Esc.")
    ra_fgrprot = models.CharField(max_length=8, blank=True, null=True, verbose_name="Prot. Ferias G.")
    ra_fgrprep = models.CharField(max_length=8, blank=True, null=True, verbose_name="Prep. Ferias G.")
    ra_fgrvcta = models.CharField(max_length=8, blank=True, null=True, verbose_name="Venc. 1a. G.")
    ra_fgrvctb = models.CharField(max_length=8, blank=True, null=True, verbose_name="Venc. 2a. G.")
    ra_fgrlim = models.CharField(max_length=8, blank=True, null=True, verbose_name="Lim. Ferias G.")
    ra_pag13 = models.CharField(max_length=1, blank=True, null=True, verbose_name="Recebe 13o. Sal.")
    ra_adianta = models.CharField(max_length=1, blank=True, null=True, verbose_name="Recebe Adiantamto.")
    ra_recfer = models.CharField(max_length=1, blank=True, null=True, verbose_name="Recebe Ferias")
    ra_adfer = models.CharField(max_length=1, blank=True, null=True, verbose_name="Adiant. 13o. Sal.")
    ra_readmis = models.CharField(max_length=1, blank=True, null=True, verbose_name="Readmissao")
    ra_ultcal = models.CharField(max_length=6, blank=True, null=True, verbose_name="Ult. Calc. Folha")
    ra_saldfer = models.FloatField(default=0, verbose_name="Saldo Ferias")
    ra_saldfej = models.FloatField(default=0, verbose_name="Sld. Ferias (JA)")
    ra_vendfer = models.FloatField(default=0, verbose_name="Sld. Venda Ferias")
    ra_saldabn = models.FloatField(default=0, verbose_name="Sld. Abono Ferias")
    ra_saldabj = models.FloatField(default=0, verbose_name="Sld. Abono (JA)")
    ra_faltas = models.FloatField(default=0, verbose_name="Faltas")
    ra_saldlic = models.FloatField(default=0, verbose_name="Licenca Premio")
    ra_histalt = models.TextField(blank=True, null=True, verbose_name="Hist. Alteracoes")
    ra_hrssem = models.FloatField(default=0, verbose_name="Horas Semana")
    ra_hrsdia = models.FloatField(default=0, verbose_name="Horas Dia")
    ra_hrsmes = models.FloatField(default=0, verbose_name="Horas Mes")
    ra_codsind = models.CharField(max_length=3, blank=True, null=True, verbose_name="Sind. Categoria")
    ra_tipoprf = models.CharField(max_length=2, blank=True, null=True, verbose_name="Tipo Profissional")
    ra_cbo = models.CharField(max_length=4, blank=True, null=True, verbose_name="CBO")
    ra_cgcfav = models.CharField(max_length=14, blank=True, null=True, verbose_name="CGC Favorecido")
    ra_tipofav = models.CharField(max_length=1, blank=True, null=True, verbose_name="Tipo Favorecido")
    ra_nascfav = models.CharField(max_length=8, blank=True, null=True, verbose_name="Nasc. Favorecido")
    ra_favorec = models.CharField(max_length=40, blank=True, null=True, verbose_name="Favorecido")
    ra_bens = models.CharField(max_length=1, blank=True, null=True, verbose_name="Bens")
    ra_foto = models.CharField(max_length=1, blank=True, null=True, verbose_name="Possui Foto")
    ra_tnotrab = models.CharField(max_length=1, blank=True, null=True, verbose_name="Turno")
    ra_nivsal = models.CharField(max_length=3, blank=True, null=True, verbose_name="Nivel Salarial")
    ra_classec = models.CharField(max_length=1, blank=True, null=True, verbose_name="Classe Salarial")
    ra_faixa = models.CharField(max_length=3, blank=True, null=True, verbose_name="Faixa Salarial")
    ra_numprocesso = models.CharField(max_length=17, blank=True, null=True, verbose_name="No. Processo")
    ra_instruc = models.CharField(max_length=2, blank=True, null=True, verbose_name="Instrucao")
    ra_anofreq = models.CharField(max_length=1, blank=True, null=True, verbose_name="Ano Frequente")
    ra_alfabet = models.CharField(max_length=1, blank=True, null=True, verbose_name="Alfabetizado")
    ra_reservi = models.CharField(max_length=1, blank=True, null=True, verbose_name="Reservista")
    ra_recpror = models.CharField(max_length=1, blank=True, null=True, verbose_name="Reconh. Prorrog.")
    ra_numcart = models.CharField(max_length=11, blank=True, null=True, verbose_name="No. CNH")
    ra_tipocor = models.CharField(max_length=1, blank=True, null=True, verbose_name="Tipo Cor")
    ra_codraca = models.CharField(max_length=2, blank=True, null=True, verbose_name="Codigo Raca")
    ra_matfunc = models.CharField(max_length=6, blank=True, null=True, verbose_name="Matricula Func.")
    ra_codfor = models.CharField(max_length=6, blank=True, null=True, verbose_name="Fornecedor")
    ra_loja = models.CharField(max_length=2, blank=True, null=True, verbose_name="Loja")
    ra_process = models.CharField(max_length=20, blank=True, null=True, verbose_name="Processo")
    ra_dtexam = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Exame Medico")
    ra_tipopas = models.CharField(max_length=1, blank=True, null=True, verbose_name="Tipo Passagem")
    ra_valeped = models.CharField(max_length=1, blank=True, null=True, verbose_name="Recebe V.Pedagio")
    ra_coduser = models.CharField(max_length=6, blank=True, null=True, verbose_name="Cod. Usuario")
    ra_rhmata = models.CharField(max_length=6, blank=True, null=True, verbose_name="Mat. Atualizacao")
    ra_rhdata = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Atualizacao")
    ra_rhhora = models.CharField(max_length=8, blank=True, null=True, verbose_name="Hora Atualizacao")
    ra_codposto = models.CharField(max_length=6, blank=True, null=True, verbose_name="Cod. Posto INSS")
    ra_origem = models.CharField(max_length=1, blank=True, null=True, verbose_name="Origem")
    ra_vincemp = models.CharField(max_length=2, blank=True, null=True, verbose_name="Vinculo Empregado")
    ra_catfunc = models.CharField(max_length=1, blank=True, null=True, verbose_name="Categ. Funcional")
    ra_tpper = models.CharField(max_length=1, blank=True, null=True, verbose_name="Tipo de Periodo")
    ra_dpc = models.CharField(max_length=1, blank=True, null=True, verbose_name="DPC")
    ra_pensao = models.CharField(max_length=1, blank=True, null=True, verbose_name="Pensão")
    ra_tppens = models.CharField(max_length=1, blank=True, null=True, verbose_name="Tipo Pensão")
    ra_vlpens = models.FloatField(default=0, verbose_name="Valor Pensão")
    ra_perpens = models.FloatField(default=0, verbose_name="Percent. Pensão")
    ra_dtinpen = models.CharField(max_length=8, blank=True, null=True, verbose_name="Inicio Pensão")
    ra_dtfimpen = models.CharField(max_length=8, blank=True, null=True, verbose_name="Fim Pensão")
    ra_codfil = models.CharField(max_length=2, blank=True, null=True, verbose_name="Filial")
    ra_tpvinc = models.CharField(max_length=1, blank=True, null=True, verbose_name="Tipo Vinculo")
    ra_dtinicarg = models.CharField(max_length=8, blank=True, null=True, verbose_name="Inicio Cargo")
    ra_provim = models.CharField(max_length=1, blank=True, null=True, verbose_name="Provimento")
    ra_alter = models.CharField(max_length=1, blank=True, null=True, verbose_name="Alteracao")
    ra_altdata = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Alteracao")
    ra_altcbo = models.CharField(max_length=6, blank=True, null=True, verbose_name="CBO Alteracao")
    ra_valetrf = models.CharField(max_length=1, blank=True, null=True, verbose_name="V.T. Refeicao")
    ra_nmovi = models.CharField(max_length=6, blank=True, null=True, verbose_name="Movimentacao")
    ra_cidade = models.CharField(max_length=4, blank=True, null=True, verbose_name="Cidade")
    ra_defifi = models.CharField(max_length=1, blank=True, null=True, verbose_name="Def. Fisico")
    ra_defivi = models.CharField(max_length=1, blank=True, null=True, verbose_name="Def. Visual")
    ra_defiau = models.CharField(max_length=1, blank=True, null=True, verbose_name="Def. Auditiva")
    ra_defifa = models.CharField(max_length=1, blank=True, null=True, verbose_name="Def. Fala")
    ra_defime = models.CharField(max_length=1, blank=True, null=True, verbose_name="Def. Mental")
    ra_defimo = models.CharField(max_length=1, blank=True, null=True, verbose_name="Def. Motora")
    ra_outdef = models.CharField(max_length=20, blank=True, null=True, verbose_name="Outras Def.")
    ra_fgts = models.CharField(max_length=1, blank=True, null=True, verbose_name="Optante FGTS")
    ra_dtfgts = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Opcao FGTS")
    ra_contfg = models.CharField(max_length=12, blank=True, null=True, verbose_name="Conta FGTS")
    ra_catfgts = models.CharField(max_length=1, blank=True, null=True, verbose_name="Categoria FGTS")
    ra_codlot = models.CharField(max_length=6, blank=True, null=True, verbose_name="Cod. Lotacao")
    ra_prodtet = models.CharField(max_length=8, blank=True, null=True, verbose_name="Dt. Produtividade")
    ra_codarea = models.CharField(max_length=2, blank=True, null=True, verbose_name="Cod. Area")
    ra_codunid = models.CharField(max_length=5, blank=True, null=True, verbose_name="Cod. Unidade")
    ra_codtab = models.CharField(max_length=3, blank=True, null=True, verbose_name="Cod. Tabela")
    ra_refeic = models.CharField(max_length=1, blank=True, null=True, verbose_name="Recebe Refeicao")
    ra_perref = models.FloatField(default=0, verbose_name="Perc. Refeicao")
    ra_vlref = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Valor Refeicao")
    ra_reccesta = models.CharField(max_length=1, blank=True, null=True, verbose_name="Recebe Cesta Basica") # Corrigido nome
    ra_diacest = models.CharField(max_length=2, blank=True, null=True, verbose_name="Dia Cesta")
    ra_dtafast = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Afastamento")
    ra_bcafas = models.CharField(max_length=1, blank=True, null=True, verbose_name="Base Afastamento")
    ra_diasafa = models.FloatField(default=0, verbose_name="Dias Afastamento")
    ra_catind = models.CharField(max_length=2, blank=True, null=True, verbose_name="Categ. Indicador")
    ra_suecia = models.CharField(max_length=1, blank=True, null=True, verbose_name="Suecia")
    ra_altqdr = models.CharField(max_length=1, blank=True, null=True, verbose_name="Alt. Quadro")
    ra_bdi = models.CharField(max_length=3, blank=True, null=True, verbose_name="BDI")
    ra_plubs = models.CharField(max_length=1, blank=True, null=True, verbose_name="Plubs")
    ra_tabrub = models.CharField(max_length=2, blank=True, null=True, verbose_name="Tab. Rubrica")
    ra_chapa = models.CharField(max_length=6, blank=True, null=True, verbose_name="Chapa")
    ra_dtransf = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Transf.")
    ra_matant = models.CharField(max_length=6, blank=True, null=True, verbose_name="Mat. Anterior")
    ra_filant = models.CharField(max_length=2, blank=True, null=True, verbose_name="Filial Anterior")
    ra_usufluig = models.CharField(max_length=5, blank=True, null=True, verbose_name="Usuario Fluig")
    ra_dmedant = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Med. Anterior")
    ra_refrh = models.CharField(max_length=1, blank=True, null=True, verbose_name="Refeicao RH")
    ra_clfunc = models.CharField(max_length=3, blank=True, null=True, verbose_name="Classe Func.")
    ra_dtalcf = models.CharField(max_length=8, blank=True, null=True, verbose_name="Data Alt. Cl. Func.")
    ra_cnhdtve = models.CharField(max_length=8, blank=True, null=True, verbose_name="Venc. CNH")

    # --- Metadados e Métodos ---
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ra_nome']
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'

    def __str__(self):
        return f"{self.ra_nome} ({self.ra_mat})"

    def _calcular_salario_bruto(self):
        """
        Calcula o salário bruto com base nas regras de negócio do Protheus.
        ESTA LÓGICA É UM EXEMPLO E PRECISA SER VALIDADA/AJUSTADA POR VOCÊ.
        """
        try:
            # Converte todos para Decimal para segurança no cálculo
            base = self.ra_salario or 0
            per_insa = self.ra_perinsa or 0
            per_per = self.ra_perper or 0
            # Adicione outros campos base aqui (ex: ra_vlradic, ra_peradit, etc.)
            
            # TODO: ADICIONE SUA FÓRMULA DE CÁLCULO AQUI
            # Exemplo simples: Salário Base + (Base * % Insalubridade / 100) + (Base * % Periculosidade / 100)
            # NOTA: Muitas empresas calculam % sobre o salário mínimo, não sobre o base.
            # Verifique sua regra de negócio.
            
            # Exemplo de cálculo (SUBSTITUA PELA SUA LÓGICA):
            salario_bruto = base + (base * (per_insa / 100)) + (base * (per_per / 100))
            
            return salario_bruto
        except Exception as e:
            print(f"Erro ao calcular salário para {self.ra_mat}: {e}")
            return self.ra_salario or 0 # Retorna o base em caso de falha

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        
        # Tenta preencher o campo 'ativo' com base na situação da folha
        if self.ra_sitfolh:
            # D = Demitido, T = Transferido, A = Afastado, F = Férias
            if self.ra_sitfolh in ['D', 'T', 'A']: # Adicione 'F' se Férias = Inativo
                self.ativo = False
            else:
                self.ativo = True
        
        # ✅ Chama o cálculo do salário bruto
        self.salario_bruto_calculado = self._calcular_salario_bruto()

        super().save(*args, **kwargs)

        # Lógica de permissão de usuário (MANTIDA)
        if self.usuario:
            pode_gerenciar_equipe = False
            if self.cargo and self.cargo.nivel:
                pode_gerenciar_equipe = self.cargo.nivel <= 4

            self.usuario.is_staff = pode_gerenciar_equipe
            try:
                content_type = ContentType.objects.get_for_model(Funcionario)
                perm_add = Permission.objects.get(content_type=content_type, codename='add_funcionario')
                perm_change = Permission.objects.get(content_type=content_type, codename='change_funcionario')
                perm_view = Permission.objects.get(content_type=content_type, codename='view_funcionario')

                if pode_gerenciar_equipe:
                    self.usuario.user_permissions.add(perm_add, perm_change, perm_view)
                elif not is_new:
                    self.usuario.user_permissions.remove(perm_add, perm_change, perm_view)

                if is_new or self.usuario.is_staff != pode_gerenciar_equipe:
                    self.usuario.save()

            except (Permission.DoesNotExist, ContentType.DoesNotExist):
                pass # Ignora se permissões não existem (primeira migração)

    # --- MÉTODOS HIERÁRQUICOS ATUALIZADOS (MANTIDOS) ---
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
        # (Lógica original... mantida)
        if not self.cargo:
            return Funcionario.objects.none()

        subordinados = Funcionario.objects.none()
        if self.setor_primario:
            subordinados_primario = Funcionario.objects.filter(
                setor_primario=self.setor_primario,
                cargo__nivel__gt=self.cargo.nivel,
                ativo=True
            )
            subordinados = subordinados | subordinados_primario

        if incluir_responsaveis and self.setores_responsaveis.exists():
            setores_resp = self.setores_responsaveis.all()
            subordinados_responsaveis = Funcionario.objects.filter(
                setor_primario__in=setores_resp,
                cargo__nivel__gt=self.cargo.nivel,
                ativo=True
            ).exclude(pk=self.pk)
            subordinados = subordinados | subordinados_responsaveis
        
        return subordinados.distinct().order_by('setor_primario__nome', 'cargo__nivel', 'ra_nome') # Atualizado para ra_nome