# Prompt 02 — O módulo de validação

> Cole este texto inteiro no Claude Code, dentro do repositório do projeto.

Este é o **prompt 02** da sequência que constrói o Data Intake Validator. Ele produz o
módulo que decide se um arquivo respeita o contrato, e um verificador que prova o
resultado.

O catálogo `lakehouse_validator` foi criado no prompt 00 e o contrato foi escrito no
prompt 01. **Não crie nem altere nada na workspace neste passo** — aqui só se escreve
Python.

---

## Contexto

O contrato está em `docs/contrato-de-dados.md`. **Leia antes de escrever** — é o que o
módulo implementa. As decisões que originaram cada regra estão em `docs/decisoes.md`:
leia também, e trate tudo como decidido.

O requisito central da arquitetura é que **a validação não pode depender do Streamlit**.
Ela é Python puro, importável por qualquer mecanismo de ingestão; o App, no prompt 03,
apenas consome o resultado.

---

## O que fazer agora

Quatro arquivos. Nenhum outro.

| Arquivo | Papel |
| --- | --- |
| `validator/contrato.py` | **só declara** — colunas, tipos, domínios, faixas, as nove regras. Zero lógica |
| `validator/validador.py` | **só aplica** — lê o arquivo, percorre as células, monta o diagnóstico |
| `validator/__init__.py` | a única porta de entrada. Exporte `validar`, `Diagnostico`, `Problema`, `Sugestao` |
| `scripts/verificar_validator.py` | prova que funciona, contra os cinco arquivos de `data/output/` |

A separação entre declarar e aplicar é deliberada: é o que permite explicar o projeto
mostrando dois arquivos, um que se lê como o contrato e outro que se lê como o motor.
Mantenha `contrato.py` sem nenhuma função de decisão.

### O que o diagnóstico precisa ter

Um `Diagnostico` com veredito, linhas analisadas, total de problemas, colunas afetadas,
resumo por regra, amostra limitada a **20** ocorrências e sugestões. O limite de 20 é de
**apresentação**: o arquivo é analisado por inteiro e o total reportado é sempre o total
verdadeiro.

As nove regras, com estes nomes exatos:

```
arquivo ilegível · arquivo sem linhas de dados · coluna obrigatória ausente
coluna inesperada · campo vazio · tipo inválido · data inválida
valor inválido · id_venda duplicado
```

**No máximo um problema por célula.** A precedência é vazio → tipo/data → valor. Uma
célula vazia não é também "tipo inválido": reportá-la duas vezes infla o total e sugere
dois defeitos onde há um.

---

## De onde vem cada regra

Nada aqui é para inventar. Tudo rastreia para um documento:

| Assunto | Origem |
| --- | --- |
| As 13 colunas, tipos e obrigatoriedade | `docs/contrato-de-dados.md` §2 |
| Veredito e a ausência de veredito parcial | §5, decisão 6.18 |
| As seis regras de validação | §4 |
| Domínios de `estado`, `categoria` e `canal_venda` | §4.5, decisão 6.2 |
| Faixas numéricas | §4.5 |
| Duas formas de data | §4.3, decisão 6.3 |
| Elementos e limite do diagnóstico | §6, decisão 6.11 |
| Sugestões | §7, decisão 6.12 |
| Unicidade de `id_venda` dentro do arquivo | §4.7, decisão 6.16 |
| Separador decimal | §2, decisão 6.19 |

**Os valores de `categoria` e `canal_venda` saem de `scripts/generate_sales.py`.** Leia o
arquivo. Não os deduza do que parece razoável. `estado` são as 27 UFs oficiais.

---

## Armadilhas conhecidas

Todas foram medidas neste projeto. Nenhuma é hipotética.

**1. `isinstance(np.int64(1), int)` é `False`.** Esta é a que quebra a demonstração. Se o
arquivo for lido sem `dtype=object`, a inferência do pandas entrega `np.int64` e
`np.float64`, e um validador que confie em `isinstance(valor, int)` reporta **todo
inteiro do arquivo** como tipo inválido — inclusive nos dois arquivos que deveriam ser
aprovados. Leia com `keep_default_na=False, na_filter=False, dtype=object`, e mesmo assim
escreva as verificações numéricas com `numbers.Integral` e `numbers.Real`.

**2. Sem `keep_default_na=False`, o `"N/A"` vira nulo.** Ele está gravado na linha 514 de
`vendas_tipo_invalido.xlsx`. Convertido em `nan`, o diagnóstico passa a dizer "campo
vazio" onde o arquivo diz `"N/A"` — descrevendo um arquivo diferente do que foi recebido.
A linha 514 do diagnóstico precisa mostrar `"N/A"`, nunca `(vazio)`.

**3. `desconto = 0` é válido, e `quantidade = 0` não é.** As faixas não são uniformes:
`quantidade` e `valor_unitario` são estritamente maiores que zero, mas `desconto` **inclui**
o zero — uma venda sem desconto é o caso mais comum do dataset. Tratar as três igualmente
reprova todo arquivo real. Declare a inclusividade, não a presuma.

**4. O `bool` é subclasse de `int` em Python.** `isinstance(True, int)` é `True`. Sem uma
guarda explícita, `True` passa como o número 1.

**5. Um limiar de similaridade não separa os casos de sugestão.** Medições nos nomes reais:

```
dt_venda -> data_venda   0.8889   deve sugerir
clientes -> cliente      0.9333   NÃO deve sugerir
```

O falso positivo é **mais parecido** que o acerto — nenhum valor de corte separa os dois.
Some ao limiar a condição de que o nome no arquivo não pode ser mais longo que o esperado:
`dt_venda` é uma abreviação, `clientes` é outra palavra. Emparelhe 1:1, do maior ratio
para o menor, e ordene por (ratio, nome, nome) para o resultado ser determinístico.

**6. A linha do Excel não é o índice do DataFrame.** A linha 1 é o cabeçalho, então o
índice `i` corresponde à linha `i + 2`. O `"N/A"` que o gerador escreve no índice 512 é a
**linha 514** — e é esse número que a pessoa vê ao abrir o arquivo.

**7. Coluna inesperada não se valida célula a célula.** O contrato não define regra para
ela. Varrer as células de `observacao_interna` produz centenas de "campo vazio" num
arquivo cujo defeito é só ter uma coluna a mais — e o diagnóstico deixa de apontar a
causa.

**8. `"1.299,90"` é rejeitado por ser texto, não por ser brasileiro.** Não é erro de
digitação do gerador.

---

## Não faça

- **não importe Streamlit** — é o requisito central da arquitetura; o módulo precisa
  rodar sem o App;
- **não corrija dados**, nem normalize caixa, nem apara espaços antes de comparar. `"sp"`
  e `" SP"` são valores fora do domínio; padronizar é trabalho da Silver (decisão 6.10);
- **não crie nem altere nada na workspace** — nem catálogo, nem tabela, nem Volume;
- **não valide verdade de negócio** (se o cliente existe, se o preço é o vigente) — o
  contrato valida conformidade, não verdade;
- **não use biblioteca de teste** — o verificador é um script simples, com casos
  declarados e saída legível. O projeto é para ser explicado, e um framework esconderia
  o que está acontecendo;
- **não avance para o App** — é o prompt 03.

---

## Critério de aceite

Rode `python scripts/verificar_validator.py` e confirme, caso a caso:

- [ ] `vendas_valido.xlsx` → `READY FOR INGESTION`, 1000 linhas, zero problemas;
- [ ] `vendas_data_texto.xlsx` → `READY FOR INGESTION` — o contrato aceita as duas formas
      de data, e este arquivo prova isso;
- [ ] `vendas_coluna_ausente.xlsx` → `FILE REJECTED`, **exatamente 2** problemas (coluna
      `data_venda` ausente + coluna `dt_venda` inesperada) e **1 sugestão**
      `dt_venda → data_venda`;
- [ ] `vendas_tipo_invalido.xlsx` → `FILE REJECTED`, **exatamente 5** problemas de tipo,
      nas linhas **19, 90, 145, 378 e 514**, com a linha 514 mostrando `"N/A"`;
- [ ] `vendas_coluna_extra.xlsx` → `FILE REJECTED`, **exatamente 1** problema;
- [ ] `grep -i "import streamlit" validator/` não retorna nada;
- [ ] o validador aceita caminho, `bytes` e objeto de arquivo, com o mesmo resultado;
- [ ] nenhuma célula gera dois problemas;
- [ ] duas execuções no mesmo arquivo produzem diagnósticos idênticos;
- [ ] `python scripts/verificar_validator.py <arquivo>` imprime o diagnóstico completo e
      sai com código 0 para aprovado e 1 para rejeitado.

O verificador deve cobrir também o que os cinco arquivos **não** exercitam: célula vazia
numa coluna numérica (só ela é reportada, o resto da coluna continua válido), `id_venda`
repetido, arquivo só com cabeçalho, linhas vazias no fim, `desconto = 0` aprovado,
`desconto = 5` reprovado, `estado = "sp"` reprovado, `"14/03/2026"` reprovado,
`"2026-02-30"` reprovado, bytes que não são planilha, e `"clientes"` no lugar de
`"cliente"` **sem** sugestão.

---

## Quando terminar

Me diga o que criou, cole a saída do verificador, e **pare**. Não avance para o App.

Se alguma regra do contrato se mostrar ambígua na hora de implementar, **não decida
sozinho**: me apresente o ponto e a sua recomendação, e eu decido.
