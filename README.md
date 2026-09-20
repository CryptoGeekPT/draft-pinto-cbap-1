# CBAP-1 vector-manifest validator

Validates manifests against the v0.2 JSON Schema and
`contract/VALIDATOR-INVARIANTS-v0.1.md`. Requires Python 3.10+.

The virtual environment must be outside the repository. From the repository
root, choose an external environment path and install the dependency
(PowerShell; `python` must identify an installed Python):

```powershell
$validatorVenv = Read-Host 'Virtual environment path outside the repository'
python -B -m venv $validatorVenv
$validatorPython = Join-Path $validatorVenv 'Scripts/python.exe'
& $validatorPython -B -m pip --disable-pip-version-check --no-cache-dir install --no-compile -r requirements.txt
```

Run validation and tests:

```powershell
& $validatorPython -B src/cbap1_validator.py path/to/manifest.json
& $validatorPython -B src/cbap1_validator.py --artifact-root path/to/corpus path/to/manifest.json
& $validatorPython -B -m unittest discover -s tests -v
```

The CLI accepts one or more UTF-8 JSON manifest files. Relative artifact paths
resolve against each manifest's directory, or against `--artifact-root` when
provided. `--artifact-root` affects relative artifact paths only. Relative
`verification_context` paths resolve against the manifest directory and are
not affected by `--artifact-root`; absolute paths are used as given.
Direct `validate()` callers must supply both `artifact_root` and
`verification_context_root`. Exit codes are **0** for all valid,
**1** for invalid/unreadable manifests, artifacts, or contexts, and **2** for usage or
frozen-input configuration errors. Diagnostics have deterministic ordering.
Duplicate JSON members and non-JSON numeric constants are rejected.

The validator checks the closed schema, class rules, authority identity and
hash, inventory membership, target prefix, B13.P06 discriminator, exact artifact
SHA-256, verification-context existence, exact-byte SHA-256 and schema validity,
reason coherence, and structured-result reachability. The authority
draft, public inventory, manifest schemas, context schema, and invariant document are checked
against frozen SHA-256 hashes on startup. Keep the `src`, `authority`, and
`contract` directories together.

Artifacts are only read for hashing. The validator does not determine whether
an artifact actually causes the declared failure, interpret the vector ID
suffix, or recompute the per-vector expected-result oracle. For positive
manifests it accepts any of the three reachable filing-window classifications.

Tests cover all 88 inventory surfaces, both B13.P06 cases, positive paths, and
invalid manifests, including alternative unreachable semantic-field values.
Their temporary opaque artifacts are not conformance vectors. Tests use the
system temporary directory; `-B` prevents repository bytecode caches.

## Licensing

The Internet-Draft in `authority/draft-pinto-cbap-1-00.txt` is subject to the
copyright and licensing terms stated in that document.

All other original material in this repository is licensed under the BSD
3-Clause License; see `LICENSE`.
