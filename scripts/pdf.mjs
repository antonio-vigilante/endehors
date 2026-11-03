/**
 * Genera i PDF dei libri che non hanno un PDF impaginato, stampando con
 * Chrome headless la pagina "testo integrale" del sito.
 *
 * Uso (dopo `npm run build`):
 *   npm run pdf                 # solo i PDF mancanti in public/download
 *   npm run pdf -- --tutti      # rigenera tutti i PDF (anche quelli impaginati!)
 *   npm run pdf -- nonviolenza-senza-miti
 *
 * Variabile CHROME: percorso dell'eseguibile di Chrome/Chromium (facoltativa).
 */
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { existsSync, readdirSync, copyFileSync, mkdirSync } from 'node:fs';
import { join, resolve, normalize, extname } from 'node:path';

const SITO = resolve(import.meta.dirname, '..');
const DIST = join(SITO, 'dist');
const PUBLIC_DL = join(SITO, 'public', 'download');
const PORTA = 4331;

const CANDIDATI = [
  process.env.CHROME,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium',
].filter(Boolean);
const chrome = CANDIDATI.find((p) => existsSync(p));
if (!chrome) {
  console.error('Chrome non trovato: indica il percorso con la variabile CHROME.');
  process.exit(1);
}
if (!existsSync(join(DIST, 'libri'))) {
  console.error('Manca la cartella dist: esegui prima `npm run build`.');
  process.exit(1);
}

const argomenti = process.argv.slice(2);
const tutti = argomenti.includes('--tutti');
const scelti = argomenti.filter((a) => !a.startsWith('--'));
const libri = readdirSync(join(DIST, 'libri')).filter((s) => existsSync(join(DIST, 'libri', s, 'integrale', 'index.html')));
const daFare = libri.filter((s) => (scelti.length ? scelti.includes(s) : tutti || !existsSync(join(PUBLIC_DL, `${s}.pdf`))));

if (!daFare.length) {
  console.log('Nessun PDF da generare (usa --tutti per rigenerarli).');
  process.exit(0);
}

// piccolo server statico per la cartella dist
const TIPI = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.woff': 'font/woff', '.woff2': 'font/woff2', '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml' };
const server = createServer(async (req, res) => {
  try {
    let percorso = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    if (percorso.endsWith('/')) percorso += 'index.html';
    const file = join(DIST, normalize(percorso));
    if (!file.startsWith(DIST)) throw new Error();
    const dati = await readFile(file);
    res.writeHead(200, { 'content-type': TIPI[extname(file)] ?? 'application/octet-stream' });
    res.end(dati);
  } catch {
    res.writeHead(404);
    res.end();
  }
});
await new Promise((r) => server.listen(PORTA, '127.0.0.1', r));

const stampa = (url, out) =>
  new Promise((ok, ko) => {
    const p = spawn(chrome, [
      '--headless=new',
      '--disable-gpu',
      '--no-pdf-header-footer',
      '--run-all-compositor-stages-before-draw',
      '--virtual-time-budget=15000',
      `--print-to-pdf=${out}`,
      url,
    ], { stdio: 'ignore' });
    p.on('exit', (c) => (c === 0 ? ok() : ko(new Error(`Chrome è uscito con codice ${c}`))));
  });

try {
  mkdirSync(PUBLIC_DL, { recursive: true });
  mkdirSync(join(DIST, 'download'), { recursive: true });
  for (const slug of daFare) {
    const out = join(PUBLIC_DL, `${slug}.pdf`);
    process.stdout.write(`PDF ${slug}… `);
    await stampa(`http://127.0.0.1:${PORTA}/libri/${slug}/integrale/`, out);
    copyFileSync(out, join(DIST, 'download', `${slug}.pdf`));
    console.log('fatto');
  }
} finally {
  server.close();
}
