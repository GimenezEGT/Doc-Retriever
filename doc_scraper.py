#!/usr/bin/env python3
"""
doc_scraper.py — Baixa uma documentação HTML, converte para Markdown limpo e
gera um único arquivo .md consolidado.

Uso:
    python doc_scraper.py --url <URL> --saida <arquivo.md> [--tmp <pasta_temp>]

Argumentos:
    --url      URL raiz da documentação a ser baixada (obrigatório)
    --saida    Caminho do arquivo .md final a ser gerado (obrigatório)
    --tmp      Pasta temporária para os HTMLs baixados e os .md intermediários
               (opcional; padrão: _tmp_scraper/)
    --manter   Se passado, mantém a pasta temporária após a execução

Exemplo:
    python doc_scraper.py \
        --url https://console.groq.com/docs \
        --saida groq_doc_completa.md
"""

import os
import sys
import shutil
import argparse
import subprocess
import textwrap
from pathlib import Path

from bs4 import BeautifulSoup
from markdownify import markdownify


# ─────────────────────────────────────────────
# 1. Download via wget
# ─────────────────────────────────────────────

def baixar_documentacao(url: str, pasta_html: Path) -> None:
    """Usa wget para espelhar recursivamente a documentação."""
    pasta_html.mkdir(parents=True, exist_ok=True)

    cmd = [
        "wget",
        "-r",                    # desce pelos links (--recursive)
        "-k",                    # adapta links para navegação local (--convert-links)
        "-p",                    # baixa CSS/JS/imagens necessários (--page-requisites)
        "-E",                    # força extensão .html em arquivos sem ela (--html-extension)
        "-U", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", # User-Agent
        "--no-clobber",          # não re-baixa arquivos já existentes
        "--no-parent",           # não sobe na hierarquia do site
        "--quiet",               # silencioso (remove para ver progresso)
        "--show-progress",       # barra de progresso simples
        "-e", "robots=off",      # ignora robots.txt
        "--directory-prefix", str(pasta_html), # Salva na pasta temporária do script
        url,                     # Usa a URL passada por argumento
    ]

    print(f"[1/3] Baixando documentação de: {url}")
    print("      (pode demorar alguns minutos dependendo do tamanho)\n")

    resultado = subprocess.run(cmd, capture_output=False)

    if resultado.returncode not in (0, 8):          # 8 = algum link quebrado, aceitável
        print(f"[AVISO] wget terminou com código {resultado.returncode}. "
              "Verifique se os arquivos foram baixados corretamente.")


# ─────────────────────────────────────────────
# 2. Limpeza HTML → Markdown
# ─────────────────────────────────────────────

def limpar_html_para_markdown(caminho_arquivo: Path) -> str:
    """Converte um arquivo HTML em Markdown limpo, removendo ruído."""
    try:
        with open(caminho_arquivo, "r", encoding="utf-8", errors="replace") as f:
            soup = BeautifulSoup(f, "html.parser")
    except Exception as e:
        print(f"  [ERRO] Não foi possível ler {caminho_arquivo.name}: {e}")
        return ""

    # Remove tags que não agregam conteúdo
    for tag in soup(["script", "style", "nav", "footer", "header", "aside",
                     "noscript", "iframe", "form"]):
        tag.decompose()

    # Busca o bloco de conteúdo principal em ordem de prioridade
    conteudo = (
        soup.find("main")
        or soup.find(role="main")
        or soup.find("article")
        or soup.find("div", class_="document")
        or soup.find("div", class_="content")
        or soup.find("div", id="content")
        or soup.body
    )

    if not conteudo:
        return ""

    texto_md = markdownify(
        str(conteudo),
        heading_style="ATX",
        code_language="python",
        strip=["a"],              # remove links inline (deixa só o texto)
    )

    # Remove linhas em branco consecutivas
    linhas = [l for l in texto_md.splitlines() if l.strip()]
    return "\n".join(linhas)


def converter_pasta(pasta_html: Path, pasta_md: Path) -> int:
    """Percorre todos os HTMLs e salva .md equivalente mantendo a estrutura."""
    pasta_md.mkdir(parents=True, exist_ok=True)
    total = 0

    for arquivo in sorted(pasta_html.rglob("*.html")):
        print(f"  Convertendo: {arquivo.relative_to(pasta_html)}")
        conteudo = limpar_html_para_markdown(arquivo)

        if not conteudo.strip():
            continue

        # Espelha a estrutura de subpastas
        relativo = arquivo.relative_to(pasta_html)
        destino = pasta_md / relativo.with_suffix(".md")
        destino.parent.mkdir(parents=True, exist_ok=True)

        destino.write_text(conteudo, encoding="utf-8")
        total += 1

    return total


# ─────────────────────────────────────────────
# 3. Mesclagem em um único .md
# ─────────────────────────────────────────────

def mesclar_markdowns(pasta_md: Path, arquivo_saida: Path) -> int:
    """Une todos os .md em um único arquivo com cabeçalhos separadores."""
    arquivos = sorted(pasta_md.rglob("*.md"))
    total = 0

    with open(arquivo_saida, "w", encoding="utf-8") as out:
        for md in arquivos:
            nome_secao = md.relative_to(pasta_md).as_posix().replace(".md", "")
            conteudo = md.read_text(encoding="utf-8").strip()

            if not conteudo:
                continue

            out.write(f"\n\n---\n\n# SEÇÃO: {nome_secao}\n\n")
            out.write(conteudo)
            out.write("\n")
            total += 1

    return total


# ─────────────────────────────────────────────
# 4. Ponto de entrada
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Baixa documentação HTML e gera um único .md limpo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Exemplos:
              python doc_scraper.py --url https://exemplo.com --saida exemplo.md
              python doc_scraper.py --url https://docs.python.org/3/ --saida python3.md --manter
        """),
    )
    parser.add_argument("--url",    required=True,  help="URL raiz da documentação")
    parser.add_argument("--saida",  required=True,  help="Arquivo .md de saída")
    parser.add_argument("--tmp",    default="_tmp_scraper",
                        help="Pasta temporária (padrão: _tmp_scraper/)")
    parser.add_argument("--manter", action="store_true",
                        help="Mantém a pasta temporária após a execução")
    args = parser.parse_args()

    pasta_tmp  = Path(args.tmp)
    pasta_html = pasta_tmp / "html"
    pasta_md   = pasta_tmp / "md"
    arquivo_saida = Path(args.saida)

    # Garante que a pasta de saída existe
    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)

    # ── Etapa 1: Download ──────────────────────────────────────────────────
    baixar_documentacao(args.url, pasta_html)

    # ── Etapa 2: Conversão HTML → MD ──────────────────────────────────────
    print(f"\n[2/3] Convertendo HTMLs para Markdown...")
    total_convertidos = converter_pasta(pasta_html, pasta_md)
    print(f"      {total_convertidos} arquivos convertidos.")

    if total_convertidos == 0:
        print("\n[ERRO] Nenhum HTML foi convertido. Verifique se o download funcionou.")
        sys.exit(1)

    # ── Etapa 3: Mesclagem ────────────────────────────────────────────────
    print(f"\n[3/3] Mesclando em '{arquivo_saida}'...")
    total_mesclados = mesclar_markdowns(pasta_md, arquivo_saida)
    print(f"      {total_mesclados} seções incluídas.")

    # ── Limpeza opcional ──────────────────────────────────────────────────
    if not args.manter and pasta_tmp.exists():
        shutil.rmtree(pasta_tmp)
        print(f"\n  Pasta temporária '{pasta_tmp}' removida.")

    tamanho_kb = arquivo_saida.stat().st_size / 1024
    print(f"\n✅ Concluído! Arquivo gerado: '{arquivo_saida}' ({tamanho_kb:.1f} KB)")


if __name__ == "__main__":
    main()