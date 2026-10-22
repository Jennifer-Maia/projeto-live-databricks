# Prompt 01 — O contrato de dados

> Cole este texto inteiro no Claude Code, dentro do repositório do projeto.

Este é o **prompt 01** da sequência que constrói o Data Intake Validator. Ele produz **um
único arquivo**: `docs/contrato-de-dados.md`. Nada além disso.

O catálogo `lakehouse_validator` já foi criado no prompt 00, com os quatro schemas e o
Volume `entrada`. **Não crie nem altere nada na workspace neste passo.**

---

## Contexto

O projeto simula uma empresa que recebe planilhas Excel de várias áreas e precisa garantir
que elas respeitem um contrato antes de entrar no Lakehouse.

A especificação completa está em `docs/projeto.md`. **Leia antes de escrever** — é a fonte de
verdade sobre o que deve existir.

As decisões já tomadas sobre os pontos que a especificação deixou em aberto estão em
`docs/decisoes.md`. **Leia também, e trate tudo como decidido.** Não reabra nenhuma decisão
e não peça confirmação sobre o que já está lá.

> **A cena das decisões já aconteceu**, no começo da live, antes do prompt 00: os pontos em
> aberto foram levantados e decididos em voz alta, e é isso que está no `decisoes.md`. Este
> prompt não a repete — se algum ponto voltar à tona, a resposta é "já decidido, está
> registrado".

---

## O que fazer agora

Escrever `docs/contrato-de-dados.md`: a versão legível do contrato — a fonte de verdade para
quem produz o arquivo e para quem o valida.

O documento deve ter estas nove seções, nesta ordem:

| Seção | Conteúdo |
| --- | --- |
| 1. O arquivo | formato, aba, cabeçalho, linhas |
| 2. Schema | as 13 colunas, com tipo, obrigatoriedade e descrição |
| 3. O que o contrato não cobre | o que fica fora de escopo, para não virar dúvida |
| 4. Regras de validação | colunas obrigatórias, inesperadas, tipos, valores, vazios, unicidade, datas |
| 5. Veredito | `READY FOR INGESTION` e `FILE REJECTED` — o que decide cada um |
| 6. Diagnóstico | os elementos que o usuário recebe ao ter o arquivo rejeitado — e os nove nomes de tipo de problema |
| 7. Sugestões | o que o sistema pode sugerir, e o que ele nunca faz |
| 8. Fronteira com a Silver | quem converte o quê |
| 9. Derivações a jusante | as fórmulas da Gold, registradas no mesmo lugar |

O documento é escrito em português, como o resto do projeto.

**Não confunda as nove seções com os nove tipos de problema.** São duas contagens
diferentes que caem no mesmo número por coincidência: o documento tem nove seções, e o §6
nomeia nove tipos de problema.

### Os nove nomes de tipo de problema

O §6 precisa nomeá-los, e os nomes são **exatos** — este é o vocabulário fechado do resumo
do diagnóstico, e nenhum outro nome aparece nele:

```
arquivo ilegível · arquivo sem linhas de dados · coluna obrigatória ausente
coluna inesperada · campo vazio · tipo inválido · data inválida
valor inválido · id_venda duplicado
```

A ordem **não é alfabética**: vai da falha mais estrutural para a mais pontual, e é a ordem
em que o resumo apresenta os tipos. São os mesmos nomes que o prompt 02 declara em
`validator/contrato.py` — os dois não podem divergir.

**São nove tipos, não as doze verificações do §4.** O §4 numera **verificações** (R1–R12);
o §6 nomeia **tipos de problema**, e a correspondência é de muitos para um — R5 a R10 geram
todas `valor inválido`, e R3 e R4 geram `data inválida` e `tipo inválido`.

---

## De onde vem cada regra

**Não invente nenhum valor de domínio.** Todos estão nos dados ou nas decisões:

| Assunto | Origem |
| --- | --- |
| As 13 colunas e seus tipos | `docs/projeto.md` §3 |
| `desconto` é fração de `0` a `1` — `0.05` é 5% | decisão 6.1 |
| Domínios de `categoria`, `canal_venda` e `estado` | decisão 6.2 |
| `data_venda`: data nativa do Excel ou texto `yyyy-MM-dd` | decisão 6.3 |
| Faturamento líquido, ticket médio, desconto médio | decisões 6.5, 6.6 e 6.15 |
| Catálogo, schemas e nomes de tabela | decisões 6.7 e 6.8 |
| Formato do diagnóstico e tamanho da amostra | decisão 6.11 |
| Sugestões limitadas a nomes de coluna | decisão 6.12 |
| Unicidade de `id_venda` dentro do arquivo | decisão 6.16 |
| Coluna inesperada bloqueia; não existe veredito parcial; decimal é ponto; vazio é ausência de conteúdo | decisões 6.17 a 6.20 |
| Os nove nomes de tipo de problema do §6, e a ordem do resumo | prompt 02 — é ele que declara o vocabulário em `validator/contrato.py` |

**Os valores de `categoria` e `canal_venda` saem de `scripts/generate_sales.py`** — leia o
arquivo. Não os deduza do que parece razoável. `estado` são as 27 UFs oficiais brasileiras,
não apenas as que aparecem nos dados de teste.

---

## Armadilhas conhecidas

**1. `valor_unitario` inválido é `"1.299,90"` — de propósito.** Não é erro de digitação do
gerador. O contrato usa ponto decimal, e `1.299,90` é rejeitado por ser **texto**, não por
ser formato brasileiro. Isso precisa estar escrito no documento, com essas palavras, senão a
pergunta volta.

**2. `pd.read_excel` converte `"N/A"` em nulo.** O texto `"N/A"` está gravado na linha 514 de
`vendas_tipo_invalido.xlsx`. Lido com o padrão do pandas, ele vira `nan`, e o diagnóstico
passaria a dizer "campo vazio" onde o arquivo diz `"N/A"` — descrevendo um arquivo diferente
do que foi recebido. As decisões 6.20 e 6.21 tratam disso: a leitura usa
`keep_default_na=False`, `na_filter=False` e `dtype=object`.

**3. `vendas_coluna_ausente.xlsx` produz dois problemas, não um.** `data_venda` ausente **e**
`dt_venda` inesperada. O diagnóstico precisa reportar os dois e ainda assim sugerir a
correspondência.

**4. Os cinco arquivos vêm do mesmo dataset base.** Qualquer diferença entre eles é
exatamente o defeito que aquele arquivo demonstra, nunca um dado diferente. Preserve essa
propriedade se mexer no gerador.

**5. O padrão do pandas é o de `vendas_tipo_invalido.xlsx`.** Ele é o único arquivo em que o
pandas não consegue inferir `int64`/`float64` e devolve `object`. Isso é o defeito, não um
problema de leitura.

---

## Não faça

- **não implemente o validador** nem a representação estruturada do contrato — é o prompt 02;
- **não crie nem altere nada na workspace** — catálogo, schemas e volume já existem;
- **não adicione regra** que não esteja em `docs/projeto.md` ou `docs/decisoes.md`;
- **não valide verdade de negócio** (se o cliente existe, se o preço é o vigente, se a data
  faz sentido no calendário) — o contrato valida conformidade, não verdade;
- **não escreva código** neste passo.

---

## Critério de aceite

- [ ] `docs/contrato-de-dados.md` existe e tem as nove seções, nesta ordem;
- [ ] as 13 colunas aparecem com tipo e obrigatoriedade, e todas são obrigatórias;
- [ ] `desconto` está descrito como fração de `0` a `1`, com `0.05` = 5% e a escala 0–100
      explicitamente descartada;
- [ ] `categoria` traz os cinco valores e `canal_venda` os três — os mesmos do gerador;
- [ ] `estado` traz as 27 UFs, não apenas as 10 que aparecem nos dados;
- [ ] `data_venda` documenta as duas formas aceitas e diz que a conversão é da Silver;
- [ ] está escrito que coluna inesperada bloqueia e que não existe veredito parcial;
- [ ] está escrito que `1.299,90` é rejeitado por ser texto, e que a leitura usa
      `keep_default_na=False`;
- [ ] a amostra de erros está fixada em 20, com o total real sempre visível ao lado;
- [ ] o §6 nomeia os **nove tipos de problema**, com os nomes exatos e na ordem do
      vocabulário — nenhum outro nome aparece no resumo;
- [ ] nenhum nome de catálogo, tabela ou caminho aparece como se já existisse;
- [ ] nenhum valor de domínio foi inventado — todos rastreiam para `projeto.md`,
      `decisoes.md` ou `scripts/generate_sales.py`.

---

## Quando terminar

Me diga o que criou, em poucas linhas, e **pare**. Não avance para o próximo passo.

Se algum ponto do contrato não estiver decidido nem em `projeto.md` nem em `decisoes.md`,
**não decida sozinho**: me apresente o ponto e a sua recomendação, e eu decido.
