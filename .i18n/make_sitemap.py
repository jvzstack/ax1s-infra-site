#!/usr/bin/env python3
"""Rewrites sitemap.xml: every NL URL that has an /en/ mirror gets hreflang alternates, plus its EN twin."""
import os, re
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
D = 'https://ax1s-infra.com/'
EN_LASTMOD = '2026-10-31'
src = open(os.path.join(ROOT, 'sitemap.xml'), encoding='utf-8').read()
src = re.sub(r'\s*<xhtml:link[^>]*/>', '', src)
blocks = re.findall(r'<url>.*?</url>', src, re.S)
out = []
for b in blocks:
    loc = re.search(r'<loc>(.*?)</loc>', b).group(1)
    if loc.startswith(D + 'en/'):
        continue  # EN twins are regenerated below
    rel = loc[len(D):] or 'index.html'
    if not os.path.exists(os.path.join(ROOT, 'en', rel)):
        out.append(b)
        continue
    en = D + 'en/' + ('' if rel == 'index.html' else rel)
    alts = ('\n    <xhtml:link rel="alternate" hreflang="nl" href="%s"/>'
            '\n    <xhtml:link rel="alternate" hreflang="en" href="%s"/>'
            '\n    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>') % (loc, en, loc)
    nl_b = b.replace('\n  </url>', alts + '\n  </url>')
    en_b = re.sub(r'<lastmod>.*?</lastmod>', '<lastmod>' + EN_LASTMOD + '</lastmod>', nl_b.replace('<loc>%s</loc>' % loc, '<loc>%s</loc>' % en))
    out += [nl_b, en_b]
head = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write(head + '  ' + '\n  '.join(out) + '\n</urlset>\n')
print(len(blocks), 'NL urls ->', len(out), 'urls')
