CREATE OR REPLACE VIEW analytics.dim_setor_fiscal AS
WITH ruas AS (
    SELECT LEFT(LPAD(CAST(s.sql AS TEXT), 11, '0'), 3) AS setor_fiscal,
           s.logradouro,
           COUNT(*) AS n
    FROM staging.itbi_dti s
    JOIN analytics.vw_dti_classificada c
      ON  c.aba_origem   = s.aba_origem
      AND c.linha_origem = s.linha_origem
      AND c.etapa_saida  = 8
    WHERE s.logradouro IS NOT NULL
    GROUP BY 1, 2
),
ordenadas AS (
    SELECT setor_fiscal,
           logradouro,
           ROW_NUMBER() OVER (PARTITION BY setor_fiscal ORDER BY n DESC, logradouro) AS posicao
    FROM ruas
)
SELECT setor_fiscal,
       STRING_AGG(logradouro, ' / ' ORDER BY posicao) AS ruas_mais_frequentes
FROM ordenadas
WHERE posicao <= 3
GROUP BY setor_fiscal;