// 공직자 브리프·약 배달 도우미·편지 쓰기 화면: 글은 숫자 없는 템플릿, 숫자는 facts.json에서 코드가 넣는다.
import { render, fmt } from './text.js';

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const LANGS = { en: 'English', es: 'Español', ht: 'Kreyòl ayisyen' };
const cache = new Map();
const get = (url, kind = 'text') => {
  if (!cache.has(url)) cache.set(url, fetch(url).then((r) => { if (!r.ok) throw new Error(url); return r[kind](); }));
  return cache.get(url);
};
const tpl = (name) => get(`../data/templates/${name}`);
const policy = () => get('../data/manual/policy.json', 'json');
const counted = new Set();
// Sample sentences for "in your own words", one set per topic and language. The resident takes one and changes it.
const SAMPLES = {
  officials: {
    en: ['My father takes heart medicine every day, and this is the only pharmacy he can walk to.',
      'I am a senior without a car. If this pharmacy closes, I will not be able to get my medicine.',
      'Our neighborhood needs a pharmacy close by, with pharmacists who know us and speak our language.'],
    es: ['Mi padre toma medicina para el corazón todos los días, y esta es la única farmacia a la que puede ir a pie.',
      'Soy una persona mayor y no tengo carro. Si esta farmacia cierra, no podré conseguir mis medicinas.',
      'Nuestro barrio necesita una farmacia cerca, con farmacéuticos que nos conozcan y hablen nuestro idioma.'],
    ht: ['Papa m pran medikaman pou kè chak jou, e se sèl famasi sa a li ka mache ale.',
      'Mwen se yon granmoun ki pa gen machin. Si famasi sa a fèmen, m p ap ka jwenn medikaman m.',
      'Katye nou an bezwen yon famasi toupre, ak famasyen ki konnen nou e ki pale lang nou.'],
  },
  masshealth: {
    en: ['I use a wheelchair, and I have no way to get to the pharmacy to pick up my medicine.',
      'My mother has MassHealth and has missed doses because the pharmacy is too far to walk to.',
      'Home delivery would let my neighbors get their medicine on time, without paying for a taxi.'],
    es: ['Uso silla de ruedas y no tengo cómo llegar a la farmacia para recoger mis medicinas.',
      'Mi madre tiene MassHealth y ha dejado de tomar sus medicinas porque la farmacia queda demasiado lejos para ir a pie.',
      'La entrega a domicilio permitiría que mis vecinos reciban sus medicinas a tiempo, sin tener que pagar un taxi.'],
    ht: ['Mwen nan chèz woulant, e m pa gen okenn fason pou m ale nan famasi pou m pran medikaman m.',
      'Manman m gen MassHealth, e li te manke pran medikaman l plizyè fwa paske famasi a twò lwen pou l mache ale.',
      'Livrezon lakay ta pèmèt vwazen m yo jwenn medikaman yo alè, san yo pa peye taksi.'],
  },
};
// Every word of the letter steps, in the language the resident picks. Facts still come from facts.json.
const UI = {
  en: {
    title: 'Write a letter', steps: ['Your officials', 'Your letter', 'Send it yourself'],
    note: (gov) => `RxGap is an AI tool built at Hackachusetts, not ${gov}. It never sends anything for you.`,
    addr: (place) => `Your home address in ${place}`, addrHint: 'Street, city and ZIP', find: 'Find my officials',
    privacy: 'Your address goes to the US Census Bureau only to find your block. RxGap does not keep it.',
    sampleTip: (what) => `The gray text is a sample address: ${what}, a public building in a pharmacy desert. Click the box or press ↓ to use it.`,
    looking: 'Looking up your block…',
    noMatch: 'We could not match that address. Check the street and ZIP, or pick your block on the map.',
    down: 'The Census lookup is not available right now. Pick your block on the map instead.',
    outside: (place) => `That address is outside ${place}. Choose its place at the top of the page first.`,
    noAddr: 'No address? Close this, click your block on the map, then choose “Write a letter”.',
    found: 'Address found:', block: 'Your block in',
    desert: 'is a pharmacy desert today', near: (s) => `would become a pharmacy desert if the ${s} closed`,
    covered: 'has a pharmacy within walking distance',
    officials: 'Your officials', contact: 'Contact', ok: 'These are my officials', redo: 'Use another address',
    ask: 'What do you want to ask for?',
    keep: 'Keep a pharmacy near us', keepTo: 'To your officials',
    keepOff: 'Your block still has a pharmacy within walking distance',
    rides: 'Pay for pharmacy rides or delivery', ridesTo: 'To MassHealth, with a copy to your officials',
    label: 'In your own words: why does this matter to you?', req: '(required)', eg: 'For example',
    tip: 'Click the empty box, or press ↓ and ↑, to fill in a sample sentence. Then make it your own.',
    make: 'Make my letter', back: 'Back',
    enCopy: 'English copy',
    aiNote: 'Translated with AI help. Please read it, or ask someone you trust to check it, before you send it.',
    copy: 'Copy letter', email: 'Open in my email', print: 'Print', change: 'Change it',
    copied: 'Copied. Paste it into your email or a letter.', copyFail: 'Select the letter text and copy it.',
    youSend: 'RxGap does not send this. You do.', offEmail: 'Find each official’s email on their page:',
    mhMail: (office) => `Mail it to ${office}, and send the copy to your officials:`,
    subject: { officials: 'Please keep a pharmacy within walking distance', masshealth: 'Please pay for pharmacy rides or home delivery' },
  },
  es: {
    title: 'Escribir una carta', steps: ['Sus funcionarios', 'Su carta', 'Usted la envía'],
    note: (gov) => `RxGap es una herramienta de IA creada en Hackachusetts; no es ${gov}. Nunca envía nada por usted.`,
    addr: (place) => `Su dirección en ${place}`, addrHint: 'Calle, ciudad y código postal', find: 'Buscar mis funcionarios',
    privacy: 'Su dirección se envía a la Oficina del Censo de EE. UU. solo para encontrar su cuadra. RxGap no la guarda.',
    sampleTip: (what) => `El texto gris es una dirección de ejemplo: ${what}, un edificio público en un desierto de farmacias. Haga clic en el cuadro o presione ↓ para usarla.`,
    looking: 'Buscando su cuadra…',
    noMatch: 'No encontramos esa dirección. Revise la calle y el código postal, o elija su cuadra en el mapa.',
    down: 'La búsqueda del Censo no está disponible en este momento. Elija su cuadra en el mapa.',
    outside: (place) => `Esa dirección no está en ${place}. Primero elija ese lugar en la parte de arriba de la página.`,
    noAddr: '¿Prefiere no dar su dirección? Cierre esta ventana, haga clic en su cuadra en el mapa y elija “Write a letter”.',
    found: 'Dirección encontrada:', block: 'Su cuadra en',
    desert: 'ya es un desierto de farmacias', near: (s) => `se convertiría en un desierto de farmacias si cerrara ${s}`,
    covered: 'tiene una farmacia a la que se puede ir a pie',
    officials: 'Sus funcionarios', contact: 'Contacto', ok: 'Sí, son mis funcionarios', redo: 'Usar otra dirección',
    ask: '¿Qué quiere pedir?',
    keep: 'Que haya una farmacia cerca', keepTo: 'A sus funcionarios',
    keepOff: 'Su cuadra todavía tiene una farmacia a la que se puede ir a pie',
    rides: 'Que paguen el transporte a la farmacia o la entrega a domicilio', ridesTo: 'A MassHealth, con copia a sus funcionarios',
    label: 'En sus propias palabras: ¿por qué es importante para usted?', req: '(obligatorio)', eg: 'Por ejemplo',
    tip: 'Haga clic en el cuadro vacío, o use las flechas ↓ y ↑, para ver una frase de ejemplo. Después, cámbiela con sus propias palabras.',
    make: 'Crear mi carta', back: 'Atrás',
    enCopy: 'Copia en inglés',
    aiNote: 'Traducción hecha con ayuda de IA. Léala, o pídale a alguien de confianza que la revise, antes de enviarla.',
    copy: 'Copiar la carta', email: 'Abrir en mi correo', print: 'Imprimir', change: 'Cambiarla',
    copied: 'Copiada. Péguela en su correo o en una carta.', copyFail: 'Seleccione el texto de la carta y cópielo.',
    youSend: 'RxGap no envía esta carta. Usted la envía.', offEmail: 'Busque el correo electrónico de cada funcionario en su página:',
    mhMail: (office) => `Envíela por correo postal a ${office} y mande la copia a sus funcionarios:`,
    subject: { officials: 'Por favor, mantengan una farmacia cerca de nosotros', masshealth: 'Por favor, paguen el transporte a la farmacia o la entrega a domicilio' },
  },
  ht: {
    title: 'Ekri yon lèt', steps: ['Reprezantan w yo', 'Lèt ou', 'Se ou ki voye l'],
    note: (gov) => `RxGap se yon zouti IA yo te fè nan Hackachusetts; se pa ${gov}. Li pa janm voye anyen pou ou.`,
    addr: (place) => `Adrès lakay ou nan ${place}`, addrHint: 'Lari, vil ak kòd postal', find: 'Jwenn reprezantan m yo',
    privacy: 'Adrès ou ale nan Biwo Resansman Etazini sèlman pou jwenn zòn ou. RxGap pa kenbe l.',
    sampleTip: (what) => `Tèks gri a se yon adrès egzanp: ${what}, yon bilding piblik nan yon dezè famasi. Klike nan bwat la oswa peze ↓ pou w sèvi avè l.`,
    looking: 'N ap chèche zòn ou…',
    noMatch: 'Nou pa jwenn adrès sa a. Verifye lari a ak kòd postal la, oswa chwazi zòn ou sou kat la.',
    down: 'Rechèch Resansman an pa disponib kounye a. Chwazi zòn ou sou kat la.',
    outside: (place) => `Adrès sa a pa nan ${place}. Chwazi kote sa a anlè paj la anvan.`,
    noAddr: 'Ou pa vle bay adrès ou? Fèmen fenèt sa a, klike sou zòn ou sou kat la, epi chwazi “Write a letter”.',
    found: 'Adrès nou jwenn:', block: 'Zòn ou nan',
    desert: 'deja se yon dezè famasi', near: (s) => `ta tounen yon dezè famasi si ${s} fèmen`,
    covered: 'gen yon famasi moun ka mache ale',
    officials: 'Reprezantan w yo', contact: 'Kontak', ok: 'Wi, se reprezantan m yo', redo: 'Sèvi ak yon lòt adrès',
    ask: 'Kisa ou vle mande?',
    keep: 'Pou gen yon famasi toupre nou', keepTo: 'Bay reprezantan w yo',
    keepOff: 'Zòn ou toujou gen yon famasi moun ka mache ale',
    rides: 'Pou yo peye transpò pou famasi a oswa livrezon lakay', ridesTo: 'Bay MassHealth, ak yon kopi pou reprezantan w yo',
    label: 'Nan pwòp mo pa w: poukisa sa enpòtan pou ou?', req: '(obligatwa)', eg: 'Pa egzanp',
    tip: 'Klike nan bwat vid la, oswa peze ↓ ak ↑, pou w wè yon fraz egzanp. Apre sa, chanje l ak pwòp mo pa w.',
    make: 'Fè lèt mwen', back: 'Retounen',
    enCopy: 'Kopi an angle',
    aiNote: 'Tradiksyon an fèt ak èd IA. Li l, oswa mande yon moun ou fè konfyans tcheke l, anvan ou voye l.',
    copy: 'Kopye lèt la', email: 'Louvri l nan imel mwen', print: 'Enprime', change: 'Chanje l',
    copied: 'Li kopye. Kole l nan imel ou oswa nan yon lèt.', copyFail: 'Chwazi tèks lèt la epi kopye l.',
    youSend: 'RxGap pa voye lèt sa a. Se ou ki voye l.', offEmail: 'Chèche imel chak reprezantan sou paj yo:',
    mhMail: (office) => `Voye l pa lapòs bay ${office}, epi voye kopi a bay reprezantan w yo:`,
    subject: { officials: 'Tanpri kenbe yon famasi toupre nou', masshealth: 'Tanpri peye transpò pou famasi a oswa livrezon lakay' },
  },
};
const GOV = { en: 'place_gov', es: 'place_gov_es', ht: 'place_gov_ht' };

// Help text is markdown-lite. It is rendered with html=true first, so every fact arrives escaped.
function md(text) {
  const inline = (t) => t.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
  return text.trim().split(/\n{2,}/).map((b) => {
    if (b.startsWith('## ')) return `<h3>${inline(b.slice(3))}</h3>`;
    if (b.startsWith('- ')) return `<ul>${b.split('\n').map((l) => `<li>${inline(l.replace(/^- /, ''))}</li>`).join('')}</ul>`;
    return `<p>${inline(b).replace(/\n/g, '<br>')}</p>`;
  }).join('');
}

function dialog(title, kind) {
  let d = document.getElementById('act');
  if (!d) {
    d = document.createElement('dialog');
    d.id = 'act';
    d.setAttribute('aria-labelledby', 'act-title');
    d.innerHTML = `<header class="act-bar"><h2 id="act-title"></h2><div class="act-tools"></div>
      <button class="close" aria-label="Close">×</button></header><div class="act-body"></div>`;
    d.querySelector('.close').addEventListener('click', () => d.close());
    d.addEventListener('close', () => document.body.classList.remove('act-open'));
    document.body.append(d);
  }
  d.className = `act act-${kind}`;
  d.querySelector('#act-title').textContent = title;
  const tools = d.querySelector('.act-tools'), body = d.querySelector('.act-body');
  tools.innerHTML = '';
  body.removeAttribute('lang');
  if (!d.open) d.showModal();
  document.body.classList.add('act-open');
  body.scrollTop = 0;
  return { tools, body };
}

const printBtn = '<button class="btn btn-quiet" data-act="print">Print</button>';
document.addEventListener('click', (e) => { if (e.target.closest('[data-act="print"]')) window.print(); });
// A modal dialog prints badly (clipped, centered), so print a plain copy of its content instead.
addEventListener('beforeprint', () => {
  const d = document.getElementById('act');
  document.getElementById('print-root')?.remove();
  if (!d?.open) return;
  const p = document.createElement('div');
  p.id = 'print-root';
  p.innerHTML = d.querySelector('.act-body').innerHTML;
  document.body.append(p);
});
addEventListener('afterprint', () => document.getElementById('print-root')?.remove());
const langBtns = (cur) => `<div class="seg-btns" role="group" aria-label="Language">${Object.entries(LANGS).map(([k, v]) =>
  `<button class="seg-btn${k === cur ? ' is-on' : ''}" data-lang="${k}" aria-pressed="${k === cur}">${v}</button>`).join('')}</div>`;

// Every rule the text leans on, with its source and the day we last confirmed it.
async function sources(ids) {
  const rows = (await policy()).filter((r) => ids.includes(r.id));
  return `<section class="act-src"><h4>Sources for these rules</h4><ul>${rows.map((r) => `<li>${esc(r.statement)}
    <a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.cite)} ↗</a>
    <small>Last confirmed ${esc(r.confirmed)}.${r.note ? ` ${esc(r.note)}` : ''}</small></li>`).join('')}</ul></section>`;
}

async function letterCount(key) {
  try {
    const [kind, id] = key.split(':');
    const rows = await fetch('/counts').then((r) => r.json());
    return rows.find((r) => r.district_type === kind && r.district_id === id)?.letters ?? 0;
  } catch {
    return 'not available';
  }
}

export async function openBrief(F, rank, key, back) {
  const rows = F.briefs[String(rank)];
  const r = rows.find((x) => x.official_key === key) || rows[0];
  const { tools, body } = dialog('Brief for officials', 'brief');
  tools.innerHTML = `${back ? '<button class="btn btn-quiet" id="brief-back">← Officials</button>' : ''}
    <label class="sr-only" for="brief-who">Official</label>
    <select id="brief-who">${rows.map((x) => `<option value="${esc(x.official_key)}"${x === r ? ' selected' : ''}>${esc(x.official_title)} ${esc(x.official_name)} · ${esc(x.official_district)}</option>`).join('')}</select>${printBtn}`;
  tools.querySelector('#brief-who').addEventListener('change', (e) => openBrief(F, rank, e.target.value, back));
  tools.querySelector('#brief-back')?.addEventListener('click', back);
  const facts = { ...F.place, ...r, letters: await letterCount(r.official_key) };
  body.innerHTML = render(await tpl('brief.en.html'), facts, true) + await sources(['closure_notice', 'pickup_rides']);
}

export function openOfficials(F) {
  const by = new Map();
  for (const [rank, rows] of Object.entries(F.briefs)) {
    for (const r of rows) {
      if (!by.has(r.official_key)) by.set(r.official_key, { r, stores: [] });
      by.get(r.official_key).stores.push({ rank, name: r.store_name, address: r.store_address, people: r.official_people });
    }
  }
  const list = [...by.values()].sort((a, b) => b.stores.reduce((n, s) => n + s.people, 0) - a.stores.reduce((n, s) => n + s.people, 0));
  const { body } = dialog(`Officials in ${F.place.place}`, 'offs');
  body.innerHTML = `<p class="act-small">Pick a store to open the one-page brief for that official. The number is how many of their residents would lose walkable access if that store closed.</p>
    <div class="off-grid">${list.map(({ r, stores }) => `<section class="off-card">
      <h3>${esc(r.official_title)} ${esc(r.official_name)} <small>${esc(r.official_district)}</small></h3>
      <ul>${stores.map((s) => `<li><button class="link" data-rank="${s.rank}" data-key="${esc(r.official_key)}">${esc(s.name)}${s.address ? ` <small>${esc(s.address)}</small>` : ''}</button><b>${fmt(s.people)}</b></li>`).join('')}</ul>
    </section>`).join('')}</div>`;
  body.querySelectorAll('[data-rank]').forEach((b) => b.addEventListener('click', () => openBrief(F, b.dataset.rank, b.dataset.key, () => openOfficials(F))));
}

export async function openHelp(F, geoid, lang = 'en') {
  const { tools, body } = dialog('Get medicine delivered', 'help');
  tools.innerHTML = langBtns(lang) + printBtn;
  tools.querySelectorAll('[data-lang]').forEach((x) => x.addEventListener('click', () => openHelp(F, geoid, x.dataset.lang)));
  body.lang = lang;
  body.innerHTML = md(render(await tpl(`help.${lang}.md`), { ...F.place, ...F.blocks[geoid] }, true))
    + await sources(['delivery_fee', 'mail_months', 'vaccine_rides', 'pt1_days', 'pickup_rides', 'mh_phone']);
}

function countLetter(b, topic) {
  const k = `${b.geoid}:${topic}`;
  if (counted.has(k)) return;
  counted.add(k);
  for (const o of b.officials) {
    fetch('/count', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ district_type: o.kind, district_id: o.id }) }).catch(() => {});
  }
}

export function openLetter(F, { geoid = null } = {}) {
  const st = { geoid, topic: null, lang: 'en', sentence: '', matched: '', step: null };
  const { tools, body } = dialog(UI.en.title, 'letter');
  const $ = (s) => body.querySelector(s);
  const t = () => UI[st.lang];
  const samples = () => SAMPLES[st.topic || 'officials'][st.lang];
  // A sample the resident has not changed follows a switch of topic or language; their own words never do.
  const follow = (change) => {
    const i = samples().indexOf(st.sentence);
    change();
    if (i >= 0) st.sentence = samples()[i];
  };
  const go = (step) => {
    st.step = step;
    document.getElementById('act-title').textContent = t().title;
    tools.innerHTML = langBtns(st.lang);
    tools.querySelectorAll('[data-lang]').forEach((x) => x.addEventListener('click', () => {
      follow(() => { st.lang = x.dataset.lang; });
      go(st.step);
      tools.querySelector(`[data-lang="${st.lang}"]`).focus();
    }));
    body.lang = st.lang;
    step();
  };
  const steps = (n) => `<ol class="steps">${t().steps.map((s, i) =>
    `<li class="${i + 1 === n ? 'is-on' : i + 1 < n ? 'is-done' : ''}"${i + 1 === n ? ' aria-current="step"' : ''}>${esc(s)}</li>`).join('')}</ol>`;
  const note = () => `<p class="act-note">${esc(t().note(F.place[GOV[st.lang]]))}</p>`;

  const find = () => {
    body.innerHTML = `${steps(1)}
      <form class="find" id="find">
        <label for="addr">${esc(t().addr(F.place.place))}</label>
        <div class="row"><input id="addr" autocomplete="street-address" placeholder="${esc(F.place.sample_address || t().addrHint)}" required minlength="5" maxlength="200"${F.place.sample_address ? ' aria-describedby="addr-tip"' : ''}>
          <button class="btn">${esc(t().find)}</button></div>
        ${F.place.sample_address ? `<p class="act-small" id="addr-tip">${esc(t().sampleTip(F.place.sample_what))}</p>` : ''}
        <p class="act-small">${esc(t().privacy)}</p>
      </form>
      <p class="act-msg" id="find-msg" role="status"></p>
      <p class="act-small">${esc(t().noAddr)}</p>${note()}`;
    // The gray sample becomes real text on a click or ↓, selected so typing replaces it at once.
    const addr = $('#addr');
    const useSample = () => {
      if (!F.place.sample_address || addr.value.trim()) return false;
      addr.value = F.place.sample_address;
      addr.select();
      return true;
    };
    addr.addEventListener('click', useSample);
    addr.addEventListener('keydown', (e) => { if (['ArrowDown', 'ArrowRight', 'Enter'].includes(e.key) && useSample()) e.preventDefault(); });
    $('#find').addEventListener('submit', async (e) => {
      e.preventDefault();
      const say = (s) => { $('#find-msg').textContent = s; };
      say(t().looking);
      try {
        const r = await fetch(`/geocode?address=${encodeURIComponent($('#addr').value.trim())}`);
        if (r.status === 404) return say(t().noMatch);
        if (!r.ok) return say(t().down);
        const hit = await r.json();
        if (!F.blocks[hit.geoid]) return say(t().outside(F.place.place));
        Object.assign(st, { geoid: hit.geoid, matched: hit.matched });
        go(confirm);
      } catch {
        say(t().down);
      }
    });
  };

  const confirm = () => {
    const b = F.blocks[st.geoid];
    const status = b.is_desert ? t().desert : b.is_near ? t().near(b.store_name) : t().covered;
    body.innerHTML = `${steps(1)}
      ${st.matched ? `<p class="act-small">${esc(t().found)} ${esc(st.matched)}</p>` : ''}
      <p class="act-lead">${esc(t().block)} <b>${esc(b.where)}</b> ${esc(status)}.</p>
      <h3>${esc(t().officials)}</h3>
      <ul class="offs">${b.officials.map((o) => `<li><span>${esc(o.title)} ${esc(o.name)} <small>(${esc(o.district)})</small></span>${o.url ? `<a href="${esc(o.url)}" target="_blank" rel="noopener">${esc(t().contact)} ↗</a>` : ''}</li>`).join('')}</ul>
      <div class="row"><button class="btn" id="ok1">${esc(t().ok)}</button><button class="btn btn-quiet" id="redo1">${esc(t().redo)}</button></div>${note()}`;
    $('#ok1').addEventListener('click', () => go(write));
    $('#redo1').addEventListener('click', () => go(find));
  };

  const write = () => {
    const b = F.blocks[st.geoid];
    const canOff = b.is_near || b.is_desert;
    if (!st.topic || (!canOff && st.topic === 'officials')) st.topic = canOff ? 'officials' : 'masshealth';
    const topic = (v, name, sub, ok = true) => `<label class="topic${ok ? '' : ' is-off'}"><input type="radio" name="topic" value="${v}"${st.topic === v ? ' checked' : ''}${ok ? '' : ' disabled'}>
      <span><b>${esc(name)}</b><small>${esc(sub)}</small></span></label>`;
    body.innerHTML = `${steps(2)}
      <fieldset class="topics"><legend>${esc(t().ask)}</legend>
        ${topic('officials', t().keep, canOff ? t().keepTo : t().keepOff, canOff)}
        ${topic('masshealth', t().rides, t().ridesTo)}
      </fieldset>
      <label class="act-label" for="own" id="own-label">${esc(t().label)} <small>${esc(t().req)}</small></label>
      <textarea id="own" rows="3" maxlength="600" aria-describedby="own-tip"></textarea>
      <p class="act-small" id="own-tip">${esc(t().tip)}</p>
      <div class="row"><button class="btn" id="make" disabled>${esc(t().make)}</button><button class="btn btn-quiet" id="back2">${esc(t().back)}</button></div>${note()}`;
    const own = $('#own');
    let k = -1;
    const sync = () => { st.sentence = own.value.trim(); k = samples().indexOf(st.sentence); $('#make').disabled = !st.sentence; };
    const hint = () => { own.placeholder = `${t().eg}: ${samples()[0]}`; };
    const put = (i) => {
      own.value = samples()[(i + samples().length) % samples().length];
      own.setSelectionRange(own.value.length, own.value.length);
      sync();
    };
    own.value = st.sentence;
    hint();
    sync();
    own.addEventListener('input', sync);
    own.addEventListener('click', () => { if (!own.value.trim()) put(0); });
    own.addEventListener('keydown', (e) => {
      if (!['ArrowDown', 'ArrowUp'].includes(e.key) || (own.value.trim() && k < 0)) return;  // never replace the resident's own words
      e.preventDefault();
      const step = e.key === 'ArrowDown' ? 1 : -1;
      put(k < 0 ? (step > 0 ? 0 : samples().length - 1) : k + step);
    });
    body.querySelectorAll('[name="topic"]').forEach((x) => x.addEventListener('change', () => {
      follow(() => { st.topic = x.value; });
      own.value = st.sentence;
      hint();
      sync();
    }));
    $('#make').addEventListener('click', () => go(show));
    $('#back2').addEventListener('click', () => go(confirm));
  };

  const show = async () => {
    const b = F.blocks[st.geoid];
    const kind = st.topic === 'officials' ? 'letter' : 'letter_masshealth';
    const facts = { ...F.place, ...b, own_sentence: st.sentence };
    const lang = st.lang;
    const [main, en] = await Promise.all([render(await tpl(`${kind}.${lang}.md`), facts),
      lang === 'en' ? '' : render(await tpl(`${kind}.en.md`), facts)]);
    if (lang !== st.lang) return;  // the resident switched language while the text loaded
    const all = en ? `${main}\n----\nEnglish copy\n\n${en}` : main;
    countLetter(b, st.topic);
    const contacts = b.officials.filter((o) => o.url).map((o) => `<a href="${esc(o.url)}" target="_blank" rel="noopener">${esc(o.title)} ${esc(o.name)} ↗</a>`).join(' · ');
    body.innerHTML = `${steps(3)}
      <div class="letters${en ? ' two' : ''}">
        <section><h3>${LANGS[lang]}</h3><pre class="letter-text" lang="${lang}">${esc(main)}</pre></section>
        ${en ? `<section lang="en"><h3>${esc(t().enCopy)}</h3><pre class="letter-text" lang="en">${esc(en)}</pre></section>` : ''}
      </div>
      ${en ? `<p class="act-small">${esc(t().aiNote)}</p>` : ''}
      <div class="row"><button class="btn" id="copy">${esc(t().copy)}</button>
        <a class="btn btn-quiet" href="mailto:?subject=${encodeURIComponent(t().subject[st.topic])}&amp;body=${encodeURIComponent(all)}">${esc(t().email)}</a>
        <button class="btn btn-quiet" data-act="print">${esc(t().print)}</button><button class="btn btn-quiet" id="back3">${esc(t().change)}</button></div>
      <p class="act-msg" id="copy-msg" role="status"></p>
      <p class="act-small"><b>${esc(t().youSend)}</b> ${esc(st.topic === 'officials' ? t().offEmail : t().mhMail(F.place.mh_office))} ${contacts}</p>${note()}`;
    $('#copy').addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(all); $('#copy-msg').textContent = t().copied; } catch { $('#copy-msg').textContent = t().copyFail; }
    });
    $('#back3').addEventListener('click', () => go(write));
  };

  go(st.geoid ? confirm : find);
}
