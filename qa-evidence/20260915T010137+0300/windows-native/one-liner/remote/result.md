# Result

Status: FAILED

Executed the exact published `irm .../install.ps1 | iex` entry point. It exited 1 during parameter binding because the raw `main` script applies `ValidateSet` to an existing empty `Environment` variable. Local RED/GREEN regression passes, but the public script remains unchanged because no push/merge was authorized.
