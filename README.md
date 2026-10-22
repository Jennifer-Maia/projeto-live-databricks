# Data Intake Validator

Solução demonstrativa de Engenharia de Dados. Planilhas Excel chegam de áreas diferentes da
empresa e precisam ser validadas contra um contrato de dados antes de a ingestão permitir a
entrada. O arquivo que passa percorre o lakehouse (Bronze, Silver, Gold) até virar consumo.

```
Usuário → Validação → Ingestão → Bronze → Silver → Gold → Consumo
```

O projeto é construído prompt a prompt, com o Claude Code, a partir do ponto de partida deste
repositório. A sequência dos prompts está em `docs/prompts/`.

## O princípio

A IA reduz o trabalho de implementação, mas não substitui a definição das regras. Por isso o
projeto começa por um contrato, e não por código.

Três consequências aparecem no código:

- **A validação não depende do App.** É um módulo Python puro. O App só mostra o resultado, e a
  mesma validação serve a qualquer mecanismo de ingestão.
- **Nenhum dado é corrigido em silêncio.** O arquivo é aprovado inteiro ou rejeitado inteiro.
  As sugestões são explícitas, e a decisão fica com uma pessoa.
- **Nenhuma regra vive fora do contrato.** As decisões de projeto estão registradas em
  `docs/decisoes.md`, cada uma com a sua justificativa.

## O que tem aqui

| Caminho | O que é |
| --- | --- |
| `docs/projeto.md` | a especificação: objetivo, schema, escopo e critérios de conclusão |
| `docs/decisoes.md` | as decisões sobre os pontos em aberto, cada uma com a justificativa |
| `docs/prompts/` | os prompts que constroem o projeto, na ordem em que são usados |
| `scripts/generate_sales.py` | gera o dataset sintético e os cinco arquivos de teste |
| `scripts/executar_sql.py` | executa um statement SQL no warehouse da workspace |
| `scripts/verificar_estado_live.py` | confere o ponto de partida antes de começar |
| `data/output/` | os cinco `.xlsx` de teste: dois aprovados e três rejeitados |
| `validator/`, `apps/`, `ingestion/`, `notebooks/`, `bronze/`, `silver/`, `gold/` | o layout de destino, ainda vazio: o que vai aqui é construído pelos prompts |

## Pré-requisitos

- Python, com as versões fixadas em `requirements.txt`.
- Um workspace Databricks com um SQL Warehouse chamado **Serverless Starter Warehouse**. O
  script `executar_sql.py` usa esse nome exato e não escolhe outro.
- Databricks CLI autenticada. O perfil é sempre passado com `--profile <perfil>`: nenhum script
  escolhe um perfil por conta própria.
- Permissão para criar catálogo, schemas e Volume.
- Databricks Apps habilitado, no Free Edition ou em plano pago. No Free Edition, há até 3 apps
  por conta, e cada app roda por até 24 horas depois de iniciado, atualizado ou reimplantado.

**Atenção ao catálogo:** em workspaces com *Default Storage*, a plataforma não deixa criar catálogo
pela CLI. Nesse caso, crie `lakehouse_validator` pela interface (Catalog Explorer → Create catalog).
Os schemas e o Volume podem ser criados pela CLI normalmente.

## Como rodar

```bash
python -m pip install -r requirements.txt
python scripts/generate_sales.py
python scripts/verificar_estado_live.py --profile <perfil>
```

Os cinco `.xlsx` já estão versionados em `data/output/`. Gerá-los de novo deve produzir o mesmo
conteúdo. Compare o conteúdo, nunca o hash do arquivo: versões diferentes de pandas e openpyxl
gravam bytes diferentes.

## Os dados

Todos os dados são sintéticos e gerados por `scripts/generate_sales.py`, com semente fixa
(`SEED = 42`) e 1.000 registros de vendas de 15 produtos. Nenhum dado real está neste repositório.

Os cinco arquivos derivam do mesmo dataset base. Cada um muda só um defeito:

| Arquivo | Defeito | Veredito |
| --- | --- | --- |
| `vendas_valido.xlsx` | nenhum | aprovado |
| `vendas_data_texto.xlsx` | `data_venda` como texto no formato `yyyy-MM-dd` | aprovado |
| `vendas_coluna_ausente.xlsx` | `data_venda` renomeada para `dt_venda` | rejeitado, com sugestão de correção |
| `vendas_tipo_invalido.xlsx` | texto em `quantidade` e `valor_unitario` em 5 linhas | rejeitado |
| `vendas_coluna_extra.xlsx` | coluna `observacao_interna`, fora do contrato | rejeitado |

## Limitações conhecidas

De propósito, a demonstração não inclui: autenticação e permissões, histórico de envios,
notificações, vários formatos de arquivo, versionamento de schema, correção automática, detecção
de duplicidade entre arquivos já ingeridos e orquestração. Esses itens são escopo futuro.

## Licença

MIT. Veja o arquivo `LICENSE`.
