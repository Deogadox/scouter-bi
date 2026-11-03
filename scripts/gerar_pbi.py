"""Gera a camada Power BI das páginas HTML (Fase 4).

Lê as páginas minificadas em powerbi/html/dist (saída de gerar_html.py) e escreve, dentro da pasta do PBIP:
  - SemanticModel/definition/tables/_Paginas.tmdl : medidas [JSON *] que serializam o modelo e [HTML <Página>]
  - SemanticModel/definition/model.tmdl           : acrescenta `ref table _Paginas`
  - Report/definition/pages/<id>/...              : uma página por app (HTML Content em tela cheia + navegador)
  - Report/definition/pages/pages.json            : ordem das páginas
  - Report/definition/report.json                 : registra o visual HTML Content (AppSource)

Uso:  python scripts/gerar_pbi.py <pasta powerbi do PBIP> [pasta dist]
"""
import hashlib, json, re, sys, uuid
from pathlib import Path

RAIZ = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "powerbi"
DIST = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parents[1] / "powerbi" / "html" / "dist"
MODELO = RAIZ / "DBZ_BI.SemanticModel" / "definition"
REL = RAIZ / "DBZ_BI.Report" / "definition"

HTML_VISUAL = "htmlContent443BE3AD55E043BF878BED274D3A6855"
PAGINAS = [  # (arquivo, nome da página, descrição da medida)
    ("scouter", "Scouter", "Ficha de cada guerreiro: leitura do scouter por saga e forma, evolução e lutas."),
    ("arena", "Arena", "Simulador de batalha jogável: o motor usa a mesma curva de chance do modelo."),
    ("escalada", "Escalada", "A inflação de poder saga a saga, em escala log, com o campeão de cada saga."),
    ("quiz", "Quiz", "Quiz de 10 perguntas geradas a partir dos dados do modelo."),
    ("radar", "Radar", "Minigame: encontre as 7 esferas do dragão com o radar."),
    ("bastidores", "Bastidores", "Como o projeto foi construído: pipeline, curadoria e métricas do modelo."),
]
TAM_LITERAL = 3000  # cada literal de texto do DAX fica abaixo deste tamanho


def hexid(*partes, n=20):
    return hashlib.md5("scouterbi/".join(partes).encode()).hexdigest()[:n]


def tag(nome):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "scouterbi/_Paginas/" + nome))


def bloco(expr, nivel=3):
    """Indenta uma expressão DAX multi-linha no padrão do TMDL salvo pelo Desktop."""
    return "\n".join("\t" * nivel + l if l.strip() else "" for l in expr.strip("\n").split("\n"))


# ----------------------------------------------------------------------------------------------- medidas JSON
# Truque: os textos são delimitados por ¤ (UNICHAR 164) enquanto o registro é montado; depois o JSON inteiro
# é escapado uma única vez (\ ' < quebras de linha) e só então ¤ vira aspas simples. Assim o escape fica em
# um lugar só por medida, em vez de repetido em cada campo.
ESCAPE = r"""VAR seguro =
    SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE (
        bruto, "\", "\\" ), "'", "\'" ), "<", "\u003c" ), UNICHAR ( 10 ), " " ), UNICHAR ( 13 ), "" )
RETURN
    "[" & SUBSTITUTE ( seguro, Q, "'" ) & "]"
"""

MEDIDAS_JSON = [
    ("JSON Sagas", "Sagas do Z em ordem cronológica: {o, n, a, e1, e2, f}.", """
VAR Q = UNICHAR ( 164 )
VAR bruto =
    CONCATENATEX (
        dim_saga,
        "{o:" & FORMAT ( dim_saga[ordem_cronologica], "0" )
            & ",n:" & Q & dim_saga[nome] & Q
            & ",a:" & Q & dim_saga[arco] & Q
            & ",e1:" & FORMAT ( COALESCE ( dim_saga[episodio_inicio], 0 ), "0" )
            & ",e2:" & FORMAT ( COALESCE ( dim_saga[episodio_fim], 0 ), "0" )
            & ",f:" & IF ( dim_saga[filler], "1", "0" ) & "}",
        ",",
        dim_saga[ordem_cronologica], ASC
    )
""" + ESCAPE),
    ("JSON Personagens", "Personagens que têm leitura de poder: {id, n, r, af, pl, img, orig}.", """
VAR Q = UNICHAR ( 164 )
VAR comPoder = FILTER ( dim_personagem, NOT ISEMPTY ( RELATEDTABLE ( fato_poder ) ) )
VAR bruto =
    CONCATENATEX (
        comPoder,
        "{id:" & FORMAT ( dim_personagem[sk_personagem], "0" )
            & ",n:" & Q & TRIM ( dim_personagem[nome] ) & Q
            & ",r:" & Q & dim_personagem[raca] & Q
            & ",af:" & Q & dim_personagem[afiliacao] & Q
            & ",pl:" & Q & TRIM ( RELATED ( dim_planeta[nome] ) ) & Q
            & ",img:" & Q & dim_personagem[url_imagem] & Q
            & ",orig:" & Q & dim_personagem[origem] & Q & "}",
        ",",
        dim_personagem[sk_personagem], ASC
    )
""" + ESCAPE),
    ("JSON Poder", "Uma linha por personagem × saga × forma: {p, s, f, fi, v, src, ob}. s = ordem da saga.", """
VAR Q = UNICHAR ( 164 )
VAR bruto =
    CONCATENATEX (
        fato_poder,
        "{p:" & FORMAT ( fato_poder[sk_personagem], "0" )
            & ",s:" & FORMAT ( RELATED ( dim_saga[ordem_cronologica] ), "0" )
            & ",f:" & Q & RELATED ( dim_transformacao[forma] ) & Q
            & ",fi:" & Q & RELATED ( dim_transformacao[url_imagem] ) & Q
            & ",v:" & FORMAT ( fato_poder[nivel_poder], "0" )
            & ",src:" & Q & LOWER ( LEFT ( fato_poder[fonte_valor], 1 ) ) & Q
            & ",ob:" & Q & fato_poder[observacao] & Q & "}",
        ",",
        fato_poder[sk_personagem], ASC,
        fato_poder[sk_saga], ASC,
        fato_poder[nivel_poder], ASC
    )
""" + ESCAPE),
    ("JSON Transformações", "Transformações da API que a curadoria não usa (galeria): {p, n, img}.", """
VAR Q = UNICHAR ( 164 )
VAR bruto =
    CONCATENATEX (
        FILTER ( dim_transformacao, dim_transformacao[origem] = "api" ),
        "{p:" & FORMAT ( dim_transformacao[sk_personagem], "0" )
            & ",n:" & Q & TRIM ( dim_transformacao[forma] ) & Q
            & ",img:" & Q & dim_transformacao[url_imagem] & Q & "}",
        ",",
        dim_transformacao[sk_personagem], ASC,
        dim_transformacao[ordem], ASC
    )
""" + ESCAPE),
    ("JSON Lutas", "Lutas canônicas: {id, s, v, fv, d, fd, r, z, ob}. v/d = vencedor/perdedor, z = zebra.", """
VAR Q = UNICHAR ( 164 )
VAR bruto =
    CONCATENATEX (
        fato_luta,
        VAR fv = LOOKUPVALUE ( dim_transformacao[forma], dim_transformacao[sk_transformacao], fato_luta[sk_transformacao_vencedor] )
        VAR fd = LOOKUPVALUE ( dim_transformacao[forma], dim_transformacao[sk_transformacao], fato_luta[sk_transformacao_perdedor] )
        RETURN
            "{id:" & FORMAT ( fato_luta[id_luta], "0" )
                & ",s:" & FORMAT ( RELATED ( dim_saga[ordem_cronologica] ), "0" )
                & ",v:" & FORMAT ( fato_luta[sk_vencedor], "0" )
                & ",fv:" & Q & fv & Q
                & ",d:" & FORMAT ( fato_luta[sk_perdedor], "0" )
                & ",fd:" & Q & fd & Q
                & ",r:" & Q & fato_luta[resultado] & Q
                & ",z:" & IF ( fato_luta[zebra], "1", "0" )
                & ",ob:" & Q & fato_luta[observacao] & Q & "}",
        ",",
        fato_luta[id_luta], ASC
    )
""" + ESCAPE),
]

# contagens da página Bastidores (uma linha por indicador)
META = [
    ("nApi", 'COUNTROWS ( FILTER ( dim_personagem, dim_personagem[origem] = "api" ) )'),
    ("nExtra", 'COUNTROWS ( FILTER ( dim_personagem, dim_personagem[origem] = "curadoria" ) )'),
    ("nPl", "COUNTROWS ( dim_planeta )"),
    ("nTr", "DISTINCTCOUNTNOBLANK ( dim_transformacao[id_api] )"),
    ("nPod", "COUNTROWS ( fato_poder )"),
    ("nCan", 'COUNTROWS ( FILTER ( fato_poder, LEFT ( fato_poder[fonte_valor], 1 ) = "c" ) )'),
    ("nGuia", 'COUNTROWS ( FILTER ( fato_poder, LEFT ( fato_poder[fonte_valor], 1 ) = "g" ) )'),
    ("nEst", 'COUNTROWS ( FILTER ( fato_poder, LEFT ( fato_poder[fonte_valor], 1 ) = "e" ) )'),
    ("nLut", "COUNTROWS ( fato_luta )"),
    ("nZeb", "COUNTROWS ( FILTER ( fato_luta, fato_luta[zebra] ) )"),
    ("nVit", 'COUNTROWS ( FILTER ( fato_luta, fato_luta[resultado] = "vitoria" ) )'),
    ("kiDesc", 'COUNTROWS ( FILTER ( dim_personagem, dim_personagem[origem] = "api" && dim_personagem[ki_max_api_status] = "desconhecido" ) )'),
    ("kiInc", 'COUNTROWS ( FILTER ( dim_personagem, dim_personagem[origem] = "api" && dim_personagem[ki_max_api_status] = "incomensuravel" ) )'),
    ("nSagas", "COUNTROWS ( dim_saga )"),
]
expr_meta = '"{"\n' + "\n".join(
    f'    & "{"," if i else ""}{k}:" & FORMAT ( {e} + 0, "0" )' for i, (k, e) in enumerate(META)) + '\n    & "}"'
MEDIDAS_JSON.append(("JSON Meta", "Contagens usadas na página Bastidores: {nApi, nExtra, nPl, nTr, nPod, ...}.", expr_meta))

EXPR_DADOS = """
"{sagas:" & [JSON Sagas]
    & ",per:" & [JSON Personagens]
    & ",pod:" & [JSON Poder]
    & ",tra:" & [JSON Transformações]
    & ",lut:" & [JSON Lutas]
    & ",meta:" & [JSON Meta] & "}"
"""


def literais(texto):
    """Quebra um texto em literais DAX (aspas duplicadas) de até TAM_LITERAL caracteres, um por linha."""
    assert "\n" not in texto and "\r" not in texto, "HTML minificado não pode ter quebra de linha"
    pedacos = [texto[i:i + TAM_LITERAL] for i in range(0, len(texto), TAM_LITERAL)]
    return ['"' + p.replace('"', '""') + '"' for p in pedacos]


def expr_html(arquivo):
    html = (DIST / f"{arquivo}.min.html").read_text(encoding="utf-8").replace("\r", "").replace("\n", " ")
    antes, depois = html.split("__DADOS__")
    partes = literais(antes) + ["dados"] + literais(depois)
    return "VAR dados = [JSON Dados]\nRETURN\n    " + "\n    & ".join(partes)


def medida(nome, desc, expr, pasta):
    nome_tmdl = f"'{nome}'" if re.search(r"[^A-Za-z0-9_]", nome) else nome
    return (f"\t/// {desc}\n\tmeasure {nome_tmdl} =\n{bloco(expr)}\n"
            f"\t\tdisplayFolder: {pasta}\n\t\tlineageTag: {tag(nome)}\n")


def gerar_tmdl():
    m = [medida(n, d, e, "Dados (JSON)") for n, d, e in MEDIDAS_JSON]
    m.append(medida("JSON Dados", "Objeto único com todo o modelo, injetado em cada página HTML como window.D.", EXPR_DADOS, "Dados (JSON)"))
    for arq, nome, desc in PAGINAS:
        m.append(medida(f"HTML {nome}", f"Página {nome}: {desc} HTML/CSS/JS minificados (fonte em powerbi/html).",
                        expr_html(arq), "Páginas"))
    t = ("table _Paginas\n\tlineageTag: " + tag("tabela") + "\n\n" + "\n".join(m) +
         "\n\tcolumn Value\n\t\tdataType: int64\n\t\tisHidden\n\t\tformatString: 0\n\t\tlineageTag: " + tag("Value") +
         "\n\t\tsummarizeBy: none\n\t\tisNameInferred\n\t\tsourceColumn: [Value]\n\n\t\tannotation SummarizationSetBy = Automatic\n\n"
         "\tpartition _Paginas = calculated\n\t\tmode: import\n\t\tsource = {1}\n\n"
         "\tannotation PBI_Id = " + hexid("tabela", n=32) + "\n")
    (MODELO / "tables" / "_Paginas.tmdl").write_text(t, encoding="utf-8")
    modelo = (MODELO / "model.tmdl").read_text(encoding="utf-8")
    if "ref table _Paginas" not in modelo:
        ultimo = list(re.finditer(r"^ref table .*$", modelo, re.M))[-1]
        modelo = modelo[:ultimo.end()] + "\nref table _Paginas" + modelo[ultimo.end():]
        (MODELO / "model.tmdl").write_text(modelo, encoding="utf-8")
    return len(t)


# ----------------------------------------------------------------------------------------------- relatório
L = lambda v: {"expr": {"Literal": {"Value": v}}}
COR = lambda c: {"solid": {"color": L(f"'{c}'")}}
SEM = {k: [{"properties": {"show": L("false")}}] for k in ("title", "subTitle", "dropShadow", "visualHeader", "background", "border")}
SEM["padding"] = [{"properties": {k: L("0D") for k in ("top", "bottom", "left", "right")}}]
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"


def estado(props):
    return [{"properties": p, "selector": {"id": s}} for s, p in props]


def visual_html(vid, medida_nome):
    return {
        "$schema": SCHEMA + "visualContainer/2.4.0/schema.json",
        "name": vid,
        "position": {"x": 0, "y": 0, "z": 0, "height": 720, "width": 1280, "tabOrder": 0},
        "visual": {
            "visualType": HTML_VISUAL,
            "query": {"queryState": {"content": {"projections": [{
                "field": {"Measure": {"Expression": {"SourceRef": {"Entity": "_Paginas"}}, "Property": medida_nome}},
                "queryRef": f"_Paginas.{medida_nome}", "nativeQueryRef": medida_nome}]}}},
            "objects": {
                "contentFormatting": [{"properties": {"showRawHtml": L("false")}}],
                "crossFilter": [{"properties": {"enabled": L("false"), "useTransparency": L("false")}}],
                "compatibility": [{"properties": {"legacyRendering": L("true")}}],
            },
            "visualContainerObjects": SEM,
            "drillFilterOtherVisuals": True,
        },
    }


def visual_menu(vid):
    return {
        "$schema": SCHEMA + "visualContainer/2.4.0/schema.json",
        "name": vid,
        "position": {"x": 16, "y": 14, "z": 1000, "height": 32, "width": 560, "tabOrder": 1000},
        "visual": {
            "visualType": "pageNavigator",
            "objects": {
                "layout": [{"properties": {"cellPadding": L("4L")}}],
                "shape": [{"properties": {"tileShape": L("'pill'")}}],
                "fill": estado([("default", {"show": L("true"), "fillColor": COR("#121A2E"), "transparency": L("0D")}),
                                ("hover", {"fillColor": COR("#1C2742")}),
                                ("selected", {"fillColor": COR("#FF8A00")})]),
                "text": estado([("default", {"fontColor": COR("#C9D1E6"), "fontSize": L("9D"), "bold": L("true"),
                                             "leftMargin": L("2L"), "rightMargin": L("2L")}),
                                ("hover", {"fontColor": COR("#FFFFFF")}),
                                ("selected", {"fontColor": COR("#0B1020")})]),
                "outline": estado([("default", {"show": L("true"), "lineColor": COR("#24304F"), "weight": L("1D")}),
                                   ("hover", {"lineColor": COR("#3A4A72")}),
                                   ("selected", {"lineColor": COR("#FFB347")})]),
            },
            "visualContainerObjects": SEM,
            "drillFilterOtherVisuals": True,
        },
    }


def salvar(caminho, obj):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def gerar_relatorio():
    ids = []
    for arq, nome, _ in PAGINAS:
        pid = hexid("pagina", arq); ids.append(pid)
        pasta = REL / "pages" / pid
        salvar(pasta / "page.json", {
            "$schema": SCHEMA + "page/2.1.0/schema.json",
            "name": pid, "displayName": nome, "displayOption": "FitToPage", "height": 720, "width": 1280,
            "objects": {
                "background": [{"properties": {"color": COR("#070B16"), "transparency": L("0D")}}],
                "outspace": [{"properties": {"color": COR("#070B16"), "transparency": L("0D")}}],
            },
        })
        salvar(pasta / "visuals" / hexid("html", arq) / "visual.json", visual_html(hexid("html", arq), f"HTML {nome}"))
        salvar(pasta / "visuals" / hexid("menu", arq) / "visual.json", visual_menu(hexid("menu", arq)))
    salvar(REL / "pages" / "pages.json", {
        "$schema": SCHEMA + "pagesMetadata/1.1.0/schema.json", "pageOrder": ids, "activePageName": ids[0]})
    rel = json.loads((REL / "report.json").read_text(encoding="utf-8"))
    cv = rel.setdefault("publicCustomVisuals", [])
    if HTML_VISUAL not in cv:
        cv.append(HTML_VISUAL)
    salvar(REL / "report.json", rel)
    return ids


def gerar_doc():
    """docs/medidas_paginas.md: as medidas de dados por extenso e o resumo das medidas de página."""
    linhas = ["# Medidas da tabela `_Paginas`", "",
              "Geradas por `scripts/gerar_pbi.py`. As medidas `[JSON *]` serializam o modelo em um objeto JavaScript; "
              "cada medida `[HTML <Página>]` junta o HTML/CSS/JS minificado de `powerbi/html/` com `[JSON Dados]`.", "",
              "Os textos são delimitados por `¤` enquanto o registro é montado. Depois o resultado inteiro é escapado "
              "uma vez (`\\`, `'`, `<` e quebras de linha) e só então `¤` vira aspas simples.", ""]
    for n, d, e in MEDIDAS_JSON + [("JSON Dados", "Objeto único com todo o modelo, injetado em cada página como `window.D`.", EXPR_DADOS)]:
        linhas += [f"## {n}", "", d, "", "```dax", f"{n} =", e.strip(), "```", ""]
    linhas += ["## Medidas de página", "", "| Medida | Página | Tamanho |", "| --- | --- | --- |"]
    for arq, nome, desc in PAGINAS:
        kb = (DIST / f"{arq}.min.html").stat().st_size / 1024
        linhas.append(f"| `HTML {nome}` | {desc} | {kb:.0f} KB + dados |")
    linhas += ["", "Formato de cada uma: `VAR dados = [JSON Dados] RETURN \"<style>…\" & … & dados & \"…</script>\"`, "
               f"com o HTML quebrado em literais de até {TAM_LITERAL} caracteres.", ""]
    destino = Path(__file__).resolve().parents[1] / "docs" / "medidas_paginas.md"
    destino.write_text("\n".join(linhas), encoding="utf-8")


if __name__ == "__main__":
    gerar_doc()
    tam = gerar_tmdl()
    ids = gerar_relatorio()
    print(f"_Paginas.tmdl: {tam / 1024:.0f} KB | páginas: {', '.join(n for _, n, _ in PAGINAS)}")
    print("ids:", " ".join(ids))
