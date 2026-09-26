// @ts-check
import { defineConfig } from 'astro/config';

// 100% free + portabile: sito statico puro, nessun adattatore server.
// GitHub Pages progetto: il sito vive su https://aledamelio.github.io/website/
// -> site deve includere il progetto (canonical/OG), base '/' cosi' i file
// restano alla radice di dist/ e il deploy pubblica index.html in /website/.
// Il prefisso /website/ sui link interni e' gestito da <base> in Base.astro.
// Se migrerai su server custom o su apex, cambia `site` (e <base href>) qui
// e ricostruisci: npm run build -> dist/ è copiabile via rsync/scp ovunque.
export default defineConfig({
  site: 'https://aledamelio.github.io/website',
  base: '/',
  output: 'static',
  build: {
    inlineStylesheets: 'auto',
  },
});
