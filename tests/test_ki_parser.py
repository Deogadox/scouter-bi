from decimal import Decimal

import pytest

from src.ki_parser import classificar_ki, ki_log10, parse_ki


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        # milhar com ponto (formato real da API)
        ("60.000.000", Decimal("60000000")),
        ("54.000.000", Decimal("54000000")),
        ("530.000", Decimal("530000")),
        ("500.000.000", Decimal("500000000")),
        ("0", Decimal("0")),
        # escala por extenso, ponto decimal
        ("90 Septillion", Decimal("90") * 10**24),
        ("19.84 Septillion", Decimal("19840000000000000000000000")),
        ("52.71 Septillion", Decimal("52710000000000000000000000")),
        ("3 Billion", Decimal("3000000000")),
        ("1.5 million", Decimal("1500000")),
        # formatos reais encontrados na carga de 2026-11-02
        ("15 septillion", Decimal("15") * 10**24),
        ("37.4 septllion", Decimal("374") * 10**23),
        ("1.2 octillion", Decimal("12") * 10**26),
        # robustez
        ("  2.000.000  ", Decimal("2000000")),
        (9000, Decimal("9000")),
    ],
)
def test_parse_ki_validos(entrada, esperado):
    assert parse_ki(entrada) == esperado


@pytest.mark.parametrize("entrada", [None, "", "Unknown", "muito forte", "5 Zillion", "1.2.3 Billion"])
def test_parse_ki_invalidos(entrada):
    assert parse_ki(entrada) is None


def test_septillion_estoura_bigint():
    assert parse_ki("90 Septillion") > 2**63 - 1


def test_ki_log10():
    assert ki_log10(parse_ki("60.000.000")) == pytest.approx(7.778, abs=1e-3)
    assert ki_log10(Decimal(0)) is None
    assert ki_log10(None) is None


@pytest.mark.parametrize(
    "entrada, status",
    [
        ("60.000.000", "numerico"),
        ("37.4 septllion", "numerico"),
        ("unknown", "desconhecido"),
        (None, "desconhecido"),
        ("969 Googolplex", "incomensuravel"),
        ("muito forte", "invalido"),
    ],
)
def test_classificar_ki(entrada, status):
    assert classificar_ki(entrada) == status
