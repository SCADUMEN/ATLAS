# site/ — the indexable documentation site

`deploy-pages.yml` used to copy the Markdown sources to the server as-is. With
`.nojekyll` set, GitHub Pages served them at their own extension, and a live
check confirmed what that meant:

```
GET /ATLAS/README.md      200  text/markdown; charset=utf-8   18416 bytes
GET /ATLAS/robots.txt     404
GET /ATLAS/sitemap.xml    404
```

Search engines index HTML. They do not index `text/markdown`. The whole
published corpus — fifteen documents — was reachable by a browser and
invisible to a crawler, with one exception: the workflow's inline
`index.html`, 1,090 bytes, roughly sixty words. That page was the entire
search footprint.

This directory fixes that.

## What it does

| | |
|---|---|
| `build.py` | Renders each published source to `<slug>/index.html` with title, meta description, canonical URL, Open Graph, Twitter card and JSON-LD. Emits `sitemap.xml`, `robots.txt` and `.nojekyll`. |
| `verify.py` | Checks the built artifact and exits non-zero on a broken crawler contract. Runs in the deploy job. |
| `test_build.py` | 18 tests over the generator. Stdlib-only, runs in `test.yml`. |

`build.py` needs `markdown`; `verify.py` and `test_build.py` do not.
`render_markdown` imports the dependency lazily so the test surface stays
stdlib-only, matching the rest of the repository.

## Building locally

```sh
python3 -m venv .venv && .venv/bin/pip install 'markdown==3.7'
.venv/bin/python site/build.py --out _site
python3 site/verify.py --out _site --base-url https://scadumen.github.io/ATLAS
python3 -m unittest discover site -v
python3 -m http.server -d _site 8000   # then open http://localhost:8000
```

## The index policy

`PAGES` in `build.py` is the single source of truth. Every file listed there is
already public — the workflow has copied each one to the live site since it was
written. The `indexable` flag decides only whether Google is *invited to rank*
it.

`indexable=False` changes nothing about reach: same URL, same content, still
linked from every page. It adds `noindex, follow` — the crawler keeps walking
the links outward but declines to list the page — and drops it from
`sitemap.xml`. Two rows are set that way deliberately:

- **`profiles/matthew.md`** — a personal collaboration profile naming a real
  person. Public is fine. Ranking on his name is a different thing, and not
  what the document is for.
- **`rapport/AGENTS.md`** — voice and cadence instructions. Internal craft,
  not something anyone is searching for.

`test_personal_material_is_not_indexed` pins that pair, so flipping either
boolean is a deliberate edit with a test to update, not a silent drift.

The sitemap and the `noindex` tag are generated from the same field on
purpose. Listing a noindex URL in a sitemap tells a crawler two contradictory
things at once, and Search Console reports it as an error.

## Google Search Console — the remaining step

Everything above is code and ships on merge. Search Console needs a Google
account and cannot be automated from here. It is also the only way to submit a
sitemap, request indexing, or see what Google actually thinks of the site.

1. Open <https://search.google.com/search-console> and add a **URL prefix**
   property for `https://scadumen.github.io/ATLAS/`.

   Use URL-prefix, not Domain. A Domain property needs a DNS record on
   `github.io`, which is not yours. URL-prefix is the correct choice for a
   project page on a shared host, and it scopes the property to this repo's
   path rather than every `scadumen.github.io` site.

2. Choose the **HTML tag** verification method and copy the `content` value —
   the long token, not the whole tag.

3. In the repository: **Settings → Secrets and variables → Actions →
   Variables → New repository variable**.

   - Name: `GOOGLE_SITE_VERIFICATION`
   - Value: the token

   A *variable*, not a secret. The token ships in the page source of every
   page by design, so it is not confidential, and secrets are deliberately
   awkward to read back. If the variable is unset the build still succeeds and
   simply omits the tag.

4. Re-run the **Deploy GitHub Pages** workflow, then press **Verify**.

5. Once verified, submit `sitemap.xml` under **Indexing → Sitemaps**, and use
   **URL Inspection → Request indexing** on the root page to prime the first
   crawl.

Expect days to weeks before pages appear, and check **Indexing → Pages** for
the reasons Google gives for anything it skips.

## Adding a page

Add a `Page(...)` row to `PAGES` and run the tests. `test_every_published_source_exists`
catches a typo'd path, `test_slugs_are_unique` catches a collision, and
`test_every_page_is_linked_from_every_page` guarantees the new page joins the
navigation — which matters here, because the Markdown sources contain no
hyperlinks of their own. Every `.md` reference in them is inside backticks and
renders as `<code>`. The injected navigation is the site's only link graph; a
page left out of it is an orphan no crawler will find.
