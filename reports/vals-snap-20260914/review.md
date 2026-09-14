# Independent authentication review

**Doc link:** <https://github.com/brando90/agents-config/blob/main/reports/vals-snap-20260914/review.md>

**TLDR:** Final scripts passed a fresh Codex review after the builder fixed credential-read failure and executable-symlink handling.

VERDICT: PASS  
CRITICAL_ISSUES: 0  
MAJOR_ISSUES: 0

No remaining blocking findings in the final versions. Concurrent edits corrected credential-read failure handling at [installer line 63](/Users/sanmikoyejo-mba-1/.codex/vals-snap-setup/repo/scripts/install_vals_node.sh:63) and executable-link rejection at [line 30](/Users/sanmikoyejo-mba-1/.codex/vals-snap-setup/repo/scripts/install_vals_node.sh:30). This verdict covers the final content fingerprints below.

Tests performed:

- Both scripts passed `bash -n`.
- Twelve mocked wrapper/routing cases passed, covering argument preservation, authentication isolation, and credential-failure rejection.
- Nine mocked installer cases passed, covering fresh installation, executable reuse, hash mismatches, symbolic links, ownership, and writable directories.
- Final file fingerprints matched the reviewed versions.

Concurrency was inspected statically; no live node installation or concurrency stress test ran. No files changed, credentials read, network calls made, or reviewers dispatched. The requested model/effort selection was not independently verified.

**TLDR-end:** [vals: installer-review] The final scripts pass this scoped review with zero critical or major findings; live installation remains untested here.
**Snapshot:** Final Secure Hash Algorithm 256-bit (SHA-256) fingerprints and representative test output:
```text
install_vals_node.sh: 471e447c0b7369f3c7b35b671670707fd1266c68f8ce732c03cb3c27fffacd36
vals_remote_entry.sh: 6e88f7665721340d62950ccce981a79ffd5ca163ef703450699db2bed058f0f0
PASS installer simulation: changed source during copy
PASS installer simulation: linked executable
PASS installer simulation: group-writable directory
```
Builder verification: reviewer rollout turn_context reports model gpt-6-astra and effort ultra. Both final file fingerprints match the working tree. Portable fake-credential regression tests also pass.
