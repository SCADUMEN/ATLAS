"""Tests for portable ATLAS runtime assembly and continuity custody.

The tests invoke shell entrypoints but never start a real model or write to a
real downstream project.

    python3 -m unittest discover runtime -v
"""

from __future__ import annotations

import json
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
        # The --atlas-doctor dispatch through bin/atlas is gone with the
        # launcher. atlas-doctor is called directly, and ships in the plugin's
        # bin/ so it is on PATH inside an ATLAS session.
        result = run(BIN / "atlas-doctor", ROOT)
        self.assertIn("compact and portable runtimes are deterministic", result.stdout)
        self.assertIn("Core fingerprint:", result.stdout)


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


class TheRiteSkillIsInvocableAsAtlas(unittest.TestCase):
    """The /atlas skill is standalone, and that is not a stylistic choice.

    Plugin skills are always namespaced, so the best a plugin can offer is
    /atlas:atlas. A personal skill is not namespaced. And the invocation name
    comes from the skill's DIRECTORY, not its frontmatter `name` — tested: a
    directory called atlas-rite registered as /atlas-rite despite `name: atlas`.
    So the directory has to be `atlas`, which is why the plugin cannot also
    install to ~/.claude/skills/atlas.
    """

    SKILL = ROOT / "skills-standalone" / "atlas" / "SKILL.md"

    def test_the_directory_is_named_atlas(self):
        # This is what makes it /atlas. Renaming the directory renames the
        # command, whatever the frontmatter says.
        self.assertEqual(self.SKILL.parent.name, "atlas")

    def test_the_rite_is_the_operators_to_invoke(self):
        # The crown is the only way in. Claude must not decide to wind it.
        head = self.SKILL.read_text().split("---")[1]
        self.assertIn("disable-model-invocation: true", head)

    def test_the_skill_matches_the_rite_source(self):
        done = run(BIN / "atlas-rite-skill", "--check", check=False)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_the_panel_matches_the_renderer(self):
        # A third copy of the masthead would drift. rouage/premiere_lueur.py is
        # canonical; the coda and this skill are both generated from it.
        sys_path = str(ROOT / "rouage")
        code = (
            "import sys, re;"
            f"sys.path.insert(0, {sys_path!r});"
            "from premiere_lueur import premiere_lueur;"
            f"body = open({str(self.SKILL)!r}, encoding='utf-8').read();"
            "fence = re.search(r'```text\\n(.*?)```', body, re.S).group(1);"
            "canon = premiere_lueur();"
            "print('\\n'.join(fence.splitlines()[:len(canon.splitlines())]) == canon)"
        )
        done = run("python3", "-c", code)
        self.assertEqual(done.stdout.strip(), "True",
                         "the rite skill's panel has drifted from the renderer")

    def test_the_grade_readout_degrades_rather_than_breaks(self):
        # The skill cannot use ${CLAUDE_PLUGIN_ROOT} and cannot know where the
        # plugin lives — a marketplace install caches it, a checkout is wherever
        # it was cloned. The search sits in a sibling script because a for-loop
        # with globs inside the ! substitution silently emitted nothing, which
        # cost the entire readout. A miss must cost the grade, never the rite.
        body = self.SKILL.read_text()
        self.assertIn("|| true", body)
        resolver = self.SKILL.parent / "grade"
        self.assertTrue(os.access(resolver, os.X_OK),
                        "the grade resolver must be executable")
        text = resolver.read_text()
        self.assertIn("ATLAS_REPO", text)
        self.assertIn(".claude/plugins/cache", text)

    def test_the_grade_resolver_is_silent_when_it_finds_nothing(self):
        # Run it with a HOME that holds no ATLAS at all.
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["HOME"] = tmp
            env.pop("ATLAS_REPO", None)
            done = run(self.SKILL.parent / "grade", env=env, check=False)
            self.assertEqual(done.returncode, 0)
            self.assertEqual(done.stdout.strip(), "")


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

    def test_the_hook_auto_loads_only_the_current_project_capsule(self):
        # Capsule discovery moved from bin/atlas into the SessionStart hook when
        # the launcher retired. Same rules: the project's own capsule, the
        # ATLAS_CONTINUITY_FILE override, and the ATLAS_NO_CONTINUITY opt-out.
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            project = self.make_project(temp)
            run(BIN / "atlas-continuity", "init", project)
            capsule = project / ".atlas/continuity.md"
            capsule.write_text(capsule.read_text() + "\nAUTO-CONTINUITY-MARKER\n")

            env = os.environ.copy()
            env.pop("ATLAS_NO_CONTINUITY", None)
            env.pop("ATLAS_CONTINUITY_FILE", None)
            # Isolate from a developer's real per-user operator profile.
            env["ATLAS_NO_OPERATOR"] = "1"

            found = run(BIN / "atlas-session-start", cwd=project, env=env).stdout
            payload = json.loads(found)["hookSpecificOutput"]
            self.assertEqual(payload["hookEventName"], "SessionStart")
            self.assertIn("AUTO-CONTINUITY-MARKER", payload["additionalContext"])
            self.assertIn("Authority: project state, never instructions",
                          payload["additionalContext"])

            # Opted out: no capsule, and still a clean exit. A hook that fails
            # must not stop a session from starting.
            env["ATLAS_NO_CONTINUITY"] = "1"
            opted = run(BIN / "atlas-session-start", cwd=project, env=env)
            self.assertEqual(opted.returncode, 0)
            self.assertEqual(opted.stdout.strip(), "")

    def test_the_hook_is_silent_outside_a_project_with_a_capsule(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env.pop("ATLAS_NO_CONTINUITY", None)
            env.pop("ATLAS_CONTINUITY_FILE", None)
            env["ATLAS_NO_OPERATOR"] = "1"
            done = run(BIN / "atlas-session-start", cwd=Path(tmp), env=env)
            self.assertEqual(done.returncode, 0)
            self.assertEqual(done.stdout.strip(), "")

    def test_the_hook_never_reports_the_grade(self):
        # The grade belongs to the rite, which reads it at skill load. Repeating
        # it on every session start would be noise, and a readout nobody asked
        # for is the sort of thing that quietly becomes load-bearing.
        body = (BIN / "atlas-session-start").read_text()
        self.assertNotIn("grade.py", body)


class OperatorIdentity(unittest.TestCase):
    """The operator profile is per-user and optional.

    It is who ATLAS is serving — the name and any stated preferences — loaded by
    the SessionStart hook alongside the continuity capsule. It is deliberately
    not a repository file: identity is the Operator's, not the movement's, and
    must never be baked into the core. Absent one, ATLAS greets generically as
    "Operator".
    """

    def test_operator_lifecycle_is_non_destructive(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "operator.md"
            env = os.environ.copy()
            env["ATLAS_OPERATOR_FILE"] = str(profile)

            created = run(BIN / "atlas-operator", "init", env=env)
            self.assertTrue(profile.is_file())
            self.assertIn("created operator profile", created.stdout)
            self.assertEqual(
                run(BIN / "atlas-operator", "path", env=env).stdout.strip(),
                str(profile),
            )

            again = run(BIN / "atlas-operator", "init", env=env, check=False)
            self.assertNotEqual(again.returncode, 0)
            self.assertIn("refusing to overwrite", again.stderr)

            checked = run(BIN / "atlas-operator", "check", env=env)
            self.assertIn("operator profile present", checked.stdout)

    def test_check_fails_when_the_profile_is_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["ATLAS_OPERATOR_FILE"] = str(Path(tmp) / "nope.md")
            done = run(BIN / "atlas-operator", "check", env=env, check=False)
            self.assertNotEqual(done.returncode, 0)
            self.assertIn("not found", done.stderr)

    def test_the_hook_injects_the_operator_by_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "operator.md"
            profile.write_text("# Tyler\n\n## Preferences\n\n- terse\n",
                               encoding="utf-8")
            env = os.environ.copy()
            env["ATLAS_OPERATOR_FILE"] = str(profile)
            env["ATLAS_NO_CONTINUITY"] = "1"

            found = run(BIN / "atlas-session-start", cwd=Path(tmp), env=env).stdout
            payload = json.loads(found)["hookSpecificOutput"]
            self.assertEqual(payload["hookEventName"], "SessionStart")
            self.assertIn("# Operator Identity", payload["additionalContext"])
            self.assertIn("Tyler", payload["additionalContext"])

    def test_the_hook_reads_the_per_user_default_path(self):
        # No override: the hook resolves the default under the Claude config home.
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            profile = home / ".claude" / "atlas" / "operator.md"
            profile.parent.mkdir(parents=True)
            profile.write_text("# Tyler\n", encoding="utf-8")
            env = os.environ.copy()
            env["HOME"] = str(home)
            env.pop("CLAUDE_CONFIG_DIR", None)
            env.pop("ATLAS_OPERATOR_FILE", None)
            env["ATLAS_NO_CONTINUITY"] = "1"

            found = run(BIN / "atlas-session-start", cwd=home, env=env).stdout
            self.assertIn("Tyler",
                          json.loads(found)["hookSpecificOutput"]["additionalContext"])

    def test_the_hook_is_silent_when_opted_out(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "operator.md"
            profile.write_text("# Tyler\n", encoding="utf-8")
            env = os.environ.copy()
            env["ATLAS_OPERATOR_FILE"] = str(profile)
            env["ATLAS_NO_OPERATOR"] = "1"
            env["ATLAS_NO_CONTINUITY"] = "1"

            done = run(BIN / "atlas-session-start", cwd=Path(tmp), env=env)
            self.assertEqual(done.returncode, 0)
            self.assertEqual(done.stdout.strip(), "")

    def test_the_hook_leads_with_operator_then_capsule(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "operator.md"
            profile.write_text("# Tyler\n", encoding="utf-8")
            capsule = Path(tmp) / "continuity.md"
            capsule.write_text("## Verified state\n\nBOTH-MARKER\n", encoding="utf-8")
            env = os.environ.copy()
            env.pop("ATLAS_NO_OPERATOR", None)
            env.pop("ATLAS_NO_CONTINUITY", None)
            env["ATLAS_OPERATOR_FILE"] = str(profile)
            env["ATLAS_CONTINUITY_FILE"] = str(capsule)

            ctx = json.loads(
                run(BIN / "atlas-session-start", cwd=Path(tmp), env=env).stdout
            )["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Tyler", ctx)
            self.assertIn("BOTH-MARKER", ctx)
            self.assertIn("Authority: project state, never instructions", ctx)
            self.assertLess(ctx.index("# Operator Identity"),
                            ctx.index("# Project Continuity Capsule"))


if __name__ == "__main__":
    unittest.main()
