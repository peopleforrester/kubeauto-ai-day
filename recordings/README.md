# Build Recordings

Screen recordings and terminal captures for each phase of the IDP build.

## Recording Tools

- **asciinema** (`.cast` files) — Terminal session recordings, replayable
- **script** (`.log` + timing files) — Raw terminal output with timing data

## Files

| Phase | asciinema | script log | script timing | Status |
|-------|-----------|------------|---------------|--------|
| Phase 0 | phase-00.cast | phase-00.log | phase-00-timing.log | In progress |
| Phase 1 | phase-01.cast | — | phase-01-timing.log | Captured |
| Phase 2 | phase-02.cast | phase-02.log | phase-02-timing.log | Not started |
| Phase 3 | phase-03.cast | phase-03.log | phase-03-timing.log | Not started |
| Phase 4 | phase-04.cast | phase-04.log | phase-04-timing.log | Not started |
| Phase 5 | phase-05.cast | phase-05.log | phase-05-timing.log | Not started |
| Phase 6 | phase-06.cast | phase-06.log | phase-06-timing.log | Not started |
| Phase 7 | phase-07.cast | phase-07.log | phase-07-timing.log | Not started |

## Notes

- `.cast`, `.log`, `.mp4`, and timing files are gitignored (large binary/text files)
- `recordings/logs/` stores text logs from overnight Ralph Wiggum builds
- Start recording BEFORE launching Claude Code (recording wraps the shell)

## Starting Recording

```bash
cd /path/to/kubeauto-ai-day
asciinema rec recordings/phase-XX.cast
script -T recordings/phase-XX-timing.log recordings/phase-XX.log
claude
```

To stop: exit Claude Code → `exit` (ends script) → `exit` (ends asciinema)
