const $ = (selector) => document.querySelector(selector);
const form = $('#treinador-form');
const picker = $('#treinador-existente');
const result = $('#resultado');
const dashboard = $('#dashboard');
const message = $('#mensagem');
const typeNames = {Normal:'Normal',Fire:'Fogo',Water:'Água',Electric:'Elétrico',Grass:'Planta',Ice:'Gelo',Fighting:'Lutador',Poison:'Veneno',Ground:'Terra',Flying:'Voador',Psychic:'Psíquico',Bug:'Inseto',Rock:'Pedra',Ghost:'Fantasma',Dragon:'Dragão',Dark:'Sombrio',Steel:'Aço',Fairy:'Fada'};
const typeColors = {Fire:'#fcf0e8',Water:'#ebf4fb',Grass:'#edf6eb',Electric:'#fbf8e6',Poison:'#f4edf8',Psychic:'#fceef2',Ice:'#ebf8f8',Dragon:'#eef0fb',Fighting:'#faf0e9',Flying:'#f0f1f9',Rock:'#f7f3e9',Ground:'#f8f2e7',Ghost:'#f1edf6',Bug:'#f1f6e7',Dark:'#f1efed',Steel:'#eef2f2',Fairy:'#fcf0f5',Normal:'#f5f5f1'};
let trainers = [];
let selectedId = null;
let dirty = true;

async function request(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let detail;
    try { detail = (await response.json()).detail; } catch { detail = null; }
    throw new Error(typeof detail === 'string' ? detail : `Erro ${response.status}. Tente novamente.`);
  }
  return response.json();
}

function setMessage(text, isError = false) {
  message.textContent = text;
  message.classList.toggle('error', isError);
}

function resetResults(text = 'Escolha suas preferências para começar a descoberta.') {
  result.replaceChildren();
  const empty = document.createElement('div'); empty.className = 'empty-state';
  const icon = document.createElement('div'); icon.className = 'empty-ball'; icon.setAttribute('aria-hidden', 'true'); icon.textContent = '◉';
  const heading = document.createElement('b'); heading.textContent = 'Seu time está esperando';
  const description = document.createElement('span'); description.textContent = text;
  empty.append(icon, heading, description); result.append(empty);
  dashboard.replaceChildren(); dashboard.hidden = true; $('#painel-vazio').hidden = false;
}

function typesSelected() {
  return [...document.querySelectorAll('#tipos input:checked')].map((input) => input.value);
}

function makeTypeOptions(types) {
  const container = $('#tipos'); container.replaceChildren();
  for (const type of types) {
    const label = document.createElement('label'); label.className = 'type-option';
    const input = document.createElement('input'); input.type = 'checkbox'; input.value = type; input.name = 'tipos';
    const text = document.createElement('span'); text.textContent = typeNames[type] || type;
    label.append(input, text); container.append(label);
  }
}

async function loadTrainers(selectId = null) {
  trainers = await request('/treinadores');
  picker.replaceChildren(new Option('+ Criar novo treinador', ''));
  for (const trainer of trainers) picker.add(new Option(`${trainer.nome} · #${trainer.id}`, String(trainer.id)));
  picker.value = selectId ? String(selectId) : '';
}

function selectTrainer() {
  const trainer = trainers.find((item) => String(item.id) === picker.value);
  selectedId = trainer?.id ?? null;
  $('#nome').value = trainer?.nome ?? '';
  $('#nome').readOnly = Boolean(trainer);
  $('#nome').title = trainer ? 'A API atual permite editar preferências, não o nome.' : '';
  $('#estilo').value = trainer?.estilo ?? 'equilibrado';
  $('#lendarios').checked = trainer?.incluir_lendarios ?? true;
  document.querySelectorAll('#tipos input').forEach((input) => { input.checked = trainer?.tipos.includes(input.value) ?? false; });
  dirty = !trainer;
  $('#descobrir').disabled = !trainer;
  $('#salvar span').textContent = trainer ? 'Salvar preferências' : 'Salvar treinador';
  $('#confirmacao').textContent = trainer ? `Tudo pronto, ${trainer.nome}!` : 'Quem vai entrar para o seu time?';
  $('#instrucao').textContent = trainer ? 'Atualize suas preferências ou encontre seu time.' : 'Salve seu treinador para desbloquear as recomendações.';
  $('#estado').textContent = trainer ? 'PERFIL SELECIONADO' : 'PRONTO PARA COMEÇAR';
  setMessage(''); resetResults();
}

function markDirty() {
  dirty = true;
  $('#descobrir').disabled = true;
  if (selectedId) {
    setMessage('Salve as alterações antes de buscar novamente.');
    $('#instrucao').textContent = 'Suas preferências mudaram. Salve para atualizar seu time.';
    resetResults('Salve suas preferências para gerar um novo time.');
  }
}

form.addEventListener('input', markDirty);
form.addEventListener('change', markDirty);
picker.addEventListener('change', selectTrainer);
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const name = $('#nome').value.trim();
  if (!name) { setMessage('Informe o nome do treinador.', true); return; }
  const preferences = {tipos: typesSelected(), estilo: $('#estilo').value, incluir_lendarios: $('#lendarios').checked};
  const button = $('#salvar'); button.disabled = true; setMessage('Salvando...');
  try {
    const editing = selectedId !== null;
    const trainer = await request(editing ? `/treinadores/${selectedId}/preferencias` : '/treinadores', {
      method: editing ? 'PUT' : 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(editing ? preferences : {...preferences, nome: name})
    });
    selectedId = trainer.id; dirty = false;
    await loadTrainers(trainer.id);
    selectTrainer();
    setMessage(editing ? 'Preferências atualizadas com sucesso.' : 'Treinador salvo! Pronto para descobrir seu time?');
  } catch (error) { setMessage(error.message, true); }
  finally { button.disabled = false; }
});

function element(tag, className, text) {
  const node = document.createElement(tag); if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderTeam(team) {
  result.replaceChildren();
  if (!team.length) { resetResults('Nenhum Pokémon disponível com essas preferências.'); return; }
  for (const pokemon of team) {
    const card = element('article', 'pokemon-card');
    const visual = element('div', 'pokemon-visual'); visual.style.background = typeColors[pokemon.tipo1] || '#f5f5f1';
    const number = element('span', 'pokemon-number', `#${String(pokemon.id).padStart(3, '0')}`);
    const image = document.createElement('img'); image.alt = `Ilustração de ${pokemon.nome}`;
    image.loading = 'lazy'; image.src = `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${encodeURIComponent(pokemon.id)}.png`;
    image.addEventListener('error', () => { image.hidden = true; });
    visual.append(number, image);
    const info = element('div', 'pokemon-info'); info.append(element('h4', '', pokemon.nome));
    const types = element('div', 'pokemon-types');
    for (const type of [pokemon.tipo1, pokemon.tipo2].filter(Boolean)) types.append(element('span', 'type-tag', typeNames[type] || type));
    const score = element('div', 'pokemon-score', 'AFINIDADE'); score.append(element('strong', '', `${Math.round(pokemon.score * 100)}%`));
    info.append(types, score); card.append(visual, info); result.append(card);
  }
}

const metrics = [
  {key:'hp', label:'Vida', icon:'♡', color:'#e96b64', background:'#fcedea'},
  {key:'ataque', label:'Ataque', icon:'⚔', color:'#e4a74c', background:'#fff5e4'},
  {key:'defesa', label:'Defesa', icon:'⬡', color:'#6e99bf', background:'#eaf3fa'},
  {key:'velocidade', label:'Velocidade', icon:'ϟ', color:'#6aaf8c', background:'#eaf7ef'}
];
const svgNS = 'http://www.w3.org/2000/svg';
function svgElement(tag, attributes) {
  const node = document.createElementNS(svgNS, tag);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, String(value));
  return node;
}

function renderDashboard(team) {
  dashboard.replaceChildren();
  if (!team.length) { dashboard.hidden = true; $('#painel-vazio').hidden = false; return; }
  dashboard.hidden = false; $('#painel-vazio').hidden = true;
  for (const metric of metrics) {
    const values = team.map((pokemon) => Number(pokemon[metric.key]));
    const average = values.reduce((sum, value) => sum + value, 0) / values.length;
    const card = element('article', 'chart-card'); card.style.setProperty('--chart-color', metric.color); card.style.setProperty('--chart-bg', metric.background);
    const top = element('div', 'chart-top'); const heading = element('div');
    heading.append(element('p', 'chart-title', `Média de ${metric.label.toLowerCase()}`));
    const number = element('div', 'chart-number', average.toLocaleString('pt-BR', {maximumFractionDigits: 1})); number.append(element('span', 'chart-unit', 'pontos'));
    heading.append(number); top.append(heading, element('span', 'chart-icon', metric.icon)); card.append(top);
    card.append(element('p', 'chart-description', `${metric.label} base por Pokémon do time`));
    const svg = svgElement('svg', {viewBox:'0 0 420 140', class:'chart-svg', role:'img', 'aria-label': `${metric.label} por Pokémon: ${team.map((p, i) => `${p.nome}: ${values[i]}`).join(', ')}. Média ${average.toFixed(1)}.`});
    const max = Math.max(1, ...values) * 1.15; const bottom = 118, topY = 8, left = 30, right = 408;
    for (let step = 0; step < 3; step++) {
      const y = topY + (bottom - topY) * step / 2;
      svg.append(svgElement('line', {x1:left, y1:y, x2:right, y2:y, class:'chart-grid'}));
      const label = svgElement('text', {x:0, y:y + 3, class:'chart-axis'}); label.textContent = String(Math.round(max * (1 - step / 2))); svg.append(label);
    }
    const points = values.map((value, i) => [values.length === 1 ? (left + right) / 2 : left + i * (right - left) / (values.length - 1), bottom - value / max * (bottom - topY)]);
    const path = points.map(([x,y], i) => `${i ? 'L' : 'M'} ${x} ${y}`).join(' ');
    svg.append(svgElement('path', {d:`${path} L ${points.at(-1)[0]} ${bottom} L ${points[0][0]} ${bottom} Z`, class:'chart-area'}));
    svg.append(svgElement('path', {d:path, class:'chart-line'}));
    for (const [x,y] of points) svg.append(svgElement('circle', {cx:x, cy:y, r:4, class:'chart-point'}));
    card.append(svg);
    const labels = element('div', 'chart-labels');
    for (const pokemon of team) { const label = element('span', '', pokemon.nome); label.title = pokemon.nome; labels.append(label); }
    card.append(labels); dashboard.append(card);
  }
}

$('#descobrir').addEventListener('click', async () => {
  if (!selectedId || dirty) return;
  const button = $('#descobrir'); button.disabled = true; $('#estado').textContent = 'BUSCANDO';
  try {
    const data = await request(`/treinadores/${selectedId}/time`);
    renderTeam(data.time); renderDashboard(data.time);
    $('#confirmacao').textContent = `O time de ${data.treinador.nome}`;
    $('#instrucao').textContent = data.time.length ? `${data.time.length} Pokémon selecionados para você.` : 'Nenhum Pokémon disponível para esta seleção.';
    $('#estado').textContent = data.time.length ? 'TIME ENCONTRADO' : 'SEM RESULTADOS';
  } catch (error) { setMessage(error.message, true); $('#estado').textContent = 'ERRO NA BUSCA'; }
  finally { button.disabled = false; }
});

try {
  const options = await request('/opcoes'); makeTypeOptions(options.tipos);
  await loadTrainers();
} catch (error) { setMessage(`Não foi possível carregar os dados: ${error.message}`, true); }
