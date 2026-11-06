"""Local CLI fallback for the Omni Video Studio pipeline (spec 6.2).

Runs the whole flow from the terminal without the web UI. Because script
generation is a HUMAN-IN-THE-LOOP prompt relay, `--manual-prompt` prints the
assembled Master Prompt, waits for you to paste the model's JSON back, then
synthesizes audio, renders the Remotion video, runs the Telegram gate and
uploads.

Examples:
    python main.py --topic "How Shazam works" --genre EVERYDAY_TECH --manual-prompt
    python main.py --topic "Braess paradox" --genre PARADOX_LOGIC \
        --manual-prompt --dry-run --skip-approval
    python main.py --payload output/render_payload.json --dry-run --skip-approval

Safety: pair --dry-run with --skip-approval for local tests so nothing is ever
published or sent to the Telegram gate.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import config  # type: ignore  # noqa: E402
import reference_gatherer  # type: ignore  # noqa: E402
import prompt_assembler  # type: ignore  # noqa: E402
import payload_ops  # type: ignore  # noqa: E402
import pipeline  # type: ignore  # noqa: E402


def _banner(msg: str) -> None:
    print("\n" + "=" * 70 + f"\n  {msg}\n" + "=" * 70)


def _read_pasted_json() -> str:
    print("\n>>> Paste the model's JSON output below, then type a line with only "
          "'END' and press Enter:\n")
    lines = []
    for line in sys.stdin:
        if line.strip() == "END":
            break
        lines.append(line)
    return "".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Omni Video Studio CLI")
    parser.add_argument("--topic", help="Topic to make a video about")
    parser.add_argument("--genre", default="EVERYDAY_TECH",
                        help="Genre enum (e.g. SCIENCE_PHYSICS, CRIME_MYSTERY)")
    parser.add_argument("--format", default="landscape", choices=["landscape", "portrait"])
    parser.add_argument("--manual-prompt", action="store_true",
                        help="Print the Master Prompt and wait for pasted JSON")
    parser.add_argument("--payload", help="Skip prompt relay; use an existing JSON payload file")
    parser.add_argument("--dry-run", action="store_true", help="Skip the YouTube upload")
    parser.add_argument("--skip-approval", action="store_true", help="Skip the Telegram gate")
    parser.add_argument("--skip-video", action="store_true", help="Skip the Remotion render")
    args = parser.parse_args()

    # --- Obtain the raw JSON (from a file, or via the prompt relay) -----------
    if args.payload:
        _banner(f"Loading payload from {args.payload}")
        with open(args.payload, encoding="utf-8") as fh:
            raw_json = fh.read()
    else:
        if not args.topic:
            parser.error("--topic is required unless --payload is given")
        _banner("STAGE 1-2: Grounding + Master Prompt assembly")
        ref = reference_gatherer.gather(args.topic)
        print(f"[cli] Reference: method={ref.method} chars={len(ref.markdown)} sources={len(ref.sources)}")
        assembled = prompt_assembler.assemble(
            args.topic, args.genre, args.format, ref.markdown, ref.sources
        )
        print("\n" + "-" * 70 + "\n  MASTER PROMPT (copy into Gemini Advanced / Claude Pro):\n" + "-" * 70)
        print(assembled["master_prompt"])
        if not args.manual_prompt:
            print("\n[cli] --manual-prompt not set; stopping after printing the prompt.")
            return
        raw_json = _read_pasted_json()

    # --- Validate -------------------------------------------------------------
    _banner("STAGE 3: Validate pasted JSON against OmniRenderPayload")
    report = payload_ops.validate(raw_json, video_format=args.format)
    if not report.ok or report.payload is None:
        print("[cli] VALIDATION FAILED:")
        for e in report.errors:
            print(f"   - {e}")
        sys.exit(1)
    for w in report.warnings:
        print(f"[cli] warning: {w}")
    print(f"[cli] Valid. {report.summary}")

    # --- Run the pipeline -----------------------------------------------------
    _banner("STAGE 4-6: Audio -> Render -> Telegram -> YouTube")
    print(f"[cli] dry_run={args.dry_run} skip_approval={args.skip_approval} skip_video={args.skip_video}")
    job_id = pipeline.start_job(
        report.payload,
        dry_run=args.dry_run,
        skip_approval=args.skip_approval,
        skip_video=args.skip_video,
    )
    # Poll to completion (the pipeline runs on a background thread).
    while True:
        job = pipeline.get_job(job_id)
        if job is None:
            break
        stages = "  ".join(f"{s['key']}:{s['status']}" for s in job["stages"])
        print(f"[cli] {job['status']:8s} | {stages}")
        if job["status"] in ("done", "error"):
            if job.get("video_id"):
                print(f"[cli] Published: https://youtu.be/{job['video_id']}")
            if job.get("error"):
                print(f"[cli] ERROR: {job['error']}")
            break
        time.sleep(3)
    _banner("DONE")


if __name__ == "__main__":
    main()
