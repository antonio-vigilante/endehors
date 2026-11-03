import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

/** Schede dei libri: src/content/libri/<slug>.yaml */
const libri = defineCollection({
  loader: glob({ base: './src/content/libri', pattern: '*.yaml' }),
  schema: ({ image }) =>
    z.object({
      titolo: z.string(),
      sottotitolo: z.string().optional(),
      autore: z.string(),
      curatore: z.string().optional(),
      traduttore: z.string().optional(),
      ordine: z.number(),
      anno: z.number(),
      anno_originale: z.number().optional(),
      titolo_originale: z.string().optional(),
      copertina: image(),
      citazione: z.string(),
      descrizione: z.array(z.string()),
      note_autori: z.array(z.string()).optional(),
      licenza: z.object({
        nome: z.string(),
        url: z.string().url(),
        testo: z.string().optional(),
      }),
      edizione: z.string().optional(),
      crediti: z.string().optional(),
      formati: z.string().optional(),
      isbn: z.string().optional(),
      doi: z.string().optional(),
      acquista: z.string().url().optional(),
      download: z.object({
        epub: z.string().optional(),
        pdf: z.string().optional(),
      }),
    }),
});

/** Testi integrali: src/content/testi/<libro>/<NN>-<capitolo>.md */
const testi = defineCollection({
  loader: glob({ base: './src/content/testi', pattern: '**/*.md' }),
  schema: z.object({
    titolo: z.string(),
    numero: z.string().optional(),
    sottotitolo: z.string().optional(),
    autore: z.string().optional(),
    /** apparato = testi del curatore; testo = l'opera; bibliografia */
    tipo: z.enum(['apparato', 'testo', 'bibliografia']).default('testo'),
    ordine: z.number(),
  }),
});

export const collections = { libri, testi };
