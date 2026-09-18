"""Contract tests with opaque temporary bytes, not CBAP conformance vectors."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cbap1_validator import ConfigurationError, ManifestValidator, main


# Fixture declarations derived directly from invariants sections 2, 5, 6, and 10.
# Draft section 6 supplies initialization; section 7.2.1 supplies exhaustive
# ownership and preservation of all earlier successful completions.
INITIAL = {
    "binding": "indeterminate", "pre_execution_evidence": "indeterminate",
    "discoverability": "indeterminate", "forum_acknowledgement": "indeterminate",
    "forum_operational_status": "not_checked", "selection_provenance": "indeterminate",
    "access_binding": "indeterminate", "notice_evidence": "indeterminate",
    "retrievability": "not_checked", "filing_window_status": "indeterminate",
    "policy_freshness": "indeterminate", "declared_effect": "indeterminate",
    "effect_acceptance": "indeterminate", "effect_trigger": "indeterminate",
    "effect_ordering": "indeterminate", "effect_application": "indeterminate",
    "reasons": [],
}
AFTER_B3 = {**INITIAL, "notice_evidence": "not_claimed"}
AFTER_B5 = {
    **AFTER_B3, "declared_effect": "none", "effect_acceptance": "not_required",
    "effect_trigger": "not_applicable", "effect_ordering": "not_applicable",
    "effect_application": "not_applicable",
}
AFTER_B13 = {**AFTER_B5, "discoverability": "complete"}
AFTER_B14 = {**AFTER_B13, "binding": "valid", "selection_provenance": "unilateral"}
AFTER_B19 = {**AFTER_B14, "pre_execution_evidence": "executor_attested"}
POSITIVE = {
    **AFTER_B19, "forum_acknowledgement": "valid_exact", "access_binding": "valid",
    "filing_window_status": "open",
}

# Each row: boundary, count, reason, state BEFORE this boundary, negative
# updates for each predicate in order. No validator transition helper is used.
BINDING = {"binding": "invalid"}
ACCESS = {"access_binding": "invalid"}
FORUM = {"forum_acknowledgement": "invalid"}
SCOPE = {"forum_acknowledgement": "invalid_scope"}
EVIDENCE = {"pre_execution_evidence": "invalid"}
CASES = (
    (1, 1, "verification_time_invalid", INITIAL, [{}]),
    (2, 3, "outer_encoding_invalid", INITIAL, [{}] * 3),
    (3, 5, "bundle_schema_invalid", INITIAL, [{}] * 5),
    (4, 4, "policy_set_invalid", AFTER_B3, [{}] * 4),
    (5, 8, "cpo_invalid", AFTER_B3, [{}] * 7 + [{**BINDING, **ACCESS}]),
    (6, 8, "forum_acceptance_invalid", AFTER_B5, [FORUM] * 8),
    (7, 8, "authorization_invalid", AFTER_B5, [BINDING] * 8),
    (8, 8, "executor_verification_invalid", AFTER_B5, [EVIDENCE] * 8),
    (9, 8, "execution_record_invalid", AFTER_B5, [EVIDENCE] * 8),
    (10, 1, "cpo_binding_mismatch", AFTER_B5, [BINDING]),
    (11, 1, "acceptance_binding_mismatch", AFTER_B5, [FORUM]),
    (12, 4, "action_digest_mismatch", AFTER_B5, [BINDING] * 2 + [EVIDENCE] * 2),
    (13, 9, "profile_binding_mismatch", AFTER_B5, [
        {}, {}, {**BINDING, **ACCESS}, {}, {}, {}, {},
        {"discoverability": "incomplete"}, {"discoverability": "complete"},
    ]),
    (14, 3, "authorization_projection_mismatch", AFTER_B13, [BINDING] * 3),
    (15, 3, "forum_terms_mismatch", AFTER_B14, [SCOPE, FORUM, FORUM]),
    (16, 2, "authorization_digest_mismatch", AFTER_B14, [EVIDENCE] * 2),
    (17, 2, "executor_verification_mismatch", AFTER_B14, [EVIDENCE] * 2),
    (18, 2, "execution_record_mismatch", AFTER_B14, [EVIDENCE] * 2),
    (19, 1, "executor_ordering_invalid", AFTER_B14, [EVIDENCE]),
    (20, 1, "filing_deadline_overflow", AFTER_B19, [{}]),
    (21, 6, "filing_horizon_invalid", AFTER_B19, [SCOPE] * 3 + [{}, {}, ACCESS]),
)


class ValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = ManifestValidator()
        cls.schema = json.loads((ROOT / "contract/vector-manifest-v0.1.schema.json").read_text())

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cbap1-validator-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        # Arbitrary bytes deliberately carry no protocol or case semantics.
        self.artifact = self.base / "opaque.bin"
        self.artifact.write_bytes(b"opaque\x00\xff\r\nbytes\n")

    def positive(self):
        return {
            "vector_id": "positive-test", "class": "positive",
            "authority": "draft-pinto-cbap-1-00",
            "authority_sha256": "98994fbbe5c45981711c0da1464b290ac34410dc51918a78182bb8ad5bf57114",
            "artifact": self.artifact.name,
            "sha256": hashlib.sha256(self.artifact.read_bytes()).hexdigest(),
            "expected_reason": None, "expected_result": deepcopy(POSITIVE),
        }

    def negative(self, boundary=1, predicate=1, uri_kind="other-required-uri"):
        _, _, reason, before, transitions = CASES[boundary - 1]
        manifest = self.positive()
        surface = f"B{boundary}.P{predicate:02d}"
        manifest.update({
            "vector_id": surface.lower().replace(".", "-") + "-test",
            "class": "verifier-negative", "target_surface": surface,
            "expected_reason": reason,
            "expected_result": deepcopy({**before, **transitions[predicate - 1], "reasons": [reason]}),
        })
        if surface == "B13.P06":
            manifest["uri_instance_kind"] = uri_kind
            if uri_kind == "affected-party-discovery-uri":
                manifest["expected_result"]["access_binding"] = "invalid"
        return manifest

    def assertValid(self, manifest):
        self.assertEqual(self.validator.validate(manifest, artifact_root=self.base), ())

    def assertInvalid(self, manifest, diagnostic=None):
        errors = self.validator.validate(manifest, artifact_root=self.base)
        self.assertTrue(errors)
        if diagnostic:
            self.assertIn(diagnostic, "\n".join(errors))

    def negative_manifests(self):
        for boundary, count, _, _, transitions in CASES:
            self.assertEqual(len(transitions), count)
            for predicate in range(1, count + 1):
                yield self.negative(boundary, predicate)
        yield self.negative(13, 6, "affected-party-discovery-uri")

    def test_all_positive_filing_states(self):
        # Draft section 7.1: choosing among these is the manifest's oracle.
        for status in ("not_open", "open", "closed"):
            with self.subTest(status=status):
                manifest = self.positive()
                manifest["expected_result"]["filing_window_status"] = status
                self.assertValid(manifest)

    def test_all_inventory_surfaces_and_both_uri_kinds(self):
        seen = set()
        for manifest in self.negative_manifests():
            with self.subTest(surface=manifest["target_surface"], kind=manifest.get("uri_instance_kind")):
                self.assertValid(manifest)
                seen.add(manifest["target_surface"])
        self.assertEqual(len(seen), 88)
        self.assertEqual(seen, self.validator.surfaces)

    def test_every_alternative_semantic_value_is_rejected_on_negative_paths(self):
        # Draft sections 6 and 7.2.1: exhaustive transitions leave no extra
        # freedom in a negative state, including within the failed boundary.
        properties = self.schema["$defs"]["structured_result"]["properties"]
        for manifest in self.negative_manifests():
            for field, definition in properties.items():
                if field == "reasons":
                    continue
                for alternative in definition.get("enum", ["invalid"]):
                    if alternative == manifest["expected_result"][field]:
                        continue
                    with self.subTest(surface=manifest["target_surface"], kind=manifest.get("uri_instance_kind"), field=field, value=alternative):
                        bad = deepcopy(manifest)
                        bad["expected_result"][field] = alternative
                        self.assertInvalid(bad)

    def test_positive_fixed_fields_cannot_change(self):
        properties = self.schema["$defs"]["structured_result"]["properties"]
        for field, definition in properties.items():
            if field == "reasons":
                continue
            for alternative in definition.get("enum", ["invalid"]):
                if alternative == POSITIVE[field] or (field == "filing_window_status" and alternative != "indeterminate"):
                    continue
                with self.subTest(field=field, value=alternative):
                    manifest = self.positive()
                    manifest["expected_result"][field] = alternative
                    self.assertInvalid(manifest, field)

    def test_unknown_fields(self):
        for nested in (False, True):
            with self.subTest(nested=nested):
                manifest = self.positive()
                target = manifest["expected_result"] if nested else manifest
                target["unknown_field"] = "test"
                self.assertInvalid(manifest, "Additional properties")

    def test_every_required_manifest_field(self):
        for field in self.schema["required"]:
            with self.subTest(field=field):
                manifest = self.positive()
                del manifest[field]
                self.assertInvalid(manifest, "required property")

    def test_every_required_result_field(self):
        for field in self.schema["$defs"]["structured_result"]["required"]:
            with self.subTest(field=field):
                manifest = self.positive()
                del manifest["expected_result"][field]
                self.assertInvalid(manifest, "required property")

    def test_manifest_types(self):
        for field in self.negative(13, 6):
            for wrong in ([], {}, 0, True, None):
                with self.subTest(field=field, value=wrong):
                    manifest = self.negative(13, 6)
                    manifest[field] = wrong
                    self.assertInvalid(manifest)

    def test_result_types_and_unknown_values(self):
        for field in POSITIVE:
            for wrong in (None, 0, True, {}, "unknown_value"):
                with self.subTest(field=field, value=wrong):
                    manifest = self.positive()
                    manifest["expected_result"][field] = wrong
                    self.assertInvalid(manifest)

    def test_non_object_manifests(self):
        for value in (None, [], "test", 0, True):
            with self.subTest(value=value):
                self.assertInvalid(value, "schema")

    def test_closed_class_vocabulary(self):
        for value in ("negative", "Positive", "", "unknown_value"):
            with self.subTest(value=value):
                manifest = self.positive()
                manifest["class"] = value
                self.assertInvalid(manifest, "schema")

    def test_authority_name_and_hash_coherence(self):
        for field, value in (
            ("authority", "draft-pinto-cbap-1-01"), ("authority", "unknown_value"),
            ("authority_sha256", "0" * 64), ("authority_sha256", "A" * 64),
            ("authority_sha256", "abc"),
        ):
            with self.subTest(field=field, value=value):
                manifest = self.positive()
                manifest[field] = value
                self.assertInvalid(manifest, field)

    def test_nonexistent_and_malformed_surfaces(self):
        for surface in ("B1.P02", "B5.P09", "B13.P00", "B13.P10", "B21.P07", "B22.P01", "b1.p01"):
            with self.subTest(surface=surface):
                manifest = self.negative()
                manifest["target_surface"] = surface
                self.assertInvalid(manifest, "target_surface")

    def test_artifact_hash_uses_exact_bytes(self):
        manifest = self.positive()
        self.artifact.write_bytes(self.artifact.read_bytes().replace(b"\r\n", b"\n"))
        self.assertInvalid(manifest, "exact artifact bytes")
        manifest["sha256"] = hashlib.sha256(self.artifact.read_bytes()).hexdigest()
        self.assertValid(manifest)

    def test_invalid_artifact_hash_format(self):
        for value in ("0" * 63, "G" * 64, "A" * 64):
            with self.subTest(value=value):
                manifest = self.positive()
                manifest["sha256"] = value
                self.assertInvalid(manifest, "sha256")

    def test_missing_directory_and_invalid_artifact_paths(self):
        for value in ("missing.bin", ".", "\x00", ""):
            with self.subTest(value=value):
                manifest = self.positive()
                manifest["artifact"] = value
                self.assertInvalid(manifest, "artifact")

    def test_empty_artifact_is_hashed_without_interpretation(self):
        self.artifact.write_bytes(b"")
        self.assertValid(self.positive())

    def test_positive_class_rules(self):
        for field, value in (
            ("expected_reason", "cpo_invalid"), ("target_surface", "B1.P01"),
            ("uri_instance_kind", "other-required-uri"),
        ):
            with self.subTest(field=field):
                manifest = self.positive()
                manifest[field] = value
                self.assertInvalid(manifest)
        manifest = self.positive()
        manifest["expected_result"]["reasons"] = ["cpo_invalid"]
        self.assertInvalid(manifest)

    def test_negative_class_rules(self):
        manifest = self.negative()
        del manifest["target_surface"]
        self.assertInvalid(manifest)
        manifest = self.negative()
        manifest["expected_reason"] = None
        self.assertInvalid(manifest)
        for reasons in ([], ["unknown_value"], [None], ["verification_time_invalid"] * 2):
            with self.subTest(reasons=reasons):
                manifest = self.negative()
                manifest["expected_result"]["reasons"] = reasons
                self.assertInvalid(manifest)

    def test_vector_id_prefix_and_separator(self):
        for value in ("b13-p061-test", "b13-p06", "b13-p05-test", "test-b13-p06-test", "B13-P06-test", "b13-p06-"):
            with self.subTest(value=value):
                manifest = self.negative(13, 6)
                manifest["vector_id"] = value
                self.assertInvalid(manifest)

    def test_vector_id_suffix_has_no_semantics(self):
        for value in ("b13-p06-a", "b13-p06-b1-p01", "b13-p06-affected-party-discovery-uri"):
            manifest = self.negative(13, 6)
            manifest["vector_id"] = value
            self.assertValid(manifest)

    def test_uri_discriminator_required_and_closed(self):
        manifest = self.negative(13, 6)
        del manifest["uri_instance_kind"]
        self.assertInvalid(manifest)
        for value in ("unknown_value", "", None, 1):
            with self.subTest(value=value):
                manifest = self.negative(13, 6)
                manifest["uri_instance_kind"] = value
                self.assertInvalid(manifest)

    def test_uri_discriminator_forbidden_elsewhere(self):
        for manifest in [self.positive(), *self.negative_manifests()]:
            if manifest.get("target_surface") == "B13.P06":
                continue
            with self.subTest(surface=manifest.get("target_surface")):
                manifest["uri_instance_kind"] = "other-required-uri"
                self.assertInvalid(manifest)

    def test_uri_discriminator_controls_only_its_transition(self):
        for original, replacement in (
            ("other-required-uri", "affected-party-discovery-uri"),
            ("affected-party-discovery-uri", "other-required-uri"),
        ):
            manifest = self.negative(13, 6, original)
            manifest["uri_instance_kind"] = replacement
            self.assertInvalid(manifest, "expected_result.access_binding")

    def test_reason_coherence(self):
        for manifest in self.negative_manifests():
            with self.subTest(surface=manifest["target_surface"]):
                wrong_reason = "cpo_invalid" if manifest["expected_reason"] != "cpo_invalid" else "outer_encoding_invalid"
                bad = deepcopy(manifest)
                bad["expected_reason"] = wrong_reason
                self.assertInvalid(bad, "expected_reason")
                bad["expected_result"]["reasons"] = [wrong_reason]
                self.assertInvalid(bad, "expected_reason")
                bad = deepcopy(manifest)
                bad["expected_result"]["reasons"] = [wrong_reason]
                self.assertInvalid(bad, "expected_result.reasons")

    def test_b13_p09_does_not_imply_boundary_success(self):
        # Draft section 7.2.1 / invariants section 8: complete is explicitly
        # assigned on this failure; B14 completions are still unreachable.
        manifest = self.negative(13, 9)
        self.assertEqual(manifest["expected_result"]["discoverability"], "complete")
        self.assertValid(manifest)
        manifest["expected_result"]["binding"] = "valid"
        manifest["expected_result"]["selection_provenance"] = "unilateral"
        self.assertInvalid(manifest, "unreachable")

    def test_file_resolution_and_override(self):
        directory = self.base / "manifests"
        directory.mkdir()
        path = directory / "manifest.json"
        manifest = self.positive()
        manifest["artifact"] = "../opaque.bin"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertEqual(self.validator.validate_file(path), ())
        manifest["artifact"] = "opaque.bin"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertTrue(self.validator.validate_file(path))
        self.assertEqual(self.validator.validate_file(path, artifact_root=self.base), ())
        manifest["artifact"] = str(self.artifact)
        self.assertValid(manifest)

    def test_invalid_json_files(self):
        path = self.base / "manifest.json"
        for content in (b"{", b"{} {}", b"\xff", b'{"unknown_field": 0, "unknown_field": 1}', b'{"expected_result": {"binding": 1, "binding": 2}}', b"NaN", b"Infinity", b"-Infinity"):
            with self.subTest(content=content):
                path.write_bytes(content)
                errors = self.validator.validate_file(path)
                self.assertIn("cannot read JSON", errors[0])
        self.assertTrue(self.validator.validate_file(self.base / "missing.json"))

    def test_deterministic_diagnostics_and_no_mutation(self):
        manifest = self.negative(13, 9)
        manifest["expected_result"]["binding"] = "valid"
        before = deepcopy(manifest)
        first = self.validator.validate(manifest, artifact_root=self.base)
        self.assertTrue(first)
        self.assertEqual(first, self.validator.validate(manifest, artifact_root=self.base))
        self.assertEqual(manifest, before)

    def test_cli_success_failure_and_usage(self):
        path = self.base / "manifest.json"
        path.write_text(json.dumps(self.positive()), encoding="utf-8")
        command = [sys.executable, "-B", str(ROOT / "src/cbap1_validator.py")]
        success = subprocess.run(command + [str(path)], cwd=self.base, capture_output=True, text=True)
        self.assertEqual(success.returncode, 0, success.stderr)
        self.assertIn("OK", success.stdout)
        self.assertEqual(success.stderr, "")
        bad = self.base / "bad.json"
        bad.write_text("{}", encoding="utf-8")
        failure = subprocess.run(command + [str(bad), str(path)], capture_output=True, text=True)
        self.assertEqual(failure.returncode, 1)
        self.assertIn("INVALID", failure.stderr)
        self.assertIn("OK", failure.stdout)
        usage = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(usage.returncode, 2)

    def test_cli_artifact_root_and_configuration_failure(self):
        directory = self.base / "manifests"
        directory.mkdir()
        path = directory / "manifest.json"
        path.write_text(json.dumps(self.positive()), encoding="utf-8")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(main(["--artifact-root", str(self.base), str(path)]), 0)
            with patch("cbap1_validator.ManifestValidator", side_effect=ConfigurationError("test")):
                self.assertEqual(main([str(path)]), 2)
            self.assertIn("configuration", errors.getvalue())

    def test_frozen_input_integrity(self):
        root = self.base / "repository"
        shutil.copytree(ROOT / "authority", root / "authority")
        shutil.copytree(ROOT / "contract", root / "contract")
        ManifestValidator(root)
        for relative_path in (
            "authority/draft-pinto-cbap-1-00.txt",
            "authority/CBAP-1-NORMATIVE-SURFACE-INVENTORY-PUBLIC-v1.0-2026-09-16.md",
            "contract/vector-manifest-v0.1.schema.json",
            "contract/VALIDATOR-INVARIANTS-v0.1.md",
        ):
            with self.subTest(path=relative_path):
                path = root / relative_path
                original = path.read_bytes()
                try:
                    path.write_bytes(original + b"\n")
                    with self.assertRaisesRegex(ConfigurationError, "SHA-256 mismatch"):
                        ManifestValidator(root)
                finally:
                    path.write_bytes(original)
        with self.assertRaises(ConfigurationError):
            ManifestValidator(self.base / "missing")


if __name__ == "__main__":
    unittest.main()
