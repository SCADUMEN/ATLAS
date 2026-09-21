"""Tests for the documentation site builder.

These run on the repository's stdlib-only Python: `build` imports `markdown`
lazily inside `render_markdown`, so everything the crawler contract depends on
— the index policy, the sitemap, robots.txt, the link graph — is testable
without the Pages build dependency.
"""

import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build  # noqa: E402


BASE = "https://example.test/ATLAS"
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
ROOT = Path(__file__).resolve().parent.parent


class TestIndexPolicy(unittest.TestCase):
    def test_every_published_source_exists(self):
        """A published page naming a missing file would 404 in the sitemap."""
        for page in build.PAGES:
            with self.subTest(page.source):
                self.assertTrue(
                    (ROOT / page.source).is_file(),
                    f"{page.source} is listed in PAGES but not in the repository",
                )

    def test_slugs_are_unique(self):
        slugs = [p.slug for p in build.PAGES]
        self.assertEqual(len(slugs), len(set(slugs)), "duplicate slug would overwrite a page")

    def test_exactly_one_root_page(self):
        self.assertEqual(sum(1 for p in build.PAGES if p.slug == ""), 1)

    def test_every_section_is_ordered(self):
        """A section missing from SECTION_ORDER drops its pages out of the nav."""
        for page in build.PAGES:
            with self.subTest(page.slug):
                self.assertIn(page.section, build.SECTION_ORDER)

    def test_descriptions_fit_a_search_result(self):
        """Google truncates around 155-160 characters; over that is wasted."""
        for page in build.PAGES:
            with self.subTest(page.slug):
                self.assertTrue(page.description, f"{page.source} has no description")
                self.assertLessEqual(len(page.description), 160)

    def test_titles_are_present_and_reasonable(self):
        for page in build.PAGES:
            with self.subTest(page.slug):
                self.assertTrue(page.title)
                self.assertLessEqual(len(page.title), 75)

    def test_personal_material_is_not_indexed(self):
        """The deliberate policy call, pinned so it cannot regress silently.

        Both pages stay public and linked; they are only withheld from ranking.
        """
        withheld = {p.source for p in build.PAGES if not p.indexable}
        self.assertEqual(withheld, {"profiles/matthew.md", "rapport/AGENTS.md"})


class TestSitemap(unittest.TestCase):
    def setUp(self):
        self.stamps = {p.slug: "2026-01-01" for p in build.PAGES}
        self.xml = build.build_sitemap(build.PAGES, BASE, self.stamps)
        self.tree = ET.fromstring(self.xml)

    def test_is_well_formed_and_correctly_namespaced(self):
        self.assertTrue(self.tree.tag.endswith("urlset"))

    def test_lists_every_indexable_page_and_nothing_else(self):
        found = {e.text for e in self.tree.findall(".//sm:loc", SITEMAP_NS)}
        expected = {
            build.page_url(BASE, p.slug) for p in build.PAGES if p.indexable
        }
        self.assertEqual(found, expected)

    def test_omits_noindex_pages(self):
        """A sitemap entry for a noindex page is a contradiction Search Console flags."""
        found = {e.text for e in self.tree.findall(".//sm:loc", SITEMAP_NS)}
        for page in build.PAGES:
            if not page.indexable:
                self.assertNotIn(build.page_url(BASE, page.slug), found)

    def test_urls_are_absolute_and_directory_form(self):
        for loc in (e.text for e in self.tree.findall(".//sm:loc", SITEMAP_NS)):
            self.assertTrue(loc.startswith("https://"))
            self.assertTrue(loc.endswith("/"), f"{loc} should end in a slash")

    def test_lastmod_is_iso_date(self):
        for mod in (e.text for e in self.tree.findall(".//sm:lastmod", SITEMAP_NS)):
            self.assertRegex(mod, r"^\d{4}-\d{2}-\d{2}$")


class TestRobots(unittest.TestCase):
    def test_points_at_the_sitemap_absolutely(self):
        """Sitemap directives in robots.txt must be fully qualified URLs."""
        robots = build.build_robots(BASE)
        self.assertIn(f"Sitemap: {BASE}/sitemap.xml", robots)
        self.assertIn("User-agent: *", robots)
        self.assertIn("Allow: /", robots)

    def test_legacy_markdown_paths_are_disallowed(self):
        """The raw sources stay published so old links resolve, but the
        rendered pages are the only copy a crawler should fetch."""
        self.assertIn("Disallow: /*.md$", build.build_robots(BASE))


class TestNavigation(unittest.TestCase):
    def test_every_page_is_linked_from_every_page(self):
        """The sources contain no hyperlinks, so the nav is the only link graph.

        If a page is not in the nav it is an orphan and will not be discovered.
        """
        for current in build.PAGES:
            nav = build.build_nav(build.PAGES, BASE, current)
            for target in build.PAGES:
                with self.subTest(current=current.slug, target=target.slug):
                    self.assertIn(build.page_url(BASE, target.slug), nav)

    def test_current_page_is_marked(self):
        nav = build.build_nav(build.PAGES, BASE, build.PAGES[1])
        self.assertIn('aria-current="page"', nav)


class TestStructuredData(unittest.TestCase):
    def test_root_is_a_website_and_others_are_articles(self):
        import json

        root = next(p for p in build.PAGES if p.slug == "")
        other = next(p for p in build.PAGES if p.slug)
        self.assertEqual(
            json.loads(build.build_jsonld(root, BASE, "u", "2026-01-01"))["@type"],
            "WebSite",
        )
        self.assertEqual(
            json.loads(build.build_jsonld(other, BASE, "u", "2026-01-01"))["@type"],
            "TechArticle",
        )

    def test_jsonld_is_valid_json(self):
        import json

        for page in build.PAGES:
            with self.subTest(page.slug):
                json.loads(build.build_jsonld(page, BASE, "u", "2026-01-01"))


class TestPageUrl(unittest.TestCase):
    def test_root_and_nested(self):
        self.assertEqual(build.page_url(BASE, ""), f"{BASE}/")
        self.assertEqual(build.page_url(BASE, "a/b"), f"{BASE}/a/b/")


if __name__ == "__main__":
    unittest.main()
