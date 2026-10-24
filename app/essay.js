// 첫 화면 사진 에세이: 실제 사진과 출처 있는 통계, 우리 숫자는 모두 데이터에서 넣는다.
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmt = (n) => Number(n).toLocaleString('en-US');

// Story text only. No digits here: every number comes from evidence.json or app_data.json.
const CHAPTERS = [
  { photo: '04_closed-walgreens-oakland', hero: true,
    kicker: 'RxGap · Massachusetts',
    title: 'When the pharmacy closes, people stop taking their heart medicine.',
    dek: 'Chains are closing stores across the country. The blocks they leave behind often have the fewest cars and the most older neighbors.' },
  { photo: '01_empty-rite-aid-la', title: 'The prescriptions stop first.',
    lead: 'qato-statin-drop', facts: ['qato-all-three-meds', 'nonadherence-cost'] },
  { photo: '03_closed-rite-aid-waterford-ct', title: 'And the closures are speeding up.',
    facts: ['rite-aid-closed-all', 'walgreens-1200', 'cvs-900'] },
  { photo: '09_pharmacy-line-austin', title: 'The blocks with the least lose the most.',
    lead: 'qato-independent-worse', facts: ['guadamuz-pharmacy-deserts', 'national-closure-rate'] },
  { photo: '06_mattapan-square', title: 'Massachusetts is not spared.',
    lead: 'ma-pharmacy-deserts', facts: ['ma-pharmacy-decline', 'ma-one-million-at-risk'] },
  { photo: '08_blue-hill-ave-bus', ours: true },
];

// Big number, smaller unit: "580,000 people" -> 580,000 + people.
const val = (v) => { const m = String(v).match(/^(.*[\d%+)])(\s+[^\d]+)?$/); return m ? `${esc(m[1])}${m[2] ? `<small>${esc(m[2])}</small>` : ''}` : esc(v); };

function fact(f, big) {
  return `<div class="es-fact${big ? ' is-big' : ''}">
    <div class="es-val">${val(f.value)}</div>
    <p class="es-say">${esc(f.statement)}</p>
    ${big ? `<p class="es-detail">${esc(f.detail)}</p>` : ''}
    <a class="es-src" href="${esc(f.url)}" target="_blank" rel="noopener">${esc(f.publisher)}, ${esc(f.year)} ↗</a>
  </div>`;
}

function ours(D) {
  const h = D.headline.state, s = D.stores[0], v = D.validation;
  return `<p class="es-kicker">What RxGap found</p>
    <h2 class="es-title">In ${esc(D.place.name)}, we checked every block.</h2>
    <div class="es-fact is-big">
      <div class="es-val">${fmt(h.desert + h.near)}<button class="info" data-prov="headline" aria-label="How we got this">i</button></div>
      <p class="es-say">residents live in a pharmacy desert or one closure away.</p>
      <p class="es-detail">That is 1 in ${fmt(v.one_in)} people. Among them, ${fmt(v.at_risk_age65)} are 65 or older.</p>
    </div>
    <div class="es-fact">
      <div class="es-val">${fmt(s.people)}<button class="info" data-prov="store" aria-label="How we got this">i</button></div>
      <p class="es-say">would lose walkable access if one store closed: the ${esc(s.name)} at ${esc(String(s.address).split(',')[0])}.</p>
    </div>`;
}

export async function openEssay(D, { reduced = false } = {}) {
  const [ev, photos] = await Promise.all([
    fetch('../data/manual/evidence.json').then((r) => r.json()),
    fetch('../data/manual/photos.json').then((r) => r.json()),
  ]);
  const E = Object.fromEntries(ev.map((f) => [f.id, f]));
  const P = Object.fromEntries(photos.map((p) => [p.file.replace(/\.jpg$/, ''), p]));
  const credit = (p) => `${esc(p.caption)} <span>Photo: <a href="${esc(p.source_url)}" target="_blank" rel="noopener">${esc(p.author)}</a>, <a href="${esc(p.license_url)}" target="_blank" rel="noopener">${esc(p.license)}</a></span>`;

  const root = document.createElement('div');
  root.id = 'essay';
  root.setAttribute('role', 'dialog');
  root.tabIndex = -1;
  root.setAttribute('aria-modal', 'true');
  root.setAttribute('aria-label', 'Why pharmacy closures matter');
  if (reduced) root.classList.add('is-still');
  root.innerHTML = `
    <div class="es-bar"><span class="es-brand">RxGap</span>
      <button class="es-skip" id="es-skip">Skip to the map →</button></div>
    ${CHAPTERS.map((c, i) => {
      const p = P[c.photo];
      const body = c.ours ? ours(D) : `
        ${c.kicker ? `<p class="es-kicker">${esc(c.kicker)}</p>` : ''}
        ${c.hero ? `<h1 class="es-title">${esc(c.title)}</h1>` : `<h2 class="es-title">${esc(c.title)}</h2>`}
        ${c.dek ? `<p class="es-dek">${esc(c.dek)}</p>` : ''}
        ${c.lead ? fact(E[c.lead], true) : ''}
        ${c.facts ? `<div class="es-row">${c.facts.map((id) => fact(E[id], false)).join('')}</div>` : ''}`;
      return `<section class="es-ch${c.hero ? ' is-hero' : ''}" data-i="${i}">
        <div class="es-photo" style="background-image:url('img/essay/${esc(p.file)}')"></div>
        <div class="es-shade"></div>
        <div class="es-copy">${body}</div>
        ${c.hero ? '<div class="es-cue" aria-hidden="true">Scroll</div>' : ''}
        <p class="es-credit">${credit(p)}</p>
      </section>`;
    }).join('')}
    <section class="es-ch es-end">
      <div class="es-copy">
        <h2 class="es-title">See who loses access, store by store.</h2>
        <p class="es-dek">Pick a pharmacy. Close it. Watch which blocks turn red, and find the best place for a new one.</p>
        <button class="es-go" id="es-go">Open the map</button>
        <p class="es-fine">Statistics link to their sources. Our own numbers have an “i” button that shows how we got them.
          Photos are free-licensed; most show closed stores outside Massachusetts.</p>
      </div>
    </section>`;
  document.body.append(root);
  document.body.classList.add('essay-open');

  const io = new IntersectionObserver((xs) => xs.forEach((x) => x.isIntersecting && x.target.classList.add('is-in')),
    { root, threshold: 0.35 });
  root.querySelectorAll('.es-ch').forEach((s) => io.observe(s));
  root.focus({ preventScroll: true });

  return new Promise((done) => {
    const close = () => {
      io.disconnect();
      document.removeEventListener('keydown', onKey);
      document.body.classList.remove('essay-open');
      root.classList.add('is-leaving');
      setTimeout(() => { root.remove(); done(); }, reduced ? 0 : 600);
    };
    const onKey = (e) => { if (e.key === 'Escape') close(); };
    document.addEventListener('keydown', onKey);
    root.querySelector('#es-skip').addEventListener('click', close);
    root.querySelector('#es-go').addEventListener('click', close);
  });
}
