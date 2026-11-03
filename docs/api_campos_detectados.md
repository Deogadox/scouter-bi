# Campos detectados na Dragon Ball API

Gerado em 20261102_222230 a partir de `https://dragonball-api.com/api`.


## /characters (lista)

Paginação (`meta`): `{"totalItems": 58, "itemCount": 5, "itemsPerPage": 5, "totalPages": 12, "currentPage": 1}`

Itens retornados: 5


| Campo | Tipo | Exemplo |
| --- | --- | --- |
| `id` | int | 1 |
| `name` | str | Goku |
| `ki` | str | 60.000.000 |
| `maxKi` | str | 90 Septillion |
| `race` | str | Saiyan |
| `gender` | str | Male |
| `description` | str | El protagonista de la serie, conocido por su gran poder y pe |
| `image` | str | https://dragonball-api.com/characters/goku_normal.webp |
| `affiliation` | str | Z Fighter |
| `deletedAt` | NoneType | None |


Exemplos de ki (texto cru, precisa converter para número):

- Goku: ki=`60.000.000` · maxKi=`90 Septillion`
- Vegeta: ki=`54.000.000` · maxKi=`19.84 Septillion`
- Piccolo: ki=`2.000.000` · maxKi=`500.000.000`
- Bulma: ki=`0` · maxKi=`0`
- Freezer: ki=`530.000` · maxKi=`52.71 Septillion`


## /characters/1 (detalhe)

Itens retornados: 1


| Campo | Tipo | Exemplo |
| --- | --- | --- |
| `id` | int | 1 |
| `name` | str | Goku |
| `ki` | str | 60.000.000 |
| `maxKi` | str | 90 Septillion |
| `race` | str | Saiyan |
| `gender` | str | Male |
| `description` | str | El protagonista de la serie, conocido por su gran poder y pe |
| `image` | str | https://dragonball-api.com/characters/goku_normal.webp |
| `affiliation` | str | Z Fighter |
| `deletedAt` | NoneType | None |
| `originPlanet` | object |  |
| `originPlanet.id` | int | 2 |
| `originPlanet.name` | str | Tierra |
| `originPlanet.isDestroyed` | bool | False |
| `originPlanet.description` | str | La Tierra también llamado Mundo del Dragón (Dragon World), e |
| `originPlanet.image` | str | https://dragonball-api.com/planetas/Tierra_Dragon_Ball_Z.web |
| `originPlanet.deletedAt` | NoneType | None |
| `transformations` | array[6] |  |
| `transformations[].id` | int | 1 |
| `transformations[].name` | str | Goku SSJ |
| `transformations[].image` | str | https://dragonball-api.com/transformaciones/goku_ssj.webp |
| `transformations[].ki` | str | 3 Billion |
| `transformations[].deletedAt` | NoneType | None |


## /planets (lista)

Paginação (`meta`): `{"totalItems": 20, "itemCount": 5, "itemsPerPage": 5, "totalPages": 4, "currentPage": 1}`

Itens retornados: 5


| Campo | Tipo | Exemplo |
| --- | --- | --- |
| `id` | int | 1 |
| `name` | str | Namek |
| `isDestroyed` | bool | True |
| `description` | str | Planeta natal de los Namekianos. Escenario de importantes ba |
| `image` | str | https://dragonball-api.com/planetas/Namek_U7.webp |
| `deletedAt` | NoneType | None |


## /transformations (lista)

Itens retornados: 43


| Campo | Tipo | Exemplo |
| --- | --- | --- |
| `id` | int | 1 |
| `name` | str | Goku SSJ |
| `image` | str | https://dragonball-api.com/transformaciones/goku_ssj.webp |
| `ki` | str | 3 Billion |
| `deletedAt` | NoneType | None |
