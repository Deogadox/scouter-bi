"""
Conversão do campo `ki` da Dragon Ball API (texto) para número.

A API mistura dois formatos incompatíveis:
  - "60.000.000"        -> ponto é separador de MILHAR
  - "19.84 Septillion"  -> ponto é separador DECIMAL + escala por extenso

Regra: se houver palavra de escala, o ponto é decimal; senão, os pontos
são milhar. Valores chegam a 10^25 (estoura BIGINT), por isso Decimal.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

ESCALAS: dict[str, int] = {
    "thousand": 3,
    "million": 6,
    "billion": 9,
    "trillion": 12,
    "quadrillion": 15,
    "quintillion": 18,
    "sextillion": 21,
    "septillion": 24,
    "octillion": 27,
    "nonillion": 30,
    "decillion": 33,
}

# Erros de digitação encontrados na API real (carga de 2026-11-02)
ALIASES: dict[str, str] = {
    "septllion": "septillion",
}

# Escalas sem representação numérica possível (googolplex = 10^(10^100))
INCOMENSURAVEIS = {"googolplex", "googol", "infinite", "infinity"}

DESCONHECIDOS = {"unknown", "desconhecido", "?", "n/a", ""}

_RE_ESCALA = re.compile(r"^\s*([\d.,]+)\s*([a-zA-Z]+)\s*$")
_RE_MILHAR = re.compile(r"^\s*\d{1,3}(?:[.,]\d{3})*\s*$")


def parse_ki(valor: str | int | float | None) -> Decimal | None:
    """Retorna o ki como Decimal inteiro, ou None se não for interpretável."""
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return Decimal(str(valor)).quantize(Decimal(1))

    texto = str(valor).strip()
    if not texto:
        return None

    # Caso 1: número + escala ("90 Septillion", "19.84 Septillion", "3 Billion")
    m = _RE_ESCALA.match(texto)
    if m:
        numero, escala = m.group(1).replace(",", "."), m.group(2).lower()
        escala = ALIASES.get(escala, escala)
        if escala not in ESCALAS:
            return None
        try:
            return (Decimal(numero) * (Decimal(10) ** ESCALAS[escala])).quantize(Decimal(1))
        except InvalidOperation:
            return None

    # Caso 2: inteiro com separador de milhar ("60.000.000", "0")
    if _RE_MILHAR.match(texto):
        return Decimal(re.sub(r"[.,\s]", "", texto))

    return None


def classificar_ki(valor: str | int | float | None) -> str:
    """numerico | desconhecido | incomensuravel | invalido"""
    if parse_ki(valor) is not None:
        return "numerico"
    texto = "" if valor is None else str(valor).strip().lower()
    if texto in DESCONHECIDOS:
        return "desconhecido"
    if texto.split() and texto.split()[-1] in INCOMENSURAVEIS:
        return "incomensuravel"
    return "invalido"


def ki_log10(valor: Decimal | None) -> float | None:
    """log10 do ki — útil para eixos e barras em escala logarítmica no Power BI."""
    if valor is None or valor <= 0:
        return None
    return float(valor.log10())
