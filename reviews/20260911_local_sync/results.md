# Local catch-up rule and coordinator schedule

**TLDR:** Add one scheduled owner for remote progress and safe editor-checkout catch-up. The proposed rule preserves local-only work, uses fast-forward updates only, and keeps laptop scheduling separate from remote recovery.

**Status:** RUNNING — policy FIXED; publication and activation pending
**Last updated:** 2026-09-11 15:23 PDT

| Phase | State | Evidence |
|---|---|---|
| Rule and schedule prompt | DONE | Trigger Rule46 local catch-up paragraph; remote-job-dispatch.md; schedule_prompt.md |
| Legacy folder audit | DONE | 24126 files;22935 already have matching blobs on VeriBench main;1191 additional byte versions retained for preservation |
| Preservation and folder cleanup | DONE | VeriBench main3a5eb0266; all24126 files verified; complete local backup retained; one active71 |
| Independent acceptance review | FIXED | Strongest Codex fallback after Claude quota failure;2major+1minor fixed;8deterministic checks pass |
| Rule publication and schedule activation | PENDING | Verify main and actual automation record before claiming enabled |

No launcher, scientific data or global model default is modified by this policy change. An existing manually paused schedule will remain paused; the user explicitly requested one coordinator schedule for this task.
