#!/usr/bin/env python3
"""
tex2ipynb.py  —  v2.1
Convierte prácticas del manual de química computacional (LaTeX)
a notebooks Jupyter con MyST Markdown para Jupyter Book.

CONVENCIÓN ORCA/G16 en el .tex:
  \\begin{orcablock}..\\end{orcablock}
  \\begin{g16block}..\\end{g16block}
→ genera tab-set MyST sincronizado

Uso:
  python tex2ipynb.py P01.tex -o p01.ipynb
  python tex2ipynb.py --all tex/ notebooks/
"""
import re, json, sys
from pathlib import Path

# ── LIMPIEZA LATEX → MARKDOWN ─────────────────────────────────
def limpiar(t):
    store = {}
    def save(m):
        k = f'__M{len(store):04d}__'; store[k] = m.group(0); return k
    t = re.sub(r'\$\$.*?\$\$', save, t, flags=re.DOTALL)
    t = re.sub(r'\$[^$\n]+?\$', save, t)
    t = re.sub(r'\\textbf\{([^}]+)\}', r'**\1**', t)
    t = re.sub(r'\\text(?:it|em)\{([^}]+)\}', r'*\1*', t)
    t = re.sub(r'\\emph\{([^}]+)\}', r'*\1*', t)
    t = re.sub(r'\\text(?:tt|sc)\{([^}]+)\}', r'`\1`', t)
    t = re.sub(r'\\path\{([^}]+)\}', r'`\1`', t)
    t = re.sub(r'\\doi\{([^}]+)\}', r'[DOI:\1](https://doi.org/\1)', t)
    t = re.sub(r'\\url\{([^}]+)\}', r'[\1](\1)', t)
    t = re.sub(r'\\href\{([^}]+)\}\{([^}]+)\}', r'[\2](\1)', t)
    t = re.sub(r'\\cite\{([^}]+)\}', r'^[\1]^', t)
    t = re.sub(r'\\(?:ref|label)\{[^}]+\}', '', t)
    t = t.replace("``", '"').replace("''", '"').replace("`", "'")
    t = re.sub(r'---', '—', t); t = re.sub(r'--', '–', t)
    t = re.sub(r'\\ldots\b', '…', t)
    acentos = {'a':'á','e':'é','i':'í','o':'ó','u':'ú',
               'A':'Á','E':'É','I':'Í','O':'Ó','U':'Ú','n':'ñ','N':'Ñ'}
    for b, a in acentos.items():
        t = t.replace(f"\\'{{{b}}}", a).replace(f"\\~{{{b}}}", a)
    t = re.sub(r'\\\\', '\n', t)
    t = re.sub(r'\\(?:vspace|hspace|medskip|bigskip|smallskip|noindent|par)\b\{?[^}]*\}?', '', t)
    t = re.sub(r'\\ ', ' ', t)
    t = re.sub(r'\\(?:begin|end)\{(?:center|quote|flushleft|flushright|minipage)\}\{?[^}]*\}?', '', t)
    t = re.sub(r'\\(?:itshape|small|large|Large)\b', '', t)
    t = re.sub(r'\\[a-zA-Z]+\*?\b', '', t)
    t = re.sub(r'\{([^{}]*)\}', r'\1', t)
    t = re.sub(r'  +', ' ', t)
    for k, v in store.items(): t = t.replace(k, v)
    return t.strip()

def math_display(t):
    t = re.sub(r'\\\[(.+?)\\\]', r'\n$$\1$$\n', t, flags=re.DOTALL)
    for env in ('equation','equation*','align','align*','gather','gather*'):
        t = re.sub(rf'\\begin\{{{env}\}}(.+?)\\end\{{{env}\}}',
                   r'\n$$\1$$\n', t, flags=re.DOTALL)
    return t

# ── ENTORNOS ESPECIALES ────────────────────────────────────────
CALLOUTS = {
    'advertencia': ('warning', '⚠️ Advertencia'),
    'notameto':    ('note',    '📝 Nota metodológica'),
}

def callout(tipo, contenido):
    cls, titulo = CALLOUTS.get(tipo, ('note','📝'))
    return (f'```{{admonition}} {titulo}\n:class: {cls}\n\n'
            f'{limpiar(contenido).strip()}\n```')

def meta_tabla(contenido):
    filas = re.findall(r'\\metaitem\{([^}]+)\}\{([^}]+)\}', contenido)
    if not filas: return ''
    rows = ['| Parámetro | Valor |', '|:--|:--|']
    for k,v in filas: rows.append(f'| **{limpiar(k)}** | {limpiar(v)} |')
    return '\n'.join(rows)

def lista(contenido, num=False):
    items = re.split(r'\\item\b', contenido)[1:]
    out = []
    for i, item in enumerate(items, 1):
        item = re.sub(r'^\[([^\]]+)\]\s*', r'**\1** ', item.strip())
        c = limpiar(item).strip().replace('\n', ' ')
        if c: out.append(f'{i}. {c}' if num else f'- {c}')
    return '\n'.join(out)

def tabla(contenido):
    out, done = [], False
    for fila in re.split(r'\\\\', contenido):
        fila = fila.strip()
        if not fila: continue
        if re.match(r'\\(?:toprule|midrule|bottomrule|hline)', fila):
            if out and not done:
                out.append('|' + ':--|' * max(out[-1].count('|')-1, 1))
                done = True
            continue
        celdas = [limpiar(c.strip()) for c in re.split(r'(?<!\\)&', fila)]
        out.append('| ' + ' | '.join(celdas) + ' |')
        if not done and len(out) == 1:
            out.append('|' + ':--|' * len(celdas)); done = True
    return '\n'.join(out)

def biblio(contenido):
    refs = re.findall(r'\\bibitem\{([^}]+)\}(.*?)(?=\\bibitem|\Z)', contenido, re.DOTALL)
    if not refs: return ''
    return '## 📚 Referencias\n\n' + '\n'.join(
        f'- **[{k}]** {limpiar(v.strip())}' for k,v in refs)

# ── PESTAÑAS ORCA / G16 ────────────────────────────────────────
def tab_set(orca, g16):
    def bloque(code): return f'```{{code-block}} text\n{code.strip()}\n```'
    p = ['````{tab-set}\n']
    if orca.strip():
        p += ['```{tab-item} ORCA 5\n:sync: orca\n\n', bloque(orca), '\n```\n\n']
    if g16.strip():
        p += ['```{tab-item} Gaussian 16\n:sync: g16\n\n', bloque(g16), '\n```\n']
    p.append('````')
    return ''.join(p)

def detectar_lang(code):
    s = code.strip()
    if re.search(r'^\s*(?:xtb|gmx |g16 |sbatch|conda |pip |grep |#!/)', s, re.M): return 'bash'
    return 'python'

# ── PARSER ─────────────────────────────────────────────────────
ENTORNOS = ['verbatim','advertencia','notameto',
            'practicameta','enumerate','itemize',
            'tabular','thebibliography','orcablock','g16block']

# Pre-compilar todo para evitar bugs con re.escape + \e en Python 3.12
RE_BEGIN = re.compile(
    r'\\begin\{(' + '|'.join(re.escape(e) for e in ENTORNOS)
    + r')(?:\*)?\}(?:\[[^\]]*\])?(?:\{[^}]*\})?', re.DOTALL)
RE_SEC   = re.compile(
    r'\\(chapter|section|subsection|subsubsection)\*?\{([^}]+(?:\{[^}]*\}[^}]*)*)\}')
RE_FIN   = {n: re.compile(r'\\end\{' + n.replace('*',r'\*') + r'(?:\*)?\}')
            for n in ENTORNOS}
NIVEL    = {'chapter':'##','section':'##','subsection':'###','subsubsection':'####'}

def tokenizar(texto):
    toks = []
    for m in RE_SEC.finditer(texto):
        toks.append(('sec', m.start(), m.group(1), m.group(2), m.end()))
    for m in RE_BEGIN.finditer(texto):
        nombre = m.group(1).rstrip('*')
        pat = RE_FIN.get(nombre)
        if pat is None: continue
        fin = pat.search(texto, m.end())
        if fin:
            toks.append(('env', m.start(), nombre, texto[m.end():fin.start()], fin.end()))
    toks.sort(key=lambda t: t[1])
    return toks

def tex_a_celdas(texto_latex):
    texto = re.sub(r'%.*?\n', '\n', texto_latex)
    texto = math_display(texto)
    celdas, pending_orca, ultimo_fin = [], None, 0

    def flush():
        nonlocal pending_orca
        if pending_orca is not None:
            add_md(tab_set(pending_orca, '')); pending_orca = None
    def add_md(s):
        s = s.strip()
        if len(s) > 2: celdas.append({'type':'markdown','source':s})
    def add_code(s, lang='python'):
        s = s.strip()
        if s: celdas.append({'type':'code','source':s,'lang':lang})

    for tok in tokenizar(texto):
        libre = limpiar(math_display(texto[ultimo_fin:tok[1]])).strip()
        if libre: flush(); add_md(libre)

        if tok[0] == 'sec':
            flush(); add_md(f'{NIVEL[tok[2]]} {limpiar(tok[3])}')
            ultimo_fin = tok[4]
        elif tok[0] == 'env':
            nombre, cont, pos_fin = tok[2], tok[3], tok[4]
            if nombre == 'orcablock':
                flush(); pending_orca = cont; ultimo_fin = pos_fin; continue
            if nombre == 'g16block':
                add_md(tab_set(pending_orca or '', cont)); pending_orca = None
                ultimo_fin = pos_fin; continue
            flush()
            if nombre == 'verbatim':
                lang = detectar_lang(cont)
                if lang == 'bash': add_code('%%bash\n' + cont, 'bash')
                else: add_code(cont, 'python')
            elif nombre in CALLOUTS: add_md(callout(nombre, cont))
            elif nombre == 'practicameta':
                t = meta_tabla(cont)
                if t: add_md('### 📋 Información de la práctica\n\n' + t)
            elif nombre == 'enumerate': add_md(lista(cont, num=True))
            elif nombre == 'itemize':   add_md(lista(cont))
            elif nombre in ('tabular','tabular*'):
                t = tabla(cont)
                if t.strip(): add_md(t)
            elif nombre == 'thebibliography':
                b = biblio(cont)
                if b: add_md(b)
            ultimo_fin = pos_fin

    flush()
    resto = limpiar(texto[ultimo_fin:]).strip()
    if resto: add_md(resto)
    return celdas

# ── CONSTRUCCIÓN IPYNB ─────────────────────────────────────────
SETUP = '''\
# ── Configuración ─────────────────────────────────────────────
# Google Colab: descomenta la siguiente línea
# !pip install rdkit-pypi xtb-python umap-learn -q

import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import matplotlib; matplotlib.rcParams["figure.dpi"] = 120
print("Entorno listo ✓  —  Manual QC UNAM")
'''

def meta(texto):
    m1 = re.search(r'\\practica\{([^}]+(?:\{[^}]*\}[^}]*)*)\}', texto)
    m2 = re.search(r'PRÁCTICA\s+(\d+)', texto)
    m3 = re.search(r'(Bloque\s+\d+[^\n]*)', texto)
    titulo = limpiar(m1.group(1).replace('\n',' ')) if m1 else 'Práctica'
    num    = int(m2.group(1)) if m2 else 0
    bloque = m3.group(1).strip() if m3 else ''
    return titulo, num, bloque

def construir(celdas, titulo, num, bloque):
    def md(src):
        return {'cell_type':'markdown','id':f'md{abs(hash(src[:20])):09x}',
                'metadata':{},'source':src}
    def code(src, lang='python'):
        return {'cell_type':'code','execution_count':None,
                'id':f'co{abs(hash(src[:20])):09x}',
                'metadata':{'tags':['bash'] if lang=='bash' else []},
                'outputs':[],'source':src}
    badge = (f'[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)]'
             f'(https://colab.research.google.com/github/qcmanual/'
             f'del-orbital-al-espacio-quimico/blob/main/notebooks/p{num:02d}.ipynb)')
    header = f'# Práctica {num}: {titulo}\n\n> **{bloque}** · Manual de QC · UNAM\n\n{badge}'
    cells  = [md(header), code(SETUP)]
    for c in celdas:
        cells.append(md(c['source']) if c['type']=='markdown'
                     else code(c['source'], c.get('lang','python')))
    return {
        'nbformat':4,'nbformat_minor':5,
        'metadata':{'kernelspec':{'display_name':'Python 3 (qcmanual)',
                                   'language':'python','name':'python3'},
                    'language_info':{'name':'python','version':'3.11.0'},
                    'title':titulo,'practica':num,
                    'authors':[{'name':'Eduardo Gabriel Guzmán-López'},
                                {'name':'Miguel Reina'}]},
        'cells':cells}

# ── API ────────────────────────────────────────────────────────
def convertir(ruta_tex, ruta_ipynb=None, verbose=True):
    ruta_tex = Path(ruta_tex)
    if not ruta_ipynb:
        stem = ruta_tex.stem.lower().replace('practica-','p')
        ruta_ipynb = ruta_tex.parent / f'{stem}.ipynb'
    ruta_ipynb = Path(ruta_ipynb)
    ruta_ipynb.parent.mkdir(parents=True, exist_ok=True)
    texto = ruta_tex.read_text(encoding='utf-8')
    titulo, num, bloque = meta(texto)
    celdas = tex_a_celdas(texto)
    nb = construir(celdas, titulo, num, bloque)
    with open(ruta_ipynb, 'w', encoding='utf-8') as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    if verbose:
        nc = sum(1 for c in celdas if c['type']=='code')
        nm = sum(1 for c in celdas if c['type']=='markdown')
        print(f'✓ P{num:02d} | {nc} código · {nm} markdown → {ruta_ipynb}')
    return ruta_ipynb

def convertir_todos(dir_tex='.', dir_out='notebooks'):
    archivos = sorted(Path(dir_tex).glob('practica-*.tex'))
    if not archivos: archivos = sorted(Path(dir_tex).glob('P*.tex'))
    print(f'Convirtiendo {len(archivos)} archivos...\n')
    for tex in archivos:
        num = re.search(r'\d+', tex.stem)
        out = Path(dir_out) / f'p{int(num.group()):02d}.ipynb'
        try: convertir(tex, out)
        except Exception as e: print(f'✗ {tex.name}: {e}')

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args: print(__doc__); sys.exit(0)
    if args[0] == '--all':
        convertir_todos(args[1] if len(args)>1 else '.', args[2] if len(args)>2 else 'notebooks')
    else:
        salida = args[args.index('-o')+1] if '-o' in args else None
        convertir(args[0], salida)
