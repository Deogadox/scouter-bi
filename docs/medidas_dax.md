# Medidas DAX do Scouter BI

Geradas junto com o modelo em `powerbi/DBZ_BI.SemanticModel`. Use este arquivo como referência ou para recriar as medidas à mão.

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
