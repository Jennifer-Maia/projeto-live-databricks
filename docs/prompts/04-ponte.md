# Prompt 04 — A ponte

> Cole este texto inteiro no Claude Code, dentro do repositório do projeto.

Este é o **prompt 04** da sequência que constrói o Data Intake Validator. Ele produz um
script local que converte os `.xlsx` aprovados do Volume em `.csv`, no mesmo Volume — a
ponte entre o que o App deposita e o que o SQL consegue ler.

O App nasceu no prompt 03 e **não muda neste passo**. Este passo **escreve no Volume**, que
está na workspace: como todo passo que sai do repositório, ele pede a minha confirmação
antes de executar.

---

## Contexto

O SQL do Databricks lê csv, json, parquet, orc, avro, text e binário — **não lê Excel**. A
validação do projeto roda em Python, então o `.xlsx` não é problema até aqui; a partir da
Bronze, é. A conversão precisa acontecer em algum lugar, e o lugar honesto é este: um passo
explícito, visível na live, que troca o **formato** do arquivo e nada mais.

**Conversão de formato, nunca de dado.** O script não limpa, não tipa, não padroniza —
tudo isso é trabalho da Silver (decisão 6.10). Ele lê as células como o openpyxl as
entregou e as grava num csv.

---

## O que fazer agora

Um arquivo: `ingestion/converter_para_csv.py`. Nada além dele.

O script roda **na minha máquina** (não é um App, não é um notebook), recebe `--profile`
obrigatório e usa o `WorkspaceClient` do SDK para falar com o Volume.

### O que ele faz, em ordem

1. **Lista** o conteúdo de `/Volumes/lakehouse_validator/raw/entrada/`
   (`w.files.list_directory_contents`) e separa os que terminam em `.xlsx`.
2. **Para cada um**: baixa (`w.files.download`), lê em memória com **a receita de leitura
   já fixada** (decisão 6.21 — não reinvente):

   ```python
   pd.read_excel(fonte, sheet_name=0, keep_default_na=False, na_filter=False, dtype=object)
   ```

3. **Grava** o csv (`to_csv`, utf-8, sem coluna de índice) e **sobe** para o mesmo Volume,
   com o mesmo nome e a extensão `.csv` (`w.files.upload(..., overwrite=True)`).
4. **Imprime** o que fez, por arquivo: nome, linhas, destino.

Os `.xlsx` **nunca são removidos** — o Volume guarda o que foi aprovado, que é a evidência
da ingestão. O script é idempotente: rodar de novo sobrescreve os `.csv`.

### Se o Volume estiver vazio

Não é erro do script — é um aviso: "nenhum `.xlsx` no Volume; aprove um arquivo no App
antes de rodar a ponte". Sai com código 0, porque a ausência não é falha da conversão.

---

## De onde vem cada regra

| Assunto | Origem |
| --- | --- |
| O Volume de entrada e seu caminho | decisão 6.7 |
| Só arquivo aprovado chega ao Volume | `docs/projeto.md` §7 |
| A receita de leitura, com as três flags | decisão 6.21 |
| Converter não é limpar: a Silver é quem transforma | decisões 6.3 e 6.10 |
| Fronteira: a Bronze lê do Volume | decisões 6.7 e 6.8 |

Nada aqui é para inventar. A receita de leitura é a mesma do validador — as três flags
existem por medição, não por estilo.

---

## Armadilhas conhecidas

**1. `keep_default_na=False` e `na_filter=False` juntas, e `dtype=object`.** Sem elas, o
`"N/A"` vira nulo e os números viram `np.int64` — o csv carregaria um arquivo diferente do
aprovado. É a decisão 6.21 inteira; não "simplifique" a chamada.

**2. O caminho do Volume no CLI tem prefixo, no SDK não.** `databricks fs ls` exige
`dbfs:/Volumes/...`; o `w.files.*` e o SQL usam `/Volumes/...`. Trocar os dois é o erro
mais fácil de cometer aqui.

**3. `w.files.download` devolve um objeto com `.contents`** — leia os bytes de lá
(`resposta.contents.read()`) antes de passar para o pandas.

**4. O CSV do `vendas_valido.xlsx` mostra a data como `2026-01-15 00:00:00`.** Isso é a
forma datetime do contrato (decisão 6.3), não uma alteração do dado — e é justamente o
contraste que a Silver demonstra ao converter as duas formas. Não "conserte" isso aqui.

**5. Console do Windows.** O script imprime nomes de arquivo e acentos: comece com
`sys.stdout.reconfigure(encoding="utf-8")`, como os outros scripts do projeto.

**6. Nenhum `--profile` presumido.** O argumento é obrigatório no argparse; se eu não
passar, o script para e pede. Nunca escolha sozinho.

---

## Não faça

- **não valide nada** — o arquivo que está no Volume já foi aprovado; a ponte não reabre o
  veredito;
- **não limpe nem transforme dado** — nem `trim`, nem cast, nem troca de valor;
- **não apague nada** — os `.xlsx` ficam onde estão;
- **não escreva fora do Volume** — nada de gravar csv no repositório;
- **não avance para a Bronze** — é o prompt 05.

---

## Critério de aceite

Com os dois aprovados já no Volume (do prompt 03):

- [ ] `python ingestion/converter_para_csv.py --profile <perfil>` roda sem erro e imprime,
      por arquivo, nome e linhas;
- [ ] `databricks fs ls dbfs:/Volumes/lakehouse_validator/raw/entrada --profile <perfil>`
      mostra os `.csv` **ao lado** dos `.xlsx` originais;
- [ ] os dois csv têm 1000 linhas de dados cada (mais o cabeçalho);
- [ ] rodar o script uma segunda vez produz o mesmo resultado — idempotente;
- [ ] nenhum arquivo do repositório foi alterado além de `ingestion/`.

---

## Quando terminar

Me diga o que criou, cole a saída do script, e **pare**. Não avance para a Bronze.

Se algum ponto da conversão não estiver definido em `projeto.md` nem em `decisoes.md`,
**não decida sozinho**: me apresente o ponto e a sua recomendação, e eu decido.
