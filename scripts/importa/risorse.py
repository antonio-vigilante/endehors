"""
Prepara le risorse statiche del sito a partire dai materiali dei libri:
copertine, logo, favicon, font dei titoli e file da scaricare (ePub/PDF).

Uso (dalla cartella `sito`):  python scripts/importa/risorse.py
"""
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None

SITO = Path(__file__).resolve().parents[2]
RADICE = SITO.parent
ASSETS = SITO / "src" / "assets"
PUBLIC = SITO / "public"

COPERTINE = {
    "dio-e-falso": RADICE / "ateismo/cover_epub.jpg",
    "il-regno-di-dio-e-in-voi": RADICE / "Tolstoj/ePub/cover.png",
    "apologia-dell-ateismo": RADICE / "Rensi/Epub pubblicato/copertina.png",
    "per-la-soppressione-dei-partiti-politici": RADICE / "Weil/cover_endehors.jpg",
    "nonviolenza-senza-miti": ("zip", RADICE / "Nonviolenza/Nonviolenza senza miti - Antonio Vigilante.epub", "OPS/images/cover.jpg"),
}

# File da scaricare. I PDF mancanti vengono generati da `npm run pdf`.
DOWNLOAD = {
    "dio-e-falso.epub": RADICE / "ateismo/epub/File pubblicato/Vigilante_Dio_è_falso.epub",
    "dio-e-falso.pdf": RADICE / "ateismo/Cartaceo file definitivi/Dio_è_falso_stampa.pdf",
    "il-regno-di-dio-e-in-voi.epub": RADICE / "Tolstoj/ePub/Lev Tolstoj-Il Regno di Dio.epub",
    "il-regno-di-dio-e-in-voi.pdf": RADICE / "Tolstoj/Impaginato/Interno_STAMPA.pdf",
    "apologia-dell-ateismo.epub": RADICE / "Rensi/Epub pubblicato/Rensi_Apologia.epub",
    "per-la-soppressione-dei-partiti-politici.epub": RADICE / "Weil/Simone Weil - Per la soppressione dei partiti politici, a cura di Antonio Vigilante.epub",
    "nonviolenza-senza-miti.epub": RADICE / "Nonviolenza/Nonviolenza senza miti - Antonio Vigilante.epub",
}

LOGO = RADICE / "ateismo/logo.png"  # figura del marchio endehors (trasparente)
TEX_GYRE = Path.home() / "AppData/Local/Programs/MiKTeX/fonts/opentype/public/tex-gyre"


def copertine():
    dest = ASSETS / "copertine"
    dest.mkdir(parents=True, exist_ok=True)
    for slug, src in COPERTINE.items():
        if isinstance(src, tuple):
            with zipfile.ZipFile(src[1]) as z, z.open(src[2]) as f:
                im = Image.open(f)
                im.load()
        else:
            im = Image.open(src)
        im = im.convert("RGB")
        im.thumbnail((1000, 1500), Image.LANCZOS)
        im.save(dest / f"{slug}.jpg", quality=86, optimize=True, progressive=True)
        print("copertina", slug, im.size)


def logo():
    im = Image.open(LOGO).convert("RGBA")
    im = im.crop(im.getbbox())
    # rende nero puro il segno, mantenendo la trasparenza
    nero = Image.new("RGBA", im.size, (20, 20, 20, 0))
    nero.putalpha(im.getchannel("A"))
    alto = nero.copy()
    alto.thumbnail((480, 480), Image.LANCZOS)
    alto.save(ASSETS / "logo-endehors.png", optimize=True)
    # favicon: segno su fondo carta
    for size, nome in ((32, "favicon-32.png"), (180, "apple-touch-icon.png"), (512, "icon-512.png")):
        fondo = Image.new("RGBA", (size, size), (251, 249, 244, 255))
        segno = nero.copy()
        pad = int(size * 0.08)
        segno.thumbnail((size - 2 * pad, size - 2 * pad), Image.LANCZOS)
        fondo.alpha_composite(segno, ((size - segno.width) // 2, (size - segno.height) // 2))
        fondo.save(PUBLIC / nome, optimize=True)
    print("logo", alto.size)


def font():
    dest = PUBLIC / "font"
    dest.mkdir(parents=True, exist_ok=True)
    for peso in ("regular", "bold"):
        src = TEX_GYRE / f"texgyreadventor-{peso}.otf"
        out = dest / f"texgyreadventor-{peso}.woff"
        subprocess.run([
            sys.executable, "-m", "fontTools.subset", str(src),
            "--unicodes=U+0020-007E,U+00A0-017F,U+2010-2027,U+2030-203A,U+20AC",
            "--layout-features=*", "--flavor=woff", f"--output-file={out}",
        ], check=True)
        print("font", out.name, out.stat().st_size // 1024, "kB")


def download():
    dest = PUBLIC / "download"
    dest.mkdir(parents=True, exist_ok=True)
    for nome, src in DOWNLOAD.items():
        shutil.copyfile(src, dest / nome)
        print("download", nome, src.stat().st_size // 1024, "kB")


if __name__ == "__main__":
    copertine()
    logo()
    font()
    download()
