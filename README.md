<div align="center">

# ⚡ PokéMatch

### Um time com a sua cara.

Um projeto acadêmico de recomendação híbrida que combina o perfil de treinadores<br>
com características e avaliações de Pokémon para sugerir um time personalizado.

**[Começar](#-comece-por-aqui)** · **[Funcionalidades](#-o-que-você-pode-fazer)** · **[Modelo](#-como-funciona-a-recomendação)** · **[Dataset](#-sobre-os-dados)**

</div>

---

## ✦ Sobre o projeto

O PokéMatch é um protótipo para estudar sistemas de recomendação, APIs, persistência de dados, testes e containerização. O usuário cria um treinador, escolhe suas preferências e recebe **até seis Pokémon** ordenados por afinidade.

> **Projeto acadêmico:** os cinco treinadores iniciais e suas avaliações são fictícios. As recomendações demonstram o funcionamento do modelo e não foram validadas com jogadores reais.

**Tecnologias:** Python · FastAPI · SQLite · JavaScript · Docker

## 🚀 Comece por aqui

Com Docker e Docker Compose instalados, execute na pasta do projeto:

```bash
docker compose up --build
```

| Acesso local | Endereço |
| --- | --- |
| Aplicação | [localhost:8000](http://localhost:8000) |
| Documentação interativa da API | [localhost:8000/docs](http://localhost:8000/docs) |

Os treinadores, as preferências, as avaliações e os cadastros são salvos em um volume Docker. Para parar a aplicação, pressione `Ctrl+C`; os dados permanecem no volume.

<details>
<summary><strong>Executar sem Docker</strong></summary>

Com Python 3.10 ou superior:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

No Windows, ative o ambiente com `.venv\Scripts\activate`. A aplicação usa SQLite e cria o banco local na primeira execução.

</details>

## 🎮 O que você pode fazer

<details>
<summary><strong>01 · Criar e editar um treinador</strong></summary>

- Escolher um nome, tipos favoritos e um estilo de jogo: equilibrado, ataque, defesa, velocidade ou prioridade aos tipos.
- Definir se Pokémon lendários podem aparecer nas recomendações.
- Selecionar um treinador salvo, alterar suas preferências e gerar o time novamente. A interface atual não oferece edição do nome.
- Registrar avaliações de 1 a 5 pela API para alimentar o componente colaborativo.

Os cinco perfis iniciais — Lia, Caio, Bianca, Rafael e Sofia — são exemplos fictícios.

</details>

<details>
<summary><strong>02 · Descobrir e analisar um time</strong></summary>

- Receber até seis Pokémon de acordo com as preferências e as interações disponíveis.
- Visualizar os atributos base de vida, ataque, defesa e velocidade em gráficos de linhas.
- Acompanhar a média de cada atributo para os Pokémon exibidos no time.
- Alterar as preferências e executar novamente a busca.

Os gráficos mostram os atributos dos Pokémon recomendados; eles não representam evolução temporal ou desempenho em batalhas.

</details>

<details>
<summary><strong>03 · Cadastrar e consultar Pokémon</strong></summary>

- Procurar Pokémon na API por nome ou consultar um item pelo número da Pokédex.
- Adicionar Pokémon na página ou pela API, preenchendo os atributos obrigatórios do catálogo.
- Calcular automaticamente o total dos seis atributos de batalha. Segundo tipo e segundo grupo de ovo são opcionais; a probabilidade de ser macho é exigida quando o Pokémon possui gênero.
- Informar opcionalmente um link direto de imagem. Sem ele, o cartão mostra um símbolo de substituição.

Um Pokémon cadastrado passa a fazer parte do catálogo usado nas próximas recomendações. A API exige os novos metadados obrigatórios; clientes do formato anterior precisam enviar esses campos.

</details>

<details>
<summary><strong>04 · Cadastrar objetos</strong></summary>

Pela API, é possível registrar e listar objetos como Pokébolas e poções, informando nome, categoria e descrição. Esse catálogo é separado: **os objetos não entram no ranking de Pokémon** nesta versão.

</details>

## 🧠 Como funciona a recomendação

O modelo combina duas abordagens:

1. **Conteúdo:** compara tipos favoritos e estilo do treinador com os tipos e atributos base de cada Pokémon. Os atributos numéricos são normalizados usando 255 como referência.
2. **Colaborativo:** usa similaridade de cosseno entre avaliações para aproveitar padrões de treinadores com Pokémon avaliados em comum.

Quando há sinal colaborativo para um candidato, o resultado combina **70% de conteúdo e 30% de colaborativo**. Sem esse sinal — como ocorre com um treinador novo sem avaliações — a recomendação usa conteúdo.

Os pesos são escolhas didáticas, sem ajuste ou validação com usuários reais. O score é uma aproximação de afinidade individual: ele **não garante o melhor time competitivo**, a cobertura de tipos ou a sinergia entre os seis. Pokémon já avaliados ainda podem ser recomendados.

## 🔌 API

Todos os campos e operações podem ser experimentados no [Swagger](http://localhost:8000/docs), com a aplicação em execução.

<details>
<summary><strong>Ver endpoints disponíveis</strong></summary>

| Método | Endpoint | Função |
| --- | --- | --- |
| `GET` | `/opcoes` | Listar tipos e estilos disponíveis. |
| `GET` | `/treinadores` | Listar treinadores salvos. |
| `POST` | `/treinadores` | Criar um treinador. |
| `PUT` | `/treinadores/{id}/preferencias` | Atualizar preferências. |
| `GET` | `/treinadores/{id}/time` | Obter até seis Pokémon; aceita `estilo` opcional. |
| `POST` | `/treinadores/{id}/avaliacoes` | Registrar ou atualizar uma avaliação. |
| `GET` | `/pokemon` | Buscar Pokémon; aceita `busca` e `limite`. |
| `GET` | `/pokemon/{id}` | Consultar os dados de um Pokémon. |
| `POST` | `/pokemon` | Cadastrar Pokémon. |
| `GET` | `/objetos` | Listar objetos cadastrados. |
| `POST` | `/objetos` | Cadastrar um objeto. |

A aplicação é um protótipo local sem autenticação: quem tiver acesso a ela poderá consultar e alterar os perfis disponíveis.

</details>

## 🧪 Testes

<details>
<summary><strong>Executar testes automatizados</strong></summary>

Com as dependências do projeto instaladas no ambiente virtual:

```bash
pip install httpx
python -m unittest discover -s tests -v
```

Os testes usam um banco temporário, separado dos dados da aplicação.

</details>

## 📊 Sobre os dados

O catálogo inicial usa o dataset [Pokémon for Data Mining and Machine Learning](https://www.kaggle.com/datasets/alopez247/pokemon), de **Asier López Zorrilla**. O [CSV incluído no projeto](data/pokemon_alopez247.csv) contém **721 registros, 721 IDs únicos e 23 colunas**, das seis primeiras gerações.

Escolhemos essa base porque ela reúne tipos e atributos numéricos úteis para comparar Pokémon com as preferências do treinador, em um arquivo pequeno e fácil de reproduzir. Ela não cobre as gerações mais recentes nem representa separadamente todas as formas alternativas.

<details>
<summary><strong>Ver as 23 colunas do dataset</strong></summary>

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

O sistema importa as 23 colunas. O ranking utiliza **tipos, HP, ataque, defesa, ataque especial, defesa especial, velocidade e status lendário**; os demais campos ficam disponíveis para consulta. Pokémon criados antes da ampliação do catálogo preservam seus dados e podem ter metadados adicionais vazios.

</details>

<details>
<summary><strong>Imagens, créditos e licença</strong></summary>

As imagens dos Pokémon originais usam links dos [sprites da PokéAPI](https://github.com/PokeAPI/sprites), associados ao número da Pokédex e carregados pelo navegador. Elas dependem de conexão. Para um Pokémon novo, o link é opcional e deve ser informado no cadastro; o sistema não presume que o ID corresponda à imagem de outro Pokémon.

O dataset informa licença [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Pokémon, seus nomes e imagens pertencem aos respectivos titulares. Este repositório é um projeto acadêmico de fãs; consulte os termos das fontes antes de reutilizar seus conteúdos.

</details>

---

<div align="center"><sub>Feito para aprender, experimentar e descobrir novos times. ✦</sub></div>
