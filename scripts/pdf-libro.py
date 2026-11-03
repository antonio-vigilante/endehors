"""Impagina un libro in PDF per la lettura su tablet (LuaLaTeX + pandoc).

Uso:  python scripts/pdf-libro.py <id-libro> [--tex]

Legge la scheda (src/content/libri/<id>.yaml) e i capitoli
(src/content/testi/<id>/*.md), compone il PDF e lo scrive in
public/download/<id>.pdf (e in dist/download se esiste).
Con --tex salva anche il sorgente .tex accanto al PDF, in originali/.

Formato 150x200 mm (3:4, come un tablet in verticale), EB Garamond 12 pt
giustificato con sillabazione italiana, note a piè di pagina, copertina,
frontespizio, colophon e indice con collegamenti.

Richiede: pandoc, LuaLaTeX (MiKTeX o TeX Live) con i pacchetti
fontspec, polyglossia, microtype, geometry, fancyhdr, titlesec, footmisc,
xcolor, graphicx, hyperref, bookmark; i font EB Garamond e TeX Gyre Adventor.
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

import yaml

SITO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def tex(s):
    """Escape per i testi brevi presi dalla scheda (titoli, crediti)."""
    s = s.replace('\\', r'\textbackslash{}')
    for c in '&%$#_{}':
        s = s.replace(c, '\\' + c)
    s = s.replace('~', r'\textasciitilde{}').replace('^', r'\textasciicircum{}')
    return s


def md2tex(md):
    r = subprocess.run(['pandoc', '-f', 'markdown', '-t', 'latex', '--wrap=preserve'],
                       input=md.encode('utf-8'), capture_output=True, check=True)
    return r.stdout.decode('utf-8').strip()


def inline(s):
    """Markdown in linea (corsivi nei crediti) -> LaTeX."""
    return md2tex(s).replace('\n', ' ')


def leggi_capitoli(libro):
    cap = []
    for f in sorted(glob.glob(os.path.join(SITO, 'src', 'content', 'testi', libro, '*.md'))):
        testo = open(f, encoding='utf-8').read()
        m = re.match(r'^---\n(.*?)\n---\n(.*)$', testo, re.S)
        meta, corpo = yaml.safe_load(m.group(1)), m.group(2)
        cap.append(dict(meta=meta, tex=md2tex(corpo)))
    cap.sort(key=lambda c: c['meta'].get('ordine', 0))
    return cap


PREAMBOLO = r"""
\documentclass[12pt,oneside,openany]{book}
\usepackage[paperwidth=150mm,paperheight=200mm,top=17mm,bottom=19mm,left=15mm,right=15mm,
            headheight=14pt,headsep=6mm,footskip=10mm]{geometry}
\usepackage{fontspec}
\usepackage{polyglossia}
\setmainlanguage{italian}
\setmainfont{EBGaramond}[Extension=.otf, UprightFont=*-Regular, ItalicFont=*-Italic,
  BoldFont=*-SemiBold, BoldItalicFont=*-SemiBoldItalic, Ligatures=TeX, Numbers=OldStyle]
\newfontfamily\adventor{texgyreadventor}[Extension=.otf, UprightFont=*-regular, BoldFont=*-bold]
\usepackage[protrusion=true,expansion=true,tracking=false,kerning=false,spacing=false]{microtype}
\usepackage{xcolor}
\definecolor{blu}{RGB}{53,74,121}
\definecolor{grigio}{RGB}{95,95,95}
\usepackage{graphicx}
\usepackage[bottom,hang]{footmisc}
\setlength{\footnotemargin}{1.2em}
\counterwithout{footnote}{chapter}   % numerazione continua, come nell'edizione originale
\setlength{\footnotesep}{0.8\baselineskip}
\renewcommand{\footnotelayout}{\raggedright}
\usepackage{titlesec}
\usepackage{titletoc}
\usepackage{fancyhdr}
\usepackage[hidelinks,pdfusetitle,bookmarksnumbered=false]{hyperref}
\usepackage{bookmark}
\urlstyle{same}

\linespread{1.1}
\setlength{\parindent}{1.1em}
\widowpenalty=10000 \clubpenalty=10000
\raggedbottom
\emergencystretch=1.5em

% capitoli
\titleformat{\chapter}[block]
  {\raggedright\adventor\bfseries\Large\color{blu}\linespread{1.05}\selectfont}
  {\thechapter.}{0.35em}{}
\titleformat{name=\chapter,numberless}[block]
  {\raggedright\adventor\bfseries\Large\color{blu}\linespread{1.05}\selectfont}{}{0pt}{}
\titlespacing*{\chapter}{0pt}{6mm}{11mm}

% indice
% titoli a bandiera, con 2.5em liberi a destra; il numero di pagina arriva al margine
\contentsmargin{0pt}
\titlecontents{chapter}[0pt]{\addvspace{0.55em}\rightskip=2.5em plus 1fil\relax\parfillskip=-\rightskip}
  {\thecontentslabel.\ }
  {}
  {\hfill\thecontentspage}[\addvspace{0pt}]

% testatine
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\fancyhead[C]{\footnotesize\color{grigio}\textsc{\MakeLowercase{@@TITOLO@@}}}
\fancyfoot[C]{\small\thepage}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[C]{\small\thepage}}

\hypersetup{pdftitle={@@TITOLO_PDF@@}, pdfauthor={@@AUTORE_PDF@@}, pdflang={it}}
"""


def documento(libro):
    d = yaml.safe_load(open(os.path.join(SITO, 'src', 'content', 'libri', libro + '.yaml'), encoding='utf-8'))
    capitoli = leggi_capitoli(libro)
    copertina = os.path.normpath(os.path.join(SITO, 'src', 'content', 'libri', d['copertina'])).replace('\\', '/')
    logo = os.path.join(SITO, 'src', 'assets', 'logo-endehors.png').replace('\\', '/')
    # indirizzo del sito preso da astro.config.mjs, come fa la pagina "integrale"
    sito = re.search(r"site:\s*'([^']+)'", open(os.path.join(SITO, 'astro.config.mjs'), encoding='utf-8').read())
    url = sito.group(1).rstrip('/') + '/libri/' + libro + '/'

    out = [PREAMBOLO.replace('@@TITOLO@@', tex(d['titolo']))
                    .replace('@@TITOLO_PDF@@', tex(d['titolo']))
                    .replace('@@AUTORE_PDF@@', tex(d['autore']))]
    out.append(r'\begin{document}')
    out.append(r'\frontmatter')

    # copertina: a tutta altezza, centrata (il fondo è bianco come la pagina)
    out.append(r'''\thispagestyle{empty}\pdfbookmark[0]{Copertina}{copertina}
\newgeometry{margin=0pt}
\noindent\makebox[\paperwidth][c]{\includegraphics[height=\paperheight,keepaspectratio]{%s}}
\restoregeometry
\clearpage''' % copertina)

    # frontespizio
    cura = []
    if d.get('traduttore') and d.get('traduttore') != d.get('curatore'):
        cura.append('Traduzione di ' + tex(d['traduttore']))
    if d.get('curatore'):
        cura.append(('Traduzione e cura di ' if d.get('traduttore') == d['curatore'] else 'A cura di ') + tex(d['curatore']))
    out.append(r'''\thispagestyle{empty}\pdfbookmark[0]{Frontespizio}{frontespizio}
\begin{center}
\vspace*{14mm}
{\large\textsc{%s}\par}
\vspace{9mm}
{\adventor\bfseries\Huge\color{blu}\linespread{1.0}\selectfont %s\par}
%s%s
\vfill
\includegraphics[height=17mm]{%s}\par
\vspace{2.5mm}
{\large\bfseries endehors\par}
\vspace*{6mm}
\end{center}
\clearpage''' % (tex(d['autore']), tex(d['titolo']),
                 ('\n\\vspace{5mm}{\\large\\itshape %s\\par}' % tex(d['sottotitolo'])) if d.get('sottotitolo') else '',
                 ('\n\\vspace{9mm}{\\itshape %s\\par}' % r'\\'.join(cura)) if cura else '',
                 logo))

    # colophon
    col = []
    if d.get('titolo_originale'):
        col.append('Titolo originale: ' + inline(d['titolo_originale']))
    if d.get('edizione'):
        col.append(inline(d['edizione']))
    lic = 'Licenza %s (\\url{%s})' % (tex(d['licenza']['nome']), d['licenza']['url'])
    if d['licenza'].get('testo'):
        lic += '. ' + inline(d['licenza']['testo'])
    col.append(lic)
    if d.get('isbn'):
        col.append('ISBN ' + tex(str(d['isbn'])))
    if d.get('doi'):
        col.append('DOI \\href{https://doi.org/%s}{%s}' % (d['doi'], tex(d['doi'])))
    if d.get('crediti'):
        col.append(inline(d['crediti']))
    col.append('endehors · \\url{%s}' % url)
    out.append(r'''\thispagestyle{empty}
\vspace*{\fill}
{\footnotesize\raggedright\color{grigio}
%s\par}
\clearpage''' % '\\par\\smallskip\n'.join(col))

    # indice
    out.append(r'''\pdfbookmark[0]{Indice}{indice}
\thispagestyle{empty}
\noindent{\adventor\bfseries\large\color{blu}Indice\par}
\vspace{6mm}
\makeatletter\@starttoc{toc}\makeatother
\clearpage''')

    out.append(r'\mainmatter')
    for c in capitoli:
        titolo = tex(c['meta']['titolo'])
        if c['meta'].get('numero'):
            out.append(r'\setcounter{chapter}{%d}\addtocounter{chapter}{-1}' % int(c['meta']['numero']))
            out.append(r'\chapter{%s}' % titolo)
        else:
            out.append(r'\chapter*{%s}\addcontentsline{toc}{chapter}{%s}' % (titolo, titolo))
        out.append(c['tex'])
    out.append(r'\end{document}')
    return '\n\n'.join(out), d


def componi(libro, salva_tex=False):
    sorgente, d = documento(libro)
    tmp = tempfile.mkdtemp(prefix='pdf-' + libro + '-')
    try:
        with open(os.path.join(tmp, libro + '.tex'), 'w', encoding='utf-8') as f:
            f.write(sorgente)
        for giro in (1, 2, 3):            # indice e riferimenti si stabilizzano in più passate
            r = subprocess.run(['lualatex', '--disable-installer', '-interaction=nonstopmode',
                                '-halt-on-error', libro + '.tex'], cwd=tmp, capture_output=True, timeout=600)
            if r.returncode:
                log = open(os.path.join(tmp, libro + '.log'), encoding='utf-8', errors='replace').read()
                print(log[-3000:])
                raise SystemExit(f'LuaLaTeX non è riuscito (passata {giro}). File in {tmp}')
        pdf = os.path.join(tmp, libro + '.pdf')
        dest = os.path.join(SITO, 'public', 'download', libro + '.pdf')
        shutil.copyfile(pdf, dest)
        if os.path.isdir(os.path.join(SITO, 'dist', 'download')):
            shutil.copyfile(pdf, os.path.join(SITO, 'dist', 'download', libro + '.pdf'))
        if salva_tex:
            shutil.copyfile(os.path.join(tmp, libro + '.tex'), os.path.join(SITO, 'originali', libro + '.tex'))
        avvisi = re.findall(r'^(?:Overfull|Underfull) \\hbox.*$',
                            open(os.path.join(tmp, libro + '.log'), encoding='utf-8', errors='replace').read(), re.M)
        print(f'{libro}: PDF scritto in {dest}  ({len(avvisi)} righe con spaziatura da controllare)')
        for a in avvisi[:15]:
            print('  ', a)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    componi(sys.argv[1], '--tex' in sys.argv)
