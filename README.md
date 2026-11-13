# ⚡ Monte seu time Pokémon

Protótipo acadêmico de recomendação híbrida com FastAPI e Docker. Crie um treinador, selecione tipos favoritos e uma estratégia e confirme para descobrir até seis Pokémon.

## Dados

O catálogo `data/pokemon_alopez247.csv` é do dataset [Pokémon for Data Mining and Machine Learning](https://www.kaggle.com/datasets/alopez247/pokemon), por Asier López Zorrilla, licença CC BY-NC-SA 4.0. Possui 721 Pokémon das seis primeiras gerações. Pokémon e nomes relacionados pertencem a seus respectivos titulares; este é um projeto acadêmico de fãs.

Cinco treinadores e suas avaliações são **fictícios**, apenas para demonstrar a filtragem colaborativa. Novos treinadores e avaliações são persistidos no SQLite; os objetos do universo Pokémon são cadastrados separadamente e não entram na recomendação de times.

## Como executar

### Docker

```bash
docker compose up --build
```

Abra http://localhost:8000 para criar seu treinador e descobrir seu time, e http://localhost:8000/docs para explorar e testar a API. Os dados ficam em um volume Docker persistente.

### Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Recomendação

O componente de conteúdo combina os tipos favoritos com o estilo escolhido: ataque, defesa, velocidade, equilibrado ou priorização de tipos. A normalização dos atributos usa 255, limite adotado para esta demonstração. O colaborativo compara avaliações de Pokémon em comum usando cosseno e considera avaliações de treinadores semelhantes. Para candidatos com sinal colaborativo, o score é 70% conteúdo e 30% colaborativo; caso contrário, usa conteúdo. Sem histórico, o treinador recém-criado recebe recomendações baseadas em suas preferências.

Os pesos são escolhas didáticas, sem ajuste ou validação com usuários reais. O score expressa compatibilidade aproximada por Pokémon; não garante o melhor time de batalha, cobertura de tipos ou sinergia entre membros. Os Pokémon já avaliados ainda podem ser recomendados. Pode haver menos de seis resultados se o catálogo elegível for pequeno.

## API

- `GET /opcoes`: tipos e estratégias aceitos.
- `POST /treinadores` e `PUT /treinadores/{id}/preferencias`: criar treinador e atualizar suas preferências.
- `GET /treinadores/{id}/time`: obter até seis recomendações; aceita `estilo` opcional.
- `POST /treinadores/{id}/avaliacoes`: registrar ou atualizar uma nota de 1 a 5.
- `GET /pokemon`, `GET /pokemon/{id}` e `POST /pokemon`: buscar, consultar e cadastrar Pokémon.
- `GET /objetos` e `POST /objetos`: listar e cadastrar objetos, como Pokébolas e poções.

As operações e os campos estão documentados no Swagger em `/docs`.

## Testes

```bash
pip install httpx
python -m unittest discover -s tests -v
```

Os testes usam um banco temporário separado do banco da aplicação.
