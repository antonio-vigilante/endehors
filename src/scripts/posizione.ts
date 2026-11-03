/** Memoria della posizione di lettura, per libro (localStorage) */
export interface Posizione {
  url: string;
  titolo: string;
  p: number;
  ts: number;
}

const chiave = (libro: string) => `endehors:posizione:${libro}`;

export function leggiPosizione(libro: string): Posizione | null {
  try {
    return JSON.parse(localStorage.getItem(chiave(libro)) || 'null');
  } catch {
    return null;
  }
}

export function salvaPosizione(libro: string, pos: Posizione) {
  try {
    localStorage.setItem(chiave(libro), JSON.stringify(pos));
  } catch {
    /* archiviazione non disponibile */
  }
}

/** Nella scheda del libro: "Riprendi la lettura da…" */
export function mostraRipresa() {
  document.querySelectorAll<HTMLElement>('[data-riprendi]').forEach((el) => {
    const pos = leggiPosizione(el.dataset.riprendi!);
    if (!pos) return;
    const a = document.createElement('a');
    a.href = pos.p > 1 ? `${pos.url}#p-${pos.p}` : pos.url;
    a.textContent = pos.titolo;
    el.append('Riprendi la lettura: ', a, pos.p > 1 ? `, § ${pos.p}` : '');
  });
}
