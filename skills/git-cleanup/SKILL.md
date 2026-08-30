---
name: git-cleanup
description: Clean up merged branches and worktrees, prune remote refs, and pull the latest main.
---

# /git-cleanup

Clean up the local git repo: remove merged worktrees, delete merged branches,
prune remote tracking refs, and pull the latest main branch.

Deletion is the whole point of this skill, so the bar for calling something
"merged" is the bar for destroying it. Every rule below exists to keep a false
positive from eating work.

## How to tell a branch is merged

A branch is merged when its content is in `main`, by whatever route it got
there. Check the signals in this order and treat **any one** as merged. Where
they disagree, the earlier signal wins.

### 1. Ancestor merge

The branch appears in `git branch --merged main`. True for fast-forward and
real merge commits. On a squash-merge repo this signal is almost never true —
do not treat its absence as evidence of unmerged work.

### 2. Merged pull request on the host

```sh
gh pr list -R <owner>/<repo> --state merged --limit 100 \
  --json headRefName --jq '.[].headRefName'
```

If the branch name appears, the host merged it. Authoritative when the remote
is GitHub, and the only signal that survives a branch being re-committed onto
after its PR merged. Skip this signal when `gh` is unavailable or the remote is
not GitHub.

### 3. Content absorbed — path-scoped diff

The reliable local check, and the one to trust when the others are silent:

```sh
mb=$(git merge-base main "$b")
files=$(git diff --name-only "$mb" "$b")
if [ -z "$files" ]; then
  merged=yes                                    # empty branch, see signal 5
elif git diff --quiet main "$b" -- $files; then
  merged=yes                                    # every touched file matches main
fi
```

Exit 0 means every file the branch touched is byte-identical in `main` — so
the work landed, however it landed.

> **Do not use a whole-tree `git diff --quiet main <branch>`.** It compares the
> entire trees, so it reports a difference whenever `main` has advanced by even
> one unrelated commit — the normal state of any active repo. It returns a false
> "unmerged" on nearly every branch, and it fails *closed-looking*: branches are
> stranded rather than lost, so nobody notices until the branch list is
> unmanageable. Verified against `SCADUMEN/ATLAS` on 2026-08-30: the whole-tree
> form called all 10 merged branches unmerged; the path-scoped form called all 10
> correctly.

Scope the diff with `--` and the touched file list. That is the entire fix.

### 4. Upstream gone

After a prune, `git branch -vv` marks the branch `[origin/<name>: gone]`.

**Corroborating only — never sufficient on its own.** A branch is also `gone`
when someone deleted it *unmerged*, and when a `gh pr checkout` branch's remote
was removed. Require signal 1, 2, or 3 as well before deleting on this basis.

### 5. Empty branch

The branch touches no files versus its merge-base. Nothing to lose; safe to
delete.

### The no-upstream class

Branches created by `gh pr checkout` (typically named `pr12`, `pr15`, …) and any
branch never pushed have **no upstream at all**, so signal 4 can never fire for
them — they will never be marked `gone` and any gone-based cleanup passes over
them forever. Judge these by signal 2 or 3 like anything else. A local-only
branch whose content is *not* absorbed is genuine unpushed work: report it and
never delete it.

If no signal holds, the branch has unmerged work. Report it to the operator and
skip it. Never force-delete unmerged work.

## Steps

### 0. Archive before you delete

Before removing anything, write a recovery manifest recording every branch name
and full SHA, and the path of every worktree, that this run intends to remove —
plus which signal justified each one. Save it outside the repo (deleting the
clone must not delete the manifest).

Any branch in it is restorable with:

```sh
git push origin <sha>:refs/heads/<name>
```

GitHub retains objects from deleted branches for roughly 90 days, so the
manifest is only useful inside that window — note the date in it. Do not skip
this step because the deletions "look obviously safe". They looked obviously
safe to the check that was wrong.

### 1. Prune first

Run `git fetch --prune` (or `git remote prune origin`) so upstream-gone
branches are marked before anything is judged.

### 2. Remove worktrees

Run `git worktree list`. For each worktree other than the main working
directory, apply the merge test to its branch:

- Merged **and clean** (`git -C <path> status --porcelain` is empty):
  `git worktree remove <path>`.
- **Dirty — stop.** Uncommitted changes exist in no other place by definition,
  so a merged branch says nothing about them. Report the worktree and its dirty
  files and skip it. Never pass `--force` to clear uncommitted work; offer the
  operator a `git stash` or a commit instead, and let them decide.
- Not merged: report and skip.

Then `git worktree prune` to clear stale metadata. Note that a worktree may be
registered in a *different* clone than the one you are standing in — prune from
the clone that owns it, or the registration is left dangling.

### 3. Delete local branches

Run `git branch`. For each branch other than the one currently checked out and
`main`:

- Merged by signal 1: `git branch -d <name>`.
- Merged by signal 2, 3, or 5: `git branch -D <name>`. `-d` refuses a
  squash-merged branch because git cannot see the merge — the manifest from
  step 0 is what makes `-D` acceptable here.
- Not merged: report and skip.

### 4. Prune remote refs

Run `git remote prune origin` to drop stale remote tracking branches.

Deleting a *remote* branch is an outward-facing, hard-to-reverse change on a
repo other people may be reading. Confirm with the operator first, present the
full list rather than deleting one at a time, then:

```sh
git push origin --delete <name> [<name> ...]
```

### 5. Pull latest main

`git checkout main` and `git pull --ff-only`.

### 6. Report

Show the final state (`git branch -a` and `git worktree list`) and summarize:

- what was removed, and which signal justified each removal
- what was skipped, and why — dirty worktrees and unmerged branches by name
- where the manifest was written, and the date its remote objects expire
