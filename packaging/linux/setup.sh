#!/bin/sh
# Respected SecondBrain installer for Linux: the program files are this script's; the product sets up the rest.
#   ./setup.sh [--vault DIR] [--set KEY=VALUE]...   install (or repair when already installed)
#   ./setup.sh --uninstall [--purge]                remove (--purge also deletes settings and data, never the vault)
set -eu
script_dir=$(CDPATH= cd -P "$(dirname "$0")" && pwd)
package="$script_dir/RespectedBrain"
: "${HOME:?HOME is required}"
: "${RESPECTED_APP_DIR:=$HOME/.local/lib/respectedbrain}"
export RESPECTED_APP_DIR
if [ "${1:-}" = "--uninstall" ]; then
    shift
    "$RESPECTED_APP_DIR/respectedbrain" uninstall "$@"
    rm -rf "$RESPECTED_APP_DIR"
    exit 0
fi
installed=no
[ -x "$RESPECTED_APP_DIR/respectedbrain" ] && "$RESPECTED_APP_DIR/respectedbrain" health >/dev/null 2>&1 && installed=yes
mkdir -p "$RESPECTED_APP_DIR"
cp -R "$package/." "$RESPECTED_APP_DIR/"
if [ "$installed" = yes ]; then
    exec "$RESPECTED_APP_DIR/respectedbrain" repair
fi
exec "$RESPECTED_APP_DIR/respectedbrain" setup --platform posix "$@"
