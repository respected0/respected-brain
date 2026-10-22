#!/bin/sh
# Respected Brain installer for macOS: the program bundle is this script's; the product sets up the rest.
#   ./setup.command [--vault DIR] [--set KEY=VALUE]...   install (or repair when already installed)
#   ./setup.command --uninstall [--purge]                remove (--purge also deletes settings and data, never the vault)
set -eu
script_dir=$(CDPATH= cd -P "$(dirname "$0")" && pwd)
package="$script_dir/RespectedBrain.app"
: "${HOME:?HOME is required}"
: "${RESPECTED_APP_DIR:=$HOME/Applications/RespectedBrain.app}"
export RESPECTED_APP_DIR
launcher="$RESPECTED_APP_DIR/Contents/MacOS/respected-brain"
if [ "${1:-}" = "--uninstall" ]; then
    shift
    "$launcher" uninstall "$@"
    rm -rf "$RESPECTED_APP_DIR"
    exit 0
fi
installed=no
[ -x "$launcher" ] && "$launcher" health >/dev/null 2>&1 && installed=yes
mkdir -p "$RESPECTED_APP_DIR"
cp -R "$package/." "$RESPECTED_APP_DIR/"
if [ "$installed" = yes ]; then
    exec "$launcher" repair
fi
exec "$launcher" setup --platform posix "$@"
