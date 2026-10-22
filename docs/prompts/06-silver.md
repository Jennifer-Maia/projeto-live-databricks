# Prompt 06 — A Silver

> Cole este texto inteiro no Claude Code, dentro do repositório do projeto.

Este é o **prompt 06** da sequência que constrói o Data Intake Validator. Ele produz
`notebooks/02_silver.sql` — a tabela `silver.vendas`, com os tipos corretos e o texto
padronizado.

A Bronze existe desde o prompt 05 e **não muda neste passo**. Este passo **cria tabela na
workspace**: pede a minha confirmação antes de executar.

---

## Contexto

A Silver é a camada do dado confiável: **tipos corretos, strings limpas, pronta para
agregação**. É aqui — e só aqui — que o dado é transformado (decisões 6.3 e 6.10). A
Bronze preservou; a Silver prepara.

Carregue as skills `databricks-core` e `databricks-dbsql` e siga o que elas dizem sobre
funções e tipos.

---

## O que fazer agora

Um arquivo: `notebooks/02_silver.sql`, com **um único statement**:

```sql
CREATE OR REPLACE TABLE lakehouse_validator.silver.vendas AS
SELECT
  CAST(id_venda       AS INT)             AS id_venda,
  to_date(data_venda)                     AS data_venda,
  CAST(id_cliente     AS INT)             AS id_cliente,
  trim(cliente)                           AS cliente,
  trim(cidade)                            AS cidade,
  trim(estado)                            AS estado,
  trim(produto)                           AS produto,
  trim(categoria)                         AS categoria,
  CAST(quantidade     AS INT)             AS quantidade,
  CAST(valor_unitario AS DECIMAL(10,2))   AS valor_unitario,
  CAST(desconto       AS DECIMAL(4,2))    AS desconto,
  trim(vendedor)                          AS vendedor,
  trim(canal_venda)                       AS canal_venda,
  data_ingestao,
  arquivo_origem,
  id_execucao
FROM lakehouse_validator.bronze.vendas;
```

Três blocos de transformação, cada um com sua origem:

| Transformação | Por quê |
| --- | --- |
| `CAST` nos inteiros e decimais | a Bronze guardou o que o csv trazia como texto; aqui o tipo passa a ser o do contrato |
| `to_date(data_venda)` | converte **as duas formas** aceitas pelo contrato: a data nativa e o texto `yyyy-MM-dd` (decisão 6.3) |
| `trim` nas strings | padronização é da Silver, não do Validator (decisão 6.10) |

As três colunas de metadados **seguem para a Silver** — elas continuam sendo a
rastreabilidade da linha (decisão 6.22).

Execute com:

```bash
python scripts/executar_sql.py notebooks/02_silver.sql --profile <perfil>
```

O `--profile` é escolhido por mim — nunca presuma. Antes de rodar, me mostre o SQL e aguarde
a confirmação.

---

## De onde vem cada regra

| Assunto | Origem |
| --- | --- |
| Tipos corretos, padronização, limpeza de strings | `docs/projeto.md` §9 |
| A conversão da data é da Silver — e aceita as duas formas | decisão 6.3 |
| A fronteira: o Validator verifica, a Silver transforma | decisão 6.10 |
| As colunas de metadados | decisão 6.22 |
| Não inventar regra de negócio | `docs/projeto.md` §9 e §12 |

---

## Armadilhas conhecidas

**1. `to_date` é o que torna a decisão 6.3 real.** Na Bronze, `data_venda` chega com as
duas formas misturadas — o csv do `vendas_valido.xlsx` traz `2026-01-15 00:00:00` e o do
`vendas_data_texto.xlsx` traz `2026-01-15`. O `to_date` converte as duas sem escolher
formato na mão.

**2. `trim` nos dois lados se a coluna vier com espaços.** O dataset de teste não tem
espaços sobrando, mas a padronização é justamente para o que não está no dataset de teste.
É barato e é da camada.

**3. Não filtre, não deduplique, não "limpe" linha.** O arquivo que chegou aqui foi
aprovado pelo contrato — não há linha inválida para remover. Se houvesse, o trabalho não
seria da Silver: seria de quem corrige a origem (decisão 6.18).

**4. Um statement por arquivo.** O runner não divide o texto por `;`.

**5. O warehouse sobe sozinho se estiver parado** — a primeira consulta demora alguns
segundos a mais.

---

## Não faça

- **não crie tabela além de `silver.vendas`** — a Gold é o próximo passo;
- **não altere a Bronze** nem reprocesse o Volume;
- **não aplique regra de negócio** — nada de filtrar vendas, agrupar, calcular desconto;
  isso é da Gold;
- **não descarte as colunas de metadados** — a rastreabilidade as acompanha;
- **não escolha o perfil** nem rode sem a minha confirmação;
- **não avance para a Gold** — é o prompt 07.

---

## Critério de aceite

Rode as verificações com
`python scripts/executar_sql.py --sql "<consulta>" --profile <perfil>`:

- [ ] `DESCRIBE lakehouse_validator.silver.vendas` mostra:
      `id_venda`/`id_cliente`/`quantidade` `int`; `valor_unitario` `decimal(10,2)`;
      `desconto` `decimal(4,2)`; `data_venda` `date`; as strings `string`; e as três
      colunas de metadados;
- [ ] `SELECT COUNT(*) FROM lakehouse_validator.silver.vendas` → **2000**;
- [ ] `SELECT MIN(data_venda), MAX(data_venda) FROM lakehouse_validator.silver.vendas`
      devolve datas (formato `yyyy-MM-dd`), não texto;
- [ ] `SELECT COUNT(*) FROM lakehouse_validator.silver.vendas WHERE data_venda IS NULL`
      → **0** — as duas formas de data foram convertidas;
- [ ] `SELECT COUNT(*) FROM lakehouse_validator.silver.vendas WHERE desconto = 0` é maior
      que zero — vendas sem desconto continuam válidas e presentes (decisão 6.1);
- [ ] nenhuma linha foi filtrada: a contagem bate com a da Bronze.

---

## Quando terminar

Me diga o que criou, cole a saída das verificações, e **pare**. Não avance para a Gold.

Se algum ponto da camada não estiver definido em `projeto.md` nem em `decisoes.md`,
**não decida sozinho**: me apresente o ponto e a sua recomendação, e eu decido.
