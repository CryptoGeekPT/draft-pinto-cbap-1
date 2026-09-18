# CBAP-1 Normative Surface Inventory v1.0

**Date:** 16 September 2026  
**State:** DERIVED INVENTORY / VERSIONED / NON-NORMATIVE

## 1. Authority and scope

Normative authority:

    draft-pinto-cbap-1-00

TXT SHA-256:

    98994fbbe5c45981711c0da1464b290ac34410dc51918a78182bb8ad5bf57114

This inventory is derived from the normative verification procedure in
Sections 7.1 and 7.2.1 of draft-pinto-cbap-1-00, together with normative
cross-references required to identify the predicate represented by each
verification boundary.

This inventory is derived solely from the published draft. No implementation
source, behaviour, or capability determines the granularity, identity, or
count of surfaces.

This document does not modify draft-pinto-cbap-1-00. If this inventory and
the published draft disagree, the published draft controls.

## 2. Counting rules

A surface identifier represents one normative predicate position in the
ordered verification procedure.

The following rules are used consistently:

1. Conditions explicitly enumerated by the normative text as distinct
   comparisons or requirements receive distinct surface identifiers.
2. A single expression, a single stated obligation, or one stated obligation
   applied to an ordered set of instances receives one surface identifier.
   Distinct failure cases or instances are recorded under that identifier and
   retain their normative evaluation order where the draft defines one.
3. Structured-result transitions annotate or group existing predicate
   identifiers. A transition does not itself create or remove a predicate
   identifier.
4. B5 through B9 use the eight ordered pipeline positions defined by Section
   7.1. Internal checks inside one explicitly defined pipeline position remain
   cases of that position rather than additional surfaces.
5. Positive-only derivations performed after all predicates at a boundary
   pass are recorded as result derivations, not as additional negative
   predicate surfaces.

The inventory therefore distinguishes predicate identity from test-vector
multiplicity. A single surface can require multiple vectors to exercise its
named cases or ordered instances.

## 3. Normative surface inventory

### B1 - verification_time_invalid [1]

**B1.P01 - external verification-time validity**

Require the external verification time to be an integer in the unsigned
64-bit range.

Named cases:

- parse failure;
- non-integer representation;
- negative value;
- value above 2^64-1.

Negative structured-result transition: none.

### B2 - outer_encoding_invalid [3]

**B2.P01 - complete received bundle size**

Require the complete received bundle to be no larger than MAX_BUNDLE_BYTES.

**B2.P02 - outer-item decoding and Core CBOR conformance**

Decode exactly one outer CBOR item under the Section 5.1 rules and require
complete input consumption.

Named cases include:

- truncated input;
- trailing input;
- indefinite-length encoding;
- non-shortest or non-preferred integer/length encoding;
- duplicate map key;
- non-deterministic map ordering;
- forbidden outer tag;
- forbidden float;
- forbidden simple value;
- invalid UTF-8;
- declared-length/cursor arithmetic failure;
- MAX_BSTR_BYTES;
- MAX_TSTR_UTF8_BYTES;
- MAX_COLLECTION_MEMBERS;
- MAX_NESTING_DEPTH.

The resource ceilings are instances of this decoding obligation and do not
create additional surface identifiers.

**B2.P03 - deterministic re-encoding equality**

Re-encode the decoded outer item under Section 5.1 and require byte-for-byte
equality with the received outer item.

This is a distinct normative operation after successful decoding and remains
a separate surface even where a conforming decoder makes isolated failure
operationally unreachable.

Negative structured-result transition for B2.P01 through B2.P03: none.

### B3 - bundle_schema_invalid [5]

**B3.P01 - closed outer bundle schema**

Require the outer item to conform to the closed `cbap1-bundle` schema.

Named cases:

- unsupported profile version;
- missing required member;
- unknown member;
- wrong required-member type.

**B3.P02 - policy-set non-empty cardinality**

Require bundle member 8 to be a non-empty array.

**B3.P03 - exact policy-pair shape**

Require every member-8 item to be exactly a two-element
`[digest, policy-bytes]` pair.

**B3.P04 - policy digest width**

Require each policy digest to be a 32-byte byte string.

**B3.P05 - policy bytes type**

Require each policy value to be a byte string.

Negative structured-result transition for B3.P01 through B3.P05: none.

Positive completion annotation:

    notice_evidence = not_claimed

### B4 - policy_set_invalid [4]

**B4.P01 - policy-set upper bound**

Require policy-set cardinality to be no greater than MAX_POLICY_PAIRS.

**B4.P02 - profile-defined ordering**

Require the policy set to be in the profile-defined order.

**B4.P03 - digest uniqueness**

Require no duplicate policy digest.

**B4.P04 - digest integrity**

Require each carried digest to equal SHA-256 of its associated policy bytes.

Negative structured-result transition: none.

The B3 member-8 schema predicates are not re-counted at B4.

## 4. Signed-object pipeline surfaces

Each of B5 through B9 contains the same eight ordered normative predicate
positions.

**P01 - complete tagged COSE_Sign1 encoding**

Validate the complete received signed object under the applicable resource
ceilings and Core Deterministic CBOR rules.

**P02 - COSE_Sign1 shape and outer header constraints**

Validate the tagged COSE_Sign1 shape, the unprotected-header constraints,
and the received signature length.

**P03 - protected-header bytes**

Decode and validate the protected-header byte string under the applicable
resource ceilings, Core CBOR rules, and protected-header constraints.

**P04 - payload bytes**

Decode the payload bytes under the applicable resource ceilings and Core
CBOR rules.

**P05 - closed payload schema**

Require the payload to satisfy its closed schema, supported profile version,
and required object type.

**P06 - protected kid / payload key-id equality**

Require the protected `kid` bytes to equal the UTF-8 bytes of the payload
signer key-id.

**P07 - trust resolution and resolved-key usage restriction**

Require exact protected-kid matching, required-role matching, exactly-one
authorized trust resolution, and, when present on the resolved COSE_Key,
`alg == -19`.

**P08 - signature verification**

Verify the Ed25519 signature over the received protected-header bytes and
payload bytes with empty external AAD.

The resulting surface identifiers are:

    B5.P01 .. B5.P08   CPO
    B6.P01 .. B6.P08   Exact Forum Acceptance
    B7.P01 .. B7.P08   Authorization Artifact
    B8.P01 .. B8.P08   Executor Verification
    B9.P01 .. B9.P08   Execution Record

This contributes 40 surfaces.

Structured-result transition annotations:

B5:

- B5.P01 through B5.P07 failure: no transition;
- B5.P08 failure:
  - `binding = invalid`;
  - `access_binding = invalid`;
- whole-boundary success:
  - `declared_effect = none`;
  - `effect_acceptance = not_required`;
  - `effect_trigger = not_applicable`;
  - `effect_ordering = not_applicable`;
  - `effect_application = not_applicable`.

B6:

- any B6.P01 through B6.P08 failure:
  - `forum_acknowledgement = invalid`.

B7:

- any B7.P01 through B7.P08 failure:
  - `binding = invalid`.

B8:

- any B8.P01 through B8.P08 failure:
  - `pre_execution_evidence = invalid`.

B9:

- any B9.P01 through B9.P08 failure:
  - `pre_execution_evidence = invalid`.

### B10 - cpo_binding_mismatch [1]

**B10.P01 - signed CPO digest binding**

Require SHA-256 of the complete signed CPO to equal the CPO digest carried by
the Authorization Artifact.

Negative transition:

    binding = invalid

### B11 - acceptance_binding_mismatch [1]

**B11.P01 - signed Exact Forum Acceptance digest binding**

Require SHA-256 of the complete signed Exact Forum Acceptance to equal the
acceptance reference carried by the CPO.

Negative transition:

    forum_acknowledgement = invalid

### B12 - action_digest_mismatch [4]

Evaluate the following comparisons in normative order.

**B12.P01 - action digest / CPO terms**

Require the recomputed action digest to equal the CPO terms action digest.

**B12.P02 - action digest / Authorization Artifact**

Require the recomputed action digest to equal the Authorization Artifact
action digest.

**B12.P03 - action digest / Executor Verification**

Require the recomputed action digest to equal the Executor Verification
action digest.

**B12.P04 - action digest / Execution Record**

Require the recomputed action digest to equal the Execution Record action
digest.

Transition grouping:

- B12.P01 or B12.P02 failure:
  - `binding = invalid`;
- B12.P03 or B12.P04 failure:
  - `pre_execution_evidence = invalid`.

The shared transitions do not merge the four predicate identifiers.

### B13 - profile_binding_mismatch [9]

**B13.P01 - ABP identifier**

Require the CPO terms ABP identifier to equal the expected CBAP-1 ABP
identifier.

**B13.P02 - Authorization Trust Profile identifier**

Require the CPO terms Authorization Trust Profile identifier to equal the
expected Authorization Trust Profile identifier.

**B13.P03 - CPO signer / authorization-issuer key-id**

Require the CPO signer key-id to equal the CPO terms
authorization-issuer key-id.

Negative transition:

- `binding = invalid`;
- `access_binding = invalid`.

**B13.P04 - authorization validity interval order**

Require `not-before <= not-after`.

**B13.P05 - filing-window duration range**

Require the filing-window duration to be in `1..2^64-1`.

**B13.P06 - required HTTPS URI conformance**

Require all required HTTPS URIs to conform.

Ordered instances:

1. forum-id;
2. submission-endpoint;
3. Standing Policy URI;
4. procedure URI;
5. selection-policy URI;
6. each affected-party discovery-uri in increasing index order;
7. Exact Forum Acceptance submission-receipt-profile URI;
8. Exact Forum Acceptance withdrawal-policy URI.

Instance-specific transition:

- failure of an affected-party discovery-uri instance:
  - `access_binding = invalid`;
- failure of any other B13.P06 instance:
  - no transition.

The ordered URI instances do not create additional surface identifiers.

**B13.P07 - forum key-id UTF-8 width**

Require the CPO terms forum key-id to encode as 1 through 64 UTF-8 bytes.

**B13.P08 - referenced policy presence**

Require every referenced policy digest to be present in bundle member 8.

Negative transition:

    discoverability = incomplete

**B13.P09 - absence of unreferenced policies**

Require bundle member 8 to contain no digest outside the referenced policy
digests.

Negative transition:

    discoverability = complete

Whole-boundary positive transition:

    discoverability = complete

### B14 - authorization_projection_mismatch [3]

**B14.P01 - authorization identifier projection**

Require the Authorization Artifact authorization identifier to equal the CPO
terms authorization identifier.

**B14.P02 - issuer key-id projection**

Require the Authorization Artifact issuer key-id to equal the CPO terms
authorization-issuer key-id.

**B14.P03 - validity projection**

Require the Authorization Artifact validity projection to equal the
corresponding CPO terms validity projection.

Named cases:

- `not-before`;
- `not-after`.

Any negative outcome:

    binding = invalid

Whole-boundary positive transition:

- `selection_provenance = unilateral`;
- `binding = valid`.

### B15 - forum_terms_mismatch [3]

**B15.P01 - accepted forum_terms digest**

Require the accepted `forum_terms` digest to equal the exact Section 5.4
projection digest.

Negative transition:

    forum_acknowledgement = invalid_scope

**B15.P02 - Exact Forum Acceptance signer key-id**

Require the Exact Forum Acceptance signer key-id to equal the CPO terms forum
key-id.

Negative transition:

    forum_acknowledgement = invalid

**B15.P03 - forum-id authorization**

Require the trust entry resolved at the signed-object trust-resolution step to
explicitly authorize the exact CPO terms forum-id.

Negative transition:

    forum_acknowledgement = invalid

### B16 - authorization_digest_mismatch [2]

**B16.P01 - Authorization Artifact digest / Executor Verification**

Require SHA-256 of the complete signed Authorization Artifact to equal the
digest carried by the Executor Verification.

**B16.P02 - Authorization Artifact digest / Execution Record**

Require the same Authorization Artifact digest to equal the digest carried by
the Execution Record.

Either negative outcome:

    pre_execution_evidence = invalid

### B17 - executor_verification_mismatch [2]

**B17.P01 - Executor Verification authorization identifier**

Require the Executor Verification authorization identifier to equal the bound
authorization identifier.

**B17.P02 - Executor Verification CPO digest**

Require the Executor Verification CPO digest to equal the bound CPO digest.

Either negative outcome:

    pre_execution_evidence = invalid

### B18 - execution_record_mismatch [2]

**B18.P01 - Execution Record Executor Verification digest**

Require the Execution Record to carry the digest of the complete signed
Executor Verification.

**B18.P02 - Execution Record authorization identifier**

Require the Execution Record authorization identifier to equal the bound
authorization identifier.

Either negative outcome:

    pre_execution_evidence = invalid

### B19 - executor_ordering_invalid [1]

**B19.P01 - executor temporal ordering chain**

Require the single normative ordering expression:

    not-before <= verified-at <= executed-at <= not-after

Named failure cases:

- `not-before > verified-at`;
- `verified-at > executed-at`;
- `executed-at > not-after`.

The three comparisons are cases of one chained normative expression and do
not create separate surface identifiers.

Any negative outcome:

    pre_execution_evidence = invalid

Whole-boundary positive transition:

    pre_execution_evidence = executor_attested

### B20 - filing_deadline_overflow [1]

**B20.P01 - checked filing-deadline arithmetic**

Compute:

    filing_deadline = executed-at + duration-seconds

and require the result to be representable using checked unsigned arithmetic.

Negative structured-result transition: none.

### B21 - filing_horizon_invalid [6]

**B21.P01 - acceptance signed-at horizon**

Require Exact Forum Acceptance `signed-at <= not-before`.

Negative transition:

    forum_acknowledgement = invalid_scope

**B21.P02 - acceptance valid-from horizon**

Require Exact Forum Acceptance `valid-from <= not-before`.

Negative transition:

    forum_acknowledgement = invalid_scope

**B21.P03 - acceptance valid-until horizon**

Require Exact Forum Acceptance `valid-until >= filing_deadline`.

Negative transition:

    forum_acknowledgement = invalid_scope

**B21.P04 - CPO issued-at horizon**

Require CPO `issued-at <= verified-at`.

Negative transition: none.

**B21.P05 - CPO expires-at horizon**

Require CPO `expires-at >= filing_deadline`.

Negative transition: none.

**B21.P06 - affected-party access horizon**

Require at least one declared affected-party access method with
`available-until >= filing_deadline`.

Negative transition:

    access_binding = invalid

Whole-boundary positive transitions:

- `forum_acknowledgement = valid_exact`;
- `access_binding = valid`;
- derive `filing_window_status`:
  - `not_open` if `verification_time < executed-at`;
  - `open` if `executed-at <= verification_time < filing_deadline`;
  - `closed` if `verification_time >= filing_deadline`.

The filing-window-status derivation is a positive result derivation, not a
seventh B21 negative predicate surface.

## 5. Surface count

    B1       1
    B2       3
    B3       5
    B4       4
    B5       8
    B6       8
    B7       8
    B8       8
    B9       8
    B10      1
    B11      1
    B12      4
    B13      9
    B14      3
    B15      3
    B16      2
    B17      2
    B18      2
    B19      1
    B20      1
    B21      6
           ---
    TOTAL   88

## 6. Frozen interpretation notes for this inventory version

N1. Parameterized instances do not multiply the surface count.

Examples include policy-pair instances, affected-party access entries, and
the ordered URI instances of B13.P06.

N2. A structured-result transition class never creates or removes a predicate
identifier.

It annotates one or more existing identifiers or instances.

N3. Internal cases inside one explicitly defined validation position remain
test-vector cases, not additional surface identifiers.

This rule is essential to keep the inventory consistent with the eight-stage
signed-object pipeline defined by the normative procedure.

## 7. Intended downstream use

This inventory provides the identifier and counting basis for CBAP-1
conformance vectors and vector-coverage documentation.

Whether a vector exists for a surface, and the type of vector used to exercise
it, are separate properties and are not assigned by this inventory.

Any later correction to surface identity, granularity, or count requires a
new version of this inventory. It MUST NOT be silently changed in downstream
conformance or vector artifacts.
