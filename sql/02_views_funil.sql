-- Funil de exclusao: de todas as DTIs pagas ate o recorte da analise.
-- Rodar com:  python src\executar_sql.py sql\02_views_funil.sql
-- Pode ser rodado varias vezes (CREATE OR REPLACE).
--
-- Ideia central: cada linha recebe UMA etapa de saida, a primeira regra que
-- ela falha. Quem passa por todas recebe 8 (esta no recorte). Assim:
--   - toda exclusao tem motivo e quantidade;
--   - a regra do recorte existe em um unico lugar (vw_dti_classificada);
--   - o funil geral e o por ano usam exatamente a mesma classificacao.
--
-- Dado desconhecido nao passa: se uma flag vier vazia (NULL), a linha e tratada
-- como excluida naquela etapa, nunca como aprovada.

-- ---------------------------------------------------------------------------
-- 1) Classificacao: uma linha por DTI, com a etapa em que ela sai do funil.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_dti_classificada AS 
SELECT 
	aba_origem, 
	linha_origem,
	CAST(EXTRACT(YEAR FROM mes_pagamento) AS INTEGER) AS ano_pagamento,
	CASE 
		WHEN flag_compra_venda       IS NOT TRUE  THEN 1   -- natureza
        WHEN flag_apto_condominio    IS NOT TRUE  THEN 2   -- tipo de imovel
        WHEN flag_proporcao_total    IS NOT TRUE  THEN 3   -- fracao do imovel
        WHEN flag_ativo_predial      IS NOT TRUE  THEN 4   -- cadastro
        WHEN flag_linha_desalinhada  IS NOT FALSE THEN 5   -- linha deslocada
        WHEN flag_valor_baixo        IS NOT FALSE THEN 6   -- valor irrisorio
        WHEN flag_area_invalida      IS NOT FALSE THEN 7   -- sem area
        ELSE 8                                             -- permanece no recorte
    END AS etapa_saida,
    (flag_compra_venda IS TRUE AND flag_terreno_com_unidade IS TRUE) AS possivel_lancamento
FROM staging.itbi_dti;

-- ---------------------------------------------------------------------------
-- 2) Funil geral: uma linha por etapa, com excluidas, restantes e motivo.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_funil_exclusao AS
WITH saidas AS (
    SELECT etapa_saida AS etapa, COUNT(*) AS linhas
    FROM analytics.vw_dti_classificada
    GROUP BY etapa_saida
),
rotulos (etapa, regra, motivo) AS (
    VALUES
    (0, 'Ponto de partida: todas as DTIs pagas',
        'Tudo o que a Prefeitura publicou nos arquivos carregados'),
    (1, 'Excluir natureza diferente de compra e venda',
        'Doação, partilha, leilão, permuta etc. não refletem preço de mercado'),
    (2, 'Excluir uso diferente de apartamento em condomínio',
        'Fora do segmento do estudo: casas, terrenos, salas, garagens. Inclui prováveis lançamentos registrados como terreno'),
    (3, 'Excluir proporção transmitida diferente de 100',
        'Fração do imóvel: o valor não corresponde à unidade inteira'),
    (4, 'Excluir cadastro que não é ativo predial',
        'Cadastros cancelados ou territoriais, sem unidade construída'),
    (5, 'Excluir linhas desalinhadas na fonte',
        'Colunas deslocadas: valor ou data ilegíveis'),
    (6, 'Excluir valor declarado até 10 mil reais',
        'Valor irrisório para um apartamento: provável erro ou operação atípica. Regra provisória, a validar na EDA'),
    (7, 'Excluir área construída ausente ou zero',
        'Impossibilita o cálculo do preço por metro quadrado'),
    (8, 'RECORTE FINAL: apartamentos válidos para a análise',
        'Universo sobre o qual o estudo trabalha')
),
funil AS (
    SELECT
        r.etapa,
        r.regra,
        r.motivo,
        CASE WHEN r.etapa IN (0, 8) THEN 0 ELSE COALESCE(s.linhas, 0) END AS excluidas
    FROM rotulos r
    LEFT JOIN saidas s ON s.etapa = r.etapa
),
total AS (
    SELECT COUNT(*) AS n FROM analytics.vw_dti_classificada
)
SELECT
    f.etapa,
    f.regra,
    f.excluidas,
    CAST(t.n - SUM(f.excluidas) OVER (ORDER BY f.etapa) AS BIGINT) AS restantes,
    ROUND(100.0 * (t.n - SUM(f.excluidas) OVER (ORDER BY f.etapa)) / t.n, 1) AS pct_restante,
    f.motivo
FROM funil f
CROSS JOIN total t
ORDER BY f.etapa;
 
-- ---------------------------------------------------------------------------
-- 3) Funil por ano de pagamento: o mesmo funil, uma linha por arquivo.
--    Serve para ver se o recorte e estavel entre os anos.
--    lancamentos_provaveis_fora: compras e vendas registradas como terreno com
--    unidade (provaveis lancamentos), que saem na etapa 2.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_funil_por_ano AS
SELECT
    ano_pagamento,
    COUNT(*)                                         AS dti_pagas,
    COUNT(*) FILTER (WHERE etapa_saida = 1)          AS ex_natureza,
    COUNT(*) FILTER (WHERE etapa_saida = 2)          AS ex_uso,
    COUNT(*) FILTER (WHERE etapa_saida = 3)          AS ex_proporcao,
    COUNT(*) FILTER (WHERE etapa_saida = 4)          AS ex_cadastro,
    COUNT(*) FILTER (WHERE etapa_saida = 5)          AS ex_desalinhada,
    COUNT(*) FILTER (WHERE etapa_saida = 6)          AS ex_valor_baixo,
    COUNT(*) FILTER (WHERE etapa_saida = 7)          AS ex_area,
    COUNT(*) FILTER (WHERE etapa_saida = 8)          AS recorte_final,
    ROUND(100.0 * COUNT(*) FILTER (WHERE etapa_saida = 8) / COUNT(*), 1) AS pct_recorte,
    COUNT(*) FILTER (WHERE possivel_lancamento)      AS lancamentos_provaveis_fora
FROM analytics.vw_dti_classificada
GROUP BY ano_pagamento
ORDER BY ano_pagamento;