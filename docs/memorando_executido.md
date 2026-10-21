# Memorando executivo: piloto de prospecção residencial em São Paulo

**Para:** Diretoria comercial e coordenação regional · **De:** Lucas Gumercindo (Análise de Dados) · **Data:** 15/10/2026
*Estudo de caso fictício (Apex Imóveis) sobre dados públicos reais de ITBI da Prefeitura de São Paulo, 2022–2025.*

## Decisão solicitada
Aprovar um piloto de prospecção de um trimestre nos **10 segmentos recomendados** abaixo e validar com a coordenação os **10 segmentos a validar**.

## O que os dados mostram
1. **Mercado ativo e concentrado.** Foram analisadas 787.633 guias de ITBI pagas. Dessas, 228.407 (29,0%) são compras e vendas de apartamentos com dados utilizáveis. Na janela de jan/2022 a nov/2025 há 222.295 transações em 236 setores fiscais. A mediana é de **R$ 4.872 por m²** (reais de dez/2025; área construída).
2. **Sem valorização real relevante.** O preço nominal subiu cerca de 20% de 2022 a 2025, e a mediana simples sugere +5,2% acima do IPCA. Parte disso é mudança no mix vendido: os apartamentos de até 50 m² passaram de 7,0% para 13,2% das vendas, e as vendas migraram para setores mais caros (+3,6%). Comparando apartamentos do mesmo tamanho e do mesmo setor, a variação real fica **entre −0,4% e +1,8%** (caso base +1,4%, com intervalo de 95% de +0,4% a +2,5%): menos de 1% ao ano acima da inflação. **A recomendação não depende de expectativa de valorização.**
3. **Segmentos confiáveis.** Dos 949 segmentos (setor × faixa de área) com vendas, 355 têm volume, recorrência, preço comparável e estável (70% das transações). Desses, 174 resistem a critérios mais rígidos (núcleo robusto).
4. **Entre os 20 segmentos mais ativos, 10 são do núcleo robusto.** Os outros 10 ficam de fora do núcleo apenas por terem preço mais disperso (dispersão de 0,40 a 0,48), embora com volume e estabilidade adequados.

## Recomendação
**Piloto nos 10 segmentos robustos mais ativos** (cerca de 800 transações por trimestre, aproximadamente 6% da atividade do recorte):

| Setor | Faixa (m²) | Rua de referência | Transações/trim. | R$/m² mediano | Ticket mediano |
|---|---|---|---|---|---|
| 078 | 80–120 | Av. Raimundo Pereira de Magalhães | 106 | 3.648 | R$ 340 mil |
| 169 | 80–120 | R. Jaracatiá | 95 | 3.590 | R$ 324 mil |
| 047 | 80–120 | Av. Fagundes Filho | 91 | 5.048 | R$ 507 mil |
| 157 | 80–120 | Av. dos Ourives | 84 | 2.917 | R$ 280 mil |
| 085 | 80–120 | R. João de Lacerda Soares | 83 | 7.158 | R$ 715 mil |
| 101 | 80–120 | Av. Eng. Heitor Antônio Eiras Garcia | 71 | 4.245 | R$ 451 mil |
| 020 | 80–120 | R. do Bosque | 70 | 5.342 | R$ 513 mil |
| 087 | 120–200 | R. Luiz Seraphico Júnior | 70 | 6.045 | R$ 925 mil |
| 007 | 50–80 | Av. São João | 70 | 5.525 | R$ 357 mil |
| 171 | 80–120 | R. Dr. Luiz Migliano | 69 | 4.051 | R$ 400 mil |

**A validar com a coordenação** (alto volume e preço estável, mas preço de referência mais espalhado):
- 120–200 m²: setores 171, 085, 090 e 013.
- 80–120 m²: setores 062, 049, 089, 041 e 010.
- até 50 m²: setor 007.

## Limites que o gestor precisa conhecer
- **Atividade observada não é liquidez nem receita da Apex.** Não há estoque nem dados internos de conversão.
- O valor é o **declarado ao fisco**. Usar a base de cálculo do imposto no lugar dele dá resultado parecido, mas isso não prova que o valor declarado reflita o preço efetivamente pago.
- O R$/m² usa a **área construída**, que inclui áreas comuns, e não é o R$/m² dos anúncios.
- O índice controla **tamanho e setor**, mas **não a idade nem o padrão construtivo** dos prédios (informações que existem na base e podem entrar numa próxima versão).
- "Real" significa **acima do IPCA**, a inflação geral do consumidor, e não a inflação específica dos imóveis.
- O **setor fiscal é uma unidade administrativa, não um bairro**. As ruas listadas são apenas referência.
- **Prováveis lançamentos ficam fora** (19.142 transações em 2022 e 30.906 em 2025, por ano de pagamento): sem área construída não há preço por m². O estudo cobre apartamentos já cadastrados individualmente.
- **Dez/2025 está incompleto** nos arquivos (guias pagas em 2026) e fica fora da janela.

## Como medir o piloto
- Registrar, por segmento: contatos com proprietários, imóveis captados, custo por captação e tempo até a captação.
- Se a operação permitir, concentrar o esforço em metade dos segmentos recomendados (sorteados) e manter a outra metade como referência, para evitar atribuir ao piloto o que seria sazonalidade ou mudança de equipe.
- Reavaliar os critérios com o próximo arquivo anual do ITBI.

## O que mudaria esta recomendação
- A coordenação indicar que algum segmento está saturado ou é inacessível.
- Os dados internos do piloto mostrarem conversão baixa em algum segmento.
- Os novos arquivos de ITBI alterarem a recorrência ou a dispersão dos segmentos.
- A decisão de incluir lançamentos, que exigiria outra métrica (por exemplo, valor por unidade, sem m²).

## Fontes e reprodução
- Prefeitura de São Paulo, Secretaria Municipal da Fazenda: *Dados das Transações Imobiliárias com recolhimento de ITBI* (arquivos anuais de 2022 a 2025).
- IBGE: IPCA, API SIDRA, tabela 1737.
