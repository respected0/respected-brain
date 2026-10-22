"""Fresh-vault project hook files for tests that need a vault carrying real provider manifests."""
import json

from respected_brain.integrations.backend import IntegrationProfile
from respected_brain.integrations.rendering import _Planner, _global_writes, validate_profile

_FILES = {".claude/settings.json": ".claude/settings.json", ".codex/hooks.json": ".codex/hooks.json", ".cursor/hooks.json": ".cursor/hooks.json",
          ".gemini/config/hooks.json": ".agents/hooks.json", ".gemini/settings.json": ".gemini/settings.json"}


class _EmptyBackend:
    def read(self, kind, key):
        return None


def local_commands(value):
    """The project-local variant of a global hook command: no --global-hook flag."""
    if isinstance(value, dict):
        return {key: item.replace(" --global-hook", "") if key == "command" and isinstance(item, str) else local_commands(item) for key, item in value.items()}
    if isinstance(value, list):
        return [local_commands(item) for item in value]
    return value


def render_project_integrations(ctx, profile):
    validate_profile(ctx, profile)
    local_profile = IntegrationProfile(profile.platform, profile.launcher, ctx.paths.vault_root)
    writes, _ = _global_writes(ctx, local_profile, _Planner(_EmptyBackend()))
    result = {}
    for path, content in writes:
        relative = path.relative_to(ctx.paths.vault_root).as_posix()
        if relative in _FILES:
            result[_FILES[relative]] = (json.dumps(local_commands(json.loads(content)), ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return result
