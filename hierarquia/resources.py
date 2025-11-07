# resources.py (VERSÃO FINAL COM "SUPER-LIMPADOR")

from import_export import resources, fields
from import_export.widgets import CharWidget, ForeignKeyWidget, ManyToManyWidget
from .models_funcionario import Funcionario # Importa do models_funcionario.py
from .models import Cargo, Setor # Importa Cargo/Setor do models.py
from django.contrib.auth.models import User

# --- ✅ WIDGET CUSTOMIZADO ATUALIZADO ---
class UppercaseForeignKeyWidget(ForeignKeyWidget):
    """
    Widget customizado que limpa o texto antes de procurar:
    1. Converte para MAIÚSCULAS.
    2. Remove espaços extras no início, no fim E NO MEIO.
    """
    def clean(self, value, row=None, **kwargs):
        if value:
            value = str(value).upper()
            # Limpa espaços extras (ex: "ANALISTA  DE CUSTOS" -> "ANALISTA DE CUSTOS")
            value = ' '.join(value.split()) 
        
        return super().clean(value, row, **kwargs)
# --- FIM DO NOVO WIDGET ---


class FuncionarioResource(resources.ModelResource):
    
    # --- 1. CAMPOS DE RELACIONAMENTO (CONFORME SOLICITADO) ---
    usuario = fields.Field(
        column_name='usuario_username',
        attribute='usuario',
        widget=ForeignKeyWidget(User, 'username')
    )
    
    # Usa o Widget "Super-Limpador"
    cargo = fields.Field(
        column_name='Desc.Funcao', 
        attribute='cargo',         
        widget=UppercaseForeignKeyWidget(Cargo, 'nome')
    )
    
    # Usa o Widget "Super-Limpador"
    setor_primario = fields.Field(
        column_name='Desc. Depto',
        attribute='setor_primario',
        widget=UppercaseForeignKeyWidget(Setor, 'nome')
    )

    setores_responsaveis = fields.Field(
        column_name='setores_responsaveis_nomes',
        attribute='setores_responsaveis',
        widget=ManyToManyWidget(Setor, field='nome', separator=',')
    )

    # --- 2. LÓGICA SKIP_ROW (PULAR DEMITIDOS) ---
    def skip_row(self, instance, original, row, import_validation_errors=None):
        situacao = row.get('Sit. Folha') 
        if situacao == 'D':
            return True 
        return False
    
    # --- 3. MAPEAMENTO DE COLUNAS (DO 'quero subir essa aq.csv') ---
    filial = fields.Field(
        column_name='Filial', 
        attribute='ra_filial', 
        widget=CharWidget(),
        readonly=False
    )
    matricula = fields.Field(
        column_name='Matricula', 
        attribute='ra_mat', 
        widget=CharWidget(),
        readonly=False
    )
    nome = fields.Field(
        column_name='Nome', 
        attribute='ra_nome', 
        widget=CharWidget(),
        readonly=False
    )
    nome_complet = fields.Field(
        column_name='Nome complet', 
        attribute='ra_nome_complet', 
        widget=CharWidget(),
        readonly=False
    )
    nome_mae = fields.Field(
        column_name='Nome Mae', 
        attribute='ra_nome_mae', 
        widget=CharWidget(),
        readonly=False
    )
    nome_pai = fields.Field(
        column_name='Nome Pai', 
        attribute='ra_nome_pai', 
        widget=CharWidget(),
        readonly=False
    )
    sexo = fields.Field(
        column_name='Sexo', 
        attribute='ra_sexo', 
        widget=CharWidget(),
        readonly=False
    )
    racacor = fields.Field(
        column_name='Raca/Cor', 
        attribute='ra_racacor', 
        widget=CharWidget(),
        readonly=False
    )
    data_nasc = fields.Field(
        column_name='Data Nasc.', 
        attribute='ra_data_nasc', 
        widget=CharWidget(),
        readonly=False
    )
    altdt_nasc = fields.Field(
        column_name='Alt.Dt. Nasc', 
        attribute='ra_altdt_nasc', 
        widget=CharWidget(),
        readonly=False
    )
    est_civil = fields.Field(
        column_name='Est. Civil', 
        attribute='ra_est_civil', 
        widget=CharWidget(),
        readonly=False
    )
    codpais_ori = fields.Field(
        column_name='Cod.Pais Ori', 
        attribute='ra_codpais_ori', 
        widget=CharWidget(),
        readonly=False
    )
    nacionalid = fields.Field(
        column_name='Nacionalid.', 
        attribute='ra_nacionalid', 
        widget=CharWidget(),
        readonly=False
    )
    c_nacion_rfb = fields.Field(
        column_name='C Nacion RFB', 
        attribute='ra_c_nacion_rfb', 
        widget=CharWidget(),
        readonly=False
    )
    branascext = fields.Field(
        column_name='Bra.Nasc.Ext', 
        attribute='ra_branascext', 
        widget=CharWidget(),
        readonly=False
    )
    naturalid_uf = fields.Field(
        column_name='Naturalid UF', 
        attribute='ra_naturalid_uf', 
        widget=CharWidget(),
        readonly=False
    )
    cod_mun_nasc = fields.Field(
        column_name='Cod Mun Nasc', 
        attribute='ra_cod_mun_nasc', 
        widget=CharWidget(),
        readonly=False
    )
    municpnasc = fields.Field(
        column_name='Municp.Nasc.', 
        attribute='ra_municpnasc', 
        widget=CharWidget(),
        readonly=False
    )
    apelido = fields.Field(
        column_name='Apelido', 
        attribute='ra_apelido', 
        widget=CharWidget(),
        readonly=False
    )
    cdinstrais = fields.Field(
        column_name='Cd.Inst.RAIS', 
        attribute='ra_cdinstrais', 
        widget=CharWidget(),
        readonly=False
    )
    email_princ = fields.Field(
        column_name='Email Princ', 
        attribute='ra_email_princ', 
        widget=CharWidget(),
        readonly=False
    )
    email_altern = fields.Field(
        column_name='Email Altern', 
        attribute='ra_email_altern', 
        widget=CharWidget(),
        readonly=False
    )
    receb_email = fields.Field(
        column_name='Receb E-Mail', 
        attribute='ra_receb_email', 
        widget=CharWidget(),
        readonly=False
    )
    tipo_email = fields.Field(
        column_name='Tipo E-Mail', 
        attribute='ra_tipo_email', 
        widget=CharWidget(),
        readonly=False
    )
    brpdh = fields.Field(
        column_name='BR/PDH', 
        attribute='ra_brpdh', 
        widget=CharWidget(),
        readonly=False
    )
    tpdeficien = fields.Field(
        column_name='Tp.Deficien', 
        attribute='ra_tpdeficien', 
        widget=CharWidget(),
        readonly=False
    )
    defi_esocial = fields.Field(
        column_name='Defi eSocial', 
        attribute='ra_defi_esocial', 
        widget=CharWidget(),
        readonly=False
    )
    centro_custo = fields.Field(
        column_name='Centro Custo', 
        attribute='ra_centro_custo', 
        widget=CharWidget(),
        readonly=False
    )
    classe_valor = fields.Field(
        column_name='Classe Valor', 
        attribute='ra_classe_valor', 
        widget=CharWidget(),
        readonly=False
    )
    item = fields.Field(
        column_name='Item', 
        attribute='ra_item', 
        widget=CharWidget(),
        readonly=False
    )
    data_admis = fields.Field(
        column_name='Data Admis.', 
        attribute='ra_data_admis', 
        widget=CharWidget(),
        readonly=False
    )
    altadmissao = fields.Field(
        column_name='Alt.Admissao', 
        attribute='ra_altadmissao', 
        widget=CharWidget(),
        readonly=False
    )
    tipo_admiss = fields.Field(
        column_name='Tipo Admiss.', 
        attribute='ra_tipo_admiss', 
        widget=CharWidget(),
        readonly=False
    )
    dep_ir = fields.Field(
        column_name='Dep. I.R.', 
        attribute='ra_dep_ir', 
        widget=CharWidget(),
        readonly=False
    )
    depsalfam = fields.Field(
        column_name='Dep.Sal.Fam.', 
        attribute='ra_depsalfam', 
        widget=CharWidget(),
        readonly=False
    )
    dt_demissao = fields.Field(
        column_name='Dt. Demissao', 
        attribute='ra_dt_demissao', 
        widget=CharWidget(),
        readonly=False
    )
    dtopfgts = fields.Field(
        column_name='Dt.Op.FGTS', 
        attribute='ra_dtopfgts', 
        widget=CharWidget(),
        readonly=False
    )
    altopçao = fields.Field(
        column_name='Alt.Opçao', 
        attribute='ra_altopçao', 
        widget=CharWidget(),
        readonly=False
    )
    bcoag_fgts = fields.Field(
        column_name='Bco.Ag. FGTS', 
        attribute='ra_bcoag_fgts', 
        widget=CharWidget(),
        readonly=False
    )
    cod_chapa = fields.Field(
        column_name='Cod. Chapa.', 
        attribute='ra_cod_chapa', 
        widget=CharWidget(),
        readonly=False
    )
    ctadepfgts = fields.Field(
        column_name='Cta.Dep.FGTS', 
        attribute='ra_ctadepfgts', 
        widget=CharWidget(),
        readonly=False
    )
    turno_trab = fields.Field(
        column_name='Turno Trab.', 
        attribute='ra_turno_trab', 
        widget=CharWidget(),
        readonly=False
    )
    local_benef = fields.Field(
        column_name='Local Benef.', 
        attribute='ra_local_benef', 
        widget=CharWidget(),
        readonly=False
    )
    _depfgts = fields.Field(
        column_name='% Dep.Fgts', 
        attribute='ra_depfgts', 
        widget=CharWidget(),
        readonly=False
    )
    bcoagdsal = fields.Field(
        column_name='Bco.Ag.D.Sal', 
        attribute='ra_bcoagdsal', 
        widget=CharWidget(),
        readonly=False
    )
    tipo_cta_sal = fields.Field(
        column_name='Tipo Cta Sal', 
        attribute='ra_tipo_cta_sal', 
        widget=CharWidget(),
        readonly=False
    )
    ctadepsal = fields.Field(
        column_name='Cta.Dep.Sal.', 
        attribute='ra_ctadepsal', 
        widget=CharWidget(),
        readonly=False
    )
    tp_previden = fields.Field(
        column_name='Tp Previden.', 
        attribute='ra_tp_previden', 
        widget=CharWidget(),
        readonly=False
    )
    sit_folha = fields.Field(
        column_name='Sit. Folha', 
        attribute='ra_sit_folha', 
        widget=CharWidget(),
        readonly=False
    )
    hrs_mensais = fields.Field(
        column_name='Hrs. Mensais', 
        attribute='ra_hrs_mensais', 
        widget=CharWidget(),
        readonly=False
    )
    hrssemanais = fields.Field(
        column_name='Hrs.Semanais', 
        attribute='ra_hrssemanais', 
        widget=CharWidget(),
        readonly=False
    )
    horas_dia = fields.Field(
        column_name='Horas Dia', 
        attribute='ra_horas_dia', 
        widget=CharWidget(),
        readonly=False
    )
    cod_funcao = fields.Field(
        column_name='Cod. Funcao', 
        attribute='ra_cod_funcao', 
        widget=CharWidget(),
        readonly=False
    )
    descfuncao = fields.Field(
        column_name='Desc.Funcao', 
        attribute='ra_descfuncao', 
        widget=CharWidget(),
        readonly=False
    )
    possui_per = fields.Field(
        column_name='Possui Per.?', 
        attribute='ra_possui_per', 
        widget=CharWidget(),
        readonly=False
    )
    tpconttrab = fields.Field(
        column_name='Tp.Cont.Trab', 
        attribute='ra_tpconttrab', 
        widget=CharWidget(),
        readonly=False
    )
    dt_term_cont = fields.Field(
        column_name='Dt Term Cont', 
        attribute='ra_dt_term_cont', 
        widget=CharWidget(),
        readonly=False
    )
    cod_processo = fields.Field(
        column_name='Cod Processo', 
        attribute='ra_cod_processo', 
        widget=CharWidget(),
        readonly=False
    )
    cttparcial = fields.Field(
        column_name='Ct.T.Parcial', 
        attribute='ra_cttparcial', 
        widget=CharWidget(),
        readonly=False
    )
    clau_assec = fields.Field(
        column_name='Clau. Assec.', 
        attribute='ra_clau_assec', 
        widget=CharWidget(),
        readonly=False
    )
    _adiantam = fields.Field(
        column_name='% Adiantam.', 
        attribute='ra_adiantam', 
        widget=CharWidget(),
        readonly=False
    )
    c_sindicato = fields.Field(
        column_name='C. Sindicato', 
        attribute='ra_c_sindicato', 
        widget=CharWidget(),
        readonly=False
    )
    alt_cbo = fields.Field(
        column_name='Alt. CBO', 
        attribute='ra_alt_cbo', 
        widget=CharWidget(),
        readonly=False
    )
    tipo_pgto = fields.Field(
        column_name='Tipo Pgto.', 
        attribute='ra_tipo_pgto', 
        widget=CharWidget(),
        readonly=False
    )
    cat_func = fields.Field(
        column_name='Cat. Func.', 
        attribute='ra_cat_func', 
        widget=CharWidget(),
        readonly=False
    )
    vinemprais = fields.Field(
        column_name='Vin.Emp.RAIS', 
        attribute='ra_vinemprais', 
        widget=CharWidget(),
        readonly=False
    )
    categ_sefip = fields.Field(
        column_name='Categ. SEFIP', 
        attribute='ra_categ_sefip', 
        widget=CharWidget(),
        readonly=False
    )
    cat_esocial = fields.Field(
        column_name='Cat. eSocial', 
        attribute='ra_cat_esocial', 
        widget=CharWidget(),
        readonly=False
    )
    hrsperic = fields.Field(
        column_name='Hrs.Peric.', 
        attribute='ra_hrsperic', 
        widget=CharWidget(),
        readonly=False
    )
    venexamed = fields.Field(
        column_name='Ven.Exa.Med.', 
        attribute='ra_venexamed', 
        widget=CharWidget(),
        readonly=False
    )
    possui_insal = fields.Field(
        column_name='Possui Insal', 
        attribute='ra_possui_insal', 
        widget=CharWidget(),
        readonly=False
    )
    codafafgts = fields.Field(
        column_name='Cod.Afa.FGTS', 
        attribute='ra_codafafgts', 
        widget=CharWidget(),
        readonly=False
    )
    contr_assis = fields.Field(
        column_name='Contr. Assis', 
        attribute='ra_contr_assis', 
        widget=CharWidget(),
        readonly=False
    )
    contr_confed = fields.Field(
        column_name='Contr Confed', 
        attribute='ra_contr_confed', 
        widget=CharWidget(),
        readonly=False
    )
    mens_sindica = fields.Field(
        column_name='Mens Sindica', 
        attribute='ra_mens_sindica', 
        widget=CharWidget(),
        readonly=False
    )
    cdrescrais = fields.Field(
        column_name='Cd.Resc.RAIS', 
        attribute='ra_cdrescrais', 
        widget=CharWidget(),
        readonly=False
    )
    multipinsal = fields.Field(
        column_name='Multip.Insal', 
        attribute='ra_multipinsal', 
        widget=CharWidget(),
        readonly=False
    )
    cargo_modelo = fields.Field( # Renomeado para não conflitar
        column_name='Cargo', 
        attribute='ra_cargo', 
        widget=CharWidget(),
        readonly=False
    )
    cod_posto = fields.Field(
        column_name='Cod. Posto', 
        attribute='ra_cod_posto', 
        widget=CharWidget(),
        readonly=False
    )
    altnome = fields.Field(
        column_name='Alt.Nome', 
        attribute='ra_altnome', 
        widget=CharWidget(),
        readonly=False
    )
    cod_depto = fields.Field(
        column_name='Cod. Depto.', 
        attribute='ra_cod_depto', 
        widget=CharWidget(),
        readonly=False
    )
    codretencao = fields.Field(
        column_name='Cod.Retencao', 
        attribute='ra_codretencao', 
        widget=CharWidget(),
        readonly=False
    )
    desc_depto = fields.Field(
        column_name='Desc. Depto', 
        attribute='ra_desc_depto', 
        widget=CharWidget(),
        readonly=False
    )
    nr_cracha = fields.Field(
        column_name='Nr. Cracha', 
        attribute='ra_nr_cracha', 
        widget=CharWidget(),
        readonly=False
    )
    regra_apont = fields.Field(
        column_name='Regra Apont.', 
        attribute='ra_regra_apont', 
        widget=CharWidget(),
        readonly=False
    )
    dt_afast_mol = fields.Field(
        column_name='Dt Afast Mol', 
        attribute='ra_dt_afast_mol', 
        widget=CharWidget(),
        readonly=False
    )
    comp_sábado = fields.Field(
        column_name='Comp. Sábado', 
        attribute='ra_comp_sábado', 
        widget=CharWidget(),
        readonly=False
    )
    aposentado = fields.Field(
        column_name='Aposentado', 
        attribute='ra_aposentado', 
        widget=CharWidget(),
        readonly=False
    )
    procmenor_14 = fields.Field(
        column_name='ProcMenor 14', 
        attribute='ra_procmenor_14', 
        widget=CharWidget(),
        readonly=False
    )
    seqiniturn = fields.Field(
        column_name='Seq.Ini.Turn', 
        attribute='ra_seqiniturn', 
        widget=CharWidget(),
        readonly=False
    )
    tpreinesoc = fields.Field(
        column_name='Tp.Rein.eSoc', 
        attribute='ra_tpreinesoc', 
        widget=CharWidget(),
        readonly=False
    )
    id_procjud = fields.Field(
        column_name='Id. Proc.Jud', 
        attribute='ra_id_procjud', 
        widget=CharWidget(),
        readonly=False
    )
    lei_anistia = fields.Field(
        column_name='Lei Anistia', 
        attribute='ra_lei_anistia', 
        widget=CharWidget(),
        readonly=False
    )
    data_efeito = fields.Field(
        column_name='Data Efeito', 
        attribute='ra_data_efeito', 
        widget=CharWidget(),
        readonly=False
    )
    dt_efev_ret = fields.Field(
        column_name='Dt Efev Ret', 
        attribute='ra_dt_efev_ret', 
        widget=CharWidget(),
        readonly=False
    )
    cpf = fields.Field(
        column_name='CPF', 
        attribute='ra_cpf', 
        widget=CharWidget(),
        readonly=False
    )
    pis = fields.Field(
        column_name='P.I.S.', 
        attribute='ra_pis', 
        widget=CharWidget(),
        readonly=False
    )
    altpis = fields.Field(
        column_name='Alt.PIS', 
        attribute='ra_altpis', 
        widget=CharWidget(),
        readonly=False
    )
    rg = fields.Field(
        column_name='R.G.', 
        attribute='ra_rg', 
        widget=CharWidget(),
        readonly=False
    )
    d_temisrg = fields.Field(
        column_name='D t.Emis.RG', 
        attribute='ra_d_temisrg', 
        widget=CharWidget(),
        readonly=False
    )
    uf_do_rg = fields.Field(
        column_name='UF do RG', 
        attribute='ra_uf_do_rg', 
        widget=CharWidget(),
        readonly=False
    )
    orgemissor = fields.Field(
        column_name='Org.Emissor', 
        attribute='ra_orgemissor', 
        widget=CharWidget(),
        readonly=False
    )
    orgao_exp_rg = fields.Field(
        column_name='Orgao exp RG', 
        attribute='ra_orgao_exp_rg', 
        widget=CharWidget(),
        readonly=False
    )
    org_emis_rg = fields.Field(
        column_name='Org Emis RG', 
        attribute='ra_org_emis_rg', 
        widget=CharWidget(),
        readonly=False
    )
    complem_rg = fields.Field(
        column_name='Complem. RG', 
        attribute='ra_complem_rg', 
        widget=CharWidget(),
        readonly=False
    )
    cartprofis = fields.Field(
        column_name='Cart.Profis.', 
        attribute='ra_cartprofis', 
        widget=CharWidget(),
        readonly=False
    )
    bh_p_folh = fields.Field(
        column_name='B.H. p/ Folh', 
        attribute='ra_bh_p_folh', 
        widget=CharWidget(),
        readonly=False
    )
    série_cart = fields.Field(
        column_name='Série Cart.', 
        attribute='ra_série_cart', 
        widget=CharWidget(),
        readonly=False
    )
    uf_cartprof = fields.Field(
        column_name='UF Cart.Prof', 
        attribute='ra_uf_cartprof', 
        widget=CharWidget(),
        readonly=False
    )
    acumbhoras = fields.Field(
        column_name='Acum.B.Horas', 
        attribute='ra_acumbhoras', 
        widget=CharWidget(),
        readonly=False
    )
    dtemisctps = fields.Field(
        column_name='Dt.Emis.CTPS', 
        attribute='ra_dtemisctps', 
        widget=CharWidget(),
        readonly=False
    )
    altcarprof = fields.Field(
        column_name='Alt.Car.Prof', 
        attribute='ra_altcarprof', 
        widget=CharWidget(),
        readonly=False
    )
    carthabil = fields.Field(
        column_name='Cart.Habil.', 
        attribute='ra_carthabil', 
        widget=CharWidget(),
        readonly=False
    )
    cnh_emissor = fields.Field(
        column_name='CNH Emissor', 
        attribute='ra_cnh_emissor', 
        widget=CharWidget(),
        readonly=False
    )
    cnh_dtemis = fields.Field(
        column_name='CNH DtEmis', 
        attribute='ra_cnh_dtemis', 
        widget=CharWidget(),
        readonly=False
    )
    cnh_dt_val = fields.Field(
        column_name='CNH Dt Val', 
        attribute='ra_cnh_dt_val', 
        widget=CharWidget(),
        readonly=False
    )
    cnh_categ = fields.Field(
        column_name='CNH Categ.', 
        attribute='ra_cnh_categ', 
        widget=CharWidget(),
        readonly=False
    )
    cnh_uf = fields.Field(
        column_name='CNH UF', 
        attribute='ra_cnh_uf', 
        widget=CharWidget(),
        readonly=False
    )
    nrreservis = fields.Field(
        column_name='Nr.Reservis.', 
        attribute='ra_nrreservis', 
        widget=CharWidget(),
        readonly=False
    )
    tipendereço = fields.Field(
        column_name='Tip.Endereço', 
        attribute='ra_tipendereço', 
        widget=CharWidget(),
        readonly=False
    )
    titeleit = fields.Field(
        column_name='Tit.Eleit.', 
        attribute='ra_titeleit', 
        widget=CharWidget(),
        readonly=False
    )
    resexterior = fields.Field(
        column_name='Res.Exterior', 
        attribute='ra_resexterior', 
        widget=CharWidget(),
        readonly=False
    )
    zona_eleit = fields.Field(
        column_name='Zona Eleit', 
        attribute='ra_zona_eleit', 
        widget=CharWidget(),
        readonly=False
    )
    país_res_ext = fields.Field(
        column_name='País Res Ext', 
        attribute='ra_país_res_ext', 
        widget=CharWidget(),
        readonly=False
    )
    seção_eleit = fields.Field(
        column_name='Seção Eleit.', 
        attribute='ra_seção_eleit', 
        widget=CharWidget(),
        readonly=False
    )
    noregistro = fields.Field(
        column_name='No.Registro', 
        attribute='ra_noregistro', 
        widget=CharWidget(),
        readonly=False
    )
    tipo_lograd = fields.Field(
        column_name='Tipo Lograd', 
        attribute='ra_tipo_lograd', 
        widget=CharWidget(),
        readonly=False
    )
    cod_funcion = fields.Field(
        column_name='Cod. Funcion', 
        attribute='ra_cod_funcion', 
        widget=CharWidget(),
        readonly=False
    )
    descrlograd = fields.Field(
        column_name='Descr.Lograd', 
        attribute='ra_descrlograd', 
        widget=CharWidget(),
        readonly=False
    )
    cód_servent = fields.Field(
        column_name='Cód. Servent', 
        attribute='ra_cód_servent', 
        widget=CharWidget(),
        readonly=False
    )
    cód_acervo = fields.Field(
        column_name='Cód. Acervo', 
        attribute='ra_cód_acervo', 
        widget=CharWidget(),
        readonly=False
    )
    nrlogradouro = fields.Field(
        column_name='NrLogradouro', 
        attribute='ra_nrlogradouro', 
        widget=CharWidget(),
        readonly=False
    )
    endereço = fields.Field(
        column_name='Endereço', 
        attribute='ra_endereço', 
        widget=CharWidget(),
        readonly=False
    )
    reg_civil = fields.Field(
        column_name='Reg. Civil', 
        attribute='ra_reg_civil', 
        widget=CharWidget(),
        readonly=False
    )
    numendereço = fields.Field(
        column_name='Num.Endereço', 
        attribute='ra_numendereço', 
        widget=CharWidget(),
        readonly=False
    )
    tipo_livro = fields.Field(
        column_name='Tipo Livro', 
        attribute='ra_tipo_livro', 
        widget=CharWidget(),
        readonly=False
    )
    class_estra = fields.Field(
        column_name='Class. Estra', 
        attribute='ra_class_estra', 
        widget=CharWidget(),
        readonly=False
    )
    complender = fields.Field(
        column_name='Compl.Ender.', 
        attribute='ra_complender', 
        widget=CharWidget(),
        readonly=False
    )
    tip_certid = fields.Field(
        column_name='Tip. Certid.', 
        attribute='ra_tip_certid', 
        widget=CharWidget(),
        readonly=False
    )
    bairro = fields.Field(
        column_name='Bairro', 
        attribute='ra_bairro', 
        widget=CharWidget(),
        readonly=False
    )
    data_emissão = fields.Field(
        column_name='Data Emissão', 
        attribute='ra_data_emissão', 
        widget=CharWidget(),
        readonly=False
    )
    estado = fields.Field(
        column_name='Estado', 
        attribute='ra_estado', 
        widget=CharWidget(),
        readonly=False
    )
    termomatric = fields.Field(
        column_name='Termo/Matric', 
        attribute='ra_termomatric', 
        widget=CharWidget(),
        readonly=False
    )
    livro = fields.Field(
        column_name='Livro', 
        attribute='ra_livro', 
        widget=CharWidget(),
        readonly=False
    )
    cod_municip = fields.Field(
        column_name='Cod Municip', 
        attribute='ra_cod_municip', 
        widget=CharWidget(),
        readonly=False
    )
    folha = fields.Field(
        column_name='Folha', 
        attribute='ra_folha', 
        widget=CharWidget(),
        readonly=False
    )
    municipio = fields.Field(
        column_name='Municipio', 
        attribute='ra_municipio', 
        widget=CharWidget(),
        readonly=False
    )
    cartório = fields.Field(
        column_name='Cartório', 
        attribute='ra_cartório', 
        widget=CharWidget(),
        readonly=False
    )
    cep = fields.Field(
        column_name='Cep', 
        attribute='ra_cep', 
        widget=CharWidget(),
        readonly=False
    )
    uf = fields.Field(
        column_name='UF', 
        attribute='ra_uf', 
        widget=CharWidget(),
        readonly=False
    )
    codmuncert = fields.Field(
        column_name='Cod.Mun.Cert', 
        attribute='ra_codmuncert', 
        widget=CharWidget(),
        readonly=False
    )
    caixa_postal = fields.Field(
        column_name='Caixa Postal', 
        attribute='ra_caixa_postal', 
        widget=CharWidget(),
        readonly=False
    )
    cep_cpostal = fields.Field(
        column_name='CEP C.Postal', 
        attribute='ra_cep_cpostal', 
        widget=CharWidget(),
        readonly=False
    )
    alterou_end = fields.Field(
        column_name='Alterou End.', 
        attribute='ra_alterou_end', 
        widget=CharWidget(),
        readonly=False
    )
    num_passap = fields.Field(
        column_name='Num. Passap.', 
        attribute='ra_num_passap', 
        widget=CharWidget(),
        readonly=False
    )
    emissor_pass = fields.Field(
        column_name='Emissor Pass', 
        attribute='ra_emissor_pass', 
        widget=CharWidget(),
        readonly=False
    )
    ddd_telefone = fields.Field(
        column_name='DDD Telefone', 
        attribute='ra_ddd_telefone', 
        widget=CharWidget(),
        readonly=False
    )
    telefone = fields.Field(
        column_name='Telefone', 
        attribute='ra_telefone', 
        widget=CharWidget(),
        readonly=False
    )
    uf_passaport = fields.Field(
        column_name='UF Passaport', 
        attribute='ra_uf_passaport', 
        widget=CharWidget(),
        readonly=False
    )
    ddd_celular = fields.Field(
        column_name='DDD Celular', 
        attribute='ra_ddd_celular', 
        widget=CharWidget(),
        readonly=False
    )
    dt_emis_pass = fields.Field(
        column_name='Dt Emis Pass', 
        attribute='ra_dt_emis_pass', 
        widget=CharWidget(),
        readonly=False
    )
    dt_val_pass = fields.Field(
        column_name='Dt Val Pass', 
        attribute='ra_dt_val_pass', 
        widget=CharWidget(),
        readonly=False
    )
    num_celular = fields.Field(
        column_name='Num. Celular', 
        attribute='ra_num_celular', 
        widget=CharWidget(),
        readonly=False
    )
    cdpais_emis = fields.Field(
        column_name='Cd.Pais Emis', 
        attribute='ra_cdpais_emis', 
        widget=CharWidget(),
        readonly=False
    )
    numero_ric = fields.Field(
        column_name='Numero RIC', 
        attribute='ra_numero_ric', 
        widget=CharWidget(),
        readonly=False
    )
    emissor_ric = fields.Field(
        column_name='Emissor RIC', 
        attribute='ra_emissor_ric', 
        widget=CharWidget(),
        readonly=False
    )
    uf_ric = fields.Field(
        column_name='UF RIC', 
        attribute='ra_uf_ric', 
        widget=CharWidget(),
        readonly=False
    )
    codmun_ric = fields.Field(
        column_name='Cod.Mun. RIC', 
        attribute='ra_codmun_ric', 
        widget=CharWidget(),
        readonly=False
    )
    num_insc_aut = fields.Field(
        column_name='Num Insc Aut', 
        attribute='ra_num_insc_aut', 
        widget=CharWidget(),
        readonly=False
    )
    tp_serv_aut = fields.Field(
        column_name='Tp Serv Aut', 
        attribute='ra_tp_serv_aut', 
        widget=CharWidget(),
        readonly=False
    )
    dtexped_ric = fields.Field(
        column_name='Dt.Exped RIC', 
        attribute='ra_dtexped_ric', 
        widget=CharWidget(),
        readonly=False
    )
    cod_profiss = fields.Field(
        column_name='Cod Profiss', 
        attribute='ra_cod_profiss', 
        widget=CharWidget(),
        readonly=False
    )
    orgclemissor = fields.Field(
        column_name='OrgClEmissor', 
        attribute='ra_orgclemissor', 
        widget=CharWidget(),
        readonly=False
    )
    orgcl_dtemis = fields.Field(
        column_name='OrgCl DtEmis', 
        attribute='ra_orgcl_dtemis', 
        widget=CharWidget(),
        readonly=False
    )
    orgcl_dt_val = fields.Field(
        column_name='OrgCl Dt Val', 
        attribute='ra_orgcl_dt_val', 
        widget=CharWidget(),
        readonly=False
    )
    códúnico = fields.Field(
        column_name='Cód.Único', 
        attribute='ra_códúnico', 
        widget=CharWidget(),
        readonly=False
    )
    procfechado = fields.Field(
        column_name='Proc.Fechado', 
        attribute='ra_procfechado', 
        widget=CharWidget(),
        readonly=False
    )
    per_fechado = fields.Field(
        column_name='Per. Fechado', 
        attribute='ra_per_fechado', 
        widget=CharWidget(),
        readonly=False
    )
    rot_fechado = fields.Field(
        column_name='Rot. Fechado', 
        attribute='ra_rot_fechado', 
        widget=CharWidget(),
        readonly=False
    )
    num_pag_fech = fields.Field(
        column_name='Num Pag Fech', 
        attribute='ra_num_pag_fech', 
        widget=CharWidget(),
        readonly=False
    )
    número_rne = fields.Field(
        column_name='Número RNE', 
        attribute='ra_número_rne', 
        widget=CharWidget(),
        readonly=False
    )
    orgemisrne = fields.Field(
        column_name='Org.Emis.RNE', 
        attribute='ra_orgemisrne', 
        widget=CharWidget(),
        readonly=False
    )
    dtexprne = fields.Field(
        column_name='Dt.Exp.RNE', 
        attribute='ra_dtexprne', 
        widget=CharWidget(),
        readonly=False
    )
    data_chegada = fields.Field(
        column_name='Data Chegada', 
        attribute='ra_data_chegada', 
        widget=CharWidget(),
        readonly=False
    )
    ano_chegada = fields.Field(
        column_name='Ano Chegada', 
        attribute='ra_ano_chegada', 
        widget=CharWidget(),
        readonly=False
    )
    naturalizac = fields.Field(
        column_name='Naturalizac.', 
        attribute='ra_naturalizac', 
        widget=CharWidget(),
        readonly=False
    )
    dnaturaliza = fields.Field(
        column_name='D.Naturaliza', 
        attribute='ra_dnaturaliza', 
        widget=CharWidget(),
        readonly=False
    )
    casado_bras = fields.Field(
        column_name='Casado Bras.', 
        attribute='ra_casado_bras', 
        widget=CharWidget(),
        readonly=False
    )
    filho_bras = fields.Field(
        column_name='Filho Bras.', 
        attribute='ra_filho_bras', 
        widget=CharWidget(),
        readonly=False
    )
    calc_inss = fields.Field(
        column_name='Calc. INSS', 
        attribute='ra_calc_inss', 
        widget=CharWidget(),
        readonly=False
    )
    hrs_insal = fields.Field(
        column_name='Hrs. Insal.', 
        attribute='ra_hrs_insal', 
        widget=CharWidget(),
        readonly=False
    )
    _adcconf = fields.Field(
        column_name='% Adc.Conf.', 
        attribute='ra_adcconf', 
        widget=CharWidget(),
        readonly=False
    )
    adctrf = fields.Field(
        column_name='%Adc.Trf.', 
        attribute='ra_adctrf', 
        widget=CharWidget(),
        readonly=False
    )
    plsaúde = fields.Field(
        column_name='Pl.Saúde', 
        attribute='ra_plsaúde', 
        widget=CharWidget(),
        readonly=False
    )
    adctmpserv = fields.Field(
        column_name='Adc.Tmp.Serv', 
        attribute='ra_adctmpserv', 
        widget=CharWidget(),
        readonly=False
    )
    tp_regjtra = fields.Field(
        column_name='Tp Reg.J.Tra', 
        attribute='ra_tp_regjtra', 
        widget=CharWidget(),
        readonly=False
    )
    data_caged = fields.Field(
        column_name='Data Caged', 
        attribute='ra_data_caged', 
        widget=CharWidget(),
        readonly=False
    )
    mat_migração = fields.Field(
        column_name='Mat Migração', 
        attribute='ra_mat_migração', 
        widget=CharWidget(),
        readonly=False
    )
    mei = fields.Field(
        column_name='MEI', 
        attribute='ra_mei', 
        widget=CharWidget(),
        readonly=False
    )
    uf_loc = fields.Field(
        column_name='Uf Loc.', 
        attribute='ra_uf_loc', 
        widget=CharWidget(),
        readonly=False
    )
    mun_loc = fields.Field(
        column_name='Mun. Loc.', 
        attribute='ra_mun_loc', 
        widget=CharWidget(),
        readonly=False
    )
    desc_mun_l = fields.Field(
        column_name='Desc. Mun. L', 
        attribute='ra_desc_mun_l', 
        widget=CharWidget(),
        readonly=False
    )
    mot_admissa = fields.Field(
        column_name='Mot. Admissa', 
        attribute='ra_mot_admissa', 
        widget=CharWidget(),
        readonly=False
    )
    substituto = fields.Field(
        column_name='Substituto', 
        attribute='ra_substituto', 
        widget=CharWidget(),
        readonly=False
    )
    tipo_justif = fields.Field(
        column_name='Tipo Justif.', 
        attribute='ra_tipo_justif', 
        widget=CharWidget(),
        readonly=False
    )
    citar = fields.Field(
        column_name='CItar', 
        attribute='ra_citar', 
        widget=CharWidget(),
        readonly=False
    )
    justificativ = fields.Field(
        column_name='Justificativ', 
        attribute='ra_justificativ', 
        widget=CharWidget(),
        readonly=False
    )
    nome_social = fields.Field(
        column_name='Nome Social', 
        attribute='ra_nome_social', 
        widget=CharWidget(),
        readonly=False
    )
    jorvariavel = fields.Field(
        column_name='Jor.Variavel', 
        attribute='ra_jorvariavel', 
        widget=CharWidget(),
        readonly=False
    )
    usr_adm = fields.Field(
        column_name='Usr Adm', 
        attribute='ra_usr_adm', 
        widget=CharWidget(),
        readonly=False
    )
    cota_def = fields.Field(
        column_name='Cota Def', 
        attribute='ra_cota_def', 
        widget=CharWidget(),
        readonly=False
    )
    desc_rem_var = fields.Field(
        column_name='Desc Rem Var', 
        attribute='ra_desc_rem_var', 
        widget=CharWidget(),
        readonly=False
    )
    dt_prim_cnh = fields.Field(
        column_name='Dt Prim CNH', 
        attribute='ra_dt_prim_cnh', 
        widget=CharWidget(),
        readonly=False
    )
    alojado = fields.Field(
        column_name='Alojado', 
        attribute='ra_alojado', 
        widget=CharWidget(),
        readonly=False
    )
    tpcontdeterm = fields.Field(
        column_name='TpContDeterm', 
        attribute='ra_tpcontdeterm', 
        widget=CharWidget(),
        readonly=False
    )
    bloq_admis = fields.Field(
        column_name='Bloq. Admis.', 
        attribute='ra_bloq_admis', 
        widget=CharWidget(),
        readonly=False
    )
    descfuncao2 = fields.Field( # Renomeado para não conflitar
        column_name='Desc.Funcao', 
        attribute='ra_descfuncao', 
        widget=CharWidget(),
        readonly=False
    )
    ctr_mat_tsv = fields.Field(
        column_name='Ctr Mat TSV', 
        attribute='ra_ctr_mat_tsv', 
        widget=CharWidget(),
        readonly=False
    )
    tempo_resid = fields.Field(
        column_name='Tempo Resid.', 
        attribute='ra_tempo_resid', 
        widget=CharWidget(),
        readonly=False
    )
    dt_ini_benef = fields.Field(
        column_name='Dt Ini Benef', 
        attribute='ra_dt_ini_benef', 
        widget=CharWidget(),
        readonly=False
    )
    incapacitado = fields.Field(
        column_name='Incapacitado', 
        attribute='ra_incapacitado', 
        widget=CharWidget(),
        readonly=False
    )
    dt_rec_incap = fields.Field(
        column_name='Dt Rec Incap', 
        attribute='ra_dt_rec_incap', 
        widget=CharWidget(),
        readonly=False
    )
    envrecpgto = fields.Field(
        column_name='Env.Rec.Pgto', 
        attribute='ra_envrecpgto', 
        widget=CharWidget(),
        readonly=False
    )
    e_gestor = fields.Field(
        column_name='E Gestor?', 
        attribute='ra_e_gestor', 
        widget=CharWidget(),
        readonly=False
    )
    setor_resp = fields.Field(
        column_name='Setor Resp', 
        attribute='ra_setor_resp', 
        widget=CharWidget(),
        readonly=False
    )
    painel_fluxo = fields.Field(
        column_name='Painel Fluxo', 
        attribute='ra_painel_fluxo', 
        widget=CharWidget(),
        readonly=False
    )

    class Meta:
        model = Funcionario
        use_model_save = True
        
        # ✅ CORRIGIDO: Usa 'matricula' (o nome do campo)
        import_id_fields = ['matricula'] 
        
        skip_unchanged = True
        report_skipped = True
        
        # Exclui campos que não vêm do CSV ou que já mapeamos
        exclude = ('id', 'usuario', 'cargo', 'setor_primario', 'setores_responsaveis', 
                   'ativo', 'salario_bruto_calculado', 'criado_em', 'atualizado_em')
        
        # ✅ CORRIGIDO: Esta é a codificação "ANSI" (Windows Brasil) do seu arquivo
        import_encoding = 'windows-1252'