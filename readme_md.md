# Priorização de prospecção imobiliária em São Paulo

**Estudo de caso fictício (Apex Imóveis) sobre dados públicos reais de ITBI, 2022–2025:** da planilha bruta da Prefeitura ao dashboard e ao memorando executivo.

![Dashboard: priorização](docs/img/pagina1_priorizacao.png)

## O problema de negócio

A diretoria comercial de uma imobiliária fictícia precisa decidir **onde concentrar um piloto de prospecção** no próximo trimestre. Hoje cada coordenador decide pela própria experiência, e falta um critério comum.

**Pergunta central:** quais segmentos de apartamentos (setor × faixa de área) têm atividade recorrente e preço de referência confiável, mesmo depois de corrigir a inflação e a composição do que é vendido?

## O que os dados mostram

| Métrica | Resultado |
|---|---|
| **Base** | 787.633 guias de ITBI pagas (2022–2025); 228.407 compras e vendas de apartamentos utilizáveis (29,0%) |
| **Janela de análise** | jan/2022 a nov/2025: 222.295 transações em 236 setores fiscais |
| **Preço mediano** | R$ 4.872 por m² (reais de dez/2025; área construída) |
| **Valorização aparente** | cerca de +20% nominal; +5,2% acima do IPCA pela mediana simples |
| **Comparando iguais com iguais** | entre **−0,4% e +1,8%** acima do IPCA (caso base +1,4%; IC de 95%: +0,4% a +2,5%) |
| **Por que a diferença** | mudança no mix: apartamentos de até 50 m² passaram de 7,0% para 13,2% das vendas, e as vendas migraram para setores mais caros (+3,6%) |
| **Segmentos** | 949 com vendas; 355 elegíveis (70% das transações); 174 no núcleo robusto |
| **Recomendação** | piloto em 10 segmentos; outros 10 a validar |

Leia o [memorando executivo](docs/memorando_executivo.md).

## Dashboard (Power BI)

| Priorização | Diagnóstico | Confiabilidade |
|:---:|:---:|:---:|
| ![Priorização](docs/img/pagina1_priorizacao.png) | ![Diagnóstico](docs/img/pagina2_diagnostico.png) | ![Confiabilidade](docs/img/pagina3_confiabilidade.png) |

O arquivo está em `dashboard/apex_imoveis.pbix` e contém **apenas resultados agregados**.

## Como o projeto foi construído

```text
Arquivos oficiais (xlsx) ──► Python: ingestão e padronização ──► CSV tratado
                                                                      │
IPCA (API SIDRA/IBGE) ─────────────────────┐                          ▼
                                           └──► PostgreSQL: staging ► analytics (views e tabelas)
                                                                      │
                                      Notebooks: EDA, índice de preço, ranking ──► tabelas res_*
                                                                      │
                                                        Power BI (3 páginas) + memorando
```

## Decisões de projeto

1. **Auditar antes de modelar.** O arquivo traz uma linha por guia de ITBI paga no mês de referência (e não uma linha por venda), e o formato muda entre abas (cabeçalho ausente, coluna ausente). A ingestão valida o formato e **marca** as linhas problemáticas, sem apagar nenhuma.
2. **O que decidi não calcular.** Tempo de venda, vacância, cap rate e desconto de negociação exigem anúncios, desfecho e dados internos que a fonte não tem. Calculá-los exigiria inventar dados.
3. **Valor declarado e área construída.** O valor é o declarado ao fisco, e a área construída inclui parte das áreas comuns. O R$/m² serve para comparar segmentos entre si e não é o dos anúncios. A base de cálculo do imposto foi testada como alternativa e não muda a conclusão.
4. **Território: setor fiscal.** O campo "bairro" é inutilizável (36% vazio, 5.539 valores distintos). O setor vem dos três primeiros dígitos do cadastro do imóvel.
5. **Prováveis lançamentos ficam fora do recorte.** Sem área construída não há R$/m². Eles são quantificados e documentados (19.142 transações em 2022; 30.906 em 2025).
6. **Valores extremos mantidos, com teste de sensibilidade.** Oito variantes da análise; o resultado fica entre −0,4% e +1,8%.
7. **Critérios transparentes em vez de um score.** Volume, recorrência, comparabilidade e estabilidade, testados com limites mais rígidos e mais frouxos. Só 49% da lista sobrevive ao cenário rígido, por isso o "núcleo robusto".

## Como os resultados foram conferidos

- O funil de exclusão fecha (559.226 excluídas + 228.407 no recorte = 787.633), com verificação automática no notebook.
- A carga no banco compara as contagens com o CSV dentro de uma transação, com *rollback* se divergirem.
- Os cálculos principais foram recalculados de forma independente em pandas.
- O índice tem intervalo de confiança (reamostragem de setores, 200 repetições) e oito testes de sensibilidade.
- Os resultados principais foram conferidos em duas execuções independentes.

## Estrutura do repositório

```text
├── dashboard/      # Power BI (.pbix), só resultados agregados
├── docs/           # memorando executivo e imagens do README
├── notebooks/      # 01 conferência e funil · 02 EDA · 03 índice de preço · 04 ranking
├── referencias/    # tabela oficial de padrões do IPTU
├── sql/            # 01 tabelas · 02 funil · 03 IPCA · 04 recorte · 05 rótulos de setor
├── src/            # conexão, ingestão, carga, IPCA e executor de SQL
├── .env.example
├── .gitignore
└── requirements.txt
```

## Como reproduzir

**Requisitos:** Python 3.13, PostgreSQL 18 local e, para o dashboard, Power BI Desktop. Os arquivos brutos **não** estão no repositório.

```bash
# 1. dependências
pip install -r requirements.txt

# 2. configuração: copie .env.example para .env e preencha a senha do PostgreSQL

# 3. crie o banco, uma vez (pgAdmin ou psql):
CREATE DATABASE apex_imoveis;

# 4. estrutura do banco
python src/executar_sql.py sql/01_criar_tabelas.sql

# 5. dados: baixe os arquivos anuais de ITBI (2022 a 2025) da fonte oficial para dados_brutos/
python src/ingest_itbi.py --saida dados_tratados dados_brutos/*.xlsx
# no PowerShell:
# python src/ingest_itbi.py --saida dados_tratados (Get-ChildItem dados_brutos\*.xlsx).FullName

python src/carregar_itbi.py --entrada dados_tratados --referencias referencias

# 6. views, IPCA e recorte
python src/executar_sql.py sql/02_views_funil.sql
python src/executar_sql.py sql/03_dim_ipca.sql
python src/carregar_ipca.py
python src/executar_sql.py sql/04_view_recorte.sql
python src/executar_sql.py sql/05_dim_setor_fiscal.sql
```

1. Rode os notebooks de cima para baixo, de `01` a `04` (reinicie o kernel antes). Os notebooks `03` e `04` gravam as tabelas `res_*` que o dashboard lê.
2. Abra `dashboard/apex_imoveis.pbix` no Power BI Desktop e atualize a fonte (`localhost`, banco `apex_imoveis`).

## Limitações

- **Atividade observada não é liquidez nem receita.** Não há estoque nem dados internos de conversão.
- O valor é o **declarado ao fisco**, e o R$/m² usa a **área construída**.
- O índice controla tamanho e setor, mas **não a idade nem o padrão construtivo** dos prédios.
- **"Real" significa acima do IPCA**, a inflação geral, e não a inflação específica dos imóveis.
- O **setor fiscal é uma unidade administrativa**, não um bairro.
- **Dez/2025 está incompleto** nos arquivos (guias pagas em 2026) e fica fora da janela.

## Próximos passos

- Incluir idade e padrão construtivo no índice.
- Rotular os setores com uma base geográfica (por exemplo, GeoSampa) e avaliar um mapa.
- Tratar os lançamentos com outra métrica (valor por unidade, sem m²).
- Incorporar o arquivo de 2026 e testar a estabilidade da recomendação.
- Evoluir o design do dashboard.

## Transparência sobre o uso de IA

Escopo, análise e código foram desenvolvidos com apoio de assistentes de IA. Todos os resultados foram executados e conferidos pelo autor, com recálculos independentes.

## Fontes e uso dos dados

- Prefeitura de São Paulo, Secretaria Municipal da Fazenda: [Dados das Transações Imobiliárias com recolhimento de ITBI](https://prefeitura.sp.gov.br/web/fazenda/w/acesso_a_informacao/31501).
- IBGE, [IPCA, API SIDRA, tabela 1737](https://sidra.ibge.gov.br/tabela/1737).
- Os dados brutos não são redistribuídos aqui. Consulte os termos de uso da fonte oficial antes de reutilizá-los.

## Licença

Este projeto está sob a licença [MIT](LICENSE).

## Autor

**Lucas Gumercindo**  
[LinkedIn](https://www.linkedin.com) · [GitHub](https://github.com)