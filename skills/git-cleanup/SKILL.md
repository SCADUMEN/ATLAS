---
name: git-cleanup
description: Clean up merged branches and worktrees, prune remote refs, and pull the latest main.
---

# /git-cleanup

Clean up the local git repo: remove merged worktrees, delete merged branches,
prune remote tracking refs, and pull the latest main branch.

## How to tell a branch is merged

Two branches are "merged" here even when git's own `--merged` says no, because a
squash merge rewrites history so the local commits are never ancestors of main.
Check in this order, and treat any one as merged:

1. **Ancestor merge** — the branch appears in `git branch --merged main`.
2. **Squash merge, remote deleted** — the upstream is gone: `git branch -vv`
   marks it `[origin/<name>: gone]` after a prune.
3. **Squash merge, remote kept** — the trees are identical:
   `git diff --quiet main <branch>` exits 0 (no content differs). GitHub does not
   always delete the head branch on merge, so signal 2 alone misses these — this
   is the reliable check.

If none hold, the branch has unmerged work: report it to the operator and skip
it. Never force-delete unmerged work.

## Steps

### 1. Prune first

Run `git fetch --prune` (or `git remote prune origin`) so upstream-gone branches
are marked before anything is judged merged.

### 2. Remove worktrees

Run `git worktree list`. For each worktree other than the main working directory,
apply the merge test above to its branch:

- Merged: `git worktree remove <path>` (add `--force` only if it holds
  uncommitted changes and the branch is otherwise merged).
- Not merged: report and skip.

Then `git worktree prune` to clear stale metadata.

### 3. Delete local branches

Run `git branch`. For each branch other than the one currently checked out and
`main`:

- Merged by signal 1: `git branch -d <name>`.
- Merged by signal 2 or 3 (squash): `git branch -D <name>` (`-d` refuses a
  squash-merged branch because git cannot see the merge).
- Not merged: report and skip.

### 4. Prune remote refs

Run `git remote prune origin` to drop stale remote tracking branches. Optionally,
offer to delete a merged branch's lingering remote head with
`git push origin --delete <name>` — confirm with the operator first, since it is
an outward-facing change.

### 5. Pull latest main

`git checkout main` and `git pull --ff-only`.

### 6. Report

Show the final state (`git branch -a` and `git worktree list`) and summarize what
was removed and what was skipped, with the reason for each skip.
