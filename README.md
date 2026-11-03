# endehors — sito

Sito statico (Astro) del progetto endehors: catalogo, testi integrali leggibili online, download in ePub e PDF.

## Comandi

| Comando | Cosa fa |
| --- | --- |
| `npm install` | installa le dipendenze |
| `npm run dev` | server di sviluppo su `localhost:4321` (la ricerca funziona solo dopo una build) |
| `npm run build` | genera il sito in `dist/` e l'indice di ricerca (Pagefind) |
| `npm run preview` | serve `dist/` in locale |
| `npm run pdf` | genera con Chrome i PDF mancanti dalla pagina "testo integrale" (dopo la build) |
| `npm run importa` | **reimporta** i testi dagli EPUB e rigenera copertine, logo, font e download |

Il sito pubblicato è la cartella `dist/`, da caricare su qualsiasi hosting statico (Netlify, GitHub Pages, un server qualsiasi). Prima di pubblicare, indica l'indirizzo vero in `site` dentro `astro.config.mjs`: serve per i link canonici e per le citazioni.

## Dove sono le cose

- `src/content/libri/<libro>.yaml`: scheda del libro (titolo, autori, citazione, descrizione, licenza, edizione, link d'acquisto, download, ordine nel catalogo).
- `src/content/testi/<libro>/NN-<capitolo>.md`: i testi, un file per capitolo. Il prefisso `NN` dà l'ordine, il resto del nome diventa l'indirizzo. Nell'intestazione: `titolo`, `numero`, `sottotitolo`, `autore`, `tipo` (`apparato` per i testi del curatore, `testo`, `bibliografia`).
  - Note: sintassi Markdown `testo[^12]` … `[^12]: testo della nota`. Il numero scritto è quello mostrato, così coincide con le edizioni a stampa.
  - Sezioni: `## Titolo`. Compaiono nell'indice e nel pannello di lettura.
  - Blocchi speciali: `<div class="epigrafe">`, `<div class="centro">`, `<div class="destra">` (lasciare una riga vuota dopo il tag di apertura e prima di quello di chiusura).
- `src/assets/copertine/`: copertine (1000 px di larghezza; Astro le ottimizza).
- `public/download/`: i file ePub e PDF scaricabili.
- `src/styles/global.css`: tutto lo stile. Colori e caratteri sono nelle variabili all'inizio del file.

## Aggiungere un libro

1. Crea `src/content/libri/<slug>.yaml` copiando una scheda esistente.
2. Metti la copertina in `src/assets/copertine/<slug>.jpg` e i file in `public/download/`.
3. Crea i capitoli in `src/content/testi/<slug>/`, oppure aggiungi il libro a `LIBRI` in `scripts/importa/importa.py` e lancia `python scripts/importa/importa.py <slug>`.
4. Esegui `npm run build`, poi `npm run pdf` se il libro non ha un PDF impaginato.

**Attenzione:** l'importatore sovrascrive `src/content/testi/<slug>/`. Dopo la prima importazione correggi direttamente i file Markdown.

## Strumenti di lettura

- Indice del libro con le sezioni del capitolo ed evidenziazione della sezione in lettura (tasto `i`).
- Note a margine sugli schermi larghi, in un riquadro a comparsa sugli schermi stretti, sempre anche in fondo al capitolo. Pagina con tutte le note del libro, con filtro di ricerca e filtro "note del curatore".
- Paragrafi numerati e linkabili (`#p-12`). Selezionando un passo si copia la citazione con il riferimento.
- Preferenze (pannello Aa): tema carta, seppia o notte; dimensione, interlinea, larghezza, allineamento; note a margine o a comparsa; numeri di paragrafo.
- Memoria della posizione di lettura per ciascun libro. Capitolo precedente e successivo con `←` e `→`.
- Ricerca a testo pieno (Pagefind) filtrabile per libro.
- Testo integrale in una pagina, pensato anche per la stampa.

## Caratteri

- Testo: Georgia (di sistema).
- Titoli: TeX Gyre Adventor (GUST Font License, libera), affine al Century Gothic delle copertine. File in `public/font/`.
- Marchio: IM Fell DW Pica (OFL), come sulle copertine.
