"""
Scouter BI — load_curadoria.py (Fase 2)

Valida os CSVs de data/curadoria/ e carrega no stg (stg.cur_*).
A validação roda antes do banco: se falhar, nada é carregado.

Uso:
  python -m src.load_curadoria              # valida e carrega
  python -m src.load_curadoria --so-validar # só valida (não precisa de banco)
"""
from __future__ import annotations

import argparse
import logging
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CUR_DIR = ROOT / "data" / "curadoria"

FONTES = {"canonico", "guia_oficial", "estimado"}
RESULTADOS = {"vitoria", "empate"}

log = logging.getLogger("scouter.curadoria")


def ler(nome: str) -> pd.DataFrame:
    df = pd.read_csv(CUR_DIR / f"{nome}.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    return df.apply(lambda col: col.str.strip())


def _int(v: str):
    return int(v) if v not in ("", None) else None


def _dec(v: str):
    try:
        return Decimal(v)
    except (InvalidOperation, TypeError):
        return None


def validar(t: dict[str, pd.DataFrame]) -> list[str]:
    erros: list[str] = []
    saga, extra, poder, luta = t["dim_saga"], t["personagem_extra"], t["fato_poder"], t["fato_luta"]
    sagas, extras = set(saga["codigo_saga"]), set(extra["codigo_extra"])

    if saga["codigo_saga"].duplicated().any():
        erros.append("dim_saga: codigo_saga duplicado")
    if saga["ordem_cronologica"].duplicated().any():
        erros.append("dim_saga: ordem_cronologica duplicada")

    for i, r in poder.iterrows():
        linha = i + 2  # cabeçalho é a linha 1
        if bool(r["id_personagem_api"]) == bool(r["codigo_extra"]):
            erros.append(f"fato_poder linha {linha}: preencha id_personagem_api OU codigo_extra")
        if r["codigo_extra"] and r["codigo_extra"] not in extras:
            erros.append(f"fato_poder linha {linha}: codigo_extra '{r['codigo_extra']}' não existe em personagem_extra")
        if r["codigo_saga"] not in sagas:
            erros.append(f"fato_poder linha {linha}: saga '{r['codigo_saga']}' não existe")
        if r["fonte_valor"] not in FONTES:
            erros.append(f"fato_poder linha {linha}: fonte_valor '{r['fonte_valor']}' inválida")
        v = _dec(r["nivel_poder"])
        if v is None or v < 0:
            erros.append(f"fato_poder linha {linha}: nivel_poder '{r['nivel_poder']}' inválido")
    dup = poder[poder.duplicated(["personagem", "codigo_saga", "forma"], keep=False)]
    for _, r in dup.iterrows():
        erros.append(f"fato_poder: duplicado {r['personagem']} / {r['codigo_saga']} / {r['forma']}")

    chaves_poder = set(zip(poder["personagem"], poder["codigo_saga"], poder["forma"]))
    for _, r in luta.iterrows():
        if r["codigo_saga"] not in sagas:
            erros.append(f"fato_luta {r['id_luta']}: saga '{r['codigo_saga']}' não existe")
        if r["resultado"] not in RESULTADOS:
            erros.append(f"fato_luta {r['id_luta']}: resultado '{r['resultado']}' inválido")
        for lado in ("vencedor", "perdedor"):
            if (r[lado], r["codigo_saga"], r[f"forma_{lado}"]) not in chaves_poder:
                erros.append(f"fato_luta {r['id_luta']}: {lado} '{r[lado]}' ({r[f'forma_{lado}']}) "
                             f"sem nível de poder em {r['codigo_saga']}")
    if luta["id_luta"].duplicated().any():
        erros.append("fato_luta: id_luta duplicado")
    return erros


def consistencia_lutas(t: dict[str, pd.DataFrame]) -> list[str]:
    """Lutas em que o vencedor tem poder menor que o perdedor (zebras)."""
    p = t["fato_poder"]
    pw = {(r.personagem, r.codigo_saga, r.forma): Decimal(r.nivel_poder) for r in p.itertuples()}
    zebras = []
    for r in t["fato_luta"].itertuples():
        v = pw.get((r.vencedor, r.codigo_saga, r.forma_vencedor))
        d = pw.get((r.perdedor, r.codigo_saga, r.forma_perdedor))
        if r.resultado == "vitoria" and v is not None and d is not None and v < d:
            zebras.append(f"luta {r.id_luta}: {r.vencedor} ({v:,.0f}) venceu {r.perdedor} ({d:,.0f}) — {r.observacao}")
    return zebras


def _col(df: pd.DataFrame, nome: str, fn) -> None:
    """Aplica fn mantendo dtype object (evita int virar float quando há None)."""
    df[nome] = pd.Series([fn(v) for v in df[nome]], index=df.index, dtype=object)


def _vazio(v: str):
    return v or None


def para_banco(t: dict[str, pd.DataFrame], id_exec: int) -> dict[str, pd.DataFrame]:
    s = t["dim_saga"].copy()
    for c in ("ordem_cronologica", "episodio_inicio", "episodio_fim"):
        _col(s, c, _int)
    _col(s, "filler", lambda v: v in ("1", "true", "True"))

    e = t["personagem_extra"].copy()
    for c in ("raca", "genero", "afiliacao"):
        _col(e, c, _vazio)

    p = t["fato_poder"].copy()
    p.insert(0, "linha_csv", range(2, len(p) + 2))
    for c in ("id_personagem_api", "id_transformacao_api"):
        _col(p, c, _int)
    for c in ("codigo_extra", "referencia", "observacao"):
        _col(p, c, _vazio)
    _col(p, "nivel_poder", _dec)

    lu = t["fato_luta"].copy()
    for c in ("id_luta", "vencedor_id_api", "perdedor_id_api", "episodio"):
        _col(lu, c, _int)
    for c in ("vencedor_codigo_extra", "perdedor_codigo_extra", "observacao"):
        _col(lu, c, _vazio)

    saida = {"cur_saga": s, "cur_personagem_extra": e, "cur_poder": p, "cur_luta": lu}
    for df in saida.values():
        df["id_execucao"] = id_exec
    return saida


def carregar(engine, tabelas: dict[str, pd.DataFrame]) -> int:
    from sqlalchemy import text
    total = 0
    with engine.begin() as conn:
        for nome, df in tabelas.items():
            conn.execute(text(f"TRUNCATE TABLE stg.{nome};"))
            df.to_sql(nome, conn, schema="stg", if_exists="append", index=False, chunksize=200)
            log.info("stg.%s: %d linhas", nome, len(df))
            total += len(df)
    return total


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-validar", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(sys.stdout)])

    t = {n: ler(n) for n in ("dim_saga", "personagem_extra", "fato_poder", "fato_luta")}
    log.info("CSVs lidos: %s", ", ".join(f"{k}={len(v)}" for k, v in t.items()))
    log.info("fato_poder por fonte: %s", t["fato_poder"]["fonte_valor"].value_counts().to_dict())

    erros = validar(t)
    for e in erros:
        log.error(e)
    for z in consistencia_lutas(t):
        log.warning("Zebra: %s", z)
    if erros:
        log.error("%d erro(s) de validação; nada foi carregado", len(erros))
        return 1
    log.info("Validação OK")
    if args.so_validar:
        return 0

    from src.db import get_engine, log_fim, log_inicio
    engine = get_engine()
    etapa = "fase2_carga_curadoria"
    id_exec = log_inicio(engine, etapa)
    try:
        linhas = carregar(engine, para_banco(t, id_exec))
        log_fim(engine, id_exec, etapa, "SUCESSO", linhas, "ok")
        log.info("Curadoria carregada: %d linhas", linhas)
        return 0
    except Exception as exc:  # noqa: BLE001
        log.exception("Falha na carga da curadoria")
        log_fim(engine, id_exec, etapa, "ERRO", None, repr(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
