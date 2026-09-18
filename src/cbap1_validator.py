"""Validate frozen CBAP-1 v0.1 manifests, without interpreting artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
AUTHORITY = "draft-pinto-cbap-1-00"
AUTHORITY_SHA256 = "98994fbbe5c45981711c0da1464b290ac34410dc51918a78182bb8ad5bf57114"
INVENTORY = "CBAP-1-NORMATIVE-SURFACE-INVENTORY-PUBLIC-v1.0-2026-09-16.md"
INVENTORY_SHA256 = "93d9f72feff872453b8fac8723dadd68a519860c0c1df17cdeaa1b043ed35a18"
SCHEMA_SHA256 = "ce2231f9eaa3bd8dd620f3fafdba6d07395d55b4f77724ab49b1a1cdcf281d63"
INVARIANTS_SHA256 = "b52a9bd2c396ffc4a62ca346d277b86367675133c16ee50e0fa3a7cf1405346b"

# Invariants section 4; draft section 7.2, B1-B21 failure precedence.
BOUNDARY_REASONS = (
    "verification_time_invalid", "outer_encoding_invalid", "bundle_schema_invalid",
    "policy_set_invalid", "cpo_invalid", "forum_acceptance_invalid",
    "authorization_invalid", "executor_verification_invalid", "execution_record_invalid",
    "cpo_binding_mismatch", "acceptance_binding_mismatch", "action_digest_mismatch",
    "profile_binding_mismatch", "authorization_projection_mismatch", "forum_terms_mismatch",
    "authorization_digest_mismatch", "executor_verification_mismatch",
    "execution_record_mismatch", "executor_ordering_invalid", "filing_deadline_overflow",
    "filing_horizon_invalid",
)

# Invariants sections 2-3; draft section 6 defines the exact initial state.
INITIAL_STATE = {
    "binding": "indeterminate",
    "pre_execution_evidence": "indeterminate",
    "discoverability": "indeterminate",
    "forum_acknowledgement": "indeterminate",
    "forum_operational_status": "not_checked",
    "selection_provenance": "indeterminate",
    "access_binding": "indeterminate",
    "notice_evidence": "indeterminate",
    "retrievability": "not_checked",
    "filing_window_status": "indeterminate",
    "policy_freshness": "indeterminate",
    "declared_effect": "indeterminate",
    "effect_acceptance": "indeterminate",
    "effect_trigger": "indeterminate",
    "effect_ordering": "indeterminate",
    "effect_application": "indeterminate",
}

# Invariants section 5; draft section 7.2.1 owns these positive completions.
# B21's filing classification remains the manifest's oracle (draft section 7.1).
POSITIVE_COMPLETIONS = {
    3: {"notice_evidence": "not_claimed"},
    5: {
        "declared_effect": "none", "effect_acceptance": "not_required",
        "effect_trigger": "not_applicable", "effect_ordering": "not_applicable",
        "effect_application": "not_applicable",
    },
    13: {"discoverability": "complete"},
    14: {"selection_provenance": "unilateral", "binding": "valid"},
    19: {"pre_execution_evidence": "executor_attested"},
    21: {"forum_acknowledgement": "valid_exact", "access_binding": "valid"},
}


class ConfigurationError(Exception):
    """A frozen input is missing, corrupt, or unusable."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON member: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant: {value}")


def _load_json(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
    )


def _sha256_file(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"not an existing file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inventory_surfaces(text: str) -> frozenset[str]:
    """Read predicate headings and the five signed-object pipeline ranges."""
    surfaces = set(re.findall(r"^\*\*(B\d+\.P\d{2}) - ", text, re.MULTILINE))
    for boundary, first, last in re.findall(
        r"^    B(\d+)\.P(\d{2}) \.\. B\1\.P(\d{2})\s", text, re.MULTILINE
    ):
        surfaces.update(f"B{boundary}.P{p:02d}" for p in range(int(first), int(last) + 1))
    if len(surfaces) != 88:
        raise ConfigurationError("frozen inventory must declare exactly 88 surfaces")
    return frozenset(surfaces)


def _negative_transition(boundary: int, predicate: int, uri_kind: str | None) -> dict[str, str]:
    # Exhaustive ownership: invariants section 6 / draft section 7.2.1.
    # The caller has already checked membership in the frozen inventory.
    if (boundary, predicate) in ((5, 8), (13, 3)):
        return {"binding": "invalid", "access_binding": "invalid"}
    if boundary in (6, 11):
        return {"forum_acknowledgement": "invalid"}
    if boundary in (7, 10, 14) or (boundary == 12 and predicate <= 2):
        return {"binding": "invalid"}
    if boundary in (8, 9, 16, 17, 18, 19) or (boundary == 12 and predicate >= 3):
        return {"pre_execution_evidence": "invalid"}
    if boundary == 13:
        if predicate == 6 and uri_kind == "affected-party-discovery-uri":
            return {"access_binding": "invalid"}
        if predicate == 8:
            return {"discoverability": "incomplete"}
        if predicate == 9:
            # Invariants section 8 / draft section 7.2.1: this is a negative
            # transition, not evidence that the whole B13 boundary passed.
            return {"discoverability": "complete"}
    if boundary == 15:
        return {"forum_acknowledgement": "invalid_scope" if predicate == 1 else "invalid"}
    if boundary == 21:
        if predicate <= 3:
            return {"forum_acknowledgement": "invalid_scope"}
        if predicate == 6:
            return {"access_binding": "invalid"}
    return {}


class ManifestValidator:
    """Load the frozen inputs once; return deterministic diagnostic tuples."""

    def __init__(self, repository_root: Path = REPOSITORY_ROOT):
        root = Path(repository_root)
        try:
            authority_path = root / "authority" / f"{AUTHORITY}.txt"
            inventory_path = root / "authority" / INVENTORY
            schema_path = root / "contract" / "vector-manifest-v0.1.schema.json"
            invariants_path = root / "contract" / "VALIDATOR-INVARIANTS-v0.1.md"
            for path, expected in (
                (authority_path, AUTHORITY_SHA256), (inventory_path, INVENTORY_SHA256),
                (schema_path, SCHEMA_SHA256), (invariants_path, INVARIANTS_SHA256),
            ):
                if _sha256_file(path) != expected:
                    raise ConfigurationError(f"frozen input SHA-256 mismatch: {path.name}")
            self.surfaces = _inventory_surfaces(inventory_path.read_text(encoding="utf-8"))
            schema = _load_json(schema_path)
            Draft202012Validator.check_schema(schema)
            self._schema = Draft202012Validator(schema)
        except (OSError, ValueError, SchemaError, RecursionError) as exc:
            raise ConfigurationError(f"cannot load frozen inputs: {exc}") from exc

    def validate(self, manifest: Any, *, artifact_root: Path) -> tuple[str, ...]:
        """Validate a JSON value, resolving relative artifact paths at artifact_root."""
        schema_errors = sorted(
            self._schema.iter_errors(manifest),
            key=lambda e: (tuple(str(p) for p in e.absolute_path), e.message),
        )
        if schema_errors:
            return tuple(
                f"schema {error.json_path}: {error.message}" for error in schema_errors
            )

        errors = []
        if manifest["authority"] != AUTHORITY:
            errors.append(f"authority: unsupported authority; expected {AUTHORITY}")
        if manifest["authority_sha256"] != AUTHORITY_SHA256:
            errors.append("authority_sha256: does not match the frozen authority bytes")

        try:
            artifact = Path(manifest["artifact"])
            if not artifact.is_absolute():
                artifact = Path(artifact_root) / artifact
            if _sha256_file(artifact) != manifest["sha256"]:
                errors.append("sha256: does not match the exact artifact bytes")
        except (OSError, ValueError) as exc:
            errors.append(f"artifact: cannot read artifact: {exc}")

        result = manifest["expected_result"]
        reachable: dict[str, Any] = dict(INITIAL_STATE)
        if manifest["class"] == "positive":
            for completion in POSITIVE_COMPLETIONS.values():
                reachable.update(completion)
            # Invariants section 10 / draft sections 7.1 and 7.2.1: check
            # reachability only; never classify time using artifact contents.
            if result["filing_window_status"] not in ("not_open", "open", "closed"):
                errors.append("expected_result.filing_window_status: positive path requires not_open, open, or closed")
            reachable["filing_window_status"] = result["filing_window_status"]
            reachable["reasons"] = []
        else:
            surface = manifest["target_surface"]
            if surface not in self.surfaces:
                errors.append("target_surface: not present in the frozen public inventory")
                return tuple(errors)
            prefix = surface.lower().replace(".", "-") + "-"
            if not manifest["vector_id"].startswith(prefix):
                errors.append(f"vector_id: must begin with {prefix!r}")
            boundary_text, predicate_text = surface.split(".")
            boundary, predicate = int(boundary_text[1:]), int(predicate_text[1:])
            reason = BOUNDARY_REASONS[boundary - 1]
            if manifest["expected_reason"] != reason:
                errors.append(f"expected_reason: {surface} requires {reason!r}")
            if result["reasons"] != [manifest["expected_reason"]]:
                errors.append("expected_result.reasons: must contain exactly expected_reason")
            # Invariants section 9 / draft sections 6 and 7.2.1: strictly
            # earlier successes, one negative transition, then stop. In
            # particular, no negative path completes B21's filing status.
            for completed_boundary, completion in POSITIVE_COMPLETIONS.items():
                if completed_boundary < boundary:
                    reachable.update(completion)
            reachable.update(_negative_transition(boundary, predicate, manifest.get("uri_instance_kind")))
            reachable["reasons"] = [reason]

        for field, value in reachable.items():
            if result[field] != value:
                errors.append(f"expected_result.{field}: unreachable value; requires {value!r}")
        return tuple(errors)

    def validate_file(self, path: Path, *, artifact_root: Path | None = None) -> tuple[str, ...]:
        """Read one UTF-8 JSON manifest; default artifact base is its directory."""
        path = Path(path)
        try:
            manifest = _load_json(path)
        except (OSError, ValueError, RecursionError) as exc:
            return (f"manifest: cannot read JSON: {exc}",)
        return self.validate(
            manifest, artifact_root=path.parent if artifact_root is None else artifact_root
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifests", type=Path, nargs="+", help="UTF-8 JSON manifest files")
    parser.add_argument(
        "--artifact-root", type=Path,
        help="base for relative artifact paths (default: each manifest's directory)",
    )
    args = parser.parse_args(argv)
    try:
        validator = ManifestValidator()
    except ConfigurationError as exc:
        print(f"configuration: {exc}", file=sys.stderr)
        return 2
    failed = False
    for path in args.manifests:
        errors = validator.validate_file(path, artifact_root=args.artifact_root)
        if errors:
            failed = True
            for error in errors:
                print(f"INVALID {path}: {error}", file=sys.stderr)
        else:
            print(f"OK {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
