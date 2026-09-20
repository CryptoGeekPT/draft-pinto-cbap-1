# CBAP-1 Vector Corpus Contract v0.1

## 1. Scope

This document defines the public corpus contract that relates CBAP-1 test
vector manifests, verifier-local input contexts, test-only generation keys,
protocol artifacts, and expected verification results.

It accompanies:

- `vector-manifest-v0.2.schema.json`
- `verification-context-v0.1.schema.json`
- `test-keys-v1.schema.json`

The JSON Schemas define corpus syntax. This document defines the relationships
between those files and the interpretation of deliberately permissive fields.

## 2. Vector identity

A vector is identified by its `vector_id` and by the concrete artifact,
verification context, and expected outcome referenced by its manifest.

Two manifests MAY reference the same artifact and different verification
contexts. Each manifest defines a distinct test vector, and its `vector_id`
identifies that vector. Reuse of a `vector_id` across manifests is a corpus
error.

The expected result is defined for the artifact and verification-context pair
identified by that manifest. The artifact alone does not determine the expected
result.

For example, the same otherwise-valid artifact can be paired with different
verification times and therefore have different expected filing-window states.

## 3. Exact-byte hashing

Artifact and verification-context digests are SHA-256 digests of the exact
referenced file bytes.

The corpus does not define JSON canonicalization. A digest identifies a
particular serialized file, not a semantic equivalence class.

Consequently, two verification-context files that represent the same semantic
inputs can have different digests if their serialized bytes differ, including
because of member ordering, whitespace, line endings, or trust-set entry order.

Trust-set entry order has no corpus-defined verification semantics.

## 4. Verification context

`verification-context-v0.1.schema.json` represents the verifier-local inputs
supplied separately from the CBAP-1 artifact:

1. the expected Authorization Trust Profile identifier supplied by trusted
   local policy;
2. the local role-authorized Ed25519 trust set; and
3. the verification-time input.

The CBAP-1 authorization-binding-profile identifier is not represented in the
verification context because it is a profile-derived verifier value rather
than a verifier-local input.

### 4.1 Authorization Trust Profile identifier

`authorization_trust_profile_id` is a lowercase hexadecimal representation of
the local expected identifier.

The corpus format deliberately does not constrain its byte length. Equality
with the identifier carried in the CPO terms is evaluated by the verifier.

### 4.2 Trust set

`trust_set` is an array with zero or more entries.

The array intentionally has:

- no minimum cardinality;
- no uniqueness constraint; and
- no corpus-defined ordering.

These choices allow the corpus to represent trust-resolution inputs including
zero matching entries and multiple entries matching the same role and `kid`.
Trust-resolution cardinality is evaluated by the verifier.

Each trust entry contains:

- `role`;
- `kid`;
- `cose_key`; and
- optionally, for `forum-role` only, `forum_id_authorization`.

The role vocabulary is closed to:

- `issuer-role`
- `forum-role`
- `executor-role`

### 4.3 Trust-entry `kid`

`kid` is the lowercase hexadecimal representation of the exact bytes
associated with the local trust entry.

The corpus format deliberately does not constrain its byte length. Matching
and other CBAP-1 validity conditions are evaluated by the verifier.

### 4.4 COSE_Key representation

`cose_key` is a closed corpus object whose members are:

- optional integer `kty`;
- optional integer `crv`;
- optional hexadecimal byte string `x`; and
- optional integer `alg`.

The members are intentionally optional, and the corpus format does not impose
the CBAP-1-valid values or the CBAP-1-valid length of `x`.

This permits structurally invalid local trust inputs to be represented.
Their absence, value, and length are evaluated by the verifier where the
CBAP-1 verification procedure requires those properties.

The `x` field represents the exact byte string placed in the COSE_Key `x`
parameter. The corpus contract does not describe it as a mathematical curve
coordinate.

### 4.5 Forum identifier authorization

`forum_id_authorization` is permitted only on a `forum-role` trust entry.

When present, it represents one explicitly authorized forum identifier.
Absence represents authorization for no forum identifier.

The corpus format does not impose URI-shape constraints on this local value.
URI conformance of the CPO terms forum identifier and equality with the local
authorization are evaluated by the verifier.

Comparison is exact. No Unicode normalization, URI normalization, case
normalization, percent-encoding normalization, or other transformation is
applied before comparison.

### 4.6 Verification time

`verification_time` is a canonical signed decimal string representing the
integer presented at the verifier boundary.

Its lexical form is:

```text
^(0|-?[1-9][0-9]*)$
```

Examples accepted by the corpus representation include:

```text
"0"
"1"
"-1"
"18446744073709551615"
"18446744073709551616"
```

Examples rejected by the corpus representation include:

```text
"+1"
"01"
"-01"
"-0"
" 1"
```

The corpus representation preserves arbitrary-size integers exactly and does
not depend on JSON numeric precision.

The corpus format deliberately does not constrain the value to the CBAP-1
unsigned range. Range validation is performed by the verifier. Therefore an
out-of-range integer can be a valid verification-context value and an invalid
CBAP-1 verifier input.

This version of the corpus defines only the integer form of verification time.
It does not define a corpus encoding for a non-integer external
verification-time representation. The `-00` specification likewise requires
rejection of a non-integer external representation without defining the
external representation format in which that condition is presented to the
verifier.

## 5. Test-only generation keys

`test-keys-v1.schema.json` represents public generation material used to
reproduce corpus artifacts. It is not verifier input.

A conforming test-key file has `test_only` set to `true`.

Private seeds published under this contract are public test material and MUST
NOT be used for any purpose outside this test corpus.

### 5.1 Fixed seeds

Each `seed_hex` value is the lowercase hexadecimal encoding of exactly 32
bytes: the Ed25519 private seed used as the input to RFC 8032 Section 5.1.5
key generation.

It is not a 64-byte expanded private key and does not include the public key.

Published seed values are fixed generation inputs. No derivation procedure is
defined for obtaining them from names, roles, key identifiers, or other
metadata.

### 5.2 Derived public key

`public_key_x_hex` is the lowercase hexadecimal encoding of the 32-byte
Ed25519 public key derived from `seed_hex`.

Those exact 32 bytes are the bytes used as the COSE_Key `x` parameter.

For every published test key:

```text
public_key_x_hex MUST equal the Ed25519 public key derived from seed_hex
under RFC 8032 Section 5.1.5.
```

### 5.3 Payload key identifier and protected kid

`key_id` is the text key identifier used in the signed payload.

`kid_hex` is redundant, independently checkable generation metadata. For
every published test key:

```text
kid_hex MUST equal lowercase_hex(UTF-8(key_id))
```

No Unicode normalization or other transformation is applied.

Reference positive material uses ASCII `key_id` values. That is a property of
the reference material, not a general restriction imposed by the test-key
schema.

### 5.4 Role and signed-object use

The role vocabulary is:

- `issuer-role`
- `forum-role`
- `executor-role`

`used_by` identifies which signed CBAP-1 objects use the key during artifact
generation. Its vocabulary is exactly:

- `CPO`
- `Exact Forum Acceptance`
- `Authorization Artifact`
- `Executor Verification`
- `Execution Record`

`used_by` is generation metadata only. It is not part of verifier input and
does not participate in trust resolution.

The schema constrains `used_by` values according to the key role, but it does
not require a concrete key file to contain any particular number of keys or to
cover every signed object. Coherence of a concrete published key set is a
property of that key set.

## 6. Verification material and generation material

The corpus separates verification inputs from generation inputs.

Verification requires:

```text
artifact
+ verification context
```

Generation can additionally use:

```text
test-only generation keys
```

The verification context does not map trust entries to signed objects. The
verifier resolves trust using the role required for each signed object and the
protected `kid` carried by that object.

The test-key material can carry `used_by` because a generator needs to know
which published key to use when reproducing each signed object.

## 7. Manifest v0.2

`vector-manifest-v0.2.schema.json` extends v0.1 by adding exactly two required
fields:

- `verification_context`
- `verification_context_sha256`

`verification_context` identifies the referenced context file.

`verification_context_sha256` is the lowercase SHA-256 digest of the exact
context-file bytes.

The existing `sha256` field continues to identify the exact artifact bytes.

The test-only key file is not referenced as verifier input by the manifest.

## 8. Corpus validator boundary

A corpus validator can check, at minimum:

- manifest conformance to `vector-manifest-v0.2.schema.json`;
- existence of the referenced artifact;
- SHA-256 equality for the referenced artifact;
- existence of the referenced verification context;
- SHA-256 equality for the referenced verification context;
- JSON validity of the verification context;
- conformance of the verification context to
  `verification-context-v0.1.schema.json`; and
- the existing manifest reason/result structural invariants.

The corpus validator does not derive the protocol verification outcome from
the artifact and context.

In particular, for a positive vector it does not derive
`filing_window_status` from `verification_time` and the filing deadline.
Doing so would require decoding the artifact, applying protocol verification
logic, and calculating the filing-window condition. That would make the corpus
validator perform verifier work rather than validate corpus structure.

Accordingly, for positive vectors, `filing_window_status` values `not_open`,
`open`, and `closed` remain structurally acceptable to the corpus validator.
The manifest's `expected_result` states the expected protocol outcome for the
referenced artifact and verification-context pair.

## 9. Closed schemas and deliberate permissiveness

The corpus schemas are closed against unknown fields.

Where a schema permits values that are invalid under CBAP-1, that
permissiveness is deliberate when the verifier is responsible for evaluating
the corresponding condition.

The schema validates the corpus representation. The verifier validates the
CBAP-1 protocol conditions.

This separation allows negative vectors to represent invalid protocol inputs
without making the corpus object itself invalid.
