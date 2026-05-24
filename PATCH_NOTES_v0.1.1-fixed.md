# Patch Notes — v0.1.1-fixed

Fixed a JSONL ledger newline bug in `reference/python/axiom/ledger.py`.

## Fix

Replaced the literal escaped sequence:

```python
"\\n"
```

with a real newline escape:

```python
"\n"
```

This ensures each ledger entry is written as a real JSONL line.

## Verification

Conformance tests pass after the patch.
