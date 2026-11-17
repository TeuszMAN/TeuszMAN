#!/usr/bin/env python3
"""Gera assets/atividade.svg com as contribuições do último ano, no visual do README.

No GitHub Actions (workflow atividade.yml) lê o calendário pela API GraphQL com o GITHUB_TOKEN.
Para testar localmente sem token: python scripts/atividade.py --dados exemplo.json
(exemplo.json = lista de [data, contagem], com datas AAAA-MM-DD).
Não precisa de bibliotecas externas.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import urllib.request
from datetime import date, timedelta
from html import escape
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ASSETS = RAIZ / "assets"

FUNDO = "#0d1117"
BARRA = "#161b22"
BORDA = "#30363d"
TEXTO = "#e6edf3"
MUDO = "#7d8590"
VERDE = "#3fb950"
NIVEIS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
FONTE = "'JBM',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

CONSULTA = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def buscar(login: str, token: str) -> list[tuple[date, int]]:
    corpo = json.dumps({"query": CONSULTA, "variables": {"login": login}}).encode()
    pedido = urllib.request.Request(
        "https://api.github.com/graphql",
        data=corpo,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "atividade-svg",
        },
    )
    with urllib.request.urlopen(pedido, timeout=30) as resposta:
        dados = json.load(resposta)
    if dados.get("errors"):
        raise SystemExit(f"Erro na API GraphQL: {dados['errors']}")
    semanas = dados["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [
        (date.fromisoformat(dia["date"]), dia["contributionCount"])
        for semana in semanas
        for dia in semana["contributionDays"]
    ]


def buscar_html(login: str) -> list[tuple[date, int]]:
    """Plano B sem token: lê o calendário público da página de contribuições do perfil."""
    pedido = urllib.request.Request(
        f"https://github.com/users/{login}/contributions", headers={"User-Agent": "atividade-svg"}
    )
    with urllib.request.urlopen(pedido, timeout=30) as resposta:
        html = resposta.read().decode("utf-8")
    datas = {}
    for celula in re.finditer(r"<td[^>]*ContributionCalendar-day[^>]*>", html):
        tag = celula.group(0)
        data = re.search(r'data-date="([0-9-]+)"', tag)
        ident = re.search(r'id="([^"]+)"', tag)
        if data and ident:
            datas[ident.group(1)] = date.fromisoformat(data.group(1))
    contagens = {}
    for dica in re.finditer(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        numero = re.match(r"\s*(\d+) contribution", dica.group(2))
        contagens[dica.group(1)] = int(numero.group(1)) if numero else 0
    if not datas:
        raise SystemExit("Não encontrei o calendário de contribuições na página do perfil.")
    return [(dia, contagens.get(ident, 0)) for ident, dia in datas.items()]


def niveis(contagens: list[int]) -> list[float]:
    """Limites dos 4 tons de verde, pelos quartis dos dias com contribuição (como o GitHub faz)."""
    positivos = sorted(c for c in contagens if c > 0)
    if not positivos:
        return [1, 1, 1]
    def quartil(q: float) -> float:
        return positivos[min(len(positivos) - 1, int(q * len(positivos)))]
    return [quartil(0.25), quartil(0.5), quartil(0.75)]


def maior_sequencia(dias: list[tuple[date, int]]) -> int:
    melhor = atual = 0
    for _, contagem in dias:
        atual = atual + 1 if contagem > 0 else 0
        melhor = max(melhor, atual)
    return melhor


def fontes_css() -> str:
    partes = []
    for peso in (400, 700):
        caminho = ASSETS / "fonts" / f"jbm-{peso}.woff2"
        if caminho.exists():
            dados = base64.b64encode(caminho.read_bytes()).decode()
            partes.append(
                "@font-face{font-family:'JBM';font-weight:%d;"
                "src:url(data:font/woff2;base64,%s) format('woff2')}" % (peso, dados)
            )
    return "".join(partes)


def milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def gerar_svg(dias: list[tuple[date, int]]) -> str:
    dias = sorted(dias)
    contagens = [c for _, c in dias]
    total = sum(contagens)
    ativos = sum(1 for c in contagens if c > 0)
    sequencia = maior_sequencia(dias)
    limites = niveis(contagens)

    largura, pad = 860, 20
    jw = largura - 2 * pad
    passo, lado = 13.5, 10.5
    gx = pad + 26 + 34  # início da grade (depois dos dias da semana)
    gy = pad + 38 + 66  # topo da grade (depois do resumo e dos meses)

    inicio = dias[0][0]
    deslocamento = (inicio.weekday() + 1) % 7  # domingo = 0, como no GitHub
    colunas: dict[int, list[tuple[int, date, int]]] = {}
    for i, (dia, contagem) in enumerate(dias):
        indice = i + deslocamento
        colunas.setdefault(indice // 7, []).append((indice % 7, dia, contagem))

    partes: list[str] = []
    mes_anterior = None
    ultimo_rotulo = -9
    for coluna in sorted(colunas):
        celulas = colunas[coluna]
        primeiro = min(celulas)[1]
        if primeiro.month != mes_anterior:
            if coluna - ultimo_rotulo >= 3 and coluna < max(colunas) - 1:
                partes.append(
                    f'<text x="{gx + coluna * passo:.1f}" y="{gy - 10}" font-size="11" fill="{MUDO}">'
                    f"{MESES[primeiro.month - 1]}</text>"
                )
                ultimo_rotulo = coluna
            mes_anterior = primeiro.month
        quadrados = []
        for linha, dia, contagem in celulas:
            nivel = 0 if contagem == 0 else 1 + sum(contagem > limite for limite in limites)
            quadrados.append(
                f'<rect x="{gx + coluna * passo:.1f}" y="{gy + linha * passo:.1f}" width="{lado}" '
                f'height="{lado}" rx="2.5" fill="{NIVEIS[nivel]}"'
                + (f' stroke="{BORDA}" stroke-opacity=".6"' if nivel == 0 else "")
                + f"><title>{dia.day} {MESES[dia.month - 1]}: {contagem}</title></rect>"
            )
        partes.append(f"<g>{''.join(quadrados)}</g>")

    for linha, nome in ((1, "seg"), (3, "qua"), (5, "sex")):
        partes.append(
            f'<text x="{pad + 26}" y="{gy + linha * passo + 9:.1f}" font-size="11" fill="{MUDO}">{nome}</text>'
        )

    resumo = (
        f'<text x="{pad + 26}" y="{pad + 38 + 32}" font-size="14">'
        f'<tspan fill="{VERDE}" font-weight="700">{milhar(total)}</tspan>'
        f'<tspan fill="{TEXTO}"> contribuições no último ano</tspan>'
        f'<tspan fill="{MUDO}">  ·  {ativos} dias ativos  ·  maior sequência: {sequencia} dias</tspan></text>'
    )

    altura_grade = 7 * passo
    ly = gy + altura_grade + 26
    legenda_x = pad + jw - 26 - (5 * passo + 2 * 46)
    legenda = [f'<text x="{legenda_x:.1f}" y="{ly + 9}" font-size="11" fill="{MUDO}">menos</text>']
    for k, cor in enumerate(NIVEIS):
        legenda.append(
            f'<rect x="{legenda_x + 46 + k * passo:.1f}" y="{ly}" width="{lado}" height="{lado}" rx="2.5" fill="{cor}"'
            + (f' stroke="{BORDA}" stroke-opacity=".6"' if k == 0 else "")
            + "/>"
        )
    legenda.append(
        f'<text x="{legenda_x + 46 + 5 * passo + 6:.1f}" y="{ly + 9}" font-size="11" fill="{MUDO}">mais</text>'
    )
    atualizado = (
        f'<text x="{pad + 26}" y="{ly + 9}" font-size="11" fill="{MUDO}">'
        f"atualizado em {dias[-1][0].day} {MESES[dias[-1][0].month - 1]} {dias[-1][0].year}</text>"
    )

    altura = ly + 30 + pad
    jh = altura - 2 * pad
    css = (
        fontes_css()
        + f"text{{font-family:{FONTE};white-space:pre}}"
    )
    alt = f"{milhar(total)} contribuições no GitHub no último ano, {ativos} dias ativos"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largura} {altura:.0f}" width="{largura}" '
        f'height="{altura:.0f}" font-size="13" xml:space="preserve" role="img" aria-label="{escape(alt)}">'
        f"<title>{escape(alt)}</title><defs><style>{css}</style>"
        '<filter id="sombra" x="-10%" y="-10%" width="120%" height="140%">'
        '<feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#010409" flood-opacity=".35"/></filter>'
        f'<clipPath id="janela"><rect x="{pad}" y="{pad}" width="{jw}" height="{jh:.0f}" rx="12"/></clipPath></defs>'
        f'<rect x="{pad}" y="{pad}" width="{jw}" height="{jh:.0f}" rx="12" fill="{FUNDO}" filter="url(#sombra)"/>'
        f'<g clip-path="url(#janela)"><rect x="{pad}" y="{pad}" width="{jw}" height="38" fill="{BARRA}"/>'
        f'<line x1="{pad}" y1="{pad + 38}" x2="{pad + jw}" y2="{pad + 38}" stroke="{BORDA}"/></g>'
        f'<rect x="{pad + 0.5}" y="{pad + 0.5}" width="{jw - 1}" height="{jh - 1:.0f}" rx="11.5" fill="none" stroke="{BORDA}"/>'
        f'<circle cx="{pad + 22}" cy="{pad + 19}" r="6" fill="#ff5f57"/>'
        f'<circle cx="{pad + 42}" cy="{pad + 19}" r="6" fill="#febc2e"/>'
        f'<circle cx="{pad + 62}" cy="{pad + 19}" r="6" fill="#28c840"/>'
        f'<text x="{largura / 2}" y="{pad + 24}" text-anchor="middle" fill="{MUDO}">'
        "mateus@hortolandia: ~/atividade</text>"
        + resumo
        + "".join(partes)
        + "".join(legenda)
        + atualizado
        + "</svg>\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("saida", nargs="?", default=str(ASSETS / "atividade.svg"))
    parser.add_argument("--dados", help="JSON local com [data, contagem] para testar sem token")
    args = parser.parse_args()

    if args.dados:
        bruto = json.loads(Path(args.dados).read_text(encoding="utf-8"))
        dias = [(date.fromisoformat(d), int(c)) for d, c in bruto]
    else:
        token = os.environ.get("GITHUB_TOKEN")
        login = os.environ.get("LOGIN", "TeuszMAN")
        try:
            if not token:
                raise RuntimeError("sem GITHUB_TOKEN")
            dias = buscar(login, token)
        except (OSError, RuntimeError, KeyError, SystemExit) as erro:
            print(f"API GraphQL indisponível ({erro}); usando a página pública do perfil.")
            dias = buscar_html(login)

    hoje = max(d for d, _ in dias)
    dias = [(d, c) for d, c in dias if d > hoje - timedelta(days=371)]
    Path(args.saida).write_text(gerar_svg(dias), encoding="utf-8")
    print(f"{args.saida}: {sum(c for _, c in dias)} contribuições em {len(dias)} dias")


if __name__ == "__main__":
    main()
