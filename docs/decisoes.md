# Decisões do Projeto — Data Intake Validator

Registro das decisões tomadas sobre os pontos em aberto levantados na análise de
[projeto.md](projeto.md). Existe para atender ao §11 do contrato, que exige que as
decisões sobre schema, contrato, regras de validação, responsabilidades das camadas e
critérios de qualidade permaneçam explícitas no projeto.

**Este documento registra decisões. Não é o contrato de dados** — a definição formal e
legível do contrato fica em `docs/contrato-de-dados.md` (criado no prompt 01), e a representação
estruturada usada pela aplicação será derivada dela.

## Status

| Status | Significado |
| --- | --- |
| **Resolvida** | Decidida. Pronta para implementar. |
| **Adiada** | Fora do caminho crítico desta versão. |

## Resumo

| # | Tema | Status |
| --- | --- | --- |
| 6.1 | `desconto` como fração | Resolvida |
| 6.2 | Domínios de valor | Resolvida |
| 6.3 | Formato de `data_venda` | Resolvida |
| 6.4 | Onde o contrato vive | Resolvida |
| 6.5 | Faturamento líquido | Resolvida |
| 6.6 | Ticket médio | Resolvida |
| 6.7 | Entrada da Bronze | Resolvida |
| 6.8 | Catálogo e schema | Resolvida |
| 6.9 | Reprocessamento | Resolvida |
| 6.10 | Fronteira Validator ↔ Silver | Resolvida |
| 6.11 | Formato do diagnóstico | Resolvida |
| 6.12 | Sugestões de correção | Resolvida |
| 6.13 | Execução na demo | Resolvida |
| 6.14 | Deploy do App | Resolvida |
| 6.15 | `desconto médio` na Gold | Resolvida |
| 6.16 | Unicidade de `id_venda` | Resolvida |
| 6.17 | Coluna inesperada | Resolvida |
| 6.18 | Veredito parcial | Resolvida |
| 6.19 | Separador decimal | Resolvida |
| 6.20 | Campo vazio | Resolvida |
| 6.21 | Receita de leitura do arquivo | Resolvida |
| 6.22 | Colunas de metadados e da Gold | Resolvida |

**22 resolvidas, 0 pendentes de ambiente, 0 adiadas.** Nenhum item bloqueia mais a
implementação.

As decisões **6.17 a 6.20** não vieram da análise do `projeto.md` — surgiram ao escrever o
[contrato-de-dados.md](contrato-de-dados.md), quando o texto genérico do projeto encontrou
os casos concretos dos arquivos de teste. Estão registradas aqui pelo mesmo motivo que as
outras: o contrato precisa ser reproduzível, e uma regra que existe só na cabeça de quem
escreveu não é.

A **6.21** veio de mais adiante ainda — da implementação do módulo de validação, quando a
leitura do arquivo deixou de ser uma suposição e virou uma medição. A **6.22** veio da
construção das camadas, quando os metadados técnicos da Bronze e os campos da Gold
precisaram de nome antes de existir em SQL.

---

# Decisões resolvidas

## 6.1 — `desconto`: fração decimal entre 0 e 1

`desconto` é armazenado como fração decimal. `0.05` representa 5%. O campo **não** usa a
escala 0–100.

`docs/projeto.md` §3 foi ajustado para refletir isso. A decisão é consistente entre
`projeto.md`, `contrato-de-dados.md` (a criar) e a implementação.

## 6.2 — Domínios de valor

Validamos domínio fechado **somente quando ele estiver claramente definido** pelo dataset
ou pelo contrato. Nesta primeira versão:

| Campo | Regra |
| --- | --- |
| `quantidade` | `> 0` |
| `valor_unitario` | `> 0` |
| `desconto` | entre `0` e `1`, inclusive |
| `categoria` | um dos valores do dataset atual |
| `canal_venda` | um dos valores do dataset atual |
| `estado` | uma das 27 UFs oficiais brasileiras |

**Fonte dos valores categóricos:** o gerador/dataset existente, não a imaginação.

- `categoria` — Eletrônicos, Periféricos, Móveis, Acessórios, Armazenamento
- `canal_venda` — Online, Loja Física, Marketplace

**Sobre `estado`:** o domínio são as **27 UFs oficiais brasileiras**, com exatamente 2
caracteres. A validação **não** é limitada às 10 UFs que o dataset de teste exercita
atualmente (PR, SP, RJ, MG, SC, RS, DF, GO, BA, PE) — esses são apenas os valores
presentes nos dados, não o domínio.

> **Consequência consciente:** com domínio fechado, um arquivo que traga uma categoria
> nova legítima será **rejeitado**. Isso é o comportamento pretendido — o contrato é
> fechado por definição. Não tratar como defeito.

## 6.3 — `data_venda`: datetime ou texto em `yyyy-MM-dd`

O Validator aceita:

- datas que o Excel entrega como **datetime válido**;
- valores textuais no formato **`yyyy-MM-dd`**.

Qualquer outro formato textual é rejeitado. A padronização final para o tipo de data é
responsabilidade da **Silver**, não do Validator.

## 6.4 — O contrato: documentação separada da implementação

- `docs/contrato-de-dados.md` — documentação legível, para humanos. **A criar.**
- A aplicação usa uma **representação estruturada e centralizada** do contrato, derivada
  da documentação, para evitar regras espalhadas pelo código.

A representação estruturada é o único lugar onde as regras de validação são declaradas. O
Validator lê dela; não redefine nada.

## 6.5 — Faturamento líquido

```
faturamento_liquido = quantidade × valor_unitario × (1 - desconto)
```

O desconto é aplicado. A Gold não reporta faturamento bruto.

## 6.6 — Ticket médio

```
ticket_medio = faturamento_liquido / quantidade_de_vendas
```

Cada registro do dataset representa **uma venda**. Portanto `quantidade_de_vendas` é a
contagem de linhas, não a soma de `quantidade` — que é o que o §10 chama de "quantidade
total vendida", um campo distinto.

## 6.7 — Entrada da Bronze

A área de entrada é um **Unity Catalog Volume dentro do schema `raw`** do catálogo
`lakehouse_validator`.

Fluxo: o App valida o `.xlsx` e, **somente se aprovado**, grava o arquivo nesse Volume. A
ingestão lê do Volume e escreve em `bronze.vendas`, acrescentando os metadados técnicos do
§8 — timestamp de ingestão, arquivo de origem e referência da execução.

Manter o Volume em `raw`, e não em `bronze`, deixa **arquivo** e **tabela** em schemas
distintos — alinhado ao comentário que já descreve a camada raw como "dados brutos, como
chegam das fontes (SQL, API, planilhas)".

O Volume se chama **`entrada`**, fixado pela qualificação de três partes:

```
lakehouse_validator.raw.entrada
```

O App grava o arquivo aprovado nesse caminho; a ingestão lê dele.

## 6.8 — Catálogo e schema

**Catálogo novo e dedicado:** `lakehouse_validator`, a criar na workspace.

Optou-se por **não** reaproveitar os catálogos existentes:

- os catálogos que já existem no workspace — pertencem a outros projetos e carregam schemas
  alheios, o que polui o Catalog Explorer durante a demonstração;
- `workspace` — catálogo padrão do metastore.

**Layout do catálogo:**

| Schema | Papel |
| --- | --- |
| `raw` | Área de entrada — contém o Volume onde o App deposita o arquivo aprovado |
| `bronze` | Tabela `vendas` — dado preservado + metadados técnicos |
| `silver` | Tabela `vendas` — dado tipado e limpo |
| `gold` | Tabela `vendas_por_produto` — agregação de consumo |

Os nomes lógicos do contrato passam a ter qualificação de três partes:

```
lakehouse_validator.bronze.vendas
lakehouse_validator.silver.vendas
lakehouse_validator.gold.vendas_por_produto
```

## 6.9 — Reprocessamento

A primeira versão **não resolve o problema de histórico de uploads** (que segue no escopo
futuro, §15), mas **não pode duplicar o mesmo arquivo silenciosamente**.

Metadados disponíveis para identificar reprocessamento: nome do arquivo e, se necessário,
hash do conteúdo.

> A detecção de duplicidade **entre** arquivos já ingeridos fica como evolução futura,
> junto com a estratégia de idempotência. Ver 6.16.

## 6.10 — Fronteira Validator ↔ Silver

| Camada | Responsabilidade |
| --- | --- |
| **Validator** | Verifica se o arquivo de entrada respeita o contrato |
| **Silver** | Normalizações e transformações técnicas, **depois** que o arquivo foi aprovado |

Não duplicar regras entre as duas camadas sem necessidade. Este é um princípio — a
fronteira concreta será verificada na prática durante a implementação, quando ficar claro
se alguma regra está sendo checada nos dois lugares.

Aplicação direta nesta versão: **o Validator aceita `yyyy-MM-dd` e datetime; a Silver
converte para o tipo final.** O Validator não faz a conversão.

## 6.11 — Formato do diagnóstico

O diagnóstico apresenta:

1. quantidade de linhas analisadas;
2. quantidade total de problemas;
3. colunas afetadas;
4. resumo por tipo de problema;
5. uma amostra limitada dos primeiros erros.

Não listar centenas de erros na interface.

A amostra é limitada a **20 ocorrências**, fixado em
[contrato-de-dados.md](contrato-de-dados.md) §6. O limite é de apresentação, não de
validação: o arquivo é analisado por inteiro, e o total reportado é sempre o total
verdadeiro — a amostra aparece sempre acompanhada dele.

## 6.12 — Sugestões de correção

Limitadas a **similaridade entre nomes de colunas** — por exemplo `dt_venda` →
`data_venda`.

O sistema **não corrige automaticamente**. Sugere, e a decisão permanece com o usuário.

## 6.13 — Execução na demonstração

**Um arquivo `.sql` por camada**, no diretório `notebooks/` que já existe no repositório:

```
notebooks/01_bronze.sql
notebooks/02_silver.sql
notebooks/03_gold.sql
```

Cada arquivo tem um único statement, executado no SQL Warehouse Serverless por
`scripts/executar_sql.py` (databricks-sdk, `statement_execution`) — três execuções
encadeadas durante a live, uma por camada. Um arquivo por camada porque preserva a
separação de responsabilidades do §6 e porque cada execução dá o gancho natural para
explicar o que aquela camada faz.

A escolha do SQL tem uma razão concreta: **o `read_files` do warehouse não lê `.xlsx`** —
csv, json, parquet, orc, avro, text e binário, e só. Como a entrada do projeto é planilha,
a conversão precisa ser um passo explícito: a **ponte** (`ingestion/converter_para_csv.py`,
prompt 04) troca o formato do arquivo aprovado no Volume — `.xlsx` para `.csv` — sem tocar
no dado. Depois dela, o SQL enxerga tudo.

Sem Jobs, sem Lakeflow Pipelines, sem notebooks `.py`, sem orquestração — conforme
decidido em princípio. Os três arquivos rodam um a um, na frente da audiência.

> **Revisão:** esta decisão previa notebooks `.py` executados manualmente. O mecanismo
> mudou quando a limitação do `read_files` ficou clara — e um runner local simples é mais
> fácil de explicar numa live do que um notebook cuja execução ninguém vê.

## 6.14 — Deploy do App

O App é um **Databricks App**, deployado pela CLI:

```bash
databricks apps create --name data-intake-validator --profile <perfil>
databricks workspace import-dir apps /Workspace/Users/<usuário>/apps/data-intake-validator \
  --overwrite --profile <perfil>
databricks apps deploy data-intake-validator \
  --source-code-path /Workspace/Users/<usuário>/apps/data-intake-validator --profile <perfil>
```

O `--overwrite` no `import-dir` não é detalhe: sem ele, o redeploy **pula em silêncio** os
arquivos que já existem e o App continua rodando a versão antiga.

O App precisa do módulo de validação dentro da própria árvore de código que sobe para a
workspace, então `validator/` é **copiado** para `apps/validator/` no momento do deploy —
empacotamento, como um `.whl`. A fonte de verdade continua sendo `validator/`, na raiz.

**Fallback documentado:** se o recurso Databricks Apps não estiver disponível na workspace —
o que o ensaio decide cedo —, o mesmo `apps/app.py` roda localmente (`streamlit run
apps/app.py`, com `DATABRICKS_CONFIG_PROFILE` apontando o perfil), e o restante do fluxo não
muda.

> **Revisão:** esta decisão estava adiada — o deploy seria avaliado depois, conforme o
> ambiente. Foi avaliado: a CLI resolve, e o ensaio valida cedo se o recurso existe.

---

# Decisões surgidas ao escrever o contrato

Vieram do encontro entre o texto do projeto e os arquivos de teste concretos. Nenhuma
delas estava ambígua no `projeto.md` — todas apareceram quando foi preciso escrever a regra
que decide o veredito.

## 6.15 — `desconto médio` na Gold

**Média simples:**

```
desconto_medio = AVG(desconto)
```

Cada registro representa uma venda, então **não** usamos média ponderada por faturamento
nesta primeira versão.

## 6.16 — Unicidade de `id_venda`

A unicidade é validada **apenas dentro do próprio arquivo recebido**.

A validação **não** consulta a Bronze para verificar duplicidade entre arquivos nesta
primeira versão. Detecção de reprocessamento entre arquivos fica como evolução futura,
relacionada à estratégia de idempotência (ver 6.9).

---

## 6.17 — Coluna inesperada é bloqueante

Uma coluna além das 13 **rejeita** o arquivo. Não é aviso.

O §4.4 do `projeto.md` só pede "testar detecção de coluna não prevista", sem dizer o que
fazer com ela. Torná-la bloqueante é o que faz `vendas_coluna_extra.xlsx` virar
`FILE REJECTED`, e fecha a conta da demonstração: dois aprovados, três rejeitados, três
motivos distintos de rejeição — coluna obrigatória ausente, coluna inesperada e tipo
inválido.

Decorre do mesmo princípio do §6.2: **o contrato é fechado por definição.** Uma coluna nova
e legítima será rejeitada — comportamento pretendido, porque evoluir o contrato é uma
decisão explícita, não algo que o arquivo decide sozinho.

## 6.18 — Não existe veredito parcial

Todas as regras do contrato são bloqueantes. Não há problema que apenas avise. O veredito é
**do arquivo**, não da linha: um arquivo rejeitado não avança em parte, nem "só com as
linhas boas".

`vendas_tipo_invalido.xlsx` tem 5 linhas ruins em 1000 e é rejeitado por inteiro.

Aceitar as 995 linhas boas seria corrigir os dados silenciosamente — o que o §5 do projeto
e o §12 proíbem. Tratar as linhas boas é trabalho da Silver, **depois** que alguém corrigir
a origem.

> **Pergunta que vem ao vivo:** *"rejeitar mil linhas por causa de cinco não é rígido
> demais?"* Resposta: o contrato não decide o que é verdade, decide o que está conforme.
> Rejeitar é o que devolve o problema para quem pode corrigi-lo na fonte.

## 6.19 — Separador decimal é o ponto

O contrato usa ponto decimal. `1299.90` é número; `1.299,90` é **texto** e é rejeitado.

A rejeição não é por ser formato brasileiro — é por não ser um número. O contrato não
adivinha intenção: verifica se o valor tem o tipo que o schema declara.

> **Pergunta que vem ao vivo:** *"e o formato brasileiro?"* Esta é a resposta, e ela vale
> para `quantidade`, `valor_unitario` e `desconto` igualmente.

## 6.20 — Vazio é ausência de conteúdo

Célula vazia é bloqueante. Mas **vazio é ausência de conteúdo, não texto que parece
vazio**: uma célula com `"N/A"` está preenchida, com um texto que viola a regra de tipo.

Quem lê o arquivo não pode deixar a biblioteca reinterpretar. `pd.read_excel` converte
`"N/A"`, `"NA"` e similares em nulo por padrão — e com isso o diagnóstico passaria a
relatar "campo vazio" na linha 514 de `vendas_tipo_invalido.xlsx`, onde o arquivo diz
`"N/A"`. O validador descreveria um arquivo diferente do que recebeu, que é exatamente o
que este projeto existe para impedir.

**Leia com `keep_default_na=False`.** Verificado: desligar a inferência não altera nenhum
dtype numérico nos cinco arquivos.

## 6.21 — A receita de leitura: `keep_default_na=False` + `dtype=object`

A leitura do arquivo é o ponto onde o projeto inteiro pode ser sabotado em silêncio. Se a
biblioteca reinterpretar uma célula antes de o contrato ser aplicado, o diagnóstico passa a
descrever **outro arquivo**. A receita fixada é:

```python
pd.read_excel(fonte, sheet_name=0, keep_default_na=False, na_filter=False, dtype=object)
```

**O que cada flag sustenta — medido, não presumido:**

| Flag | O que ela impede | Evidência |
| --- | --- | --- |
| `keep_default_na=False` | `"N/A"` virar nulo | sem ela, a linha 514 de `vendas_tipo_invalido.xlsx` chega como `nan` e o diagnóstico diria "campo vazio" (decisão 6.20) |
| `dtype=object` | o pandas inferir tipos que o arquivo não tem | sem ela, os números chegam como `np.int64`/`np.float64` e as datas como `Timestamp` |
| `na_filter=False` | a detecção de nulo em geral | sobrepõe-se a `keep_default_na`; ver abaixo |

**Por que `dtype=object` não é detalhe.** Não é só estética de tipo. `isinstance(np.int64(1),
int)` é `False` — sem `dtype=object`, **todo inteiro do arquivo seria reportado como "tipo
inválido"**, e o validador reprovaria os dois arquivos que deveriam passar. É o tipo de erro
que não aparece em nenhum arquivo de teste pequeno e apareceria ao vivo. Com `dtype=object` a
célula chega como o openpyxl a leu: `int`, `float`, `str`, `datetime`.

**Correção de uma premissa anterior.** O planejamento registrou que `keep_default_na=False`
sozinho faria o pandas *stringificar* uma coluna numérica inteira ao encontrar uma célula
vazia (`[1, None, 3]` → `['1', '', '3']`). **Essa medição não se reproduziu.** Refiz o teste
com um arquivo sintético e o resultado foi `[10, '', 30]` — os inteiros continuam inteiros; só
a célula vazia vira texto vazio. O que o padrão do pandas faz de fato, sem nenhuma flag, é
outra coisa e também é ruim: a coluna sobe para `float64` para acomodar o `NaN`
(`[10.0, nan, 30.0]`), e o `"N/A"` vira nulo.

Nenhuma das duas versões muda a receita final — as duas apontam para ler sem reinterpretação.
A diferença importa para o *motivo* declarado, não para o código.

`na_filter=False` **fica**, embora a medição mostre que ela e `keep_default_na=False` produzem
o mesmo resultado neste caso. Ela nomeia a intenção de forma mais ampla — desligar a detecção
de nulo, não apenas a lista padrão — e o custo é uma palavra-chave. O comentário no código diz
isso, para que ninguém depois leia a linha e presuma que são três causas independentes.

---

# Decisões surgidas ao construir as camadas

Vieram quando o dado aprovado passou a ter destino: a Bronze precisava carimbar as linhas, e
a Gold precisava nomear o que agrega.

## 6.22 — Colunas de metadados e da Gold

O §8 recomenda três metadados técnicos e o §10 lista cinco campos de agregação — nenhum dos
dois dá nome de coluna. Fixado assim:

| Camada | Coluna | Papel |
| --- | --- | --- |
| Bronze | `data_ingestao` | timestamp da leitura (`current_timestamp()`) |
| Bronze | `arquivo_origem` | nome do arquivo do Volume que originou a linha |
| Bronze | `id_execucao` | id da execução da camada — o runner substitui `__ID_EXECUCAO__` |
| Gold | `quantidade_vendas` | contagem de linhas (`COUNT(*)`) — decisão 6.6 |
| Gold | `quantidade_total_vendida` | soma de `quantidade` — campo distinto da contagem (§10) |
| Gold | `faturamento_total` | faturamento **líquido**, com desconto — decisão 6.5 |
| Gold | `desconto_medio` | `AVG(desconto)` — decisão 6.15 |
| Gold | `ticket_medio` | líquido ÷ contagem de vendas — decisão 6.6 |

Os nomes seguem a convenção do projeto — pt-BR, `snake_case` — e derivam literalmente das
descrições do §8 e do §10: nenhum campo novo foi criado, só nomeado. As três colunas de
metadados acompanham as linhas da Bronze até a Silver, para a rastreabilidade não se perder
no caminho.

---

# A seguir

**Não há itens pendentes de ambiente.** As vinte e duas decisões estão fechadas.

A construção é a sequência de prompts da live — os oito arquivos de `docs/prompts/`, na
ordem:

1. criar o catálogo `lakehouse_validator`, os quatro schemas e o Volume `entrada` (prompt 00);
2. escrever `docs/contrato-de-dados.md` (prompt 01);
3. derivar a representação estruturada (6.4) e implementar o módulo de validação, sem
   Streamlit (§6) — `validator/` e `scripts/verificar_validator.py` (prompt 02);
4. construir o App sobre esse módulo (prompt 03);
5. converter os `.xlsx` do Volume em `.csv` — a ponte que o SQL exige (prompt 04);
6. escrever os três arquivos de camada (prompts 05 a 07, decisão 6.13).

**O contrato e o módulo de validação nascem ao vivo** — eles não existem no ponto de partida
do repositório. O gabarito dos dois não é publicado com este repositório: fica numa referência interna,
para comparar depois de cada ensaio.

O módulo de validação vai morar em **`validator/`, na raiz** — ao lado de `apps/` e
`ingestion/`. Assim a separação do §6 fica visível na própria árvore de pastas: `apps/`
apresenta, `validator/` decide, `ingestion/` transporta, `notebooks/` transforma.

Serão três arquivos, e a divisão é a decisão 6.4 tornada visível: `contrato.py` só
**declara** (as 13 colunas, os domínios, as faixas, as nove regras), `validador.py` só
**aplica**, e `__init__.py` é a única porta de entrada. Quem consome o módulo não precisa
saber que são dois arquivos.

> **Os passos que tocam a workspace dependem de autorização a cada vez** — criar o catálogo
> (00), criar e deployar o App (03), escrever no Volume (04) e criar as tabelas (05 a 07)
> não são ações de repositório. Cada prompt pede a confirmação antes de executar, e o
> perfil é sempre escolhido por quem está conduzindo.
