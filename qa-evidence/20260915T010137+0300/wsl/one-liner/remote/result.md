# Result

Status: FAILED

Executed the exact published `curl -sSL .../install.sh | bash` entry point. It exited 1: piped execution referenced unset `BASH_SOURCE[0]`, then resolved an installer from the caller directory and ended at EOF. Local stdin regression passes, but the public script remains unchanged because no push/merge was authorized.
