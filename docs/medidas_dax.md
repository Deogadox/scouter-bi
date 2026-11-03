# Medidas DAX do Scouter BI

Geradas junto com o modelo em `powerbi/DBZ_BI.SemanticModel`. Use este arquivo como referência ou para recriar as medidas à mão. As medidas que alimentam as páginas HTML (tabela `_Paginas`) estão em [medidas_paginas.md](medidas_paginas.md).

## Tabela `fato_poder`

### Poder

Nível de poder no contexto (personagem, saga e forma). Pasta: *Poder*. Formato: `#,0`.

```dax
Poder =
MAX ( fato_poder[nivel_poder] )
```

### Poder (log10)

Ordem de grandeza do poder. Use em eixos para comparar 1.500 com 15 bilhões. Pasta: *Poder*. Formato: `0.00`.

```dax
Poder (log10) =
MAX ( fato_poder[nivel_poder_log10] )
```

### Poder Formatado

Poder em texto curto: 3,2 bi, 150,0 mi, 18,0 mil. Pasta: *Poder*.

```dax
Poder Formatado =
VAR v = [Poder]
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( v ), BLANK (),
        v >= 1E12, FORMAT ( v / 1E12, "#,0.0" ) & " tri",
        v >= 1E9, FORMAT ( v / 1E9, "#,0.0" ) & " bi",
        v >= 1E6, FORMAT ( v / 1E6, "#,0.0" ) & " mi",
        v >= 1E3, FORMAT ( v / 1E3, "#,0.0" ) & " mil",
        FORMAT ( v, "#,0" )
    )
```

### Poder Máximo na Saga

Maior nível do personagem na saga, em qualquer forma. Pasta: *Poder*. Formato: `#,0`.

```dax
Poder Máximo na Saga =
CALCULATE ( [Poder], REMOVEFILTERS ( dim_transformacao ) )
```

### Ranking na Saga

Posição do personagem entre os selecionados, pelo pico na saga. Pasta: *Poder*. Formato: `0`.

```dax
Ranking na Saga =
IF (
    ISBLANK ( [Poder Máximo na Saga] ),
    BLANK (),
    RANKX ( ALLSELECTED ( dim_personagem[nome] ), [Poder Máximo na Saga], , DESC, DENSE )
)
```

### Multiplicador da Forma

Quantas vezes a forma multiplica o poder base na mesma saga. Pasta: *Poder*. Formato: `0.0"x"`.

```dax
Multiplicador da Forma =
DIVIDE (
    [Poder],
    CALCULATE ( [Poder], REMOVEFILTERS ( dim_transformacao ), dim_transformacao[e_base] = TRUE () )
)
```

### Crescimento vs Saga Anterior

Pico do personagem nesta saga dividido pelo pico na saga anterior em que ele aparece. Pasta: *Poder*. Formato: `0.0"x"`.

```dax
Crescimento vs Saga Anterior =
VAR ordemAtual = MAX ( dim_saga[ordem_cronologica] )
VAR pico = [Poder Máximo na Saga]
VAR ordemAnterior =
    MAXX (
        FILTER (
            ALL ( dim_saga[ordem_cronologica] ),
            VAR o = dim_saga[ordem_cronologica]
            RETURN
                o < ordemAtual
                    && NOT ISBLANK ( CALCULATE ( [Poder Máximo na Saga], REMOVEFILTERS ( dim_saga ), dim_saga[ordem_cronologica] = o ) )
        ),
        dim_saga[ordem_cronologica]
    )
VAR picoAnterior =
    CALCULATE ( [Poder Máximo na Saga], REMOVEFILTERS ( dim_saga ), dim_saga[ordem_cronologica] = ordemAnterior )
RETURN
    IF ( ISBLANK ( pico ) || ISBLANK ( ordemAnterior ), BLANK (), DIVIDE ( pico, picoAnterior ) )
```

### Scouter SVG

Leitor de scouter animado (SVG) com o poder do personagem na saga. Pasta: *Visual*.

```dax
Scouter SVG =
VAR temUm = HASONEVALUE ( dim_personagem[nome] )
VAR nome = IF ( temUm, VALUES ( dim_personagem[nome] ), "Mais forte: " & [Mais Forte da Saga] )
VAR saga = IF ( HASONEVALUE ( dim_saga[nome] ), VALUES ( dim_saga[nome] ), "Todas as sagas" )
VAR leitura = IF ( ISBLANK ( [Poder] ), "SEM LEITURA", [Poder Formatado] )
VAR lg = COALESCE ( [Poder (log10)], 0 )
VAR largura = ROUND ( 360 * MIN ( 1, lg / 11 ), 0 )
VAR verde = "%2339ff88"
RETURN
    "data:image/svg+xml;utf8,"
        & "<svg xmlns='http://www.w3.org/2000/svg' width='600' height='150' viewBox='0 0 600 150'>"
        & "<rect width='600' height='150' rx='14' fill='%23041a10'/>"
        & "<rect x='4' y='4' width='592' height='142' rx='11' fill='none' stroke='" & verde & "' stroke-opacity='0.35'/>"
        & "<g stroke='" & verde & "' stroke-opacity='0.10'><line x1='0' y1='50' x2='600' y2='50'/><line x1='0' y1='100' x2='600' y2='100'/><line x1='440' y1='0' x2='440' y2='150'/></g>"
        & "<g stroke='" & verde & "' stroke-opacity='0.5'><line x1='520' y1='30' x2='520' y2='120'/><line x1='475' y1='75' x2='565' y2='75'/></g>"
        & "<circle cx='520' cy='75' r='30' fill='none' stroke='" & verde & "' stroke-width='2'>"
        & "<animate attributeName='r' values='14;44;14' dur='1.4s' repeatCount='indefinite'/>"
        & "<animate attributeName='stroke-opacity' values='1;0.1;1' dur='1.4s' repeatCount='indefinite'/></circle>"
        & "<circle cx='520' cy='75' r='5' fill='" & verde & "'/>"
        & "<text x='20' y='26' font-family='Consolas,monospace' font-size='11' fill='" & verde & "' fill-opacity='0.8'>SCOUTER // " & UPPER ( saga ) & "</text>"
        & "<text x='20' y='56' font-family='Segoe UI,sans-serif' font-size='20' font-weight='700' fill='%23ffffff'>" & nome & "</text>"
        & "<text x='20' y='104' font-family='Consolas,monospace' font-size='40' font-weight='700' fill='" & verde & "'>" & leitura & "</text>"
        & "<rect x='20' y='118' width='360' height='10' rx='5' fill='" & verde & "' fill-opacity='0.15'/>"
        & "<rect x='20' y='118' width='" & largura & "' height='10' rx='5' fill='" & verde & "'>"
        & "<animate attributeName='width' from='0' to='" & largura & "' dur='1.2s' fill='freeze'/></rect>"
        & "<text x='20' y='142' font-family='Segoe UI,sans-serif' font-size='10' fill='" & verde & "' fill-opacity='0.7'>escala logarítmica · 10^" & FORMAT ( lg, "0.0" ) & "</text>"
        & "</svg>"
```

### Mais Forte da Saga

Nome do personagem com o maior nível de poder no contexto. Pasta: *Visual*.

```dax
Mais Forte da Saga =
VAR ranking =
    FILTER (
        ADDCOLUMNS ( VALUES ( dim_personagem[nome] ), "@pico", [Poder Máximo na Saga] ),
        NOT ISBLANK ( [@pico] )
    )
RETURN
    CONCATENATEX ( TOPN ( 1, ranking, [@pico], DESC ), dim_personagem[nome], ", " )
```

### % Canônico ou Guia

Parcela dos valores que vem da obra ou de guia oficial. Pasta: *Curadoria*. Formato: `0%`.

```dax
% Canônico ou Guia =
DIVIDE (
    CALCULATE ( COUNTROWS ( fato_poder ), fato_poder[fonte_valor] IN { "canonico", "guia_oficial" } ),
    COUNTROWS ( fato_poder )
)
```

### Qtd Valores

Linhas de nível de poder no contexto. Pasta: *Curadoria*. Formato: `0`.

```dax
Qtd Valores =
COUNTROWS ( fato_poder )
```

## Tabela `fato_luta`

### Qtd Lutas

Lutas canônicas no contexto. Pasta: *Lutas*. Formato: `0`.

```dax
Qtd Lutas =
COUNTROWS ( fato_luta )
```

### Qtd Zebras

Lutas em que o personagem mais fraco venceu. Pasta: *Lutas*. Formato: `0`.

```dax
Qtd Zebras =
CALCULATE ( COUNTROWS ( fato_luta ), fato_luta[zebra] = TRUE () )
```

### Vencedor

Nome do vencedor da luta. Pasta: *Lutas*.

```dax
Vencedor =
LOOKUPVALUE ( dim_personagem[nome], dim_personagem[sk_personagem], SELECTEDVALUE ( fato_luta[sk_vencedor] ) )
```

### Perdedor

Nome do perdedor da luta. Pasta: *Lutas*.

```dax
Perdedor =
LOOKUPVALUE ( dim_personagem[nome], dim_personagem[sk_personagem], SELECTEDVALUE ( fato_luta[sk_perdedor] ) )
```

### Forma do Vencedor

Forma usada pelo vencedor. Pasta: *Lutas*.

```dax
Forma do Vencedor =
LOOKUPVALUE ( dim_transformacao[forma], dim_transformacao[sk_transformacao], SELECTEDVALUE ( fato_luta[sk_transformacao_vencedor] ) )
```

### Forma do Perdedor

Forma usada pelo perdedor. Pasta: *Lutas*.

```dax
Forma do Perdedor =
LOOKUPVALUE ( dim_transformacao[forma], dim_transformacao[sk_transformacao], SELECTEDVALUE ( fato_luta[sk_transformacao_perdedor] ) )
```

### Acurácia do Modelo

Em quantas vitórias o maior nível de poder previu o vencedor. Pasta: *Lutas*. Formato: `0%`.

```dax
Acurácia do Modelo =
VAR vitorias = CALCULATE ( COUNTROWS ( fato_luta ), fato_luta[resultado] = "vitoria" )
RETURN
    DIVIDE ( vitorias - [Qtd Zebras], vitorias )
```

## Tabela `Lutador A`

### Poder A

Poder do lutador escolhido no lado A. Pasta: *Simulador*. Formato: `#,0`.

```dax
Poder A =
MAX ( 'Lutador A'[Poder] )
```

### Poder B

Poder do lutador escolhido no lado B. Pasta: *Simulador*. Formato: `#,0`.

```dax
Poder B =
MAX ( 'Lutador B'[Poder] )
```

### Chance de Vitória A

Modelo Elo simplificado: chance = A² / (A² + B²). Poder 2x maior dá 80%. Pasta: *Simulador*. Formato: `0%`.

```dax
Chance de Vitória A =
VAR la = MAX ( 'Lutador A'[Log] )
VAR lb = MAX ( 'Lutador B'[Log] )
RETURN
    IF (
        ISBLANK ( la ) || ISBLANK ( lb ),
        BLANK (),
        1 / ( 1 + POWER ( 10, -2 * ( la - lb ) ) )
    )
```

### Chance de Vitória B

Complemento da chance de A. Pasta: *Simulador*. Formato: `0%`.

```dax
Chance de Vitória B =
IF ( ISBLANK ( [Chance de Vitória A] ), BLANK (), 1 - [Chance de Vitória A] )
```

### Batalha SVG

Arena animada: rajadas de energia se chocam e o choque empurra para o lado do mais fraco. Pasta: *Simulador*.

```dax
Batalha SVG =
VAR pa = [Chance de Vitória A]
VAR nA = SELECTEDVALUE ( 'Lutador A'[Personagem] )
VAR nB = SELECTEDVALUE ( 'Lutador B'[Personagem] )
VAR rotA = nA & " · " & SELECTEDVALUE ( 'Lutador A'[Forma] )
VAR rotB = SELECTEDVALUE ( 'Lutador B'[Forma] ) & " · " & nB
VAR vencA = pa >= 0.5
VAR pv = MAX ( pa, 1 - pa )
VAR c = ROUND ( 154 + 892 * pa, 0 )
VAR hpA = IF ( vencA, ROUND ( 300 * MAX ( 0.15, 2 * pa - 1 ), 0 ), 0 )
VAR hpB = IF ( vencA, 0, ROUND ( 300 * MAX ( 0.15, 1 - 2 * pa ), 0 ) )
VAR kt = "keyTimes='0;0.3;0.45;0.55;0.65;1' dur='3s' fill='freeze'"
VAR laranja = "%23ff8a00"
VAR azul = "%233b82f6"
VAR fonte = "font-family='Segoe UI,sans-serif'"
VAR abre = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='160' viewBox='0 0 1200 160'><rect width='1200' height='160' rx='14' fill='%230a0f1f'/>"
RETURN
    IF (
        ISBLANK ( pa ),
        abre & "<text x='600' y='88' text-anchor='middle' " & fonte & " font-size='20' fill='%239aa6c4'>Escolha os dois lutadores para começar a luta</text></svg>",
        abre
            & "<text x='40' y='26' " & fonte & " font-size='16' font-weight='700' fill='" & laranja & "'>" & rotA & "</text>"
            & "<text x='1160' y='26' text-anchor='end' " & fonte & " font-size='16' font-weight='700' fill='" & azul & "'>" & rotB & "</text>"
            & "<rect x='40' y='34' width='300' height='8' rx='4' fill='%23ffffff' fill-opacity='0.12'/>"
            & "<rect x='40' y='34' width='300' height='8' rx='4' fill='%2339ff88'><animate attributeName='width' from='300' to='" & hpA & "' begin='2s' dur='1.2s' fill='freeze'/></rect>"
            & "<rect x='860' y='34' width='300' height='8' rx='4' fill='%23ffffff' fill-opacity='0.12'/>"
            & "<rect x='860' y='34' width='300' height='8' rx='4' fill='%2339ff88'><animate attributeName='width' from='300' to='" & hpB & "' begin='2s' dur='1.2s' fill='freeze'/>"
            & "<animate attributeName='x' from='860' to='" & 1160 - hpB & "' begin='2s' dur='1.2s' fill='freeze'/></rect>"
            & "<circle cx='110' cy='100' r='36' fill='" & laranja & "' fill-opacity='0.25' stroke='" & laranja & "' stroke-width='3'>"
            & "<animate attributeName='r' values='32;40;32' dur='0.6s' repeatCount='indefinite'/>"
            & "<animate attributeName='opacity' from='1' to='" & IF ( vencA, "1", "0.2" ) & "' begin='3.2s' dur='0.5s' fill='freeze'/></circle>"
            & "<circle cx='1090' cy='100' r='36' fill='" & azul & "' fill-opacity='0.25' stroke='" & azul & "' stroke-width='3'>"
            & "<animate attributeName='r' values='32;40;32' dur='0.6s' repeatCount='indefinite'/>"
            & "<animate attributeName='opacity' from='1' to='" & IF ( vencA, "0.2", "1" ) & "' begin='3.2s' dur='0.5s' fill='freeze'/></circle>"
            & "<text x='600' y='70' text-anchor='middle' " & fonte & " font-size='26' font-weight='800' fill='%23ffffff'>VS"
            & "<animate attributeName='opacity' from='1' to='0' begin='0.6s' dur='0.4s' fill='freeze'/></text>"
            & "<rect x='154' y='93' width='0' height='14' rx='7' fill='" & laranja & "'>"
            & "<animate attributeName='width' values='0;446;446;466;426;" & c - 154 & "' " & kt & "/></rect>"
            & "<rect x='1046' y='93' width='0' height='14' rx='7' fill='" & azul & "'>"
            & "<animate attributeName='x' values='1046;600;600;620;580;" & c & "' " & kt & "/>"
            & "<animate attributeName='width' values='0;446;446;426;466;" & 1046 - c & "' " & kt & "/></rect>"
            & "<circle cx='600' cy='100' r='0' fill='%23ffffff'>"
            & "<animate attributeName='cx' values='600;600;600;620;580;" & c & "' " & kt & "/>"
            & "<animate attributeName='r' values='0;14;18;12;20;10' " & kt & "/></circle>"
            & "<circle cx='" & c & "' cy='100' r='0' fill='%23fff3c4' opacity='0'>"
            & "<animate attributeName='r' from='0' to='70' begin='3s' dur='0.6s' fill='freeze'/>"
            & "<animate attributeName='opacity' values='0;1;0' begin='3s' dur='0.6s' fill='freeze'/></circle>"
            & "<text x='600' y='150' text-anchor='middle' " & fonte & " font-size='18' font-weight='800' fill='%23ffffff' opacity='0'>"
            & "VITÓRIA DE " & UPPER ( IF ( vencA, nA, nB ) ) & " · " & FORMAT ( pv, "0%" ) & " DE CHANCE"
            & "<animate attributeName='opacity' from='0' to='1' begin='3.2s' dur='0.5s' fill='freeze'/></text>"
            & "</svg>"
    )
```

### Barra de Chance SVG

Barra dividida com a chance de cada lado (SVG). Pasta: *Simulador*.

```dax
Barra de Chance SVG =
VAR a = [Chance de Vitória A]
VAR largura = IF ( ISBLANK ( a ), 280, ROUND ( 560 * a, 0 ) )
VAR txtA = IF ( ISBLANK ( a ), "–", FORMAT ( a, "0%" ) )
VAR txtB = IF ( ISBLANK ( a ), "–", FORMAT ( 1 - a, "0%" ) )
RETURN
    "data:image/svg+xml;utf8,"
        & "<svg xmlns='http://www.w3.org/2000/svg' width='600' height='90' viewBox='0 0 600 90'>"
        & "<rect x='20' y='30' width='560' height='30' rx='15' fill='%233b82f6'/>"
        & "<rect x='20' y='30' width='" & largura & "' height='30' rx='15' fill='%23ff8a00'>"
        & "<animate attributeName='width' from='280' to='" & largura & "' dur='1s' fill='freeze'/></rect>"
        & "<text x='20' y='20' font-family='Segoe UI,sans-serif' font-size='16' font-weight='700' fill='%23ff8a00'>A " & txtA & "</text>"
        & "<text x='580' y='20' text-anchor='end' font-family='Segoe UI,sans-serif' font-size='16' font-weight='700' fill='%233b82f6'>" & txtB & " B</text>"
        & "<text x='300' y='84' text-anchor='middle' font-family='Segoe UI,sans-serif' font-size='12' fill='%23c9d1e6'>chance de vitória</text>"
        & "</svg>"
```

### Imagem A

Retrato do lutador A. Pasta: *Simulador*.

```dax
Imagem A =
SELECTEDVALUE ( 'Lutador A'[Imagem] )
```

### Imagem B

Retrato do lutador B. Pasta: *Simulador*.

```dax
Imagem B =
SELECTEDVALUE ( 'Lutador B'[Imagem] )
```

### Veredito

Frase do resultado do simulador. Pasta: *Simulador*.

```dax
Veredito =
VAR a = SELECTEDVALUE ( 'Lutador A'[Personagem] )
VAR b = SELECTEDVALUE ( 'Lutador B'[Personagem] )
VAR p = [Chance de Vitória A]
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( p ), "Escolha os dois lutadores",
        p >= 0.95, a & " vence com folga",
        p > 0.55, a & " é favorito",
        p >= 0.45, "Luta equilibrada",
        p > 0.05, b & " é favorito",
        b & " vence com folga"
    )
```

## Tabelas calculadas `Lutador A` e `Lutador B`

Cópias desconectadas da `fato_poder`, uma para cada lado do simulador.

```dax
SELECTCOLUMNS (
    fato_poder,
    "Opção", RELATED ( dim_personagem[nome] ) & " · " & RELATED ( dim_transformacao[forma] ) & " · " & RELATED ( dim_saga[nome] ),
    "Personagem", RELATED ( dim_personagem[nome] ),
    "Forma", RELATED ( dim_transformacao[forma] ),
    "Saga", RELATED ( dim_saga[nome] ),
    "Ordem Saga", RELATED ( dim_saga[ordem_cronologica] ),
    "Imagem", RELATED ( dim_personagem[url_imagem] ),
    "Poder", fato_poder[nivel_poder],
    "Log", fato_poder[nivel_poder_log10]
)
```
