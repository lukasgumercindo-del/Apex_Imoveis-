# Priorização de Prospecção Imobiliária em São Paulo 🏢

**Estudo de caso fictício (Apex Imóveis) sobre dados públicos reais de ITBI, 2022–2025:** da planilha bruta da Prefeitura ao dashboard e ao memorando executivo. 

## 📌 O Problema de Negócio

A diretoria comercial de uma imobiliária fictícia precisa decidir **onde concentrar um piloto de prospecção** no próximo trimestre. Hoje cada coordenador decide pela própria experiência, e falta um critério comum.

**Pergunta central:** quais segmentos de apartamentos (setor × faixa de área) têm atividade recorrente e preço de referência confiável, mesmo depois de corrigir a inflação e a composição do que é vendido?

---

## 📊 O Que os Dados Mostram

| Métrica / Recorte | Resultado |
| :--- | :--- |
| **Base total** | 787.633 guias de ITBI pagas (2022–2025); 228.407 compras e vendas de apartamentos utilizáveis (29,0%) |
| **Janela de análise** | Jan/2022 a Nov/2025: 222.295 transações em 236 setores fiscais |
| **Preço mediano** | R$ 4.872 por m² (reais de dez/2025; área construída) |
| **Valorização aparente** | Cerca de +20% nominal; +5,2% acima do IPCA pela mediana simples |
| **Comparando iguais com iguais** | Entre **−0,4% e +1,8%** acima do IPCA (caso base +1,4%; IC de 95%: +0,4% a +2,5%) |
| **Por que a diferença** | Mudança no mix: apartamentos de até 50 m² passaram de 7,0% para 13,2% das vendas, e as vendas migraram para setores mais caros (+3,6%) |
| **Segmentos** | 949 com vendas; 355 elegíveis (70% das transações); 174 no núcleo robusto |
| **Recomendação** | Piloto em 10 segmentos recomendados; outros 10 a validar |

> 📄 Leia o [Memorando Executivo](docs/memorando_executido.md) completo para entender os detalhes da estratégia.

---

## 🖥️ Dashboard (Power BI)

O relatório interativo foi construído no Power BI Desktop e estruturado em **3 páginas analíticas complemento-estratégicas**, permitindo que a diretoria navegue do nível executivo ao detalhe metodológico:

* **Página 1: Priorização**  
  Apresenta os KPIs de volume e cobertura de mercado, uma tabela detalhada dos segmentos elegíveis (com ruas de referência, volume de transações, R$/m² mediano e índice de dispersão) e um gráfico de ranking destacando os **10 segmentos recomendados** para a atuação imediata e os **10 a validar**.

* **Página 2: Diagnóstico**  
  Analisa a evolução temporal do preço real dos imóveis. Exibe o índice trimestral com intervalo de confiança e um comparativo anual demonstrando como o controle por tamanho e setor reduz a valorização real aparente de **+5,2% para +1,4%**, além do gráfico de sensibilidade que avalia a variação sob diferentes cenários de estresse.

* **Página 3: Confiabilidade**  
  Oferece governança e transparência ao projeto. Apresenta as limitações declaradas do estudo, o funil completo de exclusão das 787 mil guias originais até o recorte analítico e uma análise de sensibilidade testando a robustez dos segmentos diante de critérios mais rígidos e frouxos.

*O arquivo do relatório está disponível no repositório em `dashboard/apex_imoveis.pbix` e contém apenas os resultados agregados.*

---

## 🏗️ Como o Projeto Foi Construído

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

---

## 🎯 Decisões de Projeto

1. **Auditar antes de modelar:** O arquivo traz uma linha por guia de ITBI paga no mês de referência (e não uma linha por venda), e o formato muda entre abas (cabeçalho ausente, coluna ausente). A ingestão valida o formato e marca as linhas problemáticas, sem apagar nenhuma.
2. **O que decidi não calcular:** Tempo de venda, vacância, cap rate e desconto de negociação exigem anúncios, desfecho e dados internos que a fonte não tem. Calculá-los exigiria inventar dados.
3. **Valor declarado e área construída:** O valor é o declarado ao fisco, e a área construída inclui parte das áreas comuns. O R$/m² serve para comparar segmentos entre si e não é o dos anúncios. A base de cálculo do imposto foi testada como alternativa e não muda a conclusão.
4. **Território (Setor fiscal):** O campo "bairro" é inutilizável (36% vazio, 5.539 valores distintos). O setor vem dos três primeiros dígitos do cadastro do imóvel.
5. **Lançamentos fora do recorte:** Prováveis lançamentos sem área construída não geram R$/m² e ficam fora do estudo principal. Eles são quantificados e documentados à parte (19.142 transações em 2022; 30.906 em 2025).
6. **Valores extremos mantidos com sensibilidade:** Foram testadas oito variantes da análise; o resultado final de valorização fica consistentemente entre −0,4% e +1,8%.
7. **Critérios transparentes em vez de score arbitrário:** Volume, recorrência, comparabilidade e estabilidade foram testados com limites mais rígidos e frouxos. Como apenas 49% da lista sobrevive ao cenário mais rígido, definimos o "núcleo robusto".

---

## ✅ Como os Resultados Foram Conferidos

* O **funil de exclusão fecha perfeitamente** (559.226 excluídas + 228.407 no recorte = 787.633), com verificação automática via script no notebook.
* A carga no banco compara as contagens com o CSV dentro de uma transação SQL, executando *rollback* em caso de divergência.
* Os cálculos do índice e agrupamentos foram recalculados de forma independente em Python/Pandas.
* O índice de preço conta com intervalo de confiança de 95% (reamostragem de setores por bootstrap, 200 repetições) e 8 testes de sensibilidade.
* Todos os resultados foram reexecutados e auditados em duas execuções independentes.

---

## 📁 Estrutura do Repositório

```text
apex-imoveis/
├── dashboard/      # Power BI (.pbix), contendo apenas os dados agregados
├── docs/           # Memorando executivo e imagens para o README
│   └── img/        # Prints em alta resolução das telas do dashboard
├── notebooks/      # 01 conferência e funil · 02 EDA · 03 índice de preço · 04 ranking
├── referencias/    # Tabela oficial de padrões do IPTU
├── sql/            # 01 tabelas · 02 funil · 03 IPCA · 04 recorte · 05 rótulos de setor
├── src/            # Scripts Python: conexão, ingestão, carga, IPCA e executor de SQL
├── .env.example    # Exemplo de variáveis de ambiente
├── .gitignore      # Arquivos ignorados no versionamento Git
├── README.md       # Documentação principal do projeto
└── requirements.txt# Dependências do projeto Python

```

---

## ⚙️ Como Reproduzir

### **Requisitos:**

Python 3.13+, PostgreSQL 18 local e Power BI Desktop. *(Os dados brutos não são redistribuídos neste repositório)*.

```bash
# 1. Instalar dependências de bibliotecas
pip install -r requirements.txt

# 2. Configuração: copie .env.example para .env e preencha a senha do seu PostgreSQL

# 3. Crie o banco de dados (no pgAdmin ou psql):
CREATE DATABASE apex_imoveis;

# 4. Criar a estrutura das tabelas no banco
python src/executar_sql.py sql/01_criar_tabelas.sql

# 5. Processar os dados: baixe os arquivos de ITBI (2022 a 2025) da fonte oficial para dados_brutos/
python src/ingest_itbi.py --saida dados_tratados dados_brutos/*.xlsx
# No PowerShell Windows:
# python src/ingest_itbi.py --saida dados_tratados (Get-ChildItem dados_brutos\*.xlsx).FullName

python src/carregar_itbi.py --entrada dados_tratados --referencias referencias

# 6. Criar views, carregar dimensão IPCA e aplicar o recorte
python src/executar_sql.py sql/02_views_funil.sql
python src/executar_sql.py sql/03_dim_ipca.sql
python src/carregar_ipca.py
python src/executar_sql.py sql/04_view_recorte.sql
python src/executar_sql.py sql/05_dim_setor_fiscal.sql

```

7. Execute os notebooks na pasta `notebooks/` na ordem numérica de `01` a `04`. Os notebooks `03` e `04` geram as tabelas agregadas `res_*` lidas pelo Power BI.
8. Abra o arquivo `dashboard/apex_imoveis.pbix` no Power BI Desktop e atualize as fontes de dados para apontar para o seu servidor local (`localhost`, banco `apex_imoveis`).

---

## ⚠️ Limitações Conhecidas

* **Atividade observada não indica liquidez nem receita:** A base não possui dados de estoque ou taxa de conversão comercial.
* **R$/m² baseado em área construída:** Usa o valor declarado ao fisco e inclui proporcionalmente as áreas comuns.
* **Sem idade e padrão do prédio:** O índice controla tamanho e setor, mas não a idade ou estado de conservação do imóvel.
* **Definição de "Real":** Refere-se estritamente aos valores deflacionados pelo IPCA (inflação oficial geral) e não à inflação imobiliária.
* **Setor Fiscal:** Trata-se de uma unidade de cadastro administrativo da Prefeitura, não correspondendo exatamente aos limites de bairros.
* **Dezembro/2025:** Mês parcialmente incompleto nos arquivos brutos oficiais devido ao ciclo de recolhimento no ano seguinte.

---

## 🔮 Próximos Passos

* [ ] Incorporar variáveis de idade e padrão construtivo no modelo estatístico do índice.
* [ ] Mapear os setores fiscais utilizando arquivos geográficos (shapefiles do GeoSampa) para visualização em mapas.
* [ ] Criar uma esteira de análise específica para o segmento de lançamentos (valor global por unidade).
* [ ] Atualizar o pipeline com a entrada da base de dados de 2026 para validar a estabilidade das recomendações.


## 📚 Fontes dos Dados

* Prefeitura de São Paulo, Secretaria Municipal da Fazenda: [Dados das Transações Imobiliárias (ITBI)](https://prefeitura.sp.gov.br/web/fazenda/w/acesso_a_informacao/31501).
* IBGE: [Tabela 1737 - IPCA (API SIDRA)](https://sidra.ibge.gov.br/tabela/1737).

---

## 📜 Licença

Este projeto está sob a licença [MIT](https://www.google.com/search?q=LICENSE).

---

## 👤 Autor

**Lucas Gumercindo**

* LinkedIn: [https://www.linkedin.com/in/lucas-gumercindo/](https://www.google.com/search?q=https://www.linkedin.com/in/lucas-gumercindo/)
* GitHub: [https://github.com/LucasGumercindo](https://www.google.com/search?q=https://github.com/LucasGumercindo)
