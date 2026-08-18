#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera as visoes do projeto a partir de ESTADO.csv.

ESTADO.csv e a FONTE UNICA do estado do projeto. Este script le aquele arquivo e
escreve as visoes derivadas, no repositorio e no vault. As visoes NAO SAO EDITADAS
A MAO — toda alteracao de estado se faz mudando uma celula do CSV e rodando isto.

    python scripts/gerar_visoes.py
    python scripts/gerar_visoes.py --check   # so valida, nao escreve

Por que existe: estado reafirmado em prosa em varios documentos diverge na primeira
vez que alguem atualiza so um. Projecao gerada nao diverge; copia mantida a mao, sim.

Ajuste as quatro constantes marcadas abaixo ao copiar para um projeto novo.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import defaultdict, OrderedDict
from datetime import date, datetime
from pathlib import Path

# --- AJUSTE ESTAS QUATRO AO COPIAR PARA UM PROJETO NOVO --------------------
PROJETO = "Cyanki"
# Id do item que representa a entrega final. Tudo na cadeia de `depende_de` que
# leva ate ele bloqueia o objetivo. Deixe None se o projeto nao tiver alvo unico.
# Cyanki nao tem entrega unica: o backlog e uma lista de UCs independentes.
ALVO = None
# O prefixo `0. ` e proposital: faz o resumo ficar em primeiro na pasta do
# projeto no Obsidian, que ordena por nome.
NOME_NOTA_VAULT = f"0. Resumo {PROJETO}.md"
# So usado quando a nota ainda nao existe no vault; depois disso ela e procurada.
# Projeto pessoal de estudo, entao Pessoal/Estudos e nao Trabalho/CGOD.
DESTINO_INICIAL = ("Pessoal", "Estudos")
# --------------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / "ESTADO.csv"

VAULT_PADRAO = Path.home() / "OneDrive - mtegovbr" / "00. vault"
IGNORAR_NO_VAULT = {"_claude", ".obsidian", ".trash"}

# Nao e ordem alfabetica de proposito: e a ordem em que se olha um quadro.
# "Descartado" fecha a lista: e item que saiu do produto por decisao, nao por
# entrega. Sem esse estado a unica saida seria apagar a linha, e ai o motivo de
# ter saido some junto — que e exatamente o que o CSV existe para impedir.
ORDEM_ESTADO = ["A fazer", "Em andamento", "Revisao", "Bloqueado", "Concluido", "Descartado"]
ABERTOS = {"A fazer", "Em andamento", "Revisao", "Bloqueado"}

COLUNAS = [
    "id", "titulo", "frente", "estado", "dono", "dono_nomeado",
    "depende_de", "estimativa", "evidencia", "data_conferido",
    "proximo_movimento", "bloqueia_objetivo",
]

DIAS_ATE_ENVELHECER = 90

CABECALHO = (
    "<!-- GERADO POR scripts/gerar_visoes.py A PARTIR DE ESTADO.csv.\n"
    "     NAO EDITE ESTE ARQUIVO A MAO — a edicao se perde na proxima geracao.\n"
    "     Para mudar o estado de um item, mude a celula em ESTADO.csv. -->\n\n"
)


def carregar() -> list[dict]:
    if not FONTE.exists():
        sys.exit(f"ERRO: {FONTE} nao encontrado.")
    with FONTE.open(encoding="utf-8-sig", newline="") as fh:
        itens = list(csv.DictReader(fh))
    if not itens:
        sys.exit("ERRO: ESTADO.csv esta vazio.")
    faltando = set(COLUNAS) - {"bloqueia_objetivo"} - set(itens[0].keys())
    if faltando:
        sys.exit(f"ERRO: colunas ausentes em ESTADO.csv: {sorted(faltando)}")
    return itens


def deps(item: dict) -> list[str]:
    """Separador e ESPACO, para nao brigar com a virgula do CSV."""
    return [d for d in (item.get("depende_de") or "").split() if d]


def ler_data(texto: str):
    """Aceita AAAA-MM-DD e DD/MM/AAAA; devolve None se nao for data.

    Projeto antigo escreve DD/MM/AAAA. Rejeitar isso so obrigaria a converter o CSV
    inteiro antes de adotar o gerador; aqui a data e normalizada para ISO na
    regravacao, entao o formato converge sozinho na primeira execucao.
    """
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    return None


def conferir(itens: list[dict]) -> tuple[list[str], dict[str, list[str]]]:
    """Erros bloqueiam a geracao. Avisos saem marcados na propria visao."""
    erros: list[str] = []
    avisos: dict[str, list[str]] = {}
    hoje = date.today()
    vistos: set[str] = set()

    for n, item in enumerate(itens, start=2):
        ident = (item.get("id") or "").strip()
        if not ident:
            erros.append(f"linha {n}: sem id")
            continue
        if ident in vistos:
            erros.append(f"id duplicado: {ident}")
        vistos.add(ident)

        if item.get("estado") not in ORDEM_ESTADO:
            erros.append(f"{ident}: estado desconhecido '{item.get('estado')}'")
        # Regra 1: nenhuma afirmacao sem o que a comprova.
        if not (item.get("evidencia") or "").strip():
            erros.append(f"{ident}: sem evidencia — nenhum item entra sem apontar o que o comprova")
        # Aviso, nao erro: item aberto pode legitimamente esperar terceiro ou decisao.
        # O que nao pode e a espera ficar invisivel.
        if item.get("estado") in ABERTOS and not (item.get("proximo_movimento") or "").strip():
            avisos.setdefault(ident, []).append("aberto sem proximo movimento")

        # Regra 3: data de conferencia, nao de escrita.
        conferido = (item.get("data_conferido") or "").strip()
        if not conferido:
            avisos.setdefault(ident, []).append("nunca conferido")
        else:
            quando = ler_data(conferido)
            if quando is None:
                erros.append(f"{ident}: data_conferido '{conferido}' nao e data (use AAAA-MM-DD ou DD/MM/AAAA)")
            else:
                item["data_conferido"] = quando.isoformat()  # normaliza na regravacao
                if quando > hoje:
                    erros.append(f"{ident}: data_conferido no futuro ({conferido})")
                elif (hoje - quando).days > DIAS_ATE_ENVELHECER:
                    avisos.setdefault(ident, []).append(f"conferido ha {(hoje - quando).days} dias")

    por_id = {i["id"]: i for i in itens if i.get("id")}
    for item in itens:
        ident = (item.get("id") or "").strip()
        if not ident:
            continue
        for d in deps(item):
            if d not in vistos:
                erros.append(f"{ident}: depende de '{d}', que nao existe")
        # A conferencia que motivou o padrao: item liberado com dependencia presa.
        if item.get("estado") in ("A fazer", "Em andamento"):
            presas = [d for d in deps(item)
                      if d in por_id and por_id[d].get("estado") != "Concluido"]
            if presas:
                erros.append(
                    f"{ident}: marcado '{item['estado']}' mas depende de {presas}, "
                    "que nao esta(o) concluido(s)"
                )
    return erros, avisos


def calcular_bloqueio(itens: list[dict]) -> list[str]:
    """
    `bloqueia_objetivo` e derivada, nao digitada: marca `sim` para o ALVO e para
    tudo de que ele depende, direta ou indiretamente. `depende_de` aponta para
    tras, entao bloquear = estar entre os antecessores do ALVO.
    """
    por_id = {i["id"]: i for i in itens}
    if ALVO is None:
        for item in itens:
            item["bloqueia_objetivo"] = ""
            item["_cadeia"] = []
        return []
    if ALVO not in por_id:
        sys.exit(f"ERRO: o alvo {ALVO} nao existe em ESTADO.csv.")

    bloqueiam = {ALVO}
    fronteira = [ALVO]
    while fronteira:
        atual = fronteira.pop()
        for d in deps(por_id[atual]):
            if d not in bloqueiam:
                bloqueiam.add(d)
                fronteira.append(d)

    # Cadeia mais curta ate o ALVO: largura primeiro. Responde "por que este importa".
    cadeia = {ALVO: [ALVO]}
    fila = [ALVO]
    while fila:
        atual = fila.pop(0)
        for anterior in deps(por_id[atual]):
            if anterior not in cadeia:
                cadeia[anterior] = [anterior] + cadeia[atual]
                fila.append(anterior)

    mudancas = []
    for item in itens:
        novo = "sim" if item["id"] in bloqueiam else "nao"
        antigo = item.get("bloqueia_objetivo")
        if antigo not in (None, "") and antigo != novo:
            mudancas.append(f"{item['id']}: {antigo} -> {novo}")
        item["bloqueia_objetivo"] = novo
        item["_cadeia"] = cadeia.get(item["id"], [])
    return mudancas


def regravar_csv(itens: list[dict]) -> None:
    """Devolve a coluna calculada ao CSV, para ele se ler sozinho sem rodar nada."""
    with FONTE.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUNAS, lineterminator="\n")
        w.writeheader()
        for item in itens:
            w.writerow({c: item.get(c, "") for c in COLUNAS})


def marca(ident: str, avisos: dict) -> str:
    return f" ⚠ *{'; '.join(avisos[ident])}*" if ident in avisos else ""


def dono_de(item: dict) -> str:
    sufixo = "" if item.get("dono_nomeado") == "sim" else " ⚠"
    return f"{item.get('dono', 'A NOMEAR')}{sufixo}"


def render_resumo(itens: list[dict], avisos: dict) -> str:
    """A visao do vault: para ela ler, nao para o agente trabalhar."""
    abertos = [i for i in itens if i["estado"] in ABERTOS]
    fechados = [i for i in itens if i["estado"] == "Concluido"]
    descartados = [i for i in itens if i["estado"] == "Descartado"]

    p = [CABECALHO, "---", f"projeto: {PROJETO}", f"gerado: {date.today().isoformat()}",
         "fonte: ESTADO.csv no repositório do projeto",
         "tags: [projeto, gerado]", "---", "",
         f"# Resumo — {PROJETO}", "",
         f"**{len(fechados)} itens concluídos, {len(abertos)} em aberto"
         + (f", {len(descartados)} descartados" if descartados else "")
         + ".** Esta página é "
         "gerada a partir de `ESTADO.csv`: o que estiver aqui está no CSV, e o que não "
         "estiver no CSV não existe.", ""]

    if avisos:
        p += [f"> ⚠ **{len(avisos)} de {len(itens)} itens sem conferência recente.** "
              "A marca aparece na própria linha. Item marcado é afirmação herdada, "
              "não verificada — reconfira antes de usar em relatório.", ""]

    if ALVO:
        criticos = [i for i in abertos if i.get("bloqueia_objetivo") == "sim"]
        p += [f"No caminho crítico até `{ALVO}`: **{len(criticos)} itens abertos**. "
              f"Os outros {len(abertos) - len(criticos)} não bloqueiam a entrega.", ""]

    por_frente = OrderedDict()
    for i in sorted(itens, key=lambda x: (x["frente"], x["id"])):
        por_frente.setdefault(i["frente"], []).append(i)

    for frente, lista in por_frente.items():
        p += [f"## {frente}", "",
              "| Item | Estado | Dono | Evidência |", "|---|---|---|---|"]
        for i in lista:
            p.append(f"| **{i['id']}** {i['titulo']}{marca(i['id'], avisos)} "
                     f"| {i['estado']} | {dono_de(i)} | {i['evidencia']} |")
        p.append("")
        movimentos = [i for i in lista
                      if (i.get("proximo_movimento") or "").strip() and i["estado"] in ABERTOS]
        if movimentos:
            p.append("Próximo movimento:")
            p.append("")
            p += [f"- **{i['id']}** — {i['proximo_movimento']}" for i in movimentos]
            p.append("")

    sem_dono = [i for i in abertos if i.get("dono_nomeado") != "sim"]
    if sem_dono:
        p += ["---", "",
              f"## Sem dono nomeado ({len(sem_dono)})", "",
              "Área não responde mensagem. Enquanto a linha disser área ou papel, "
              "ninguém é cobrável.", ""]
        p += [f"- **{i['id']}** {i['titulo']} · _{i.get('dono')}_" for i in sem_dono]
        p.append("")

    return "\n".join(p) + "\n"


def render_quadro(itens: list[dict], avisos: dict) -> str:
    grupos = defaultdict(list)
    for i in itens:
        grupos[i["estado"]].append(i)

    p = [CABECALHO, f"# {PROJETO} — quadro", "", "| Coluna | Itens |", "|---|---:|"]
    for e in ORDEM_ESTADO:
        p.append(f"| {e} | {len(grupos.get(e, []))} |")
    p += ["", "---", ""]
    for e in ORDEM_ESTADO:
        col = grupos.get(e, [])
        if not col:
            continue
        p += [f"## {e} ({len(col)})", ""]
        por_frente = OrderedDict()
        for i in col:
            por_frente.setdefault(i["frente"], []).append(i)
        for frente, lista in por_frente.items():
            p += [f"**{frente}**", ""]
            for i in lista:
                trava = f" · depende de {' '.join(deps(i))}" if deps(i) else ""
                p.append(f"- `{i['id']}` {i['titulo']} · **{dono_de(i)}**{trava}"
                         f"{marca(i['id'], avisos)}")
            p.append("")
    return "\n".join(p) + "\n"


def render_hoje(itens: list[dict]) -> str:
    """O que da para puxar agora: aberto, no caminho critico, sem dependencia presa."""
    por_id = {i["id"]: i for i in itens}
    candidatos = [i for i in itens if i["estado"] in ("A fazer", "Em andamento")]
    if ALVO:
        candidatos = [i for i in candidatos if i.get("bloqueia_objetivo") == "sim"]
    livres = [i for i in candidatos
              if all(por_id[d]["estado"] == "Concluido" for d in deps(i) if d in por_id)]

    p = [CABECALHO, f"# {PROJETO} — o que dá para fazer agora", ""]
    if ALVO:
        p += [f"Só o que bloqueia `{ALVO}` e já está liberado. A cadeia embaixo de cada "
              "item é calculada do grafo de `depende_de`, não escrita à mão.", ""]
    p += ["---", ""]

    if not livres:
        p += ["_Nada liberado: ou está tudo concluído, ou tudo espera dependência._", ""]
    for i in sorted(livres, key=lambda x: x["id"]):
        p.append(f"- `{i['id']}` {i['titulo']} · **{dono_de(i)}**")
        if i.get("_cadeia"):
            p.append(f"  - _por que importa:_ {' → '.join(i['_cadeia'][1:]) or 'é o próprio objetivo'}")
        if (i.get("proximo_movimento") or "").strip():
            p.append(f"  - _próximo movimento:_ {i['proximo_movimento']}")
    p.append("")

    # Gargalo contado, nao estimado: o que trava mais coisa.
    quantos = defaultdict(int)
    for i in itens:
        for d in deps(i):
            if d in por_id and por_id[d]["estado"] != "Concluido":
                quantos[d] += 1
    if quantos:
        p += ["## Gargalos — o que trava mais coisa", "",
              "| Item | Trava | Estado | Dono |", "|---|---:|---|---|"]
        for pid, n in sorted(quantos.items(), key=lambda x: -x[1])[:5]:
            it = por_id[pid]
            p.append(f"| `{pid}` {it['titulo']} | {n} | {it['estado']} | {dono_de(it)} |")
        p.append("")
    return "\n".join(p) + "\n"


def achar_no_vault(vault: Path) -> Path | None:
    """
    Onde gravar: onde a nota ja esta, ou o destino inicial se for a primeira vez.
    Caminho fixo aqui quebra calado quando o vault se reorganiza.
    """
    if not vault.is_dir():
        return None
    for achada in sorted(vault.rglob(NOME_NOTA_VAULT)):
        if not IGNORAR_NO_VAULT.intersection(achada.parts):
            return achada
    inicial = vault.joinpath(*DESTINO_INICIAL)
    return inicial / NOME_NOTA_VAULT if inicial.is_dir() else None


def escrever(caminho: Path, texto: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto, encoding="utf-8")
    print(f"  gerado: {caminho}")


def main() -> int:
    ap = argparse.ArgumentParser(description=f"Gera as visoes de {PROJETO} a partir de ESTADO.csv.")
    ap.add_argument("--check", action="store_true", help="valida sem escrever")
    args = ap.parse_args()

    itens = carregar()
    erros, avisos = conferir(itens)
    if erros:
        print(f"ESTADO.csv REPROVOU — {len(erros)} erro(s). Nada foi gerado.\n")
        for e in erros:
            print(f"  - {e}")
        return 1

    print(f"ESTADO.csv OK — {len(itens)} itens.")
    if avisos:
        print(f"{len(avisos)} com aviso (a visao sai, com a marca na linha):")
        for ident, msgs in sorted(avisos.items()):
            print(f"  - {ident}: {'; '.join(msgs)}")

    mudancas = calcular_bloqueio(itens)
    if ALVO:
        n_sim = sum(1 for i in itens if i.get("bloqueia_objetivo") == "sim")
        print(f"Caminho critico ate {ALVO}: {n_sim} bloqueiam, {len(itens) - n_sim} nao.")
        for m in mudancas:
            print(f"    - bloqueia_objetivo recalculada: {m}")

    if args.check:
        return 0

    regravar_csv(itens)
    print()
    escrever(RAIZ / "VISAO_hoje.md", render_hoje(itens))
    escrever(RAIZ / "VISAO_quadro.md", render_quadro(itens, avisos))

    vault = Path(os.environ.get("VAULT_DIR", VAULT_PADRAO))
    alvo = achar_no_vault(vault)
    if alvo is not None:
        escrever(alvo, render_resumo(itens, avisos))
    else:
        print(f"  nota '{NOME_NOTA_VAULT}' nao encontrada no vault {vault} — visao do vault nao gerada.")

    print("\nPronto. As visoes sao derivadas: nao as edite a mao.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
