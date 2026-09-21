#!/usr/bin/env python3
"""Verify a built site against the contract a crawler expects.

site/test_build.py tests the generator. This checks the artifact it produced,
which is where a path bug, a missing source or a stale output directory would
actually show up. Run after build.py; a non-zero exit should fail the deploy.

    python3 site/verify.py --out _site --base-url https://scadumen.github.io/ATLAS
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def page_path(out: Path, base_url: str, loc: str) -> Path:
    """Map a sitemap URL back to the file GitHub Pages would serve for it."""
    slug = loc[len(base_url):].strip("/") if loc.startswith(base_url) else loc.strip("/")
    return out / slug / "index.html" if slug else out / "index.html"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=Path("_site"), type=Path)
    parser.add_argument("--base-url", required=True)
    args = parser.parse_args()

    out: Path = args.out
    base_url: str = args.base_url.rstrip("/")
    errors: list[str] = []

    for required in ("index.html", "sitemap.xml", "robots.txt"):
        if not (out / required).is_file() or not (out / required).stat().st_size:
            errors.append(f"{required} is missing or empty")
    if errors:
        print("\n".join(f"error: {e}" for e in errors), file=sys.stderr)
        return 1

    robots = (out / "robots.txt").read_text(encoding="utf-8")
    if f"Sitemap: {base_url}/sitemap.xml" not in robots:
        errors.append("robots.txt does not advertise the sitemap at the deployed base URL")
    if "Disallow: /*.md$" not in robots:
        errors.append("robots.txt does not disallow the legacy raw-Markdown paths")

    locs = [
        e.text or ""
        for e in ET.parse(out / "sitemap.xml").getroot().findall(".//sm:loc", SITEMAP_NS)
    ]
    if not locs:
        errors.append("sitemap.xml lists no URLs")

    pages = sorted(out.rglob("index.html"))
    listed = set()

    for loc in locs:
        if not loc.startswith(base_url):
            errors.append(f"sitemap URL is not under the deployed base URL: {loc}")
            continue
        target = page_path(out, base_url, loc)
        if not target.is_file():
            errors.append(f"sitemap lists {loc} but {target} was not built")
            continue
        listed.add(target)
        text = target.read_text(encoding="utf-8")
        if re.search(r'<meta name="robots"[^>]*noindex', text):
            errors.append(f"sitemap lists {loc}, but that page carries noindex")

    for page in pages:
        text = page.read_text(encoding="utf-8")
        if "<title>" not in text:
            errors.append(f"{page} has no <title>")
        if 'name="description"' not in text:
            errors.append(f"{page} has no meta description")
        if 'rel="canonical"' not in text:
            errors.append(f"{page} has no canonical URL")
        noindex = bool(re.search(r'<meta name="robots"[^>]*noindex', text))
        if not noindex and page not in listed:
            errors.append(f"{page} is indexable but absent from sitemap.xml")

    if errors:
        print("\n".join(f"error: {e}" for e in errors), file=sys.stderr)
        return 1

    print(
        f"crawler contract OK — {len(pages)} pages built, "
        f"{len(locs)} listed in sitemap, {len(pages) - len(locs)} noindex"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
