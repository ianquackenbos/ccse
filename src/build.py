"""Rebuild the two static pages from src/.  Run from the repo root:  python3 src/build.py"""
import json, os
R = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(R)
j = lambda x: json.dumps(x, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
# CCSE
c = os.path.join(R, 'ccse'); t = open(os.path.join(c, 'template.html')).read()
qs = json.load(open(os.path.join(c, 'qs.json')))
body = (t.replace('__EXPL__', open(os.path.join(c, 'expl.js')).read())
         .replace('__FACTS__', open(os.path.join(c, 'facts.js')).read())
         .replace('__DATA__', json.dumps([[q['id'], q['q'], q['opts'], q['a']] for q in qs], ensure_ascii=False, separators=(',', ':'))))
idx = os.path.join(ROOT, 'index.html'); old = open(idx).read()
head = old[:old.index('<body>\n') + len('<body>\n')]
open(idx, 'w').write(head + body + '\n</body>\n</html>\n')
# DELE A2
d = os.path.join(R, 'dele-a2'); t = open(os.path.join(d, 'template.html')).read()
rd = [json.load(open(os.path.join(d, f'R{n}.json'))) for n in range(1, 6)]
ls = [json.load(open(os.path.join(d, f'L{n}.json'))) for n in range(1, 6)]
os.makedirs(os.path.join(ROOT, 'dele-a2'), exist_ok=True)
open(os.path.join(ROOT, 'dele-a2', 'index.html'), 'w').write(t.replace('__READ__', j(rd)).replace('__LIST__', j(ls)))
print('built index.html and dele-a2/index.html')
