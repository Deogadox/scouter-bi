"""
Scouter BI — check_api.py (Fase 0)

Faz o reconhecimento da Dragon Ball API:
  - testa os endpoints /characters, /planets e /transformations
  - lista os campos e tipos que a API devolve hoje
  - mostra exemplos de ki/maxKi (vêm como texto e precisam de tratamento)
  - salva tudo em docs/api_campos_detectados.md e uma amostra em data/raw/

Uso:  python src\\check_api.py
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

BASE_URL = os.getenv("API_BASE_URL", "https://dragonball-api.com/api").rstrip("/")
TIMEOUT = int(os.getenv("API_TIMEOUT_SECONDS", "15"))

RAW_DIR = ROOT / "data" / "raw"
DOCS_DIR = ROOT / "docs"
RAW_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)


def get(path: str, **params) -> dict | list:
    url = f"{BASE_URL}{path}"
    resp = requests.get(url, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def describe(obj, prefix: str = "") -> list[tuple[str, str, str]]:
    """Achata um JSON em (campo, tipo, exemplo)."""
    rows = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            name = f"{prefix}{k}"
            if isinstance(v, dict):
                rows.append((name, "object", ""))
                rows += describe(v, name + ".")
            elif isinstance(v, list):
                rows.append((name, f"array[{len(v)}]", ""))
                if v and isinstance(v[0], dict):
                    rows += describe(v[0], name + "[].")
            else:
                exemplo = str(v)
                rows.append((name, type(v).__name__, exemplo[:60]))
    return rows


def items_of(payload):
    """A API pode devolver {items: [...]} paginado ou uma lista direta."""
    if isinstance(payload, dict) and "items" in payload:
        return payload["items"]
    return payload if isinstance(payload, list) else [payload]


def main() -> None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = [f"# Campos detectados na Dragon Ball API\n", f"Gerado em {stamp} a partir de `{BASE_URL}`.\n"]

    checks = {
        "/characters (lista)": ("/characters", {"page": 1, "limit": 5}),
        "/characters/1 (detalhe)": ("/characters/1", {}),
        "/planets (lista)": ("/planets", {"page": 1, "limit": 5}),
        "/transformations (lista)": ("/transformations", {}),
    }

    for titulo, (path, params) in checks.items():
        try:
            data = get(path, **params)
        except Exception as exc:  # noqa: BLE001
            report.append(f"\n## {titulo}\n\nERRO: `{exc}`\n")
            print(f"[ERRO] {titulo}: {exc}")
            continue

        (RAW_DIR / f"amostra_{path.strip('/').replace('/', '_')}_{stamp}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        report.append(f"\n## {titulo}\n")
        if isinstance(data, dict) and "meta" in data:
            report.append(f"Paginação (`meta`): `{json.dumps(data['meta'])}`\n")

        itens = items_of(data)
        report.append(f"Itens retornados: {len(itens)}\n")
        if itens:
            report.append("\n| Campo | Tipo | Exemplo |\n| --- | --- | --- |")
            for campo, tipo, ex in describe(itens[0]):
                report.append(f"| `{campo}` | {tipo} | {ex.replace('|', '/')} |")
            report.append("")

        if path == "/characters":
            report.append("\nExemplos de ki (texto cru, precisa converter para número):\n")
            for c in itens:
                report.append(f"- {c.get('name')}: ki=`{c.get('ki')}` · maxKi=`{c.get('maxKi')}`")
            report.append("")

        print(f"[OK]   {titulo}: {len(itens)} item(ns)")

    out = DOCS_DIR / "api_campos_detectados.md"
    out.write_text("\n".join(report), encoding="utf-8")
    print(f"\nRelatório salvo em {out}")


if __name__ == "__main__":
    main()
