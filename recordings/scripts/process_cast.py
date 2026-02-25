# ABOUTME: Streaming processor for asciinema v3 .cast files from Claude Code sessions.
# ABOUTME: Extracts clean transcripts, user prompts, tool calls, errors, and timing stats.
"""
Process asciinema .cast files to extract:
- Clean, readable transcripts (ANSI stripped)
- User prompts with timestamps
- Claude Code tool calls with timestamps
- Errors and failures
- Key milestones (commits, test results, phase markers)
- Timing statistics

Usage:
    python process_cast.py <path-to-cast-file> [--output-dir <dir>]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO


# ---------------------------------------------------------------------------
# ANSI / terminal escape stripping
# ---------------------------------------------------------------------------

# Matches ANSI escape sequences: CSI sequences, OSC sequences, and simple escapes
_ANSI_RE = re.compile(
    r"""
    \x1b          # ESC character
    (?:
        \[\d+C                   # Cursor forward (special — replaced with spaces)
      | \[[\d;]*[A-Za-z]        # CSI sequences  (e.g. \e[38;5;174m, \e[?2004h)
      | \[\?[\d;]*[a-zA-Z]      # CSI ? sequences
      | \].*?(?:\x07|\x1b\\)    # OSC sequences  (e.g. \e]9;4;0;\a)
      | [()][AB012]             # Character set selection
      | [>=<]                   # Keypad modes
      | .                       # Two-char sequences (e.g. \eM)
    )
    """,
    re.VERBOSE,
)

# Carriage return cleanup, control chars, and [1C (single-char-forward) placeholders
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _ansi_replace(match: re.Match[str]) -> str:
    """Replace ANSI sequences, converting cursor-forward to spaces."""
    seq = match.group(0)
    # \x1b[NC — cursor forward N positions → N spaces
    m = re.match(r"\x1b\[(\d+)C", seq)
    if m:
        return " " * int(m.group(1))
    return ""


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences and control characters from text.

    Cursor-forward sequences (\\x1b[NC) are replaced with N spaces
    since Claude Code uses them for word spacing in rendered output.
    """
    text = _ANSI_RE.sub(_ansi_replace, text)
    # Catch any remaining literal [NC that survived partial stripping
    text = re.sub(r"\[(\d+)C", lambda m: " " * int(m.group(1)), text)
    text = _CONTROL_RE.sub("", text)
    return text


# ---------------------------------------------------------------------------
# Pattern matchers for Claude Code output
# ---------------------------------------------------------------------------

# User prompt line (after ANSI strip): starts with ❯ or > followed by text
_PROMPT_RE = re.compile(r"^[❯>]\s+(.+)", re.MULTILINE)

# Claude tool call: ● ToolName(args)  or  ● ToolName
_TOOL_CALL_RE = re.compile(r"^●\s+(Bash|Read|Write|Edit|Glob|Grep|Task|WebSearch|WebFetch)\s*\(?(.*?)\)?\s*$", re.MULTILINE)

# Error patterns
_ERROR_RE = re.compile(
    r"(?:^|\s)"
    r"(?:Error|ERROR|error|FAILED|Failed|Exception|Traceback|FATAL|fatal|panic)"
    r"(?:\s|:|\b)",
    re.MULTILINE,
)

# Git commit pattern — require explicit commit-related context, not just hex strings
_COMMIT_RE = re.compile(
    r"(?:"
    r"git commit"               # explicit git commit command
    r"|git add .* && git commit" # add+commit combo
    r"|\] \d+ files? changed"   # git commit summary output
    r"|create mode \d+"         # git commit file listing
    r"|\b[0-9a-f]{7,12}\b\s+\S.*(?:commit|merge|push|Merge)" # hash + commit context
    r")",
    re.IGNORECASE,
)

# Test result patterns — match actual pytest execution output, not filenames
_TEST_RE = re.compile(
    r"(?:"
    r"uv run pytest"                  # test command invocation
    r"|\bpytest\b.*\btests/"          # pytest with test path
    r"|\d+\s+passed"                  # pytest summary "X passed"
    r"|\d+\s+failed"                  # pytest summary "X failed"
    r"|PASSED\s*$"                    # individual test PASSED
    r"|FAILED\s*$"                    # individual test FAILED
    r"|={3,}\s*\d+\s+(?:passed|failed)" # pytest summary bar
    r")",
    re.IGNORECASE,
)

# Phase completion markers
_PHASE_RE = re.compile(r"(?:PHASE\d+_DONE|ALL_PHASES_COMPLETE|<promise>)", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Event:
    """A timestamped event extracted from the recording."""
    timestamp: float
    category: str  # prompt, tool_call, error, commit, test, phase
    text: str


@dataclass
class IdlePeriod:
    """A detected idle gap in the recording."""
    start_time: float
    duration: float


@dataclass
class SessionStats:
    """Aggregate statistics for the recording session."""
    wall_clock_seconds: float = 0.0
    active_seconds: float = 0.0
    idle_seconds: float = 0.0
    prompt_count: int = 0
    tool_call_count: int = 0
    error_count: int = 0
    commit_count: int = 0
    test_run_count: int = 0
    idle_periods: list[IdlePeriod] = field(default_factory=list)


# Threshold for what counts as "idle" — gaps longer than this are idle periods
IDLE_THRESHOLD_SECONDS = 300  # 5 minutes


@dataclass
class ProcessingState:
    """Mutable state carried through the streaming processor."""
    output_buffer: str = ""
    cumulative_time: float = 0.0  # Running sum of delta timestamps
    last_flush_ts: float = 0.0
    events: list[Event] = field(default_factory=list)
    stats: SessionStats = field(default_factory=SessionStats)
    clean_lines: list[str] = field(default_factory=list)
    line_count: int = 0
    bytes_processed: int = 0
    total_bytes: int = 0
    # Deduplication: track seen prompt text to filter out conversation replays
    seen_prompts: dict[str, float] = field(default_factory=dict)  # text -> first timestamp


# ---------------------------------------------------------------------------
# Core processing
# ---------------------------------------------------------------------------

FLUSH_THRESHOLD = 8192  # Flush buffer every 8KB of accumulated output


def process_chunk(state: ProcessingState, timestamp: float, data: str) -> None:
    """Process a single output event from the .cast file."""
    state.output_buffer += data

    # Flush periodically to avoid unbounded memory growth
    if len(state.output_buffer) >= FLUSH_THRESHOLD:
        flush_buffer(state, timestamp)


def flush_buffer(state: ProcessingState, timestamp: float) -> None:
    """Strip ANSI from buffer, scan for patterns, and emit clean text."""
    if not state.output_buffer:
        return

    clean = strip_ansi(state.output_buffer)
    state.output_buffer = ""

    # Skip empty chunks
    if not clean.strip():
        return

    # Split into lines for pattern matching
    lines = clean.split("\n")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            # Collapse blank lines — only emit one
            if state.clean_lines and state.clean_lines[-1] != "":
                state.clean_lines.append("")
            continue

        state.clean_lines.append(stripped)

        # --- Pattern matching ---

        if _PROMPT_RE.search(stripped):
            # Deduplicate: Claude Code replays conversation history on
            # restart/compact, causing each prompt to appear multiple times.
            # Keep only the first occurrence of each unique prompt text.
            prompt_key = stripped[:200]  # Normalize by truncating
            if prompt_key not in state.seen_prompts:
                state.seen_prompts[prompt_key] = timestamp
                state.events.append(Event(timestamp, "prompt", stripped))
                state.stats.prompt_count += 1

        if _TOOL_CALL_RE.search(stripped):
            state.events.append(Event(timestamp, "tool_call", stripped))
            state.stats.tool_call_count += 1

        if _ERROR_RE.search(stripped):
            # Avoid false positives from code comments, import paths, etc.
            if not stripped.startswith("#") and "error_handler" not in stripped.lower():
                state.events.append(Event(timestamp, "error", stripped))
                state.stats.error_count += 1

        if _COMMIT_RE.search(stripped):
            state.events.append(Event(timestamp, "commit", stripped))
            state.stats.commit_count += 1

        if _TEST_RE.search(stripped):
            state.events.append(Event(timestamp, "test", stripped))
            state.stats.test_run_count += 1

        if _PHASE_RE.search(stripped):
            state.events.append(Event(timestamp, "phase", stripped))

    state.last_flush_ts = timestamp


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


def print_progress(state: ProcessingState) -> None:
    """Print progress indicator to stderr."""
    if state.total_bytes > 0:
        pct = (state.bytes_processed / state.total_bytes) * 100
        bar_width = 30
        filled = int(bar_width * pct / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        mb_done = state.bytes_processed / (1024 * 1024)
        mb_total = state.total_bytes / (1024 * 1024)
        sys.stderr.write(
            f"\r  Processing: {bar} {pct:5.1f}% ({mb_done:.0f}/{mb_total:.0f} MB) "
            f"| Lines: {state.line_count:,}"
        )
        sys.stderr.flush()


def process_cast_file(cast_path: Path) -> ProcessingState:
    """Stream-process a .cast file and return the extracted state."""
    state = ProcessingState()

    # Get file size for progress
    state.total_bytes = cast_path.stat().st_size

    print(f"Processing: {cast_path.name}", file=sys.stderr)
    print(f"File size:  {state.total_bytes / (1024*1024):.1f} MB", file=sys.stderr)

    with open(cast_path, "r", encoding="utf-8", errors="replace") as f:
        # First line is the header
        header_line = f.readline()
        state.bytes_processed += len(header_line.encode("utf-8", errors="replace"))

        try:
            header = json.loads(header_line)
        except json.JSONDecodeError:
            print("WARNING: Could not parse header line", file=sys.stderr)
            header = {}

        # Process event lines — timestamps are DELTA (time since previous event)
        for line in f:
            state.line_count += 1
            state.bytes_processed += len(line.encode("utf-8", errors="replace"))

            # Progress every 50K lines
            if state.line_count % 50000 == 0:
                print_progress(state)

            line = line.strip()
            if not line:
                continue

            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if not isinstance(event, list) or len(event) < 3:
                continue

            delta, event_type, data = event[0], event[1], event[2]

            # Track idle periods (large gaps)
            if delta > IDLE_THRESHOLD_SECONDS:
                state.stats.idle_periods.append(
                    IdlePeriod(start_time=state.cumulative_time, duration=delta)
                )
                state.stats.idle_seconds += delta

            # Accumulate delta into cumulative time
            state.cumulative_time += delta

            # Only process output events
            if event_type == "o":
                process_chunk(state, state.cumulative_time, data)

    # Final flush
    flush_buffer(state, state.cumulative_time)
    print_progress(state)
    print("", file=sys.stderr)  # Newline after progress bar

    state.stats.wall_clock_seconds = state.cumulative_time
    state.stats.active_seconds = state.cumulative_time - state.stats.idle_seconds

    return state


# ---------------------------------------------------------------------------
# Output generation
# ---------------------------------------------------------------------------

def write_clean_transcript(state: ProcessingState, output_path: Path) -> None:
    """Write the clean, ANSI-stripped transcript."""
    print(f"Writing clean transcript: {output_path}", file=sys.stderr)
    with open(output_path, "w", encoding="utf-8") as f:
        for line in state.clean_lines:
            f.write(line + "\n")
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  Clean transcript: {size_mb:.1f} MB, {len(state.clean_lines):,} lines", file=sys.stderr)


def write_summary(state: ProcessingState, output_path: Path, source_name: str) -> None:
    """Write the summary markdown with timing, events, and stats."""
    print(f"Writing summary: {output_path}", file=sys.stderr)
    stats = state.stats

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Recording Summary: {source_name}\n\n")

        # --- Timing ---
        f.write("## Session Timing\n\n")
        f.write(f"- **Wall clock time:** {format_duration(stats.wall_clock_seconds)}\n")
        f.write(f"- **Active time:** {format_duration(stats.active_seconds)}\n")
        f.write(f"- **Idle time:** {format_duration(stats.idle_seconds)}")
        f.write(f" ({len(stats.idle_periods)} idle period(s) > 5min)\n")
        if stats.idle_periods:
            f.write("\n**Idle periods:**\n")
            for ip in stats.idle_periods:
                f.write(f"  - At {format_duration(ip.start_time)}: "
                        f"gap of {format_duration(ip.duration)}\n")
        f.write("\n")

        # --- Stats ---
        f.write("## Statistics\n\n")
        f.write(f"| Metric | Count |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| User prompts | {stats.prompt_count} |\n")
        f.write(f"| Tool calls | {stats.tool_call_count} |\n")
        f.write(f"| Errors detected | {stats.error_count} |\n")
        f.write(f"| Commits | {stats.commit_count} |\n")
        f.write(f"| Test runs | {stats.test_run_count} |\n\n")

        # --- User Prompts ---
        prompts = [e for e in state.events if e.category == "prompt"]
        if prompts:
            f.write("## User Prompts\n\n")
            f.write("| Time | Prompt |\n")
            f.write("|------|--------|\n")
            for e in prompts:
                time_str = format_duration(e.timestamp)
                # Truncate long prompts for the table
                text = e.text[:120].replace("|", "\\|")
                f.write(f"| {time_str} | {text} |\n")
            f.write("\n")

        # --- Errors ---
        errors = [e for e in state.events if e.category == "error"]
        if errors:
            f.write("## Errors & Failures\n\n")
            # Deduplicate similar errors
            seen: set[str] = set()
            for e in errors:
                key = e.text[:80]
                if key not in seen:
                    seen.add(key)
                    time_str = format_duration(e.timestamp)
                    f.write(f"- **[{time_str}]** `{e.text[:200]}`\n")
            f.write("\n")

        # --- Tool Calls ---
        tool_calls = [e for e in state.events if e.category == "tool_call"]
        if tool_calls:
            f.write("## Tool Calls (sample)\n\n")
            # Show first 50 and last 10
            display = tool_calls[:50]
            if len(tool_calls) > 60:
                f.write(f"*Showing first 50 of {len(tool_calls)} tool calls*\n\n")
            for e in display:
                time_str = format_duration(e.timestamp)
                f.write(f"- **[{time_str}]** {e.text[:150]}\n")
            if len(tool_calls) > 60:
                f.write(f"\n*... {len(tool_calls) - 50} more tool calls ...*\n\n")
                f.write("### Last 10 tool calls\n\n")
                for e in tool_calls[-10:]:
                    time_str = format_duration(e.timestamp)
                    f.write(f"- **[{time_str}]** {e.text[:150]}\n")
            f.write("\n")

        # --- Commits ---
        commits = [e for e in state.events if e.category == "commit"]
        if commits:
            f.write("## Git Activity\n\n")
            seen_commits: set[str] = set()
            for e in commits:
                key = e.text[:60]
                if key not in seen_commits:
                    seen_commits.add(key)
                    time_str = format_duration(e.timestamp)
                    f.write(f"- **[{time_str}]** {e.text[:200]}\n")
            f.write("\n")

        # --- Test Results ---
        tests = [e for e in state.events if e.category == "test"]
        if tests:
            f.write("## Test Activity\n\n")
            seen_tests: set[str] = set()
            for e in tests:
                key = e.text[:60]
                if key not in seen_tests:
                    seen_tests.add(key)
                    time_str = format_duration(e.timestamp)
                    f.write(f"- **[{time_str}]** {e.text[:200]}\n")
            f.write("\n")

        # --- Phase Markers ---
        phases = [e for e in state.events if e.category == "phase"]
        if phases:
            f.write("## Phase Milestones\n\n")
            for e in phases:
                time_str = format_duration(e.timestamp)
                f.write(f"- **[{time_str}]** {e.text[:200]}\n")
            f.write("\n")

        # --- Clip Candidates ---
        f.write("## Suggested Clip Timestamps\n\n")
        f.write("These are interesting moments that might make good clips for the talk:\n\n")

        clip_events: list[tuple[str, Event]] = []
        if prompts:
            clip_events.append(("First prompt", prompts[0]))
            if len(prompts) > 1:
                clip_events.append(("Last prompt", prompts[-1]))
        for e in errors[:5]:
            clip_events.append(("Error moment", e))
        for e in [ev for ev in state.events if ev.category == "phase"]:
            clip_events.append(("Phase completion", e))
        # Test failures are interesting
        for e in tests:
            if "FAILED" in e.text.upper() or "PASSED" in e.text.upper():
                clip_events.append(("Test result", e))

        clip_events.sort(key=lambda x: x[1].timestamp)
        seen_clips: set[str] = set()
        for label, e in clip_events[:20]:
            key = f"{e.timestamp:.0f}"
            if key not in seen_clips:
                seen_clips.add(key)
                start = max(0, e.timestamp - 5)
                end = e.timestamp + 30
                f.write(f"- **{label}** [{format_duration(e.timestamp)}]: "
                        f"clip range `{start:.1f}s - {end:.1f}s`\n")
                f.write(f"  {e.text[:100]}\n")
        f.write("\n")

    print(f"  Summary written: {output_path}", file=sys.stderr)


def write_events_json(state: ProcessingState, output_path: Path) -> None:
    """Write all events as JSON for downstream tooling (e.g., clip cutting)."""
    print(f"Writing events JSON: {output_path}", file=sys.stderr)
    events_data = [
        {
            "timestamp": e.timestamp,
            "time_human": format_duration(e.timestamp),
            "category": e.category,
            "text": e.text[:500],
        }
        for e in state.events
    ]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(events_data, f, indent=2, ensure_ascii=False)
    print(f"  Events: {len(events_data)} total", file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Process asciinema .cast files from Claude Code sessions"
    )
    parser.add_argument("cast_file", type=Path, help="Path to .cast file")
    parser.add_argument(
        "--output-dir", "-o", type=Path, default=None,
        help="Output directory (defaults to same directory as input)"
    )
    args = parser.parse_args()

    cast_path: Path = args.cast_file.resolve()
    if not cast_path.exists():
        print(f"ERROR: File not found: {cast_path}", file=sys.stderr)
        sys.exit(1)

    output_dir: Path = args.output_dir or cast_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Derive output filenames from input
    stem = cast_path.stem  # e.g., "phase-00"

    # Process
    state = process_cast_file(cast_path)

    # Write outputs
    write_clean_transcript(state, output_dir / f"{stem}-clean.txt")
    write_summary(state, output_dir / f"{stem}-summary.md", stem)
    write_events_json(state, output_dir / f"{stem}-events.json")

    print(
        f"\nDone! Wall clock: {format_duration(state.stats.wall_clock_seconds)}"
        f" | Active: {format_duration(state.stats.active_seconds)}",
        file=sys.stderr,
    )
    print(f"Output files in: {output_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
