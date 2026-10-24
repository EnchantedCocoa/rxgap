// RxGap 지도 앱 로직: 데이터 로드, 지도 레이어, 순위 목록, 폐점 시뮬레이션.
const $ = (s, el = document) => el.querySelector(s);
const fmt = (n) => (n == null ? '—' : Number(n).toLocaleString('en-US'));
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
import { openEssay } from './essay.js';
const STATUS_LABEL = { desert: 'Desert', 'near-desert': 'One closure away', covered: 'Covered' };

const state = { rule: 'state', selected: null, closed: null, timers: [], town: 'boston' };
let D, BG, map, bgIndex, bostonLayer, pinLayer;

// ---------- data ----------
const placeBase = (slug) => (slug === 'boston' ? '../data/' : `../data/places/${slug}/`);
async function load(slug = 'boston') {
  const [d, bg] = await Promise.all([
    fetch(placeBase(slug) + 'app_data.json').then((r) => r.json()),
    fetch(placeBase(slug) + 'bg_out.geojson').then((r) => r.json()),
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
  countTo($('[data-num="atrisk"]'), h.desert + h.near);
  for (const [k, v] of [['desert', h.desert], ['near', h.near], ['covered', h.covered]])
    $(`#seg-${k}`).style.width = `${(v / h.total) * 100}%`; // gray remainder = everyone else
  const v = D.validation, P = D.place;
  $('#hl-title').textContent = `${P.name} residents in a pharmacy desert or one closure away`;
  const types = Object.entries(P.area_types).filter(([, n]) => n > 0).sort((x, y) => y[1] - x[1]);
  $('#town-note').hidden = P.slug === 'boston';
  $('#rk-title').textContent = `Stores ${P.name} can’t afford to lose`;
  $('#town-note').innerHTML = P.why ? `${esc(P.why)}. Walk limit by area: ${types.map(([t, n]) => `${t} ${fmt(n)} people`).join(', ')}. <button class="info" data-prov="headline" aria-label="How we got this">i</button>` : '';
  $('#at-risk').innerHTML = state.rule === 'state'
    ? `<b>1 in ${fmt(v.one_in)}</b> ${esc(P.name)} residents. Among them, <b>${fmt(v.at_risk_age65)}</b> are 65 or older and <b>${fmt(v.at_risk_nocar_hh)}</b> homes have no car.`
    : `<b>1 in ${fmt(Math.round(h.total / (h.desert + h.near)))}</b> ${esc(P.name)} residents at this walk limit.`;
  $('#fallback-banner').hidden = D.rule === 'state';
  const manual = D.pharmacies.filter((p) => p.source && p.source !== 'OpenStreetMap').length;
  if (manual) $('#source-note').textContent = `Stores: OpenStreetMap (a floor, not the full list), plus ${fmt(manual)} added by hand with a source.`;
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
  if (!map) return;
  for (const g of s.block_groups) layers.get(g)?.getElement()?.classList.toggle('is-hl', on);
  if (on) for (const g of s.block_groups) layers.get(g)?.bringToFront();
  const p = pharmacyFor(s);
  if (p) markers.get(p.id)?.getElement()?.classList.toggle('is-hl', on);
  rowFor(s)?.classList.toggle('is-hl', on);
}

// ---------- map (Leaflet + SVG: no WebGL needed) ----------
const statusProp = () => D.rules[state.rule];
const layers = new Map();   // GEOID -> Leaflet path
const markers = new Map();  // pharmacy id -> Leaflet marker
const STATUS_CLASSES = ['st-desert', 'st-near-desert', 'st-covered'];
const EMPTY_POP = 50;

function restyle() {
  const prop = statusProp();
  for (const [g, l] of layers) {
    const el = l.getElement();
    el.classList.remove(...STATUS_CLASSES);
    const p = bgIndex.get(g).properties;
    el.classList.add(`st-${p[prop]}`);
    el.classList.toggle('is-empty', p.pop < EMPTY_POP); // parks, harbor islands: few or no residents
  }
}

function initMap() {
  map = L.map('map', { zoomSnap: 1, zoomControl: false, attributionControl: false })
    .setView([42.295, -71.085], 13); // open on Dorchester, Mattapan, Roxbury, where access is thinnest
  L.control.zoom({ position: 'topright' }).addTo(map);
  L.control.attribution({ prefix: false }).addTo(map);
  map.createPane('labels').style.zIndex = 450;
  map.getPane('labels').style.pointerEvents = 'none';
  const esri = 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_';
  const tiles = (kind, pane) => L.tileLayer(`${esri}${kind}/MapServer/tile/{z}/{y}/{x}`, {
    maxZoom: 16, pane, attribution: 'Base map © Esri, HERE, Garmin, © OpenStreetMap contributors',
  });
  tiles('Base', 'tilePane').addTo(map);
  tiles('Reference', 'labels').addTo(map); // labels stay readable above the colored blocks

  drawPlace();
}

function drawPlace() {
  clearTimers(); // pending wave steps point at the old layers
  bostonLayer?.remove(); pinLayer?.remove(); clearRoute(); clearSiting();
  layers.clear(); markers.clear();
  pinLayer = L.layerGroup().addTo(map);
  bostonLayer = L.geoJSON(BG, {
    style: () => ({ className: 'bg', weight: 0.6 }),
    onEachFeature: (f, l) => {
      layers.set(f.properties.GEOID, l);
      l.on('click', () => openSheet(f.properties.GEOID));
    },
  }).addTo(map);
  restyle();

  for (const c of D.closed) {
    pinLayer.addLayer(L.marker([c.lat, c.lon], { keyboard: false, title: `${c.name} — closed ${c.date}`,
      icon: L.divIcon({ className: 'pin pin-closed', iconSize: [12, 12] }) }));
  }
  for (const p of D.pharmacies) {
    const s = p.rank && D.stores[p.rank - 1];
    const size = s ? Math.round(26 - p.rank * 0.4) : 8;
    const m = L.marker([p.lat, p.lon], {
      keyboard: false, title: p.name, zIndexOffset: s ? 1000 - p.rank : 0,
      icon: L.divIcon({ className: s ? 'pin pin-rank' : 'pin pin-minor', iconSize: [size, size], html: s ? `<span>${p.rank}</span>` : '' }),
    }).addTo(pinLayer);
    m.on('click', () => (s ? select(s) : selectMinor(p.name)));
    markers.set(p.id, m);
  }
}

// ---------- other places (state's published results) ----------
async function setTown(slug) {
  if (slug === state.town) return;
  if (state.closed) undo(true);
  ['#store-card', '#result-card', '#sheet'].forEach((x) => { $(x).hidden = true; });
  state.town = slug;
  await load(slug);
  drawPlace();
  renderHeadline();
  renderRanking();
  renderMethod();
  map.flyTo(D.place.view.slice(0, 2), D.place.view[2], { animate: !reduced, duration: 1.2 });
}

// ---------- selection + simulation ----------
function select(s) {
  if (state.closed && state.closed !== s) undo(true);
  document.querySelectorAll('.rank-row.is-selected').forEach((r) => r.classList.remove('is-selected'));
  rowFor(s)?.classList.add('is-selected');
  state.selected = s;
  map.flyTo([s.lat, s.lon], Math.max(map.getZoom(), 13.5), { animate: !reduced, duration: 0.8 });
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
  restyle();
  renderHeadline();
}

function clearTimers() { state.timers.forEach(clearTimeout); state.timers = []; }

function wave(s, on) {
  const lost = s.block_groups.map((g) => bgIndex.get(g)).filter(Boolean);
  const d = (f) => Math.hypot((f.properties._c[0] - s.lon) * 0.74, f.properties._c[1] - s.lat); // 0.74 ≈ cos(42°)
  const far = Math.max(...lost.map(d), 1e-6);
  for (const f of lost) {
    const delay = reduced ? 0 : (on ? d(f) / far : 1 - d(f) / far) * 700;
    state.timers.push(setTimeout(() => layers.get(f.properties.GEOID).getElement().classList.toggle('is-sim', on), delay));
  }
  return lost;
}

function simulate(s) {
  tourEnd();
  if (state.rule !== 'state') setRule('state');
  clearTimers();
  state.closed = s;
  highlight(s, false);
  const p = pharmacyFor(s);
  if (p) markers.get(p.id).getElement().classList.add('is-closed');
  rowFor(s)?.classList.add('is-closed');
  const lost = wave(s, true);
  const box = L.latLngBounds([[s.lat, s.lon]]);
  for (const f of lost) box.extend(layers.get(f.properties.GEOID).getBounds());
  map.flyToBounds(box, { paddingTopLeft: [40, 60], paddingBottomRight: [400, 60], maxZoom: 14, animate: !reduced, duration: 1.1 });
  renderResult(s);
  state.timers.push(setTimeout(() => drawRoute(s), reduced ? 0 : 1300)); // after the red wave and camera move
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
      <p class="walk-note">Next open pharmacy: up to <b>${fmt(s.next_walk_max)} min</b> on foot${D.place.walk_estimate ? ' (estimate: straight line × 1.3)' : ''} <button class="info" data-prov="walk" aria-label="How we got this number">i</button> · ${esc(s.hoods.join(', '))}</p>
      <h4>Officials for these residents <button class="info" data-prov="officials" aria-label="How we got this">i</button></h4>
      <ul class="offs">${offs}</ul>
    </div>
    <div class="row actions">
        <button class="btn" disabled title="Coming in the next phase">Open brief</button>
        <button class="btn btn-quiet" id="sites-btn">Best replacement site</button>
        <button class="btn btn-quiet" id="undo2">Undo</button>
    </div>`;
  card.hidden = false;
  $('#undo2').addEventListener('click', () => undo());
  $('#sites-btn').addEventListener('click', () => renderSites(s));
  countTo($('#r-people'), s.people);
  countTo($('#r-65'), s.age65);
  countTo($('#r-car'), s.nocar_hh);
  countTo($('#r-eng'), s.lim_eng_hh);
}

function undo(silent = false) {
  const s = state.closed;
  if (!s) return;
  clearTimers();
  clearSiting();
  clearRoute();
  wave(s, false);
  const p = pharmacyFor(s);
  if (p) markers.get(p.id).getElement().classList.remove('is-closed');
  rowFor(s)?.classList.remove('is-closed');
  state.closed = null;
  $('#result-card').hidden = true;
  if (!silent) select(s);
}

// ---------- walking route to the next open pharmacy ----------
const routeLayers = [];
function clearRoute() { routeLayers.splice(0).forEach((l) => l.remove()); }

function drawRoute(s) {
  clearRoute();
  const r = s.route;
  if (!r || state.closed !== s) return;
  const opts = { interactive: false };
  const halo = L.polyline(r.coords, { ...opts, className: 'route-halo' }).addTo(map);
  const line = L.polyline(r.coords, { ...opts, className: 'route' }).addTo(map);
  const start = L.marker(r.coords[0], { ...opts, icon: L.divIcon({ className: 'route-start', iconSize: [14, 14] }) }).addTo(map);
  routeLayers.push(halo, line, start);
  for (const el of [halo.getElement(), line.getElement()]) {  // draw the line from home to the store
    const len = el.getTotalLength();
    el.style.strokeDasharray = `${len}`;
    el.style.strokeDashoffset = `${len}`;
    el.getBoundingClientRect();
    el.style.transition = reduced ? 'none' : 'stroke-dashoffset 1.8s cubic-bezier(0.4, 0, 0.2, 1)';
    el.style.strokeDashoffset = '0';
  }
  const tag = () => {
    if (state.closed !== s) return;
    const m = L.marker(r.coords[r.coords.length - 1], { ...opts, zIndexOffset: 3000, icon: L.divIcon({
      className: 'route-tag', iconAnchor: [-8, 14],
      html: `${r.estimate ? 'about ' : ''}${fmt(r.minutes)} min walk <small>to ${esc(r.store)}</small>` }) }).addTo(map);
    routeLayers.push(m);
  };
  reduced ? tag() : state.timers.push(setTimeout(tag, 1800));
  map.flyToBounds(L.latLngBounds(r.coords).extend(layers.get(r.GEOID).getBounds()).pad(0.25),
    { paddingTopLeft: [40, 60], paddingBottomRight: [400, 60], maxZoom: 15, animate: !reduced, duration: 0.9 });
}

// ---------- opening tour (numbers come from app_data.json) ----------
const tour = { i: -1, timer: null, on: false };
function tourStops() {
  const top = D.stores.slice(0, 3);
  const v = D.validation;
  return [
    { text: `<b>1 in ${fmt(v.one_in)}</b> ${esc(D.place.name)} residents lives in a pharmacy desert or one closure away from one.`,
      view: () => map.flyTo(D.place.view.slice(0, 2), D.place.view[2], { duration: 1.6 }) },
    ...top.map((s) => ({
      text: `${esc(s.hoods.join(' & '))}: if the ${esc(s.name)} at ${esc(String(s.address).split(',')[0])} closes, <b>${fmt(s.people)}</b> residents lose walkable access.`
        + (s.route ? ` For some, the next pharmacy is a <b>${fmt(s.route.minutes)}-minute</b> walk.` : ''),
      view: () => { map.flyTo([s.lat, s.lon], 14, { duration: 1.6 }); highlight(s, true); },
      leave: () => highlight(s, false) })),
    { text: 'Pick any store on the list to see who would lose access, and the best place for a replacement.',
      view: () => map.flyTo(D.place.view.slice(0, 2), D.place.view[2], { duration: 1.4 }) },
  ];
}

function tourGo(i) {
  const stops = tourStops();
  stops[tour.i]?.leave?.();
  clearTimeout(tour.timer);
  if (i >= stops.length) return tourEnd();
  tour.i = i;
  $('#tour-step').textContent = `${i + 1} of ${stops.length}`;
  $('#tour-text').innerHTML = stops[i].text;
  $('#tour-next').textContent = i === stops.length - 1 ? 'Explore' : 'Next';
  const bar = $('#tour-progress');
  bar.style.transition = 'none'; bar.style.width = '0';
  bar.getBoundingClientRect();
  bar.style.transition = 'width 5.5s linear'; bar.style.width = '100%';
  stops[i].view();
  tour.timer = setTimeout(() => tourGo(i + 1), 5500);
}

function tourStart() {
  if (state.closed) return;
  tour.on = true; $('#tour').hidden = false; tourGo(0);
}
function tourEnd() {
  if (!tour.on) return;
  tourStops()[tour.i]?.leave?.();
  clearTimeout(tour.timer); tour.on = false; tour.i = -1; $('#tour').hidden = true;
}

// ---------- replacement siting ----------
const MILE_M = 1609.344;
const siting = { pins: [], ring: null, restored: [] };

function clearSiting() {
  siting.pins.forEach((m) => m.remove());
  siting.ring?.remove();
  for (const g of siting.restored) layers.get(g)?.getElement()?.classList.remove('is-restored');
  Object.assign(siting, { pins: [], ring: null, restored: [] });
}

function showRestored(geoids) {
  for (const g of siting.restored) layers.get(g)?.getElement()?.classList.remove('is-restored');
  siting.restored = geoids;
  geoids.forEach((g, i) => state.timers.push(setTimeout(
    () => layers.get(g)?.getElement()?.classList.add('is-restored'), reduced ? 0 : i * 40)));
}

function renderSites(s) {
  const S = s.sites, card = $('#result-card');
  clearSiting();
  clearRoute();
  const best = S.best_set;
  const rows = S.top.map((c, i) => `
    <li><button class="site-row" data-i="${i}">
      <span class="site-n">${i + 1}</span>
      <span><b>${esc(c.name)}</b><br><small>${esc(c.kind === 'health_center' ? 'Health center' : c.kind === 'mbta_station' ? 'T station' : 'Storefront')}${c.at_closed_store ? ' · next to the closed store' : ''}${best.sites.includes(c.name) ? ' · in best set' : ''}</small></span>
      <span class="site-gain">+${fmt(c.gain)}</span>
    </button></li>`).join('');
  card.innerHTML = `
    <div class="result-head good">
      <p class="eyebrow">Replacement sites · ${esc(s.name)} closed</p>
      <div class="result-big"><span id="r-best">0</span><button class="info" data-prov="siting" aria-label="How we got this number">i</button></div>
      <div>of ${fmt(S.lost_pop)} residents regain access if pharmacies open at the best ${fmt(best.sites.length)} site${best.sites.length === 1 ? '' : 's'}</div>
    </div>
    <div class="result-body">
      ${S.top.length ? `
      <h4>Best single sites <small>(residents brought back)</small></h4>
      <ol class="sites">${rows}</ol>
      <div id="site-math"></div>` : `
      <p class="walk-note">No health center, T station or listed storefront within reach brings these blocks back.
        Add a storefront to <code>data/manual/candidate_sites.csv</code> to test it.</p>`}
    </div>
    <div class="row actions">
      <button class="btn btn-quiet" id="back">← Who lost access</button>
      ${best.sites.length > 1 ? '<button class="btn btn-quiet" id="show-best">Show best set together</button>' : ''}
      <button class="btn btn-quiet" id="undo3">Undo</button>
    </div>`;
  countTo($('#r-best'), best.gain);
  $('#back').addEventListener('click', () => { clearSiting(); renderResult(s); drawRoute(s); });
  $('#undo3').addEventListener('click', () => undo());
  $('#show-best')?.addEventListener('click', () => {
    siting.ring?.remove(); siting.ring = null;
    const picked = S.top.filter((c) => best.sites.includes(c.name));
    showRestored([...new Set(picked.flatMap((c) => c.restored.map((r) => r.GEOID)))]);
    $('#site-math').innerHTML = `<p class="walk-note">Together, the best set brings back <b>${fmt(best.gain)}</b> residents (${esc(best.solver || 'PuLP')}).</p>`;
    document.querySelectorAll('.site-row').forEach((r) => r.classList.toggle('is-selected', best.sites.includes(S.top[r.dataset.i].name)));
  });
  S.top.forEach((c, i) => {
    const m = L.marker([c.lat, c.lon], { keyboard: false, title: c.name, zIndexOffset: 2000,
      icon: L.divIcon({ className: 'pin pin-site', iconSize: [24, 24], html: `<span>${i + 1}</span>` }) }).addTo(map);
    m.on('click', () => pickSite(s, i));
    siting.pins.push(m);
  });
  document.querySelectorAll('.site-row').forEach((r) => r.addEventListener('click', () => pickSite(s, Number(r.dataset.i))));
  if (S.top.length) pickSite(s, 0);
}

function pickSite(s, i) {
  const S = s.sites, c = S.top[i];
  document.querySelectorAll('.site-row').forEach((r) => r.classList.toggle('is-selected', Number(r.dataset.i) === i));
  siting.ring?.remove();
  siting.ring = L.circle([c.lat, c.lon], { radius: S.ring_mi * MILE_M, className: 'ring', interactive: false }).addTo(map);
  showRestored(c.restored.map((r) => r.GEOID));
  map.flyToBounds(siting.ring.getBounds(), { paddingTopLeft: [40, 60], paddingBottomRight: [400, 60], maxZoom: 14, animate: !reduced, duration: 0.8 });
  const hood = (g) => esc(bgIndex.get(g)?.properties.hood || '');
  $('#site-math').innerHTML = `
    <h4>Why #${i + 1} ranks here</h4>
    ${c.at_closed_store ? `<p class="walk-note"><b>Same spot as the closed store.</b> Reopening a pharmacy here, for example inside ${esc(c.name)}, restores everyone who lost access.</p>` : ''}
    <p class="walk-note">A pharmacy at ${esc(c.address || c.name)} would put these blocks back above the ${esc(D.validation.area_pct)} line.
      The ring shows the ${fmt(S.ring_mi)}-mile walk limit.</p>
    <table class="math"><thead><tr><th>Block</th><th>Residents</th><th>Area in reach</th></tr></thead><tbody>
      ${c.restored.map((r) => `<tr><td>${hood(r.GEOID)} <small>${esc(r.GEOID.slice(-7))}</small></td><td>${fmt(r.pop)}</td>
        <td>${r.share_before}% → <b>${r.share_after}%</b></td></tr>`).join('')}
      <tr class="sum"><td>Total</td><td>${fmt(c.gain)}</td><td></td></tr>
    </tbody></table>`;
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
    <p style="margin:0 0 8px;font-size:var(--fs-sm);color:var(--ink-2)">${p.council ? `Council District ${esc(p.council)}${offName('council', p.council) ? ` (${esc(offName('council', p.council))})` : ''} · ` : ''}${esc(p.house)} · ${esc(p.senate)} · ${esc(p.area_type || '')} area, ${fmt(p.limit_mi)}-mile limit
      <button class="info" data-prov="block" aria-label="How we got these numbers">i</button></p>
    ${near ? `<h4 style="margin:8px 0 4px;font-size:var(--fs-sm)">Nearest open pharmacies <button class="info" data-prov="walk" aria-label="How we got this">i</button></h4><ol class="near-list">${near}</ol>` : ''}`;
  sheet.hidden = false;
  $('.close', sheet).addEventListener('click', () => { sheet.hidden = true; });
}

// ---------- method dialog ----------
async function renderMethod() {
  const tpl = await fetch(`../data/templates/validation.${D.place.slug === 'boston' ? 'en' : 'place'}.md`).then((r) => r.text());
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
  initMap();
  renderMethod();
  $('#town').addEventListener('change', (e) => { tourEnd(); setTown(e.target.value); });
  $('#tour-skip').addEventListener('click', tourEnd);
  $('#tour-next').addEventListener('click', () => tourGo(tour.i + 1));
  $('#play-tour').addEventListener('click', () => { if (state.closed) undo(true); tourStart(); });
  for (const el of [$('#rank-list'), $('#map')]) el.addEventListener('pointerdown', tourEnd); // any real interaction ends it
  document.querySelectorAll('.rules button').forEach((b) => b.addEventListener('click', () => setRule(b.dataset.rule)));
  for (const id of ['open-method', 'why-differ']) $(`#${id}`).addEventListener('click', () => $('#method').showModal());
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (!$('#sheet').hidden) $('#sheet').hidden = true;
    else if (!$('#store-card').hidden && !state.closed) $('#store-card').hidden = true;
  });
  const q = new URLSearchParams(location.search);
  const story = () => { tourEnd(); return openEssay(D, { reduced }); };
  $('#open-story').addEventListener('click', story);
  if (q.get('splash') !== '0') await story(); // photo essay first, then the map
  if (!reduced && q.get('tour') !== '0') setTimeout(tourStart, 900);
  window.rxgap = { state, simulate: (rank) => simulate(D.stores[rank - 1]), undo }; // for the smoke test
}
boot();
