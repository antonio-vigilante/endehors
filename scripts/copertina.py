"""Copertine della collana endehors, sul modello di "Il Regno di Dio è in voi".

Uso:  python scripts/copertina.py <id-libro> [file-di-uscita.jpg]

Senza file di uscita scrive src/assets/copertine/<id>.jpg (983x1500) e
originali/<id>-2x.jpg (1966x3000, per ebook e stampa).

Schema: fondo bianco; autore in maiuscoletto Garamond; titolo in maiuscolo
Adventor Bold blu, con eventuali parole in corsivo grigio (come la "è" di
Tolstoj); righe di credito in corsivo grigio; marchio in basso a sinistra.
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

SITO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UF = os.path.expandvars(r'%LOCALAPPDATA%/Microsoft/Windows/Fonts/')

# Titolo: lista di righe; ogni riga è una lista di (testo, stile),
# stile 'T' = maiuscolo blu, 'i' = corsivo grigio.
LIBRI = {
    'nonviolenza-senza-miti': dict(
        autore='Antonio Vigilante',
        titolo=[[('NONVIOLENZA', 'T')], [('senza', 'i'), ('MITI', 'T')]],
        crediti=[],
    ),
    'apologia-dell-ateismo': dict(
        autore='Giuseppe Rensi',
        titolo=[[('APOLOGIA', 'T')], [('dell’', 'i'), ('ATEISMO', 'T')]],
        crediti=['A cura di Antonio Vigilante'],
    ),
}

K = 2                                   # sovracampionamento
W, H = 983 * K, 1500 * K
BLU = (53, 74, 121)
GRIGIO = (80, 80, 80)
NERO = (20, 20, 20)
ML = 87 * K                             # margine sinistro del titolo
MR = W - 83 * K                         # margine destro
SIZE_MAX = 177 * K                      # corpo del titolo di Tolstoj
TRACK = -5 / 177                        # spaziatura del titolo, in frazione del corpo

sans = lambda s: ImageFont.truetype(SITO + '/public/font/texgyreadventor-bold.woff', s)
gar = lambda s: ImageFont.truetype(UF + 'EBGaramond-Regular.ttf', s)
gar_it = lambda s: ImageFont.truetype(UF + 'EBGaramond-Italic.ttf', s)
gar_sb = lambda s: ImageFont.truetype(UF + 'EBGaramond-SemiBold.ttf', s)


def cap_h(font):
    b = font.getbbox('H')
    return b[3] - b[1]


CAP_SANS = cap_h(sans(1000)) / 1000
CAP_IT = cap_h(gar_it(1000)) / 1000
CAP_GAR = cap_h(gar(1000)) / 1000


def larghezza(s, font, track=0):
    return sum(font.getlength(c) + track for c in s) - track


def font_riga(size):
    """Font e spaziature per un titolo di corpo 'size'."""
    fT = sans(size)
    ch = cap_h(fT)
    fI = gar_it(round(ch / CAP_IT * 0.95))
    return fT, fI, TRACK * size, 0.30 * ch


def spazio(t, st, gap, fT):
    """Spazio dopo un segmento: ridotto dopo un'elisione (dell’ATEISMO)."""
    if t.endswith('’'):
        return 0.06 * gap / 0.30
    return gap if st == 'i' else fT.getlength(' ')


def largh_riga(riga, size):
    fT, fI, trk, gap = font_riga(size)
    w = 0
    for n, (t, st) in enumerate(riga):
        w += larghezza(t, fT, trk) if st == 'T' else fI.getlength(t)
        if n < len(riga) - 1:
            w += spazio(t, st, gap, fT)
    return w


def disegna(libro, out):
    cfg = LIBRI[libro]
    im = Image.new('RGB', (W, H), 'white')
    d = ImageDraw.Draw(im)

    def testo(x, base, s, font, fill, track=0):
        for ch in s:
            d.text((x, base), ch, font=font, fill=fill, anchor='ls')
            x += font.getlength(ch) + track
        return x

    # Autore in maiuscoletto
    fA = gar(round(30 * K / CAP_GAR))
    fa = gar(round(fA.size * 0.76))
    x = 76 * K
    for parola in cfg['autore'].split():
        x = testo(x, 107 * K, parola[0], fA, NERO, 1 * K)
        x = testo(x, 107 * K, parola[1:].upper(), fa, NERO, 1.5 * K)
        x += fA.getlength(' ')

    # Titolo: il corpo più grande che fa stare ogni riga nella giustezza
    size = SIZE_MAX
    while max(largh_riga(r, size) for r in cfg['titolo']) > MR - ML:
        size -= 2
    fT, fI, trk, gap = font_riga(size)
    ch = cap_h(fT)
    pitch = round(ch * 146 / 131)       # interlinea di Tolstoj
    base = 165 * K + ch
    for riga in cfg['titolo']:
        x = ML
        for n, (t, st) in enumerate(riga):
            if st == 'T':
                x = testo(x - (fT.getbbox(t[0])[0] if x == ML else 0), base, t, fT, BLU, trk)
            else:
                x = testo(x - fI.getbbox(t[0])[0] + (4 * K if x == ML else 0), base, t, fI, GRIGIO)
            if n < len(riga) - 1:
                x += spazio(t, st, gap, fT)
        base += pitch
    fine = base - pitch

    # Crediti in corsivo grigio
    fC = gar_it(round(30 * K / CAP_IT))
    y = fine + 82 * K
    for r in cfg['crediti']:
        d.text((93 * K, y), r, font=fC, fill=GRIGIO, anchor='ls')
        y += 58 * K

    # Marchio editoriale
    logo = Image.open(SITO + '/src/assets/logo-endehors.png').convert('RGBA')
    logo = logo.crop(logo.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox())
    lh = 84 * K
    logo = logo.resize((round(logo.width * lh / logo.height), lh), Image.LANCZOS)
    cx = 146 * K
    im.paste(logo, (cx - logo.width // 2, 1322 * K), logo)
    d.text((cx, 1439 * K), 'endehors', font=gar_sb(29 * K), fill=NERO, anchor='ms')

    out2x = out[:-4] + '-2x.jpg' if out else os.path.join(SITO, 'originali', libro + '-2x.jpg')
    out = out or os.path.join(SITO, 'src', 'assets', 'copertine', libro + '.jpg')
    im.save(out2x, quality=94)
    im.resize((983, 1500), Image.LANCZOS).save(out, quality=92)
    print(f'{libro}: corpo titolo {size // K}, maiuscole {ch // K}px -> {out}')


if __name__ == '__main__':
    disegna(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
