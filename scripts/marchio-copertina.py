"""Sostituisce il vecchio marchio endehors in una copertina esistente.

Uso:  python scripts/marchio-copertina.py <id-libro> <ingresso> <uscita>

Le coordinate sono quelle delle copertine del sito (src/assets/copertine);
per immagini più grandi vengono scalate in proporzione alla larghezza.
  - 'figura': cambia solo la figura, lasciando la scritta "endehors";
  - 'marchio': cancella figura e scritta e ridisegna il marchio completo.
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

SITO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UF = os.path.expandvars(r'%LOCALAPPDATA%/Microsoft/Windows/Fonts/')

COPERTINE = {
    # larghezza della copertina del sito, zona in cui cercare la vecchia figura
    'il-regno-di-dio-e-in-voi': dict(tipo='figura', w=983, zona=(60, 1310, 300, 1412)),
    'dio-e-falso': dict(tipo='figura', w=1000, zona=(60, 1215, 300, 1312)),
    # la copertina dell'ePub di Dio è falso ha proporzioni diverse da quella del sito
    'dio-e-falso-epub': dict(tipo='figura', w=1571, zona=(150, 2095, 420, 2256)),
    # per Weil: rettangolo da sbiancare, linea di base e margine sinistro della scritta
    'per-la-soppressione-dei-partiti-politici': dict(tipo='marchio', w=1000, H=1414,
                                                     sbianca=(95, 1170, 230, 1345), base=1336, sx=106),
}

ALTEZZA_FIGURA_ORIGINALE = 464   # altezza della figura nel disegno originale (con la punta)


def logo_nuovo():
    im = Image.open(SITO + '/src/assets/logo-endehors.png').convert('RGBA')
    return im.crop(im.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox())


def ridimensiona(im, w, h):
    return im.resize((round(w * 4), round(h * 4)), Image.LANCZOS).resize((round(w), round(h)), Image.LANCZOS)


def sostituisci(libro, ingresso, uscita):
    c = COPERTINE[libro]
    im = Image.open(ingresso).convert('RGB')
    s = im.width / c['w']
    nuovo = logo_nuovo()
    d = ImageDraw.Draw(im)

    if c['tipo'] == 'figura':
        x0, y0, x1, y1 = [round(v * s) for v in c['zona']]
        m = im.convert('L').crop((x0, y0, x1, y1)).point(lambda v: 255 if v < 235 else 0)
        l, t, r, b = m.getbbox()
        l, t, r, b = l + x0, t + y0, r + x0, b + y0
        d.rectangle((l - 3 * s, t - 3 * s, r + 3 * s, min(b + 3 * s, y1)), fill='white')
        k = (b - t) / ALTEZZA_FIGURA_ORIGINALE
        f = ridimensiona(nuovo, nuovo.width * k, nuovo.height * k)
        im.paste(f, (l, b - f.height), f)
    else:
        d.rectangle([v * s for v in c['sbianca']], fill='white')
        k = c['H'] / 1500 * s             # scala rispetto alla copertina di Tolstoj (1500 px)
        font = ImageFont.truetype(UF + 'EBGaramond-SemiBold.ttf', round(29 * k))
        base, sx = c['base'] * s, c['sx'] * s
        tw = font.getlength('endehors')
        asc = -font.getbbox('endehors', anchor='ls')[1]
        cx = sx + tw / 2
        lh = 84 * k
        lw = nuovo.width * lh / nuovo.height
        f = ridimensiona(nuovo, lw, lh)
        im.paste(f, (round(cx - lw / 2), round(base - asc - 13 * k - lh)), f)
        d.text((cx, base), 'endehors', font=font, fill=(20, 20, 20), anchor='ms')

    if uscita.lower().endswith(('.jpg', '.jpeg')):
        im.save(uscita, quality=92)
    else:
        im.save(uscita, optimize=True)
    print(f'{libro}: {im.size} -> {uscita}')


if __name__ == '__main__':
    sostituisci(*sys.argv[1:4])
