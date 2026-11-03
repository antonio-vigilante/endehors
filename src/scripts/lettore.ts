/**
 * Strumenti del lettore endehors.
 * Tutto è un miglioramento progressivo: senza JavaScript il testo resta
 * leggibile, con le note in fondo al capitolo e i collegamenti funzionanti.
 */
import { leggiPosizione, salvaPosizione } from './posizione';

const radice = document.documentElement;
const CHIAVE_PREF = 'endehors:preferenze';

// ---------------------------------------------------------------------------
// Utilità
// ---------------------------------------------------------------------------
let timerAvviso: number | undefined;
function avviso(testo: string, azione?: { etichetta: string; fn: () => void }, durata = 3200) {
  document.querySelector('.avviso')?.remove();
  const el = document.createElement('div');
  el.className = 'avviso';
  el.setAttribute('role', 'status');
  el.textContent = testo;
  if (azione) {
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = azione.etichetta;
    b.addEventListener('click', () => {
      azione.fn();
      el.remove();
    });
    el.append(b);
  }
  document.body.append(el);
  clearTimeout(timerAvviso);
  timerAvviso = window.setTimeout(() => el.remove(), durata);
}

async function copia(testo: string, html?: string) {
  try {
    if (html && 'ClipboardItem' in window) {
      await navigator.clipboard.write([
        new ClipboardItem({
          'text/plain': new Blob([testo], { type: 'text/plain' }),
          'text/html': new Blob([html], { type: 'text/html' }),
        }),
      ]);
    } else {
      await navigator.clipboard.writeText(testo);
    }
    return true;
  } catch {
    const t = document.createElement('textarea');
    t.value = testo;
    t.style.position = 'fixed';
    t.style.opacity = '0';
    document.body.append(t);
    t.select();
    const ok = document.execCommand('copy');
    t.remove();
    return ok;
  }
}

const escape = (s: string) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]!);

// ---------------------------------------------------------------------------
// Preferenze di lettura
// ---------------------------------------------------------------------------
function preferenze(dopo: () => void) {
  const leggi = (): Record<string, string> => {
    try {
      return JSON.parse(localStorage.getItem(CHIAVE_PREF) || '{}');
    } catch {
      return {};
    }
  };
  const aggiorna = () => {
    document.querySelectorAll<HTMLElement>('[data-pref]').forEach((g) => {
      const k = g.dataset.pref!;
      const v = radice.dataset[k] ?? '';
      g.querySelectorAll<HTMLButtonElement>('button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.valore === v)));
    });
  };
  document.querySelectorAll<HTMLElement>('[data-pref]').forEach((g) => {
    g.addEventListener('click', (e) => {
      const b = (e.target as HTMLElement).closest('button');
      if (!b) return;
      const k = g.dataset.pref!;
      const v = b.dataset.valore ?? '';
      const p = leggi();
      if (v) {
        radice.dataset[k] = v;
        p[k] = v;
      } else {
        delete radice.dataset[k];
        delete p[k];
      }
      try {
        localStorage.setItem(CHIAVE_PREF, JSON.stringify(p));
      } catch {}
      aggiorna();
      dopo();
    });
  });
  aggiorna();
}

// ---------------------------------------------------------------------------
// Pannelli laterali
// ---------------------------------------------------------------------------
function pannelli() {
  const velo = document.querySelector<HTMLElement>('.velo')!;
  let aperto: HTMLElement | null = null;
  let origine: HTMLElement | null = null;

  const chiudi = () => {
    if (!aperto) return;
    aperto.hidden = true;
    velo.hidden = true;
    document.querySelectorAll('[data-apri]').forEach((b) => b.setAttribute('aria-expanded', 'false'));
    aperto = null;
    origine?.focus();
  };
  const apri = (nome: string, da?: HTMLElement) => {
    const p = document.getElementById(`pannello-${nome}`);
    if (!p) return;
    if (aperto === p) return chiudi();
    chiudi();
    p.hidden = false;
    velo.hidden = false;
    aperto = p;
    origine = da ?? null;
    document.querySelector(`[data-apri="${nome}"]`)?.setAttribute('aria-expanded', 'true');
    (p.querySelector('.corrente a, .qui, [aria-pressed="true"]') as HTMLElement | null)?.scrollIntoView({ block: 'center' });
    p.querySelector<HTMLElement>('[data-chiudi]')?.focus();
  };

  document.querySelectorAll<HTMLElement>('[data-apri]').forEach((b) => b.addEventListener('click', () => apri(b.dataset.apri!, b)));
  document.querySelectorAll('[data-chiudi]').forEach((b) => b.addEventListener('click', chiudi));
  velo.addEventListener('click', chiudi);
  // chiudi l'indice quando si sceglie una sezione dello stesso capitolo
  document.getElementById('pannello-indice')?.addEventListener('click', (e) => {
    const a = (e.target as HTMLElement).closest('a');
    if (a && a.getAttribute('href')?.startsWith('#')) chiudi();
  });
  return { apri, chiudi, aperto: () => aperto };
}

// ---------------------------------------------------------------------------
// Barra: si nasconde scorrendo in giù, mostra l'avanzamento
// ---------------------------------------------------------------------------
function barra(testo: HTMLElement) {
  const b = document.querySelector<HTMLElement>('.barra')!;
  const av = document.querySelector<HTMLElement>('.avanzamento')!;
  let ultimo = scrollY;
  let richiesto = false;
  const aggiorna = () => {
    richiesto = false;
    const y = scrollY;
    const fine = testo.offsetTop + testo.offsetHeight - innerHeight;
    av.style.transform = `scaleX(${Math.min(1, Math.max(0, y / Math.max(1, fine)))})`;
    if (Math.abs(y - ultimo) > 6) {
      b.classList.toggle('nascosta', y > ultimo && y > 200);
      ultimo = y;
    }
  };
  addEventListener('scroll', () => {
    if (!richiesto) {
      richiesto = true;
      requestAnimationFrame(aggiorna);
    }
  }, { passive: true });
  aggiorna();
}

// ---------------------------------------------------------------------------
// Note: a margine (schermi larghi) o a comparsa
// ---------------------------------------------------------------------------
function note(testo: HTMLElement) {
  const corpo = testo.querySelector<HTMLElement>('.corpo')!;
  const margine = testo.querySelector<HTMLElement>('.margine')!;
  const contenuti = new Map<string, string>();
  testo.querySelectorAll<HTMLLIElement>('.note-capitolo li[data-nota]').forEach((li) => {
    const c = li.cloneNode(true) as HTMLElement;
    c.querySelectorAll('a.ritorno').forEach((a) => a.remove());
    contenuti.set(li.dataset.nota!, c.innerHTML.trim());
  });
  const rimandi = [...corpo.querySelectorAll<HTMLAnchorElement>('a.rimando')];
  if (!rimandi.length) return { ricalcola: () => {} };

  let aMargine = false;
  const notaMargine = new Map<string, HTMLElement>();

  const ricalcola = () => {
    const spazio = (innerWidth - testo.offsetWidth) / 2;
    aMargine = radice.dataset.note !== 'comparsa' && spazio >= 21 * 16;
    testo.classList.toggle('con-margine', aMargine);
    margine.replaceChildren();
    notaMargine.clear();
    if (!aMargine) return;
    const base = testo.getBoundingClientRect().top;
    let fondo = 0;
    for (const r of rimandi) {
      const label = r.dataset.nota!;
      if (notaMargine.has(label)) continue;
      const el = document.createElement('div');
      el.className = 'nota-margine';
      el.innerHTML = `<span class="n">${escape(label)}</span>${contenuti.get(label) ?? ''}`;
      // il primo paragrafo della nota prosegue sulla riga del numero
      const primo = el.querySelector('p');
      if (primo) {
        primo.prepend(el.querySelector('.n')!);
      }
      margine.append(el);
      const top = Math.max(r.getBoundingClientRect().top - base - 2, fondo);
      el.style.top = `${top}px`;
      fondo = top + el.offsetHeight + 14;
      notaMargine.set(label, el);
    }
  };

  // evidenziazione reciproca rimando ↔ nota
  const evidenzia = (label: string | undefined, on: boolean) => {
    if (!label) return;
    notaMargine.get(label)?.classList.toggle('attivo', on);
    rimandi.filter((r) => r.dataset.nota === label).forEach((r) => r.classList.toggle('attivo', on));
  };
  corpo.addEventListener('mouseover', (e) => evidenzia((e.target as HTMLElement).closest<HTMLElement>('a.rimando')?.dataset.nota, true));
  corpo.addEventListener('mouseout', (e) => evidenzia((e.target as HTMLElement).closest<HTMLElement>('a.rimando')?.dataset.nota, false));
  margine.addEventListener('mouseover', (e) => {
    const n = (e.target as HTMLElement).closest<HTMLElement>('.nota-margine');
    if (n) evidenzia([...notaMargine].find(([, v]) => v === n)?.[0], true);
  });
  margine.addEventListener('mouseout', (e) => {
    const n = (e.target as HTMLElement).closest<HTMLElement>('.nota-margine');
    if (n) evidenzia([...notaMargine].find(([, v]) => v === n)?.[0], false);
  });

  // fumetto
  let fumetto: HTMLElement | null = null;
  const chiudiFumetto = () => {
    fumetto?.remove();
    fumetto = null;
    rimandi.forEach((r) => r.classList.remove('attivo'));
  };
  const apriFumetto = (r: HTMLAnchorElement) => {
    chiudiFumetto();
    const label = r.dataset.nota!;
    const el = document.createElement('div');
    el.className = 'fumetto';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-label', `Nota ${label}`);
    el.innerHTML = `<div class="contenuto"><span class="n">${escape(label)}</span>${contenuti.get(label) ?? ''}</div>
      <div class="piede-fumetto"><a href="#fn-${encodeURIComponent(label)}">Tutte le note del capitolo ↓</a><button type="button">Chiudi</button></div>`;
    const primo = el.querySelector('.contenuto p');
    if (primo) primo.prepend(el.querySelector('.contenuto .n')!);
    el.querySelector('button')!.addEventListener('click', chiudiFumetto);
    el.querySelector('.piede-fumetto a')!.addEventListener('click', () => {
      testo.classList.remove('con-margine');
      chiudiFumetto();
    });
    document.body.append(el);
    const rr = r.getBoundingClientRect();
    const larghezza = el.offsetWidth;
    el.style.left = `${Math.min(Math.max(8, rr.left + scrollX - 24), scrollX + innerWidth - larghezza - 8)}px`;
    el.style.top = `${rr.bottom + scrollY + 8}px`;
    r.classList.add('attivo');
    fumetto = el;
  };

  corpo.addEventListener('click', (e) => {
    const r = (e.target as HTMLElement).closest<HTMLAnchorElement>('a.rimando');
    if (!r) return;
    e.preventDefault();
    if (aMargine) {
      const n = notaMargine.get(r.dataset.nota!);
      if (n) {
        n.classList.add('attivo');
        n.animate([{ background: 'var(--evidenza)' }, { background: 'transparent' }], { duration: 1600 });
        setTimeout(() => n.classList.remove('attivo'), 1600);
      }
    } else if (fumetto && r.classList.contains('attivo')) {
      chiudiFumetto();
    } else {
      apriFumetto(r);
    }
  });
  document.addEventListener('click', (e) => {
    if (fumetto && !fumetto.contains(e.target as Node) && !(e.target as HTMLElement).closest('a.rimando')) chiudiFumetto();
  });

  new ResizeObserver(() => requestAnimationFrame(ricalcola)).observe(testo);
  document.fonts?.ready.then(ricalcola);
  ricalcola();
  return { ricalcola, chiudiFumetto, haFumetto: () => !!fumetto };
}

// ---------------------------------------------------------------------------
// Paragrafi: copia il collegamento; citazione dalla selezione
// ---------------------------------------------------------------------------
function paragrafi(testo: HTMLElement) {
  const corpo = testo.querySelector<HTMLElement>('.corpo')!;
  const base = testo.dataset.url!;
  const citazione = testo.dataset.citazione!;

  corpo.addEventListener('click', async (e) => {
    if ((e.target as HTMLElement).closest('a')) return;
    const p = (e.target as HTMLElement).closest<HTMLElement>('.corpo > [data-p]');
    if (!p || e.clientX >= p.getBoundingClientRect().left) return;
    const n = p.dataset.p;
    history.replaceState(null, '', `#p-${n}`);
    p.classList.remove('lampeggia');
    void p.offsetWidth;
    p.classList.add('lampeggia');
    if (await copia(`${base}#p-${n}`)) avviso(`Collegamento al § ${n} copiato`);
  });

  // pulsante "Copia citazione" sulla selezione
  let bottone: HTMLButtonElement | null = null;
  const togli = () => {
    bottone?.remove();
    bottone = null;
  };
  const mostra = () => {
    const sel = getSelection();
    const t = sel?.toString().replace(/\s+/g, ' ').trim() ?? '';
    if (!sel || sel.isCollapsed || t.length < 4 || !corpo.contains(sel.anchorNode)) return togli();
    const range = sel.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    if (!bottone) {
      bottone = document.createElement('button');
      bottone.type = 'button';
      bottone.className = 'cita-selezione';
      bottone.textContent = 'Copia citazione';
      bottone.addEventListener('mousedown', (ev) => ev.preventDefault());
      bottone.addEventListener('click', async () => {
        const s = getSelection();
        const testoSel = s?.toString().replace(/\s+/g, ' ').trim() ?? '';
        const nodo = s?.anchorNode instanceof Element ? s.anchorNode : s?.anchorNode?.parentElement;
        const n = nodo?.closest<HTMLElement>('.corpo > [data-p]')?.dataset.p;
        const dove = n ? `, § ${n}` : '';
        const link = n ? `${base}#p-${n}` : base;
        const piano = `«${testoSel}» (${citazione}${dove}, ${link}).`;
        const html = `«${escape(testoSel)}» (${escape(citazione)}${dove}, <a href="${link}">${link}</a>).`;
        if (await copia(piano, html)) avviso('Citazione copiata, con il riferimento');
        togli();
      });
      document.body.append(bottone);
    }
    bottone.style.left = `${rect.left + rect.width / 2 + scrollX}px`;
    bottone.style.top = `${rect.top + scrollY}px`;
  };
  let t: number | undefined;
  document.addEventListener('selectionchange', () => {
    clearTimeout(t);
    t = window.setTimeout(mostra, 220);
  });
}

// ---------------------------------------------------------------------------
// Sezioni: evidenzia nell'indice la sezione in lettura
// ---------------------------------------------------------------------------
function sezioni(testo: HTMLElement) {
  const titoli = [...testo.querySelectorAll<HTMLElement>('.corpo > h2[id]')];
  if (!titoli.length) return;
  const link = new Map([...document.querySelectorAll<HTMLAnchorElement>('[data-sezione]')].map((a) => [a.dataset.sezione!, a]));
  const aggiorna = () => {
    let attuale: string | undefined;
    for (const h of titoli) if (h.getBoundingClientRect().top < innerHeight * 0.3) attuale = h.id;
    link.forEach((a, id) => a.classList.toggle('qui', id === attuale));
  };
  addEventListener('scroll', aggiorna, { passive: true });
  aggiorna();
}

// ---------------------------------------------------------------------------
// Posizione di lettura
// ---------------------------------------------------------------------------
function posizione(testo: HTMLElement) {
  const libro = testo.dataset.libro!;
  const url = location.pathname;
  const titolo = testo.dataset.titoloCapitolo!;
  const blocchi = [...testo.querySelectorAll<HTMLElement>('.corpo > [data-p]')];
  const corrente = () => {
    const b = blocchi.find((el) => el.getBoundingClientRect().bottom > 90);
    return b ? Number(b.dataset.p) : 1;
  };

  const salvata = leggiPosizione(libro);
  if (!location.hash && salvata && salvata.url === url && salvata.p > 3) {
    avviso(
      `Eri arrivato al § ${salvata.p}`,
      {
        etichetta: 'Riprendi',
        fn: () => document.getElementById(`p-${salvata.p}`)?.scrollIntoView({ block: 'start' }),
      },
      9000,
    );
  }

  let t: number | undefined;
  const salva = () => salvaPosizione(libro, { url, titolo, p: corrente(), ts: Date.now() });
  addEventListener('scroll', () => {
    clearTimeout(t);
    t = window.setTimeout(salva, 800);
  }, { passive: true });
  // registra comunque l'apertura del capitolo
  if (!salvata || salvata.url !== url) salva();
}

// ---------------------------------------------------------------------------
// Scorciatoie da tastiera
// ---------------------------------------------------------------------------
function tastiera(testo: HTMLElement, p: ReturnType<typeof pannelli>, n: ReturnType<typeof note>) {
  addEventListener('keydown', (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const t = e.target as HTMLElement;
    if (t.closest('input, textarea, select, [contenteditable]')) return;
    if (e.key === 'Escape') {
      p.chiudi();
      (n as any).chiudiFumetto?.();
      return;
    }
    if (p.aperto()) return;
    if (e.key === 'ArrowRight' && testo.dataset.succ) location.href = testo.dataset.succ;
    else if (e.key === 'ArrowLeft' && testo.dataset.prec) location.href = testo.dataset.prec;
    else if (e.key === 'i') p.apri('indice');
    else if (e.key === '/') {
      e.preventDefault();
      location.href = `/cerca/?libro=${testo.dataset.libro}`;
    } else if (e.key === 'n') {
      const sez = testo.querySelector<HTMLElement>('.note-capitolo');
      if (sez) {
        testo.classList.remove('con-margine');
        sez.scrollIntoView({ block: 'start' });
      }
    }
  });
}

// ---------------------------------------------------------------------------
export function avviaLettore() {
  const testo = document.getElementById('testo');
  if (!testo) return;
  const n = note(testo);
  preferenze(() => n.ricalcola());
  const p = pannelli();
  barra(testo);
  paragrafi(testo);
  sezioni(testo);
  posizione(testo);
  tastiera(testo, p, n);
}
