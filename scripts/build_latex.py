"""Render the manuscript blocks as a LaTeX article (authors: N. Kumbasar, M. O. Güneren) and compile it."""
import json, re, subprocess, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'TESLIM_2026-10-18/latex'
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'figures').mkdir(exist_ok=True)
blocks = json.loads((ROOT / 'paper/manuscript_content_authored.json').read_text())
refs = json.loads((ROOT / 'paper/references.json').read_text())


def dehyphen(t):
    t = re.sub(r'(?<![\w.])-(?=\d)', '\u2212', t)
    t = re.sub(r'(?<=\d)-(?=\d)', ' to ', t)
    return t.replace('-', ' ')


def esc(s):
    urls = []
    def keep(m):
        u = m.group(0); dot = u.endswith('.'); u = u.rstrip('.')
        urls.append(u); return f'@@URL{len(urls)-1}@@' + ('.' if dot else '')
    s = re.sub(r'https?://\S+', keep, s)
    maths = []
    def math(m):
        maths.append(m); return f'@@MATH{len(maths)-1}@@'
    for a, b in [('Σ_k (R_k − R_(k−1)) P_k', r'$\sum_k (R_k - R_{k-1})\, P_k$'), ('(1/N) Σ_i (p_i − y_i)²', r'$(1/N)\sum_i (p_i - y_i)^2$'), ('N_train', r'$N_{\mathrm{train}}$'), ('N_labeled', r'$N_{\mathrm{labeled}}$')]:
        if a in s: s = s.replace(a, math(b))
    s = s.replace('\\', r'\textbackslash{}')
    for a, b in [('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'), ('_', r'\_'), ('{', r'\{'), ('}', r'\}'), ('~', r'\textasciitilde{}'), ('^', r'\textasciicircum{}')]:
        s = s.replace(a, b)
    s = s.replace('×', r'$\times$').replace('−', r'$-$').replace('–', '--').replace('—', '---').replace('≥', r'$\geq$').replace('≤', r'$\leq$').replace('±', r'$\pm$').replace('•', r'\textbullet{}')
    s = re.sub(r'\[(\d+(?:,\s*\d+)*)\]', lambda m: r'\cite{' + ','.join('ref' + x.strip() for x in m.group(1).split(',')) + '}', s)
    for i, u in enumerate(urls):
        s = s.replace(f'@@URL{i}@@', r'\url{' + u + '}')
    for i, m in enumerate(maths):
        s = s.replace(f'@@MATH{i}@@', m)
    return s


def latex_table(b):
    n = len(b['headers'])
    col = 'l' + 'r' * (n - 1) if n > 2 else 'lr'
    if b['caption'].startswith('Table 2'): col = 'lrrr'
    if b['caption'].startswith(('Table 3', 'Table 4')): col = 'l' * 2 + 'r' * (n - 2) if n > 3 else col
    rows = [' & '.join(esc(c) for c in b['headers']) + r' \\ \midrule'] + [' & '.join(esc(c) for c in r) + r' \\' for r in b['rows']]
    cap = esc(b['caption'])
    small = r'\small' if n >= 6 else ''
    if b['caption'].startswith('Table 8'): col = 'p{2.4cm}p{3.2cm}p{3.0cm}p{3.0cm}p{3.6cm}'; small = r'\footnotesize'
    if b['caption'].startswith('Table 7'): col = 'p{5.6cm}p{4.2cm}p{2.8cm}p{2.0cm}'; small = r'\small'
    return '\n'.join([r'\begin{table}[htbp]', r'\centering', small, r'\caption{' + cap + '}', r'\begin{tabular}{' + col + '}', r'\toprule', *rows, r'\bottomrule', r'\end{tabular}', r'\end{table}', ''])


body = []
abstract = []
in_abstract = False
title = ''
figs = []
for b in blocks:
    k = b['kind']
    if k == 'title': title = esc(b['text']); continue
    if k == 'heading':
        in_abstract = (b['text'] == 'Abstract')
        if in_abstract: continue
        if b['text'] == 'References': continue
        text = re.sub(r'^\d+(\.\d+)?\s+', '', b['text'])
        level = 'subsection' if re.match(r'^\d+\.\d+', b['text']) else 'section'
        star = '*' if b['text'] in ['Data and code availability', 'Author contributions and assistance disclosure'] else ''
        body.append(f'\\{level}{star}{{{esc(text)}}}')
        continue
    if k == 'paragraph':
        t = b['text']
        if t.startswith('Mehmet Oğuz Güneren¹') or t.startswith('¹ ') or t.startswith('² ') or t.startswith(('Draft for co-author','Draft for coauthor','Anonymous research manuscript')) or t.startswith('Keywords:') or re.match(r'^\[\d+\]', t):
            if t.startswith('Keywords:'): keywords = esc(t.replace('Keywords: ', ''))
            continue
        (abstract if in_abstract else body).append(esc(t) + '\n')
        continue
    if k == 'table': body.append(latex_table(b)); continue
    if k == 'figure':
        name = Path(b['path']).name
        shutil.copy(ROOT / b['path'], OUT / 'figures' / name)
        m = re.match(r'(Figure \d+)\. (.*)', b['caption'])
        figs.append('\n'.join([r'\begin{figure}[htbp]', r'\centering', r'\includegraphics[width=\linewidth]{figures/' + name + '}', r'\caption{' + esc(m.group(2)) + '}', r'\label{' + m.group(1).replace(' ', '').lower() + '}', r'\end{figure}', '']))

bib = []
for i, r in enumerate(refs, 1):
    url = f"https://doi.org/{r['doi']}" if r.get('doi') else r['url']
    bib.append(r'\bibitem{ref%d} %s (%s). %s. %s. \url{%s}' % (i, esc(dehyphen(r['authors'])), r['year'], esc(dehyphen(r['title'])), esc(dehyphen(r['venue'])), url))

tex = r'''\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{times}
\usepackage[margin=2.4cm]{geometry}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{amsmath}
\usepackage{url}
\usepackage[colorlinks=true,linkcolor=black,citecolor=black,urlcolor=blue]{hyperref}
\usepackage{microtype}
\usepackage{caption}
\captionsetup{font=small,labelfont=bf}
\urlstyle{same}
\setlength{\parskip}{4pt}

\title{\LARGE TITLE}
\author{Nida Kumbasar$^{1}$ \and Mehmet Oğuz Güneren$^{2}$\\[6pt]
\small $^{1}$TÜBİTAK BİLGEM, Information Technologies Institute (BTE), Data Valorization Department, Gebze, Kocaeli, Türkiye \\
\small \texttt{nida.kumbasar@tubitak.gov.tr}\\[3pt]
\small $^{2}$Department of Artificial Intelligence and Data Engineering, Istanbul Technical University, Istanbul, Türkiye \\
\small \texttt{gnrnoguz@gmail.com}}
\date{\small Draft for coauthor review \textbullet{} revision 3 \textbullet{} 9 November 2026}

\begin{document}
\maketitle

\begin{abstract}
ABSTRACT
\end{abstract}
\noindent\textbf{Keywords:} KEYWORDS

BODY

FIGURES

\begin{thebibliography}{99}
\small
BIB
\end{thebibliography}
\end{document}
'''
tex = tex.replace('TITLE', title).replace('ABSTRACT', '\n'.join(abstract)).replace('KEYWORDS', keywords).replace('BODY', '\n'.join(body)).replace('FIGURES', '\n'.join(figs)).replace('BIB', '\n'.join(bib))
(OUT / 'Orman_SSL_Makale.tex').write_text(tex)
for _ in range(2):
    r = subprocess.run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error', 'Orman_SSL_Makale.tex'], cwd=OUT, capture_output=True, text=True, errors='replace')
if r.returncode != 0:
    print(r.stdout[-3000:]); raise SystemExit('pdflatex failed')
for ext in ['aux', 'log', 'out']:
    (OUT / f'Orman_SSL_Makale.{ext}').unlink(missing_ok=True)
print('ok', OUT / 'Orman_SSL_Makale.pdf')
