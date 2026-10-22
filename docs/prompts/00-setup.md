# Prompt 00 — O catálogo na workspace

> Cole este texto inteiro no Claude Code, dentro do repositório do projeto.

Este é o **prompt 00**, o primeiro da sequência que constrói o Data Intake Validator. Ele
não produz nenhum arquivo no repositório: ele cria a estrutura na **workspace Databricks**.

Altera algo fora do repositório — a workspace Databricks — e é o único passo da sequência
que pede confirmação antes de executar. Criar é barato; desfazer não é.

---

## Contexto

O projeto usa um catálogo dedicado, `lakehouse_validator`, com quatro schemas e um Volume.
Tudo que as camadas seguintes fizerem vai gravar dentro dele.

Antes de executar qualquer coisa, carregue a skill `databricks-core` e depois
`databricks-unity-catalog`, e siga o que elas dizem sobre os comandos.

---

## O que criar

| Recurso | Nome exato | Por quê |
| --- | --- | --- |
| Catálogo | `lakehouse_validator` | dedicado ao projeto — decisão 6.8 |
| Schema | `raw` | área de entrada; contém o Volume |
| Schema | `bronze` | dado recebido + metadados técnicos |
| Schema | `silver` | dado tipado e limpo |
| Schema | `gold` | agregações de consumo |
| Volume | `lakehouse_validator.raw.entrada` | onde o App deposita o arquivo aprovado |

O Volume fica em **`raw`**, e não em `bronze`: assim o arquivo e a tabela ficam em schemas
distintos, alinhado ao papel de cada camada. Ver decisão 6.7.

> **Dos seis recursos, cinco nascem pela CLI — o catálogo é a exceção.** Esta conta usa
> *Default Storage*, e a plataforma só cria catálogos assim pela interface: a API recusa as
> duas formas possíveis (armadilha 1). O catálogo é criado pela pessoa, em ~30 segundos no
> Catalog Explorer; a CLI cria os quatro schemas e o Volume.

---

## Antes de executar

**1. Escolha o perfil com o usuário.** Liste os perfis disponíveis com
`databricks auth profiles`, apresente todos com o host de cada um, e **pergunte qual usar**.
Nunca escolha sozinho, nem quando houver apenas um. Todos os comandos recebem
`--profile <nome>` explicitamente.

**2. Verifique se o catálogo já existe**, antes de tentar criá-lo:

```bash
databricks catalogs list --profile <perfil>
```

**3. Confirme com o usuário antes de criar.** Mostre exatamente o que será criado e
aguarde o "pode ir".

**3a. O catálogo, pela interface.** Explique a restrição antes de pedir os cliques:

1. **Catalog Explorer** → **Create catalog**;
2. **Catalog name:** `lakehouse_validator`;
3. **Catalog type:** Standard;
4. **Storage location:** **Default storage** — a opção que só aparece porque a conta usa
   Default Storage, e a razão de a CLI não conseguir criar este catálogo;
5. **Create**.

Aguarde a confirmação de que o catálogo existe antes de seguir.

**3b. O resto, pela CLI** — só depois de o catálogo existir:

```bash
databricks schemas create --json '{"name": "raw",    "catalog_name": "lakehouse_validator"}' --profile <perfil>
databricks schemas create --json '{"name": "bronze", "catalog_name": "lakehouse_validator"}' --profile <perfil>
databricks schemas create --json '{"name": "silver", "catalog_name": "lakehouse_validator"}' --profile <perfil>
databricks schemas create --json '{"name": "gold",   "catalog_name": "lakehouse_validator"}' --profile <perfil>
databricks volumes create --json '{"catalog_name": "lakehouse_validator", "schema_name": "raw", "name": "entrada", "volume_type": "MANAGED"}' --profile <perfil>
```

> Confirme a sintaxe de cada comando com `--help` antes de rodar. As duas formas funcionam —
> a posicional (`databricks schemas create raw lakehouse_validator`) e a `--json` — mas a
> ordem dos posicionais **muda de comando para comando**, então prefira `--json`, que não
> depende de ordem. Em nenhuma das duas existe `--catalog-name`.

---

## Armadilhas conhecidas

**1. O catálogo não nasce pela CLI nesta conta.** Ela usa *Default Storage*, e a plataforma
reserva a criação de catálogos assim à interface. Verificado no ensaio, com as duas
tentativas: `databricks catalogs create lakehouse_validator` responde *"Metastore storage
root URL does not exist. Default Storage is enabled in your account"*; e a variante com o
storage root da conta responde *"Please use the UI to create a catalog with Default
Storage"*. Não é sintaxe nem versão da CLI — é política da plataforma. Não insista: crie o
catálogo pela UI (passo 3a) e siga. E **não** aponte o storage root para o caminho de outro
catálogo: os que já existem no workspace são de outros projetos.

**2. `CREATE CATALOG` falha se o catálogo já existir — e isso é uma informação, não um
erro a contornar.** Se ele já existir, **pare e me avise**. Não rode `DROP CATALOG`, nem
`CASCADE`, nem tente recriar por cima. Apagar um catálogo não tem volta, e a decisão de
limpar a workspace é minha, não sua.

**3. Não reaproveite catálogo existente.** Os que já existem no workspace pertencem a outros
projetos. Usar qualquer um deles traria schemas alheios para dentro da demonstração.

**4. O SQL Warehouse fica STOPPED.** É serverless e sobe sozinho na primeira consulta, com
alguns segundos de latência. Se for preciso rodar SQL, avise que a primeira consulta é
lenta — não é travamento.

**5. Não crie tabela nenhuma.** Nem na Bronze, nem na Silver, nem na Gold. Este passo cria
apenas catálogo, schemas e o Volume. As tabelas nascem quando cada camada rodar.

---

## Não faça

- **não escolha o perfil automaticamente**, nem presuma qual é;
- **não execute nada sem confirmação** — este passo mexe na workspace, e desfazer não é barato;
- **não apague nada** — nem catálogo, nem schema, nem volume, nem tabela;
- **não crie tabelas** nem rode notebooks;
- **não escreva nada no repositório** neste passo.

---

## Critério de aceite

- [ ] o perfil foi escolhido por mim, e todo comando o recebeu explicitamente;
- [ ] `databricks catalogs list --profile <perfil>` mostra `lakehouse_validator`;
- [ ] `databricks schemas list lakehouse_validator --profile <perfil>` mostra os quatro:
      `raw`, `bronze`, `silver`, `gold` — ao lado de `default` e `information_schema`, que a
      Unity Catalog cria sozinha em todo catálogo novo. O aceite é os quatro estarem lá;
- [ ] `databricks volumes list lakehouse_validator raw --profile <perfil>` mostra `entrada`;
- [ ] nenhuma tabela foi criada em nenhum schema;
- [ ] nada foi escrito no repositório — `git status` continua limpo.

---

## Quando terminar

Me diga o que foi criado, cole a saída dos comandos de verificação, e **pare**. Não avance
para o contrato.

Se o catálogo já existir, **não faça nada**: me diga que ele existe e aguarde a minha
decisão.
