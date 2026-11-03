import { getCollection, type CollectionEntry } from 'astro:content';
import { parse } from 'node-html-parser';

export type Libro = CollectionEntry<'libri'>;
export type Capitolo = CollectionEntry<'testi'>;

/** Capitolo con le informazioni di navigazione già calcolate */
export interface Voce {
  entry: Capitolo;
  libro: string;
  slug: string;
  url: string;
  titolo: string;
  etichetta: string; // "Capitolo I", "3", "Introduzione"...
  indice: number;
  sezioni: { id: string; testo: string }[];
}

export const urlLibro = (slug: string) => `/libri/${slug}/`;

/** Converte il markdown "in linea" usato nelle schede (*corsivo*) in HTML */
export function inline(md = ''): string {
  return md
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>');
}

export const senzaMarkup = (md = '') => md.replace(/\*/g, '');

export async function getLibri(): Promise<Libro[]> {
  const libri = await getCollection('libri');
  return libri.sort((a, b) => a.data.ordine - b.data.ordine);
}

/** Nome (con eventuale numero) da mostrare per un capitolo */
export function etichettaCapitolo(c: Capitolo): string {
  const n = c.data.numero;
  if (!n) return c.data.titolo;
  if (/^[IVXLC]+$/.test(n) || /^\d+$/.test(n)) return `${n}. ${c.data.titolo}`;
  return `${n}. ${c.data.titolo}`;
}

const cache = new Map<string, Voce[]>();

export async function getCapitoli(libro: string): Promise<Voce[]> {
  if (cache.has(libro)) return cache.get(libro)!;
  const tutti = await getCollection('testi', (e) => e.id.startsWith(`${libro}/`));
  const voci = tutti
    .sort((a, b) => a.data.ordine - b.data.ordine)
    .map((entry, i): Voce => {
      const slug = entry.id.split('/').pop()!.replace(/^\d+-/, '');
      const headings = (entry.rendered?.metadata?.headings ?? []) as { depth: number; slug: string; text: string }[];
      return {
        entry,
        libro,
        slug,
        url: `/libri/${libro}/${slug}/`,
        titolo: entry.data.titolo,
        etichetta: entry.data.numero ?? '',
        indice: i,
        sezioni: headings.filter((h) => h.depth === 2 && h.slug !== 'footnote-label').map((h) => ({ id: h.slug, testo: h.text })),
      };
    });
  cache.set(libro, voci);
  return voci;
}

// ---------------------------------------------------------------------------
// Note
// ---------------------------------------------------------------------------
export interface Nota {
  label: string;
  html: string;
  testo: string;
  curatore: boolean; // nota del curatore / traduttore
  capitolo: Voce;
  url: string; // rimando nel testo
}

const CURATORE = /\b(N\.?\s?d\.?\s?[CTR]\.?|NdC|NdT)\b/;

export async function getNote(libro: string): Promise<Nota[]> {
  const voci = await getCapitoli(libro);
  const note: Nota[] = [];
  for (const v of voci) {
    const html = v.entry.rendered?.html ?? '';
    if (!html.includes('note-capitolo')) continue;
    const root = parse(html);
    for (const li of root.querySelectorAll('section.note-capitolo li')) {
      li.querySelectorAll('a.ritorno').forEach((a) => a.remove());
      const label = li.getAttribute('data-nota') ?? '';
      const interno = li.innerHTML.trim().replace(/^<p>([\s\S]*)<\/p>$/, '$1');
      const testo = li.textContent.replace(/\s+/g, ' ').trim();
      note.push({
        label,
        html: interno,
        testo,
        curatore: CURATORE.test(testo),
        capitolo: v,
        url: `${v.url}#fnref-${label}`,
      });
    }
  }
  return note;
}

/** Parole di un testo html (per tempi di lettura) */
export function parole(html: string): number {
  return html.replace(/<[^>]+>/g, ' ').split(/\s+/).filter(Boolean).length;
}

export function tempoLettura(n: number): string {
  const min = Math.max(1, Math.round(n / 230));
  if (min < 60) return `${min} min`;
  const h = Math.floor(min / 60);
  const m = min % 60;
  return m ? `${h} h ${m} min` : `${h} h`;
}
