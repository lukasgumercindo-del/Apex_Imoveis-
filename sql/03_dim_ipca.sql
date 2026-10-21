-- Dimensao do IPCA: uma linha por mes, para corrigir valores pela inflacao.
-- Rodar com:  python src\executar_sql.py sql\03_dim_ipca.sql
-- Carregada por:  python src\carregar_ipca.py
--
-- Fonte: IBGE, API SIDRA, tabela 1737.
--   numero_indice        -> variavel 2266 (base: dezembro de 1993 = 100)
--   variacao_mensal_pct  -> variavel 63   (variacao mensal, em pontos percentuais)
-- Limite: o IPCA mede a inflacao geral do consumidor, nao a dos imoveis.

CREATE TABLE IF NOT EXISTS analytics.dim_ipca(
	mes 				DATE 		PRIMARY KEY, --- primeiro dia do mes de referencia
	numero_indice 		NUMERIC		NOT NULL,
	variacao_mensal_pct	NUMERIC,
	fonte				TEXT 		NOT NULL DEFAULT 'IBGE, SIDRA tabela 1737',
	carregado_em 		TIMESTAMPTZ	NOT NULL DEFAULT now()
); 

COMMENT ON TABLE analytics.dim_ipca IS 'IPCA mensal(IBGE). Usado para deflacionar valores de transacao';
COMMENT ON COLUMN analytics.dim_ipca.numero_indice IS 'Numero-indice do IPCA, base dezembro de 1993 = 100'
COMMENT ON COLUMN analytics.dim_ipca.variacao_mensal_pct IS 'Variacao mensal publicada pelo IBGE, em pontos percentuais';