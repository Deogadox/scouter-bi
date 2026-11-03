# Metodologia dos níveis de poder

A Dragon Ball API traz um único `ki` atual e um `maxKi` por personagem. Esses números não servem para comparar personagens ao longo da história:

- não existe nível de poder por saga;
- os valores são inconsistentes entre si (ex.: Trunks SSJ3 = 1,25 bi, abaixo do SSJ2 = 18 bi; Majin Boo Puro = 4 bi, abaixo do Super Boo = 5,67 bi);
- personagens importantes não existem na API (Nappa, Forças Especiais Ginyu, Chaos).

Por isso o projeto mantém uma **curadoria própria** em `data/curadoria/`, e o `ki` da API fica apenas como referência.

## Fonte de cada valor (`fonte_valor`)

| Valor | Significado | Uso |
| --- | --- | --- |
| `canonico` | Número dito na obra (leitura de scouter ou fala de personagem) | Saga Saiyajin e Namekusei |
| `guia_oficial` | Número de guia oficial (Daizenshuu 7) | Era do scouter, até a Saga Freeza |
| `estimado` | Estimativa deste projeto, pela regra abaixo | Da Saga Trunks em diante |

> Os valores `guia_oficial` estão em revisão contra a fonte original.

## Regra das estimativas

1. Cada personagem tem uma **base por saga**, crescente ao longo da história.
2. Formas aplicam um **multiplicador fixo** sobre a base:

| Forma | Multiplicador |
| --- | --- |
| Kaioken x2 / x3 / x4 / x20 | 2 / 3 / 4 / 20 |
| Super Saiyajin (SSJ) | 50 |
| Super Saiyajin 2 (SSJ2) | 100 |
| Super Saiyajin 3 (SSJ3) | 400 |

3. Formas sem multiplicador conhecido (formas de Freeza, Cell, Boo, fusões) recebem valor direto.
4. **Restrição de consistência:** o vencedor de cada luta canônica em `fato_luta.csv` precisa ter nível de poder maior ou igual ao do perdedor. A única exceção registrada é a luta 22 (Goku SSJ3 vence Kid Boo com a Genki Dama, energia emprestada).

## Granularidade

Uma linha por **personagem × saga × forma**. Quando o personagem tem dois momentos na mesma saga (ex.: Goku contra Raditz com 416 e contra Nappa com 8.000), fica o valor de pico, e a coluna `observacao` registra o outro.

## Como contribuir

Edite os CSVs, rode `scripts\run_fase2.ps1` e confira a seção de consistência no log. A procedure `dw.sp_carga_dw` recusa a carga se houver chave órfã ou duplicada.
