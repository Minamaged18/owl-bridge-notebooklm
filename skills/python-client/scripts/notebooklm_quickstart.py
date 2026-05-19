#!/usr/bin/env python3
"""
NotebookLM Python Client — Quickstart Script
=============================================
Complete working example: create notebook → add sources → generate artifacts → download.

Usage:
    python3 notebooklm_quickstart.py

Requirements:
    pip install notebooklm

Authentication:
    Expects a Playwright-format storage_state.json at:
    ~/.notebooklm/profiles/default/storage_state.json

    If auth fails, extract fresh cookies from Chrome:
    1. pip install browser_cookie3
    2. Run the cookie extraction script from the auth-fix skill
"""

import asyncio
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
STORAGE_PATH = Path.home() / ".notebooklm/profiles/default/storage_state.json"

# Sources to add to the notebook
SOURCES = [
    "https://en.wikipedia.org/wiki/Large_language_model",
    "https://en.wikipedia.org/wiki/Retrieval-augmented_generation",
]

# Output directory for downloaded artifacts
OUTPUT_DIR = Path("/tmp/notebooklm_output")

# Artifact generation timeout in seconds
ARTIFACT_TIMEOUT = 600  # 10 minutes

# Polling interval in seconds
POLL_INTERVAL = 30


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------
async def main():
    # --- Lazy import so the script fails gracefully if not installed ---
    try:
        from notebooklm.client import NotebookLMClient
        from notebooklm.types import AudioFormat
    except ImportError:
        print("ERROR: notebooklm package not installed.")
        print("  pip install notebooklm")
        sys.exit(1)

    # --- Check storage file exists ---
    if not STORAGE_PATH.exists():
        print(f"ERROR: Storage file not found at {STORAGE_PATH}")
        print("Run the auth-fix skill to extract cookies from Chrome first.")
        sys.exit(1)

    # --- Create output directory ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Connect ---
    print(f"Connecting using storage: {STORAGE_PATH}")
    try:
        async with await NotebookLMClient.from_storage(str(STORAGE_PATH)) as client:
            # is_connected is a property, NOT a method
            if not client.is_connected:
                print("ERROR: Client not connected. Cookies may be stale.")
                sys.exit(1)
            print("✓ Connected to NotebookLM")

            # --- List existing notebooks ---
            notebooks = await client.notebooks.list()
            print(f"\nExisting notebooks ({len(notebooks)}):")
            for nb in notebooks:
                print(f"  - [{nb.id}] {nb.title}")

            # --- Create a new notebook ---
            title = "LLM Research Overview"
            print(f"\nCreating notebook: '{title}'")
            nb = await client.notebooks.create(title)
            print(f"  ✓ Created: [{nb.id}] {nb.title}")

            # --- Add sources ---
            print(f"\nAdding {len(SOURCES)} sources...")
            for url in SOURCES:
                try:
                    await client.sources.add_url(nb.id, url)
                    print(f"  ✓ Added: {url}")
                except Exception as e:
                    print(f"  ✗ Failed to add {url}: {e}")

            # --- Wait for sources to be processed ---
            print("\nWaiting for sources to be processed...")
            try:
                await client.sources.wait_until_ready(nb.id)
                print("  ✓ All sources ready")
            except asyncio.TimeoutError:
                print("  ⚠ Timeout waiting for sources — proceeding anyway")

            # --- List sources ---
            try:
                sources = await client.sources.list(nb.id)
                print(f"\nSources in notebook ({len(sources)}):")
                for src in sources:
                    print(f"  - {src.title or src.url or src.id}")
            except Exception:
                pass  # Non-critical

            # --- Generate artifacts ---
            print("\nGenerating artifacts (async)...")
            tasks = {}

            try:
                result = await client.artifacts.generate_audio(
                    nb.id, audio_format=AudioFormat.DEEP_DIVE
                )
                tasks['audio'] = result.task_id
                print(f"  ✓ Audio task: {result.task_id}")
            except Exception as e:
                print(f"  ✗ Audio generation failed: {e}")

            try:
                result = await client.artifacts.generate_video(nb.id)
                tasks['video'] = result.task_id
                print(f"  ✓ Video task: {result.task_id}")
            except Exception as e:
                print(f"  ✗ Video generation failed: {e}")

            try:
                result = await client.artifacts.generate_report(nb.id)
                tasks['report'] = result.task_id
                print(f"  ✓ Report task: {result.task_id}")
            except Exception as e:
                print(f"  ✗ Report generation failed: {e}")

            try:
                result = await client.artifacts.generate_slide_deck(nb.id)
                tasks['slides'] = result.task_id
                print(f"  ✓ Slide deck task: {result.task_id}")
            except Exception as e:
                print(f"  ✗ Slide deck generation failed: {e}")

            try:
                result = await client.artifacts.generate_mind_map(nb.id)
                tasks['mindmap'] = result.task_id
                print(f"  ✓ Mind map task: {result.task_id}")
            except Exception as e:
                print(f"  ✗ Mind map generation failed: {e}")

            try:
                result = await client.artifacts.generate_flashcards(nb.id)
                tasks['flashcards'] = result.task_id
                print(f"  ✓ Flashcards task: {result.task_id}")
            except Exception as e:
                print(f"  ✗ Flashcards generation failed: {e}")

            try:
                result = await client.artifacts.generate_quiz(nb.id)
                tasks['quiz'] = result.task_id
                print(f"  ✓ Quiz task: {result.task_id}")
            except Exception as e:
                print(f"  ✗ Quiz generation failed: {e}")

            try:
                result = await client.artifacts.generate_data_table(nb.id)
                tasks['datatable'] = result.task_id
                print(f"  ✓ Data table task: {result.task_id}")
            except Exception as e:
                print(f"  ✗ Data table generation failed: {e}")

            # --- Poll for completion ---
            if tasks:
                print(f"\nPolling {len(tasks)} artifacts for completion...")
                print(f"  (timeout: {ARTIFACT_TIMEOUT}s, interval: {POLL_INTERVAL}s)")

                completed = set()
                failed = set()
                elapsed = 0

                while len(completed) + len(failed) < len(tasks) and elapsed < ARTIFACT_TIMEOUT:
                    await asyncio.sleep(POLL_INTERVAL)
                    elapsed += POLL_INTERVAL

                    for name, task_id in tasks.items():
                        if name in completed or name in failed:
                            continue
                        try:
                            status = await client.artifacts.poll_status(nb.id, task_id)
                            if status.status == 3:  # done
                                completed.add(name)
                                print(f"  ✓ {name} ready ({elapsed}s)")
                            elif status.status == 2:  # failed
                                failed.add(name)
                                print(f"  ✗ {name} failed: {status.error}")
                            # status == 1 means still in progress
                        except Exception as e:
                            print(f"  ⚠ Error polling {name}: {e}")

                # Report any still-pending
                pending = set(tasks.keys()) - completed - failed
                if pending:
                    print(f"  ⏳ Still pending after timeout: {', '.join(pending)}")

            # --- Download completed artifacts ---
            download_map = {
                'audio':   ('download_audio',   OUTPUT_DIR / 'audio.mp3'),
                'video':   ('download_video',   OUTPUT_DIR / 'video.mp4'),
                'report':  ('download_report',  OUTPUT_DIR / 'report.md'),
                'slides':  ('download_slide_deck', OUTPUT_DIR / 'slides.pdf'),
                'mindmap': ('download_mind_map',   OUTPUT_DIR / 'mindmap.json'),
                'flashcards': ('download_flashcards', OUTPUT_DIR / 'flashcards.json'),
                'quiz':    ('download_quiz',    OUTPUT_DIR / 'quiz.json'),
                'datatable': ('download_data_table', OUTPUT_DIR / 'data.csv'),
            }

            print(f"\nDownloading completed artifacts to {OUTPUT_DIR}/")
            for name, output_path in download_map.items():
                if name not in completed:
                    continue
                method_name, path = output_path
                try:
                    method = getattr(client.artifacts, method_name)
                    await method(nb.id, str(path))
                    size = path.stat().st_size if path.exists() else 0
                    print(f"  ✓ {name}: {path} ({size:,} bytes)")
                except Exception as e:
                    print(f"  ✗ {name} download failed: {e}")

            # --- Summary ---
            print(f"\n{'='*60}")
            print(f"Done! Notebook: {nb.title} [{nb.id}]")
            print(f"  Completed: {len(completed)}/{len(tasks)} artifacts")
            if failed:
                print(f"  Failed:    {', '.join(failed)}")
            print(f"  Output:    {OUTPUT_DIR}/")
            print(f"{'='*60}")

    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nTroubleshooting:")
        print("  1. Check that storage_state.json exists and has fresh cookies")
        print("  2. Run: pip install browser_cookie3")
        print("  3. Run the auth-fix skill to extract fresh cookies from Chrome")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
