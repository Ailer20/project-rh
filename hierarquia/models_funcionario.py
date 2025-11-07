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
    ra_filial = models.CharField(max_length=255, blank=True, null=True, verbose_name='Filial')
    ra_mat = models.CharField(max_length=255, blank=True, null=True, verbose_name='Matricula')
    ra_nome = models.CharField(max_length=255, blank=True, null=True, verbose_name='Nome')
    ra_nome_complet = models.CharField(max_length=255, blank=True, null=True, verbose_name='Nome complet')
    ra_nome_mae = models.CharField(max_length=255, blank=True, null=True, verbose_name='Nome Mae')
    ra_nome_pai = models.CharField(max_length=255, blank=True, null=True, verbose_name='Nome Pai')
    ra_sexo = models.CharField(max_length=255, blank=True, null=True, verbose_name='Sexo')
    ra_racacor = models.CharField(max_length=255, blank=True, null=True, verbose_name='Raca/Cor')
    ra_data_nasc = models.CharField(max_length=255, blank=True, null=True, verbose_name='Data Nasc.')
    ra_altdt_nasc = models.CharField(max_length=255, blank=True, null=True, verbose_name='Alt.Dt. Nasc')
    ra_est_civil = models.CharField(max_length=255, blank=True, null=True, verbose_name='Est. Civil')
    ra_codpais_ori = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cod.Pais Ori')
    ra_nacionalid = models.CharField(max_length=255, blank=True, null=True, verbose_name='Nacionalid.')
    ra_c_nacion_rfb = models.CharField(max_length=255, blank=True, null=True, verbose_name='C Nacion RFB')
    ra_branascext = models.CharField(max_length=255, blank=True, null=True, verbose_name='Bra.Nasc.Ext')
    ra_naturalid_uf = models.CharField(max_length=255, blank=True, null=True, verbose_name='Naturalid UF')
    ra_cod_mun_nasc = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cod Mun Nasc')
    ra_municpnasc = models.CharField(max_length=255, blank=True, null=True, verbose_name='Municp.Nasc.')
    ra_apelido = models.CharField(max_length=255, blank=True, null=True, verbose_name='Apelido')
    ra_cdinstrais = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cd.Inst.RAIS')
    ra_email_princ = models.CharField(max_length=255, blank=True, null=True, verbose_name='Email Princ')
    ra_email_altern = models.CharField(max_length=255, blank=True, null=True, verbose_name='Email Altern')
    ra_receb_email = models.CharField(max_length=255, blank=True, null=True, verbose_name='Receb E-Mail')
    ra_tipo_email = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tipo E-Mail')
    ra_brpdh = models.CharField(max_length=255, blank=True, null=True, verbose_name='BR/PDH')
    ra_tpdeficien = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tp.Deficien')
    ra_defi_esocial = models.CharField(max_length=255, blank=True, null=True, verbose_name='Defi eSocial')
    ra_centro_custo = models.CharField(max_length=255, blank=True, null=True, verbose_name='Centro Custo')
    ra_classe_valor = models.CharField(max_length=255, blank=True, null=True, verbose_name='Classe Valor')
    ra_item = models.CharField(max_length=255, blank=True, null=True, verbose_name='Item')
    ra_data_admis = models.CharField(max_length=255, blank=True, null=True, verbose_name='Data Admis.')
    ra_altadmissao = models.CharField(max_length=255, blank=True, null=True, verbose_name='Alt.Admissao')
    ra_tipo_admiss = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tipo Admiss.')
    ra_dep_ir = models.CharField(max_length=255, blank=True, null=True, verbose_name='Dep. I.R.')
    ra_depsalfam = models.CharField(max_length=255, blank=True, null=True, verbose_name='Dep.Sal.Fam.')
    ra_dt_demissao = models.CharField(max_length=255, blank=True, null=True, verbose_name='Dt. Demissao')
    ra_dtopfgts = models.CharField(max_length=255, blank=True, null=True, verbose_name='Dt.Op.FGTS')
    ra_altopçao = models.CharField(max_length=255, blank=True, null=True, verbose_name='Alt.Opçao')
    ra_bcoag_fgts = models.CharField(max_length=255, blank=True, null=True, verbose_name='Bco.Ag. FGTS')
    ra_cod_chapa = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cod. Chapa.')
    ra_ctadepfgts = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cta.Dep.FGTS')
    ra_turno_trab = models.CharField(max_length=255, blank=True, null=True, verbose_name='Turno Trab.')
    ra_local_benef = models.CharField(max_length=255, blank=True, null=True, verbose_name='Local Benef.')
    ra_depfgts = models.CharField(max_length=255, blank=True, null=True, verbose_name='% Dep.Fgts')
    ra_bcoagdsal = models.CharField(max_length=255, blank=True, null=True, verbose_name='Bco.Ag.D.Sal')
    ra_tipo_cta_sal = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tipo Cta Sal')
    ra_ctadepsal = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cta.Dep.Sal.')
    ra_tp_previden = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tp Previden.')
    ra_sit_folha = models.CharField(max_length=255, blank=True, null=True, verbose_name='Sit. Folha')
    ra_hrs_mensais = models.CharField(max_length=255, blank=True, null=True, verbose_name='Hrs. Mensais')
    ra_hrssemanais = models.CharField(max_length=255, blank=True, null=True, verbose_name='Hrs.Semanais')
    ra_horas_dia = models.CharField(max_length=255, blank=True, null=True, verbose_name='Horas Dia')
    ra_cod_funcao = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cod. Funcao')
    ra_possui_per = models.CharField(max_length=255, blank=True, null=True, verbose_name='Possui Per.?')
    ra_tpconttrab = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tp.Cont.Trab')
    ra_dt_term_cont = models.CharField(max_length=255, blank=True, null=True, verbose_name='Dt Term Cont')
    ra_cod_processo = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cod Processo')
    ra_cttparcial = models.CharField(max_length=255, blank=True, null=True, verbose_name='Ct.T.Parcial')
    ra_clau_assec = models.CharField(max_length=255, blank=True, null=True, verbose_name='Clau. Assec.')
    ra_adiantam = models.CharField(max_length=255, blank=True, null=True, verbose_name='% Adiantam.')
    ra_c_sindicato = models.CharField(max_length=255, blank=True, null=True, verbose_name='C. Sindicato')
    ra_alt_cbo = models.CharField(max_length=255, blank=True, null=True, verbose_name='Alt. CBO')
    ra_tipo_pgto = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tipo Pgto.')
    ra_cat_func = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cat. Func.')
    ra_vinemprais = models.CharField(max_length=255, blank=True, null=True, verbose_name='Vin.Emp.RAIS')
    ra_categ_sefip = models.CharField(max_length=255, blank=True, null=True, verbose_name='Categ. SEFIP')
    ra_cat_esocial = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cat. eSocial')
    ra_hrsperic = models.CharField(max_length=255, blank=True, null=True, verbose_name='Hrs.Peric.')
    ra_venexamed = models.CharField(max_length=255, blank=True, null=True, verbose_name='Ven.Exa.Med.')
    ra_possui_insal = models.CharField(max_length=255, blank=True, null=True, verbose_name='Possui Insal')
    ra_codafafgts = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cod.Afa.FGTS')
    ra_contr_assis = models.CharField(max_length=255, blank=True, null=True, verbose_name='Contr. Assis')
    ra_contr_confed = models.CharField(max_length=255, blank=True, null=True, verbose_name='Contr Confed')
    ra_mens_sindica = models.CharField(max_length=255, blank=True, null=True, verbose_name='Mens Sindica')
    ra_cdrescrais = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cd.Resc.RAIS')
    ra_multipinsal = models.CharField(max_length=255, blank=True, null=True, verbose_name='Multip.Insal')
    ra_cargo = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cargo')
    ra_cod_posto = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cod. Posto')
    ra_altnome = models.CharField(max_length=255, blank=True, null=True, verbose_name='Alt.Nome')
    ra_cod_depto = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cod. Depto.')
    ra_codretencao = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cod.Retencao')
    ra_desc_depto = models.CharField(max_length=255, blank=True, null=True, verbose_name='Desc. Depto')
    ra_nr_cracha = models.CharField(max_length=255, blank=True, null=True, verbose_name='Nr. Cracha')
    ra_regra_apont = models.CharField(max_length=255, blank=True, null=True, verbose_name='Regra Apont.')
    ra_dt_afast_mol = models.CharField(max_length=255, blank=True, null=True, verbose_name='Dt Afast Mol')
    ra_comp_sábado = models.CharField(max_length=255, blank=True, null=True, verbose_name='Comp. Sábado')
    ra_aposentado = models.CharField(max_length=255, blank=True, null=True, verbose_name='Aposentado')
    ra_procmenor_14 = models.CharField(max_length=255, blank=True, null=True, verbose_name='ProcMenor 14')
    ra_seqiniturn = models.CharField(max_length=255, blank=True, null=True, verbose_name='Seq.Ini.Turn')
    ra_tpreinesoc = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tp.Rein.eSoc')
    ra_id_procjud = models.CharField(max_length=255, blank=True, null=True, verbose_name='Id. Proc.Jud')
    ra_lei_anistia = models.CharField(max_length=255, blank=True, null=True, verbose_name='Lei Anistia')
    ra_data_efeito = models.CharField(max_length=255, blank=True, null=True, verbose_name='Data Efeito')
    ra_dt_efev_ret = models.CharField(max_length=255, blank=True, null=True, verbose_name='Dt Efev Ret')
    ra_cpf = models.CharField(max_length=255, blank=True, null=True, verbose_name='CPF')
    ra_pis = models.CharField(max_length=255, blank=True, null=True, verbose_name='P.I.S.')
    ra_altpis = models.CharField(max_length=255, blank=True, null=True, verbose_name='Alt.PIS')
    ra_rg = models.CharField(max_length=255, blank=True, null=True, verbose_name='R.G.')
    ra_d_temisrg = models.CharField(max_length=255, blank=True, null=True, verbose_name='D t.Emis.RG')
    ra_uf_do_rg = models.CharField(max_length=255, blank=True, null=True, verbose_name='UF do RG')
    ra_orgemissor = models.CharField(max_length=255, blank=True, null=True, verbose_name='Org.Emissor')
    ra_orgao_exp_rg = models.CharField(max_length=255, blank=True, null=True, verbose_name='Orgao exp RG')
    ra_org_emis_rg = models.CharField(max_length=255, blank=True, null=True, verbose_name='Org Emis RG')
    ra_complem_rg = models.CharField(max_length=255, blank=True, null=True, verbose_name='Complem. RG')
    ra_cartprofis = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cart.Profis.')
    ra_bh_p_folh = models.CharField(max_length=255, blank=True, null=True, verbose_name='B.H. p/ Folh')
    ra_série_cart = models.CharField(max_length=255, blank=True, null=True, verbose_name='Série Cart.')
    ra_uf_cartprof = models.CharField(max_length=255, blank=True, null=True, verbose_name='UF Cart.Prof')
    ra_acumbhoras = models.CharField(max_length=255, blank=True, null=True, verbose_name='Acum.B.Horas')
    ra_dtemisctps = models.CharField(max_length=255, blank=True, null=True, verbose_name='Dt.Emis.CTPS')
    ra_altcarprof = models.CharField(max_length=255, blank=True, null=True, verbose_name='Alt.Car.Prof')
    ra_carthabil = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cart.Habil.')
    ra_cnh_emissor = models.CharField(max_length=255, blank=True, null=True, verbose_name='CNH Emissor')
    ra_cnh_dtemis = models.CharField(max_length=255, blank=True, null=True, verbose_name='CNH DtEmis')
    ra_cnh_dt_val = models.CharField(max_length=255, blank=True, null=True, verbose_name='CNH Dt Val')
    ra_cnh_categ = models.CharField(max_length=255, blank=True, null=True, verbose_name='CNH Categ.')
    ra_cnh_uf = models.CharField(max_length=255, blank=True, null=True, verbose_name='CNH UF')
    ra_nrreservis = models.CharField(max_length=255, blank=True, null=True, verbose_name='Nr.Reservis.')
    ra_tipendereço = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tip.Endereço')
    ra_titeleit = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tit.Eleit.')
    ra_resexterior = models.CharField(max_length=255, blank=True, null=True, verbose_name='Res.Exterior')
    ra_zona_eleit = models.CharField(max_length=255, blank=True, null=True, verbose_name='Zona Eleit')
    ra_país_res_ext = models.CharField(max_length=255, blank=True, null=True, verbose_name='País Res Ext')
    ra_seção_eleit = models.CharField(max_length=255, blank=True, null=True, verbose_name='Seção Eleit.')
    ra_noregistro = models.CharField(max_length=255, blank=True, null=True, verbose_name='No.Registro')
    ra_tipo_lograd = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tipo Lograd')
    ra_cod_funcion = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cod. Funcion')
    ra_descrlograd = models.CharField(max_length=255, blank=True, null=True, verbose_name='Descr.Lograd')
    ra_cód_servent = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cód. Servent')
    ra_cód_acervo = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cód. Acervo')
    ra_nrlogradouro = models.CharField(max_length=255, blank=True, null=True, verbose_name='NrLogradouro')
    ra_endereço = models.CharField(max_length=255, blank=True, null=True, verbose_name='Endereço')
    ra_reg_civil = models.CharField(max_length=255, blank=True, null=True, verbose_name='Reg. Civil')
    ra_numendereço = models.CharField(max_length=255, blank=True, null=True, verbose_name='Num.Endereço')
    ra_tipo_livro = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tipo Livro')
    ra_class_estra = models.CharField(max_length=255, blank=True, null=True, verbose_name='Class. Estra')
    ra_complender = models.CharField(max_length=255, blank=True, null=True, verbose_name='Compl.Ender.')
    ra_tip_certid = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tip. Certid.')
    ra_bairro = models.CharField(max_length=255, blank=True, null=True, verbose_name='Bairro')
    ra_data_emissão = models.CharField(max_length=255, blank=True, null=True, verbose_name='Data Emissão')
    ra_estado = models.CharField(max_length=255, blank=True, null=True, verbose_name='Estado')
    ra_termomatric = models.CharField(max_length=255, blank=True, null=True, verbose_name='Termo/Matric')
    ra_livro = models.CharField(max_length=255, blank=True, null=True, verbose_name='Livro')
    ra_cod_municip = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cod Municip')
    ra_folha = models.CharField(max_length=255, blank=True, null=True, verbose_name='Folha')
    ra_municipio = models.CharField(max_length=255, blank=True, null=True, verbose_name='Municipio')
    ra_cartório = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cartório')
    ra_cep = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cep')
    ra_uf = models.CharField(max_length=255, blank=True, null=True, verbose_name='UF')
    ra_codmuncert = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cod.Mun.Cert')
    ra_caixa_postal = models.CharField(max_length=255, blank=True, null=True, verbose_name='Caixa Postal')
    ra_cep_cpostal = models.CharField(max_length=255, blank=True, null=True, verbose_name='CEP C.Postal')
    ra_alterou_end = models.CharField(max_length=255, blank=True, null=True, verbose_name='Alterou End.')
    ra_num_passap = models.CharField(max_length=255, blank=True, null=True, verbose_name='Num. Passap.')
    ra_emissor_pass = models.CharField(max_length=255, blank=True, null=True, verbose_name='Emissor Pass')
    ra_ddd_telefone = models.CharField(max_length=255, blank=True, null=True, verbose_name='DDD Telefone')
    ra_telefone = models.CharField(max_length=255, blank=True, null=True, verbose_name='Telefone')
    ra_uf_passaport = models.CharField(max_length=255, blank=True, null=True, verbose_name='UF Passaport')
    ra_ddd_celular = models.CharField(max_length=255, blank=True, null=True, verbose_name='DDD Celular')
    ra_dt_emis_pass = models.CharField(max_length=255, blank=True, null=True, verbose_name='Dt Emis Pass')
    ra_dt_val_pass = models.CharField(max_length=255, blank=True, null=True, verbose_name='Dt Val Pass')
    ra_num_celular = models.CharField(max_length=255, blank=True, null=True, verbose_name='Num. Celular')
    ra_cdpais_emis = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cd.Pais Emis')
    ra_numero_ric = models.CharField(max_length=255, blank=True, null=True, verbose_name='Numero RIC')
    ra_emissor_ric = models.CharField(max_length=255, blank=True, null=True, verbose_name='Emissor RIC')
    ra_uf_ric = models.CharField(max_length=255, blank=True, null=True, verbose_name='UF RIC')
    ra_codmun_ric = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cod.Mun. RIC')
    ra_num_insc_aut = models.CharField(max_length=255, blank=True, null=True, verbose_name='Num Insc Aut')
    ra_tp_serv_aut = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tp Serv Aut')
    ra_dtexped_ric = models.CharField(max_length=255, blank=True, null=True, verbose_name='Dt.Exped RIC')
    ra_cod_profiss = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cod Profiss')
    ra_orgclemissor = models.CharField(max_length=255, blank=True, null=True, verbose_name='OrgClEmissor')
    ra_orgcl_dtemis = models.CharField(max_length=255, blank=True, null=True, verbose_name='OrgCl DtEmis')
    ra_orgcl_dt_val = models.CharField(max_length=255, blank=True, null=True, verbose_name='OrgCl Dt Val')
    ra_códúnico = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cód.Único')
    ra_procfechado = models.CharField(max_length=255, blank=True, null=True, verbose_name='Proc.Fechado')
    ra_per_fechado = models.CharField(max_length=255, blank=True, null=True, verbose_name='Per. Fechado')
    ra_rot_fechado = models.CharField(max_length=255, blank=True, null=True, verbose_name='Rot. Fechado')
    ra_num_pag_fech = models.CharField(max_length=255, blank=True, null=True, verbose_name='Num Pag Fech')
    ra_número_rne = models.CharField(max_length=255, blank=True, null=True, verbose_name='Número RNE')
    ra_orgemisrne = models.CharField(max_length=255, blank=True, null=True, verbose_name='Org.Emis.RNE')
    ra_dtexprne = models.CharField(max_length=255, blank=True, null=True, verbose_name='Dt.Exp.RNE')
    ra_data_chegada = models.CharField(max_length=255, blank=True, null=True, verbose_name='Data Chegada')
    ra_ano_chegada = models.CharField(max_length=255, blank=True, null=True, verbose_name='Ano Chegada')
    ra_naturalizac = models.CharField(max_length=255, blank=True, null=True, verbose_name='Naturalizac.')
    ra_dnaturaliza = models.CharField(max_length=255, blank=True, null=True, verbose_name='D.Naturaliza')
    ra_casado_bras = models.CharField(max_length=255, blank=True, null=True, verbose_name='Casado Bras.')
    ra_filho_bras = models.CharField(max_length=255, blank=True, null=True, verbose_name='Filho Bras.')
    ra_calc_inss = models.CharField(max_length=255, blank=True, null=True, verbose_name='Calc. INSS')
    ra_hrs_insal = models.CharField(max_length=255, blank=True, null=True, verbose_name='Hrs. Insal.')
    ra_adcconf = models.CharField(max_length=255, blank=True, null=True, verbose_name='% Adc.Conf.')
    ra_adctrf = models.CharField(max_length=255, blank=True, null=True, verbose_name='%Adc.Trf.')
    ra_plsaúde = models.CharField(max_length=255, blank=True, null=True, verbose_name='Pl.Saúde')
    ra_adctmpserv = models.CharField(max_length=255, blank=True, null=True, verbose_name='Adc.Tmp.Serv')
    ra_tp_regjtra = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tp Reg.J.Tra')
    ra_data_caged = models.CharField(max_length=255, blank=True, null=True, verbose_name='Data Caged')
    ra_mat_migração = models.CharField(max_length=255, blank=True, null=True, verbose_name='Mat Migração')
    ra_mei = models.CharField(max_length=255, blank=True, null=True, verbose_name='MEI')
    ra_uf_loc = models.CharField(max_length=255, blank=True, null=True, verbose_name='Uf Loc.')
    ra_mun_loc = models.CharField(max_length=255, blank=True, null=True, verbose_name='Mun. Loc.')
    ra_desc_mun_l = models.CharField(max_length=255, blank=True, null=True, verbose_name='Desc. Mun. L')
    ra_mot_admissa = models.CharField(max_length=255, blank=True, null=True, verbose_name='Mot. Admissa')
    ra_substituto = models.CharField(max_length=255, blank=True, null=True, verbose_name='Substituto')
    ra_tipo_justif = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tipo Justif.')
    ra_citar = models.CharField(max_length=255, blank=True, null=True, verbose_name='CItar')
    ra_justificativ = models.CharField(max_length=255, blank=True, null=True, verbose_name='Justificativ')
    ra_nome_social = models.CharField(max_length=255, blank=True, null=True, verbose_name='Nome Social')
    ra_jorvariavel = models.CharField(max_length=255, blank=True, null=True, verbose_name='Jor.Variavel')
    ra_usr_adm = models.CharField(max_length=255, blank=True, null=True, verbose_name='Usr Adm')
    ra_cota_def = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cota Def')
    ra_desc_rem_var = models.CharField(max_length=255, blank=True, null=True, verbose_name='Desc Rem Var')
    ra_dt_prim_cnh = models.CharField(max_length=255, blank=True, null=True, verbose_name='Dt Prim CNH')
    ra_alojado = models.CharField(max_length=255, blank=True, null=True, verbose_name='Alojado')
    ra_tpcontdeterm = models.CharField(max_length=255, blank=True, null=True, verbose_name='TpContDeterm')
    ra_bloq_admis = models.CharField(max_length=255, blank=True, null=True, verbose_name='Bloq. Admis.')
    ra_descfuncao = models.CharField(max_length=255, blank=True, null=True, verbose_name='Desc.Funcao')
    ra_ctr_mat_tsv = models.CharField(max_length=255, blank=True, null=True, verbose_name='Ctr Mat TSV')
    ra_tempo_resid = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tempo Resid.')
    ra_dt_ini_benef = models.CharField(max_length=255, blank=True, null=True, verbose_name='Dt Ini Benef')
    ra_incapacitado = models.CharField(max_length=255, blank=True, null=True, verbose_name='Incapacitado')
    ra_dt_rec_incap = models.CharField(max_length=255, blank=True, null=True, verbose_name='Dt Rec Incap')
    ra_envrecpgto = models.CharField(max_length=255, blank=True, null=True, verbose_name='Env.Rec.Pgto')
    ra_e_gestor = models.CharField(max_length=255, blank=True, null=True, verbose_name='E Gestor?')
    ra_setor_resp = models.CharField(max_length=255, blank=True, null=True, verbose_name='Setor Resp')
    ra_painel_fluxo = models.CharField(max_length=255, blank=True, null=True, verbose_name='Painel Fluxo')


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
        
        # ✅ CORREÇÃO AQUI: Use 'ra_sit_folha' (o nome real do campo no modelo)
        if self.ra_sit_folha:
            # D = Demitido, T = Transferido, A = Afastado, F = Férias
            if self.ra_sit_folha in ['D', 'T', 'A']: # Adicione 'F' se Férias = Inativo
                self.ativo = False
            else:
                self.ativo = True
        
        # Chama o cálculo do salário bruto
        #self.salario_bruto_calculado = self._calcular_salario_bruto()

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