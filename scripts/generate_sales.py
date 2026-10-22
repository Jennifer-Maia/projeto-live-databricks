"""
Gera um dataset sintético de vendas para o projeto Data Intake Validator.

Saída:
- vendas_valido.xlsx
- vendas_coluna_ausente.xlsx
- vendas_tipo_invalido.xlsx
- vendas_coluna_extra.xlsx
- vendas_data_texto.xlsx

Uso:
    python generate_sales.py
"""

from pathlib import Path
import pandas as pd
import numpy as np
import random

SEED = 42
N_RECORDS = 1000
# Ancorado na raiz do projeto, não no diretório de execução: o script pode ser
# rodado de qualquer lugar sem espalhar uma pasta "output" pelo caminho.
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "output"

# O restante deste arquivo reproduz exatamente a geração usada nos arquivos
# fornecidos com o projeto.
# Altere N_RECORDS para gerar outro volume mantendo o mesmo modelo.

random.seed(SEED)
np.random.seed(SEED)

products = [
    ("Notebook Pro 14", "Eletrônicos", 4200),
    ("Notebook Air 13", "Eletrônicos", 3500),
    ("Monitor 27", "Eletrônicos", 1450),
    ("Monitor 24", "Eletrônicos", 980),
    ("Teclado Mecânico", "Periféricos", 320),
    ("Mouse Sem Fio", "Periféricos", 150),
    ("Headset Pro", "Periféricos", 420),
    ("Webcam Full HD", "Periféricos", 290),
    ("Cadeira Ergonômica", "Móveis", 1250),
    ("Mesa Escritório", "Móveis", 890),
    ("Suporte Notebook", "Acessórios", 180),
    ("Hub USB-C", "Acessórios", 230),
    ("Mochila Executiva", "Acessórios", 310),
    ("HD Externo 2TB", "Armazenamento", 620),
    ("SSD 1TB", "Armazenamento", 540),
]

cities = [
    ("Curitiba", "PR"), ("Londrina", "PR"), ("Maringá", "PR"),
    ("São Paulo", "SP"), ("Campinas", "SP"), ("Santos", "SP"),
    ("Rio de Janeiro", "RJ"), ("Niterói", "RJ"),
    ("Belo Horizonte", "MG"), ("Uberlândia", "MG"),
    ("Florianópolis", "SC"), ("Joinville", "SC"),
    ("Porto Alegre", "RS"), ("Caxias do Sul", "RS"),
    ("Brasília", "DF"), ("Goiânia", "GO"),
    ("Salvador", "BA"), ("Recife", "PE"),
]

names = [
    "Ana Silva", "João Santos", "Maria Oliveira", "Carlos Souza",
    "Fernanda Lima", "Rafael Costa", "Juliana Almeida", "Bruno Martins",
    "Camila Rodrigues", "Lucas Pereira", "Mariana Rocha", "Gabriel Gomes",
    "Beatriz Carvalho", "Pedro Ferreira", "Larissa Mendes", "Felipe Barbosa",
    "Isabela Nunes", "André Ribeiro", "Letícia Teixeira", "Diego Moreira",
    "Amanda Castro", "Thiago Vieira", "Renata Dias", "Marcelo Cardoso",
    "Paula Araújo", "Vinícius Monteiro", "Clara Freitas", "Gustavo Ramos",
    "Natália Correia", "Eduardo Martins"
]
sellers = ["Ana", "Bruno", "Camila", "Diego", "Fernanda", "Gabriel", "Juliana", "Lucas", "Mariana", "Rafael"]
channels = ["Online", "Loja Física", "Marketplace"]

customer_ids = list(range(5001, 5201))
customer_names = {cid: random.choice(names) for cid in customer_ids}

start = pd.Timestamp("2026-01-01")
end = pd.Timestamp("2026-12-31")
rows = []

for i in range(N_RECORDS):
    product, category, base_price = random.choice(products)
    city, state = random.choice(cities)
    customer_id = random.choice(customer_ids)
    qty = random.choices([1,2,3,4,5,6,8,10], weights=[22,24,20,14,8,5,4,3])[0]
    price = round(base_price * random.uniform(0.88, 1.12), 2)
    discount = round(random.choice([0, 0, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20]), 2)
    date = start + pd.to_timedelta(random.randint(0, (end-start).days), unit="D")

    rows.append({
        "id_venda": 100001 + i,
        "data_venda": date,
        "id_cliente": customer_id,
        "cliente": customer_names[customer_id],
        "cidade": city,
        "estado": state,
        "produto": product,
        "categoria": category,
        "quantidade": qty,
        "valor_unitario": price,
        "desconto": discount,
        "vendedor": random.choice(sellers),
        "canal_venda": random.choice(channels),
    })

df = pd.DataFrame(rows)
df["data_venda"] = pd.to_datetime(df["data_venda"])
df["id_venda"] = df["id_venda"].astype("int64")
df["id_cliente"] = df["id_cliente"].astype("int64")
df["quantidade"] = df["quantidade"].astype("int64")
df["valor_unitario"] = df["valor_unitario"].round(2)
df["desconto"] = df["desconto"].round(2)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

df.to_excel(OUTPUT_DIR / "vendas_valido.xlsx", index=False)

df.rename(columns={"data_venda": "dt_venda"}).to_excel(
    OUTPUT_DIR / "vendas_coluna_ausente.xlsx", index=False
)

# O astype(object) é obrigatório no pandas 3: ele não faz mais upcast automático
# de coluna numérica ao receber texto, e a atribuição abaixo levanta TypeError.
# O upcast é exatamente o defeito que este arquivo precisa carregar — por isso é
# explícito, e não um acidente da versão da biblioteca.
invalid = df.copy()
invalid["quantidade"] = invalid["quantidade"].astype(object)
invalid.loc[[17, 143, 512], "quantidade"] = ["três", "dez", "N/A"]
invalid["valor_unitario"] = invalid["valor_unitario"].astype(object)
invalid.loc[[88, 376], "valor_unitario"] = ["1.299,90", "valor_invalido"]
invalid.to_excel(OUTPUT_DIR / "vendas_tipo_invalido.xlsx", index=False)

extra = df.copy()
extra["observacao_interna"] = [
    random.choice(["", "Cliente VIP", "Revisar cadastro", "Pedido prioritário"])
    for _ in range(N_RECORDS)
]
extra.to_excel(OUTPUT_DIR / "vendas_coluna_extra.xlsx", index=False)

# Único arquivo que exercita a segunda forma de data do contrato (§4.3): aqui
# data_venda é gravada como texto em yyyy-MM-dd, não como data nativa do Excel.
# Ele deve ser APROVADO — o contrato aceita as duas formas.
#
# Fica por último de propósito: não consome nenhum número aleatório, então não
# desloca a sequência que gera os quatro arquivos anteriores.
texto = df.copy()
texto["data_venda"] = texto["data_venda"].dt.strftime("%Y-%m-%d")
texto.to_excel(OUTPUT_DIR / "vendas_data_texto.xlsx", index=False)

print(f"Arquivos gerados em: {OUTPUT_DIR.resolve()}")
