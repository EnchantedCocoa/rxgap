// 템플릿에 사실(facts) 값을 채우는 렌더러: rxgap/text.py와 같은 규칙으로 같은 결과를 낸다.
const TOKEN = /\{([#?^/]?)(\w+)\}/g;
const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };

// Numbers get thousands commas and at most one decimal, the same in every language.
export function fmt(v, html = false) {
  if (v == null || typeof v === 'boolean' || typeof v === 'object') throw new TypeError(`cannot print ${JSON.stringify(v)}`);
  const s = typeof v === 'number'
    ? (Number.isInteger(v) ? v.toLocaleString('en-US') : v.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }))
    : String(v);
  return html ? s.replace(/[&<>"']/g, (c) => ESC[c]) : s;
}

const lookup = (stack, name) => {
  for (const ctx of stack) if (ctx && typeof ctx === 'object' && !Array.isArray(ctx) && name in ctx) return ctx[name];
  return null;
};
const truthy = (v) => (Array.isArray(v) ? v.length > 0 : Boolean(v));

function close(tpl, name, start) {
  const re = new RegExp(TOKEN.source, 'g');
  re.lastIndex = start;
  let depth = 1, m;
  while ((m = re.exec(tpl))) {
    if (m[2] !== name) continue;
    depth += m[1] === '/' ? -1 : m[1] ? 1 : 0;
    if (depth === 0) return m;
  }
  throw new Error(`no {/${name}}`);
}

function walk(tpl, stack, html) {
  const re = new RegExp(TOKEN.source, 'g');
  let out = '', i = 0, m;
  while ((re.lastIndex = i, m = re.exec(tpl))) {
    out += tpl.slice(i, m.index);
    const [tok, kind, name] = m;
    if (!kind) {
      const v = lookup(stack, name);
      if (v == null) throw new Error(`missing fact: ${name}`);
      out += fmt(v, html);
      i = m.index + tok.length;
      continue;
    }
    if (kind === '/') throw new Error(`stray {/${name}}`);
    const end = close(tpl, name, m.index + tok.length);
    const inner = tpl.slice(m.index + tok.length, end.index), v = lookup(stack, name);
    if (kind === '#') out += (v || []).map((x) => walk(inner, [x, ...stack], html)).join('');
    else if ((kind === '?') === truthy(v)) out += walk(inner, stack, html);
    i = end.index + end[0].length;
  }
  return out + tpl.slice(i);
}

// {key} prints a fact; {#list}..{/list} repeats; {?key}..{/key} if set; {^key}..{/key} if not set.
export function render(tpl, facts, html = false) {
  const text = walk(tpl, [facts], html).replace(/[ \t]+\n/g, '\n').replace(/\n{3,}/g, '\n\n');
  return `${text.trim()}\n`;
}
