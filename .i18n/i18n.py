#!/usr/bin/env python3
"""
AX1S Infra i18n tooling (NL source -> EN mirror under /en/).

Usage (from the repo root, with beautifulsoup4 installed):
  python .i18n/i18n.py extract   # list untranslated text units -> .i18n/missing.json
  python .i18n/i18n.py build     # (re)generate en/ + patch NL pages with the language switch

Source of truth is the Dutch site in the repo root. Translations live in
.i18n/tr/*.json (flat {dutch: english}) and .i18n/js_replacements.json
(per-file exact substring replacements for strings that live inside <script>).
This folder starts with a dot, so the deploy workflow (`for item in *`) skips it.
"""
import copy, glob, html, json, os, re, sys
from bs4 import BeautifulSoup, NavigableString, Comment, Tag
from bs4.element import Doctype, Declaration, ProcessingInstruction, CData

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TR_DIR = os.path.join(ROOT, '.i18n', 'tr')
DOMAIN = 'https://ax1s-infra.com/'
SKIP_FILES = {'kennismaking.html'}          # noindex LinkedIn landing page, Dutch only
SKIP_TAGS = {'script', 'style', 'noscript', 'svg'}
INLINE = {'a', 'strong', 'b', 'em', 'i', 'span', 'br', 'iconify-icon', 'code', 'sup', 'sub',
          'small', 'u', 'mark', 'abbr', 'img'}
VOID = {'br', 'img', 'input', 'hr', 'meta', 'link'}
ATTRS = ('alt', 'placeholder', 'title', 'aria-label')
META_KEYS = {'description', 'og:title', 'og:description', 'twitter:title', 'twitter:description'}
LD_KEYS = {'name', 'headline', 'description', 'text', 'articleSection', 'alternateName'}
LETTER = re.compile(r'[A-Za-zÀ-ÿ]')
META_CLASSES = ('article-meta', 'blog-card-meta')

MONTHS = {'jan': 'Jan', 'feb': 'Feb', 'mrt': 'Mar', 'apr': 'Apr', 'mei': 'May', 'jun': 'Jun',
          'jul': 'Jul', 'aug': 'Aug', 'sep': 'Sep', 'okt': 'Oct', 'nov': 'Nov', 'dec': 'Dec'}


def source_files():
    files = sorted(glob.glob(os.path.join(ROOT, '*.html'))) + sorted(glob.glob(os.path.join(ROOT, 'blog', '*.html')))
    return [os.path.relpath(f, ROOT) for f in files if os.path.basename(f) not in SKIP_FILES]


def load_translations():
    tr = {}
    for f in sorted(glob.glob(os.path.join(TR_DIR, '*.json'))):  # *.json only
        with open(f, encoding='utf-8') as fh:
            data = json.load(fh)
        for k, v in data.items():
            tr[k] = v
    idf = os.path.join(TR_DIR, '_identity.txt')
    if os.path.exists(idf):
        for line in open(idf, encoding='utf-8'):
            line = line.rstrip('\n')
            if line and not line.startswith('#'):
                tr.setdefault(line, line)
    return tr


def norm(s):
    return re.sub(r'\s+', ' ', s).strip()


# ---------------------------------------------------------------- units
def open_html(tag):
    attrs = ''
    for k, v in tag.attrs.items():
        if isinstance(v, list):
            v = ' '.join(v)
        attrs += ' %s="%s"' % (k, html.escape(str(v), quote=True))
    return '<%s%s>' % (tag.name, attrs)


def tokenize(nodes):
    """nodes -> (key string with {n}/{/n} tokens, tokens list of (open_html, close_html|None))."""
    tokens = []

    def rec(ns):
        out = ''
        for n in ns:
            if isinstance(n, (Comment, Doctype, Declaration, ProcessingInstruction, CData)):
                continue
            if isinstance(n, NavigableString):
                t = str(n)
                if '{' in t or '}' in t:
                    raise ValueError('curly brace in text: %r' % t)
                out += t
            elif isinstance(n, Tag):
                idx = len(tokens) + 1
                if n.name in VOID or (n.name == 'iconify-icon' and not n.contents):
                    tokens.append((open_html(n) if n.name in VOID else open_html(n) + '</%s>' % n.name, None))
                    out += '{%d}' % idx
                else:
                    tokens.append((open_html(n), '</%s>' % n.name))
                    out += '{%d}' % idx + rec(list(n.children)) + '{/%d}' % idx
        return out

    return norm(rec(nodes)), tokens


def untokenize(text, tokens):
    """translated text with tokens -> html string."""
    parts = re.split(r'(\{/?\d+\})', text)
    out = ''
    used = set()
    for p in parts:
        m = re.fullmatch(r'\{(/?)(\d+)\}', p)
        if not m:
            out += html.escape(p, quote=False)
            continue
        i = int(m.group(2)) - 1
        if i >= len(tokens):
            raise ValueError('bad token %s in %r' % (p, text))
        op, cl = tokens[i]
        used.add((m.group(1) == '/', i))
        if m.group(1) == '/':
            if cl is None:
                raise ValueError('closing token for void %s' % p)
            out += cl
        else:
            out += op
    return out, used


def collect_units(container, units):
    """find translatable runs under container; append (nodes_list) to units."""
    if isinstance(container, Tag) and (container.name in SKIP_TAGS):
        return
    if isinstance(container, Tag):
        cls = container.get('class') or []
        if any(c in META_CLASSES for c in cls):
            return
    kids = list(container.children)
    run = []

    def flush():
        nonlocal run
        if run:
            key, _ = tokenize(run)
            if LETTER.search(re.sub(r'\{/?\d+\}', '', key)):
                units.append(list(run))
        run = []

    for c in kids:
        if isinstance(c, (Comment, Doctype, Declaration, ProcessingInstruction, CData)):
            continue
        if isinstance(c, NavigableString):
            run.append(c)
        elif isinstance(c, Tag):
            if c.name in SKIP_TAGS:
                flush()
            elif c.name in INLINE and not _has_block_desc(c):
                run.append(c)
            else:
                flush()
                collect_units(c, units)
    flush()


def _has_block_desc(tag):
    for d in tag.descendants:
        if isinstance(d, Tag) and d.name not in INLINE:
            return True
    return False


def attr_units(soup):
    out = []
    for t in soup.find_all(True):
        if t.name in ('script', 'style'):
            continue
        for a in ATTRS:
            v = t.get(a)
            if isinstance(v, str) and LETTER.search(v):
                out.append((t, a, norm(v)))
        if t.name == 'meta':
            k = t.get('name') or t.get('property')
            if k in META_KEYS and t.get('content'):
                out.append((t, 'content', norm(t['content'])))
    return out


def ld_strings(obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in LD_KEYS and isinstance(v, str):
                out.add(v)
            elif k == 'knowsAbout' and isinstance(v, list):
                for s in v:
                    if isinstance(s, str):
                        out.add(s)
            else:
                ld_strings(v, out)
    elif isinstance(obj, list):
        for v in obj:
            ld_strings(v, out)


def parse(path):
    """parse a Dutch source page; strip i18n scaffolding so runs are idempotent."""
    with open(os.path.join(ROOT, path), encoding='utf-8') as fh:
        soup = BeautifulSoup(fh.read(), 'html.parser')
    for t in soup.find_all('a', class_='lang-switch'):
        t.decompose()
    for t in soup.find_all('link', rel='alternate'):
        if t.get('hreflang'):
            t.decompose()
    for t in soup.find_all('link', rel='stylesheet'):
        if 'lang-switch.css' in (t.get('href') or ''):
            t.decompose()
    return soup


def ld_scripts(soup):
    return [s for s in soup.find_all('script', type='application/ld+json')]


# ---------------------------------------------------------------- extract
def cmd_extract():
    tr = load_translations()
    missing = {}
    for f in source_files():
        soup = parse(f)
        units = []
        collect_units(soup, units)
        for u in units:
            key, _ = tokenize(u)
            if key not in tr:
                missing.setdefault(key, []).append(f)
        for t, a, v in attr_units(soup):
            if v not in tr:
                missing.setdefault(v, []).append(f)
        for s in ld_scripts(soup):
            strs = set()
            ld_strings(json.loads(s.string), strs)
            for v in strs:
                if norm(v) not in tr:
                    missing.setdefault(norm(v), []).append(f)
    out = {k: sorted(set(v)) for k, v in missing.items()}
    with open(os.path.join(ROOT, '.i18n', 'missing.json'), 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print('%d untranslated units (see .i18n/missing.json)' % len(out))


# ---------------------------------------------------------------- build
def page_urls(rel):
    """rel: 'foo.html' | 'blog/x.html' -> (nl_abs, en_abs)"""
    if rel == 'index.html':
        return DOMAIN, DOMAIN + 'en/'
    return DOMAIN + rel, DOMAIN + 'en/' + rel


def switch_hrefs(rel):
    """relative href for toggle: from NL page -> en, from EN page -> nl"""
    depth = rel.count('/')
    up = '../' * depth
    if rel == 'index.html':
        return 'en/', '../'
    return up + 'en/' + rel, '../' * (depth + 1) + rel


def date_en(s):
    def m(mo):
        return '%s %s %s' % (mo.group(1), MONTHS[mo.group(2).lower()], mo.group(3))
    s = re.sub(r'(\d{1,2}) (jan|feb|mrt|apr|mei|jun|jul|aug|sep|okt|nov|dec) (\d{4})', m, s, flags=re.I)
    s = re.sub(r'(\d+) min leestijd', r'\1 min read', s)
    s = s.replace('Direct te gebruiken, geen verplichting. Sommige tools vragen om een e-mailadres om je resultaat te sturen, downloads en de calculator niet.',
                  'Ready to use, no obligation. Some tools ask for an email address to send you your result; downloads and the calculators do not.')
    return s


def rewrite_ld_url(u):
    if not u.startswith(DOMAIN):
        return u
    rest = u[len(DOMAIN):]
    if rest.startswith('assets/'):
        return u
    if re.match(r'#(organization|website|service-[a-z]+)$', rest):
        return u
    rest = re.sub(r'^index\.html', '', rest)
    return DOMAIN + 'en/' + rest


def translate_ld(obj, tr, in_id_obj=False, missing=None):
    if isinstance(obj, dict):
        idv = obj.get('@id')
        id_obj = isinstance(idv, str) and re.search(r'#(organization|website|service-[a-z]+)$', idv) is not None
        new = {}
        for k, v in obj.items():
            if k in LD_KEYS and isinstance(v, str):
                n = norm(v)
                if n in tr:
                    new[k] = tr[n]
                else:
                    if missing is not None:
                        missing.add(n)
                    new[k] = v
            elif k == 'knowsAbout' and isinstance(v, list):
                new[k] = [tr.get(norm(s), s) if isinstance(s, str) else s for s in v]
            elif k == 'inLanguage':
                new[k] = 'en'
            elif k in ('url', 'item', '@id') and isinstance(v, str) and not id_obj and not in_id_obj:
                new[k] = rewrite_ld_url(v)
            else:
                new[k] = translate_ld(v, tr, in_id_obj or id_obj, missing)
        return new
    if isinstance(obj, list):
        return [translate_ld(v, tr, in_id_obj, missing) for v in obj]
    return obj


def make_switch(label, href, lang, aria):
    return ('<a href="%s" class="lang-switch" lang="%s" hreflang="%s" aria-label="%s" title="%s">'
            '<iconify-icon icon="solar:global-linear" width="14"></iconify-icon><span>%s</span></a>'
            % (href, lang, lang, aria, aria, label))


def hreflang_block(rel):
    nl, en = page_urls(rel)
    return ('<link rel="alternate" hreflang="nl" href="%s">\n<link rel="alternate" hreflang="en" href="%s">\n'
            '<link rel="alternate" hreflang="x-default" href="%s">' % (nl, en, en))


def build_en(rel, tr, js_repl, missing_all):
    soup = parse(rel)
    depth = rel.count('/')
    # 1. text units
    units = []
    collect_units(soup, units)
    for u in units:
        key, tokens = tokenize(u)
        if key not in tr:
            missing_all.setdefault(key, set()).add(rel)
            continue
        new_html, used = untokenize(tr[key], tokens)
        # sanity: every token used exactly as in source
        need = set()
        for i, (op, cl) in enumerate(tokens):
            need.add((False, i))
            if cl is not None:
                need.add((True, i))
        if used != need:
            raise ValueError('%s: token mismatch for %r -> %r' % (rel, key, tr[key]))
        frag = BeautifulSoup(new_html, 'html.parser')
        new_nodes = list(frag.contents)
        anchor = u[0]
        for n in new_nodes:
            anchor.insert_before(n)
        for n in u:
            n.extract()
    # 2. attribute units
    for t, a, v in attr_units(soup):
        if v in tr:
            t[a] = tr[v]
        else:
            missing_all.setdefault(v, set()).add(rel)
    # 3. dates / reading time in meta rows
    for el in soup.find_all(lambda t: isinstance(t, Tag) and any(c in META_CLASSES for c in (t.get('class') or []))):
        for s_ in list(el.find_all(string=True)):
            if not isinstance(s_, (Comment, Doctype, Declaration, ProcessingInstruction, CData)):
                s_.replace_with(date_en(str(s_)))
    # 4. JSON-LD
    for s in ld_scripts(soup):
        data = json.loads(s.string)
        ms = set()
        out = translate_ld(data, tr, False, ms)
        for m_ in ms:
            missing_all.setdefault(m_, set()).add(rel)
        s.string = json.dumps(out, ensure_ascii=False, indent=2)
    # 5. head: lang, canonical, og, hreflang, css
    soup.html['lang'] = 'en'
    nl_abs, en_abs = page_urls(rel)
    for t in soup.find_all('link', rel='canonical'):
        t['href'] = en_abs
        t.insert_after(BeautifulSoup('\n' + hreflang_block(rel), 'html.parser'))
    for t in soup.find_all('meta'):
        if t.get('property') == 'og:url':
            t['content'] = en_abs
        if t.get('property') == 'og:locale':
            t['content'] = 'en_GB'
    css = soup.new_tag('link', rel='stylesheet', href=('../' * depth) + 'assets/lang-switch.css')
    soup.head.append(css)
    # 6. language switch in nav
    _, nl_href = switch_hrefs(rel)
    sw = BeautifulSoup(make_switch('NL', nl_href, 'nl', 'Nederlandse versie'), 'html.parser')
    add_switch(soup, sw)
    # 7. paths: assets one level deeper
    for t in soup.find_all(True):
        for a in ('href', 'src'):
            v = t.get(a)
            if isinstance(v, str) and (v.startswith('assets/') or v.startswith('../assets/')):
                t[a] = '../' + v
    out_html = str(soup)
    # 8. JS string replacements (exact substring, per file)
    for pair in js_repl.get(rel, []):
        nl, en = pair
        if nl not in out_html:
            print('NOTE %s: js replacement not applied (already translated?): %r' % (rel, nl[:70]))
            continue
        out_html = out_html.replace(nl, en)
    dest = os.path.join(ROOT, 'en', rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'w', encoding='utf-8') as fh:
        fh.write(out_html)


def add_switch(soup, sw):
    cta = soup.find('a', class_='nav-cta')
    if cta is None:
        return
    group = cta.find_parent(class_='nav-cta-group')
    if group is None:
        group = soup.new_tag('div')
        group['class'] = ['nav-cta-group']
        cta.insert_before(group)
        group.append(cta.extract())
    group.append(sw)


def patch_nl(rel):
    path = os.path.join(ROOT, rel)
    with open(path, encoding='utf-8') as fh:
        s = fh.read()
    if 'class="lang-switch"' in s:
        return False
    depth = rel.count('/')
    en_href, _ = switch_hrefs(rel)
    # hreflang after canonical
    s, n = re.subn(r'(<link rel="canonical" href="[^"]*">)', lambda m: m.group(1) + '\n' + hreflang_block(rel), s, count=1)
    if n != 1:
        raise ValueError('no canonical in ' + rel)
    # stylesheet before </head>
    s = s.replace('</head>', '<link rel="stylesheet" href="%sassets/lang-switch.css">\n</head>' % ('../' * depth), 1)
    sw = make_switch('EN', en_href, 'en', 'English version')
    m = re.search(r'<a [^>]*class="nav-cta"[^>]*>.*?</a>', s, re.S)
    if not m:
        raise ValueError('no nav-cta in ' + rel)
    before = s[:m.start()]
    grouped = before.rfind('class="nav-cta-group"') > before.rfind('<nav')
    if grouped:
        s = s[:m.end()] + '\n      ' + sw + s[m.end():]
    else:
        s = s[:m.start()] + '<div class="nav-cta-group">\n      ' + m.group(0) + '\n      ' + sw + '\n    </div>' + s[m.end():]
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(s)
    return True


def cmd_build():
    tr = load_translations()
    jsr_path = os.path.join(ROOT, '.i18n', 'js_replacements.json')
    js_repl = json.load(open(jsr_path, encoding='utf-8')) if os.path.exists(jsr_path) else {}
    missing_all = {}
    for rel in source_files():
        build_en(rel, tr, js_repl, missing_all)
    if missing_all:
        with open(os.path.join(ROOT, '.i18n', 'missing.json'), 'w', encoding='utf-8') as fh:
            json.dump({k: sorted(v) for k, v in missing_all.items()}, fh, ensure_ascii=False, indent=1)
        print('WARNING: %d untranslated units remain (kept Dutch) -> .i18n/missing.json' % len(missing_all))
    else:
        print('en/ built, all units translated')
    patched = [rel for rel in source_files() if patch_nl(rel)]
    print('NL pages patched with language switch: %d' % len(patched))


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    {'extract': cmd_extract, 'build': cmd_build}.get(cmd, lambda: print(__doc__))()
