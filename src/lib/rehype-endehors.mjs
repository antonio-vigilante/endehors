/**
 * Plugin rehype per i testi endehors.
 *
 * - I rimandi di nota mostrano l'etichetta originale (es. 23) invece della
 *   numerazione progressiva di GFM, così coincidono con le edizioni a stampa.
 * - Le note in fondo al capitolo riportano lo stesso numero (attributo value).
 * - I blocchi di testo di primo livello ricevono un numero di paragrafo
 *   (id="p-12"), che permette di citare e linkare un punto preciso.
 */
import { visit } from 'unist-util-visit';

const etichetta = (href = '') => decodeURIComponent(href.replace(/^#?fn-?/, ''));

const testoDi = (nodo) =>
  nodo.type === 'text' ? nodo.value : (nodo.children || []).map(testoDi).join('');

export default function rehypeEndehors() {
  return (tree) => {
    // 1. rimandi
    visit(tree, 'element', (node) => {
      if (node.tagName !== 'a' || node.properties?.dataFootnoteRef === undefined) return;
      const label = etichetta(String(node.properties.href || ''));
      node.children = [{ type: 'text', value: label }];
      node.properties.className = ['rimando'];
      node.properties.dataNota = label;
      node.properties.ariaLabel = `Nota ${label}`;
      delete node.properties.ariaDescribedBy;
    });

    // 2. note in fondo
    visit(tree, 'element', (node) => {
      if (node.tagName !== 'section' || node.properties?.dataFootnotes === undefined) return;
      node.properties.className = ['note-capitolo'];
      node.properties.ariaLabel = 'Note';
      visit(node, 'element', (li) => {
        if (li.tagName !== 'li') return;
        const label = etichetta(String(li.properties.id || ''));
        li.properties.dataNota = label;
        if (/^\d+$/.test(label)) li.properties.value = Number(label);
        visit(li, 'element', (a) => {
          if (a.tagName === 'a' && a.properties?.dataFootnoteBackref !== undefined) {
            a.properties.className = ['ritorno'];
            a.properties.dataPagefindIgnore = '';
            a.children = [{ type: 'text', value: '↩' }];
          }
        });
      });
    });

    // 3. numeri di paragrafo (solo blocchi di primo livello)
    let n = 0;
    for (const node of tree.children) {
      if (node.type !== 'element') continue;
      if (node.properties?.dataFootnotes !== undefined) continue;
      if (!['p', 'blockquote', 'ul', 'ol', 'div'].includes(node.tagName)) continue;
      if (!testoDi(node).trim()) continue;
      n += 1;
      node.properties.id = node.properties.id || `p-${n}`;
      node.properties.dataP = n;
    }
  };
}
