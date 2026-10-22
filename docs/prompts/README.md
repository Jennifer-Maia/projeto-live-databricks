# Os prompts

A sequência que constrói o Data Intake Validator, na ordem em que é usada. Cada prompt é
autocontido: copie o arquivo inteiro, cole no Claude Code dentro do repositório e deixe rodar.

**Não pule a ordem.** Cada prompt assume que o anterior terminou. O 02 lê o contrato que o 01
escreveu, e o 05 grava no catálogo que o 00 criou.

## O mapa

| # | Prompt | O que produz | Onde toca |
| --- | --- | --- | --- |
| 00 | [setup](00-setup.md) | catálogo, 4 schemas e o Volume `entrada` | workspace Databricks |
| 01 | [contrato](01-contrato.md) | `docs/contrato-de-dados.md` | repositório |
| 02 | [validação](02-validacao.md) | `validator/` e o verificador | repositório |
| 03 | [app](03-app.md) | o App Streamlit, implantado como Databricks App | `apps/` e workspace |
| 04 | [ponte](04-ponte.md) | o `.xlsx` aprovado convertido em `.csv` no Volume | `ingestion/` e Volume |
| 05 | [bronze](05-bronze.md) | `bronze.vendas`, com metadados técnicos | `notebooks/` e warehouse |
| 06 | [silver](06-silver.md) | `silver.vendas`, tipada | `notebooks/` e warehouse |
| 07 | [gold](07-gold.md) | `gold.vendas_por_produto` e a consulta final | `notebooks/` e warehouse |

O prompt 00 é o único que pede confirmação antes de executar: ele cria o catálogo, e criar é
barato, mas desfazer não é. Os prompts 03 a 07 alteram o repositório e a workspace ao mesmo
tempo (o App, o Volume e as tabelas). As camadas 05 a 07 rodam SQL pelo
`scripts/executar_sql.py`, e não por Jobs nem por Pipelines.

## Antes do prompt 00: as decisões

As decisões não estão em nenhum prompt. Antes do 00, peça ao Claude que leia `docs/projeto.md`
e liste os pontos em aberto **sem consultar `docs/decisoes.md`**. Depois decida os que aparecerem
e só então siga. A sessão precisa ser nova: uma sessão que já leu `decisoes.md` responde que
tudo já está decidido.

## Ponto de partida

O repositório começa sem o contrato de dados (`docs/contrato-de-dados.md`) e sem o módulo de
validação (`validator/`). Eles são criados pelos prompts 01 e 02. Se o contrato já existir antes do
prompt 01, o Claude vai encontrar um arquivo que o prompt manda criar. O script
`scripts/verificar_estado_live.py` confere justamente essa ausência.
