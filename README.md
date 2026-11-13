# ⚡ Monte seu time Pokémon

**Um projeto acadêmico de recomendação híbrida para ajudar treinadores a descobrir seu próximo time.**

Crie um treinador, escolha tipos favoritos e um estilo de jogo e receba até seis Pokémon ordenados por afinidade. A aplicação combina características dos Pokémon com avaliações de treinadores e oferece uma API documentada com FastAPI.

> 🎓 **Objetivo acadêmico:** aplicar conceitos de sistemas de recomendação, modelagem de dados, APIs, testes e containerização em um projeto prático. Os resultados demonstram o funcionamento das técnicas; não representam uma avaliação com jogadores reais.

## 🧭 Visão geral

- Cadastro de treinadores e atualização de preferências.
- Recomendações com foco em ataque, defesa, velocidade, equilíbrio ou tipos favoritos.
- Consulta e cadastro de Pokémon; registro de avaliações de 1 a 5.
- Cadastro separado de objetos do universo Pokémon, como Pokébolas e poções.
- Interface web para criar um treinador e descobrir o time; API interativa em `/docs`.

## 📊 Dataset

O catálogo é baseado no [Pokémon for Data Mining and Machine Learning](https://www.kaggle.com/datasets/alopez247/pokemon), disponibilizado no Kaggle por **Asier López Zorrilla**. O arquivo [pokemon_alopez247.csv](data/pokemon_alopez247.csv) incluído no projeto contém **721 registros, 721 identificadores únicos e 23 colunas**, abrangendo as seis primeiras gerações.

**Por que escolhemos esta base?** Ela reúne, em um único CSV, tipos e atributos numéricos diretamente úteis para comparar Pokémon com as preferências de um treinador. Seu tamanho facilita o estudo, a execução local e a reprodução da atividade. Como a base não inclui as gerações mais recentes, o catálogo inicial não pretende representar todos os Pokémon existentes.

### Colunas do arquivo original

| Coluna | Descrição |
| --- | --- |
| `Number` | Número de identificação na Pokédex. |
| `Name` | Nome do Pokémon. |
| `Type_1` | Tipo primário. |
| `Type_2` | Tipo secundário, quando existente. |
| `Total` | Soma dos seis atributos de batalha. |
| `HP` | Pontos de vida base. |
| `Attack` | Ataque físico base. |
| `Defense` | Defesa física base. |
| `Sp_Atk` | Ataque especial base. |
| `Sp_Def` | Defesa especial base. |
| `Speed` | Velocidade base. |
| `Generation` | Geração em que o Pokémon foi introduzido. |
| `isLegendary` | Indica se o Pokémon é lendário. |
| `Color` | Cor registrada na Pokédex. |
| `hasGender` | Indica se o Pokémon possui gênero. |
| `Pr_Male` | Probabilidade de ser macho, quando aplicável. |
| `Egg_Group_1` | Grupo de ovo principal. |
| `Egg_Group_2` | Segundo grupo de ovo, quando existente. |
| `hasMegaEvolution` | Indica se possui megaevolução. |
| `Height_m` | Altura em metros. |
| `Weight_kg` | Peso em quilogramas. |
| `Catch_Rate` | Taxa base de captura. |
| `Body_Style` | Formato corporal. |

O sistema atual importa apenas **identificador, nome, tipos, HP, ataque, defesa, ataque especial, defesa especial, velocidade, geração e status lendário**. As demais colunas permanecem no CSV para futuras análises e não influenciam as recomendações nesta versão.

### Origem e limitações

- **Licença do dataset:** [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/); consulte seus termos antes de reutilizar os dados.
- A base representa uma forma selecionada por espécie: formas alternativas e megaevoluções não são cadastradas como entradas separadas.
- O catálogo não inclui histórico de treinadores. Os **cinco treinadores e suas avaliações iniciais são fictícios**, criados para demonstrar a filtragem colaborativa.
- Pokémon e nomes relacionados pertencem aos respectivos titulares. Este projeto é uma iniciativa acadêmica de fãs.
- Novos treinadores, preferências e avaliações são persistidos no SQLite. Objetos do universo Pokémon são cadastrados separadamente e não participam do ranking.

## 🚀 Como executar

### Docker

```bash
docker compose up --build
```

Abra [a aplicação](http://localhost:8000) para criar seu treinador e descobrir seu time e [o Swagger](http://localhost:8000/docs) para explorar e testar a API. Os dados ficam em um volume Docker persistente.

### Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 🧠 Como a recomendação funciona

O componente de conteúdo combina os tipos favoritos com o estilo escolhido: ataque, defesa, velocidade, equilibrado ou priorização de tipos. A normalização dos atributos usa 255, limite adotado para esta demonstração. O colaborativo compara avaliações de Pokémon em comum usando cosseno e considera avaliações de treinadores semelhantes. Para candidatos com sinal colaborativo, o score é 70% conteúdo e 30% colaborativo; caso contrário, usa conteúdo. Sem histórico, o treinador recém-criado recebe recomendações baseadas em suas preferências.

Os pesos são escolhas didáticas, sem ajuste ou validação com usuários reais. O score expressa compatibilidade aproximada por Pokémon; não garante o melhor time de batalha, cobertura de tipos ou sinergia entre membros. Os Pokémon já avaliados ainda podem ser recomendados. Pode haver menos de seis resultados se o catálogo elegível for pequeno.

## 🔌 API

- `GET /opcoes`: tipos e estratégias aceitos.
- `POST /treinadores` e `PUT /treinadores/{id}/preferencias`: criar treinador e atualizar suas preferências.
- `GET /treinadores/{id}/time`: obter até seis recomendações; aceita `estilo` opcional.
- `POST /treinadores/{id}/avaliacoes`: registrar ou atualizar uma nota de 1 a 5.
- `GET /pokemon`, `GET /pokemon/{id}` e `POST /pokemon`: buscar, consultar e cadastrar Pokémon.
- `GET /objetos` e `POST /objetos`: listar e cadastrar objetos, como Pokébolas e poções.

As operações e os campos estão documentados no Swagger em `/docs`.

## 🧪 Testes

```bash
pip install httpx
python -m unittest discover -s tests -v
```

Os testes usam um banco temporário separado do banco da aplicação.
