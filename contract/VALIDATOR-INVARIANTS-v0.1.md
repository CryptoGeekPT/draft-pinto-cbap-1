# CBAP-1 Vector Validator Invariants v0.1

## 1. Purpose and authority

This document defines result-coherence invariants for validation of
CBAP-1 vector manifests.

It is derived from the closed structured-result contract in Section 6
and the exhaustive structured-result transition rules in Section 7.2.1
of draft-pinto-cbap-1-00.

It does not define an independent expected-result oracle.

The manifest is the per-vector expected-result oracle. The validator
checks whether the declared result is reachable under the normative
initial state, mandatory prior positive completions, first-failure rule,
and closed transition ownership defined by the draft.

The validator does not establish that the vector artifact actually
causes the declared failure. That is a separate conformance check.

## 2. Initial structured result

Before B1, the structured result is:

    binding                  = indeterminate
    pre_execution_evidence   = indeterminate
    discoverability          = indeterminate
    forum_acknowledgement    = indeterminate
    forum_operational_status = not_checked
    selection_provenance     = indeterminate
    access_binding           = indeterminate
    notice_evidence          = indeterminate
    retrievability           = not_checked
    filing_window_status     = indeterminate
    policy_freshness         = indeterminate
    declared_effect          = indeterminate
    effect_acceptance        = indeterminate
    effect_trigger           = indeterminate
    effect_ordering          = indeterminate
    effect_application       = indeterminate
    reasons                  = []

Each semantic field may leave its initial value at most once and then
retains the resulting value.

On a positive path, reasons remains [].

On a negative path, reasons changes exactly once to the one-element
array containing the reason code of the first failed boundary.

## 3. Fields fixed on every path

The following values are invariant on every CBAP-1 path:

    forum_operational_status = not_checked
    retrievability           = not_checked
    policy_freshness         = indeterminate

Any manifest declaring another value for one of these fields is
incoherent.

## 4. Boundary reason mapping

The reason associated with each failure-precedence boundary is:

    B1   verification_time_invalid
    B2   outer_encoding_invalid
    B3   bundle_schema_invalid
    B4   policy_set_invalid
    B5   cpo_invalid
    B6   forum_acceptance_invalid
    B7   authorization_invalid
    B8   executor_verification_invalid
    B9   execution_record_invalid
    B10  cpo_binding_mismatch
    B11  acceptance_binding_mismatch
    B12  action_digest_mismatch
    B13  profile_binding_mismatch
    B14  authorization_projection_mismatch
    B15  forum_terms_mismatch
    B16  authorization_digest_mismatch
    B17  executor_verification_mismatch
    B18  execution_record_mismatch
    B19  executor_ordering_invalid
    B20  filing_deadline_overflow
    B21  filing_horizon_invalid

For a verifier-negative vector:

    expected_reason

MUST equal the reason associated with the boundary containing
target_surface, and:

    expected_result.reasons

MUST equal the one-element array containing exactly expected_reason.

For a positive vector:

    expected_reason = null
    expected_result.reasons = []

## 5. Positive completion ownership

A positive completion is applied only after the corresponding boundary
has passed, unless the draft explicitly states an earlier completion.

For draft-pinto-cbap-1-00, the positive semantic-field completions are:

| Boundary | Positive completion |
| --- | --- |
| B3 | `notice_evidence = not_claimed` |
| B5 | `declared_effect = none`; `effect_acceptance = not_required`; `effect_trigger = not_applicable`; `effect_ordering = not_applicable`; `effect_application = not_applicable` |
| B13 | `discoverability = complete` |
| B14 | `selection_provenance = unilateral`; `binding = valid` |
| B19 | `pre_execution_evidence = executor_attested` |
| B21 | `forum_acknowledgement = valid_exact`; `access_binding = valid`; `filing_window_status` is derived as specified by Section 7.1 |

All other B1-B21 boundaries have no positive semantic-field completion.

For a verifier-negative vector whose target is in boundary Bn, every
positive completion belonging to a boundary strictly earlier than Bn
MUST already be reflected in expected_result.

The positive completion of Bn itself MUST NOT be applied when Bn is the
failed boundary, except where the closed negative-transition table
explicitly assigns the same value.

## 6. Negative transition ownership

At the first failed predicate, only the following semantic-field
transition is permitted. `--` means no semantic-field transition.

| Target surface | Reason | Negative transition |
| --- | --- | --- |
| B1.P01 | `verification_time_invalid` | -- |
| B2.P01-B2.P03 | `outer_encoding_invalid` | -- |
| B3.P01-B3.P05 | `bundle_schema_invalid` | -- |
| B4.P01-B4.P04 | `policy_set_invalid` | -- |
| B5.P01-B5.P07 | `cpo_invalid` | -- |
| B5.P08 | `cpo_invalid` | `binding = invalid`; `access_binding = invalid` |
| B6.P01-B6.P08 | `forum_acceptance_invalid` | `forum_acknowledgement = invalid` |
| B7.P01-B7.P08 | `authorization_invalid` | `binding = invalid` |
| B8.P01-B8.P08 | `executor_verification_invalid` | `pre_execution_evidence = invalid` |
| B9.P01-B9.P08 | `execution_record_invalid` | `pre_execution_evidence = invalid` |
| B10.P01 | `cpo_binding_mismatch` | `binding = invalid` |
| B11.P01 | `acceptance_binding_mismatch` | `forum_acknowledgement = invalid` |
| B12.P01-B12.P02 | `action_digest_mismatch` | `binding = invalid` |
| B12.P03-B12.P04 | `action_digest_mismatch` | `pre_execution_evidence = invalid` |
| B13.P01-B13.P02 | `profile_binding_mismatch` | -- |
| B13.P03 | `profile_binding_mismatch` | `binding = invalid`; `access_binding = invalid` |
| B13.P04-B13.P05 | `profile_binding_mismatch` | -- |
| B13.P06 + `affected-party-discovery-uri` | `profile_binding_mismatch` | `access_binding = invalid` |
| B13.P06 + `other-required-uri` | `profile_binding_mismatch` | -- |
| B13.P07 | `profile_binding_mismatch` | -- |
| B13.P08 | `profile_binding_mismatch` | `discoverability = incomplete` |
| B13.P09 | `profile_binding_mismatch` | `discoverability = complete` |
| B14.P01-B14.P03 | `authorization_projection_mismatch` | `binding = invalid` |
| B15.P01 | `forum_terms_mismatch` | `forum_acknowledgement = invalid_scope` |
| B15.P02-B15.P03 | `forum_terms_mismatch` | `forum_acknowledgement = invalid` |
| B16.P01-B16.P02 | `authorization_digest_mismatch` | `pre_execution_evidence = invalid` |
| B17.P01-B17.P02 | `executor_verification_mismatch` | `pre_execution_evidence = invalid` |
| B18.P01-B18.P02 | `execution_record_mismatch` | `pre_execution_evidence = invalid` |
| B19.P01 | `executor_ordering_invalid` | `pre_execution_evidence = invalid` |
| B20.P01 | `filing_deadline_overflow` | -- |
| B21.P01-B21.P03 | `filing_horizon_invalid` | `forum_acknowledgement = invalid_scope` |
| B21.P04-B21.P05 | `filing_horizon_invalid` | -- |
| B21.P06 | `filing_horizon_invalid` | `access_binding = invalid` |

These transitions are exhaustive for CBAP-1 failure classification.

## 7. B13.P06 instance discriminator

`uri_instance_kind` exists only to distinguish the two transition
classes inside B13.P06.

For:

    target_surface = B13.P06

the field is REQUIRED and has exactly one of:

    affected-party-discovery-uri
    other-required-uri

`affected-party-discovery-uri` denotes failure of an affected-party
`discovery-uri` instance and permits:

    access_binding = invalid

`other-required-uri` denotes failure of any other required HTTPS URI
instance at B13.P06 and permits no semantic-field transition.

`uri_instance_kind` is forbidden for every other target surface and for
positive vectors.

## 8. B13.P09 exception

Failure at B13.P09 explicitly sets:

    discoverability = complete

This is a negative transition even though `complete` is also the positive
completion value of B13.

The validator MUST NOT infer that:

    discoverability = complete

proves that B13 passed.

B13.P09 is the explicit exception that demonstrates why field value and
boundary-success history are not interchangeable.

## 9. Reachability check for verifier-negative manifests

For a verifier-negative manifest with target surface in boundary Bn, the
validator checks result-state reachability as follows:

1. Start from the exact initial state in Section 2.

2. Apply the positive completions in Section 5 for every boundary
   strictly earlier than Bn.

3. Do not apply the positive completion of Bn.

4. Apply exactly the negative transition assigned to target_surface in
   Section 6, using uri_instance_kind when target_surface is B13.P06.

5. Set reasons to the one-element array containing the reason associated
   with Bn.

6. Every semantic field not changed by steps 2 through 4 retains its
   previous value.

7. For every verifier-negative manifest:

       filing_window_status = indeterminate

   The only normative assignment of a non-indeterminate
   filing_window_status occurs on successful completion of B21.
   A verifier-negative vector necessarily stops before that positive
   completion occurs, including when the first failure is within B21.

The declared expected_result MUST equal a state reachable under these
rules.

This check validates consistency of the declared target surface, reason,
and structured result. It does not inspect the vector artifact to decide
whether the artifact actually reaches or fails at the declared surface.

## 10. Reachability check for positive manifests

For a positive manifest:

1. expected_reason MUST be null.

2. expected_result.reasons MUST be [].

3. All positive completions in Section 5 MUST be present.

4. The fifteen semantic fields whose positive-path final value is fixed
   independently of filing-window classification are:

       binding                  = valid
       pre_execution_evidence   = executor_attested
       discoverability          = complete
       forum_acknowledgement    = valid_exact
       forum_operational_status = not_checked
       selection_provenance     = unilateral
       access_binding           = valid
       notice_evidence          = not_claimed
       retrievability           = not_checked
       policy_freshness         = indeterminate
       declared_effect          = none
       effect_acceptance        = not_required
       effect_trigger           = not_applicable
       effect_ordering          = not_applicable
       effect_application       = not_applicable

5. The remaining semantic field, filing_window_status, MUST be one of:

       not_open
       open
       closed

The validator does not independently derive which of those three filing
window values is correct from the artifact. The manifest remains the
expected-result oracle for that value.

## 11. Manifest-level cross-field checks

The following checks are required in addition to JSON Schema validation:

1. `target_surface`, when present, MUST exist in the public normative
   surface inventory.

2. For a verifier-negative vector, define:

       normalized_target =
           lowercase(target_surface with "." replaced by "-")

   `vector_id` MUST begin with:

       normalized_target + "-"

   Example:

       target_surface = B13.P06
       required vector_id prefix = b13-p06-

   Therefore `b13-p061-...` does not satisfy the rule.

3. For a verifier-negative vector:

       expected_result.reasons[0] == expected_reason

4. `authority_sha256` MUST equal the SHA-256 of the exact authority
   identified by `authority`.

5. `artifact` MUST resolve to the intended corpus artifact, and `sha256`
   MUST equal SHA-256 of its exact bytes.

## 12. Non-goals

The validator does not:

- derive target_surface from artifact bytes;
- derive expected_reason from artifact bytes;
- independently compute the complete per-vector expected-result oracle;
- infer semantic meaning from the suffix of vector_id;
- accept implementation-specific result values or reason strings;
- accept free-text manifest metadata.

The suffix of vector_id is an identifier only. It is not interpreted as
a case taxonomy.
