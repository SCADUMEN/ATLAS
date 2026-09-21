#!/usr/bin/env python3
"""Build the indexable ATLAS documentation site.

GitHub Pages serves `.md` as `text/markdown`, which search engines do not index
as documents. Every word ATLAS publishes was therefore invisible to Google: the
only indexable page on the site was a sixty-word `index.html`.

This renders each published Markdown source to a real HTML page carrying a
title, description, canonical URL and structured data, links every page to
every other (the sources contain no hyperlinks at all, so each page would
otherwise be an orphan), and emits the sitemap and robots.txt a crawler needs.

Run from the repository root:

    python3 site/build.py --out _site --base-url https://scadumen.github.io/ATLAS

The `markdown` dependency is installed by the Pages build job only; the test
surface stays stdlib-only.
"""

from __future__ import annotations

import argparse
import html
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import date, timezone, datetime
from pathlib import Path


BASE_URL_DEFAULT = "https://scadumen.github.io/ATLAS"
SITE_NAME = "ATLAS"


@dataclass(frozen=True)
class Page:
    """One published document and the metadata a crawler reads off it."""

    source: str          # path relative to the repository root
    slug: str            # published path, no extension; "" is the site root
    title: str           # <title> and og:title
    description: str     # <meta name="description">, <= ~155 chars
    section: str         # navigation grouping
    indexable: bool      # False emits <meta name="robots" content="noindex, follow">
    priority: float


# ---------------------------------------------------------------------------
# The index policy.
#
# Every file here is ALREADY public — deploy-pages.yml copies each one to the
# live site today, and has since the workflow was written. The only question
# this table settles is whether Google is invited to rank it.
#
# `indexable=False` changes nothing about reach: same URL, same content, still
# linked from every page. It adds `noindex, follow`, which keeps the crawler
# walking the links outward while declining to list the page itself, and drops
# it from sitemap.xml.
#
# Two rows are set False deliberately:
#   profiles/matthew.md  — a personal collaboration profile naming a real
#                          person. Public is fine; ranking on his name is a
#                          different thing, and not what the document is for.
#   rapport/AGENTS.md    — voice and cadence instructions. Internal craft, not
#                          reference material anyone is searching for.
# Flip either boolean to change that.
# ---------------------------------------------------------------------------
PAGES: list[Page] = [
    Page(
        "README.md", "",
        "ATLAS — an operating layer for recovery, archive work and calm execution",
        "ATLAS is a versioned operating layer for technical recovery, archive work, "
        "project planning and calm execution. Reusable instructions and templates.",
        "Core", True, 1.0,
    ),
    Page(
        "ATLAS.md", "core",
        "The ATLAS core operating layer",
        "The core operating layer: how ATLAS addresses the Operator, holds identity, "
        "and helps build, document, recover, organize and ship.",
        "Core", True, 0.9,
    ),
    Page(
        "AGENTS.md", "agents",
        "ATLAS repository instructions",
        "Repository instructions for working inside ATLAS — what to read before "
        "making changes, and which layer is authoritative for what.",
        "Core", True, 0.7,
    ),
    Page(
        "rapport/AGENTS.md", "rapport",
        "The ATLAS rapport layer",
        "The rapport layer: conversational cadence, mission-control tone and signoff "
        "behavior. Refines voice without overriding technical correctness.",
        "Core", False, 0.3,
    ),

    Page(
        "overlays/forgotten-industries.md", "overlays/forgotten-industries",
        "Forgotten Industries overlay",
        "An archive and evidence-based memoir exploring what happens to the things we "
        "leave behind: old machines, abandoned projects, and parts of ourselves.",
        "Overlays", True, 0.8,
    ),
    Page(
        "overlays/le-conseil.md", "overlays/le-conseil",
        "Le Conseil — human judgement, machine collaboration, contre l'oubli",
        "The three-tier doctrine at the centre of ATLAS: human judgement holds the "
        "decision, machine collaboration does the work, and nothing is lost.",
        "Overlays", True, 0.8,
    ),
    Page(
        "overlays/le-protocol-de-trois.md", "overlays/le-protocol-de-trois",
        "Le Protocol de Trois — the Protocol of the Three Witnesses",
        "A callable brainstorming and judgment subroutine using three operating "
        "ghosts: Le Sauvegarder, Le Continuant and Le Rédempteur.",
        "Overlays", True, 0.8,
    ),
    Page(
        "overlays/le-barillet.md", "overlays/le-barillet",
        "Le Barillet — the barrel",
        "The mainspring barrel: stores the power the crown winds and releases it "
        "through Le Rouage. A component, not a member, mode or voice.",
        "Overlays", True, 0.7,
    ),
    Page(
        "overlays/le-rouage.md", "overlays/le-rouage",
        "Le Rouage — the going train",
        "Carries force from the barrel to the escapement and distributes the "
        "regulated result to the registers and the hands.",
        "Overlays", True, 0.7,
    ),
    Page(
        "overlays/le-sas.md", "overlays/le-sas",
        "Le Sas — the escapement",
        "The escapement: regulates release between the registers and the dial. "
        "A complication sitting between register 01 and ATLAS.",
        "Overlays", True, 0.7,
    ),
    Page(
        "overlays/le-niveau.md", "overlays/le-niveau",
        "Le Niveau — the completeness readout",
        "Measures how complete the instrument is as one deterministic number. "
        "A readout about the whole, outside the cycle it reports on.",
        "Overlays", True, 0.7,
    ),

    Page(
        "templates/repo-AGENTS.md", "templates/repo-agents",
        "Repository AGENTS.md template",
        "A starting AGENTS.md for a new repository: what to read first, which "
        "operating layer applies, and how local instructions take precedence.",
        "Templates", True, 0.6,
    ),
    Page(
        "templates/project-overlay.md", "templates/project-overlay",
        "Project overlay template",
        "A template for describing what a project is and what it is trying to "
        "preserve, build, restore or ship.",
        "Templates", True, 0.6,
    ),
    Page(
        "templates/continuity-capsule.md", "templates/continuity-capsule",
        "Continuity capsule template",
        "Project-local handoff material: evidence-aware working state that carries "
        "context between sessions, kept out of version control.",
        "Templates", True, 0.6,
    ),

    Page(
        "profiles/matthew.md", "profiles/matthew",
        "Operator profile",
        "An example operator profile: stable collaboration preferences that guide "
        "communication and project support without replacing direct instruction.",
        "Profiles", False, 0.3,
    ),
]

SECTION_ORDER = ["Core", "Overlays", "Templates", "Profiles"]


STYLE = """\
:root{color-scheme:light dark;--fg:#1a1a1a;--bg:#fdfdfb;--muted:#5a5a55;
--rule:#dcdcd4;--link:#6b5230;--accent:#8a6d3b}
@media (prefers-color-scheme:dark){:root{--fg:#e8e6e0;--bg:#16161a;
--muted:#a09c94;--rule:#32323a;--link:#c9a86a;--accent:#c9a86a}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.65 ui-serif,Georgia,"Iowan Old Style",serif;
-webkit-text-size-adjust:100%}
.wrap{max-width:74rem;margin:0 auto;padding:0 16px;
display:grid;grid-template-columns:15rem minmax(0,1fr);gap:3rem}
@media(max-width:820px){.wrap{grid-template-columns:1fr;gap:1.5rem}}
nav{padding:2.5rem 0;font:13px/1.5 ui-sans-serif,system-ui,sans-serif}
@media(min-width:821px){nav{position:sticky;top:0;align-self:start;
max-height:100vh;overflow-y:auto}}
nav .brand{font-weight:700;letter-spacing:.14em;text-transform:uppercase;
font-size:12px;color:var(--accent);margin-bottom:1.5rem;display:block;
text-decoration:none}
nav h2{font:600 10px/1 ui-sans-serif,system-ui,sans-serif;letter-spacing:.16em;
text-transform:uppercase;color:var(--muted);margin:1.5rem 0 .5rem}
nav ul{list-style:none;margin:0;padding:0}
nav li{margin:.3rem 0}
nav a{color:var(--fg);text-decoration:none;opacity:.8}
nav a:hover{opacity:1;text-decoration:underline}
nav a[aria-current=page]{color:var(--accent);font-weight:600;opacity:1}
main{padding:2.5rem 0 5rem;min-width:0}
main h1{font-size:2rem;line-height:1.2;margin:0 0 1.5rem;letter-spacing:-.01em}
main h2{font-size:1.3rem;margin:2.5rem 0 .75rem;padding-bottom:.3rem;
border-bottom:1px solid var(--rule)}
main h3{font-size:1.05rem;margin:1.75rem 0 .5rem}
main a{color:var(--link)}
code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.86em}
code{background:color-mix(in srgb,var(--fg) 8%,transparent);
padding:.12em .35em;border-radius:3px}
pre{background:color-mix(in srgb,var(--fg) 6%,transparent);padding:1rem;
border-radius:6px;overflow-x:auto;border:1px solid var(--rule)}
pre code{background:none;padding:0}
blockquote{margin:1.5rem 0;padding-left:1.1rem;border-left:3px solid var(--accent);
color:var(--muted)}
table{border-collapse:collapse;width:100%;margin:1.5rem 0;font-size:.93em;
display:block;overflow-x:auto}
th,td{border:1px solid var(--rule);padding:.45rem .7rem;text-align:left}
th{background:color-mix(in srgb,var(--fg) 5%,transparent)}
hr{border:0;border-top:1px solid var(--rule);margin:2.5rem 0}
footer{margin-top:4rem;padding-top:1.5rem;border-top:1px solid var(--rule);
font:13px/1.6 ui-sans-serif,system-ui,sans-serif;color:var(--muted)}
footer a{color:var(--link)}
"""


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
{robots}{verification}<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{site_name}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<link rel="sitemap" type="application/xml" href="{base_url}/sitemap.xml">
<script type="application/ld+json">{jsonld}</script>
<style>{style}</style>
</head>
<body>
<div class="wrap">
<nav aria-label="Site">
<a class="brand" href="{base_url}/">{site_name}</a>
{nav}
</nav>
<main>
{body}
<footer>
<p>{site_name} — an operating layer for technical recovery, archive work and
calm execution. Source: <a href="{repo_url}">{repo_url}</a></p>
<p>Built from <code>{source}</code> · last updated {lastmod}</p>
</footer>
</main>
</div>
</body>
</html>
"""


def run_git(root: Path, *args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, timeout=15
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def last_modified(root: Path, source: str, fallback: str) -> str:
    """Last commit date for a file, as YYYY-MM-DD, for honest sitemap lastmod."""
    stamp = run_git(root, "log", "-1", "--format=%cI", "--", source)
    if stamp:
        return stamp[:10]
    try:
        mtime = (root / source).stat().st_mtime
        return datetime.fromtimestamp(mtime, timezone.utc).date().isoformat()
    except OSError:
        return fallback


def render_markdown(text: str) -> str:
    """Convert Markdown to an HTML fragment."""
    import markdown  # imported lazily so --help works without the dependency

    return markdown.markdown(
        text,
        extensions=["extra", "sane_lists", "admonition"],
        output_format="html5",
    )


def page_url(base_url: str, slug: str) -> str:
    return f"{base_url}/{slug}/" if slug else f"{base_url}/"


def build_nav(pages: list[Page], base_url: str, current: Page) -> str:
    """Full site navigation, emitted into every page.

    The Markdown sources contain no hyperlinks whatsoever, so without this every
    page is an orphan: reachable only by guessing its URL. Repeating the whole
    index on each page puts every document one hop from every other.
    """
    parts: list[str] = []
    for section in SECTION_ORDER:
        members = [p for p in pages if p.section == section]
        if not members:
            continue
        parts.append(f"<h2>{html.escape(section)}</h2>\n<ul>")
        for page in members:
            current_attr = ' aria-current="page"' if page.slug == current.slug else ""
            parts.append(
                f'<li><a href="{html.escape(page_url(base_url, page.slug))}"'
                f'{current_attr}>{html.escape(page.title.split(" — ")[0])}</a></li>'
            )
        parts.append("</ul>")
    return "\n".join(parts)


def build_jsonld(page: Page, base_url: str, repo_url: str, lastmod: str) -> str:
    """Structured data: WebSite at the root, TechArticle elsewhere."""
    import json

    canonical = page_url(base_url, page.slug)
    if not page.slug:
        data = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": SITE_NAME,
            "url": canonical,
            "description": page.description,
            "codeRepository": repo_url,
        }
    else:
        data = {
            "@context": "https://schema.org",
            "@type": "TechArticle",
            "headline": page.title,
            "description": page.description,
            "url": canonical,
            "dateModified": lastmod,
            "isPartOf": {"@type": "WebSite", "name": SITE_NAME, "url": f"{base_url}/"},
        }
    return json.dumps(data, ensure_ascii=False)


def build_sitemap(pages: list[Page], base_url: str, stamps: dict[str, str]) -> str:
    """sitemap.xml over the indexable pages only.

    Listing a noindex page here sends a crawler a contradiction: the sitemap
    asks it to index, the meta tag refuses. Search Console reports that as an
    error, so the two must agree.
    """
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for page in pages:
        if not page.indexable:
            continue
        lines += [
            "  <url>",
            f"    <loc>{html.escape(page_url(base_url, page.slug))}</loc>",
            f"    <lastmod>{stamps[page.slug]}</lastmod>",
            f"    <priority>{page.priority:.1f}</priority>",
            "  </url>",
        ]
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def build_robots(base_url: str) -> str:
    """robots.txt.

    The raw Markdown sources are still published at their original paths so
    links that predate the HTML build keep resolving, but they are the same
    content as the rendered pages and must not compete with them. Disallowing
    `*.md` keeps the HTML the only crawlable copy; a crawler that already knows
    a `.md` URL is told not to fetch it, and the canonical tag on every page
    points at the rendered version regardless.
    """
    return (
        "# ATLAS — https://github.com/SCADUMEN/ATLAS\n"
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        "# Legacy raw-Markdown paths: still served, never the canonical copy.\n"
        "Disallow: /*.md$\n"
        f"\nSitemap: {base_url}/sitemap.xml\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the indexable ATLAS documentation site."
    )
    parser.add_argument("--out", default=Path("_site"), type=Path)
    parser.add_argument("--base-url", default=BASE_URL_DEFAULT)
    parser.add_argument("--repo-url", default="https://github.com/SCADUMEN/ATLAS")
    parser.add_argument(
        "--verification",
        default=os.environ.get("GOOGLE_SITE_VERIFICATION", ""),
        help="Google Search Console token; emits the google-site-verification meta tag.",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    root = Path(__file__).resolve().parent.parent
    out = args.out
    today = date.today().isoformat()

    verification = ""
    if args.verification:
        token = html.escape(args.verification, quote=True)
        verification = f'<meta name="google-site-verification" content="{token}">\n'

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    stamps = {p.slug: last_modified(root, p.source, today) for p in PAGES}

    for page in PAGES:
        source_path = root / page.source
        if not source_path.exists():
            raise SystemExit(f"missing published source: {page.source}")

        text = source_path.read_text(encoding="utf-8")
        robots = "" if page.indexable else '<meta name="robots" content="noindex, follow">\n'

        document = PAGE_TEMPLATE.format(
            title=html.escape(page.title),
            description=html.escape(page.description),
            canonical=html.escape(page_url(base_url, page.slug)),
            robots=robots,
            verification=verification,
            og_type="website" if not page.slug else "article",
            site_name=html.escape(SITE_NAME),
            base_url=html.escape(base_url),
            repo_url=html.escape(args.repo_url),
            jsonld=build_jsonld(page, base_url, args.repo_url, stamps[page.slug]),
            style=STYLE,
            nav=build_nav(PAGES, base_url, page),
            body=render_markdown(text),
            source=html.escape(page.source),
            lastmod=stamps[page.slug],
        )

        destination = out / page.slug / "index.html" if page.slug else out / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(document, encoding="utf-8")

    # Keep every pre-existing URL working. Before the HTML build the workflow
    # copied these sources verbatim, so /ATLAS/README.md and friends were the
    # only addresses this site ever had. Dropping them would 404 any link that
    # predates this change. They stay, disallowed in robots.txt, with the
    # rendered page as the canonical copy.
    for page in PAGES:
        legacy = out / page.source
        legacy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / page.source, legacy)

    (out / "sitemap.xml").write_text(build_sitemap(PAGES, base_url, stamps), encoding="utf-8")
    (out / "robots.txt").write_text(build_robots(base_url), encoding="utf-8")
    (out / ".nojekyll").touch()

    indexed = sum(1 for p in PAGES if p.indexable)
    print(
        f"built {len(PAGES)} pages ({indexed} indexable, "
        f"{len(PAGES) - indexed} noindex) into {out}/"
    )
    if not args.verification:
        print("note: no Search Console token supplied (GOOGLE_SITE_VERIFICATION unset)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
