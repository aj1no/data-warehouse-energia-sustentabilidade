# FACULDADE DE TECNOLOGIA DE JUNDIAÍ - FATEC JUNDIAÍ
## CURSO DE TECNOLOGIA EM CIÊNCIA DE DADOS

<br/><br/><br/><br/>

### RODOLFO VINICIUS CIMA TAKEMOTO
### TIAGO GALHARDO AVELAR

<br/><br/><br/><br/>

## DATA WAREHOUSE PARA ANÁLISE DA MATRIZ ENERGÉTICA MUNDIAL:
### Um estudo sobre geração elétrica renovável, fóssil e de baixo carbono

<br/><br/><br/><br/><br/><br/><br/><br/>

#### JUNDIAÍ
#### 2026

---

### RODOLFO VINICIUS CIMA TAKEMOTO
### TIAGO GALHARDO AVELAR

<br/><br/><br/><br/>

## DATA WAREHOUSE PARA ANÁLISE DA MATRIZ ENERGÉTICA MUNDIAL:
### Um estudo sobre geração elétrica renovável, fóssil e de baixo carbono

<br/><br/><br/><br/>

<p align="right">
Relatório técnico e acadêmico apresentado ao Curso de Tecnologia em Ciência de Dados da Faculdade de Tecnologia de Jundiaí (FATEC Jundiaí), como requisito parcial para a aprovação na disciplina Banco e Armazém de Dados.
<br/><br/>
<b>Orientação:</b> Prof. Rafael Gross
</p>

<br/><br/><br/><br/><br/><br/>

#### JUNDIAÍ
#### 2026

---

### RESUMO

Este relatório apresenta o desenvolvimento de um Data Warehouse (DW) completo, projetado em DuckDB, SQL e Python, destinado a analisar a evolução da geração elétrica mundial por fonte de energia. O principal objetivo é classificar e comparar a geração elétrica de fontes renováveis, fósseis e de baixo carbono entre países e ao longo do tempo, utilizando o dataset público *Our World in Data Energy Dataset*. O modelo dimensional adota a modelagem estrela (Star Schema) de Kimball, contendo uma tabela fato centralizada no grão de país, ano e fonte de energia, e três dimensões de suporte: data, país (com histórico implementado via Slowly Changing Dimension - SCD Tipo 2 por faixas socioeconômicas) e fonte de energia. Para otimizar as consultas analíticas, foi projetada uma tabela agregada anual. As análises englobam a evolução temporal da matriz elétrica brasileira, o ranking dos principais países geradores de fontes renováveis, a agregação multidimensional, a análise de cohort para a penetração de energia solar e o cálculo de KPIs de negócio. O pipeline implementado é totalmente idempotente, garantindo reprodutibilidade das cargas. Os testes de validação de integridade referencial demonstraram ausência de chaves órfãs e total consistência lógica dos dados consolidados no banco de dados colunar DuckDB.
<br/><br/>
<b>Palavras-chave:</b> Data Warehouse. Modelagem Dimensional. DuckDB. Transição Energética. SCD Tipo 2.

---

### SUMÁRIO ESTRUTURADO

* 1 Introdução
* 2 Fundamentação Teórica
  * 2.1 Modelagem Dimensional de Kimball
  * 2.2 Camadas de Dados: Staging e OLTP Intermediário
  * 2.3 Histórico de Dimensões com SCD Tipo 2
  * 2.4 Banco de Dados Analítico DuckDB
* 3 Metodologia e Fonte de Dados
* 4 Modelagem Dimensional do Data Warehouse
  * 4.1 Grão da Tabela Fato
  * 4.2 Atributos das Dimensões
  * 4.3 Definição das Métricas
* 5 Pipeline de Carga (ETL) e Idempotência
* 6 Consultas Analíticas e KPIs de Negócio
* 7 Visualizações Gráficas e Dashboard
* 8 Avaliação de Performance e Otimização
* 9 Resultados e Validação de Qualidade de Dados
* 10 Conclusão
* Referências

---

## 1 INTRODUÇÃO

A transição para matrizes de geração elétrica com menor intensidade de emissão de carbono constitui um dos principais desafios contemporâneos na agenda geopolítica e ambiental global. O acompanhamento rigoroso do progresso das energias renováveis e de baixo carbono, em comparação com os combustíveis fósseis tradicionais, demanda a consolidação de grandes volumes de dados históricos. Contudo, bases de dados brutas de caráter público costumam apresentar estruturas transacionais (wide tables) com dezenas de colunas esparsas e problemas de integridade referencial, o que inviabiliza análises analíticas ágeis e de alta granularidade.

Neste contexto, o presente projeto acadêmico propõe a modelagem e a construção de um Data Warehouse (DW) robusto focado na análise da Matriz Energética Mundial. O objetivo geral é estabelecer um pipeline analítico ponta a ponta que processe os dados reais da *Our World in Data (OWID)*, estruture-os em um esquema dimensional estrela e produza análises fundamentadas sobre a evolução temporal, o ranking de liderança em energias limpas e o comportamento de cohorts de países na transição para fontes específicas, como a energia solar. O relatório a seguir é estruturado em padrão acadêmico inspirado nas normas ABNT, especialmente NBR 14724 e NBR 6023, documentando rigorosamente a arquitetura conceitual e física adotada.

---

## 2 FUNDAMENTAÇÃO TEÓRICA

### 2.1 Modelagem Dimensional de Kimball
A arquitetura dimensional consolidada por Ralph Kimball preconiza que o banco de dados analítico deve ser estruturado com foco na facilidade de uso pelos tomadores de decisão e no alto desempenho de leitura. O modelo estrela (*Star Schema*) organiza a base em dois tipos de tabelas: as tabelas fato, que armazenam as medidas quantitativas e numéricas dos eventos de negócio (métricas), e as tabelas dimensão, que descrevem o contexto detalhado do evento (quem, onde, quando, o quê). Essa separação reduz o número de junções necessárias na execução das consultas SQL comparado ao modelo normalizado tradicional (Entity-Relationship).

### 2.2 Camadas de Dados: Staging e OLTP Intermediário
A construção de um armazém de dados moderno adota uma estratégia de separação de responsabilidades em camadas físicas de dados:
- **Camada Staging (`stg`)**: Área de pouso dos dados extraídos na qual o arquivo bruto (CSV) é ingerido sem transformações estruturais de negócio. O foco principal é a carga rápida e a conversão inicial dos tipos primitivos de dados.
- **Camada OLTP Intermediária (`oltp`)**: Área de preparação na qual os dados sofrem normalização, filtragem de registros inválidos (como códigos ISO não nacionais) e enriquecimento conceitual preliminar (determinação de faixas populacionais e cálculo do PIB per capita).

### 2.3 Histórico de Dimensões com SCD Tipo 2
A técnica de dimensões que sofrem alteração lenta (*Slowly Changing Dimensions* - SCD) resolve o desafio de rastrear dados descritivos que mudam ao longo do tempo. Na SCD Tipo 2, quando um atributo descritivo de uma dimensão sofre modificação, uma nova linha é inserida na tabela contendo a nova versão do registro, atribuindo-se chaves substitutas distintas para cada estado histórico e controlando sua vigência com atributos de tempo (`start_year`, `end_year` e o marcador lógico `is_current`). No escopo deste projeto, a dimensão de país cria versões históricas para preservar a exatidão analítica no momento do registro do fato quando faixas de população ou PIB per capita mudam de intervalo de classificação.

### 2.4 Banco de Dados Analítico DuckDB
O DuckDB é um sistema de gerenciamento de banco de dados (SGBD) relacional voltado para processos analíticos (OLAP) de vetorização colunar em memória. Projetado para integração profunda com ambientes de programação Python e R, ele oferece execução SQL nativa veloz sobre dados tabulares estruturados, combinando a facilidade de implantação de um banco embarcado (como o SQLite) com o poder analítico de processamento de consultas com agregação rápida típicos de grandes plataformas corporativas.

---

## 3 METODOLOGIA E FONTE DE DADOS

O pipeline utiliza o dataset unificado **Our World in Data Energy Dataset**, mantido publicamente e atualizado continuamente pela OWID. A extração dos dados brutos é feita via requisição HTTP direta ao arquivo CSV hospedado na infraestrutura pública da OWID:

`https://owid-public.owid.io/data/energy/owid-energy-data.csv`

A metodologia de desenvolvimento compreende as seguintes fases:
1. **Ingestão automatizada**: Download condicional e dinâmico do CSV em lote.
2. **Transformação Estrutural (Pipeline SQL)**: Execução ordenada de 6 scripts SQL em lote no DuckDB. O fluxo limpa dados, normaliza tabelas e preenche as chaves substitutas no banco.
3. **Carga e Medição**: População física da tabela fato e das tabelas dimensões no banco colunar, gerando dados analíticos limpos de forma idempotente.
4. **Visualização e Publicação**: Geração automatizada de gráficos em vetor SVG e consolidação de um Dashboard HTML estático acoplado a relatórios em PDF.

---

## 4 MODELAGEM DIMENSIONAL DO DATA WAREHOUSE

O modelo analítico do projeto adota a arquitetura estrela clássica com relacionamentos de integridade referencial implementados através de chaves substitutas (*surrogate keys*).

### 4.1 Grão da Tabela Fato
O grão da tabela fato `dw.fact_energy_generation` é definido como: **uma linha por país, ano e fonte de energia**. Isso assegura granularidade suficiente para detalhar a transição da matriz energética em nível nacional sem inflar desnecessariamente o volume de armazenamento analítico.

### 4.2 Atributos das Dimensões
- **`dw.dim_date`**: Armazena o ano como a chave de tempo primária. Os atributos associados são a década correspondente, o primeiro dia do ano de referência (`year_start_date`), o flag de ano atual do sistema (`is_current_year`) e o flag indicativo do ano mais recente presente na base histórica do dataset (`is_latest_dataset_year`).
- **`dw.dim_country`**: Dimensão histórica (SCD Tipo 2). Contém a chave substituta autogerada (`country_key`), o nome do país, o código ISO-3 de identificação internacional, faixas descritivas de classificação populacional (`population_band`) e de PIB per capita (`gdp_per_capita_band`), além dos intervalos de vigência temporal do registro (`start_year` e `end_year`) e do sinalizador de registro atual (`is_current`).
- **`dw.dim_energy_source`**: Classifica as fontes energéticas. Armazena o nome da fonte (Solar, Wind, Hydro, Nuclear, Coal, Gas, Oil, Biofuel, Other renewable), o grupo conceitual correspondente (`Renewable`, `Fossil`, ou `Low Carbon`) e os respectivos sinalizadores lógicos (`is_renewable` e `is_low_carbon`).

### 4.3 Definição das Métricas
A tabela fato armazena as seguintes variáveis quantitativas:
- `electricity_twh`: Volume físico bruto de geração elétrica no ano medido em Terawatt-hora.
- `electricity_share_pct`: Participação percentual que a fonte específica representa sobre o total de geração de eletricidade da localidade naquele ano.
- `population` e `gdp`: Métricas demográficas e econômicas de contexto para a ponderação ponderada de indicadores socioeconômicos.

---

## 5 PIPELINE DE CARGA (ETL) E IDEMPOTÊNCIA

O pipeline ETL foi projetado para rodar em lote e ser rigorosamente idempotente. Isso significa que, independentemente de quantas vezes o pipeline de carga for reexecutado, o estado final do Data Warehouse permanecerá consistente e sem duplicação física de registros nas tabelas dimensionais ou fatos.

O fluxo é sequenciado pelos scripts localizados no diretório `/scripts`:
1. `00_staging.sql`: Cria o esquema de staging e importa o CSV.
2. `01_oltp.sql`: Normaliza e transpõe a tabela larga da OWID em tabelas longas relacionais, estruturando as observações de fonte em linhas.
3. `02_dw_model.sql`: Cria fisicamente a estrutura relacional do DW com chaves primárias e relacionamentos.
4. `03_etl_load.sql`: Executa a lógica de Slowly Changing Dimension (SCD Tipo 2) para a tabela de países e popula a tabela fato por meio de cruzamentos históricos usando `o.year BETWEEN c.start_year AND c.end_year`.
5. `04_analytics.sql`: Consolida os resultados das consultas analíticas e gera as tabelas de validação.
6. `05_performance.sql`: Agrupa dados em tabelas físicas para aceleração de relatórios.

---

## 6 CONSULTAS ANALÍTICAS E KPIS DE NEGÓCIO

Foram consolidadas cinco consultas analíticas obrigatórias materializadas no banco de dados analítico DuckDB:

- **Q1 - Evolução Temporal**: Mede o crescimento e a variação da geração elétrica das fontes eólica, solar e hidrelétrica no Brasil ano a ano, mapeando a evolução física da geração limpa nacional.
- **Q2 - Ranking TOP N**: Lista os 10 principais países geradores de energia renovável (em TWh) no ano mais recente do dataset (2025).
- **Q3 - Agregação Multidimensional**: Agrupa a geração elétrica em TWh consolidando por grupo de fonte (Renováveis, Fósseis e Baixo Carbono) e por país para fins de comparação geopolítica.
- **Q4 - Análise de Cohort e Retenção**: Identifica a data em que cada país rompeu o patamar de 1% de participação de energia solar na sua matriz e calcula a taxa de permanência acima dessa linha de corte nos anos subsequentes.
- **Q5 - KPI de Participação Renovável**: Calcula o percentual ponderado de geração limpa em relação ao total modelado de energia de cada país, fornecendo um indicador do progresso rumo à descarbonização.

---

## 7 VISUALIZAÇÕES GRÁFICAS E DASHBOARD

A validação analítica gerou quatro visualizações obrigatórias salvas em formatos vetoriais e integradas no painel visual:
1. **Gráfico de Linha**: Representa a evolução temporal das energias Solar, Eólica e Hidrelétrica no Brasil, evidenciando o crescimento expressivo das novas renováveis.
2. **Gráfico de Barras**: Exibe o ranking dos top 10 maiores produtores de eletricidade limpa em 2025.
3. **Heatmap Analítico**: Representa de forma matricial a evolução percentual de cada fonte de geração elétrica na matriz do Brasil ao longo dos anos.
4. **Dashboard HTML Integrado**: Uma interface estática web unificada que centraliza KPIs de negócio essenciais e renderiza nativamente os gráficos SVG associados e tabelas de benchmark.

---

## 8 AVALIAÇÃO DE PERFORMANCE E OTIMIZAÇÃO

Para otimizar o tempo de resposta das consultas corporativas de nível gerencial, foi criada a tabela agregada física `dw.fact_energy_generation_annual_grouped`, que pré-calcula a soma das gerações anuais agregadas por ano, país e grupo conceitual de fonte de energia.

Um teste comparativo de benchmark foi conduzido para medir os tempos médios de resposta do banco ao executar a mesma agregação a partir da tabela fato original com múltiplos joins dimensionais versus a leitura otimizada na tabela agregada.
Os dados obtidos empiricamente com o dataset real apontam:
- **Consulta Fato Original**: Média de **9,27 ms** por consulta.
- **Consulta Tabela Agregada**: Média de **2,61 ms** por consulta.

Isso representa um ganho médio de velocidade de **3,56 vezes** na renderização e recuperação de relatórios analíticos anuais agrupados.

---

## 9 RESULTADOS E VALIDAÇÃO DE QUALIDADE DE DADOS

Para manter o rigor e a confiabilidade analítica exigida, foram estruturadas quatro consultas de teste e qualidade de dados materializadas em tabelas de auditoria:
1. **`validation_row_counts`**: Realiza o censo físico de linhas por tabela para auditoria de perdas no ETL.
2. **`validation_fk_nulls`**: Verifica a integridade física de chaves estrangeiras nulas na tabela fato. O teste acusou 0 ocorrências de chaves nulas em todas as dimensões de junção.
3. **`validation_integrity`**: Detecta chaves órfãs na fato com buscas lógicas (left joins). O teste acusou zero órfãos nas conexões dimensionais.
4. **`validation_generation_by_source`**: Verifica se as somas brutas das fontes fecham com as quantidades consolidadas na extração primária.

---

## 10 CONCLUSÃO

O presente projeto demonstrou a viabilidade prática da construção de um Data Warehouse de alto desempenho focado em transição energética e sustentabilidade. Através da modelagem estrela de Kimball e da implementação física sobre o SGBD DuckDB, foi possível extrair dados brutos e não estruturados da Our World in Data, limpá-los por meio de staging, transpor métricas via camadas intermediárias e carregá-los de forma consistente, preservando o histórico geográfico via SCD Tipo 2.

Os testes de qualidade e consistência física evidenciaram um DW confiável, seguro para reexecuções e ágil, com ganhos expressivos de performance através do uso de tabelas agregadas. A estruturação acadêmica do relatório técnico com foco nas principais teorias e nas normas indicativas contribui para a clareza expositiva do artefato de engenharia de dados entregue.

---

## REFERÊNCIAS

DUCKDB. **DuckDB Documentation**. Disponível em: <https://duckdb.org/docs/>. Acesso em: 25 mai. 2026.

KIMBALL, Ralph; ROSS, Margy. **The Data Warehouse Toolkit**: The Definitive Guide to Dimensional Modeling. 3. ed. Indianapolis: John Wiley & Sons, 2013.

OUR WORLD IN DATA. **OWID Energy Dataset**. Disponível em: <https://owid-public.owid.io/data/energy/owid-energy-data.csv>. Acesso em: 25 mai. 2026.

PANDAS. **Pandas: powerful Python data analysis toolkit**. Disponível em: <https://pandas.pydata.org/docs/>. Acesso em: 25 mai. 2026.

PYTHON SOFTWARE FOUNDATION. **Python Language Reference**, version 3.12. Disponível em: <https://www.python.org/>. Acesso em: 25 mai. 2026.
