// @ts-check
import { defineConfig } from 'astro/config';
import rehypeEndehors from './src/lib/rehype-endehors.mjs';

// https://astro.build/config
export default defineConfig({
  // Indirizzo pubblico del sito: serve per i link canonici e le citazioni.
  site: 'https://endehors.example.org',
  trailingSlash: 'always',
  build: { format: 'directory' },
  markdown: {
    // i testi hanno già la tipografia corretta (virgolette, apostrofi, lineette)
    smartypants: false,
    remarkRehype: {
      footnoteLabel: 'Note',
      footnoteBackLabel: 'Torna al testo',
      clobberPrefix: '',
    },
    rehypePlugins: [rehypeEndehors],
  },
});
