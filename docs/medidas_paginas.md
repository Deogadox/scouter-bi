# Medidas da tabela `_Paginas`

Geradas por `scripts/gerar_pbi.py`. As medidas `[JSON *]` serializam o modelo em um objeto JavaScript; cada medida `[HTML <Página>]` junta o HTML/CSS/JS minificado de `powerbi/html/` com `[JSON Dados]`.

Os textos são delimitados por `¤` enquanto o registro é montado. Depois o resultado inteiro é escapado uma vez (`\`, `'`, `<` e quebras de linha) e só então `¤` vira aspas simples.

## JSON Sagas

Sagas do Z em ordem cronológica: {o, n, a, e1, e2, f}.

```dax
JSON Sagas =
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
VAR seguro =
    SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE (
        bruto, "\", "\\" ), "'", "\'" ), "<", "\u003c" ), UNICHAR ( 10 ), " " ), UNICHAR ( 13 ), "" )
RETURN
    "[" & SUBSTITUTE ( seguro, Q, "'" ) & "]"
```

## JSON Personagens

Personagens que têm leitura de poder: {id, n, r, af, pl, img, orig}.

```dax
JSON Personagens =
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
VAR seguro =
    SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE (
        bruto, "\", "\\" ), "'", "\'" ), "<", "\u003c" ), UNICHAR ( 10 ), " " ), UNICHAR ( 13 ), "" )
RETURN
    "[" & SUBSTITUTE ( seguro, Q, "'" ) & "]"
```

## JSON Poder

Uma linha por personagem × saga × forma: {p, s, f, fi, v, src, ob}. s = ordem da saga.

```dax
JSON Poder =
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
VAR seguro =
    SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE (
        bruto, "\", "\\" ), "'", "\'" ), "<", "\u003c" ), UNICHAR ( 10 ), " " ), UNICHAR ( 13 ), "" )
RETURN
    "[" & SUBSTITUTE ( seguro, Q, "'" ) & "]"
```

## JSON Transformações

Transformações da API que a curadoria não usa (galeria): {p, n, img}.

```dax
JSON Transformações =
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
VAR seguro =
    SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE (
        bruto, "\", "\\" ), "'", "\'" ), "<", "\u003c" ), UNICHAR ( 10 ), " " ), UNICHAR ( 13 ), "" )
RETURN
    "[" & SUBSTITUTE ( seguro, Q, "'" ) & "]"
```

## JSON Lutas

Lutas canônicas: {id, s, v, fv, d, fd, r, z, ob}. v/d = vencedor/perdedor, z = zebra.

```dax
JSON Lutas =
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
VAR seguro =
    SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE ( SUBSTITUTE (
        bruto, "\", "\\" ), "'", "\'" ), "<", "\u003c" ), UNICHAR ( 10 ), " " ), UNICHAR ( 13 ), "" )
RETURN
    "[" & SUBSTITUTE ( seguro, Q, "'" ) & "]"
```

## JSON Meta

Contagens usadas na página Bastidores: {nApi, nExtra, nPl, nTr, nPod, ...}.

```dax
JSON Meta =
"{"
    & "nApi:" & FORMAT ( COUNTROWS ( FILTER ( dim_personagem, dim_personagem[origem] = "api" ) ) + 0, "0" )
    & ",nExtra:" & FORMAT ( COUNTROWS ( FILTER ( dim_personagem, dim_personagem[origem] = "curadoria" ) ) + 0, "0" )
    & ",nPl:" & FORMAT ( COUNTROWS ( dim_planeta ) + 0, "0" )
    & ",nTr:" & FORMAT ( DISTINCTCOUNTNOBLANK ( dim_transformacao[id_api] ) + 0, "0" )
    & ",nPod:" & FORMAT ( COUNTROWS ( fato_poder ) + 0, "0" )
    & ",nCan:" & FORMAT ( COUNTROWS ( FILTER ( fato_poder, LEFT ( fato_poder[fonte_valor], 1 ) = "c" ) ) + 0, "0" )
    & ",nGuia:" & FORMAT ( COUNTROWS ( FILTER ( fato_poder, LEFT ( fato_poder[fonte_valor], 1 ) = "g" ) ) + 0, "0" )
    & ",nEst:" & FORMAT ( COUNTROWS ( FILTER ( fato_poder, LEFT ( fato_poder[fonte_valor], 1 ) = "e" ) ) + 0, "0" )
    & ",nLut:" & FORMAT ( COUNTROWS ( fato_luta ) + 0, "0" )
    & ",nZeb:" & FORMAT ( COUNTROWS ( FILTER ( fato_luta, fato_luta[zebra] ) ) + 0, "0" )
    & ",nVit:" & FORMAT ( COUNTROWS ( FILTER ( fato_luta, fato_luta[resultado] = "vitoria" ) ) + 0, "0" )
    & ",kiDesc:" & FORMAT ( COUNTROWS ( FILTER ( dim_personagem, dim_personagem[origem] = "api" && dim_personagem[ki_max_api_status] = "desconhecido" ) ) + 0, "0" )
    & ",kiInc:" & FORMAT ( COUNTROWS ( FILTER ( dim_personagem, dim_personagem[origem] = "api" && dim_personagem[ki_max_api_status] = "incomensuravel" ) ) + 0, "0" )
    & ",nSagas:" & FORMAT ( COUNTROWS ( dim_saga ) + 0, "0" )
    & "}"
```

## JSON Dados

Objeto único com todo o modelo, injetado em cada página como `window.D`.

```dax
JSON Dados =
"{sagas:" & [JSON Sagas]
    & ",per:" & [JSON Personagens]
    & ",pod:" & [JSON Poder]
    & ",tra:" & [JSON Transformações]
    & ",lut:" & [JSON Lutas]
    & ",meta:" & [JSON Meta] & "}"
```

## Medidas de página

| Medida | Página | Tamanho |
| --- | --- | --- |
| `HTML Scouter` | Ficha de cada guerreiro: leitura do scouter por saga e forma, evolução e lutas. | 35 KB + dados |
| `HTML Arena` | Simulador de batalha jogável: o motor usa a mesma curva de chance do modelo. | 41 KB + dados |
| `HTML Escalada` | A inflação de poder saga a saga, em escala log, com o campeão de cada saga. | 26 KB + dados |
| `HTML Quiz` | Quiz de 10 perguntas geradas a partir dos dados do modelo. | 29 KB + dados |
| `HTML Radar` | Minigame: encontre as 7 esferas do dragão com o radar. | 28 KB + dados |
| `HTML Bastidores` | Como o projeto foi construído: pipeline, curadoria e métricas do modelo. | 25 KB + dados |

Formato de cada uma: `VAR dados = [JSON Dados] RETURN "<style>…" & … & dados & "…</script>"`, com o HTML quebrado em literais de até 3000 caracteres.
