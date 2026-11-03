# Scouter BI — Dragon Ball Z no Power BI

Relatório Power BI jogável sobre o universo Dragon Ball Z, sustentado por um pipeline de dados próprio:

```
Dragon Ball API ─► Python (extração) ─► SQL Server (stg → dw) ─► Power BI (modelo estrela + DAX) ─► 6 páginas HTML jogáveis
                         ▲
              CSV de curadoria (poder, sagas, lutas)
```

## Stack

| Camada | Tecnologia |
| --- | --- |
| Extração | Python 3.11+, requests, pandas |
| Armazenamento | SQL Server 2022 Developer (banco `DBZ_BI`) |
| Transformação | Stored procedures T-SQL (schemas `stg`, `dw`, `ctl`) |
| Modelo | Power BI (esquema estrela, DAX, projeto PBIP em TMDL/PBIR) |
| Visualização | HTML, CSS e JavaScript dentro do visual HTML Content |

## Estrutura

```
scouter-bi/
├── src/                 # scripts Python (extração e carga)
├── sql/                 # DDL e procedures, numerados na ordem de execução
├── data/
│   ├── raw/             # JSON cru da API (não versionado)
│   └── curadoria/       # CSVs curados manualmente (versionados)
├── powerbi/             # projeto .pbip (modelo TMDL + relatório PBIR)
│   └── html/            # código-fonte das 6 páginas (HTML/CSS/JS)
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

# 7. Fase 4 (opcional, só se mexer nas páginas): minifica o HTML e regera as medidas e páginas do PBIP
npm install
npm run build
powershell -ExecutionPolicy Bypass -File scripts\aplicar_relatorio.ps1
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

| Página | O que faz |
| --- | --- |
| **Scouter** | Ficha de cada guerreiro: leitura do scouter por saga e forma, evolução do poder, formas e lutas canônicas |
| **Arena** | Batalha jogável entre quaisquer dois guerreiros. O motor é calibrado na mesma curva de chance do modelo (A² ÷ (A² + B²)) e simula 1.000 lutas |
| **Escalada** | A inflação de poder saga a saga, em escala log, com o campeão de cada saga e o tamanho de cada salto |
| **Quiz** | 10 perguntas geradas a partir dos dados, com tempo, sequência e patentes |
| **Radar** | Minigame do Radar do Dragão: ache as 7 esferas antes de a bateria acabar |
| **Bastidores** | O pipeline, a curadoria e a acurácia do modelo de poder |

**Como funciona:** a tabela `_Paginas` tem as medidas `[JSON *]`, que serializam o modelo (sagas, personagens, poder, lutas) em um objeto JavaScript, e uma medida `[HTML <Página>]` por página, com o HTML/CSS/JS minificado e o `[JSON Dados]` injetado. Cada página do relatório é um visual [HTML Content](https://html-content.com) em tela cheia + o navegador de páginas nativo. O código-fonte das páginas está em `powerbi/html/`; `npm run build` regera as medidas e as páginas a partir dele.

Os níveis de poder seguem a [metodologia documentada](docs/metodologia_poder.md): cada valor é marcado como `canonico`, `guia_oficial` ou `estimado`.

## Fonte dos dados

- [Dragon Ball API](https://web.dragonball-api.com/documentation) — personagens, planetas e transformações.
- Curadoria própria — níveis de poder por saga, sagas e lutas canônicas. A coluna `fonte_valor` indica se o número é **canônico** ou **estimado**.

## Aviso legal

Projeto pessoal, sem fins comerciais. Dragon Ball © Bird Studio / Shueisha, Toei Animation. Imagens e nomes pertencem aos detentores dos direitos.

## Autor

Felipe Rios Miranda — [github.com/Deogadox](https://github.com/Deogadox)
