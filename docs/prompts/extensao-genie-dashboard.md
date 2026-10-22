# Extensão — Genie Agent e dashboard sobre a Gold

> Cole este texto inteiro no Claude Code, dentro do repositório do projeto.

Este **não é um prompt da live**: ele não entra na sequência 00–07 nem no tempo de 75 minutos.
É o próximo passo do projeto, para quando alguém pedir uma demonstração de consumo — ou para
o caso de a live ganhar um anexo. Ele cria dois objetos **na workspace**, por isso pede a
minha confirmação antes de criar qualquer coisa.

---

## Contexto

A Gold, `lakehouse_validator.gold.vendas_por_produto`, existe desde o prompt 07 e tem as
cinco métricas do §10: `quantidade_vendas`, `quantidade_total_vendida`, `faturamento_total`
(líquido, decisão 6.5), `desconto_medio` (média simples, decisão 6.15) e `ticket_medio`
(decisão 6.6). Esta extensão só **consome** essa tabela. Ela não cria métrica nova, não
altera a Silver nem a Gold, e não cria tabela.

O §15 de `docs/projeto.md` lista "perguntas em linguagem natural sobre a Gold" e
"dashboards" como escopo futuro. Este passo é exatamente essa extensão — por isso fica
fora da primeira versão e fora da live.

Carregue as skills `databricks-core`, `databricks-genie-agents` e `databricks-aibi-dashboards`
e siga o que elas dizem sobre criação, teste e publicação.

---

## O que fazer

Dois objetos, nesta ordem.

### 1. Genie Agent

- **Fonte:** só `lakehouse_validator.gold.vendas_por_produto`. Nenhuma outra tabela.
- **Nome:** `Vendas por produto`.
- **Descrição e instruções em português**, com as fórmulas das decisões: faturamento é
  líquido (já com o desconto aplicado); ticket médio é faturamento dividido por quantidade de
  vendas; desconto médio é média simples, não ponderada.
- **Perguntas de teste** — o agente precisa respondê-las corretamente antes de eu considerar
  o passo concluído:
  1. Qual produto teve o maior faturamento?
  2. Qual é o ticket médio da categoria Móveis?
  3. Qual produto tem o maior desconto médio?

### 2. Dashboard AI/BI

Um dashboard, com:

- **Quatro indicadores (KPIs):** faturamento total (soma de `faturamento_total`), vendas
  (soma de `quantidade_vendas`), ticket médio geral (faturamento total ÷ vendas) e desconto
  médio geral.
- **Um gráfico de barras:** faturamento total por produto, ordenado do maior para o menor.
- **Uma tabela:** as sete colunas da Gold.

**Teste cada SQL pela CLI antes de publicar** — é o que a skill `databricks-aibi-dashboards`
exige.

---

## Antes de executar

- **O perfil é escolhido por mim, nunca presumido.** Pergunte com a escolha de opções, com os
  três perfis do `.databrickscfg`.
- **Mostre-me o que será criado** — o nome do Genie Agent, o nome do dashboard, as perguntas
  de teste e os SQL do dashboard — e aguarde a minha confirmação.

---

## Não faça

- **não crie tabela, view, Job, pipeline ou notebook;**
- **não altere a Silver nem a Gold;**
- **não crie métrica além das cinco do §10;**
- **não altere o App nem a ponte;**
- **não publique o dashboard para ninguém além de mim** — deixe-o privado, sem compartilhar.

---

## Critério de aceite

- [ ] o Genie Agent responde corretamente às três perguntas de teste, e eu vejo as respostas;
- [ ] o dashboard publicado mostra os quatro KPIs, o gráfico e a tabela, sem erro de SQL;
- [ ] os valores do dashboard batem com `SELECT SUM(faturamento_total) FROM
      lakehouse_validator.gold.vendas_por_produto`;
- [ ] nenhum objeto foi criado além do Genie Agent e do dashboard.

---

## Quando terminar

Me diga o que criou, cole as respostas do agente e o link do dashboard, e **pare**.

Se algum ponto não estiver definido em `docs/projeto.md` nem em `docs/decisoes.md`,
**não decida sozinho**: me apresente o ponto e a sua recomendação, e eu decido.
