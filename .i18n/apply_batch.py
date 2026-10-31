#!/usr/bin/env python3
"""apply_batch.py <batch.json>  : batch = {"pairs":[[idx,"english"],...], "same":[idx,...]} indexed on snapshot.json"""
import json, os, re, sys
here = os.path.dirname(os.path.abspath(__file__))
snap = json.load(open(os.path.join(here, 'snapshot.json'), encoding='utf-8'))
b = json.load(open(sys.argv[1], encoding='utf-8'))
out = {}
tok = lambda s: sorted(re.findall(r'\{/?\d+\}', s))
for i, en in b.get('pairs', []):
    k = snap[i]['k']
    if tok(k) != tok(en):
        print('TOKEN MISMATCH', i, k, '->', en); sys.exit(1)
    out[k] = en
for i in b.get('same', []):
    out[snap[i]['k']] = snap[i]['k']
name = os.path.splitext(os.path.basename(sys.argv[1]))[0]
json.dump(out, open(os.path.join(here, 'tr', name + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(name, len(out), 'translations written')
