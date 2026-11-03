# Dragon Ball API — mapeamento de campos (Fase 0)

Base URL: `https://dragonball-api.com/api` · sem autenticação · documentação: <https://web.dragonball-api.com/documentation>

> Endpoints e filtros abaixo vêm da especificação OpenAPI publicada. Os campos de resposta seguem a estrutura conhecida da API e **devem ser confirmados** rodando `python src\check_api.py`, que gera `docs/api_campos_detectados.md`.

## Endpoints

| Endpoint | Filtros / parâmetros | Retorno |
| --- | --- | --- |
| `GET /characters` | `page`, `limit`, `name`, `gender`, `race`, `affiliation` | Lista paginada de personagens |
| `GET /characters/{id}` | — | Personagem + planeta de origem + transformações |
| `GET /planets` | `page`, `limit`, `name`, `isDestroyed` | Lista paginada de planetas |
| `GET /planets/{id}` | — | Planeta + personagens originários |
| `GET /transformations` | — | Todas as transformações |
| `GET /transformations/{id}` | — | Uma transformação |

Valores aceitos nos filtros:

- **gender:** Male, Female, Other, Unknown
- **race:** Saiyan, Namekian, Human, Majin, Frieza Race, Jiren Race, Android, God, Angel, Evil, Unknown, Nucleico benigno, Nucleico
- **affiliation:** Z Fighter, Red Ribbon Army, Namekian Warrior, Freelancer, Army of Frieza, Other, Pride Troopers, Assistant of Vermoud, Assistant of Beerus, Villain

## Campos esperados

### Personagem (`/characters`)

| Campo API | Tipo | Destino no DW | Observação |
| --- | --- | --- | --- |
| `id` | int | `dim_personagem.id_api` | Chave natural |
| `name` | string | `nome` | |
| `ki` | **string** | `fato_poder` (base) | Texto com separador de milhar ou por extenso. Exige parser |
| `maxKi` | **string** | `ki_maximo` | Mesmo tratamento do `ki` |
| `race` | string | `raca` | |
| `gender` | string | `genero` | |
| `affiliation` | string | `afiliacao` | |
| `description` | string | `descricao` | Texto em espanhol |
| `image` | string (URL) | `url_imagem` | |
| `originPlanet` | object | `id_planeta` | Só no detalhe `/characters/{id}` |
| `transformations[]` | array | `dim_transformacao` | Só no detalhe: `id`, `name`, `image`, `ki` |

### Paginação (listas)

`items[]` + `meta` (`totalItems`, `itemCount`, `itemsPerPage`, `totalPages`, `currentPage`) + `links` (`first`, `previous`, `next`, `last`). O extrator da Fase 1 segue `links.next` até vir vazio.

### Planeta (`/planets`)

`id`, `name`, `isDestroyed` (bool), `description`, `image` → `dim_planeta`.

### Transformação (`/transformations`)

`id`, `name`, `image`, `ki` → `dim_transformacao`. O vínculo com o personagem vem do detalhe `/characters/{id}`.

## Lacunas que a curadoria cobre

| Necessidade do relatório | Existe na API? | Solução |
| --- | --- | --- |
| Nível de poder por saga | Não (só um `ki` atual e `maxKi`) | CSV `fato_poder` |
| Sagas e ordem cronológica | Não | CSV `dim_saga` |
| Lutas canônicas e vencedor | Não | CSV `fato_luta` |
| Multiplicador de transformação | Não (só `ki` da forma) | Calculado: ki da forma ÷ ki base |
| Série (Z / Super / GT) | Não | Curadoria em `dim_saga` |

## Decisões para a Fase 1

1. Puxar a lista paginada e, em seguida, o detalhe de cada `id` (é o único jeito de obter planeta e transformações).
2. Gravar o JSON cru em `data/raw/` antes de qualquer tratamento.
3. Criar a função `parse_ki()` com testes, cobrindo formatos numéricos e por extenso.
