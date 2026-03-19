# Machine: <MACHINE_NAME>

One-line description of this machine and its primary use case.

---

## Connection

```bash
ssh <YOUR_USERNAME>@<HOSTNAME_OR_IP>
```

- **Hostname:** `<HOSTNAME>`
- **Jump host (if any):** `<JUMP_HOST>` or N/A
- **Port:** `<PORT>` (default 22)

---

## Filesystem

| Path | Description |
|:-----|:------------|
| `<HOME_DIR>` | Home directory |
| `<SCRATCH_DIR>` | Local scratch (fast I/O, not backed up) |
| `<SHARED_FS>` | Shared filesystem (NFS/AFS/DFS) |
| `<DATA_DIR>` | Large dataset storage |

**Storage notes:**
- <Any mount quirks, quota limits, or backup policies>

---

## Compute

- **GPUs:** <GPU_COUNT> x <GPU_MODEL> (<VRAM> each)
- **CPUs:** <CPU_COUNT> x <CPU_MODEL>
- **RAM:** <RAM_AMOUNT>
- **OS:** <OS_VERSION>

---

## Environment Setup

```bash
# Activate default environment
<ACTIVATION_COMMAND>

# Key tools
<TOOL_VERSIONS>
```

---

## Common Issues

### <Issue 1 title>
**Symptom:** <What you see>
**Fix:** <What to do>

### <Issue 2 title>
**Symptom:** <What you see>
**Fix:** <What to do>

---

## Tips

- <Tip 1>
- <Tip 2>
