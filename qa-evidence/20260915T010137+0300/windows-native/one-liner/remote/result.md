# Result

Status: VERIFIED

Published `main` at product commit `b835c19` was downloaded from `raw.githubusercontent.com` and executed as a PowerShell script block, the parameterized equivalent of `irm .../install.ps1 | iex`. A clean isolated-profile Windows-native install, two same-version updates, and two data-preserving uninstalls returned exit 0. The Unicode/emoji/space vault was retained. Every observed remote clone directory from the fixed run was removed.
