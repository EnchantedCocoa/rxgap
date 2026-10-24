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
  const st = { geoid, topic: null, lang: 'en', sentence: '', matched: '' };
  const { body } = dialog('Write a letter', 'letter');
  const $ = (s) => body.querySelector(s);
  const steps = (n) => `<ol class="steps">${['Your officials', 'Your letter', 'Send it yourself'].map((t, i) =>
    `<li class="${i + 1 === n ? 'is-on' : i + 1 < n ? 'is-done' : ''}"${i + 1 === n ? ' aria-current="step"' : ''}>${t}</li>`).join('')}</ol>`;
  const note = `<p class="act-note">RxGap is an AI tool built at Hackachusetts, not ${esc(F.place.place_gov)}. It never sends anything for you.</p>`;

  const find = () => {
    body.innerHTML = `${steps(1)}
      <form class="find" id="find">
        <label for="addr">Your home address in ${esc(F.place.place)}</label>
        <div class="row"><input id="addr" autocomplete="street-address" placeholder="Street, city and ZIP" required minlength="5" maxlength="200">
          <button class="btn">Find my officials</button></div>
        <p class="act-small">Your address goes to the US Census Bureau only to find your block. RxGap does not keep it.</p>
      </form>
      <p class="act-msg" id="find-msg" role="status"></p>
      <p class="act-small">No address? Close this, click your block on the map, then choose “Write a letter”.</p>${note}`;
    $('#find').addEventListener('submit', async (e) => {
      e.preventDefault();
      const say = (t) => { $('#find-msg').textContent = t; };
      say('Looking up your block…');
      try {
        const r = await fetch(`/geocode?address=${encodeURIComponent($('#addr').value.trim())}`);
        if (r.status === 404) return say('We could not match that address. Check the street and ZIP, or pick your block on the map.');
        if (!r.ok) return say('The Census lookup is not available right now. Pick your block on the map instead.');
        const hit = await r.json();
        if (!F.blocks[hit.geoid]) return say(`That address is outside ${F.place.place}. Choose its place at the top of the page first.`);
        Object.assign(st, { geoid: hit.geoid, matched: hit.matched });
        confirm();
      } catch {
        say('The Census lookup is not available right now. Pick your block on the map instead.');
      }
    });
  };

  const confirm = () => {
    const b = F.blocks[st.geoid];
    const status = b.is_desert ? 'is a pharmacy desert today'
      : b.is_near ? `would become a pharmacy desert if the ${b.store_name} closed` : 'has a pharmacy within walking distance';
    body.innerHTML = `${steps(1)}
      ${st.matched ? `<p class="act-small">Address found: ${esc(st.matched)}</p>` : ''}
      <p class="act-lead">Your block in <b>${esc(b.where)}</b> ${esc(status)}.</p>
      <h3>Your officials</h3>
      <ul class="offs">${b.officials.map((o) => `<li><span>${esc(o.title)} ${esc(o.name)} <small>(${esc(o.district)})</small></span>${o.url ? `<a href="${esc(o.url)}" target="_blank" rel="noopener">Contact ↗</a>` : ''}</li>`).join('')}</ul>
      <div class="row"><button class="btn" id="ok1">These are my officials</button><button class="btn btn-quiet" id="redo1">Use another address</button></div>${note}`;
    $('#ok1').addEventListener('click', write);
    $('#redo1').addEventListener('click', find);
  };

  const write = () => {
    const b = F.blocks[st.geoid];
    const canOff = b.is_near || b.is_desert;
    if (!st.topic || (!canOff && st.topic === 'officials')) st.topic = canOff ? 'officials' : 'masshealth';
    const topic = (v, t, sub, ok = true) => `<label class="topic${ok ? '' : ' is-off'}"><input type="radio" name="topic" value="${v}"${st.topic === v ? ' checked' : ''}${ok ? '' : ' disabled'}>
      <span><b>${t}</b><small>${sub}</small></span></label>`;
    body.innerHTML = `${steps(2)}
      <fieldset class="topics"><legend>What do you want to ask for?</legend>
        ${topic('officials', 'Keep a pharmacy near us', canOff ? 'To your officials' : 'Your block still has a pharmacy within walking distance', canOff)}
        ${topic('masshealth', 'Pay for pharmacy rides or delivery', 'To MassHealth, with a copy to your officials')}
      </fieldset>
      <p class="act-label">Language</p>${langBtns(st.lang)}
      <label class="act-label" for="own">In your own words: why does this matter to you? <small>(required)</small></label>
      <textarea id="own" rows="3" maxlength="600" placeholder="For example: my father takes heart medicine and does not drive."></textarea>
      <div class="row"><button class="btn" id="make" disabled>Make my letter</button><button class="btn btn-quiet" id="back2">Back</button></div>${note}`;
    const own = $('#own');
    own.value = st.sentence;
    const sync = () => { st.sentence = own.value.trim(); $('#make').disabled = !st.sentence; };
    sync();
    own.addEventListener('input', sync);
    body.querySelectorAll('[name="topic"]').forEach((x) => x.addEventListener('change', () => { st.topic = x.value; }));
    body.querySelectorAll('[data-lang]').forEach((x) => x.addEventListener('click', () => { st.lang = x.dataset.lang; write(); }));
    $('#make').addEventListener('click', show);
    $('#back2').addEventListener('click', confirm);
  };

  const show = async () => {
    const b = F.blocks[st.geoid];
    const kind = st.topic === 'officials' ? 'letter' : 'letter_masshealth';
    const facts = { ...F.place, ...b, own_sentence: st.sentence };
    const main = render(await tpl(`${kind}.${st.lang}.md`), facts);
    const en = st.lang === 'en' ? '' : render(await tpl(`${kind}.en.md`), facts);
    const all = en ? `${main}\n----\nEnglish copy\n\n${en}` : main;
    const subject = st.topic === 'officials' ? 'Please keep a pharmacy within walking distance' : 'Please pay for pharmacy rides or home delivery';
    countLetter(b, st.topic);
    const contacts = b.officials.filter((o) => o.url).map((o) => `<a href="${esc(o.url)}" target="_blank" rel="noopener">${esc(o.title)} ${esc(o.name)} ↗</a>`).join(' · ');
    body.innerHTML = `${steps(3)}
      <div class="letters${en ? ' two' : ''}">
        <section><h3>${LANGS[st.lang]}</h3><pre class="letter-text" lang="${st.lang}">${esc(main)}</pre></section>
        ${en ? `<section><h3>English copy</h3><pre class="letter-text" lang="en">${esc(en)}</pre></section>` : ''}
      </div>
      ${en ? '<p class="act-small">Translated with AI help. Please read it, or ask someone you trust to check it, before you send it.</p>' : ''}
      <div class="row"><button class="btn" id="copy">Copy letter</button>
        <a class="btn btn-quiet" href="mailto:?subject=${encodeURIComponent(subject)}&amp;body=${encodeURIComponent(all)}">Open in my email</a>
        ${printBtn}<button class="btn btn-quiet" id="back3">Change it</button></div>
      <p class="act-msg" id="copy-msg" role="status"></p>
      <p class="act-small"><b>RxGap does not send this. You do.</b> ${st.topic === 'officials' ? 'Find each official’s email on their page:' : `Mail it to ${esc(F.place.mh_office)}, and send the copy to your officials:`} ${contacts}</p>${note}`;
    $('#copy').addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(all); $('#copy-msg').textContent = 'Copied. Paste it into your email or a letter.'; } catch { $('#copy-msg').textContent = 'Select the letter text and copy it.'; }
    });
    $('#back3').addEventListener('click', write);
  };

  if (st.geoid) confirm(); else find();
}
