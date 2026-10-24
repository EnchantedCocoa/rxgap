// 첫 화면 사진 에세이: 실제 사진과 출처 있는 통계, 우리 숫자는 모두 데이터에서 넣는다.
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmt = (n) => Number(n).toLocaleString('en-US');
const clamp = (x) => Math.max(0, Math.min(1, x));

// Story text only. No digits here: every number comes from evidence.json or app_data.json.
const CHAPTERS = [
  { photo: '04_closed-walgreens-oakland', hero: true,
    kicker: 'RxGap · Massachusetts',
    title: 'When the pharmacy closes, people stop taking their heart medicine.',
    dek: 'Chains are closing stores across the country. The blocks they leave behind often have the fewest cars and the most older neighbors.' },
  { photo: '01_empty-rite-aid-la', title: 'The prescriptions stop first.',
    lead: 'qato-statin-drop', facts: ['qato-independent-worse', 'nonadherence-cost'] },
  { photo: '03_closed-rite-aid-waterford-ct', title: 'And the closures are speeding up.',
    facts: ['rite-aid-closed-all', 'walgreens-1200', 'national-closure-rate', 'guadamuz-pharmacy-deserts'] },
  { photo: '06_mattapan-square', title: 'Massachusetts is not spared.',
    lead: 'ma-pharmacy-deserts', facts: ['ma-pharmacy-decline'], ours: 'headline' },
  { photo: '10_pharmacy-desert-rally', end: true },
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

// Our own numbers, with the same "how we got this" button as the map.
function oursFact(D) {
  const h = D.headline.state;
  return `<div class="es-fact is-ours">
    <div class="es-val">${fmt(h.desert + h.near)}<button class="info" data-prov="headline" aria-label="How we got this">i</button></div>
    <p class="es-say">${esc(D.place.name)} residents in a desert or one closure away: 1 in ${fmt(D.validation.one_in)}.</p>
    <span class="es-src">RxGap, block by block</span>
  </div>`;
}

function endCopy(D) {
  const s = D.stores[0];
  return `<h2 class="es-title">See who loses access, store by store.</h2>
    <p class="es-dek">If the ${esc(s.name)} at ${esc(String(s.address).split(',')[0])} closes,
      <b class="es-num">${fmt(s.people)}</b><button class="info" data-prov="store" aria-label="How we got this">i</button>
      ${esc(D.place.name)} residents lose walkable access. Pick any store and watch.</p>
    <button class="es-go" id="es-go">Open the map</button>
    <p class="es-fine">Statistics link to their sources. Our own numbers have an “i” button that shows how we got them.
      Photos are credited where they appear; the closed stores shown are outside Massachusetts.</p>`;
}

export async function openEssay(D, { reduced = false } = {}) {
  const [ev, photos] = await Promise.all([
    fetch('../data/manual/evidence.json').then((r) => r.json()),
    fetch('../data/manual/photos.json').then((r) => r.json()),
  ]);
  const E = Object.fromEntries(ev.map((f) => [f.id, f]));
  const P = Object.fromEntries(photos.map((p) => [p.file.replace(/\.jpg$/, ''), p]));
  const link = (href, text) => (href ? `<a href="${esc(href)}" target="_blank" rel="noopener">${esc(text)}</a>` : esc(text));
  const credit = (p) => `${esc(p.caption)} <span>Photo: ${link(p.source_url, p.author)}, ${link(p.license_url, p.license)}</span>`;

  const root = document.createElement('div');
  root.id = 'essay';
  root.tabIndex = -1;
  root.setAttribute('role', 'dialog');
  root.setAttribute('aria-modal', 'true');
  root.setAttribute('aria-label', 'Why pharmacy closures matter');
  if (reduced) root.classList.add('is-still');
  // Photos sit in one fixed stack and cross-fade; the words scroll over them.
  root.innerHTML = `
    <div class="es-stage" aria-hidden="true">
      ${CHAPTERS.map((c) => `<div class="es-layer"><div class="es-photo" style="background-image:url('img/essay/${esc(P[c.photo].file)}')"></div></div>`).join('')}
      <div class="es-shade"></div>
    </div>
    <div class="es-bar"><span class="es-brand">RxGap</span>
      <button class="es-skip" id="es-skip">Skip to the map →</button></div>
    ${CHAPTERS.map((c, i) => {
      const body = c.end ? endCopy(D) : `
        ${c.kicker ? `<p class="es-kicker">${esc(c.kicker)}</p>` : ''}
        ${c.hero ? `<h1 class="es-title">${esc(c.title)}</h1>` : `<h2 class="es-title">${esc(c.title)}</h2>`}
        ${c.dek ? `<p class="es-dek">${esc(c.dek)}</p>` : ''}
        ${c.lead ? fact(E[c.lead], true) : ''}
        ${c.facts ? `<div class="es-row">${c.facts.map((id) => fact(E[id], false)).join('')}${c.ours ? oursFact(D) : ''}</div>` : ''}`;
      return `<section class="es-ch${c.hero ? ' is-hero' : ''}${c.end ? ' es-end' : ''}" data-i="${i}">
        <div class="es-copy">${body}</div>
        ${c.hero ? '<div class="es-cue" aria-hidden="true">Scroll</div>' : ''}
        <p class="es-credit">${credit(P[c.photo])}</p>
      </section>`;
    }).join('')}`;
  document.body.append(root);
  document.body.classList.add('essay-open');
  root.focus({ preventScroll: true });

  const layers = [...root.querySelectorAll('.es-layer')];
  const secs = [...root.querySelectorAll('.es-ch')];
  // Scroll-linked: photo i fades in as its section rises; words fade around the middle of the screen.
  let raf = 0;
  const paint = () => {
    raf = 0;
    const vh = root.clientHeight, y = root.scrollTop;
    secs.forEach((s, i) => {
      const top = s.offsetTop, h = s.offsetHeight;
      if (i) layers[i].style.opacity = clamp((y - (top - vh * 0.75)) / (vh * 0.75));
      layers[i].classList.toggle('is-on', y + vh > top && y < top + h);
      const mid = (top + h / 2 - (y + vh / 2)) / (vh * 0.75);
      const o = clamp(1.25 - Math.abs(mid) * 1.25);
      s.style.setProperty('--o', o.toFixed(3));
      s.style.setProperty('--dy', reduced ? '0px' : `${(mid * 40).toFixed(1)}px`);
    });
  };
  const onScroll = () => { if (!raf) raf = requestAnimationFrame(paint); };
  root.addEventListener('scroll', onScroll, { passive: true });
  addEventListener('resize', onScroll);
  paint();

  // One arrow press glides to the next or previous scene, centered on screen.
  const spot = (s) => Math.max(0, Math.min(root.scrollHeight - root.clientHeight, s.offsetTop + (s.offsetHeight - root.clientHeight) / 2));
  let anim = 0, goal = -1;
  const glide = (to) => {
    cancelAnimationFrame(anim);
    const from = root.scrollTop, t0 = performance.now(), ms = reduced ? 0 : 900;
    const tick = (now) => {
      const k = ms ? Math.min(1, (now - t0) / ms) : 1;
      root.scrollTop = from + (to - from) * (k < 0.5 ? 4 * k ** 3 : 1 - (-2 * k + 2) ** 3 / 2);
      if (k < 1) anim = requestAnimationFrame(tick); else goal = -1;
    };
    anim = requestAnimationFrame(tick);
  };
  const stop = () => { cancelAnimationFrame(anim); goal = -1; };
  root.addEventListener('wheel', stop, { passive: true });
  root.addEventListener('touchstart', stop, { passive: true });
  const step = (d) => {
    const T = secs.map(spot), y = root.scrollTop;
    const i = goal >= 0 ? goal : T.findIndex((t) => Math.abs(t - y) < 4);
    const n = i >= 0 ? i + d : d > 0 ? T.findIndex((t) => t > y + 4) : T.findLastIndex((t) => t < y - 4);
    if (n < 0 || n >= T.length) return;
    goal = n;
    glide(T[n]);
  };
  const KEYS = { ArrowDown: 1, PageDown: 1, ArrowUp: -1, PageUp: -1 };

  return new Promise((done) => {
    const close = () => {
      stop();
      root.removeEventListener('scroll', onScroll);
      removeEventListener('resize', onScroll);
      document.removeEventListener('keydown', onKey);
      document.body.classList.remove('essay-open');
      root.classList.add('is-leaving');
      setTimeout(() => { root.remove(); done(); }, reduced ? 0 : 700);
    };
    const onKey = (e) => {
      if (e.key === 'Escape') close();
      else if (KEYS[e.key]) { e.preventDefault(); step(KEYS[e.key]); }
    };
    document.addEventListener('keydown', onKey);
    root.querySelector('#es-skip').addEventListener('click', close);
    root.querySelector('#es-go').addEventListener('click', close);
  });
}
