# Result

Status: VERIFIED

Published `main` at product commit `b835c19` was executed through `curl -sSL ... | bash -s -- ...` in a disposable WSL Linux-filesystem HOME and vault. Install, two same-version updates, and two data-preserving uninstalls returned exit 0. The Journal SHA-256 matched before/after both updates, the vault survived uninstall, and no install/update/uninstall staging directory remained.
