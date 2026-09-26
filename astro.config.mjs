// @ts-check
import { defineConfig } from 'astro/config';

// 100% free + portabile: sito statico puro, nessun adattatore server.
// Per GitHub Pages apex (aledamelio.github.io) -> site apex, base /
// Se migrerai su server custom o sottocartella, cambia solo `site` qui
// e ricostruisci: npm run build -> dist/ è copiabile via rsync/scp ovunque.
export default defineConfig({
  site: 'https://aledamelio.github.io',
  base: '/website',
  output: 'static',
  build: {
    inlineStylesheets: 'auto',
  },
});
