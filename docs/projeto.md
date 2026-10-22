# Data Intake Validator — Contrato do Projeto

## 1. Objetivo

Construir uma solução demonstrativa de Engenharia de Dados utilizando Databricks, IA e arquitetura Lakehouse.

O projeto simula um cenário comum de empresas que recebem arquivos Excel de diferentes usuários ou áreas e precisam garantir que esses arquivos estejam de acordo com um contrato de dados antes de permitir sua ingestão no pipeline.

O objetivo principal não é construir uma plataforma completa de Data Quality, mas demonstrar um fluxo funcional e compreensível:

Usuário → Validação → Ingestão → Bronze → Silver → Gold → Consumo

O projeto deve ser suficientemente simples para ser demonstrado em uma live, mas possuir estrutura suficiente para representar uma solução realista de Engenharia de Dados.

---

## 2. Problema de negócio

Arquivos recebidos de usuários podem sofrer alterações entre envios.

Exemplos:

* coluna renomeada;
* coluna removida;
* coluna adicionada inesperadamente;
* alteração de tipo;
* alteração de formato de data;
* valores incompatíveis com o tipo esperado.

Essas alterações podem causar falhas ou comportamentos inesperados em pipelines automatizados.

O projeto deve implementar uma camada de validação antes da ingestão para identificar problemas no arquivo e impedir que arquivos incompatíveis avancem no pipeline.

---

## 3. Dataset

O domínio escolhido é vendas.

O dataset principal deve conter aproximadamente 1.000 registros sintéticos.

O volume não precisa ser grande, mas deve ser suficiente para permitir:

* agregações;
* análises por período;
* análises por produto;
* análises por categoria;
* análises geográficas;
* análises por canal;
* análises por vendedor.

### Schema esperado

| Campo          | Tipo    | Descrição                    |
| -------------- | ------- | ---------------------------- |
| id_venda       | integer | Identificador único da venda |
| data_venda     | date    | Data da venda                |
| id_cliente     | integer | Identificador do cliente     |
| cliente        | string  | Nome do cliente              |
| cidade         | string  | Cidade do cliente            |
| estado         | string  | Estado do cliente            |
| produto        | string  | Produto vendido              |
| categoria      | string  | Categoria do produto         |
| quantidade     | integer | Quantidade vendida           |
| valor_unitario | decimal | Valor unitário do produto    |
| desconto       | decimal | Fração de desconto (0 a 1)   |
| vendedor       | string  | Responsável pela venda       |
| canal_venda    | string  | Canal utilizado na venda     |

`desconto` é uma fração entre `0` e `1` — `0.05` representa 5%, não 5. O campo não usa a
escala 0–100.

---

## 4. Arquivos de teste

O projeto deve possuir pelo menos quatro versões do arquivo de entrada.

### 4.1 Arquivo válido

`vendas_valido.xlsx`

Deve seguir integralmente o contrato de dados.

### 4.2 Coluna renomeada

`vendas_coluna_ausente.xlsx`

A coluna `data_venda` deve ser renomeada para `dt_venda`.

O conteúdo dos dados deve permanecer igual ao arquivo válido.

Objetivo:

Testar detecção de coluna obrigatória ausente e coluna inesperada.

### 4.3 Tipo inválido

`vendas_tipo_invalido.xlsx`

Deve conter alguns valores incompatíveis com os tipos esperados, mantendo a maior parte do dataset válida.

Exemplo:

`quantidade` contendo valores textuais em algumas linhas.

Objetivo:

Testar validação de tipos e valores.

### 4.4 Coluna inesperada

`vendas_coluna_extra.xlsx`

Deve possuir uma coluna adicional chamada `observacao_interna`.

Objetivo:

Testar detecção de colunas não previstas no contrato.

Os arquivos devem ser derivados do mesmo dataset base para que as diferenças entre eles representem exclusivamente os problemas de qualidade que estão sendo demonstrados.

---

## 5. Aplicação

A aplicação será construída como um Databricks App utilizando Python e Streamlit.

Nome:

**Data Intake Validator**

Responsabilidade:

Permitir que o usuário envie um arquivo Excel e receber um diagnóstico sobre sua compatibilidade com o contrato de dados.

### Funcionalidades mínimas

1. Upload de arquivo `.xlsx`.
2. Leitura do arquivo.
3. Validação das colunas obrigatórias.
4. Identificação de colunas inesperadas.
5. Validação de tipos.
6. Validação de datas.
7. Validação de valores numéricos.
8. Resumo da validação.
9. Detalhamento dos erros encontrados.
10. Indicação clara de arquivo aprovado ou rejeitado.

### Comportamento

Arquivo válido:

`READY FOR INGESTION`

Arquivo inválido:

`FILE REJECTED`

O App não deve corrigir silenciosamente os dados.

Quando possível, pode sugerir uma possível correção, mas a decisão deve permanecer explícita para o usuário.

Exemplo:

`data_venda` ausente.

Possível correspondência encontrada:

`dt_venda`

Sugestão:

`Renomear dt_venda para data_venda`

---

## 6. Separação de responsabilidades

A interface do App não deve concentrar toda a lógica de validação.

A lógica responsável por validar o contrato de dados deve ser separada da camada de apresentação sempre que possível.

Isso permitirá reutilizar a validação posteriormente em outros mecanismos de ingestão.

Conceito:

App
↓
Validação
↓
Resultado

A validação não deve depender do Streamlit para funcionar.

---

# 7. Ingestão

Somente arquivos aprovados devem avançar para a ingestão.

O fluxo conceitual é:

Arquivo
↓
Validação
↓
Aprovado
↓
Entrada do Lakehouse
↓
Bronze

A implementação deve priorizar simplicidade e clareza para fins educacionais.

Não adicionar autenticação, APIs externas ou infraestrutura desnecessária.

---

# 8. Bronze

A Bronze representa a camada de entrada do Lakehouse.

Responsabilidade:

Preservar o dado recebido após a validação, adicionando apenas metadados técnicos necessários.

A Bronze não deve aplicar regras de negócio complexas.

Metadados recomendados:

* timestamp de ingestão;
* arquivo de origem;
* identificador ou referência da execução, quando aplicável.

Tabela conceitual:

`bronze.vendas`

---

# 9. Silver

A Silver representa a camada de dados confiáveis e preparados para consumo analítico.

Responsabilidades:

* aplicação de tipos corretos;
* padronização de valores;
* tratamento de nulos quando necessário;
* limpeza de strings;
* aplicação de regras técnicas de qualidade;
* preparação para agregações e análises.

Tabela principal:

`silver.vendas`

As transformações devem ser justificadas e não devem inventar regras de negócio não definidas pelo projeto.

---

# 10. Gold

A Gold deve representar dados orientados ao consumo.

A primeira Gold deve ser uma visão agregada de vendas por produto.

Tabela:

`gold.vendas_por_produto`

Campos esperados:

* produto;
* categoria;
* quantidade de vendas;
* quantidade total vendida;
* faturamento total;
* desconto médio;
* ticket médio.

Outras Golds podem ser criadas caso sejam úteis para a demonstração.

Possíveis extensões:

* vendas por mês;
* vendas por estado;
* vendas por canal;
* vendas por vendedor.

Não criar múltiplas tabelas Gold sem necessidade.

---

# 11. IA no projeto

O projeto deve ser desenvolvido com apoio de ferramentas de IA, principalmente Claude Code e, posteriormente, Genie Code.

A IA pode ser utilizada para:

* geração de código;
* criação da estrutura do projeto;
* explicação de código;
* identificação de problemas;
* sugestões de melhoria;
* criação de transformações;
* documentação.

A IA não deve ser tratada como autoridade sobre regras de negócio.

As decisões sobre:

* schema;
* contrato;
* regras de validação;
* responsabilidades das camadas;
* transformações;
* critérios de qualidade;

devem permanecer explícitas no projeto e ser revisadas pelo responsável.

---

# 12. Princípios técnicos

Priorizar:

* simplicidade;
* legibilidade;
* separação de responsabilidades;
* reprodutibilidade;
* código explicável;
* arquitetura Lakehouse;
* validação antes da ingestão;
* documentação das decisões.

Evitar:

* complexidade desnecessária;
* dependências externas sem necessidade;
* automações que dificultem a explicação;
* regras de negócio inventadas;
* correções silenciosas de dados;
* abstrações excessivas para um projeto demonstrativo.

---

# 13. Objetivo da demonstração

A solução deve permitir demonstrar a seguinte narrativa:

"Recebemos arquivos de uma fonte externa. Antes de permitir que esses arquivos entrem no nosso pipeline, fazemos uma validação baseada em um contrato de dados. Arquivos incompatíveis são rejeitados e o usuário recebe informações suficientes para corrigi-los. Arquivos aprovados seguem para o Lakehouse e percorrem as camadas Bronze, Silver e Gold."

A demonstração deve enfatizar que IA reduz trabalho de implementação, mas não substitui a definição das regras, o entendimento dos dados e a validação humana.

---

# 14. Critério de conclusão

O projeto será considerado funcional quando:

* o dataset puder ser reproduzido;
* os arquivos válidos e inválidos puderem ser gerados;
* o App conseguir validar os arquivos;
* arquivos inválidos forem identificados corretamente;
* arquivos válidos puderem seguir para ingestão;
* Bronze estiver disponível;
* Silver estiver disponível;
* pelo menos uma Gold útil estiver disponível;
* as principais decisões arquiteturais estiverem documentadas;
* o fluxo puder ser explicado e reproduzido durante uma demonstração.

---

# 15. Escopo futuro

Os seguintes recursos podem ser considerados posteriormente, mas não fazem parte do escopo inicial:

* autenticação;
* histórico de arquivos enviados;
* versionamento de schemas;
* configuração dinâmica do contrato;
* auto-correção de arquivos;
* notificações;
* múltiplos tipos de arquivo;
* integração com agentes;
* perguntas em linguagem natural sobre a Gold;
* dashboards;
* monitoramento avançado de qualidade.

Esses recursos devem ser tratados como extensões e não devem aumentar a complexidade da primeira versão sem necessidade.
