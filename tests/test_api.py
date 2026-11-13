import os
from pathlib import Path
import tempfile
import unittest
import sqlite3

from fastapi.testclient import TestClient
import app.main as modulo


class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.path_original = modulo.DB_PATH
        modulo.DB_PATH = Path(cls.temp.name) / 'teste.db'
        cls.client = TestClient(modulo.app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        modulo.DB_PATH = cls.path_original
        cls.temp.cleanup()

    def test_catalogo_e_cinco_treinadores(self):
        self.assertEqual(len(self.client.get('/treinadores').json()), 5)
        self.assertEqual(self.client.get('/pokemon/25').json()['nome'], 'Pikachu')

    def test_criar_atualizar_e_recomendar(self):
        response = self.client.post('/treinadores', json={'nome': 'Teste', 'tipos': ['Poison'], 'estilo': 'tipo', 'incluir_lendarios': False})
        self.assertEqual(response.status_code, 201)
        treinador = response.json()['id']
        time = self.client.get(f'/treinadores/{treinador}/time').json()['time']
        self.assertEqual(len(time), 6)
        self.assertTrue(all('Poison' in (p['tipo1'], p['tipo2']) for p in time))
        self.assertTrue(all(not p['lendario'] for p in time))
        response = self.client.put(f'/treinadores/{treinador}/preferencias', json={'tipos': ['Water'], 'estilo': 'defesa'})
        self.assertEqual(response.json()['tipos'], ['Water'])
        self.assertEqual(response.json()['estilo'], 'defesa')

    def test_erros_e_avaliacao(self):
        self.assertEqual(self.client.get('/pokemon/999999').status_code, 404)
        self.assertEqual(self.client.post('/treinadores', json={'nome': 'X', 'tipos': ['Inexistente']}).status_code, 422)
        self.assertEqual(self.client.post('/treinadores/1/avaliacoes', json={'pokemon_id': 25, 'nota': 6}).status_code, 422)
        self.assertEqual(self.client.post('/treinadores/1/avaliacoes', json={'pokemon_id': 25, 'nota': 4}).status_code, 200)

    def test_cadastro_objeto(self):
        r = self.client.post('/objetos', json={'nome': 'Pokébola de teste', 'categoria': 'captura', 'descricao': 'Exemplo.'})
        self.assertEqual(r.status_code, 201)
        self.assertTrue(any(x['nome'] == 'Pokébola de teste' for x in self.client.get('/objetos').json()))

    def test_interface_e_recursos_estaticos(self):
        self.assertIn('Seu treinador', self.client.get('/').text)
        self.assertEqual(self.client.get('/static/app.js').status_code, 200)
        self.assertEqual(self.client.get('/static/style.css').status_code, 200)
        self.assertEqual(self.client.get('/static/catalog.css').status_code, 200)

    def test_preferencias_persistem_e_alteram_time(self):
        treinador = self.client.post('/treinadores', json={'nome': 'Persistência', 'tipos': ['Water'], 'estilo': 'tipo'}).json()
        anterior = self.client.get(f"/treinadores/{treinador['id']}/time").json()['time']
        resposta = self.client.put(f"/treinadores/{treinador['id']}/preferencias", json={'tipos': ['Fire'], 'estilo': 'tipo', 'incluir_lendarios': False})
        self.assertEqual(resposta.status_code, 200)
        modulo.inicializar()
        depois = self.client.get(f"/treinadores/{treinador['id']}/time").json()
        self.assertEqual(depois['treinador']['tipos'], ['Fire'])
        self.assertFalse(depois['treinador']['incluir_lendarios'])
        self.assertNotEqual([p['id'] for p in anterior], [p['id'] for p in depois['time']])

    def test_cadastrar_pokemon_e_persistir(self):
        pokemon = {'id': 9999, 'nome': 'PokemonTeste', 'tipo1': 'Water', 'hp': 50, 'ataque': 55, 'defesa': 60, 'velocidade': 45, 'ataque_especial': 40, 'defesa_especial': 50, 'geracao': 1, 'lendario': False, 'cor': 'Blue', 'tem_genero': True, 'prob_macho': 0.5, 'grupo_ovo1': 'Water 1', 'tem_megaevolucao': False, 'altura_m': 0.7, 'peso_kg': 10.0, 'taxa_captura': 45, 'estilo_corpo': 'quadruped'}
        self.assertEqual(self.client.post('/pokemon', json=pokemon).status_code, 201)
        salvo = self.client.get('/pokemon/9999').json()
        self.assertEqual(salvo['nome'], 'PokemonTeste')
        self.assertEqual(salvo['total'], 300)
        self.assertIsNone(salvo['imagem_url'])
        self.assertEqual(self.client.post('/pokemon', json=pokemon).status_code, 409)
        modulo.inicializar()
        self.assertEqual(self.client.get('/pokemon/9999').json()['nome'], 'PokemonTeste')

    def test_catalogo_original_tem_metadados_e_imagem(self):
        pokemon = self.client.get('/pokemon/25').json()
        self.assertEqual(pokemon['nome'], 'Pikachu')
        self.assertEqual(pokemon['cor'], 'Yellow')
        self.assertTrue(pokemon['imagem_url'].endswith('/25.png'))

    def test_pokemon_requer_metadados_obrigatorios(self):
        response = self.client.post('/pokemon', json={'id': 9998, 'nome': 'Incompleto', 'tipo1': 'Water', 'hp': 50, 'ataque': 55, 'defesa': 60, 'velocidade': 45, 'ataque_especial': 40, 'defesa_especial': 50, 'geracao': 1})
        self.assertEqual(response.status_code, 422)

    def test_pokemon_personalizado_guarda_imagem_informada(self):
        pokemon = {'id': 9997, 'nome': 'Ilustrado', 'tipo1': 'Fire', 'hp': 50, 'ataque': 55, 'defesa': 60, 'velocidade': 45, 'ataque_especial': 40, 'defesa_especial': 50, 'geracao': 1, 'lendario': False, 'cor': 'Red', 'tem_genero': False, 'grupo_ovo1': 'Undiscovered', 'tem_megaevolucao': False, 'altura_m': 0.7, 'peso_kg': 10, 'taxa_captura': 45, 'estilo_corpo': 'quadruped', 'imagem_url': 'https://example.com/pokemon.png'}
        resposta = self.client.post('/pokemon', json=pokemon)
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(self.client.get('/pokemon/9997').json()['imagem_url'], 'https://example.com/pokemon.png')

    def test_migracao_preserva_pokemon_cadastrado_e_treinadores(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / 'antigo.db'
            with sqlite3.connect(caminho) as c:
                c.executescript('''
                    CREATE TABLE pokemon (id INTEGER PRIMARY KEY, nome TEXT NOT NULL UNIQUE, tipo1 TEXT NOT NULL, tipo2 TEXT, hp INTEGER NOT NULL, ataque INTEGER NOT NULL, defesa INTEGER NOT NULL, velocidade INTEGER NOT NULL, ataque_especial INTEGER NOT NULL, defesa_especial INTEGER NOT NULL, geracao INTEGER NOT NULL, lendario INTEGER NOT NULL);
                    CREATE TABLE configuracao (chave TEXT PRIMARY KEY, valor TEXT NOT NULL);
                    CREATE TABLE treinadores (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, tipos TEXT NOT NULL, estilo TEXT NOT NULL, lendarios INTEGER NOT NULL DEFAULT 1);
                    INSERT INTO pokemon VALUES (25, 'Pikachu', 'Electric', NULL, 35, 55, 40, 90, 50, 50, 1, 0);
                    INSERT INTO pokemon VALUES (9999, 'Criado pelo usuário', 'Water', NULL, 50, 55, 60, 45, 40, 50, 1, 0);
                    INSERT INTO treinadores VALUES (42, 'Salvo', '["Water"]', 'defesa', 1);
                    INSERT INTO configuracao VALUES ('dados_iniciais', '1');
                ''')
            anterior = modulo.DB_PATH
            try:
                modulo.DB_PATH = caminho
                modulo.inicializar()
                modulo.inicializar()
                with modulo.conectar() as c:
                    self.assertEqual(c.execute('SELECT nome FROM treinadores WHERE id=42').fetchone()['nome'], 'Salvo')
                    custom = c.execute('SELECT * FROM pokemon WHERE id=9999').fetchone()
                    self.assertEqual(custom['nome'], 'Criado pelo usuário')
                    self.assertIsNone(custom['imagem_url'])
                    self.assertEqual(c.execute('SELECT cor FROM pokemon WHERE id=25').fetchone()['cor'], 'Yellow')
            finally:
                modulo.DB_PATH = anterior


if __name__ == '__main__':
    unittest.main()
