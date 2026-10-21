-- Projeto Apex Imoveis: estrutura inicial do banco apex_imoveis.
-- Pode ser executado mais de uma vez (IF NOT EXISTS), sem apagar dados.
--
-- Camadas:
--   staging   ---> espelho fiel do CSV tratado: TODAS as linhas, nada excluido.
--   analytics ---> dimensoes e (depois) views com o recorte e as regras de analise.

CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;

-- ---------------------------------------------------------------------------
-- staging.itbi_dti
-- GRAO: uma linha = uma DTI (guia de ITBI) paga, como vem no arquivo da
-- Prefeitura. Nao e "um imovel" nem "uma venda": o mesmo SQL pode repetir.
-- Chave: (aba_origem, linha_origem) identifica a linha no arquivo original.
-- Regra da camada: nao rejeita dado sujo. Quem valida e a camada analytics.
-- Fora de proposito: bairro (inutilizavel), referencia (texto livre) e
-- matricula (identificador sem uso analitico).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.itbi_dti (
    -- rastreabilidade
    aba_origem               TEXT     NOT NULL,   -- ex.: JAN-2025
    linha_origem             INTEGER  NOT NULL,   -- linha no Excel
    aba_sem_cabecalho        BOOLEAN,
    mes_pagamento            DATE     NOT NULL,   -- 1o dia do mes em que a guia foi paga

    -- imovel e localizacao
    sql                      BIGINT,              -- cadastro; perde zeros a esquerda
    logradouro               TEXT,
    numero                   INTEGER,             -- 99999 = sem numero
    complemento              TEXT,
    cep                      INTEGER,             -- perde zeros a esquerda
    situacao_sql             TEXT,
    uso_cod                  SMALLINT,
    uso_desc                 TEXT,
    padrao_cod               SMALLINT,            -- descricao em analytics.dim_padrao_iptu
    ano_conclusao            SMALLINT,
    area_terreno             NUMERIC,
    testada                  NUMERIC,
    fracao_ideal             DOUBLE PRECISION,
    area_construida          NUMERIC,

    -- transacao
    natureza_transacao       TEXT,
    natureza_cod             SMALLINT,
    data_transacao           DATE,
    valor_transacao          NUMERIC,             -- declarado pelo contribuinte
    proporcao_transmitida    NUMERIC,             -- % do imovel transmitido
    vvr                      NUMERIC,             -- valor venal de referencia
    vvr_proporcional         NUMERIC,
    base_calculo             NUMERIC,             -- maior entre declarado e vvr proporcional
    tipo_financiamento       TEXT,
    valor_financiado         NUMERIC,
    cartorio                 TEXT,

    -- marcacoes de qualidade (calculadas na ingestao, nada foi excluido)
    flag_linha_desalinhada     BOOLEAN,
    flag_compra_venda          BOOLEAN,
    flag_apto_condominio       BOOLEAN,
    flag_terreno_com_unidade   BOOLEAN,
    flag_proporcao_total       BOOLEAN,
    flag_area_invalida         BOOLEAN,
    flag_valor_baixo           BOOLEAN,
    flag_declarado_abaixo_vvr  BOOLEAN,
    razao_declarado_base       DOUBLE PRECISION,
    flag_sql_repetido_no_ano   BOOLEAN,
    flag_ativo_predial         BOOLEAN,

    PRIMARY KEY (aba_origem, linha_origem)
);

COMMENT ON TABLE  staging.itbi_dti IS 'Uma linha por DTI de ITBI paga (Prefeitura de SP). Dado tratado, sem exclusoes.';
COMMENT ON COLUMN staging.itbi_dti.mes_pagamento IS 'Mes de PAGAMENTO da guia (aba do arquivo), nao o mes da transacao.';
COMMENT ON COLUMN staging.itbi_dti.data_transacao IS 'Data do contrato ou escritura. Usar esta para analise temporal.';
COMMENT ON COLUMN staging.itbi_dti.valor_transacao IS 'Valor DECLARADO pelo contribuinte; pode diferir do preco efetivo.';
COMMENT ON COLUMN staging.itbi_dti.area_construida IS 'Inclui a parte das areas comuns do condominio; nao e area privativa.';
COMMENT ON COLUMN staging.itbi_dti.proporcao_transmitida IS 'Percentual do imovel transmitido; valores abaixo de 100 sao fracoes.';
COMMENT ON COLUMN staging.itbi_dti.base_calculo IS 'Maior entre o valor declarado e o valor venal de referencia proporcional.';
COMMENT ON COLUMN staging.itbi_dti.sql IS 'Numero do cadastro; setor fiscal = 3 primeiros digitos apos completar 11 digitos.';

CREATE INDEX IF NOT EXISTS idx_itbi_data_transacao ON staging.itbi_dti (data_transacao);
CREATE INDEX IF NOT EXISTS idx_itbi_uso_cod        ON staging.itbi_dti (uso_cod);

-- ---------------------------------------------------------------------------
-- staging.log_carga: registra cada carga (quando, qual arquivo, quantas linhas).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.log_carga (
    id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ano_arquivo       SMALLINT    NOT NULL,
    arquivo_tratado   TEXT        NOT NULL,
    linhas_carregadas INTEGER     NOT NULL,
    carregado_em      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- analytics.dim_padrao_iptu: dimensao (tabela oficial de padroes da Prefeitura).
-- Carregada de referencias/padroes_iptu.csv.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analytics.dim_padrao_iptu (
    padrao_cod  SMALLINT PRIMARY KEY,
    padrao_desc TEXT     NOT NULL
);