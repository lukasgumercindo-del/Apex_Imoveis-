-- Recorte final da analise: apartamentos validos, com setor fiscal, preco por
-- metro quadrado nominal e real (corrigido pelo IPCA) e a marcacao da janela.
-- Rodar com:  python src\executar_sql.py sql\04_view_recorte.sql
-- Depende de: 02_views_funil.sql (classificacao) e 03_dim_ipca.sql + carga do IPCA.
--
-- Parametros (so aqui; para mudar, edite o bloco "parametros" e rode de novo):
--   mes_base       -> mes cujo valor em reais serve de referencia da correcao
--   janela_inicio / janela_fim -> meses (pela DATA DA TRANSACAO) considerados
--                     completos. Motivo: cada arquivo agrupa por mes de PAGAMENTO,
--                     e cerca de 88 por cento das guias sao pagas no mes da
--                     transacao e 99 por cento ate o mes seguinte. Dez/2021 fica
--                     fora (arquivo de 2021 nao carregado) e dez/2025 tambem
--                     (guias pagas em jan/2026 nao estao nos arquivos carregados).
--
-- Privacidade: a coluna sql identifica o imovel. Serve para a EDA local; nao deve
-- aparecer em nada publicado (use apenas agregacoes por setor e periodo).
-- Linhas sem deflator ficam na view com sem_deflator = true (nunca somem).

CREATE OR REPLACE VIEW analytics.vw_apto_recorte AS 
WITH parametros AS (
	SELECT DATE '2025-12-01' AS mes_base,
		   DATE '2022-01-01' AS janela_inicio,
		   DATE '2025-11-01' AS janela_fim
)
SELECT
	s.aba_origem,
	s.linha_origem,
	s.data_transacao,
	CAST(DATE_TRUNC('month', s.data_transacao) AS DATE) AS mes_transacao,
	CAST(EXTRACT(YEAR FROM s.data_transacao) AS INTEGER) AS ano_transacao,
	c.ano_pagamento,

  --- teritorio: setor fiscal = 3 primeiros digitos do SQL completado para 11
    LEFT(LPAD(CAST(s.sql AS TEXT), 11, '0'), 3)             AS setor_fiscal,
    s.sql,
 
    -- atributos do imovel
    s.area_construida,
    s.ano_conclusao,
    s.padrao_cod,
 
    -- valores e preco por metro quadrado (area construida inclui areas comuns)
    s.valor_transacao,
    s.base_calculo,
    ROUND(s.valor_transacao / s.area_construida, 2)         AS preco_m2_nominal,
    ROUND(s.base_calculo    / s.area_construida, 2)         AS preco_m2_base_nominal,
 
    -- correcao pelo IPCA: valor do mes da transacao levado ao mes-base
    ROUND(ib.numero_indice / i.numero_indice, 6)            AS fator_ipca,
    ROUND(s.valor_transacao * ib.numero_indice / i.numero_indice, 2)
                                                            AS valor_real,
    ROUND(s.valor_transacao / s.area_construida * ib.numero_indice / i.numero_indice, 2)
                                                            AS preco_m2_real,
 
    -- apoio a analises de sensibilidade e de repeticao
    s.razao_declarado_base,
    s.flag_declarado_abaixo_vvr,
    s.flag_sql_repetido_no_ano,
 
    -- controles
    (i.numero_indice IS NULL OR ib.numero_indice IS NULL)   AS sem_deflator,
    (CAST(DATE_TRUNC('month', s.data_transacao) AS DATE)
        BETWEEN p.janela_inicio AND p.janela_fim)           AS na_janela_analise
FROM staging.itbi_dti s
JOIN analytics.vw_dti_classificada c
  ON  c.aba_origem   = s.aba_origem
  AND c.linha_origem = s.linha_origem
  AND c.etapa_saida  = 8
CROSS JOIN parametros p
LEFT JOIN analytics.dim_ipca ib ON ib.mes = p.mes_base
LEFT JOIN analytics.dim_ipca i  ON i.mes  = CAST(DATE_TRUNC('month', s.data_transacao) AS DATE);

SELECT COUNT (*) FROM analytics.vw_apto_recorte; 
SELECT COUNT (*) FROM analytics.vw_apto_recorte WHERE na_janela_analise;
SELECT COUNT (*) FROM analytics.vw_apto_recorte WHERE sem_deflator;
SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY preco_m2_nominal) AS mediana_nominal,
          percentile_cont(0.5) WITHIN GROUP (ORDER BY preco_m2_real)     AS mediana_real
FROM analytics.vw_apto_recorte WHERE na_janela_analise;