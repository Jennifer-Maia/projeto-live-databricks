# Prompt 05 — A Bronze

> Cole este texto inteiro no Claude Code, dentro do repositório do projeto.

Este é o **prompt 05** da sequência que constrói o Data Intake Validator. Ele produz o
primeiro arquivo de camada: `notebooks/01_bronze.sql` — a tabela `bronze.vendas`, com o
dado que chegou ao Volume mais os metadados técnicos.

A ponte nasceu no prompt 04 e os `.csv` já estão no Volume. Este passo **cria tabela na
workspace**: pede a minha confirmação antes de executar.

---

## Contexto

A Bronze é a camada de entrada do Lakehouse: **ela preserva o dado recebido** e acrescenta
apenas os metadados técnicos do §8 — quando o dado chegou, de qual arquivo, e sob qual
execução. Nada de regra de negócio, nada de tipagem: isso é a Silver (decisão 6.10).

A execução é por `scripts/executar_sql.py`, que já existe no repositório: ele lê um arquivo
`.sql`, roda no SQL Warehouse e mostra o resultado. Carregue as skills `databricks-core` e
`databricks-dbsql` e siga o que elas dizem sobre `read_files` e sobre os comandos.

---

## O que fazer agora

Um arquivo: `notebooks/01_bronze.sql`, com **um único statement**:

```sql
CREATE OR REPLACE TABLE lakehouse_validator.bronze.vendas AS
SELECT
  id_venda,
  data_venda,
  id_cliente,
  cliente,
  cidade,
  estado,
  produto,
  categoria,
  quantidade,
  valor_unitario,
  desconto,
  vendedor,
  canal_venda,
  current_timestamp()        AS data_ingestao,
  _metadata.file_name        AS arquivo_origem,
  '__ID_EXECUCAO__'          AS id_execucao
FROM read_files(
  '/Volumes/lakehouse_validator/raw/entrada/*.csv',
  format => 'csv',
  header => true,
  inferColumnTypes => false
);
```

As treze colunas do contrato são listadas **uma a uma**, e não com `*`. Motivo: o
`read_files` acrescenta por padrão a coluna `_rescued_data` (dado que não casou com o
esquema), e um `*` a deixaria passar para a tabela. Listar as colunas a deixa de fora
sem depender de opção do `read_files` — que, nos testes, não aceitou `NULL` nem string
vazia para desligá-la.

**Tudo chega como texto.** `inferColumnTypes => false` desliga a inferência de tipos do
`read_files`. Sem essa opção, a Bronze sai tipada (`id_venda` como `int`, `data_venda` como
`timestamp`, `desconto` como `double`) — e isso não é bruto. A Bronze preserva o que chegou; os
tipos são trabalho da Silver (decisão 6.10). Medido no ensaio: com a opção, os CASTs da Silver
passam sobre o texto dos dois arquivos aprovados sem nenhuma falha.

As três colunas de metadados são a decisão 6.22, e rastreiam o §8:

| Coluna | O que registra |
| --- | --- |
| `data_ingestao` | quando esta execução leu o arquivo |
| `arquivo_origem` | de qual arquivo do Volume a linha veio |
| `id_execucao` | sob qual execução — o runner troca `__ID_EXECUCAO__` por um id único |

**`__ID_EXECUCAO__` é literal no arquivo.** Não invente um valor: quem substitui é o
runner, uma vez por execução. É o que permite distinguir a carga de hoje da de ontem sem
guardar histórico de uploads (§15).

Execute com:

```bash
python scripts/executar_sql.py notebooks/01_bronze.sql --profile <perfil>
```

O `--profile` é escolhido por mim — nunca presuma. Antes de rodar, me mostre o SQL e aguarde
a confirmação.

---

## De onde vem cada regra

| Assunto | Origem |
| --- | --- |
| Preservar o dado + metadados técnicos; sem regra de negócio | `docs/projeto.md` §8 |
| Nomes `data_ingestao`, `arquivo_origem`, `id_execucao` | decisão 6.22 |

> **Por que o `id_execucao` só existe na Bronze.** A Bronze é quem ingere, então é quem carimba a execução. A Silver copia esse valor e não gera um próprio, e a Gold não carrega metadados: é a decisão 6.22. Se perguntarem, não é esquecimento, é a fronteira.
| O Volume e seu caminho; a ponte entrega os csv | decisões 6.7 e 6.8 |
| Execução por arquivo `.sql`, sem Jobs nem pipelines | decisão 6.13 |
| A tipagem fica para a Silver | decisão 6.10 |

---

## Armadilhas conhecidas

**1. `read_files` não lê `.xlsx`.** É por isso que a ponte existe: o SQL lê os `.csv` que
o prompt 04 gerou, no mesmo Volume. Se os csv não estiverem lá, a tabela nasce vazia — não
é erro de sintaxe.

**2. No SQL, o caminho do Volume é `/Volumes/...` — sem `dbfs:`.** O prefixo `dbfs:` é
exigência do CLI (`databricks fs`), não do `read_files`. Trocar os dois é o erro mais
provável deste passo.

**3. O warehouse fica STOPPED fora de uso.** A primeira execução sobe o compute e demora
alguns segundos a mais — o runner já espera e avisa. Não é travamento, e a segunda consulta
é instantânea.

**4. Um statement por arquivo.** O runner **não** divide o texto por `;` — ele envia o
arquivo inteiro. Mantenha um `CREATE OR REPLACE TABLE` e mais nada.

**5. `_metadata.file_name` traz o nome do arquivo; `file_path` traz o caminho inteiro.**
Queremos o nome (é o que identifica o arquivo de origem). Se `_metadata.file_name` não
estiver disponível na sua versão do runtime, o plano B é
`substring_index(_metadata.file_path, '/', -1)` — me avise se precisar dele.

**6. Não crie Job, Pipeline nem notebook.** A camada é um arquivo `.sql` executado pelo
runner. É a decisão 6.13.

**7. Os dois aprovados entram na mesma tabela — de propósito.** São 2000 linhas: o
`vendas_valido.xlsx` (data como datetime) e o `vendas_data_texto.xlsx` (data como texto).
A Bronze aceita as duas formas porque ela preserva; quem converte é a Silver (decisão 6.3).

**Consequência que a plateia vai ver: a Gold sai com o faturamento dobrado.** Cada arquivo
é validado sozinho, e nenhuma camada detecta que os dois trazem as mesmas vendas (decisão 6.9).
Isso é uma lição, não um erro: diga em voz alta, mostre a `COUNT(DISTINCT id_venda) = 1000` ao
lado de `COUNT(*) = 2000`, e pergunte à plateia o que deveria acontecer.

---

## Não faça

- **não crie tabela além de `bronze.vendas`** — Silver e Gold são os próximos passos;
- **não altere o Volume** nem os csv que a ponte gerou;
- **não aplique regra de negócio nem tipo** — nem cast, nem filtro, nem deduplicação;
- **não escolha o perfil** nem rode sem a minha confirmação;
- **não avance para a Silver** — é o prompt 06.

---

## Critério de aceite

Rode as verificações com
`python scripts/executar_sql.py --sql "<consulta>" --profile <perfil>`:

- [ ] `SELECT COUNT(*) FROM lakehouse_validator.bronze.vendas` → **2000**;
- [ ] `SELECT DISTINCT arquivo_origem FROM lakehouse_validator.bronze.vendas` → os **2**
      nomes dos arquivos que estão no Volume (terminando em `.csv`);
- [ ] `SELECT COUNT(DISTINCT id_execucao) FROM lakehouse_validator.bronze.vendas` → **1**;
- [ ] `DESCRIBE lakehouse_validator.bronze.vendas` mostra **16** colunas: as 13 do contrato
      **mais** as três de metadados, sem `_rescued_data`; e `SELECT * FROM
      lakehouse_validator.bronze.vendas LIMIT 5` mostra os valores sem nenhuma transformação;
- [ ] rodar o arquivo de novo **não duplica** nada — a tabela é substituída, e o
      `id_execucao` muda (é uma execução nova);
- [ ] nenhum Job, pipeline ou notebook foi criado.

---

## Quando terminar

Me diga o que criou, cole a saída das verificações, e **pare**. Não avance para a Silver.

Se algum ponto da camada não estiver definido em `projeto.md` nem em `decisoes.md`,
**não decida sozinho**: me apresente o ponto e a sua recomendação, e eu decido.
