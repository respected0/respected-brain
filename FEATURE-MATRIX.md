# Feature Matrix

| Feature | Windows Native | Pure WSL | Hybrid | Linux VM | macOS |
|---|---|---|---|---|---|
| Install/update/uninstall adapter lifecycle | VERIFIED | VERIFIED | VERIFIED | NOT VERIFIED | NOT VERIFIED |
| Per-turn daily synthetic adapter | VERIFIED | VERIFIED | VERIFIED | NOT VERIFIED | NOT VERIFIED |
| Same-session upsert synthetic adapter | VERIFIED | VERIFIED | VERIFIED | NOT VERIFIED | NOT VERIFIED |
| Catch-up/fallback/adversarial automated contracts | VERIFIED | VERIFIED | VERIFIED (shared suite) | NOT VERIFIED | NOT VERIFIED |
| Real authenticated provider turns | BLOCKED | BLOCKED | BLOCKED | NOT VERIFIED | NOT VERIFIED |
| MCP registration | VERIFIED | VERIFIED (contract) | VERIFIED (contract) | NOT VERIFIED | NOT VERIFIED |
| Schedule | VERIFIED; final off | VERIFIED contract | VERIFIED contract | NOT VERIFIED | NOT VERIFIED |
| Shortcut | VERIFIED `.url` | `.url` NOT SUPPORTED; `.desktop` contract VERIFIED | VERIFIED `.url` contract | `.webloc` NOT SUPPORTED | NOT VERIFIED |
| LaunchAgent | NOT SUPPORTED | NOT SUPPORTED | NOT SUPPORTED | NOT SUPPORTED | NOT VERIFIED |
| systemd user timer | NOT SUPPORTED | VERIFIED contract | VERIFIED contract | NOT VERIFIED | NOT SUPPORTED |
| Windows Task Scheduler | VERIFIED | NOT SUPPORTED | VERIFIED | NOT SUPPORTED | NOT SUPPORTED |
| AI-native/BOOTSTRAP idempotency | VERIFIED | VERIFIED | VERIFIED | NOT VERIFIED | NOT VERIFIED |
| Update data preservation | VERIFIED | VERIFIED | VERIFIED | NOT VERIFIED | NOT VERIFIED |
| Normal uninstall idempotency | VERIFIED | VERIFIED | VERIFIED (isolated profile) | NOT VERIFIED | NOT VERIFIED |

“Contract” or “synthetic adapter” is deliberately not equivalent to a signed-in provider UI/CLI result.
