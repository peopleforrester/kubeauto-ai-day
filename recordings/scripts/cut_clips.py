# ABOUTME: Cuts time-range clips from asciinema v3 .cast files with delta timestamps.
# ABOUTME: Produces uploadable clips under 8MB for asciinema.org from large recordings.
"""
Cut clips from asciinema v3 .cast files.

Handles delta-timestamp format (time since previous event, not cumulative).
Produces small .cast files suitable for asciinema.org upload (< 8MB limit).

Usage:
    # Cut a single clip by cumulative time range (seconds):
    python cut_clips.py recordings/phase-00.cast --start 103440 --end 103500 --name session-killed

    # Cut all predefined "highlight" clips:
    python cut_clips.py recordings/phase-00.cast --highlights

    # Cut clips from a JSON clip definition file:
    python cut_clips.py recordings/phase-00.cast --clips-file clips.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ClipDef:
    """Definition of a clip to cut."""
    name: str
    start_seconds: float  # Cumulative seconds from recording start
    end_seconds: float
    description: str = ""


# ---------------------------------------------------------------------------
# Predefined highlight clips for phase-00 (the full build recording)
# Times are cumulative seconds. Derived from process_cast.py events output.
# Each clip includes ~15s before the moment and ~45-60s after.
# ---------------------------------------------------------------------------

PHASE_00_HIGHLIGHTS: list[ClipDef] = [
    ClipDef(
        name="01-build-begins",
        start_seconds=5 * 3600 + 52 * 60 + 10,   # 5h 52m 10s
        end_seconds=5 * 3600 + 53 * 60 + 30,      # 5h 53m 30s
        description="'Let's start Phase 0' — the build begins",
    ),
    ClipDef(
        name="02-session-killed-recovery",
        start_seconds=28 * 3600 + 3 * 60 + 45,    # 28h 3m 45s
        end_seconds=28 * 3600 + 5 * 60 + 0,       # 28h 5m 0s
        description="Session killed, picks up where left off",
    ),
    ClipDef(
        name="03-phase-two-argocd",
        start_seconds=28 * 3600 + 43 * 60 + 40,   # 28h 43m 40s
        end_seconds=28 * 3600 + 44 * 60 + 30,     # 28h 44m 30s
        description="'Excellent, let's do phase two Argo CD!'",
    ),
    ClipDef(
        name="04-secrets-manager-frustration",
        start_seconds=29 * 3600 + 4 * 60 + 30,    # 29h 4m 30s
        end_seconds=29 * 3600 + 5 * 60 + 30,      # 29h 5m 30s
        description="Frustration with manual AWS Secrets Manager creation",
    ),
    ClipDef(
        name="05-cost-check",
        start_seconds=33 * 3600 + 59 * 60 + 15,   # 33h 59m 15s
        end_seconds=34 * 3600 + 0 * 60 + 30,      # 34h 0m 30s
        description="'Quick check: how much are the EKS clusters costing me?'",
    ),
    ClipDef(
        name="06-overnight-decision",
        start_seconds=34 * 3600 + 7 * 60 + 50,    # 34h 7m 50s
        end_seconds=34 * 3600 + 9 * 60 + 15,      # 34h 9m 15s
        description="'So I need to stop for the night...' → 'Oh, just keep going!'",
    ),
    ClipDef(
        name="07-no-github-login-button",
        start_seconds=99 * 3600 + 37 * 60 + 15,   # 99h 37m 15s
        end_seconds=99 * 3600 + 38 * 60 + 0,      # 99h 38m 0s
        description="Discovers Backstage has no GitHub login button",
    ),
    ClipDef(
        name="08-use-puppeteer-yourself",
        start_seconds=126 * 3600 + 41 * 60 + 50,  # 126h 41m 50s
        end_seconds=126 * 3600 + 42 * 60 + 30,    # 126h 42m 30s
        description="'Use puppeteer and go look at it yourself!'",
    ),
    ClipDef(
        name="09-unicorns-faster",
        start_seconds=133 * 3600 + 24 * 60 + 0,   # 133h 24m 0s
        end_seconds=133 * 3600 + 25 * 60 + 0,     # 133h 25m 0s
        description="'Can we make the unicorns move faster?'",
    ),
    ClipDef(
        name="10-meta-recording-moment",
        start_seconds=159 * 3600 + 19 * 60 + 45,  # 159h 19m 45s
        end_seconds=159 * 3600 + 21 * 60 + 0,     # 159h 21m 0s
        description="'Even this interaction was recorded! 1.8GB!'",
    ),
]


def format_duration(seconds: float) -> str:
    """Format seconds into human-readable duration."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def cut_clip(
    cast_path: Path,
    clip: ClipDef,
    output_dir: Path,
) -> Path | None:
    """Cut a single clip from a .cast file.

    Streams the file, accumulates delta timestamps to find the cumulative
    position, and extracts events within the clip's time range. The output
    .cast file has timestamps reset to deltas from the clip start.
    """
    output_path = output_dir / f"{clip.name}.cast"

    print(f"  Cutting: {clip.name} [{format_duration(clip.start_seconds)} → "
          f"{format_duration(clip.end_seconds)}]", file=sys.stderr)
    print(f"    {clip.description}", file=sys.stderr)

    cumulative = 0.0
    clip_events: list[tuple[float, str]] = []  # (delta, raw_line)
    header_line = ""
    events_in_range = 0
    past_end = False

    with open(cast_path, "r", encoding="utf-8", errors="replace") as f:
        header_line = f.readline().strip()

        prev_cumulative_in_clip = clip.start_seconds

        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if not isinstance(event, list) or len(event) < 3:
                continue

            delta = event[0]
            cumulative += delta

            # Before clip range — skip
            if cumulative < clip.start_seconds:
                continue

            # Past clip range — done
            if cumulative > clip.end_seconds:
                past_end = True
                break

            # In range — capture with adjusted delta
            adjusted_delta = cumulative - prev_cumulative_in_clip
            prev_cumulative_in_clip = cumulative

            adjusted_event = [round(adjusted_delta, 3), event[1], event[2]]
            clip_events.append((adjusted_delta, json.dumps(adjusted_event, ensure_ascii=False)))
            events_in_range += 1

    if events_in_range == 0:
        print(f"    WARNING: No events found in range!", file=sys.stderr)
        return None

    # Write the clip .cast file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header_line + "\n")
        for _, event_line in clip_events:
            f.write(event_line + "\n")

    size_bytes = output_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    duration = clip.end_seconds - clip.start_seconds

    status = "OK" if size_bytes < 8 * 1024 * 1024 else "WARNING: > 8MB"
    print(f"    → {output_path.name}: {events_in_range} events, "
          f"{size_mb:.1f} MB, ~{format_duration(duration)} [{status}]",
          file=sys.stderr)

    return output_path


def cut_clips_single_pass(
    cast_path: Path,
    clips: list[ClipDef],
    output_dir: Path,
) -> list[tuple[ClipDef, Path | None]]:
    """Cut multiple clips in a single pass through the .cast file.

    Clips must be sorted by start_seconds. Streams through the file once,
    collecting events for all clips simultaneously.
    """
    print(f"Single-pass extraction from {cast_path.name} ({len(clips)} clips)",
          file=sys.stderr)

    # State for each clip
    clip_events: dict[str, list[str]] = {c.name: [] for c in clips}
    clip_prev_cum: dict[str, float] = {c.name: c.start_seconds for c in clips}
    clip_counts: dict[str, int] = {c.name: 0 for c in clips}

    # Find the earliest start and latest end to know when to stop
    earliest_start = clips[0].start_seconds
    latest_end = max(c.end_seconds for c in clips)

    cumulative = 0.0
    header_line = ""
    total_lines = 0
    file_size = cast_path.stat().st_size

    with open(cast_path, "r", encoding="utf-8", errors="replace") as f:
        header_line = f.readline().strip()

        for line in f:
            total_lines += 1
            line = line.strip()
            if not line:
                continue

            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if not isinstance(event, list) or len(event) < 3:
                continue

            delta = event[0]
            cumulative += delta

            # Progress every 50K lines
            if total_lines % 50000 == 0:
                pct = min(100, (cumulative / latest_end) * 100) if latest_end > 0 else 0
                bar_w = 30
                filled = int(bar_w * pct / 100)
                bar = "█" * filled + "░" * (bar_w - filled)
                sys.stderr.write(f"\r  Scanning: {bar} {pct:5.1f}% | Line {total_lines:,}")
                sys.stderr.flush()

            # Before any clip starts — skip
            if cumulative < earliest_start:
                continue

            # Past all clips — done
            if cumulative > latest_end:
                break

            # Check each active clip
            for clip in clips:
                if cumulative < clip.start_seconds:
                    continue
                if cumulative > clip.end_seconds:
                    continue

                # Event is within this clip's range
                adjusted_delta = cumulative - clip_prev_cum[clip.name]
                clip_prev_cum[clip.name] = cumulative

                adjusted_event = [round(adjusted_delta, 3), event[1], event[2]]
                clip_events[clip.name].append(
                    json.dumps(adjusted_event, ensure_ascii=False)
                )
                clip_counts[clip.name] += 1

    print(f"\r  Scanning complete: {total_lines:,} lines processed    ",
          file=sys.stderr)
    print(file=sys.stderr)

    # Write clip files
    results: list[tuple[ClipDef, Path | None]] = []
    for clip in clips:
        events = clip_events[clip.name]
        if not events:
            print(f"  {clip.name}: WARNING — no events found in range!", file=sys.stderr)
            results.append((clip, None))
            continue

        output_path = output_dir / f"{clip.name}.cast"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header_line + "\n")
            for event_line in events:
                f.write(event_line + "\n")

        size_mb = output_path.stat().st_size / (1024 * 1024)
        duration = clip.end_seconds - clip.start_seconds
        status = "OK" if size_mb < 8.0 else "WARNING: > 8MB"
        print(f"  {clip.name}: {len(events)} events, "
              f"{size_mb:.1f} MB, ~{format_duration(duration)} [{status}]",
              file=sys.stderr)
        results.append((clip, output_path))

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cut clips from asciinema .cast files"
    )
    parser.add_argument("cast_file", type=Path, help="Path to .cast file")
    parser.add_argument(
        "--output-dir", "-o", type=Path, default=None,
        help="Output directory for clips (default: recordings/clips/)"
    )
    parser.add_argument(
        "--highlights", action="store_true",
        help="Cut predefined highlight clips for phase-00"
    )
    parser.add_argument(
        "--clips-file", type=Path, default=None,
        help="JSON file with clip definitions"
    )
    parser.add_argument("--start", type=float, help="Start time in cumulative seconds")
    parser.add_argument("--end", type=float, help="End time in cumulative seconds")
    parser.add_argument("--name", type=str, default="clip", help="Clip name (for single clip mode)")

    args = parser.parse_args()

    cast_path: Path = args.cast_file.resolve()
    if not cast_path.exists():
        print(f"ERROR: File not found: {cast_path}", file=sys.stderr)
        sys.exit(1)

    output_dir: Path = args.output_dir or (cast_path.parent / "clips")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine which clips to cut
    clips: list[ClipDef] = []

    if args.highlights:
        clips = PHASE_00_HIGHLIGHTS
    elif args.clips_file:
        with open(args.clips_file) as f:
            clip_data = json.load(f)
        clips = [
            ClipDef(
                name=c["name"],
                start_seconds=c["start_seconds"],
                end_seconds=c["end_seconds"],
                description=c.get("description", ""),
            )
            for c in clip_data
        ]
    elif args.start is not None and args.end is not None:
        clips = [ClipDef(name=args.name, start_seconds=args.start, end_seconds=args.end)]
    else:
        print("ERROR: Specify --highlights, --clips-file, or --start/--end", file=sys.stderr)
        sys.exit(1)

    print(f"Cutting {len(clips)} clip(s) from {cast_path.name}", file=sys.stderr)
    print(f"Output: {output_dir}", file=sys.stderr)
    print(file=sys.stderr)

    # Single-pass extraction: sort clips by start time, stream through the
    # file once, and collect events for all clips simultaneously.
    clips_sorted = sorted(clips, key=lambda c: c.start_seconds)
    results = cut_clips_single_pass(cast_path, clips_sorted, output_dir)

    # Summary
    print(f"\n{'='*60}", file=sys.stderr)
    print("Clip Summary:", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)

    uploadable = 0
    for clip, path in results:
        if path and path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            under_limit = size_mb < 8.0
            marker = "  ✓" if under_limit else "  ✗ >8MB"
            if under_limit:
                uploadable += 1
            print(f"  {clip.name:40s} {size_mb:6.1f} MB{marker}", file=sys.stderr)
        else:
            print(f"  {clip.name:40s}  EMPTY (no events in range)", file=sys.stderr)

    print(f"\n{uploadable}/{len(results)} clips under 8MB upload limit", file=sys.stderr)
    if uploadable > 0:
        print(f"\nTo upload: asciinema upload {output_dir}/<clip>.cast", file=sys.stderr)


if __name__ == "__main__":
    main()
