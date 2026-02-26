# Build Recordings

Terminal captures of the entire IDP build, from Phase 0 scaffolding through Phase 7 hardening.

## Recording Tools

- **asciinema** (`.cast` files) — Terminal session recordings, replayable
- **script** (`.log` + timing files) — Raw terminal output with timing data

## Primary Recording

The entire build was captured in a single continuous asciinema session:

| File | Size | Wall Clock | Active Time | Phases Covered |
|------|------|------------|-------------|----------------|
| `phase-00.cast` | 1.8 GB | 173h 20m | 10h 48m | All (0–7) |

The original plan was per-phase recordings, but the session ran continuously
across the full build. Phase timestamps from the summary:

| Phase | Approx. Start | Prompt |
|-------|---------------|--------|
| 0 | ~5h 52m | "Let's start Phase 0" |
| 1 | ~26h 27m | "Let's start Phase 1" |
| 2 | ~28h 44m | "Excellent, let's do phase two Argo CD!" |
| 3 | ~31h 4m | "Okay, let's start phase three!" |
| 4 | ~33h 52m | "Let's do phase four!" |
| 5 | ~34h 24m | "Let's keep going with phase five!" |
| 6 | ~134h | Phase 6 integration work |
| 7 | ~152h+ | Phase 7 hardening and collateral |

A separate shorter recording also exists:

| File | Description |
|------|-------------|
| `phase-01.cast` | 60 MB standalone Phase 1 capture |

## Highlight Clips

10 clips extracted from `phase-00.cast` via `scripts/cut_clips.py`, each under
8 MB for asciinema.org upload:

| Clip | File | Description |
|------|------|-------------|
| 01 | `clips/01-build-begins.cast` | Build kickoff |
| 02 | `clips/02-session-killed-recovery.cast` | Session killed, recovery |
| 03 | `clips/03-phase-two-argocd.cast` | ArgoCD bootstrap |
| 04 | `clips/04-secrets-manager-frustration.cast` | ESO/Secrets Manager debugging |
| 05 | `clips/05-cost-check.cast` | Cost awareness check |
| 06 | `clips/06-overnight-decision.cast` | Overnight build decision |
| 07 | `clips/07-no-github-login-button.cast` | Backstage auth discovery |
| 08 | `clips/08-use-puppeteer-yourself.cast` | Puppeteer self-use moment |
| 09 | `clips/09-unicorns-faster.cast` | Unicorn Party speedrun |
| 10 | `clips/10-meta-recording-moment.cast` | Meta recording moment |

## Processing Scripts

Both in `scripts/`:

- **`process_cast.py`** — Streams large .cast files, strips ANSI, extracts
  prompts/tool calls/errors/timing. Produces `-clean.txt`, `-summary.md`,
  `-events.json`.
- **`cut_clips.py`** — Cuts time-range clips from .cast files with
  delta-adjusted timestamps. Keeps output under 8 MB.

## Generated Outputs

| File | Description | Gitignored? |
|------|-------------|-------------|
| `phase-00-summary.md` | Session stats, idle periods, events, clip suggestions | No (committed) |
| `phase-01-summary.md` | Phase 1 standalone summary | No (committed) |
| `phase-00-clean.txt` | ANSI-stripped transcript (597 MB) | Yes |
| `phase-00-events.json` | Structured events (224 MB) | Yes |
| `phase-00-timing.log` | Raw timing data | Yes |
| `phase-00.log` | Raw script output | Yes |

## Notes

- `.cast`, `.log`, `.mp4`, and timing files are gitignored (large binary/text files)
- Summary files (`*-summary.md`) are committed via `.gitignore` exception
- `recordings/logs/` stores text logs from overnight Ralph Wiggum builds
