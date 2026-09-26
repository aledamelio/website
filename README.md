# Alessandro D'Amelio — Sito Personale (Astro, 100% free & portabile)

Sito statico minimal per GitHub Pages (apex `aledamelio.github.io`), con aggiornamento automatico pubblicazioni via ORCID/OpenAlex e gestione manuale news in Markdown.

**Requisiti rispettati:**
- **Costo 0**: solo GitHub Pages (repo pubblico) + OpenAlex/Crossref gratis. Nessun dominio a pagamento, nessun storage esterno.
- **Copia esatta in locale**: tutto in `wesite/` — `npm run dev` / `npm run build` funziona offline. `dist/` è copiabile via `rsync`/`scp` su qualsiasi server Apache/Nginx/VPS senza modifiche.
- **Scholar proxy**: Google Scholar non ha API ufficiali. Si usa ORCID `0000-0002-8210-4457` → OpenAlex (39 lavori al 2026) + Crossref fallback, con link Scholar per ogni titolo.

## Avvio locale

```bash
npm install
npm run dev      # http://localhost:4321
npm run build    # genera dist/
npm run preview  # serve dist/ come farebbe GitHub Pages / Apache
```

## Struttura

```
src/layouts/Base.astro      # layout + SEO + schema.org Person
src/pages/index.astro       # Home (hero, highlights, latest news, selected pubs)
src/pages/publications.astro # lista completa auto-aggiornata
src/pages/teaching.astro    # corsi + tesi
src/pages/news.astro        # usa src/content/news/*.md
src/content/news/*.md       # <--- aggiungi qui le news
src/data/publications.json  # generato da scripts/fetch_pubs.py (non editare a mano)
scripts/fetch_pubs.py       # fetcher OpenAlex/Crossref
.github/workflows/deploy.yml            # build+deploy su push main
.github/workflows/update-publications.yml # cron weekly auto-update pubs
public/assets/profile.jpg   # <--- metti qui foto reale
public/assets/cv.pdf        # <--- metti qui CV
```

## Aggiungere una news

Crea `src/content/news/2026-09-06-titolo.md`:

```md
---
title: "Titolo news"
date: 2026-09-06
tags: ["paper", "workshop"]
pinned: false
---

Testo in **Markdown**. Link, liste, ecc.
```

Poi `git add . && git commit -m "news: ..." && git push` — il deploy è automatico in ~60s.

## Aggiornare pubblicazioni manualmente

```bash
python3 scripts/fetch_pubs.py        # rigenera src/data/publications.json da OpenAlex
# oppure modifica a mano src/data/publications.json e commit
```

L'Action `update-publications` fa lo stesso ogni lunedì alle 03:00 UTC e committa se ci sono differenze. Per disabilitare: commenta `schedule` in `.github/workflows/update-publications.yml`.

## Deploy su GitHub Pages (gratis)

1. Crea repo pubblico `aledamelio.github.io` su GitHub (se non esiste).
2. Da questa cartella:
   ```bash
   git init
   git add .
   git commit -m "init site"
   git branch -M main
   git remote add origin https://github.com/aledamelio/aledamelio.github.io.git
   git push -u origin main
   ```
3. Su GitHub: Settings → Pages → Source: **GitHub Actions** (non branch). Il workflow `deploy.yml` pubblicherà automaticamente.
4. URL finale: `https://aledamelio.github.io` (o con dominio custom se un giorno lo configurerai in `astro.config.mjs` → `site`).

## Migrare su server proprio (portabilità)

```bash
npm run build
rsync -av dist/ user@tuoserver:/var/www/html/
# oppure
scp -r dist/* user@tuoserver:/var/www/html/
```

`dist/` contiene solo HTML/CSS statici, funziona su Apache/Nginx senza configurazioni. Per cambiare dominio, modifica solo `site:` in `astro.config.mjs` e ricostruisci.

## Foto e CV

Sostituisci `public/assets/profile.jpg` e `public/assets/cv.pdf` con i tuoi file reali. Mantieni nomi identici — il sito li referenzia come `/assets/profile.jpg`.

## Note su Scholar vs OpenAlex

- Scholar (`chkawtoAAAAJ`, 796 citazioni) non espone API → scraping richiederebbe SerpAPI a pagamento e violerebbe ToS.
- OpenAlex/Crossref sono open, legali, completi per metadata. I conteggi citazioni sono leggermente diversi ma correlati; ogni pub ha link "Scholar" per verifica diretta su Scholar.

## Licenza

MIT — riutilizzabile.
