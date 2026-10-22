# Prompt 03 — O App

> Cole este texto inteiro no Claude Code, dentro do repositório do projeto.

Este é o **prompt 03** da sequência que constrói o Data Intake Validator. Ele produz o App
Streamlit que julga os arquivos e, quando aprovados, os deposita no Volume.

O módulo de validação nasceu no prompt 02 e **não muda neste passo** — o App apenas o
consome.

Este passo **altera a workspace**: cria o App e faz o deploy. Como todo passo que sai do
repositório, ele **pede a minha confirmação antes de executar**.

---

## Contexto

O App é a cara do projeto, mas é fino de propósito: toda a decisão sobre o arquivo mora em
`validator/`. O App **só renderiza o diagnóstico** e, quando o veredito é aprovado, grava o
arquivo no Volume. A separação do §6 do projeto é um requisito, não uma preferência —
nenhuma regra de validação pode aparecer no `app.py`.

Carregue as skills `databricks-core` e `databricks-apps-python` antes de escrever, e siga o
que elas dizem sobre `app.yaml`, deploy e permissões. A skill `databricks-apps`
(`references/other-frameworks.md` §8) tem os três ajustes obrigatórios do Streamlit que
estão nas armadilhas abaixo — sem eles, o App sobe e devolve **502**.

---

## O que fazer agora

Quatro arquivos dentro de `apps/` e o deploy:

| Arquivo | Papel |
| --- | --- |
| `apps/app.py` | a interface Streamlit |
| `apps/app.yaml` | a configuração do Databricks App |
| `apps/requirements.txt` | as dependências que o runtime precisa instalar |
| `apps/validator/` | **cópia** do módulo da raiz — empacotamento do deploy |

### A cópia do módulo

Copie `validator/__init__.py`, `validator/contrato.py` e `validator/validador.py` para
`apps/validator/`. É empacotamento, como um `.whl`: o App precisa do módulo dentro da
própria árvore de código que sobe para a workspace.

**A fonte de verdade continua sendo `validator/`, na raiz.** A cópia nunca é editada — se
uma regra mudar, muda na raiz e a cópia é refeita.

### O comportamento do `app.py`, em ordem

1. **Upload** — `st.file_uploader` aceitando `.xlsx`.
2. **Validação** — `validar(bytes_do_arquivo)`; o módulo aceita `bytes`, caminho ou
   file-like. Nenhum recálculo, nenhuma regra nova.
3. **Diagnóstico** — renderize o `Diagnostico` **usando as propriedades dele**:
   - veredito em destaque: `READY FOR INGESTION` (verde) ou `FILE REJECTED` (vermelho);
   - linhas analisadas e total de problemas;
   - resumo por regra e colunas afetadas;
   - amostra das ocorrências, **sempre ao lado do total verdadeiro** — ela é limitada a 20
     por apresentação, e o arquivo foi analisado por inteiro;
   - sugestões, quando houver, com a ressalva de que nada foi alterado.
4. **Aprovação** — o botão **"Aprovar e enviar para o Lakehouse"** aparece **somente** com
   o arquivo aprovado. Ao clicar, grave o arquivo em
   `/Volumes/lakehouse_validator/raw/entrada/` com o nome original, via
   `w.files.upload(file_path=..., contents=io.BytesIO(arquivo.getvalue()), overwrite=True)`
   — **`contents` é um fluxo, não `bytes`** (armadilha 9).

**Rejeitado não tem botão.** O arquivo rejeitado não toca o Volume, e nada é corrigido —
nem nome de coluna, nem tipo, nem valor.

### O `app.yaml`

Use este conteúdo como base — os três ajustes de Streamlit são obrigatórios (adaptado de
`databricks-apps/references/other-frameworks.md` §8):

```yaml
command:
  - streamlit
  - run
  - app.py
  - --server.port
  - "${DATABRICKS_APP_PORT:-8000}"
  - --server.address
  - "0.0.0.0"
env:
  - name: STREAMLIT_SERVER_ENABLE_CORS
    value: "false"
  - name: STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION
    value: "false"
  - name: VOLUME_ENTRADA
    valueFrom: volume
```

O recurso `volume` é o Volume `lakehouse_validator.raw.entrada`, adicionado na interface do
App (Configure → **+ Add resource** → Volume) com permissão de **leitura e escrita**. É
isso que dá ao service principal do App o direito de gravar — sem o recurso, o upload falha
com `PERMISSION_DENIED`. No código, leia o caminho com
`os.getenv("VOLUME_ENTRADA", "/Volumes/lakehouse_validator/raw/entrada")`.

### O deploy

Obtenha o seu usuário da workspace com `databricks current-user me --profile <perfil>` — o
caminho do código na workspace é `/Workspace/Users/<seu-usuário>/apps/data-intake-validator`.

**A infraestrutura é pré-criada, antes da live** (decisão de §2 do guia). Ela não muda com o
código, e é onde estão as falhas de permissão e de build lento. Na ordem, porque a ordem importa:

1. `databricks apps create` (bloco abaixo, primeira linha);
2. **recurso de Volume na UI**: Configure → + Add resource → Volume → "Can read and write".
   Isto vem **antes** do primeiro deploy: o `app.yaml` declara `valueFrom: volume`, e sem o
   recurso o deploy falha ou sobe sem a variável `VOLUME_ENTRADA`;
3. os grants do service principal em `lakehouse_validator` e `raw` (`USE CATALOG`, `USE SCHEMA`,
   `WRITE VOLUME`);
4. um deploy de teste, para medir o tempo do build e confirmar o runtime (pandas no Python do App).

**Ao vivo**, sobra só o `import-dir` e o `apps deploy` de atualização, com o código que o Claude
acabou de gerar.

```bash
databricks apps create --name data-intake-validator \
  --json '{"description": "Valida planilhas de vendas contra o contrato antes da ingestão"}' \
  --profile <perfil>

databricks workspace mkdirs /Workspace/Users/<seu-usuário>/apps/data-intake-validator --profile <perfil>
databricks workspace import-dir apps /Workspace/Users/<seu-usuário>/apps/data-intake-validator --overwrite --profile <perfil>

databricks apps deploy data-intake-validator \
  --source-code-path /Workspace/Users/<seu-usuário>/apps/data-intake-validator --profile <perfil>

databricks apps get data-intake-validator --profile <perfil>
databricks apps logs data-intake-validator --profile <perfil>
```

**O App roda o que está no workspace, não o que está na sua pasta.** Antes de cada deploy,
confirme que o `import-dir` acima de fato reenviou o código: o `app.py` do workspace
precisa conter a linha `contents=io.BytesIO(arquivo.getvalue())`.

```bash
databricks workspace export /Workspace/Users/<seu-usuário>/apps/data-intake-validator/app.py --profile <perfil> | grep -n "BytesIO"
```

Tem que aparecer uma linha. Se não aparecer, o `grep` volta vazio: a linha é
`contents=arquivo.getvalue()` (bytes, sem `BytesIO`), e o workspace está com a versão antiga.
Rode o `import-dir` de novo antes do deploy.

**No Windows (Git Bash):** o shell converte caminhos que começam com `/`, e o CLI recusa o
resultado. Prefixe os comandos com `/Workspace/...` por `MSYS_NO_PATHCONV=1`, por exemplo
`MSYS_NO_PATHCONV=1 databricks apps deploy ...`.

**Pare antes do deploy e me mostre o que será criado** — nome, caminho e comandos. Só
execute depois do meu "pode ir".

---

## De onde vem cada regra

| Assunto | Origem |
| --- | --- |
| Funcionalidades do App (upload, diagnóstico, veredito) | `docs/projeto.md` §5 |
| `READY FOR INGESTION` / `FILE REJECTED`; nunca corrigir | §5, decisão 6.18 |
| Sugestões explícitas, decisão do usuário | §5, decisão 6.12 |
| O App não concentra a validação; não depende de decidir | §6 |
| Somente aprovado entra; o Volume é a porta | §7, decisões 6.7 e 6.8 |
| Elementos do diagnóstico e amostra de 20 | `docs/contrato-de-dados.md` §6, decisão 6.11 |
| Proibição de corrigir dados silenciosamente | §12 |

Nada aqui é para inventar. O que o App mostra é exatamente o que o `Diagnostico` já
calcula.

---

## Armadilhas conhecidas

**1. Os três ajustes de Streamlit, ou 502.** O proxy do Databricks Apps serve o App de uma
origem diferente da workspace, e a proteção CORS/XSRF do Streamlit derruba a conexão. Os
dois `env` do `app.yaml` acima **precisam** existir, e a porta **precisa** ser
`${DATABRICKS_APP_PORT:-8000}` com `--server.address 0.0.0.0`. Porta errada é a causa nº 1
de 502.

**2. `@st.cache_resource` no cliente.** O Streamlit reexecuta o script inteiro a cada
interação. Um `WorkspaceClient()` criado a cada render esgota as conexões e o App congela
por minutos. Crie-o uma vez, numa função decorada.

**3. O `import-dir` sem `--overwrite` pula em silêncio os arquivos que já existem.** No
primeiro deploy não faz diferença; em qualquer redeploy, o App continua rodando o código
velho sem avisar. Sempre com `--overwrite`.

**4. `__pycache__` não vai para o deploy.** Remova `apps/validator/__pycache__` (e
qualquer `.pyc`) antes do `import-dir`.

**5. O primeiro deploy demora, e 502 transitório no início é esperado.** O App leva alguns
minutos para instalar dependências e subir. `abrir → 502 → recarregar` faz parte. Se
persistir, `databricks apps logs data-intake-validator`.

**6. A cópia do módulo não se edita.** Se o App julgar errado, o defeito está na raiz —
corrija lá e recopie. Editar `apps/validator/` cria duas versões da mesma regra, que é o
que o projeto inteiro existe para evitar.

**7. O service principal do App não é você.** Ele recebe `DATABRICKS_CLIENT_ID` e
`DATABRICKS_CLIENT_SECRET` injetados no runtime, e o `WorkspaceClient()` detecta sozinho —
não leia nem passe essas variáveis manualmente. As permissões dele vêm do recurso de
Volume.

**8. O App não valida nada por conta própria.** Se você sentir vontade de escrever
`if coluna not in ...` no `app.py`, pare: isso é `validator/`.

**9. `w.files.upload` quer um fluxo, não `bytes`.** O `WorkspaceClient.files` é o `FilesExt`
do SDK, e o `upload` dele chama `contents.seekable()` para medir o arquivo antes de escolher
entre um PUT único e um upload multipart. Com `contents=arquivo.getvalue()` — que é `bytes` —
o App passa pela validação inteira, mostra `READY FOR INGESTION`, e só **no clique do botão**
responde `Não foi possível gravar no Volume: 'bytes' object has no attribute 'seekable'`. Passe
`io.BytesIO(arquivo.getvalue())`: um `BytesIO` sobre os mesmos bytes, seekable, e o `.xlsx` de
72 KB segue por um PUT único. A pegadinha é que o `FilesAPI` cru, de
`databricks.sdk.service.files`, **aceitaria** `bytes` — quem recusa é o mixin que o
`WorkspaceClient` devolve.

---

## Não faça

- **não escreva regra de validação no App** — o §6 do projeto é explícito: o App consome o
  resultado, não decide;
- **não altere o módulo `validator/`** nem edite a cópia — o módulo está fechado desde o
  prompt 02;
- **não corrija dados** em nenhum caminho, nem ofereça "aplicar sugestão" — sugestão se
  lê, não se executa sozinha;
- **não crie tabela nenhuma** — este passo só grava arquivo no Volume, e só o aprovado;
- **não execute o deploy sem a minha confirmação**;
- **não avance para a ponte** — é o prompt 04.

### Se o Databricks Apps não estiver disponível

Se `databricks apps create` falhar porque o recurso não está habilitado nesta workspace,
**pare e me avise**. O plano B é rodar o **mesmo App localmente**:
`DATABRICKS_CONFIG_PROFILE=<perfil> streamlit run apps/app.py` (em Git Bash; no PowerShell,
`$env:DATABRICKS_CONFIG_PROFILE = "<perfil>"; streamlit run apps/app.py`). O SDK lê o perfil
da variável de ambiente e o resto do fluxo não muda. A decisão é minha.

---

## Critério de aceite

- [ ] `grep -i "import streamlit" validator/` continua vazio — a separação se manteve;
- [ ] `apps/` tem os quatro itens: `app.py`, `app.yaml`, `requirements.txt`, `validator/`;
- [ ] o `app.yaml` tem os dois `env` de CORS/XSRF e a porta `${DATABRICKS_APP_PORT:-8000}`;
- [ ] `databricks apps get data-intake-validator --profile <perfil>` mostra o App ativo;
- [ ] no App, **na interface**, os cinco arquivos de `data/output/` produzem:
      `vendas_valido.xlsx` e `vendas_data_texto.xlsx` → `READY FOR INGESTION`;
      `vendas_coluna_ausente.xlsx` → `FILE REJECTED` com a sugestão `dt_venda → data_venda`;
      `vendas_tipo_invalido.xlsx` → `FILE REJECTED`, 5 problemas de tipo;
      `vendas_coluna_extra.xlsx` → `FILE REJECTED`, 1 problema;
- [ ] aprovar `vendas_valido.xlsx` e `vendas_data_texto.xlsx` grava os dois no Volume, e
      `databricks fs ls dbfs:/Volumes/lakehouse_validator/raw/entrada --profile <perfil>`
      mostra os dois (o prefixo `dbfs:` é obrigatório no CLI);
- [ ] os três rejeitados **não** aparecem no Volume;
- [ ] nenhum arquivo do repositório fora de `apps/` foi alterado.

---

## Quando terminar

Me diga o que criou, cole a saída de `apps get`, e **pare**. Não avance para a ponte.

Se algum comportamento do App não estiver definido em `projeto.md` nem em `decisoes.md`,
**não decida sozinho**: me apresente o ponto e a sua recomendação, e eu decido.
