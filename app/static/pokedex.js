const form = document.querySelector('#pokedex-busca');
const searchInput = document.querySelector('#pokedex-termo');
const grid = document.querySelector('#pokedex-resultados');
const count = document.querySelector('#pokedex-contagem');
const message = document.querySelector('#pokedex-mensagem');
const more = document.querySelector('#pokedex-mais');
const dialog = document.querySelector('#pokemon-detalhes');
const details = document.querySelector('#detalhes-conteudo');
const pageSize = 24;
const names = {Normal:'Normal',Fire:'Fogo',Water:'Água',Electric:'Elétrico',Grass:'Planta',Ice:'Gelo',Fighting:'Lutador',Poison:'Veneno',Ground:'Terra',Flying:'Voador',Psychic:'Psíquico',Bug:'Inseto',Rock:'Pedra',Ghost:'Fantasma',Dragon:'Dragão',Dark:'Sombrio',Steel:'Aço',Fairy:'Fada'};
const colors = {Fire:'#fcf0e8',Water:'#ebf4fb',Grass:'#edf6eb',Electric:'#fbf8e6',Poison:'#f4edf8',Psychic:'#fceef2',Ice:'#ebf8f8',Dragon:'#eef0fb',Fighting:'#faf0e9',Flying:'#f0f1f9',Rock:'#f7f3e9',Ground:'#f8f2e7',Ghost:'#f1edf6',Bug:'#f1f6e7',Dark:'#f1efed',Steel:'#eef2f2',Fairy:'#fcf0f5',Normal:'#f5f5f1'};
let offset = 0;
let query = '';
let loading = false;
let requestId = 0;

function create(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = String(text);
  return node;
}

function visualFor(pokemon, className) {
  const visual = create('div', className);
  visual.style.background = colors[pokemon.tipo1] || '#f5f5f1';
  const number = create('span', 'pokemon-number', `#${String(pokemon.id).padStart(3, '0')}`);
  const placeholder = create('span', 'pokemon-image-placeholder', '◉');
  placeholder.setAttribute('aria-hidden', 'true');
  visual.append(number, placeholder);
  if (pokemon.imagem_url) {
    const image = document.createElement('img');
    image.alt = `Ilustração de ${pokemon.nome}`;
    image.loading = 'lazy';
    image.referrerPolicy = 'no-referrer';
    image.addEventListener('load', () => { placeholder.hidden = true; });
    image.addEventListener('error', () => { image.hidden = true; });
    image.src = pokemon.imagem_url;
    visual.append(image);
  }
  return visual;
}

function renderCard(pokemon) {
  const button = create('button', 'pokedex-card');
  button.type = 'button';
  button.setAttribute('aria-label', `Ver detalhes de ${pokemon.nome}`);
  const visual = visualFor(pokemon, 'pokedex-visual');
  const body = create('div', 'pokedex-card-body');
  body.append(create('h3', '', pokemon.nome));
  const types = create('div', 'pokemon-types');
  for (const type of [pokemon.tipo1, pokemon.tipo2].filter(Boolean)) types.append(create('span', 'type-tag', names[type] || type));
  body.append(types, create('span', 'pokedex-card-link', 'Ver detalhes ↗'));
  button.append(visual, body);
  button.addEventListener('click', () => openDetails(pokemon.id));
  return button;
}

function readable(value, suffix = '') {
  return value === null || value === undefined || value === '' ? 'Não informado' : `${value}${suffix}`;
}

function booleanLabel(value) {
  return value === null || value === undefined ? 'Não informado' : value ? 'Sim' : 'Não';
}

function addDetail(list, label, value) {
  const block = create('div', 'detail-item');
  block.append(create('dt', '', label), create('dd', '', value));
  list.append(block);
}

async function openDetails(id) {
  document.querySelector('#detalhes-titulo').textContent = 'Carregando...';
  details.replaceChildren();
  if (!dialog.open) dialog.showModal();
  try {
    const response = await fetch(`/pokemon/${encodeURIComponent(id)}`);
    if (!response.ok) throw new Error('Não foi possível carregar os detalhes.');
    const pokemon = await response.json();
    document.querySelector('#detalhes-titulo').textContent = pokemon.nome;
    const layout = create('div', 'detail-layout');
    layout.append(visualFor(pokemon, 'detail-visual'));
    const content = create('div', 'detail-body');
    const types = create('div', 'pokemon-types');
    for (const type of [pokemon.tipo1, pokemon.tipo2].filter(Boolean)) types.append(create('span', 'type-tag', names[type] || type));
    content.append(types);
    const stats = create('dl', 'detail-stats');
    for (const [label, field] of [['Vida','hp'],['Ataque','ataque'],['Defesa','defesa'],['Ataque especial','ataque_especial'],['Defesa especial','defesa_especial'],['Velocidade','velocidade']]) addDetail(stats, label, readable(pokemon[field]));
    content.append(create('h3', 'detail-subtitle', 'Atributos base'), stats);
    const metadata = create('dl', 'detail-metadata');
    const entries = [
      ['Total de atributos', readable(pokemon.total)], ['Geração', readable(pokemon.geracao)],
      ['Lendário', booleanLabel(pokemon.lendario)], ['Cor', readable(pokemon.cor)],
      ['Possui gênero', booleanLabel(pokemon.tem_genero)],
      ['Probabilidade de ser macho', pokemon.prob_macho == null ? 'Não informado' : `${(Number(pokemon.prob_macho) * 100).toLocaleString('pt-BR', {maximumFractionDigits: 2})}%`],
      ['Grupo de ovo principal', readable(pokemon.grupo_ovo1)], ['Segundo grupo de ovo', readable(pokemon.grupo_ovo2)],
      ['Megaevolução', booleanLabel(pokemon.tem_megaevolucao)], ['Altura', readable(pokemon.altura_m, ' m')],
      ['Peso', readable(pokemon.peso_kg, ' kg')], ['Taxa de captura', readable(pokemon.taxa_captura)],
      ['Formato corporal', readable(pokemon.estilo_corpo)]
    ];
    for (const [label, value] of entries) addDetail(metadata, label, value);
    content.append(create('h3', 'detail-subtitle', 'Mais informações'), metadata);
    layout.append(content); details.replaceChildren(layout);
  } catch (error) {
    document.querySelector('#detalhes-titulo').textContent = 'Detalhes indisponíveis';
    details.replaceChildren(create('p', 'pokedex-message', error.message));
  }
}

async function loadPage(reset = false) {
  if (loading && !reset) return;
  const current = ++requestId;
  if (reset) { offset = 0; grid.replaceChildren(); }
  loading = true;
  more.hidden = true;
  message.textContent = '';
  count.textContent = 'Buscando Pokémon...';
  try {
    const params = new URLSearchParams({busca: query, limite: String(pageSize + 1), offset: String(offset)});
    const response = await fetch(`/pokemon?${params}`);
    if (!response.ok) throw new Error('Não foi possível carregar o catálogo. Tente novamente.');
    const pokemon = await response.json();
    if (current !== requestId) return;
    const page = pokemon.slice(0, pageSize);
    for (const item of page) grid.append(renderCard(item));
    offset += page.length;
    count.textContent = `${offset} ${offset === 1 ? 'Pokémon exibido' : 'Pokémon exibidos'}`;
    more.hidden = pokemon.length <= pageSize;
    if (offset === 0) message.textContent = 'Nenhum Pokémon encontrado. Tente outro nome ou número.';
  } catch (error) {
    if (current === requestId) {
      count.textContent = '';
      message.textContent = error.message || 'Não foi possível carregar o catálogo.';
      more.hidden = false;
      more.firstChild.textContent = 'Tentar novamente ';
    }
  } finally {
    if (current === requestId) loading = false;
  }
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  query = searchInput.value.trim();
  more.firstChild.textContent = 'Carregar mais Pokémon ';
  loadPage(true);
});
searchInput.addEventListener('search', () => {
  if (!searchInput.value) { query = ''; loadPage(true); }
});
more.addEventListener('click', () => { more.firstChild.textContent = 'Carregar mais Pokémon '; loadPage(); });
document.querySelector('#fechar-detalhes').addEventListener('click', () => dialog.close());
window.addEventListener('pokemon:cadastrado', () => loadPage(true));
loadPage(true);
