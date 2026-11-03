"""Conexão com o SQL Server e helpers de log (ctl.sp_log)."""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def get_engine() -> Engine:
    server = os.getenv("SQL_SERVER", "localhost")
    database = os.getenv("SQL_DATABASE", "DBZ_BI")
    driver = os.getenv("SQL_DRIVER", "ODBC Driver 18 for SQL Server")
    user, password = os.getenv("SQL_USER"), os.getenv("SQL_PASSWORD")

    auth = f"UID={user};PWD={password}" if user else "Trusted_Connection=yes"
    odbc = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};{auth};TrustServerCertificate=yes"
    return create_engine(f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc)}")


def log_inicio(engine: Engine, etapa: str) -> int:
    sql = text(
        "SET NOCOUNT ON; DECLARE @id INT; "
        "EXEC ctl.sp_log @etapa = :etapa, @status = 'INICIADO', @id_execucao = @id OUTPUT; "
        "SELECT @id;"
    )
    with engine.begin() as conn:
        return int(conn.execute(sql, {"etapa": etapa}).scalar_one())


def log_fim(engine: Engine, id_execucao: int, etapa: str, status: str,
            linhas: int | None = None, mensagem: str | None = None) -> None:
    sql = text(
        "EXEC ctl.sp_log @etapa = :etapa, @status = :status, @linhas_afetadas = :linhas, "
        "@mensagem = :msg, @id_execucao = :id"
    )
    with engine.begin() as conn:
        conn.execute(sql, {"etapa": etapa, "status": status, "linhas": linhas,
                           "msg": (mensagem or "")[:4000], "id": id_execucao})
