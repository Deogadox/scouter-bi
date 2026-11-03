# Scouter BI — Dragon Ball Z no Power BI

Relatório Power BI jogável sobre o universo Dragon Ball Z, sustentado por um pipeline de dados próprio:

```
Dragon Ball API ─► Python (extração) ─► SQL Server (stg → dw) ─► Power BI (modelo estrela + DAX) ─► Publicar na web
                         ▲
              CSV de curadoria (poder, sagas, lutas)
```

## Stack

| Camada | Tecnologia |
| --- | --- |
| Extração | Python 3.11+, requests, pandas |
| Armazenamento | SQL Server 2022 Developer (banco `DBZ_BI`) |
| Transformação | Stored procedures T-SQL (schemas `stg`, `dw`, `ctl`) |
| Visualização | Power BI Desktop (DAX, SVG dinâmico) |

## Estrutura

```
scouter-bi/
├── src/                 # scripts Python (extração e carga)
├── sql/                 # DDL e procedures, numerados na ordem de execução
├── data/
│   ├── raw/             # JSON cru da API (não versionado)
│   └── curadoria/       # CSVs curados manualmente (versionados)
├── powerbi/             # .pbip / .pbix
├── docs/                # documentação (campos da API, metodologia)
└── scripts/             # automações PowerShell
```

## Como rodar

```powershell
# 1. Ambiente Python
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Variáveis de ambiente
Copy-Item .env.example .env   # ajuste servidor e banco

# 3. Banco de dados
sqlcmd -S localhost -E -i sql\00_create_database.sql

# 4. Conferir a API
python src\check_api.py

# 5. Fase 1: tabelas de staging + extração
sqlcmd -S localhost -E -C -i sql\01_stg_tables.sql
python -m pytest -q
python -m src.extract

# 6. Fase 2: curadoria (CSVs) -> stg -> dw
powershell -ExecutionPolicy Bypass -File scripts\run_fase2.ps1
```

## Modelo de dados (schema `dw`)

| Tabela | Grão | Origem |
| --- | --- | --- |
| `dim_personagem` | personagem | API + extras da curadoria |
| `dim_saga` | saga do Dragon Ball Z | curadoria |
| `dim_transformacao` | personagem × forma | curadoria + API |
| `dim_planeta` | planeta | API |
| `fato_poder` | personagem × saga × forma | curadoria |
| `fato_luta` | luta canônica | curadoria |

## Power BI

O relatório fica em `powerbi/DBZ_BI.pbip` (formato de projeto, versionável). Abra no Power BI Desktop e clique em **Atualizar**. Os parâmetros `Servidor` e `Banco` apontam para `localhost` / `DBZ_BI`. As medidas estão documentadas em [docs/medidas_dax.md](docs/medidas_dax.md).

Os níveis de poder seguem a [metodologia documentada](docs/metodologia_poder.md): cada valor é marcado como `canonico`, `guia_oficial` ou `estimado`.

## Fonte dos dados

- [Dragon Ball API](https://web.dragonball-api.com/documentation) — personagens, planetas e transformações.
- Curadoria própria — níveis de poder por saga, sagas e lutas canônicas. A coluna `fonte_valor` indica se o número é **canônico** ou **estimado**.

## Aviso legal

Projeto pessoal, sem fins comerciais. Dragon Ball © Bird Studio / Shueisha, Toei Animation. Imagens e nomes pertencem aos detentores dos direitos.

## Autor

Felipe Rios Miranda — [github.com/Deogadox](https://github.com/Deogadox)
