"""
Checklist de preparação da live do Data Intake Validator.

Roda ANTES de cada ensaio e no dia da live. Confere duas coisas:

1. o repositório está no ponto de partida — os artefatos que nascem ao vivo
   (contrato, módulo de validação, verificador) ainda NÃO existem;
2. o ambiente responde — dependências instaladas, CLI autenticado no perfil
   escolhido, catálogo ainda não criado, warehouse visível.

Uso:
    python scripts/verificar_estado_live.py --profile <perfil>

O perfil é sempre escolhido por quem roda. Sai com código 0 se tudo estiver
[OK] e 1 se qualquer item falhar.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# O que a live constrói: estes arquivos NÃO podem existir no ponto de partida.
# Eles nascem nos prompts indicados, e a referência construída não faz parte deste repositório.
ARTEFATOS_QUE_NASCEM_AO_VIVO = [
    ("docs/contrato-de-dados.md", "prompt 01"),
    ("validator/contrato.py", "prompt 02"),
    ("validator/validador.py", "prompt 02"),
    ("validator/__init__.py", "prompt 02"),
    ("scripts/verificar_validator.py", "prompt 02"),
]

ARQUIVOS_DE_TESTE = [
    "vendas_valido.xlsx",
    "vendas_data_texto.xlsx",
    "vendas_coluna_ausente.xlsx",
    "vendas_tipo_invalido.xlsx",
    "vendas_coluna_extra.xlsx",
]

CATALOGO = "lakehouse_validator"
WAREHOUSE_PREFERIDO = "Serverless Starter Warehouse"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def rodar(comando):
    """Roda um comando na raiz do projeto. Devolve (código, stdout, stderr)."""
    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=RAIZ,
        )
        return resultado.returncode, resultado.stdout or "", resultado.stderr or ""
    except FileNotFoundError:
        return None, "", f"comando não encontrado: {comando[0]}"


def verificar_git():
    codigo, _, erro = rodar(["git", "rev-parse", "--is-inside-work-tree"])
    if codigo != 0:
        return False, f"não é um repositório git ({erro.strip() or 'git indisponível'})"
    _, branch, _ = rodar(["git", "branch", "--show-current"])
    if branch.strip() != "main":
        return False, f"branch atual: {branch.strip() or '(vazia)'} — esperado: main"
    _, status, _ = rodar(["git", "status", "--porcelain"])
    if status.strip():
        return False, f"há alterações não commitadas:\n{status.strip()}"
    return True, "branch main, sem alterações pendentes"


def verificar_ausentes():
    encontrados = [
        (caminho, prompt)
        for caminho, prompt in ARTEFATOS_QUE_NASCEM_AO_VIVO
        if (RAIZ / caminho).exists()
    ]
    if encontrados:
        linhas = "\n".join(f"{caminho} — nasce no {prompt}" for caminho, prompt in encontrados)
        return False, f"estes arquivos não deveriam existir ainda:\n{linhas}"
    return True, f"{len(ARTEFATOS_QUE_NASCEM_AO_VIVO)} artefatos ausentes (como esperado)"


def verificar_copia_do_app():
    """apps/validator/ é cópia de validator/ (o deploy empacota o módulo dentro do App).

    Duas cópias que divergem = a regra declarada em dois lugares. Só confere quando
    as duas existem — no ponto de partida nenhuma delas existe.
    """
    origem, copia = RAIZ / "validator", RAIZ / "apps" / "validator"
    # Diretório vazio não conta: no ponto de partida apps/validator/ pode existir sem arquivos.
    tem_origem = bool(list(origem.glob("*.py"))) if origem.is_dir() else False
    tem_copia = bool(list(copia.glob("*.py"))) if copia.is_dir() else False
    if not tem_origem and not tem_copia:
        return True, "validator/ ainda não existe (nada a comparar)"
    if tem_origem != tem_copia:
        return False, "só uma das duas tem módulo: validator/ e apps/validator/ devem coexistir"
    divergentes = [
        arquivo.name
        for arquivo in sorted(origem.glob("*.py"))
        if not (copia / arquivo.name).exists()
        or (copia / arquivo.name).read_bytes() != arquivo.read_bytes()
    ]
    if divergentes:
        return False, f"apps/validator/ diverge de validator/: {', '.join(divergentes)} — copie de novo"
    return True, "apps/validator/ idêntico a validator/"


def verificar_xlsx():
    faltando = [nome for nome in ARQUIVOS_DE_TESTE if not (RAIZ / "data" / "output" / nome).exists()]
    if faltando:
        return False, f"faltando em data/output/: {', '.join(faltando)}"
    return True, f"os {len(ARQUIVOS_DE_TESTE)} arquivos de teste estão em data/output/"


def verificar_pandas():
    try:
        import pandas  # noqa: PLC0415 — import tardio: só interessa aqui

        return True, f"pandas {pandas.__version__}"
    except Exception as erro:
        return False, f"pandas não importável: {erro}"


def verificar_cli(perfil):
    codigo, saida, erro = rodar(["databricks", "current-user", "me", "--profile", perfil])
    if codigo is None:
        return False, erro
    if codigo != 0:
        return False, f"`databricks current-user me --profile {perfil}` falhou:\n{erro.strip()}"
    try:
        usuario = json.loads(saida).get("userName", saida.strip())
    except json.JSONDecodeError:
        usuario = saida.strip()
    return True, f"autenticado como {usuario}"


def verificar_catalogo(perfil):
    codigo, saida, erro = rodar(["databricks", "catalogs", "list", "--profile", perfil, "--output", "json"])
    if codigo is None:
        return False, erro
    if codigo != 0:
        return False, f"não consegui listar catálogos:\n{erro.strip()}"
    try:
        catalogs = json.loads(saida)
    except json.JSONDecodeError:
        return False, "a lista de catálogos não veio em JSON — confira a versão do CLI"
    nomes = {catalogo.get("name") for catalogo in catalogs}
    if CATALOGO in nomes:
        return False, (
            f"o catálogo {CATALOGO} já existe — rode o reset antes de ensaiar:\n"
            f"DROP CATALOG {CATALOGO} CASCADE (procedimento de reset; não tem volta)"
        )
    return True, f"catálogo {CATALOGO} ainda não existe (como esperado)"


def verificar_warehouse(perfil):
    try:
        from databricks.sdk import WorkspaceClient  # noqa: PLC0415 — import tardio

        w = WorkspaceClient(profile=perfil)
        armazens = list(w.warehouses.list())
    except Exception as erro:
        return False, f"o SDK não respondeu com o perfil {perfil}: {erro}"
    if not armazens:
        return False, "nenhum SQL Warehouse encontrado na workspace"
    descricao = "; ".join(
        f"{a.name} ({getattr(a.state, 'value', a.state)})" for a in armazens
    )
    if not any(a.name == WAREHOUSE_PREFERIDO and getattr(a.state, "value", "") == "RUNNING" for a in armazens):
        return True, f"{descricao}\n(o preferido não está RUNNING — o runner sobe na primeira consulta; aquecer antes da live)"
    return True, descricao


def main():
    parser = argparse.ArgumentParser(
        description="Checklist de preparação da live: repositório no ponto de partida + ambiente.",
    )
    parser.add_argument(
        "--profile",
        required=True,
        help="perfil do CLI a verificar (obrigatório — o script nunca escolhe sozinho)",
    )
    args = parser.parse_args()

    verificacoes = [
        ("git no ponto de partida", verificar_git),
        ("artefatos que nascem ao vivo ausentes", verificar_ausentes),
        ("cópia do módulo no App idêntica", verificar_copia_do_app),
        ("arquivos de teste presentes", verificar_xlsx),
        ("dependências Python", verificar_pandas),
        ("CLI autenticado", lambda: verificar_cli(args.profile)),
        ("catálogo ainda não criado", lambda: verificar_catalogo(args.profile)),
        ("warehouse visível", lambda: verificar_warehouse(args.profile)),
    ]

    falhas = 0
    for nome, verificar in verificacoes:
        ok, detalhe = verificar()
        print(f"{'[OK]    ' if ok else '[FALHOU]'} {nome}")
        for linha in (detalhe or "").splitlines():
            print(f"         {linha}")
        if not ok:
            falhas += 1

    print()
    if falhas:
        print(f"{falhas} item(ns) com falha — resolva antes de ensaiar.")
        return 1
    print("Tudo pronto para ensaiar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
