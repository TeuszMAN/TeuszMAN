#!/usr/bin/env python3
"""Gera o cabeçalho e os cartões de projeto do README.

Uso: python scripts/gerar_assets.py
Edite os textos em CABECALHO e CARTOES e rode de novo para atualizar os SVGs em assets/.
Não precisa de bibliotecas externas.
"""

from __future__ import annotations

import base64
from html import escape
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ASSETS = RAIZ / "assets"

# Paleta inspirada no tema escuro do GitHub
FUNDO = "#0d1117"
BARRA = "#161b22"
BORDA = "#30363d"
TEXTO = "#e6edf3"
SUAVE = "#9da7b3"
MUDO = "#7d8590"
APAGADO = "#3d444d"
AZUL = "#58a6ff"
ROXO = "#bc8cff"
VERDE = "#3fb950"
AMBAR = "#d29922"
CIANO = "#a5d6ff"

FONTE = "'JBM',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def fontes_css() -> str:
    """Embute a JetBrains Mono (subconjunto, licença OFL) para o SVG renderizar igual em todo lugar."""
    partes = []
    for peso in (400, 700):
        dados = base64.b64encode((ASSETS / "fonts" / f"jbm-{peso}.woff2").read_bytes()).decode()
        partes.append(
            "@font-face{font-family:'JBM';font-weight:%d;"
            "src:url(data:font/woff2;base64,%s) format('woff2')}" % (peso, dados)
        )
    return "".join(partes)


# ---------------------------------------------------------------- cabeçalho

LARGURA = 860
PAD = 20  # espaço em volta da janela, para a sombra
X0 = PAD + 26  # início do texto dentro da janela
FS = 15  # tamanho da fonte do terminal
CW = FS * 0.6  # largura de um caractere da JetBrains Mono
LH = 24  # altura de linha

CABECALHO = {
    "titulo_janela": "mateus@hortolandia: ~",
    "nome": "Mateus Alves Nunes",
    "linha": "Engenharia de Computação (UNASP) · QA no Instituto Eldorado",
    "slogan": "Construo agentes de IA e depois tento quebrá-los.",
    "testes": [
        # (pasta, arquivo, status, comentário)
        ("formacao/", "test_engenharia_de_computacao.py", "PASSED", "# UNASP, 2028"),
        ("eldorado/", "test_agentes_de_auditoria.py", "PASSED", "# -50% de tempo"),
        ("pesquisa/", "test_artigo_sbes_2026.py", "PASSED", "# publicado"),
        ("hackathons/", "test_ibm_unasp_2026.py", "PASSED", "# 2º lugar"),
        ("proximo/", "test_ai_engineer.py", "RUNNING", "# em andamento"),
    ],
    "ano": "2026",
}


def col(c: float) -> float:
    return X0 + c * CW


def t(texto: str, cor: str, peso: int = 400, extra: str = "") -> str:
    return f'<tspan fill="{cor}" font-weight="{peso}"{extra}>{escape(texto)}</tspan>'


def prompt(y: float, comando: str, inicio: float, passo: float, caminho: str = "~") -> tuple[str, float]:
    """Linha de prompt com o comando sendo digitado letra a letra."""
    cx = col(len(caminho) + 1)
    seta = (
        f'<path d="M{cx + 1.5:.1f} {y - 10.5:.1f}l5 4.75-5 4.75" fill="none" stroke="{ROXO}" '
        'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
    )
    letras = "".join(
        f'<tspan class="k" style="animation-delay:{inicio + 0.25 + i * passo:.2f}s">{escape(ch)}</tspan>'
        for i, ch in enumerate(comando)
    )
    fim = inicio + 0.25 + len(comando) * passo
    svg = (
        f'<g class="l" style="animation-delay:{inicio:.2f}s">'
        f'<text x="{col(0)}" y="{y}" fill="{AZUL}" font-weight="700">{escape(caminho)}</text>{seta}'
        f'<text x="{col(len(caminho) + 3)}" y="{y}" fill="{TEXTO}">{letras}</text></g>'
    )
    return svg, fim


def linha(y: float, conteudo: str, atraso: float, tamanho: float = FS) -> str:
    return (
        f'<g class="l" style="animation-delay:{atraso:.2f}s">'
        f'<text x="{col(0)}" y="{y}" font-size="{tamanho}">{conteudo}</text></g>'
    )


def gerar_cabecalho() -> str:
    c = CABECALHO
    partes: list[str] = []
    y = PAD + 38 + 34

    svg, fim = prompt(y, "whoami", 0.3, 0.07)
    partes.append(svg)
    y += 36
    partes.append(linha(y, t(c["nome"], "#ffffff", 700), fim + 0.2, 24))
    y += LH + 4
    partes.append(linha(y, t(c["linha"], TEXTO), fim + 0.35))
    y += LH
    partes.append(linha(y, t(c["slogan"], CIANO), fim + 0.5))

    y += LH + 16
    svg, fim = prompt(y, "pytest carreira/ -v", fim + 1.0, 0.045)
    partes.append(svg)
    y += LH
    partes.append(linha(y, t(f"collected {len(c['testes'])} items", MUDO), fim + 0.25))
    y += 8

    col_status, col_pct, col_coment = 47, 54, 62
    atraso = fim + 0.55
    total = len(c["testes"])
    passou = 0
    for i, (pasta, arquivo, status, comentario) in enumerate(c["testes"]):
        y += LH
        nome = pasta + arquivo
        pontos = "·" * max(3, col_status - len(nome) - 2)
        cor = VERDE if status == "PASSED" else AMBAR
        pulso = ' class="pulse"' if status != "PASSED" else ""
        conteudo = (
            t(pasta, MUDO) + t(arquivo, TEXTO) + t(" " + pontos + " ", APAGADO)
            + t(status, cor, 700, pulso)
        )
        if status == "PASSED":
            passou += 1
            pct = round(100 * (i + 1) / total)
            conteudo += t(" " * (col_pct - col_status - len(status)) + f"[{pct:>3}%]", MUDO)
            conteudo += t(" " * (col_coment - col_pct - 6) + comentario, MUDO)
        else:
            conteudo += t(" " * (col_coment - col_status - len(status)) + comentario, MUDO)
        partes.append(linha(y, conteudo, atraso))
        atraso += 0.3

    y += LH + 10
    rodando = total - passou
    miolo = f" {passou} passed, {rodando} running in {c['ano']} "
    lado = (80 - len(miolo)) // 2
    resumo = (
        t("=" * lado + " ", MUDO)
        + t(f"{passou} passed", VERDE, 700)
        + t(", ", MUDO)
        + t(f"{rodando} running", AMBAR, 700)
        + t(f" in {c['ano']} " + "=" * (80 - len(miolo) - lado), MUDO)
    )
    partes.append(linha(y, resumo, atraso + 0.1))

    y += LH + 12
    inicio_cursor = atraso + 0.45
    cx = col(2)
    partes.append(
        f'<g class="l" style="animation-delay:{inicio_cursor:.2f}s">'
        f'<text x="{col(0)}" y="{y}" fill="{AZUL}" font-weight="700">~</text>'
        f'<path d="M{cx + 1.5:.1f} {y - 10.5:.1f}l5 4.75-5 4.75" fill="none" stroke="{ROXO}" '
        'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<rect class="blink" style="animation-delay:{inicio_cursor + 0.3:.2f}s" x="{col(4)}" '
        f'y="{y - 13}" width="{CW:.1f}" height="17" fill="{TEXTO}"/></g>'
    )

    altura = y + 26 + PAD
    jy = PAD
    jh = altura - 2 * PAD
    jw = LARGURA - 2 * PAD
    titulo = escape(c["titulo_janela"])
    css = (
        fontes_css()
        + f"text{{font-family:{FONTE};white-space:pre}}"
        ".l{animation:entra .35s ease-out backwards}"
        "@keyframes entra{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}"
        ".k{animation:tecla .01s linear backwards}"
        "@keyframes tecla{from{fill-opacity:0}to{fill-opacity:1}}"
        ".blink{animation:pisca 1.1s steps(1) infinite}"
        "@keyframes pisca{50%{opacity:0}}"
        ".pulse{animation:pulsa 1.2s ease-in-out infinite alternate}"
        "@keyframes pulsa{from{fill-opacity:1}to{fill-opacity:.35}}"
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
    )
    alt = f"{c['nome']}: {c['linha']}. {c['slogan']}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {LARGURA} {altura}" '
        f'width="{LARGURA}" height="{altura}" font-size="{FS}" xml:space="preserve" role="img" aria-label="{escape(alt)}">'
        f"<title>{escape(alt)}</title>"
        f"<defs><style>{css}</style>"
        '<filter id="sombra" x="-10%" y="-10%" width="120%" height="130%">'
        '<feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#010409" flood-opacity=".35"/></filter>'
        f'<clipPath id="janela"><rect x="{PAD}" y="{jy}" width="{jw}" height="{jh}" rx="12"/></clipPath></defs>'
        f'<rect x="{PAD}" y="{jy}" width="{jw}" height="{jh}" rx="12" fill="{FUNDO}" filter="url(#sombra)"/>'
        f'<g clip-path="url(#janela)"><rect x="{PAD}" y="{jy}" width="{jw}" height="38" fill="{BARRA}"/>'
        f'<line x1="{PAD}" y1="{jy + 38}" x2="{PAD + jw}" y2="{jy + 38}" stroke="{BORDA}"/></g>'
        f'<rect x="{PAD + 0.5}" y="{jy + 0.5}" width="{jw - 1}" height="{jh - 1}" rx="11.5" fill="none" stroke="{BORDA}"/>'
        f'<circle cx="{PAD + 22}" cy="{jy + 19}" r="6" fill="#ff5f57"/>'
        f'<circle cx="{PAD + 42}" cy="{jy + 19}" r="6" fill="#febc2e"/>'
        f'<circle cx="{PAD + 62}" cy="{jy + 19}" r="6" fill="#28c840"/>'
        f'<text x="{LARGURA / 2}" y="{jy + 24}" text-anchor="middle" font-size="13" fill="{MUDO}">{titulo}</text>'
        + "".join(partes)
        + "</svg>\n"
    )


# ------------------------------------------------------------------ cartões

CARTOES = [
    {
        "arquivo": "card-tailor.svg",
        "caminho": "TeuszMAN/tailor-ai-stylist-engine",
        "nome": "Tailor AI Engine",
        "selo": ("103 testes", VERDE),
        "descricao": [
            "Microsserviço agêntico que monta looks só com",
            "peças em estoque. Fallback do LLM para regras,",
            "guardrails e trace de cada ferramenta.",
        ],
        "tags": ["Python", "LangGraph", "FastAPI", "Pydantic"],
    },
    {
        "arquivo": "card-matchhelp.svg",
        "caminho": "TeuszMAN/hackaton-unasp-2026",
        "nome": "MatchHelp",
        "selo": ("2º lugar · IBM", AMBAR),
        "descricao": [
            "Plataforma multiagente que liga instituições",
            "em crise a voluntários a partir de relatos em",
            "linguagem natural. Fiz a API e o matchmaking.",
        ],
        "tags": ["FastAPI", "PostgreSQL", "watsonx"],
    },
    {
        "arquivo": "card-nexxus.svg",
        "caminho": "nexxus.earth",
        "nome": "Nexxus",
        "selo": ("NASA Space Apps", AZUL),
        "descricao": [
            "Globo 3D que compara passagens do satélite de",
            "radar NISAR para mostrar enchentes. Fiz a API,",
            "o pipeline de dados e o deploy na Azure.",
        ],
        "tags": ["NestJS", "Python", "Azure"],
    },
    {
        "arquivo": "card-medlink.svg",
        "caminho": "VitorBuenoOliveira/MedlinkProject",
        "nome": "MedLink",
        "selo": ("spec + testes", ROXO),
        "descricao": [
            "Gestão de transporte sanitário do SUS, com",
            "cada cenário da especificação ligado a um",
            "teste. Apresentado na Semana de Tecnologia.",
        ],
        "tags": ["Java", "Spring", "React", "PostgreSQL"],
    },
]


def gerar_cartao(cartao: dict) -> str:
    w, h = 420, 194
    selo_texto, selo_cor = cartao["selo"]
    selo_w = len(selo_texto) * 7.2 + 30
    selo_x = w - 20 - selo_w
    partes = [
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="10" fill="{FUNDO}" stroke="{BORDA}"/>',
        f'<text x="20" y="32" font-size="12" fill="{MUDO}">{escape(cartao["caminho"])}</text>',
        f'<text x="20" y="62" font-size="20" font-weight="700" fill="{TEXTO}">{escape(cartao["nome"])}</text>',
        f'<rect x="{selo_x:.1f}" y="44" width="{selo_w:.1f}" height="24" rx="12" fill="{selo_cor}" '
        f'fill-opacity=".12" stroke="{selo_cor}" stroke-opacity=".55"/>',
        f'<circle cx="{selo_x + 13:.1f}" cy="56" r="4" fill="{selo_cor}"/>',
        f'<text x="{selo_x + 23:.1f}" y="60" font-size="12" fill="{selo_cor}">{escape(selo_texto)}</text>',
    ]
    y = 92
    for linha_desc in cartao["descricao"]:
        partes.append(f'<text x="20" y="{y}" font-size="13" fill="{SUAVE}">{escape(linha_desc)}</text>')
        y += 20
    x = 20.0
    for tag in cartao["tags"]:
        tw = len(tag) * 7.2 + 20
        partes.append(
            f'<rect x="{x:.1f}" y="150" width="{tw:.1f}" height="24" rx="6" fill="{BARRA}" stroke="{BORDA}"/>'
            f'<text x="{x + 10:.1f}" y="166" font-size="12" fill="{TEXTO}">{escape(tag)}</text>'
        )
        x += tw + 8
    alt = f"{cartao['nome']}: {' '.join(cartao['descricao'])}"
    css = fontes_css() + f"text{{font-family:{FONTE};white-space:pre}}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'font-size="13" xml:space="preserve" role="img" aria-label="{escape(alt)}"><title>{escape(alt)}</title>'
        f"<defs><style>{css}</style></defs>" + "".join(partes) + "</svg>\n"
    )


def main() -> None:
    (ASSETS / "header.svg").write_text(gerar_cabecalho(), encoding="utf-8")
    for cartao in CARTOES:
        (ASSETS / cartao["arquivo"]).write_text(gerar_cartao(cartao), encoding="utf-8")
    print("assets gerados em", ASSETS)


if __name__ == "__main__":
    main()
