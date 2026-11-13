import os
from pathlib import Path
import tempfile
import unittest

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
        pokemon = {'id': 9999, 'nome': 'PokemonTeste', 'tipo1': 'Water', 'hp': 50, 'ataque': 55, 'defesa': 60, 'velocidade': 45, 'ataque_especial': 40, 'defesa_especial': 50, 'geracao': 1, 'lendario': False}
        self.assertEqual(self.client.post('/pokemon', json=pokemon).status_code, 201)
        self.assertEqual(self.client.get('/pokemon/9999').json()['nome'], 'PokemonTeste')
        self.assertEqual(self.client.post('/pokemon', json=pokemon).status_code, 409)
        modulo.inicializar()
        self.assertEqual(self.client.get('/pokemon/9999').json()['nome'], 'PokemonTeste')


if __name__ == '__main__':
    unittest.main()
