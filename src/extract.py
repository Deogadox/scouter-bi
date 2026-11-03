"""
Scouter BI — extract.py (Fase 1)

Extrai a Dragon Ball API e carrega o schema stg do SQL Server.

  1. /planets e /characters paginados (segue links.next)
  2. /characters/{id} para cada personagem (planeta de origem + transformações)
  3. /transformations
  4. JSON cru salvo em data/raw/<AAAAMMDD_HHMMSS>/
  5. TRUNCATE + INSERT nas tabelas stg, com log em ctl.log_execucao

Uso:
  python -m src.extract              # extrai e carrega
  python -m src.extract --sem-banco  # só extrai e salva o JSON
  python -m src.extract --de-arquivo data/raw/20261102_223000  # recarrega a partir do JSON salvo
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from dotenv import load_dotenv

from src.ki_parser import classificar_ki, parse_ki

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
RAW_DIR = ROOT / "data" / "raw"
LOG_DIR = ROOT / "logs"

BASE_URL = os.getenv("API_BASE_URL", "https://dragonball-api.com/api").rstrip("/")
PAGE_LIMIT = int(os.getenv("API_PAGE_LIMIT", "100"))
TIMEOUT = int(os.getenv("API_TIMEOUT_SECONDS", "15"))

log = logging.getLogger("scouter.extract")


# --------------------------------------------------------------------------- API
def sessao_http() -> requests.Session:
    retry = Retry(total=5, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=("GET",))
    s = requests.Session()
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers["User-Agent"] = "scouter-bi/1.0 (+https://github.com/Deogadox/scouter-bi)"
    return s


def get_json(s: requests.Session, url: str, **params):
    resp = s.get(url, params=params or None, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_paginado(s: requests.Session, path: str) -> list[dict]:
    """Segue links.next até o fim. Aceita também resposta em lista simples."""
    itens: list[dict] = []
    payload = get_json(s, f"{BASE_URL}{path}", page=1, limit=PAGE_LIMIT)
    while True:
        if isinstance(payload, list):
            return itens + payload
        itens += payload.get("items", [])
        prox = (payload.get("links") or {}).get("next")
        if not prox:
            break
        payload = get_json(s, prox)
    total = (payload.get("meta") or {}).get("totalItems")
    if total is not None and total != len(itens):
        log.warning("%s: meta.totalItems=%s, recebidos=%s", path, total, len(itens))
    return itens


def extrair() -> dict[str, list]:
    s = sessao_http()
    log.info("Extraindo planetas...")
    planetas = get_paginado(s, "/planets")
    log.info("Extraindo lista de personagens...")
    lista = get_paginado(s, "/characters")
    log.info("Extraindo detalhe de %d personagens...", len(lista))
    detalhes = [get_json(s, f"{BASE_URL}/characters/{c['id']}") for c in lista]
    log.info("Extraindo transformações...")
    transformacoes = get_paginado(s, "/transformations")
    return {"planets": planetas, "characters": detalhes, "transformations": transformacoes}


# ------------------------------------------------------------------ arquivos cru
def salvar_raw(dados: dict[str, list], pasta: Path) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    for nome, conteudo in dados.items():
        (pasta / f"{nome}.json").write_text(json.dumps(conteudo, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("JSON cru salvo em %s", pasta)


def ler_raw(pasta: Path) -> dict[str, list]:
    return {n: json.loads((pasta / f"{n}.json").read_text(encoding="utf-8"))
            for n in ("planets", "characters", "transformations")}


# ---------------------------------------------------------------- transformação
def _sem_nan(df: pd.DataFrame) -> pd.DataFrame:
    return df.astype(object).where(pd.notnull(df), None)


def _dt(v):
    return pd.to_datetime(v).to_pydatetime().replace(tzinfo=None) if v else None


def montar_tabelas(dados: dict[str, list], id_execucao: int) -> dict[str, pd.DataFrame]:
    planeta = pd.DataFrame([{
        "id_api": p["id"], "nome": (p["name"] or "").strip(), "destruido": p.get("isDestroyed"),
        "descricao": p.get("description"), "url_imagem": p.get("image"),
        "deleted_at": _dt(p.get("deletedAt")), "id_execucao": id_execucao,
    } for p in dados["planets"]])

    personagem, ponte = [], []
    for c in dados["characters"]:
        personagem.append({
            "id_api": c["id"], "nome": (c["name"] or "").strip(), "raca": c.get("race"), "genero": c.get("gender"),
            "afiliacao": c.get("affiliation"),
            "ki_texto": c.get("ki"), "ki_valor": parse_ki(c.get("ki")),
            "ki_status": classificar_ki(c.get("ki")),
            "ki_max_texto": c.get("maxKi"), "ki_max_valor": parse_ki(c.get("maxKi")),
            "ki_max_status": classificar_ki(c.get("maxKi")),
            "id_planeta_origem": (c.get("originPlanet") or {}).get("id"),
            "descricao": c.get("description"), "url_imagem": c.get("image"),
            "deleted_at": _dt(c.get("deletedAt")), "id_execucao": id_execucao,
        })
        for ordem, t in enumerate(c.get("transformations") or [], start=1):
            ponte.append({"id_personagem_api": c["id"], "id_transformacao_api": t["id"],
                          "ordem": ordem, "id_execucao": id_execucao})

    transformacao = pd.DataFrame([{
        "id_api": t["id"], "nome": (t["name"] or "").strip(), "ki_texto": t.get("ki"),
        "ki_valor": parse_ki(t.get("ki")), "ki_status": classificar_ki(t.get("ki")),
        "url_imagem": t.get("image"), "deleted_at": _dt(t.get("deletedAt")), "id_execucao": id_execucao,
    } for t in dados["transformations"]])

    df_personagem = pd.DataFrame(personagem)
    df_personagem["id_planeta_origem"] = df_personagem["id_planeta_origem"].astype("Int64")

    tabelas = {
        "planeta": planeta,
        "personagem": df_personagem,
        "transformacao": transformacao,
        "personagem_transformacao": pd.DataFrame(ponte).drop_duplicates(
            ["id_personagem_api", "id_transformacao_api"]),
    }
    return {k: _sem_nan(v) for k, v in tabelas.items()}


def checar_qualidade(tabelas: dict[str, pd.DataFrame]) -> list[str]:
    avisos = []
    for nome, df in tabelas.items():
        if df.empty:
            avisos.append(f"{nome}: nenhuma linha")
        if "id_api" in df and df["id_api"].duplicated().any():
            avisos.append(f"{nome}: id_api duplicado")
    for nome, pares in {"personagem": [("ki_texto", "ki_status"), ("ki_max_texto", "ki_max_status")],
                        "transformacao": [("ki_texto", "ki_status")]}.items():
        df = tabelas[nome]
        for txt, st in pares:
            for _, r in df[df[st] == "invalido"].iterrows():
                avisos.append(f"{nome}.{txt} inválido: id={r['id_api']} valor='{r[txt]}'")
            contagem = df[st].value_counts().to_dict()
            log.info("%s.%s: %s", nome, st, contagem)
    return avisos


# ------------------------------------------------------------------------ carga
def carregar(engine, tabelas: dict[str, pd.DataFrame]) -> int:
    from sqlalchemy import text
    ordem = ["planeta", "personagem", "transformacao", "personagem_transformacao"]
    total = 0
    with engine.begin() as conn:  # tudo ou nada
        for nome in ordem:
            conn.execute(text(f"TRUNCATE TABLE stg.{nome};"))
            tabelas[nome].to_sql(nome, conn, schema="stg", if_exists="append", index=False, chunksize=200)
            log.info("stg.%s: %d linhas", nome, len(tabelas[nome]))
            total += len(tabelas[nome])
    return total


# ------------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Extração da Dragon Ball API para o stg")
    ap.add_argument("--sem-banco", action="store_true", help="só extrai e salva o JSON")
    ap.add_argument("--de-arquivo", type=Path, help="carrega a partir de uma pasta em data/raw")
    args = ap.parse_args(argv)

    LOG_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(sys.stdout),
                                  logging.FileHandler(LOG_DIR / f"extract_{stamp}.log", encoding="utf-8")])

    engine = id_exec = None
    etapa = "fase1_extracao_api"
    try:
        if not args.sem_banco:
            from src.db import get_engine, log_inicio
            engine = get_engine()
            id_exec = log_inicio(engine, etapa)

        if args.de_arquivo:
            dados = ler_raw(args.de_arquivo)
        else:
            dados = extrair()
            salvar_raw(dados, RAW_DIR / stamp)

        tabelas = montar_tabelas(dados, id_exec or 0)
        avisos = checar_qualidade(tabelas)
        for a in avisos:
            log.warning(a)

        if args.sem_banco:
            log.info("Modo --sem-banco: %s",
                     ", ".join(f"{k}={len(v)}" for k, v in tabelas.items()))
            return 0

        linhas = carregar(engine, tabelas)
        from src.db import log_fim
        log_fim(engine, id_exec, etapa, "SUCESSO", linhas,
                f"{len(avisos)} aviso(s) de qualidade" if avisos else "ok")
        log.info("Carga concluída: %d linhas, %d aviso(s)", linhas, len(avisos))
        return 0
    except Exception as exc:  # noqa: BLE001
        log.exception("Falha na extração")
        if engine is not None and id_exec:
            from src.db import log_fim
            log_fim(engine, id_exec, etapa, "ERRO", None, repr(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
