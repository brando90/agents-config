# Machine: Example Private Config

This file shows what a private machine override looks like. It contains REAL values
that should NEVER be committed to a public repo.

In practice, copy a template from `machine/public/` to `machine/private/` and fill in
the actual values. The `.gitignore` ensures this directory is never tracked.

---

## Example: Real Ampere1 Config

```
Hostname: ampere1.example.stanford.edu
IP: 10.0.1.42
SSH: ssh brando9@ampere1.example.stanford.edu -p 2222 -J jump.example.edu
Home: /afs/cs.stanford.edu/u/brando9
Scratch: /lfs/ampere1/0/brando9
DFS: /dfs/scratch0/brando9
GPUs: 8 x A100 80GB
CUDA: 12.4
API key path: ~/keys/openai_key.txt
```

**This is an EXAMPLE with fake values.** Replace with your actual machine details.
