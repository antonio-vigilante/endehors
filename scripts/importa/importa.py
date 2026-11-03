"""
Importa i testi dei libri endehors dagli EPUB pubblicati in capitoli Markdown
(con note GFM) per il sito Astro.

Uso (dalla cartella `sito`):
    python scripts/importa/importa.py            # importa tutti i libri
    python scripts/importa/importa.py dio-e-falso

ATTENZIONE: sovrascrive src/content/testi/<libro>/. Dopo la prima importazione
i file Markdown diventano la fonte di riferimento: correggili lì, e rilancia
l'importazione solo se vuoi ripartire da un nuovo EPUB.

Requisiti: Python 3 con beautifulsoup4 e Pillow, pandoc nel PATH.
"""
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from posixpath import dirname, join, normpath

from bs4 import BeautifulSoup, NavigableString, Tag

SITO = Path(__file__).resolve().parents[2]
RADICE = SITO.parent  # cartella con i materiali dei libri
TESTI = SITO / "src" / "content" / "testi"

# --------------------------------------------------------------------------
# Configurazione dei libri
# Ogni capitolo: (file nell'EPUB, slug, titolo, numero, sottotitolo, tipo)
#   tipo: "apparato" (testi del curatore) | "testo" (opera)
#   "+file" accoda il contenuto al capitolo precedente (epigrafi, dediche)
# --------------------------------------------------------------------------
LIBRI = {
    "dio-e-falso": {
        "epub": RADICE / "ateismo/epub/File pubblicato/Vigilante_Dio_è_falso.epub",
        "formato": "pandoc",
        "capitoli": [
            ("OEBPS/Text/premessa.html", "premessa", "Premessa", None, None, "testo"),
            ("OEBPS/Text/cap_1.html", "l-assenza-di-dio", "L’assenza di Dio", "1", None, "testo"),
            ("OEBPS/Text/cap_2.html", "la-gloriosa-macelleria-di-dio", "La gloriosa macelleria di Dio", "2", None, "testo"),
            ("OEBPS/Text/cap_3.html", "i-sacri-e-i-massacrabili", "I sacri e i massacrabili", "3", None, "testo"),
            ("OEBPS/Text/cap_4.html", "oltre-dio", "Oltre Dio", "4", None, "testo"),
            ("OEBPS/Text/bibliografia.html", "bibliografia-minima", "Bibliografia minima", None, None, "bibliografia"),
        ],
    },
    "il-regno-di-dio-e-in-voi": {
        "epub": RADICE / "Tolstoj/ePub/Lev Tolstoj-Il Regno di Dio.epub",
        "formato": "pandoc",
        "capitoli": [
            ("OEBPS/Text/introduzione.xhtml", "introduzione", "Introduzione", None, "Oltre il cerchio della violenza", "apparato"),
            ("OEBPS/Text/nota_bio-bibliografica.xhtml", "nota-bio-bibliografica", "Nota bio-bibliografica", None, None, "apparato"),
            ("OEBPS/Text/nota-alla-traduzione.xhtml", "nota-alla-traduzione", "Nota alla traduzione", None, None, "apparato"),
            ("OEBPS/Text/epigrafe.xhtml", "capitolo-1", None, None, None, "testo"),
            ("+OEBPS/Text/cap_1.xhtml",),
        ] + [
            (f"OEBPS/Text/cap_{n}.xhtml", f"capitolo-{n}", None, None, None, "testo")
            for n in range(2, 13)
        ],
        "epigrafi": ["OEBPS/Text/epigrafe.xhtml"],
        # titoli completi (dall'indice dell'EPUB)
        "titoli": {
            "capitolo-1": "Capitolo I. La dottrina della non-resistenza al male con la violenza è stata insegnata dalla minoranza degli uomini sin dall’origine del cristianesimo",
            "capitolo-2": "Capitolo II. Opinioni dei credenti e dei liberi pensatori sulla non resistenza al male con la violenza",
            "capitolo-3": "Capitolo III. Il cristianesimo mal compreso dai credenti",
            "capitolo-4": "Capitolo IV. Il cristianesimo mal compreso dagli scienziati",
            "capitolo-5": "Capitolo V. Contraddizione fra la nostra vita e la coscienza cristiana",
            "capitolo-6": "Capitolo VI. Gli uomini della nostra società e la guerra",
            "capitolo-7": "Capitolo VII. Significato del servizio militare",
            "capitolo-8": "Capitolo VIII. Accettazione inevitabile dagli uomini della nostra società della dottrina della non-resistenza al male",
            "capitolo-9": "Capitolo IX. L’accettazione de concetto cristiano della vita preserva gli uomini dai mali della nostra vita pagana",
            "capitolo-10": "Capitolo X. Inutilità della violenza governativa per sopprimere il male. Il progresso morale dell’umanità si compie non solo con la conoscenza della verità, ma anche con il formarsi dell’opinione pubblica",
            "capitolo-11": "Capitolo XI. Il concetto cristiano della vita già nasce nella nostra società e distrugge infallibilmente l’ordinamento della nostra vita, fondato sulla violenza. Quando ciò avverrà",
            "capitolo-12": "Capitolo XII. Conclusione. Fate penitenza, perché il Regno di Dio è prossimo, esso è alla nostra porta",
        },
    },
    "apologia-dell-ateismo": {
        "epub": RADICE / "Rensi/Epub pubblicato/Rensi_Apologia.epub",
        "formato": "rensi",
        "capitoli": [
            ("OPS/introduzione.xhtml", "introduzione", "Introduzione", None, "Giuseppe Rensi o l’ateismo come compimento della religione", "apparato"),
            ("OPS/notabio.xhtml", "nota-bio-bibliografica", "Nota bio-bibliografica", None, None, "apparato"),
            ("OPS/nota.xhtml", "nota-del-curatore", "Nota del curatore", None, None, "apparato"),
            ("OPS/epigrafe.xhtml", "avvertenza", "Avvertenza", None, None, "testo"),
            ("+OPS/dedica.xhtml",),
            ("+OPS/avvertenza.xhtml",),
            ("OPS/cap1.xhtml", "che-cosa-e-l-essere", "Che cosa è l’Essere", "I", None, "testo"),
            ("OPS/cap2.xhtml", "dio-e-il-non-essere", "Dio è il non-Essere", "II", None, "testo"),
            ("OPS/cap3.xhtml", "gli-attributi-di-dio", "Gli attributi di Dio", "III", None, "testo"),
            ("OPS/cap4.xhtml", "i-falsi-dio", "I falsi Dio", "IV", None, "testo"),
            ("OPS/cap5.xhtml", "estetica-etica-e-religione-dell-ateismo", "Estetica, etica e religione dell’ateismo", "V", None, "testo"),
        ],
        "note": "OPS/footnotes.xhtml",
        "epigrafi": ["OPS/epigrafe.xhtml", "OPS/dedica.xhtml"],
    },
    "per-la-soppressione-dei-partiti-politici": {
        "epub": RADICE / "Weil/Simone Weil - Per la soppressione dei partiti politici, a cura di Antonio Vigilante.epub",
        "formato": "scrivener",
        "capitoli": [
            ("OPS/body3.xhtml", "introduzione", "Introduzione", None, "Uccidere il grosso animale", "apparato"),
            ("OPS/body5.xhtml", "per-la-soppressione-dei-partiti-politici", "Per la soppressione dei partiti politici", None, None, "testo"),
        ],
        "note": "OPS/footnotes.xhtml",
    },
    "nonviolenza-senza-miti": {
        "epub": RADICE / "Nonviolenza/Nonviolenza senza miti - Antonio Vigilante.epub",
        "formato": "scrivener",
        "capitoli": [("OPS/body3.xhtml", "prefazione", "Prefazione", None, None, "testo")]
        + [(f"OPS/body{n}.xhtml", f"capitolo-{n - 3}", None, None, None, "testo") for n in range(4, 14)]
        + [("OPS/body14.xhtml", "una-conclusione-provvisoria", "Una conclusione provvisoria", None, None, "testo")],
        "note": "OPS/footnotes.xhtml",
    },
}

NUOVO = BeautifulSoup("", "html.parser")
ROMANI = re.compile(r"^(Capitolo\s+[IVXLC]+|\d+)\.\s+(.+)$", re.S)


# --------------------------------------------------------------------------
# Utilità
# --------------------------------------------------------------------------
def leggi(z: zipfile.ZipFile, nome: str) -> BeautifulSoup:
    return BeautifulSoup(z.read(nome).decode("utf-8"), "html.parser")


def testo(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ")).strip()


def vuoto(el: Tag) -> bool:
    return not testo(el).replace("\xa0", "").strip() and not el.find(["img", "hr"])


def pandoc(html: str) -> str:
    out = subprocess.run(
        ["pandoc", "-f", "html-native_divs-native_spans", "-t", "gfm-raw_html+footnotes", "--wrap=none"],
        input=html.encode("utf-8"),
        capture_output=True,
        check=True,
    )
    return out.stdout.decode("utf-8").strip()


def stili_css(z: zipfile.ZipFile) -> dict:
    """Mappa classe -> proprietà CSS (per gli EPUB generati da Scrivener)."""
    regole = {}
    for nome in z.namelist():
        if nome.endswith(".css") or nome.endswith(".xhtml"):
            src = z.read(nome).decode("utf-8", "ignore")
            for m in re.finditer(r"\.([\w-]+)\s*\{([^}]*)\}", src):
                props = dict(
                    (k.strip().lower(), v.strip().lower())
                    for k, _, v in (p.partition(":") for p in m.group(2).split(";"))
                    if k.strip()
                )
                regole.setdefault(m.group(1), {}).update(props)
    return regole


def segnaposto(label: str) -> str:
    return f"XNOTAX{label}XFINEX"


# --------------------------------------------------------------------------
# Normalizzazione per formato
# --------------------------------------------------------------------------
def note_pandoc(body: Tag) -> dict:
    """Formato Pandoc/Sigil: <a class=footnote-ref href=#fnN> + <ol><li id=fnN>."""
    note = {}
    for li in body.select("li[id^=fn]"):
        label = li["id"][2:]
        for a in li.select("a.footnote-back"):
            a.decompose()
        note[label] = li.decode_contents()
        lista = li.parent
        li.decompose()
        if lista and lista.name == "ol" and not lista.find("li"):
            lista.decompose()
    for sez in body.select("section.footnotes, div.footnotes, hr.footnotes-sep"):
        sez.decompose()
    for a in body.select("a.footnote-ref"):
        label = a["href"].split("#fn")[-1]
        a.replace_with(NavigableString(segnaposto(label)))
    return note


def note_esterne(z: zipfile.ZipFile, file_note: str, css: dict) -> dict:
    """Note raccolte in footnotes.xhtml (Scrivener)."""
    soup = leggi(z, file_note)
    if css:
        for span in soup.find_all("span"):
            p = {}
            for c in span.get("class", []):
                p.update(css.get(c, {}))
            if "italic" in p.get("font-style", ""):
                span.name = "em"
                del span["class"]
            elif p.get("font-weight", "") in ("bold", "700"):
                span.name = "strong"
                del span["class"]
    note = {}
    for ancora in soup.select("a[id^=fn]"):
        p = ancora.find_parent("p")
        label = ancora["id"][2:]
        for a in p.find_all("a"):
            if a.get("id", "").startswith("fn") or a.get("href", "").count("#fn"):
                a.decompose()
        html = p.decode_contents().strip()
        html = re.sub(r"^(<span>\s*</span>|\s|&nbsp;|\xa0)+", "", html)
        note[label] = html
    return note


def rimpiazza_rimandi_scrivener(body: Tag):
    """Rimandi Scrivener: {<a id=fnN></a><a href=footnotes.xhtml#fnN>N</a>}"""
    for a in body.select('a[href*="#fn"]'):
        label = a["href"].split("#fn")[-1]
        prec = a.find_previous_sibling()
        if prec is not None and prec.name == "a" and prec.get("id", "").startswith("fn"):
            prec.decompose()
        a.replace_with(NavigableString(segnaposto(label)))
    # graffe attorno al rimando
    for s in body.find_all(string=re.compile("XNOTAX")):
        nuovo = re.sub(r"\{\s*(XNOTAX\w+?XFINEX)\s*\}", r"\1", str(s))
        s.replace_with(NavigableString(nuovo))
    for s in list(body.find_all(string=re.compile(r"[{}]"))):
        # graffe rimaste spezzate tra nodi adiacenti al segnaposto
        txt = str(s)
        nxt = s.next_element
        prv = s.previous_element
        if txt.rstrip().endswith("{") and nxt is not None and "XNOTAX" in str(nxt):
            txt = txt.rstrip()[:-1]
        if txt.lstrip().startswith("}") and prv is not None and "XFINEX" in str(prv):
            txt = txt.lstrip()[1:]
        if txt != str(s):
            s.replace_with(NavigableString(txt))


def normalizza_scrivener(body: Tag, css: dict):
    """Converte le classi di stile di Scrivener in markup semantico."""
    def props(el):
        p = {}
        for c in el.get("class", []):
            p.update(css.get(c, {}))
        return p

    def grande(el):
        size = props(el).get("font-size", "")
        m = re.match(r"([\d.]+)%", size)
        return bool(m and float(m.group(1)) >= 150)

    for span in body.find_all("span"):
        p = props(span)
        if grande(span):
            span["data-titolo"] = "1"
            continue
        italic = "italic" in p.get("font-style", "")
        bold = p.get("font-weight", "") in ("bold", "700", "600")
        if italic or bold:
            inner = span
            span.name = "em" if italic else "strong"
            if italic and bold:
                b = NUOVO.new_tag("strong")
                for c in list(inner.contents):
                    b.append(c.extract())
                inner.append(b)
            del span["class"]
    for p in body.find_all("p"):
        pr = props(p)
        if p.find(attrs={"data-titolo": "1"}) and len(testo(p)) < 220:
            p.name = "h2"
            continue
        if pr.get("text-align") == "center":
            p["data-allinea"] = "centro"
        elif pr.get("text-align") == "right":
            p["data-allinea"] = "destra"
    for el in body.find_all(True):
        if el.name in ("span", "font"):
            el.unwrap()


def normalizza_rensi(body: Tag):
    for p in body.find_all("p"):
        cls = p.get("class", [])
        if "citazione" in cls:
            p.name = "blockquote"
        elif "testocentrato" in cls:
            p["data-allinea"] = "centro"
        elif "testodestra" in cls:
            p["data-allinea"] = "destra"
    for s in body.select('span[style*="italic"]'):
        s.unwrap()
    for el in body.find_all("span"):
        el.unwrap()


def pulisci(body: Tag):
    for el in body.find_all(["script", "style", "img", "svg"]):
        el.decompose()
    for br in body.select("p > br:only-child"):
        br.decompose()
    for el in body.find_all("div", class_="centered"):
        el["data-allinea"] = "centro"
        el.name = "p"
    for p in body.find_all(["p", "h1", "h2", "h3"]):
        if vuoto(p):
            p.decompose()
    # separatori *** -> <hr>
    for p in body.find_all("p"):
        if re.fullmatch(r"[\s*\u2217\u2022·]+", testo(p)) and "*" in testo(p):
            p.replace_with(NUOVO.new_tag("hr"))
    for i in body.find_all("i"):
        i.name = "em"
    for b in body.find_all("b"):
        b.name = "strong"
    for a in body.find_all("a"):
        if not a.get("href", "").startswith("http"):
            a.unwrap()
    # attributi superflui
    for el in body.find_all(True):
        for k in list(el.attrs):
            if k not in ("href", "data-allinea"):
                del el[k]


# --------------------------------------------------------------------------
# HTML -> Markdown
# --------------------------------------------------------------------------
def in_markdown(body: Tag) -> str:
    """Converte i blocchi uno alla volta: i paragrafi allineati restano HTML."""
    parti = []
    buffer = []

    def svuota():
        if buffer:
            parti.append(pandoc("".join(buffer)))
            buffer.clear()

    for el in body.children:
        if isinstance(el, NavigableString):
            if str(el).strip():
                buffer.append(f"<p>{el}</p>")
            continue
        if el.get("data-allinea"):
            svuota()
            classe = "centro" if el["data-allinea"] == "centro" else "destra"
            del el["data-allinea"]
            md = pandoc(f"<p>{el.decode_contents()}</p>")
            parti.append(f'<div class="{classe}">\n\n{md}\n\n</div>')
        else:
            buffer.append(str(el))
    svuota()
    return "\n\n".join(p for p in parti if p.strip())


def nota_markdown(html: str) -> str:
    md = pandoc(html if "<p" in html else f"<p>{html}</p>")
    righe = md.split("\n")
    return "\n".join([righe[0]] + [("    " + r) if r.strip() else "" for r in righe[1:]])


def frontmatter(dati: dict) -> str:
    righe = ["---"]
    for k, v in dati.items():
        if v is None:
            continue
        if isinstance(v, (int, float)):
            righe.append(f"{k}: {v}")
        else:
            righe.append(f'{k}: "{str(v).replace(chr(34), chr(92) + chr(34))}"')
    righe.append("---")
    return "\n".join(righe) + "\n\n"


# --------------------------------------------------------------------------
def importa(slug: str):
    conf = LIBRI[slug]
    z = zipfile.ZipFile(conf["epub"])
    formato = conf["formato"]
    css = stili_css(z) if formato == "scrivener" else {}
    note_globali = note_esterne(z, conf["note"], css) if conf.get("note") else {}

    dest = TESTI / slug
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    capitoli = []
    for voce in conf["capitoli"]:
        accoda = voce[0].startswith("+")
        nome = voce[0].lstrip("+")
        soup = leggi(z, nome)
        body = soup.body
        note_cap = {}
        if formato == "pandoc":
            note_cap = note_pandoc(body)
        else:
            rimpiazza_rimandi_scrivener(body)
            if formato == "scrivener":
                normalizza_scrivener(body, css)
            else:
                normalizza_rensi(body)

        # titolo originale (primo h1/h2) e autore dell'eventuale saggio
        h = body.find(["h1", "h2"])
        titolo_orig = testo(h) if h else ""
        if h is not None and (formato != "scrivener" or body.find(["h1", "h2"]) == h):
            h.decompose()
            # Scrivener: titoli su più paragrafi grandi consecutivi (es. Weil)
            while formato == "scrivener":
                nxt = body.find(["h1", "h2", "p"])
                if nxt is not None and nxt.name == "h2" and len(testo(nxt)) < 120 and not capitoli:
                    titolo_orig += ". " + testo(nxt)
                    nxt.decompose()
                else:
                    break
        pulisci(body)
        autore = None
        primo = body.find("p")
        if primo is not None and testo(primo) in ("Antonio Vigilante",):
            autore = testo(primo)
            primo.decompose()

        md = in_markdown(body)
        usate = re.findall(r"XNOTAX(\w+?)XFINEX", md)
        md = re.sub(r"\\?XNOTAX(\w+?)XFINEX", r"[^\1]", md)
        # graffe residue attorno ai rimandi: {[^3]} -> [^3]
        md = re.sub(r"\\?\{\s*(\[\^\w+\])", r"\1", md)
        md = re.sub(r"(\[\^\w+\])\s*\\?\}", r"\1", md)
        # nessuno spazio prima del rimando di nota
        md = re.sub(r"[ \t\xa0]+(\[\^\w+\])", r"\1", md)
        fonti = {**note_globali, **note_cap}
        corpo_note = []
        for label in dict.fromkeys(usate):
            if label in fonti:
                corpo_note.append(f"[^{label}]: {nota_markdown(fonti[label])}")
            else:
                print(f"  ! {slug}/{nome}: nota {label} non trovata")
        if nome in conf.get("epigrafi", ()):
            md = f'<div class="epigrafe">\n\n{md}\n\n</div>'

        if accoda:
            capitoli[-1]["md"] += "\n\n" + md
            capitoli[-1]["note"] += corpo_note
            continue

        _, cslug, titolo, numero, sottotitolo, tipo = voce
        if titolo is None:
            titolo = conf.get("titoli", {}).get(cslug) or titolo_orig
            m = ROMANI.match(titolo)
            if m:
                numero = numero or m.group(1)
                titolo = m.group(2).strip()
        capitoli.append(
            {"slug": cslug, "titolo": titolo, "numero": numero, "sottotitolo": sottotitolo,
             "tipo": tipo, "autore": autore, "md": md, "note": corpo_note}
        )

    for i, c in enumerate(capitoli, 1):
        fm = {
            "titolo": c["titolo"].rstrip(". "),
            "numero": c["numero"],
            "sottotitolo": c["sottotitolo"],
            "autore": c["autore"],
            "tipo": c["tipo"],
            "ordine": i,
        }
        corpo = c["md"].strip()
        if c["note"]:
            corpo += "\n\n" + "\n\n".join(c["note"])
        (dest / f"{i:02d}-{c['slug']}.md").write_text(frontmatter(fm) + corpo + "\n", encoding="utf-8")
        print(f"  {i:02d} {c['slug']}  ({len(corpo) // 1000} kB, {len(c['note'])} note)")


if __name__ == "__main__":
    scelti = sys.argv[1:] or list(LIBRI)
    for s in scelti:
        print(s)
        importa(s)
