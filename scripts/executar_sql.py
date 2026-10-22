"""
Executa UM statement SQL no SQL Warehouse da workspace Databricks.

Uso:
    python scripts/executar_sql.py notebooks/01_bronze.sql --profile <perfil>
    python scripts/executar_sql.py --sql "SELECT COUNT(*) FROM lakehouse_validator.bronze.vendas" --profile <perfil>

O arquivo .sql contém um único statement: este runner não divide o texto por ";".
A substring __ID_EXECUCAO__ é trocada por um id único a cada execução — é assim
que as camadas carimbam as linhas que ingerem (decisão 6.22).

O perfil é sempre escolhido por quem roda: --profile é obrigatório e o script
nunca presume um. Sai com código 0 em sucesso e 1 em falha.
"""

from __future__ import annotations

import argparse
import sys
import time
import uuid
from pathlib import Path

from databricks.sdk import WorkspaceClient

# O warehouse serverless fica STOPPED fora de uso e sobe sozinho na primeira
# consulta — os tempos abaixo são a paciência do script com essa subida.
TIMEOUT_SUBIDA = 180  # segundos até desistir de esperar o warehouse subir
TIMEOUT_STATEMENT = 300  # segundos até desistir de esperar o statement terminar
INTERVALO_SUBIDA = 5
INTERVALO_STATEMENT = 2
NOME_WAREHOUSE = "Serverless Starter Warehouse"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def _texto(valor):
    """O SDK devolve enums; para comparar e imprimir, queremos o texto."""
    return getattr(valor, "value", None) or str(valor)


def escolher_warehouse(w):
    """Só o warehouse pelo nome exato. Nunca escolhe outro: o perfil também não é presumido."""
    for armazem in w.warehouses.list():
        if armazem.name == NOME_WAREHOUSE:
            return armazem
    return None


def subir_warehouse(w, armazem):
    """Garante o warehouse RUNNING. Devolve o id, ou None se não subir no timeout."""
    if _texto(armazem.state) == "RUNNING":
        return armazem.id
    print("warehouse parado — subindo (serverless, alguns segundos)...")
    try:
        w.warehouses.start(id=armazem.id)
    except Exception as erro:  # o start é disparado; quem decide é o polling abaixo
        print(f"  aviso: start devolveu {erro!r}")
    inicio = time.monotonic()
    while time.monotonic() - inicio < TIMEOUT_SUBIDA:
        estado = _texto(w.warehouses.get(id=armazem.id).state)
        if estado == "RUNNING":
            print(f"  warehouse no ar ({time.monotonic() - inicio:.0f}s).")
            return armazem.id
        time.sleep(INTERVALO_SUBIDA)
    return None


def executar(w, warehouse_id, sql):
    """Dispara o statement e espera. Devolve a resposta, ou None se estourar o tempo."""
    resposta = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql,
        wait_timeout="30s",
    )
    inicio = time.monotonic()
    while _texto(resposta.status.state) in ("PENDING", "RUNNING"):
        if time.monotonic() - inicio > TIMEOUT_STATEMENT:
            print(
                f"erro: o statement não terminou em {TIMEOUT_STATEMENT}s "
                f"(id {resposta.statement_id})."
            )
            return None
        time.sleep(INTERVALO_STATEMENT)
        resposta = w.statement_execution.get_statement(resposta.statement_id)
    return resposta


def imprimir_resultado(resposta):
    """Imprime as linhas do resultado de forma legível, alinhada em colunas."""
    manifest = resposta.manifest
    colunas = (
        [coluna.name for coluna in manifest.schema.columns]
        if manifest and manifest.schema
        else []
    )
    linhas = list(resposta.result.data_array or []) if resposta.result else []
    if not colunas:
        print("(comando aplicado; sem resultado tabular)")
        return
    texto = [[("NULL" if valor is None else str(valor)) for valor in linha] for linha in linhas]
    larguras = [max([len(nome)] + [len(linha[i]) for linha in texto]) for i, nome in enumerate(colunas)]
    cabecalho = "  ".join(nome.ljust(larguras[i]) for i, nome in enumerate(colunas))
    print(cabecalho)
    print("-" * len(cabecalho))
    for linha in texto:
        print("  ".join(linha[i].ljust(larguras[i]) for i in range(len(colunas))))
    plural = "s" if len(texto) != 1 else ""
    print(f"({len(texto)} linha{plural})")
    if manifest and getattr(manifest, "truncated", False):
        print("(resultado truncado pelo serviço — refine a consulta)")


def main():
    parser = argparse.ArgumentParser(
        description="Executa UM statement SQL no warehouse da workspace (Databricks).",
    )
    parser.add_argument("arquivo", nargs="?", help="arquivo .sql com um único statement")
    parser.add_argument("--sql", help="statement avulso, para consultas rápidas")
    parser.add_argument(
        "--profile",
        required=True,
        help="perfil do CLI a usar (obrigatório — o script nunca escolhe sozinho)",
    )
    parser.add_argument(
        "--id-execucao",
        help="id desta execução (padrão: um novo a cada chamada; substitui __ID_EXECUCAO__)",
    )
    args = parser.parse_args()

    if bool(args.arquivo) == bool(args.sql):
        parser.error("informe um arquivo .sql OU --sql — exatamente um dos dois")

    if args.arquivo:
        caminho = Path(args.arquivo)
        if not caminho.is_file():
            print(f"erro: arquivo não encontrado: {caminho}")
            return 1
        # utf-8-sig: um .sql salvo com BOM (comum no Windows) não pode deixar ﻿ no statement.
        texto = caminho.read_text(encoding="utf-8-sig").strip()
        if not texto:
            print(f"erro: {caminho} está vazio")
            return 1
        fonte = str(caminho)
    else:
        texto = args.sql.strip()
        fonte = "--sql"

    id_execucao = args.id_execucao or uuid.uuid4().hex[:12]
    usa_id = "__ID_EXECUCAO__" in texto
    sql = texto.replace("__ID_EXECUCAO__", id_execucao)

    print(f"perfil:    {args.profile}")
    print(f"fonte:     {fonte}")
    if usa_id:
        print(f"execução:  {id_execucao}")

    w = WorkspaceClient(profile=args.profile)

    armazem = escolher_warehouse(w)
    if armazem is None:
        disponiveis = ", ".join(a.name for a in w.warehouses.list()) or "(nenhum)"
        print(f"erro: o warehouse '{NOME_WAREHOUSE}' não existe nesta workspace.")
        print(f"warehouses visíveis: {disponiveis}")
        print("Nenhum outro é usado no lugar — ajuste NOME_WAREHOUSE se o nome mudou.")
        return 1
    print(f"warehouse: {armazem.name} ({armazem.id}) — estado {_texto(armazem.state)}")

    warehouse_id = subir_warehouse(w, armazem)
    if warehouse_id is None:
        print(
            f"erro: o warehouse não ficou RUNNING em {TIMEOUT_SUBIDA}s. "
            "Rode de novo — a subida já foi disparada."
        )
        return 1

    resposta = executar(w, warehouse_id, sql)
    if resposta is None:
        return 1

    estado = _texto(resposta.status.state)
    if estado != "SUCCEEDED":
        erro = getattr(resposta.status, "error", None)
        mensagem = getattr(erro, "message", None) or "(sem detalhe)"
        print(f"FALHOU ({estado}): {mensagem}")
        return 1

    imprimir_resultado(resposta)
    return 0


if __name__ == "__main__":
    sys.exit(main())
