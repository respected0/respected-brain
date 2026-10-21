"""Strict fixture lifecycle proves the manifest attestation reaches every consumer."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from respectedbrain import __version__
from respectedbrain.core.config import ConfigStore
from respectedbrain.core.paths import Roots
from respectedbrain.installation.deferred import defer_operation, resume_operation
from respectedbrain.installation.ownership import digest, read_manifest
from respectedbrain.installation.provenance import TrustedProvenancePolicy
from respectedbrain.installation.repair import repair
from respectedbrain.installation.setup import setup
from respectedbrain.installation.update import update
from respectedbrain.vault.registry import build_context
from tests.support.packages import seed_package
from tests.support.fakes import Backend
from respectedbrain.core.errors import OwnershipConflict
from respectedbrain.installation.provenance import verify_release_provenance
from tests.support.packages import fixture_gh


ATTESTATION = "distribution.json.attestation.json"


def attach_attestation(package: Path) -> Path:
    manifest = package / "distribution.json"
    statement = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{
            "name": "distribution.json",
            "digest": {"sha256": hashlib.sha256(manifest.read_bytes()).hexdigest()},
        }],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {"buildDefinition": {"externalParameters": {"workflow": {
            "repository": "https://github.com/respected0/respected-secondbrain",
            "path": ".github/workflows/release.yml",
            "ref": f"refs/tags/v{__version__}",
        }}}},
    }
    bundle = {
        "mediaType": "application/vnd.dev.sigstore.bundle+json;version=0.2",
        "dsseEnvelope": {
            "payload": base64.b64encode(json.dumps(statement).encode()).decode(),
            "payloadType": "application/vnd.in-toto+json",
            "signatures": [{"sig": "fixture-policy"}],
        },
    }
    target = package / ATTESTATION
    target.write_text(json.dumps(bundle), encoding="utf-8")
    return target


class ProvenanceLifecycleTransportTest(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "win32", "deferred activation is Windows-only")
    def test_attestation_survives_setup_update_repair_and_deferred_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            roots = Roots(root / "app", root / "data", root / "vault")
            home = root / "home"
            home.mkdir()
            backend = Backend()
            packages = [seed_package(root / f"package-{index}", content=f"MZ-{index}".encode()) for index in range(3)]
            for package in packages:
                attach_attestation(package)
            policy = TrustedProvenancePolicy(
                expected_ref=f"refs/tags/v{__version__}",
                verifier_callable=lambda *_: (True, "explicit fixture policy"),
            )
            policy_patch = mock.patch(
                "respectedbrain.installation.provenance.TrustedProvenancePolicy",
                return_value=policy,
            )
            health_patch = mock.patch(
                "respectedbrain.installation.payload.validate_installed_health",
                return_value=None,
            )
            with policy_patch, health_patch:
                result = setup(
                    roots,
                    roots.default_vault,
                    profile={"platform": "windows-native", "user_home": str(home)},
                    desired={"global": False, "mcp": False, "schedule": False, "shortcut": False},
                    backend=backend,
                    package=packages[0],
                    require_provenance=True,
                )
                self.assertTrue(result.success, result.conflicts)
                self.assertTrue((roots.app_root / ATTESTATION).is_file())
                self.assertIn(roots.app_root / ATTESTATION, {item.path for item in read_manifest(roots.data_root / "install-manifest.json").files})
                store = ConfigStore(roots.data_root)
                ctx = build_context(roots, store, vault=roots.default_vault, vault_id=None, env={})
                result = update(ctx, package=packages[1], backend=backend, require_provenance=True)
                self.assertTrue(result.success, result.conflicts)
                self.assertTrue((roots.app_root / ATTESTATION).is_file())
                result = repair(ctx, backend=backend, require_provenance=True)
                self.assertTrue(result.success, result.conflicts)

                captured = []

                def capture(*command, **kwargs):
                    captured.append(command[0])
                    return mock.Mock()

                launcher = roots.app_root / "respectedbrain.exe"
                with (
                    mock.patch("respectedbrain.installation.deferred.sys.frozen", True, create=True),
                    mock.patch("respectedbrain.installation.deferred.sys.executable", str(launcher)),
                    mock.patch("respectedbrain.installation.deferred.subprocess.Popen", side_effect=capture),
                    mock.patch("respectedbrain.installation.deferred._wait_parent", return_value=None),
                ):
                    pending = defer_operation(ctx, mode="update", package=packages[2], require_provenance=True)
                self.assertTrue(pending.pending)
                request = Path(captured[-1][captured[-1].index("--request") + 1])
                with mock.patch("respectedbrain.installation.deferred._wait_parent", return_value=None):
                    self.assertEqual(resume_operation(request, expected_hash=digest(request), require_provenance=True), 0)
            self.assertTrue((roots.app_root / ATTESTATION).is_file())
            self.assertIn(roots.app_root / ATTESTATION, {item.path for item in read_manifest(roots.data_root / "install-manifest.json").files})


DESIRED = {"global": False, "mcp": False, "schedule": False, "shortcut": False}


def break_attestation(package: Path) -> None:
    """Replace the attestation envelope with an unusable, non-empty document."""
    (package / ATTESTATION).write_text(json.dumps({"dsseEnvelope": {"signatures": []}}), encoding="utf-8")


def drop_attestation(package: Path) -> None:
    (package / ATTESTATION).unlink()


class ProvenanceFailClosedTest(unittest.TestCase):
    """A missing or corrupt attestation must stop every consumer before writes."""

    def _install(self, root: Path):
        roots = Roots(root / "app", root / "data", root / "vault")
        home = root / "home"
        home.mkdir()
        backend = Backend()
        package = seed_package(root / "package", content=b"MZ-installed")
        with fixture_gh(root), mock.patch("respectedbrain.installation.payload.validate_installed_health", return_value=None):
            result = setup(
                roots,
                roots.default_vault,
                profile={"platform": "windows-native", "user_home": str(home)},
                desired=dict(DESIRED),
                backend=backend,
                package=package,
                require_provenance=True,
            )
        self.assertTrue(result.success, result.conflicts)
        ctx = build_context(roots, ConfigStore(roots.data_root), vault=roots.default_vault, vault_id=None, env={})
        return roots, backend, ctx

    def test_update_rejects_missing_attestation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            roots, backend, ctx = self._install(root)
            before = (roots.app_root / "respectedbrain.exe").read_bytes()
            bad = seed_package(root / "update-package", content=b"MZ-update")
            drop_attestation(bad)
            result = update(ctx, package=bad, backend=backend)
            self.assertFalse(result.success)
            self.assertEqual((roots.app_root / "respectedbrain.exe").read_bytes(), before)

    def test_update_rejects_corrupt_attestation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            roots, backend, ctx = self._install(root)
            bad = seed_package(root / "update-package", content=b"MZ-update")
            break_attestation(bad)
            result = update(ctx, package=bad, backend=backend)
            self.assertFalse(result.success)

    def test_repair_rejects_missing_attestation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            roots, backend, ctx = self._install(root)
            drop_attestation(roots.app_root)
            result = repair(ctx, backend=backend)
            self.assertFalse(result.success)

    def test_repair_rejects_corrupt_attestation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            roots, backend, ctx = self._install(root)
            break_attestation(roots.app_root)
            result = repair(ctx, backend=backend)
            self.assertFalse(result.success)

    @unittest.skipUnless(sys.platform == "win32", "deferred activation is Windows-only")
    def test_deferred_update_rejects_missing_attestation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            roots, backend, ctx = self._install(root)
            bad = seed_package(root / "update-package", content=b"MZ-update")
            drop_attestation(bad)
            with (
                mock.patch("respectedbrain.installation.deferred.sys.frozen", True, create=True),
                mock.patch("respectedbrain.installation.deferred.sys.executable", str(roots.app_root / "respectedbrain.exe")),
                mock.patch("respectedbrain.installation.deferred.sys.platform", "win32"),
            ):
                with self.assertRaises(OwnershipConflict):
                    defer_operation(ctx, mode="update", package=bad, require_provenance=True)


class ReleaseSignatureSeparationTest(unittest.TestCase):
    """Fixture provenance is a test seam; the real release path stays fail-closed."""

    def test_fixture_envelope_without_verifier_seam_fails_closed(self):
        import base64
        import hashlib
        policy = TrustedProvenancePolicy(expected_ref=f"refs/tags/v{__version__}")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            payload = {
                "_type": "https://in-toto.io/Statement/v1",
                "subject": [{"name": "distribution.json", "digest": {"sha256": hashlib.sha256(b"x").hexdigest()}}],
                "predicateType": "https://slsa.dev/provenance/v1",
                "predicate": {"buildDefinition": {"externalParameters": {"workflow": {
                    "repository": "https://github.com/respected0/respected-secondbrain",
                    "path": ".github/workflows/release.yml",
                    "ref": f"refs/tags/v{__version__}",
                }}}},
            }
            bundle = {
                "dsseEnvelope": {
                    "payload": base64.b64encode(json.dumps(payload).encode()).decode(),
                    "payloadType": "application/vnd.in-toto+json",
                    "signatures": [{"sig": "fixture-policy"}],
                },
            }
            artifact = root / "distribution.json"
            artifact.write_bytes(b"x")
            bundle_file = root / "distribution.json.attestation.json"
            bundle_file.write_text(json.dumps(bundle), encoding="utf-8")
            with mock.patch("shutil.which", return_value=None):
                ok, reason, _ = verify_release_provenance(artifact, bundle_file, policy=policy)
            self.assertFalse(ok)
            self.assertIn("verifier not available", reason.lower())


if __name__ == "__main__":
    unittest.main()
