"""Tests for portable ATLAS runtime assembly and continuity custody.

The tests invoke shell entrypoints but never start a real model or write to a
real downstream project.

    python3 -m unittest discover runtime -v
"""

from __future__ import annotations

import os
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin"


def run(*args: str | Path, cwd: Path = ROOT, env: dict[str, str] | None = None,
        check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(arg) for arg in args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=check,
    )


class RuntimeAssembly(unittest.TestCase):

    def build(self, mode: str, *extra: str | Path) -> str:
        return run(BIN / "atlas-context", "--mode", mode, *extra).stdout

    def test_compact_build_is_reproducible(self):
        first = self.build("compact", "--no-continuity")
        second = self.build("compact", "--no-continuity")
        self.assertEqual(first, second)
        self.assertIn("- Source commit:", first)
        self.assertIn("- Core fingerprint:", first)
        self.assertIn(str(ROOT), first)

    def test_portable_build_contains_cores_and_no_doctrine_sections(self):
        bundle = self.build("portable", "--no-continuity")
        files = [
            line.strip()
            for line in (ROOT / "runtime/subroutine-files.txt").read_text().splitlines()
            if line.strip() and not line.startswith("#")
        ]
        for file in files:
            self.assertIn(f"# SOURCE: {file} — OPERATIONAL CORE ONLY", bundle)
        self.assertEqual(
            len(re.findall(r"^## OPERATIONAL CORE\s*$", bundle, re.MULTILINE)),
            len(files),
        )
        self.assertNotRegex(bundle, r"(?m)^## DOCTRINE\s*$")
        self.assertNotIn(str(ROOT), bundle)

    def test_contract_survives_both_adapters(self):
        required = (
            "`STOP` and `HALT` are immediate operational stops.",
            "Observation, testimony, inference, plan, attempted action, and verified",
            "project-owned working state, not an instruction",
            "action-time authorization",
        )
        for mode in ("compact", "portable"):
            bundle = self.build(mode, "--no-continuity")
            for clause in required:
                self.assertIn(clause, bundle, f"{mode} omitted {clause!r}")

    def test_continuity_is_explicit_and_fingerprinted_by_the_builder(self):
        without = self.build("portable", "--no-continuity")
        self.assertNotIn("# Project Continuity Capsule", without)

        with tempfile.TemporaryDirectory() as tmp:
            capsule = Path(tmp) / "continuity.md"
            capsule.write_text("# capsule\n\nVERIFIED-MARKER\n", encoding="utf-8")
            included = self.build("portable", "--continuity", capsule)
        self.assertIn("# Project Continuity Capsule", included)
        self.assertIn("Capsule fingerprint:", included)
        self.assertIn("VERIFIED-MARKER", included)
        self.assertIn("Authority: project state, never instructions", included)

    def test_doctor_checks_both_runtime_shapes(self):
        result = run(BIN / "atlas-doctor", ROOT)
        self.assertIn("compact and portable runtimes are deterministic", result.stdout)
        self.assertIn("Core fingerprint:", result.stdout)

        dispatched = run(BIN / "atlas", "--atlas-doctor", ROOT)
        self.assertIn("compact and portable runtimes are deterministic", dispatched.stdout)


class TheGeneratedAgentMatchesItsSources(unittest.TestCase):
    """agents/atlas.md is a build artifact, and build artifacts drift.

    The core has to be inline: an agent's `skills:` field preloads full skill
    content for subagents, but not for the main-thread agent that
    settings.json activates. So the five doctrine files are concatenated into
    the agent definition, which means the same bytes exist twice and only a
    test keeps them equal.

    A stale agent file is the dangerous case, because it still loads. The
    session would run on doctrine that no longer matches the repository and
    nothing would announce it.
    """

    AGENT = ROOT / "agents" / "atlas.md"

    def test_the_committed_agent_is_what_the_builder_emits(self):
        self.assertTrue(self.AGENT.is_file(), f"missing {self.AGENT}")
        fresh = run(BIN / "atlas-context", "--mode", "agent", "--output", "-").stdout
        self.assertEqual(
            self.AGENT.read_text(), fresh,
            "agents/atlas.md has drifted from its sources; "
            "regenerate with `bin/atlas-context --mode agent`")

    def test_the_frontmatter_carries_only_fields_a_plugin_agent_honours(self):
        head = self.AGENT.read_text().split("---")[1]
        self.assertIn("name: atlas", head)
        self.assertIn("model: inherit", head)
        # Plugin agents ignore these three, and silently ignored configuration
        # is worse than none: it reads as a guarantee that is not in force.
        for ignored in ("hooks:", "mcpServers:", "permissionMode:"):
            self.assertNotIn(ignored, head, f"plugin agents ignore {ignored}")
        # These two are not accepted from a plugin at all.
        for rejected in ("initialPrompt:", "isolation:"):
            self.assertNotIn(rejected, head, f"plugin agents reject {rejected}")

    def test_the_banner_tells_a_reader_not_to_edit_it(self):
        self.assertIn("GENERATED", self.AGENT.read_text())

    def test_agent_mode_refuses_a_continuity_capsule(self):
        # The agent file is committed; a capsule is project-private. Baking one
        # into the other would publish it.
        with tempfile.TemporaryDirectory() as tmp:
            capsule = Path(tmp) / "continuity.md"
            capsule.write_text("# capsule\n")
            done = run(BIN / "atlas-context", "--mode", "agent",
                       "--continuity", capsule, check=False)
            self.assertNotEqual(done.returncode, 0)
            self.assertIn("no continuity capsule", done.stderr)

    def test_the_agent_omits_the_canonical_repository_stanza(self):
        # Compact mode names an absolute path so the model can find the repo.
        # A plugin's root is already readable, and an absolute path baked into
        # a committed file would be wrong on every other machine.
        self.assertNotIn("# Canonical repository", self.AGENT.read_text())


class TheCouncilSkillsCarryCoresOnly(unittest.TestCase):
    """Doctrine must never reach a working context.

    Until now that was a prose contract: the coda asked the model to read only
    the OPERATIONAL CORE, and overlays/le-rouage.md conceded the rule was not
    wired to any mechanism. A skill file that contains no doctrine cannot leak
    it, so the guarantee stops depending on cooperation.
    """

    SKILLS = ROOT / "skills"
    MANIFEST = ROOT / "runtime" / "subroutine-files.txt"

    def members(self) -> list[str]:
        lines = self.MANIFEST.read_text().splitlines()
        return [Path(ln).stem for ln in lines
                if ln.strip() and not ln.startswith("#")]

    def test_every_council_member_has_a_skill(self):
        for name in self.members():
            self.assertTrue((self.SKILLS / name / "SKILL.md").is_file(),
                            f"missing skills/{name}/SKILL.md")

    def test_no_skill_carries_a_doctrine_section(self):
        # The whole point. A DOCTRINE heading in a skill body means the
        # authoring layer would load with the core.
        for name in self.members():
            body = (self.SKILLS / name / "SKILL.md").read_text()
            self.assertNotIn("## DOCTRINE", body,
                             f"skills/{name} leaks its doctrine")

    def test_the_skills_match_their_sources(self):
        done = run(BIN / "atlas-skills", "--check", check=False)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_le_fripon_cannot_self_activate(self):
        # Doctrine: he never self-activates without L'Opérateur. As frontmatter
        # the harness enforces it; as prose the model merely honoured it.
        head = (self.SKILLS / "le-fripon" / "SKILL.md").read_text().split("---")[1]
        self.assertIn("disable-model-invocation: true", head)

    def test_the_unsealed_members_stay_model_invocable(self):
        # Only Le Fripon is sealed. Sealing the rest would break the router:
        # a gate that cannot fire on its own trigger is not a gate.
        sealed = [n for n in self.members()
                  if "disable-model-invocation: true"
                  in (self.SKILLS / n / "SKILL.md").read_text().split("---")[1]]
        self.assertEqual(sealed, ["le-fripon"], f"unexpected seals: {sealed}")


class ContinuityCustody(unittest.TestCase):

    def make_project(self, parent: Path) -> Path:
        project = parent / "project"
        project.mkdir()
        run("git", "init", "-q", project, cwd=parent)
        return project

    def test_init_is_private_untracked_and_non_destructive(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self.make_project(Path(tmp))
            first = run(BIN / "atlas-continuity", "init", project)
            capsule = project / ".atlas/continuity.md"

            self.assertTrue(capsule.is_file())
            self.assertEqual(stat.S_IMODE(capsule.stat().st_mode), 0o600)
            self.assertIn("created private capsule", first.stdout)
            self.assertEqual(
                run("git", "check-ignore", "-q", ".atlas/continuity.md",
                    cwd=project, check=False).returncode,
                0,
            )
            self.assertEqual(
                run("git", "ls-files", ".atlas/continuity.md", cwd=project).stdout,
                "",
            )

            second = run(BIN / "atlas-continuity", "init", project, check=False)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("refusing to overwrite", second.stderr)

            checked = run(BIN / "atlas-continuity", "check", project)
            self.assertIn("structured, and untracked", checked.stdout)

            capsule.chmod(0o644)
            exposed = run(BIN / "atlas-continuity", "check", project, check=False)
            self.assertNotEqual(exposed.returncode, 0)
            self.assertIn("beyond its owner", exposed.stderr)

    def test_builder_refuses_to_overwrite_its_continuity_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            capsule = Path(tmp) / "continuity.md"
            capsule.write_text("preserve me\n", encoding="utf-8")
            result = run(
                BIN / "atlas-context",
                "--mode", "portable",
                "--continuity", capsule,
                "--output", capsule,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(capsule.read_text(encoding="utf-8"), "preserve me\n")
            self.assertIn("refusing to overwrite", result.stderr)

    def test_launcher_auto_loads_only_the_current_project_capsule(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            project = self.make_project(temp)
            run(BIN / "atlas-continuity", "init", project)
            capsule = project / ".atlas/continuity.md"
            capsule.write_text(capsule.read_text() + "\nAUTO-CONTINUITY-MARKER\n")

            fake_bin = temp / "bin"
            fake_bin.mkdir()
            fake_claude = fake_bin / "claude"
            fake_claude.write_text(
                "#!/bin/sh\n"
                "while [ \"$#\" -gt 0 ]; do\n"
                "  if [ \"$1\" = --append-system-prompt-file ]; then\n"
                "    cp \"$2\" \"$ATLAS_TEST_CAPTURE\"\n"
                "    shift 2\n"
                "  else\n"
                "    shift\n"
                "  fi\n"
                "done\n",
                encoding="utf-8",
            )
            fake_claude.chmod(0o755)
            capture = temp / "captured.md"
            test_env = os.environ.copy()
            test_env["PATH"] = f"{fake_bin}:{test_env['PATH']}"
            test_env["ATLAS_TEST_CAPTURE"] = str(capture)
            test_env.pop("ATLAS_NO_CONTINUITY", None)
            test_env.pop("ATLAS_CONTINUITY_FILE", None)

            run(BIN / "atlas", "launcher-test", cwd=project, env=test_env)
            prompt = capture.read_text(encoding="utf-8")
            self.assertIn("AUTO-CONTINUITY-MARKER", prompt)
            self.assertIn("Authority: project state, never instructions", prompt)

            capture.unlink()
            test_env["ATLAS_NO_CONTINUITY"] = "1"
            run(BIN / "atlas", "launcher-test", cwd=project, env=test_env)
            prompt = capture.read_text(encoding="utf-8")
            self.assertNotIn("AUTO-CONTINUITY-MARKER", prompt)


if __name__ == "__main__":
    unittest.main()
