// RxGap 지도 앱 로직: 데이터 로드, 지도 레이어, 순위 목록, 폐점 시뮬레이션.
const $ = (s, el = document) => el.querySelector(s);
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const fmt = (n) => (n == null ? '—' : Number(n).toLocaleString('en-US'));
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const STATUS_LABEL = { desert: 'Desert', 'near-desert': 'One closure away', covered: 'Covered' };

const state = { rule: 'state', selected: null, closed: null, timers: [] };
let D, BG, map, bgIndex;

// ---------- data ----------
async function load() {
  const [d, bg] = await Promise.all([
    fetch('../data/app_data.json').then((r) => r.json()),
    fetch('../data/bg_out.geojson').then((r) => r.json()),
  ]);
  D = d; BG = bg;
  bgIndex = new Map(bg.features.map((f) => [f.properties.GEOID, f]));
  for (const f of bg.features) f.properties._c = centroid(f.geometry);
}

function centroid(g) {
  let minx = 180, miny = 90, maxx = -180, maxy = -90;
  const walk = (c) => (typeof c[0] === 'number'
    ? (minx = Math.min(minx, c[0]), maxx = Math.max(maxx, c[0]), miny = Math.min(miny, c[1]), maxy = Math.max(maxy, c[1]))
    : c.forEach(walk));
  walk(g.coordinates);
  return [(minx + maxx) / 2, (miny + maxy) / 2, minx, miny, maxx, maxy];
}

// ---------- numbers ----------
function countTo(el, value) {
  if (value == null) { el.textContent = '—'; return; }
  if (reduced) { el.textContent = fmt(value); return; }
  const from = Number(el.dataset.v || 0), t0 = performance.now(), dur = 700;
  el.dataset.v = value;
  const step = (t) => {
    const k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3);
    el.textContent = fmt(Math.round(from + (value - from) * e));
    if (k < 1) requestAnimationFrame(step); else el.textContent = fmt(value); // final frame = exact value
  };
  requestAnimationFrame(step);
}

function renderHeadline() {
  const h = D.headline[state.rule];
  countTo($('[data-num="desert"]'), h.desert);
  countTo($('[data-num="near"]'), h.near);
  countTo($('[data-num="covered"]'), h.covered);
  $('[data-num="globe"]').textContent = fmt(D.validation.globe_pop);
  for (const [k, v] of [['desert', h.desert], ['near', h.near], ['covered', h.covered]])
    $(`#seg-${k}`).style.width = `${(v / h.total) * 100}%`;
  $('#fallback-banner').hidden = D.rule === 'state';
}

// ---------- provenance popover ----------
function showProv(btn) {
  const p = D.prov[btn.dataset.prov];
  const pop = $('#pop');
  const src = p.sources.map((k) => {
    const s = D.sources[k] || {};
    const pulled = (s.pulled || s.council?.pulled || '').slice(0, 10);
    return `<li>${esc(s.dataset || s.council?.dataset || k)}${pulled ? ` <small>· pulled ${esc(pulled)}</small>` : ''}</li>`;
  }).join('');
  pop.innerHTML = `<h4>How we got this</h4><div>Made by <code>${esc(p.function)}</code></div>${src ? `<ul>${src}</ul>` : ''}`;
  pop.showPopover();
  const r = btn.getBoundingClientRect();
  pop.style.left = `${Math.min(r.left, innerWidth - 340)}px`;
  pop.style.top = `${r.bottom + 6}px`;
}
document.addEventListener('click', (e) => {
  const b = e.target.closest('.info');
  if (b) { e.stopPropagation(); showProv(b); }
});

// ---------- ranking list ----------
function renderRanking() {
  const max = D.stores[0].people;
  $('#rank-list').innerHTML = D.stores.map((s) => `
    <li><button class="rank-row" data-rank="${s.rank}" aria-label="${esc(s.name)}, ${esc(s.address)}: ${fmt(s.people)} residents">
      <span class="rank-n">${s.rank}</span>
      <span><span class="rank-name">${esc(s.name)}</span><br><span class="rank-where">${esc(s.hoods.join(' · ') || s.address)}</span>
        <span class="bar"><i style="width:${(s.people / max) * 100}%"></i></span></span>
      <span class="rank-people">${fmt(s.people)}<small>residents</small></span>
    </button></li>`).join('');
  for (const btn of document.querySelectorAll('.rank-row')) {
    const s = D.stores[btn.dataset.rank - 1];
    btn.addEventListener('mouseenter', () => highlight(s, true));
    btn.addEventListener('mouseleave', () => highlight(s, false));
    btn.addEventListener('focus', () => highlight(s, true));
    btn.addEventListener('blur', () => highlight(s, false));
    btn.addEventListener('click', () => select(s));
  }
}

function rowFor(s) { return $(`.rank-row[data-rank="${s?.rank}"]`); }
function pharmacyFor(s) { return D.pharmacies.find((p) => p.lat === s.lat && p.lon === s.lon); }

function highlight(s, on) {
  if (!map?.loaded()) return;
  for (const g of s.block_groups) map.setFeatureState({ source: 'bg', id: g }, { hl: on });
  const p = pharmacyFor(s);
  if (p) map.setFeatureState({ source: 'stores', id: p.id }, { hl: on });
  rowFor(s)?.classList.toggle('is-hl', on);
}

// ---------- map ----------
async function pickStyle() {
  const style = await fetch('vendor/basemap-style.json').then((r) => r.json());
  const blank = { version: 8, sources: {}, layers: [{ id: 'blank', type: 'background', paint: { 'background-color': css('--map-blank') } }] };
  try {
    const src = Object.values(style.sources).find((s) => s.url);
    const ctl = new AbortController();
    setTimeout(() => ctl.abort(), 2500);
    await fetch(src.url, { signal: ctl.signal });
    return style;
  } catch { return blank; } // offline: data layers still draw on a plain background
}

function hatch() {
  const n = 8, c = document.createElement('canvas');
  c.width = c.height = n;
  const x = c.getContext('2d');
  x.fillStyle = css('--near'); x.fillRect(0, 0, n, n);
  x.strokeStyle = css('--near-hatch'); x.lineWidth = 1.2;
  x.beginPath(); x.moveTo(0, n); x.lineTo(n, 0); x.moveTo(-2, 2); x.lineTo(2, -2); x.moveTo(n - 2, n + 2); x.lineTo(n + 2, n - 2); x.stroke();
  return { width: n, height: n, data: x.getImageData(0, 0, n, n).data };
}

const statusProp = () => D.rules[state.rule];
const isSimDesert = ['==', ['feature-state', 'sim'], 'desert'];

function bgPaint() {
  const p = ['get', statusProp()];
  return {
    color: ['case', isSimDesert, css('--desert'),
      ['match', p, 'desert', css('--desert'), 'near-desert', css('--near'), css('--covered')]],
    opacity: ['case', isSimDesert, 0.78,
      ['match', p, 'desert', 0.66, 'near-desert', 0, 0.16]],
    hatchFilter: ['==', p, 'near-desert'],
  };
}

async function initMap() {
  const style = await pickStyle();
  const hasGlyphs = !!style.glyphs;
  map = new maplibregl.Map({
    container: 'map', style, center: [-71.075, 42.315], zoom: 11.3, minZoom: 9.5, maxZoom: 17,
    attributionControl: { compact: true },
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
  await new Promise((r) => map.on('load', r));
  map.addImage('hatch', hatch());

  const firstLabel = map.getStyle().layers.find((l) => l.type === 'symbol')?.id;
  const P = bgPaint();
  map.addSource('bg', { type: 'geojson', data: BG, promoteId: 'GEOID' });
  map.addLayer({ id: 'bg-fill', type: 'fill', source: 'bg', paint: {
    'fill-color': P.color, 'fill-opacity': P.opacity,
    'fill-color-transition': { duration: 600 }, 'fill-opacity-transition': { duration: 600 } } }, firstLabel);
  map.addLayer({ id: 'bg-hatch', type: 'fill', source: 'bg', filter: P.hatchFilter, paint: {
    'fill-pattern': 'hatch', 'fill-opacity': ['case', isSimDesert, 0, 0.62],
    'fill-opacity-transition': { duration: 600 } } }, firstLabel);
  map.addLayer({ id: 'bg-line', type: 'line', source: 'bg', paint: {
    'line-color': css('--block-line'), 'line-width': ['interpolate', ['linear'], ['zoom'], 10, 0.2, 14, 1], 'line-opacity': 0.8 } }, firstLabel);
  map.addLayer({ id: 'bg-hl', type: 'line', source: 'bg', paint: {
    'line-color': css('--ink'), 'line-width': ['case', ['boolean', ['feature-state', 'hl'], false], 2.2, 0],
    'line-width-transition': { duration: 150 } } }, firstLabel);

  const pts = (rows, props) => ({ type: 'FeatureCollection', features: rows.map((r) => ({
    type: 'Feature', id: r.id, geometry: { type: 'Point', coordinates: [r.lon, r.lat] }, properties: props(r) })) });
  map.addSource('closed', { type: 'geojson', data: pts(D.closed.map((c, i) => ({ ...c, id: i })), (c) => ({ name: c.name })) });
  map.addLayer({ id: 'closed', type: 'circle', source: 'closed', paint: {
    'circle-radius': 5, 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': css('--closed'), 'circle-stroke-width': 2 } });

  map.addSource('stores', { type: 'geojson', data: pts(D.pharmacies, (p) => (p.rank ? { name: p.name, rank: p.rank } : { name: p.name })) });
  const closedS = ['boolean', ['feature-state', 'closed'], false];
  const hlS = ['boolean', ['feature-state', 'hl'], false];
  map.addLayer({ id: 'stores', type: 'circle', source: 'stores', paint: {
    'circle-radius': ['case', closedS, 4,
      ['has', 'rank'], ['+', ['interpolate', ['linear'], ['get', 'rank'], 1, 10, 18, 7], ['case', hlS, 2, 0]],
      3.5],
    'circle-color': ['case', closedS, css('--closed'), ['has', 'rank'], css('--store'), css('--store-minor')],
    'circle-stroke-color': css('--surface'), 'circle-stroke-width': ['case', ['has', 'rank'], 2, 1],
    'circle-radius-transition': { duration: 400 }, 'circle-color-transition': { duration: 400 } } });
  if (hasGlyphs) map.addLayer({ id: 'store-n', type: 'symbol', source: 'stores', filter: ['has', 'rank'], layout: {
    'text-field': ['to-string', ['get', 'rank']], 'text-size': 10, 'text-allow-overlap': true,
    'text-font': [map.getStyle().layers.find((l) => l.layout?.['text-font'])?.layout['text-font'][0] || 'Noto Sans Regular'] },
    paint: { 'text-color': css('--brand-ink'), 'text-opacity': ['case', closedS, 0, 1] } });

  for (const id of ['stores', 'bg-fill']) {
    map.on('mouseenter', id, () => { map.getCanvas().style.cursor = 'pointer'; });
    map.on('mouseleave', id, () => { map.getCanvas().style.cursor = ''; });
  }
  map.on('click', (e) => {
    const st = map.queryRenderedFeatures(e.point, { layers: ['stores'] })[0];
    if (st) {
      const s = D.stores.find((x) => x.rank === st.properties.rank);
      return s ? select(s) : selectMinor(st.properties.name);
    }
    const b = map.queryRenderedFeatures(e.point, { layers: ['bg-fill'] })[0];
    if (b) openSheet(b.properties.GEOID);
  });
}

// ---------- selection + simulation ----------
function select(s) {
  if (state.closed && state.closed !== s) undo(true);
  document.querySelectorAll('.rank-row.is-selected').forEach((r) => r.classList.remove('is-selected'));
  rowFor(s)?.classList.add('is-selected');
  state.selected = s;
  map.easeTo({ center: [s.lon, s.lat], zoom: Math.max(map.getZoom(), 12.6), duration: reduced ? 0 : 800 });
  const card = $('#store-card');
  const done = state.closed === s;
  card.innerHTML = `
    <h3>${esc(s.name)}</h3>
    <p class="meta">#${s.rank} of ${D.stores.length} · ${esc(s.address)}</p>
    <p class="lead">If it closes, <b>${fmt(s.people)}</b> residents lose walkable access.</p>
    <div class="row">${done
      ? '<button class="btn btn-quiet" id="undo">Undo closure</button>'
      : '<button class="btn btn-danger" id="simulate">Simulate closure</button>'}</div>`;
  card.hidden = false;
  $('#simulate')?.addEventListener('click', () => simulate(s));
  $('#undo')?.addEventListener('click', () => undo());
}

function selectMinor(name) {
  const card = $('#store-card');
  card.innerHTML = `<h3>${esc(name || 'Pharmacy')}</h3>
    <p class="lead">No block group depends on this store alone. Closing it would not create a desert.</p>`;
  card.hidden = false;
}

function setRule(rule) {
  if (state.closed) undo(true);
  state.rule = rule;
  document.querySelectorAll('.rules button').forEach((b) => b.setAttribute('aria-checked', String(b.dataset.rule === rule)));
  const P = bgPaint();
  map.setPaintProperty('bg-fill', 'fill-color', P.color);
  map.setPaintProperty('bg-fill', 'fill-opacity', P.opacity);
  map.setFilter('bg-hatch', P.hatchFilter);
  renderHeadline();
}

function clearTimers() { state.timers.forEach(clearTimeout); state.timers = []; }

function wave(s, on) {
  const lost = s.block_groups.map((g) => bgIndex.get(g)).filter(Boolean);
  const d = (f) => Math.hypot((f.properties._c[0] - s.lon) * 0.74, f.properties._c[1] - s.lat); // 0.74 ≈ cos(42°)
  const far = Math.max(...lost.map(d), 1e-6);
  for (const f of lost) {
    const delay = reduced ? 0 : (on ? d(f) / far : 1 - d(f) / far) * 700;
    state.timers.push(setTimeout(() => map.setFeatureState({ source: 'bg', id: f.properties.GEOID }, { sim: on ? 'desert' : null }), delay));
  }
  return lost;
}

function simulate(s) {
  if (state.rule !== 'state') setRule('state');
  clearTimers();
  state.closed = s;
  highlight(s, false);
  const p = pharmacyFor(s);
  if (p) map.setFeatureState({ source: 'stores', id: p.id }, { closed: true });
  rowFor(s)?.classList.add('is-closed');
  const lost = wave(s, true);
  const [minx, miny, maxx, maxy] = lost.reduce((b, f) => {
    const c = f.properties._c;
    return [Math.min(b[0], c[2]), Math.min(b[1], c[3]), Math.max(b[2], c[4]), Math.max(b[3], c[5])];
  }, [s.lon, s.lat, s.lon, s.lat]);
  map.fitBounds([[minx, miny], [maxx, maxy]], { padding: { top: 60, bottom: 60, left: 360, right: 400 }, duration: reduced ? 0 : 1100, maxZoom: 13.6 });
  renderResult(s);
  $('#store-card').hidden = true; // the result card has its own Undo
  rowFor(s)?.classList.add('is-selected');
  state.selected = s;
}

function renderResult(s) {
  const card = $('#result-card');
  const offs = s.officials.map((o) => `<li><span>${esc(o.title)} ${esc(o.name)} <small>(${esc(o.district)})</small></span><span>${fmt(o.people)}</span></li>`).join('');
  card.innerHTML = `
    <div class="result-head">
      <p class="eyebrow">Simulated closure · ${esc(s.name)}</p>
      <div class="result-big"><span id="r-people">0</span><button class="info" data-prov="store" aria-label="How we got this number">i</button></div>
      <div>residents lose walkable access to a pharmacy</div>
    </div>
    <div class="result-body">
      <dl class="facts">
        <div><dt>Age 65+</dt><dd id="r-65">0</dd></div>
        <div><dt>Homes, no car</dt><dd id="r-car">0</dd></div>
        <div><dt>Limited English</dt><dd id="r-eng">0</dd></div>
      </dl>
      <p class="walk-note" style="margin-top:-8px">Counts are homes, except age 65+. <button class="info" data-prov="lim_eng_hh" aria-label="How we got the limited English count">i</button></p>
      <p class="walk-note">Next open pharmacy: up to <b>${fmt(s.next_walk_max)} min</b> on foot <button class="info" data-prov="walk" aria-label="How we got this number">i</button> · ${esc(s.hoods.join(', '))}</p>
      <h4>Officials for these residents <button class="info" data-prov="officials" aria-label="How we got this">i</button></h4>
      <ul class="offs">${offs}</ul>
    </div>
    <div class="row actions">
      <button class="btn" disabled title="Coming in the next phase">Open brief</button>
      <button class="btn btn-quiet" disabled title="Coming in the next phase">Best replacement site</button>
      <button class="btn btn-quiet" id="undo2">Undo</button>
    </div>`;
  card.hidden = false;
  $('#undo2').addEventListener('click', () => undo());
  countTo($('#r-people'), s.people);
  countTo($('#r-65'), s.age65);
  countTo($('#r-car'), s.nocar_hh);
  countTo($('#r-eng'), s.lim_eng_hh);
}

function undo(silent = false) {
  const s = state.closed;
  if (!s) return;
  clearTimers();
  wave(s, false);
  const p = pharmacyFor(s);
  if (p) map.setFeatureState({ source: 'stores', id: p.id }, { closed: false });
  rowFor(s)?.classList.remove('is-closed');
  state.closed = null;
  $('#result-card').hidden = true;
  if (!silent) select(s);
}

// ---------- block sheet ----------
function openSheet(geoid) {
  const f = bgIndex.get(geoid);
  if (!f) return;
  const p = f.properties;
  const simLost = state.closed?.lost.find((b) => b.GEOID === geoid);
  const status = simLost ? 'desert' : p[statusProp()];
  const offName = (kind, id) => D.stores.flatMap((s) => s.officials).find((o) => o.kind === kind && o.district === (kind === 'council' ? `District ${id}` : id))?.name;
  const near = simLost?.nearest.map((n) => `<li>${esc(n.name)} — ${fmt(n.walk_min)} min walk <small>${esc(n.address || '')}</small></li>`).join('');
  const sheet = $('#sheet');
  sheet.innerHTML = `
    <button class="close" aria-label="Close">×</button>
    <span class="pill pill-${status}">${STATUS_LABEL[status]}${simLost ? ' after closure' : ''}</span>
    <h3 id="sheet-title" style="margin:6px 0 0">${esc(p.hood || 'Boston')} <small style="color:var(--muted);font-weight:400">block group ${esc(geoid)}</small></h3>
    <dl class="grid">
      <div><dt>Residents</dt><dd>${fmt(p.pop)}</dd></div>
      <div><dt>Age 65+</dt><dd>${fmt(p.age65)}</dd></div>
      <div><dt>Homes, no car</dt><dd>${p.nocar_pct == null ? '—' : `${p.nocar_pct}%`}</dd></div>
      <div><dt>Limited English</dt><dd>${p.lim_eng}%</dd></div>
    </dl>
    <p style="margin:0 0 8px;font-size:var(--fs-sm);color:var(--ink-2)">Council District ${esc(p.council)}${offName('council', p.council) ? ` (${esc(offName('council', p.council))})` : ''} · ${esc(p.house)} · ${esc(p.senate)}
      <button class="info" data-prov="block" aria-label="How we got these numbers">i</button></p>
    ${near ? `<h4 style="margin:8px 0 4px;font-size:var(--fs-sm)">Nearest open pharmacies <button class="info" data-prov="walk" aria-label="How we got this">i</button></h4><ol class="near-list">${near}</ol>` : ''}`;
  sheet.hidden = false;
  $('.close', sheet).addEventListener('click', () => { sheet.hidden = true; });
}

// ---------- method dialog ----------
async function renderMethod() {
  const tpl = await fetch('../data/templates/validation.en.md').then((r) => r.text());
  const v = D.validation;
  const filled = tpl.replace(/\{(\w+)\}/g, (_, k) => esc(typeof v[k] === 'number' ? fmt(v[k]) : v[k]));
  const html = filled.split(/\n\n+/).map((block) => {
    const md = (t) => t.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
    if (block.trim().startsWith('- ')) return `<ul>${block.split(/\n(?=- )/).map((li) => `<li>${md(li.replace(/^- /, ''))}</li>`).join('')}</ul>`;
    return `<p>${md(block)}</p>`;
  }).join('');
  $('#validation').innerHTML = html;
  $('#sources').innerHTML = Object.entries(D.sources).flatMap(([k, s]) => (s.dataset || s.pulled
    ? [[s.dataset || k, s.pulled]]
    : Object.values(s).filter((x) => x && x.dataset).map((x) => [x.dataset, x.pulled])))
    .map(([d, p]) => `<tr><td>${esc(d)}</td><td>${esc((p || '').slice(0, 10))}</td></tr>`).join('');
}

// ---------- boot ----------
async function boot() {
  await load();
  renderHeadline();
  renderRanking();
  await initMap();
  renderMethod();
  document.querySelectorAll('.rules button').forEach((b) => b.addEventListener('click', () => setRule(b.dataset.rule)));
  for (const id of ['open-method', 'why-differ']) $(`#${id}`).addEventListener('click', () => $('#method').showModal());
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (!$('#sheet').hidden) $('#sheet').hidden = true;
    else if (!$('#store-card').hidden && !state.closed) $('#store-card').hidden = true;
  });
  window.rxgap = { state, simulate: (rank) => simulate(D.stores[rank - 1]), undo }; // for the smoke test
}
boot();
