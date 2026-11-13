"""API de recomendação de Pokémon com treinadores fictícios e SQLite."""
from contextlib import asynccontextmanager
import csv
import json
import math
import os
from pathlib import Path
import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, HttpUrl, model_validator
from typing import Literal

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get('POKEMON_DB', ROOT / 'storage' / 'pokemon.db'))
TIPOS = ['Normal', 'Fire', 'Water', 'Electric', 'Grass', 'Ice', 'Fighting', 'Poison', 'Ground', 'Flying', 'Psychic', 'Bug', 'Rock', 'Ghost', 'Dragon', 'Dark', 'Steel', 'Fairy']
Estilo = Literal['equilibrado', 'ataque', 'defesa', 'velocidade', 'tipo']


def conectar():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def enriquecer_catalogo(c):
    """Adiciona metadados do CSV sem substituir Pokémon cadastrados pelo usuário."""
    colunas = {
        'total': 'INTEGER', 'cor': 'TEXT', 'tem_genero': 'INTEGER', 'prob_macho': 'REAL',
        'grupo_ovo1': 'TEXT', 'grupo_ovo2': 'TEXT', 'tem_megaevolucao': 'INTEGER',
        'altura_m': 'REAL', 'peso_kg': 'REAL', 'taxa_captura': 'INTEGER',
        'estilo_corpo': 'TEXT', 'imagem_url': 'TEXT',
    }
    existentes = {r['name'] for r in c.execute('PRAGMA table_info(pokemon)')}
    for nome, tipo in colunas.items():
        if nome not in existentes:
            c.execute(f'ALTER TABLE pokemon ADD COLUMN {nome} {tipo}')
    if c.execute("SELECT 1 FROM configuracao WHERE chave='metadados_csv_v1'").fetchone():
        return
    with (ROOT / 'data' / 'pokemon_alopez247.csv').open(encoding='utf-8', newline='') as arquivo:
        for p in csv.DictReader(arquivo):
            imagem = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{int(p['Number'])}.png"
            c.execute('''UPDATE pokemon SET total=?, cor=?, tem_genero=?, prob_macho=?, grupo_ovo1=?,
                grupo_ovo2=?, tem_megaevolucao=?, altura_m=?, peso_kg=?, taxa_captura=?, estilo_corpo=?, imagem_url=?
                WHERE id=? AND nome=?''',
                (int(p['Total']), p['Color'], int(p['hasGender'].lower() == 'true'),
                 float(p['Pr_Male']) if p['Pr_Male'] else None, p['Egg_Group_1'], p['Egg_Group_2'] or None,
                 int(p['hasMegaEvolution'].lower() == 'true'), float(p['Height_m']), float(p['Weight_kg']),
                 int(p['Catch_Rate']), p['Body_Style'], imagem, int(p['Number']), p['Name']))
    c.execute("INSERT INTO configuracao VALUES ('metadados_csv_v1', '1')")


def inicializar():
    with conectar() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS pokemon (id INTEGER PRIMARY KEY, nome TEXT NOT NULL UNIQUE, tipo1 TEXT NOT NULL, tipo2 TEXT, hp INTEGER NOT NULL, ataque INTEGER NOT NULL, defesa INTEGER NOT NULL, velocidade INTEGER NOT NULL, ataque_especial INTEGER NOT NULL, defesa_especial INTEGER NOT NULL, geracao INTEGER NOT NULL, lendario INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS treinadores (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, tipos TEXT NOT NULL, estilo TEXT NOT NULL, lendarios INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS avaliacoes (treinador_id INTEGER NOT NULL REFERENCES treinadores(id), pokemon_id INTEGER NOT NULL REFERENCES pokemon(id), nota INTEGER NOT NULL CHECK(nota BETWEEN 1 AND 5), PRIMARY KEY(treinador_id, pokemon_id));
        CREATE TABLE IF NOT EXISTS objetos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE, categoria TEXT NOT NULL, descricao TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS configuracao (chave TEXT PRIMARY KEY, valor TEXT NOT NULL);
        ''')
        if not c.execute("SELECT 1 FROM configuracao WHERE chave='dados_iniciais'").fetchone():
            with (ROOT / 'data' / 'pokemon_alopez247.csv').open(encoding='utf-8', newline='') as f:
                for p in csv.DictReader(f):
                    c.execute('INSERT INTO pokemon (id,nome,tipo1,tipo2,hp,ataque,defesa,velocidade,ataque_especial,defesa_especial,geracao,lendario) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (int(p['Number']), p['Name'], p['Type_1'], p['Type_2'] or None, int(p['HP']), int(p['Attack']), int(p['Defense']), int(p['Speed']), int(p['Sp_Atk']), int(p['Sp_Def']), int(p['Generation']), int(p['isLegendary'].lower() == 'true')))
            treinadores = [('Lia', ['Fire'], 'ataque', [4, 6, 37, 58, 77]), ('Caio', ['Water'], 'defesa', [7, 9, 54, 79, 131]), ('Bianca', ['Grass', 'Poison'], 'tipo', [1, 3, 43, 69, 25]), ('Rafael', ['Electric', 'Flying'], 'velocidade', [25, 26, 16, 21, 6]), ('Sofia', ['Psychic', 'Water'], 'equilibrado', [63, 65, 79, 120, 9])]
            for nome, tipos, estilo, favoritos in treinadores:
                cur = c.execute('INSERT INTO treinadores(nome, tipos, estilo, lendarios) VALUES (?,?,?,?)', (nome, json.dumps(tipos), estilo, 1))
                c.executemany('INSERT INTO avaliacoes VALUES (?,?,?)', [(cur.lastrowid, pid, 5) for pid in favoritos])
            c.execute("INSERT INTO configuracao VALUES ('dados_iniciais', '1')")
        enriquecer_catalogo(c)


@asynccontextmanager
async def lifespan(app):
    inicializar()
    yield


app = FastAPI(title='Pokémon: encontre seu time', version='1.0.0', lifespan=lifespan)
app.mount('/static', StaticFiles(directory=ROOT / 'app' / 'static'), name='static')


class Preferencias(BaseModel):
    tipos: list[str] = Field(default_factory=list, description='Tipos disponíveis em GET /opcoes.')
    estilo: Estilo = 'equilibrado'
    incluir_lendarios: bool = True


class TreinadorNovo(Preferencias):
    nome: str = Field(min_length=1, max_length=80)


class PokemonNovo(BaseModel):
    id: int = Field(ge=1)
    nome: str = Field(min_length=1, max_length=80)
    tipo1: str
    tipo2: str | None = None
    hp: int = Field(ge=1, le=255)
    ataque: int = Field(ge=1, le=255)
    defesa: int = Field(ge=1, le=255)
    velocidade: int = Field(ge=1, le=255)
    ataque_especial: int = Field(ge=1, le=255)
    defesa_especial: int = Field(ge=1, le=255)
    geracao: int = Field(ge=1)
    lendario: bool
    cor: str = Field(min_length=1, max_length=40)
    tem_genero: bool
    prob_macho: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    grupo_ovo1: str = Field(min_length=1, max_length=50)
    grupo_ovo2: str | None = Field(default=None, min_length=1, max_length=50)
    tem_megaevolucao: bool
    altura_m: float = Field(gt=0, allow_inf_nan=False)
    peso_kg: float = Field(gt=0, allow_inf_nan=False)
    taxa_captura: int = Field(ge=0, le=255)
    estilo_corpo: str = Field(min_length=1, max_length=80)
    imagem_url: HttpUrl | None = None

    @model_validator(mode='after')
    def validar_detalhes(self):
        if not self.nome.strip() or not self.cor.strip() or not self.grupo_ovo1.strip() or not self.estilo_corpo.strip():
            raise ValueError('Os campos de texto obrigatórios não podem conter apenas espaços.')
        if self.tem_genero and self.prob_macho is None:
            raise ValueError('Informe a probabilidade de ser macho para Pokémon com gênero.')
        if not self.tem_genero and self.prob_macho is not None:
            raise ValueError('A probabilidade de ser macho deve ficar vazia para Pokémon sem gênero.')
        if self.tipo2 and self.tipo1 == self.tipo2:
            raise ValueError('O segundo tipo deve ser diferente do primeiro.')
        return self


class Avaliacao(BaseModel):
    pokemon_id: int
    nota: int = Field(ge=1, le=5)


class ObjetoNovo(BaseModel):
    nome: str = Field(min_length=1)
    categoria: str = Field(min_length=1)
    descricao: str = Field(min_length=1)


def validar_tipos(tipos):
    invalidos = [t for t in tipos if t not in TIPOS]
    if invalidos:
        raise HTTPException(422, f'Tipos inválidos: {invalidos}; opções: {TIPOS}')


def obter_treinador(c, treinador_id):
    row = c.execute('SELECT * FROM treinadores WHERE id=?', (treinador_id,)).fetchone()
    if row is None:
        raise HTTPException(404, 'Treinador não encontrado.')
    p = dict(row)
    p['tipos'] = json.loads(p['tipos'])
    p['incluir_lendarios'] = bool(p.pop('lendarios'))
    return p


@app.get('/', response_class=HTMLResponse, include_in_schema=False)
def inicio():
    return (ROOT / 'app' / 'index.html').read_text(encoding='utf-8')


@app.get('/opcoes')
def opcoes():
    return {'tipos': TIPOS, 'estilos': ['equilibrado', 'ataque', 'defesa', 'velocidade', 'tipo']}


@app.get('/treinadores')
def listar_treinadores():
    with conectar() as c:
        return [obter_treinador(c, row['id']) for row in c.execute('SELECT id FROM treinadores ORDER BY id').fetchall()]


@app.post('/treinadores', status_code=201)
def criar_treinador(t: TreinadorNovo):
    validar_tipos(t.tipos)
    if not t.nome.strip():
        raise HTTPException(422, 'Nome não pode ser vazio.')
    with conectar() as c:
        cur = c.execute('INSERT INTO treinadores(nome, tipos, estilo, lendarios) VALUES (?,?,?,?)', (t.nome.strip(), json.dumps(t.tipos), t.estilo, int(t.incluir_lendarios)))
        return obter_treinador(c, cur.lastrowid)


@app.put('/treinadores/{treinador_id}/preferencias')
def atualizar_preferencias(treinador_id: int, p: Preferencias):
    validar_tipos(p.tipos)
    with conectar() as c:
        obter_treinador(c, treinador_id)
        c.execute('UPDATE treinadores SET tipos=?, estilo=?, lendarios=? WHERE id=?', (json.dumps(p.tipos), p.estilo, int(p.incluir_lendarios), treinador_id))
        return obter_treinador(c, treinador_id)


@app.get('/pokemon')
def listar_pokemon(busca: str = '', limite: int = 30):
    if not 1 <= limite <= 100:
        raise HTTPException(422, 'Limite deve estar entre 1 e 100.')
    with conectar() as c:
        return [dict(r) for r in c.execute('SELECT * FROM pokemon WHERE nome LIKE ? ORDER BY id LIMIT ?', (f'%{busca}%', limite))]


@app.get('/pokemon/{pokemon_id}')
def pokemon_detalhes(pokemon_id: int):
    with conectar() as c:
        p = c.execute('SELECT * FROM pokemon WHERE id=?', (pokemon_id,)).fetchone()
        if not p:
            raise HTTPException(404, 'Pokémon não encontrado.')
        return dict(p)


@app.post('/pokemon', status_code=201)
def criar_pokemon(p: PokemonNovo):
    validar_tipos([t for t in [p.tipo1, p.tipo2] if t])
    try:
        with conectar() as c:
            c.execute('''INSERT INTO pokemon (id,nome,tipo1,tipo2,hp,ataque,defesa,velocidade,
                ataque_especial,defesa_especial,geracao,lendario,total,cor,tem_genero,prob_macho,
                grupo_ovo1,grupo_ovo2,tem_megaevolucao,altura_m,peso_kg,taxa_captura,estilo_corpo,imagem_url)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (p.id, p.nome.strip(), p.tipo1, p.tipo2, p.hp, p.ataque, p.defesa, p.velocidade,
                 p.ataque_especial, p.defesa_especial, p.geracao, int(p.lendario),
                 p.hp + p.ataque + p.defesa + p.ataque_especial + p.defesa_especial + p.velocidade,
                 p.cor.strip(), int(p.tem_genero), p.prob_macho, p.grupo_ovo1.strip(),
                 p.grupo_ovo2.strip() if p.grupo_ovo2 else None, int(p.tem_megaevolucao),
                 p.altura_m, p.peso_kg, p.taxa_captura, p.estilo_corpo.strip(),
                 str(p.imagem_url) if p.imagem_url else None))
    except sqlite3.IntegrityError:
        raise HTTPException(409, 'ID ou nome de Pokémon já existe.')
    return pokemon_detalhes(p.id)


@app.post('/treinadores/{treinador_id}/avaliacoes')
def avaliar_pokemon(treinador_id: int, a: Avaliacao):
    with conectar() as c:
        obter_treinador(c, treinador_id)
        if not c.execute('SELECT 1 FROM pokemon WHERE id=?', (a.pokemon_id,)).fetchone():
            raise HTTPException(404, 'Pokémon não encontrado.')
        c.execute('INSERT INTO avaliacoes VALUES (?,?,?) ON CONFLICT(treinador_id,pokemon_id) DO UPDATE SET nota=excluded.nota', (treinador_id, a.pokemon_id, a.nota))
    return {'treinador_id': treinador_id, **a.model_dump()}


@app.get('/objetos')
def listar_objetos():
    with conectar() as c:
        return [dict(r) for r in c.execute('SELECT * FROM objetos ORDER BY id')]


@app.post('/objetos', status_code=201)
def criar_objeto(objeto: ObjetoNovo):
    try:
        with conectar() as c:
            cur = c.execute('INSERT INTO objetos(nome,categoria,descricao) VALUES (?,?,?)', (objeto.nome, objeto.categoria, objeto.descricao))
            return {'id': cur.lastrowid, **objeto.model_dump()}
    except sqlite3.IntegrityError:
        raise HTTPException(409, 'Objeto já existe.')


@app.get('/treinadores/{treinador_id}/time')
def recomendar_time(treinador_id: int, estilo: Estilo | None = None):
    """Retorna até seis Pokémon diferentes. Colaborativo usa avaliações fictícias e reais registradas."""
    with conectar() as c:
        treinador = obter_treinador(c, treinador_id)
        pokemons = [dict(p) for p in c.execute('SELECT * FROM pokemon ORDER BY id')]
        ratings = c.execute('SELECT treinador_id,pokemon_id,nota FROM avaliacoes').fetchall()
    estilo = estilo or treinador['estilo']
    historicos = {}
    for r in ratings:
        historicos.setdefault(r['treinador_id'], {})[r['pokemon_id']] = r['nota']
    alvo = historicos.get(treinador_id, {})
    soma, pesos = {}, {}
    # Similaridade por cosseno das avaliações com notas explícitas; sem histórico, só conteúdo.
    for outro, notas in historicos.items():
        if outro == treinador_id or not alvo:
            continue
        comum = set(alvo) & set(notas)
        if not comum:
            continue
        produto = sum(alvo[i] * notas[i] for i in comum)
        norma = math.sqrt(sum(v*v for v in alvo.values()) * sum(v*v for v in notas.values()))
        sim = produto / norma if norma else 0
        for pid, nota in notas.items():
            if pid not in alvo:
                soma[pid] = soma.get(pid, 0) + sim * (nota / 5)
                pesos[pid] = pesos.get(pid, 0) + sim
    resultados = []
    for p in pokemons:
        if not treinador['incluir_lendarios'] and p['lendario']:
            continue
        afinidade = float(bool(set(treinador['tipos']) & {p['tipo1'], p['tipo2']})) if treinador['tipos'] else 0.5
        ataque = (p['ataque'] + p['ataque_especial']) / 2 / 255
        defesa = (p['defesa'] + p['defesa_especial'] + p['hp']) / 3 / 255
        velocidade = p['velocidade'] / 255
        estilo_score = {'ataque': ataque, 'defesa': defesa, 'velocidade': velocidade, 'equilibrado': (ataque + defesa + velocidade) / 3, 'tipo': afinidade}[estilo]
        conteudo = 0.5 * afinidade + 0.5 * estilo_score
        colaborativo = soma[p['id']] / pesos[p['id']] if p['id'] in pesos else None
        score = 0.7 * conteudo + 0.3 * colaborativo if colaborativo is not None else conteudo
        resultados.append({**p, 'score': round(score, 4), 'score_conteudo': round(conteudo, 4), 'score_colaborativo': round(colaborativo, 4) if colaborativo is not None else None})
    resultados.sort(key=lambda x: (-x['score'], x['id']))
    return {'treinador': treinador, 'estrategia': estilo, 'nota': 'Componente colaborativo baseado em interações disponíveis; usuários novos usam conteúdo.', 'time': resultados[:6]}
