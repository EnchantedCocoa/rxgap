# 템플릿에 사실(facts) 값을 채우는 렌더러: 숫자는 코드가 넣고, 템플릿에는 숫자가 없다 (app/text.js와 동일 규칙).
import re

TOKEN = re.compile(r'\{([#?^/]?)(\w+)\}')
ESC = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}


def fmt(v, html=False):
    """Numbers get thousands commas and at most one decimal, the same in every language."""
    if v is None or isinstance(v, (bool, list, dict)):
        raise TypeError(f'cannot print {v!r}')
    if isinstance(v, int):
        s = f'{v:,}'
    elif isinstance(v, float):
        s = f'{int(v):,}' if v.is_integer() else f'{v:,.1f}'
    else:
        s = str(v)
    return ''.join(ESC.get(c, c) for c in s) if html else s


def _lookup(stack, name):
    for ctx in stack:
        if isinstance(ctx, dict) and name in ctx:
            return ctx[name]
    return None


def _close(tpl, name, start):
    depth = 1
    for m in TOKEN.finditer(tpl, start):
        if m[2] == name:
            depth += -1 if m[1] == '/' else 1 if m[1] else 0
            if depth == 0:
                return m
    raise ValueError(f'no {{/{name}}}')


def _render(tpl, stack, html):
    out, i = [], 0
    while m := TOKEN.search(tpl, i):
        out.append(tpl[i:m.start()])
        kind, name = m[1], m[2]
        if not kind:
            v = _lookup(stack, name)
            if v is None:
                raise KeyError(name)
            out.append(fmt(v, html))
            i = m.end()
            continue
        if kind == '/':
            raise ValueError(f'stray {{/{name}}}')
        end = _close(tpl, name, m.end())
        inner, v = tpl[m.end():end.start()], _lookup(stack, name)
        if kind == '#':
            out += [_render(inner, [x, *stack], html) for x in (v or [])]
        elif (kind == '?') == bool(v):
            out.append(_render(inner, stack, html))
        i = end.end()
    out.append(tpl[i:])
    return ''.join(out)


def render(tpl, facts, html=False):
    """{key} prints a fact; {#list}..{/list} repeats; {?key}..{/key} if set; {^key}..{/key} if not set."""
    text = _render(tpl, [facts], html)
    text = re.sub(r'[ \t]+\n', '\n', text)
    return re.sub(r'\n{3,}', '\n\n', text).strip() + '\n'


def numbers(text):
    """Every number written in a text, as printed (e.g. '12,623', '0.5')."""
    return set(re.findall(r'\d(?:[\d,.]*\d)?', text))
