# SNAP nodes Brando can access, and whether they need Slurm

**Doc link:** <https://docs.google.com/document/d/1wNmYbPQp-HlfaAonAcyjyPQ4oscSMp638isJQ1yO_8o/edit>

**TLDR:** Five nodes are open to Brando with no Slurm: `skampere1-3` and `mercury1-2` (start jobs with `nohup` or `tmux`, only on idle GPUs). The other 17 GPU nodes and the CPU servers (`rambo`, `trinity`, `furiosa`, `madmax2-4,6,7`) are closed behind a Slurm account he lacks; `ilc.stanford.edu` accepts his login, so Slurm is one approval away. Recommendation: build our own GPU-claiming queue on the five open nodes now, and ask CS IT for the Slurm account when he says so.

Server list: <https://ilwiki.stanford.edu/doku.php?id=snap-servers:snap-servers> (it refused the assistant's connection on 10-22, so the node names come from the overview text Brando pasted).

Last verified: Thu 10-22-2026, 16:20-17:25 PDT.

For environment, filesystems and setup see [`snap.md`](snap.md) and the per-node files ([`skampere1`](skampere1.md), [`skampere2`](skampere2.md), [`mercury1`](mercury1.md), [`mercury2`](mercury2.md)).

## How to reach any node

Through the gateway: `ssh brando9@whale.stanford.edu`, then `ssh <node>.stanford.edu` (use the full `.stanford.edu` name; short names failed from whale). `whale` itself is a jump host only: 1 core, AFS home, never run work on it. Auth is the Kerberos ticket (Mac: `kinit`; assistant: stored keytab). Test one node at a time with pauses and no retry loops: bursts of connections look like an attack and trigger blocks (see [`snap.md`](snap.md) on the 10-15-2026 block).

## A. Accessible now (direct SSH, no Slurm)

| Node | Verified | GPUs | CPU / RAM | Disk (free at check) | Needs Slurm? | Notes |
|---|---|---|---|---|---|---|
| `skampere1` | yes, 10-22 (16:21 and later); 10 s `nohup` test job ran | 8x A100-SXM4-80GB | 128 cores, ~2 TB RAM | `/` 217 GB; `/lfs/skampere1/0` 424 GB (shared, 100% full) | no | Others' jobs share it (alexspan, vmadan, sttruong, eth127, eshaanb, truongvo, animjha, sahasras); ~4 GPUs near idle at 16:21. Brando's rl4cv runs live here. |
| `skampere2` | yes, 10-22 16:21; test job ran | 8x H200 (144 GB) | 224 cores, ~3 TB RAM | `/` 1.5 TB; `/lfs/skampere2/0` only 44 GB free (100% full) | no | No idle GPU at 16:21 (4 at ~100% util, 3 hold 83-114 GB at 0% util). CPU mostly free (load ~12-15). |
| `skampere3` | yes, 10-22 16:37; test job ran | 8x B200 (183 GB each) | 288 cores, ~3 TB RAM | `/` 238 GB free; `/lfs/skampere3/0` 386 GB free (shared, 100% full) | no | New node. No fully idle GPU at 16:37 (4 hold memory at 0% util, 2 at ~95% util). |
| `mercury1` | yes, 10-22 16:37; test job ran | 10x RTX A4000 (16 GB) | 96 cores, 487 GB RAM | `/` 63 GB free; `/lfs/mercury1/0` 756 GB free (89% full) | no | 2 idle GPUs at 16:37, 8 busy at 100% (owner not yet identified). |
| `mercury2` | yes, 10-22 16:37; test job ran | 10x RTX A4000 (16 GB) | 96 cores, ~503 GB RAM (from [`mercury2.md`](mercury2.md); not re-read) | not read: SSH to `mercury2` hung at 25 s and 70 s on 10-22 ~17:20 (cause unknown), so no `df` reading | no | All 10 GPUs idle at 16:37. Brando wants these used heavily. |

Rules for all five: only idle GPUs, pinned with `CUDA_VISIBLE_DEVICES`; never touch other users' jobs or files; mind the nearly-full shared `/lfs` disks; nothing paid and nothing in `vals-ai`. The Koyejo group's own servers are `mercury1-2` and `skampere1-2` ([InfoLab list](https://ilwiki.stanford.edu/doku.php?id=koyejo-servers:koyejo)); `skampere3` and the rest are shared SNAP machines.

## B. Reachable, but not for jobs

| Host | Status | Why |
|---|---|---|
| `whale.stanford.edu` | yes, verified | Jump host only: 1 core, no GPU, AFS home only. |

## C. Not accessible now

| Node(s) | Verified | Why |
|---|---|---|
| `turing1`, `turing2`, `turing3` | 10-22 16:37, one try each | `Access denied by pam_slurm_adopt: you have no active jobs on this node`: Slurm-gated. |
| `hyperturing1`, `hyperturing2` | same | same |
| `hyperion1` | same | same |
| `ampere1` to `ampere9` | same | same, all nine |
| `snap.stanford.edu` | ssh refused (exit 255) at 15:3x and 16:36 | Not a login host: it is the SNAP group's public web server (Rylan, 10-22). Never a target; no CS IT email needed. |
| `mercury3`, `mercury4`, `turing4`+, `ampere10`+ | do not resolve in DNS | Do not exist (`turing4` is listed as offline). |

## D. Named on the SNAP wiki overview (tested 10-22 17:05-17:12, one try each from `whale`)

Source: the SNAP server list <https://ilwiki.stanford.edu/doku.php?id=snap-servers:snap-servers> (names are from the overview text Brando pasted at 16:54). Old boxes: check python and CUDA before launching anywhere that opens.

| Node | Kind | Result | Needs Slurm? |
|---|---|---|---|
| `rambo`, `trinity`, `furiosa` | CPU compute servers | login refused: `pam_slurm_adopt: you have no active jobs on this node` | yes (`il-cpu` partition) |
| `madmax2`, `madmax3`, `madmax4`, `madmax6`, `madmax7` | CPU compute servers | same refusal | yes (`il-cpu`) |
| `madmax1`, `madmax5`, `rambino` | CPU compute servers | `connection timed out` on port 22; not listed in Slurm either: down, retired or firewalled | unknown |
| `hyperion3`, `blackwell1` | GPU servers | same refusal | yes (`il`) |
| `ilhead1` | Slurm head node | `Permission denied (publickey,gssapi...)` with the Kerberos ticket | n/a |
| `ilc.stanford.edu` | Slurm login node | **login works** (no GPU, no jobs there; AFS home not mounted for brando9). `showaccount` lists no account for `brando9` | n/a (it is where Slurm commands run) |
| `iln01` to `iln38` | base cluster nodes | not tested, by design (Slurm-managed; no scan) | yes |

## Slurm: which nodes need it, and could all nodes be managed by it?

**Today.** The five open nodes run no scheduler, so nothing queues, nothing enforces fair sharing, and two people can pick the same GPU; that is why we claim only idle GPUs and pin them. The Slurm client is on `ilc.stanford.edu`, not on the open nodes. `sinfo` there (10-22 17:12) shows partition `il` (17 GPU nodes: ampere1-9, blackwell1, hyperion1 and 3, hyperturing1-2, turing1-3; 21-day limit), `il-cpu` (15 nodes: furiosa, madmax2-4,6,7, rambo, trinity and several GPU nodes; 31-day limit) and `il-data`. Everything else in the cluster (`turing`, `hyperturing`, `hyperion1`, `hyperion3`, `ampere`, `blackwell1`, the CPU servers and the base `iln` nodes) has been migrated to Slurm and is reachable only through an allocation (`pam_slurm_adopt` lets you SSH to a node only while you hold a job there).

**Why Slurm is closed to Brando.** `showaccount` is empty for `brando9` (checked 10-13, 10-14 and again 10-22 17:12 on `ilc`: empty table); `sbatch --test-only --partition=il --account=infolab` reports an invalid account or partition. The `infolab` association was requested from `il-action@cs.stanford.edu` on 10-14 19:40, and CS IT said on 10-15 that Koyejo-group students are not eligible yet.

**Could everything be managed by Slurm?** Yes in principle; there are three routes:
1. *Use the gated nodes.* Needs the `infolab` association for `brando9` (CS IT decision, plus a sponsor). Then run through `ilc`: `srun --partition=il --qos=il-interactive --account=infolab --nodelist=<node> --gres=gpu:1 --pty bash -l` (CPU-only: `--partition=il-cpu`). Do not email CS IT again before Brando says so.
2. *Put our own five nodes under Slurm.* Needs a SNAP/CS IT admin to add them to the cluster (slurmd plus the SSH gate), which they have done for the older nodes. It is their call, not ours, and it has a cost: once gated, direct SSH stops working without an allocation, as on `ampere`, and the Koyejo nodes would compete with the shared partition rules.
3. *What we can do without anyone's permission.* A thin queue of our own on the open nodes: a small watcher that runs `nvidia-smi`, claims only idle GPUs, runs one job per GPU with `nohup`, and writes a status line per job. A `job_queue` watcher already exists on `skampere1` (max-concurrent 1). Extending it across the five nodes gives most of the benefit of Slurm (queueing, one place to look) with no admin involved.

**Recommendation.** Do step 3 now; ask for step 1 only when Brando wants to, since it unlocks 17 GPU nodes and the CPU servers; leave step 2 alone.
