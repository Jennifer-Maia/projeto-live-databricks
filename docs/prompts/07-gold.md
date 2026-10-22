# Prompt 07 — A Gold

> Cole este texto inteiro no Claude Code, dentro do repositório do projeto.

Este é o **prompt 07**, o último da sequência que constrói o Data Intake Validator. Ele
produz `notebooks/03_gold.sql` — a tabela `gold.vendas_por_produto`, orientada a consumo.

A Silver existe desde o prompt 06 e **não muda neste passo**. Este passo **cria tabela na
workspace**: pede a minha confirmação antes de executar.

---

## Contexto

A Gold é a camada de consumo: dado agregado, no formato em que uma área de negócio o
usaria. A primeira Gold é a visão de vendas por produto (§10) — e as fórmulas não são
invenção nossa: faturamento líquido (6.5), ticket médio (6.6) e desconto médio (6.15)
estão decididos desde o começo do projeto.

Carregue as skills `databricks-core` e `databricks-dbsql`.

---

## O que fazer agora

Um arquivo: `notebooks/03_gold.sql`, com **um único statement**:

```sql
CREATE OR REPLACE TABLE lakehouse_validator.gold.vendas_por_produto AS
SELECT
  produto,
  categoria,
  COUNT(*)                                                               AS quantidade_vendas,
  SUM(quantidade)                                                        AS quantidade_total_vendida,
  ROUND(SUM(quantidade * valor_unitario * (1 - desconto)), 2)            AS faturamento_total,
  AVG(desconto)                                                          AS desconto_medio,
  ROUND(SUM(quantidade * valor_unitario * (1 - desconto)) / COUNT(*), 2) AS ticket_medio
FROM lakehouse_validator.silver.vendas
GROUP BY produto, categoria
ORDER BY faturamento_total DESC;
```

Cada campo, com sua origem:

| Campo | Fórmula | Origem |
| --- | --- | --- |
| `quantidade_vendas` | `COUNT(*)` | cada linha é uma venda — decisão 6.6 |
| `quantidade_total_vendida` | `SUM(quantidade)` | campo distinto da contagem — §10 |
| `faturamento_total` | `SUM(quantidade × valor_unitario × (1 − desconto))` | faturamento **líquido** — decisão 6.5 |
| `desconto_medio` | `AVG(desconto)` | média simples — decisão 6.15 |
| `ticket_medio` | `faturamento líquido / COUNT(*)` | decisão 6.6 |

O `ROUND(..., 2)` é de **apresentação** — duas casas para leitura, não uma regra de
negócio. As fórmulas são as das decisões; o arredondamento é da tela.

Execute com:

```bash
python scripts/executar_sql.py notebooks/03_gold.sql --profile <perfil>
```

O `--profile` é escolhido por mim — nunca presuma. Antes de rodar, me mostre o SQL e aguarde
a confirmação.

---

## De onde vem cada regra

| Assunto | Origem |
| --- | --- |
| A visão por produto e seus campos | `docs/projeto.md` §10 |
| Faturamento líquido, com desconto aplicado | decisão 6.5 |
| Ticket médio = líquido ÷ contagem de vendas | decisão 6.6 |
| Desconto médio é média simples | decisão 6.15 |
| Uma Gold só; não criar tabelas sem necessidade | §10 e §12 |
| Execução por arquivo `.sql` | decisão 6.13 |

---

## Armadilhas conhecidas

**1. `COUNT(*)`, não `SUM(quantidade)`, para "quantidade de vendas".** São dois campos
diferentes e é fácil trocá-los: uma venda pode ter 10 unidades. `SUM(quantidade)` é a
"quantidade total vendida"; a contagem de vendas é o número de linhas (decisão 6.6).

**2. O desconto entra na conta.** `SUM(quantidade * valor_unitario)` seria faturamento
bruto, que a Gold **não** reporta — a decisão 6.5 fixou o líquido.

**3. `AVG` simples no desconto.** Sem ponderar por faturamento — decisão 6.15.

**4. `ORDER BY` na tabela é conveniência de leitura.** O agrupamento é o que define o
conteúdo; a ordenação deixa a tabela já apresentável para a consulta final da live.

**5. Um statement por arquivo.** O runner não divide o texto por `;`.

---

## Não faça

- **não crie outras tabelas Gold** — extensões como vendas por mês ou por estado são
  escopo futuro (§15); uma Gold basta para a demonstração;
- **não altere a Silver** nem reprocesse camadas anteriores;
- **não invente métrica** que não esteja no §10 ou nas decisões — e não remova nenhuma das
  cinco;
- **não escolha o perfil** nem rode sem a minha confirmação;
- **não pare aqui sem me mostrar o resultado** — este é o último passo, e a consulta final
  é parte dele.

---

## Critério de aceite

Rode as verificações com
`python scripts/executar_sql.py --sql "<consulta>" --profile <perfil>`:

- [ ] `SELECT COUNT(*) FROM lakehouse_validator.gold.vendas_por_produto` → **15** (os 15
      produtos do gerador);
- [ ] o resultado tem as sete colunas: `produto`, `categoria`, `quantidade_vendas`,
      `quantidade_total_vendida`, `faturamento_total`, `desconto_medio`, `ticket_medio`;
- [ ] a consulta final —

      ```sql
      SELECT * FROM lakehouse_validator.gold.vendas_por_produto
      ORDER BY faturamento_total DESC LIMIT 10;
      ```

      devolve os produtos em ordem decrescente de faturamento;
- [ ] em uma linha qualquer, `ticket_medio = faturamento_total / quantidade_vendas` (com
      o arredondamento de duas casas);
- [ ] a soma de `quantidade_total_vendida` da Gold bate com
      `SELECT SUM(quantidade) FROM lakehouse_validator.silver.vendas` — nenhuma linha se
      perdeu no caminho;
- [ ] nenhuma outra tabela foi criada.

---

## Quando terminar

Me diga o que criou, cole a saída da consulta final, e **pare**. A sequência terminou — o
fluxo inteiro está de pé: validação, ingestão, Bronze, Silver e Gold.

Se algum ponto da camada não estiver definido em `projeto.md` nem em `decisoes.md`,
**não decida sozinho**: me apresente o ponto e a sua recomendação, e eu decido.
