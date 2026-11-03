"""
Scouter BI — gerar_html.py
Monta as páginas HTML do relatório (powerbi/html/*.html + comum.css + comum.js),
minifica e grava em powerbi/html/dist/. Cada página vira uma medida DAX no Power BI
(o marcador __DADOS__ recebe a medida [JSON Dados]).

Uso: npm install  (uma vez)  e depois  python scripts/gerar_html.py
"""
import re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "powerbi" / "html"
DIST = HTML / "dist"
PAGINAS = ["scouter", "arena", "escalada", "quiz", "radar", "bastidores"]
MINIFY = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "scripts" / "minify.js"


def montar(nome: str) -> str:
    src = (HTML / f"{nome}.html").read_text(encoding="utf-8")
    css = re.search(r"<style>(.*?)</style>", src, re.S).group(1)
    js = list(re.finditer(r"<script>(.*?)</script>", src, re.S))[-1]
    corpo = src[src.index("</style>") + len("</style>"): js.start()]
    return ("<style>" + (HTML / "comum.css").read_text(encoding="utf-8") + "\n" + css + "</style>" + corpo +
            "<script>window.D=__DADOS__;</script><script>" + (HTML / "comum.js").read_text(encoding="utf-8") +
            "</script><script>" + js.group(1) + "</script>")


if __name__ == "__main__":
    DIST.mkdir(parents=True, exist_ok=True)
    for p in PAGINAS:
        if not (HTML / f"{p}.html").exists():
            continue
        bruto = DIST / f"{p}.full.html"
        bruto.write_text(montar(p), encoding="utf-8")
        subprocess.run(["node", str(MINIFY), str(bruto), str(DIST / f"{p}.min.html")], check=True)
        bruto.unlink()
