#!/bin/sh
# install.sh — put the `atlas` command on your PATH.
#
# Recommended (install and use in the SAME shell, no reload):
#
#     eval "$(./install.sh)"
#
# Plain form (installs durably; open a new terminal to use it):
#
#     ./install.sh
#
# What it does: symlinks bin/atlas into ~/.local/bin, and makes sure that
# directory is on your PATH now and in future shells. All human-readable output
# goes to stderr; the ONLY thing written to stdout is a PATH line, so wrapping
# the call in eval "$(...)" updates your current shell without a restart.
set -eu
CDPATH=''

log() { echo "$@" >&2; }

# Repo root = the directory containing this script, resolved through symlinks.
SOURCE=$0
while [ -h "$SOURCE" ]; do
  dir=$(cd -P "$(dirname "$SOURCE")" && pwd)
  SOURCE=$(readlink "$SOURCE")
  case $SOURCE in
    /*) ;;
    *) SOURCE=$dir/$SOURCE ;;
  esac
done
REPO=$(cd -P "$(dirname "$SOURCE")" && pwd)

if [ ! -f "$REPO/bin/atlas" ]; then
  log "install: $REPO/bin/atlas not found."
  log "install: run this from inside the ATLAS repository."
  exit 1
fi
chmod +x "$REPO/bin/atlas" 2>/dev/null || true

command -v claude >/dev/null 2>&1 || \
  log "install: note — 'claude' is not on your PATH yet. Install Claude Code before running atlas."

BIN="$HOME/.local/bin"
mkdir -p "$BIN"
ln -sf "$REPO/bin/atlas" "$BIN/atlas"
log "linked $BIN/atlas -> $REPO/bin/atlas"

# Is ~/.local/bin already on PATH?
on_path=0
case ":$PATH:" in
  *":$BIN:"*) on_path=1 ;;
esac

# Append a PATH line to a shell rc, once, if it does not already reference it.
add_rc() {
  rc=$1
  [ -e "$rc" ] || return 0
  if grep -q '.local/bin' "$rc" 2>/dev/null; then
    return 0
  fi
  printf '\n# added by ATLAS install.sh\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$rc"
  log "added ~/.local/bin to PATH in $rc"
}

if [ "$on_path" = 1 ]; then
  log "atlas installed. ~/.local/bin is already on your PATH."
  log "Run:  atlas"
  # Nothing to stdout: the command is already reachable in a PATH search.
else
  add_rc "$HOME/.zshrc"
  add_rc "$HOME/.bashrc"
  add_rc "$HOME/.bash_profile"
  add_rc "$HOME/.profile"
  # Activate the current shell. Consumed by eval "$(./install.sh)".
  printf 'export PATH="%s:$PATH"\n' "$BIN"
  log "atlas installed. ~/.local/bin was added to your PATH for future shells."
  log "To use it in THIS shell without reloading, run:  eval \"\$(./install.sh)\""
  log "Otherwise open a new terminal, then:  atlas"
fi
