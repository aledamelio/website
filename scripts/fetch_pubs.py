#!/usr/bin/env python3
"""
Fetch publications for Alessandro D'Amelio via ORCID as source of truth,
enriched with Crossref (and OpenAlex fallback).
- Primary: ORCID Public API (https://pub.orcid.org/v3.0/{orcid}/works) -> all public works, including eid-only Scopus entries
- Enrich: Crossref by DOI for authors/venue/citations; fallback to ORCID metadata if no DOI
- Also merge OpenAlex for cited_by_count when Crossref lacks it
Output: src/data/publications.json (sorted by year desc)
Keeps 100% free, no key, portable.
"""
import json, sys, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path

ORCID = "0000-0002-8210-4457"
OUT = Path(__file__).parent.parent / "src" / "data" / "publications.json"
HEADERS_JSON = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (mailto:alessandro.damelio@unimi.it) fetch_pubs.py",
}

def http_get_json(url, headers=HEADERS_JSON, timeout=30):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def fetch_orcid_groups(orcid=ORCID):
    url = f"https://pub.orcid.org/v3.0/{orcid}/works"
    print(f"[fetch] ORCID: {url}")
    data = http_get_json(url)
    groups = data.get("group", [])
    print(f"[ok] ORCID returned {len(groups)} groups")
    # Each group is a work with multiple put-codes; we take the preferred (display-index 1) or first
    works = []
    seen_doi = set()
    seen_eid = set()
    for g in groups:
        summaries = g.get("work-summary", [])
        if not summaries:
            continue
        # Prefer display-index smallest, else first; also prefer Crossref/Scopus with DOI
        # Pick the one with DOI if available
        chosen = None
        for s in summaries:
            eids = (s.get("external-ids") or {}).get("external-id", [])
            has_doi = any(e.get("external-id-type") == "doi" for e in eids)
            if has_doi:
                chosen = s
                break
        if not chosen:
            chosen = summaries[0]
        title = ((chosen.get("title") or {}).get("title") or {}).get("value") or ""
        title = title.strip()
        if not title:
            continue
        # collect external ids from group level (more complete) + chosen
        ext_ids_group = (g.get("external-ids") or {}).get("external-id", [])
        ext_ids_chosen = (chosen.get("external-ids") or {}).get("external-id", [])
        # merge
        doi = None
        eid = None
        for e in ext_ids_group + ext_ids_chosen:
            t = e.get("external-id-type")
            v = e.get("external-id-value")
            if t == "doi" and not doi:
                doi = v
            if t == "eid" and not eid:
                eid = v
        # dedup by doi/eid
        key = (doi or eid or title.lower())[:200]
        if doi and doi in seen_doi:
            continue
        if eid and eid in seen_eid:
            # allow if doi different? but eid dup means same work
            # if doi present and already seen, skip
            if doi and doi not in seen_doi:
                pass
            else:
                continue
        if doi:
            seen_doi.add(doi)
        if eid:
            seen_eid.add(eid)
        pub_date = chosen.get("publication-date") or {}
        year = None
        y = pub_date.get("year") or {}
        if y and y.get("value"):
            try:
                year = int(y["value"])
            except:
                pass
        venue = (chosen.get("journal-title") or {}).get("value") or ""
        typ = chosen.get("type") or ""
        url_val = (chosen.get("url") or {}).get("value") or ""
        if not url_val and doi:
            url_val = f"https://doi.org/{doi}"
        works.append({
            "title": title,
            "doi": doi,
            "eid": eid,
            "year": year,
            "venue": venue,
            "type": typ,
            "url": url_val,
            "orcid_put_code": chosen.get("put-code"),
        })
    return works

def enrich_crossref(doi):
    if not doi:
        return None
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
    try:
        data = http_get_json(url, headers={"Accept":"application/json", "User-Agent": HEADERS_JSON["User-Agent"]})
        msg = data.get("message", {})
        title = (msg.get("title") or [""])[0]
        venue = (msg.get("container-title") or [""])[0] or (msg.get("short-container-title") or [""])[0]
        issued = (msg.get("issued") or {}).get("date-parts", [[]])[0]
        year = issued[0] if issued else None
        authors = ", ".join([f"{a.get('given','')} {a.get('family','')}".strip() for a in msg.get("author", [])][:12])
        cites = msg.get("is-referenced-by-count")
        typ = msg.get("type") or ""
        return {
            "title": title,
            "venue": venue,
            "year": int(year) if year else None,
            "authors": authors,
            "citations": cites,
            "type": typ,
        }
    except Exception as e:
        print(f"[warn] Crossref {doi}: {e}", file=sys.stderr)
        return None

def fetch_openalex_by_doi(doi):
    if not doi:
        return None
    url = f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}?mailto=alessandro.damelio@unimi.it"
    try:
        data = http_get_json(url)
        cites = data.get("cited_by_count")
        primary = data.get("primary_location") or {}
        pdf = primary.get("pdf_url") if isinstance(primary, dict) else None
        auths = data.get("authorships") or []
        authors = ", ".join([(a.get("author") or {}).get("display_name","") for a in auths][:12])
        return {"citations": cites, "pdf": pdf, "authors": authors}
    except Exception as e:
        print(f"[warn] OpenAlex doi {doi}: {e}", file=sys.stderr)
        return None

def main():
    out = OUT
    if len(sys.argv) > 2 and sys.argv[1] == "--out":
        out = Path(sys.argv[2])

    # 1) ORCID primary
    orcid_works = []
    try:
        orcid_works = fetch_orcid_groups()
    except Exception as e:
        print(f"[error] ORCID fetch failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not orcid_works:
        print("[error] No ORCID works returned", file=sys.stderr)
        sys.exit(1)

    pubs = []
    for w in orcid_works:
        doi = w.get("doi")
        # enrich
        cr = enrich_crossref(doi) if doi else None
        oa = fetch_openalex_by_doi(doi) if doi else None
        # tiny politeness delay to avoid 429
        time.sleep(0.15)

        title = (cr.get("title") if cr and cr.get("title") else w["title"])
        venue = (cr.get("venue") if cr and cr.get("venue") else w.get("venue") or "")
        year = (cr.get("year") if cr and cr.get("year") else w.get("year") or 0)
        # authors: prefer Crossref, else OpenAlex, else TBD
        authors = ""
        if cr and cr.get("authors"):
            authors = cr["authors"]
        elif oa and oa.get("authors"):
            authors = oa["authors"]
        else:
            authors = "TBD"

        cites = None
        if cr and cr.get("citations") is not None:
            cites = cr["citations"]
        if oa and oa.get("citations") is not None:
            # OpenAlex often more complete for citations; prefer max
            cites = max(cites or 0, oa["citations"]) if cites is not None else oa["citations"]

        typ = (cr.get("type") if cr and cr.get("type") else w.get("type") or "")
        url_val = w.get("url") or (f"https://doi.org/{doi}" if doi else None)
        pdf = (oa.get("pdf") if oa else None)

        pubs.append({
            "title": title,
            "authors": authors,
            "venue": venue,
            "year": int(year) if year else 0,
            "doi": doi,
            "url": url_val,
            "pdf": pdf,
            "citations": cites,
            "type": typ,
        })

    # dedup (ORCID already deduped, but keep safety)
    seen=set()
    uniq=[]
    for p in pubs:
        key=(p.get("doi") or p["title"].lower().strip())[:180]
        if key in seen:
            continue
        seen.add(key)
        uniq.append(p)
    uniq.sort(key=lambda x: (-(x["year"] or 0), x["title"]))

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and len(uniq) < 5:
        print(f"[warn] fetched only {len(uniq)} items, keeping existing file", file=sys.stderr)
        sys.exit(0)
    with open(out,"w", encoding="utf-8") as f:
        json.dump(uniq, f, ensure_ascii=False, indent=2)
    print(f"[done] wrote {len(uniq)} pubs to {out}")
    # quick check for the example paper
    found = [p for p in uniq if p["doi"]=="10.1080/10447318.2025.2561185"]
    if found:
        print(f"[check] FOUND example paper: {found[0]['title']} ({found[0]['year']})")
    else:
        print("[check] MISSING example paper 10.1080/10447318.2025.2561185", file=sys.stderr)

if __name__ == "__main__":
    main()
