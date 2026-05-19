---
name: notebooklm-python-client
description: Use the notebooklm Python client directly (bypassing the MCP server) to create notebooks, add sources, generate artifacts (audio, video, reports, slide decks, mind maps, flashcards, quizzes, data tables), and download results. Recommended for headless VPS environments where MCP server auth is unreliable. Covers installation, authentication, complete workflow, method names, polling, and error handling.
triggers:
  - notebooklm python client
  - notebooklm-py
  - notebooklm direct client
  - bypass mcp notebooklm
  - notebooklm without mcp
  - notebooklm script
  - notebooklm automation
  - notebooklm generate podcast
  - notebooklm generate audio
  - notebooklm generate report
  - notebooklm generate slides
---

# NotebookLM Python Client Skill

Use the `notebooklm` Python package directly to interact with NotebookLM — no MCP server required.

## When to Use Python Client vs MCP Server

| Scenario | Recommendation |
|----------|---------------|
| Headless VPS / no display | **Python client** — avoids MCP auth issues |
| Interactive chat via Telegram | MCP server — convenient tool calls |
| Automated scripts / batch jobs | **Python client** — full control, no server needed |
| Auth keeps expiring | **Python client** — direct cookie management |
| Quick one-off tasks | MCP server — simpler if already connected |
| Need artifact downloads | **Python client** — direct file output |

**Rule of thumb**: If you're on a headless server or the MCP server auth is flaky, use the Python client. It talks directly to the same Google APIs without the MCP middleware.

## Installation

```bash
pip install notebooklm
```

Or in the Hermes Agent venv:

```bash
uv pip install --python /usr/local/lib/hermes-agent/venv/bin/python3 notebooklm
```

## Authentication

The Python client supports two authentication methods:

### Method 1: `from_storage()` (Recommended)

Reads cookies from a Playwright-format `storage_state.json` file. This is the same file the MCP server uses.

```python
from notebooklm.client import NotebookLMClient

# Default path: ~/.notebooklm/profiles/default/storage_state.json
client = await NotebookLMClient.from_storage()

# Or specify a custom path
client = await NotebookLMClient.from_storage(
    storage_path="/root/.notebooklm/profiles/default/storage_state.json"
)
```

**Storage file format** (Playwright-style):
```json
{
  "cookies": [
    {
      "name": "SID",
      "value": "...",
      "domain": ".google.com",
      "path": "/",
      "secure": true,
      "httpOnly": false
    }
  ],
  "origins": []
}
```

> **CRITICAL**: The file MUST be `{"cookies": [...]}` — a flat dict `{name: value}` will fail validation.

### Method 2: `from_cookies()`

Pass cookies directly as a dict:

```python
client = await NotebookLMClient.from_cookies({
    "SID": "your-sid-cookie",
    "__Secure-1PSIDTS": "your-psidts-cookie",
    "HSID": "your-hsid-cookie",
    "SSID": "your-ssid-cookie",
})
```

### Getting Fresh Cookies

If auth fails, extract fresh cookies from Chrome:

```bash
pip install browser_cookie3
```

```python
import browser_cookie3, json
from pathlib import Path

COOKIE_DB = '/root/.notebooklm/profiles/default/browser_profile/Default/Cookies'
STORAGE_PATH = '/root/.notebooklm/profiles/default/storage_state.json'

domains = [
    '.google.com', 'accounts.google.com', 'notebooklm.google.com',
    'mail.google.com', 'drive.google.com', 'www.google.com',
]

all_cookies = []
for domain in domains:
    try:
        cj = browser_cookie3.chrome(cookie_file=COOKIE_DB, domain_name=domain)
        for c in cj:
            all_cookies.append({
                'name': c.name, 'value': c.value, 'domain': c.domain,
                'path': '/', 'secure': True, 'httpOnly': False
            })
    except Exception:
        pass

# Deduplicate
seen, unique = set(), []
for c in all_cookies:
    key = (c['name'], c['domain'])
    if key not in seen and c['value']:
        seen.add(key)
        unique.append(c)

Path(STORAGE_PATH).parent.mkdir(parents=True, exist_ok=True)
with open(STORAGE_PATH, 'w') as f:
    json.dump({'cookies': unique, 'origins': []}, f, indent=2)

print(f"Saved {len(unique)} cookies")
```

## Complete Workflow

### Quickstart Script

See [`scripts/notebooklm_quickstart.py`](./scripts/notebooklm_quickstart.py) for a complete working example that:
1. Connects to NotebookLM
2. Creates a notebook
3. Adds URL sources
4. Waits for processing
5. Generates all artifact types
6. Polls for completion
7. Downloads everything

### Step-by-Step

```python
import asyncio
from notebooklm.client import NotebookLMClient
from notebooklm.types import AudioFormat

async def main():
    # 1. Connect
    async with await NotebookLMClient.from_storage() as client:
        print(f"Connected: {client.is_connected}")  # property, not method!

        # 2. List existing notebooks
        notebooks = await client.notebooks.list()
        for nb in notebooks:
            print(f"  {nb.id}: {nb.title}")

        # 3. Create a new notebook
        nb = await client.notebooks.create("My Research Topic")
        print(f"Created: {nb.id} — {nb.title}")

        # 4. Add sources
        await client.sources.add_url(nb.id, "https://example.com/article1")
        await client.sources.add_url(nb.id, "https://example.com/article2")

        # 5. Wait for sources to be processed
        await client.sources.wait_until_ready(nb.id)

        # 6. Generate artifacts (all async — returns immediately with task_id)
        audio_task = await client.artifacts.generate_audio(
            nb.id, audio_format=AudioFormat.DEEP_DIVE
        )
        video_task = await client.artifacts.generate_video(nb.id)
        report_task = await client.artifacts.generate_report(nb.id)
        slides_task = await client.artifacts.generate_slide_deck(nb.id)
        mindmap_task = await client.artifacts.generate_mind_map(nb.id)
        flashcards_task = await client.artifacts.generate_flashcards(nb.id)
        quiz_task = await client.artifacts.generate_quiz(nb.id)
        datatable_task = await client.artifacts.generate_data_table(nb.id)

        # 7. Poll for completion
        tasks = {
            'audio': audio_task.task_id,
            'video': video_task.task_id,
            'report': report_task.task_id,
            'slides': slides_task.task_id,
        }
        for name, task_id in tasks.items():
            while True:
                status = await client.artifacts.poll_status(nb.id, task_id)
                if status.status == 3:    # done
                    print(f"✓ {name} ready")
                    break
                elif status.status == 2:  # failed
                    print(f"✗ {name} failed: {status.error}")
                    break
                await asyncio.sleep(30)

        # 8. Download artifacts
        await client.artifacts.download_audio(nb.id, '/tmp/audio.mp3')
        await client.artifacts.download_video(nb.id, '/tmp/video.mp4')
        await client.artifacts.download_report(nb.id, '/tmp/report.md')
        await client.artifacts.download_slide_deck(nb.id, '/tmp/slides.pdf')
        await client.artifacts.download_mind_map(nb.id, '/tmp/mindmap.json')
        await client.artifacts.download_flashcards(nb.id, '/tmp/flashcards.json')
        await client.artifacts.download_quiz(nb.id, '/tmp/quiz.json')
        await client.artifacts.download_data_table(nb.id, '/tmp/data.csv')

asyncio.run(main())
```

## API Reference

### Client

| Method | Description |
|--------|-------------|
| `NotebookLMClient.from_storage(path=None)` | Create client from storage_state.json |
| `NotebookLMClient.from_cookies(cookies_dict)` | Create client from cookie dict |
| `client.is_connected` | Property (not method!) — check connection |
| `async with client:` | Context manager for auto-cleanup |

### Notebooks

| Method | Description |
|--------|-------------|
| `client.notebooks.list()` | List all notebooks |
| `client.notebooks.create(title)` | Create a new notebook |
| `client.notebooks.get(notebook_id)` | Get notebook details |
| `client.notebooks.delete(notebook_id)` | Delete a notebook |
| `client.notebooks.rename(notebook_id, new_title)` | Rename a notebook |

### Sources

| Method | Description |
|--------|-------------|
| `client.sources.add_url(notebook_id, url)` | Add a URL source |
| `client.sources.add_text(notebook_id, text, title)` | Add pasted text |
| `client.sources.list(notebook_id)` | List sources in a notebook |
| `client.sources.delete(notebook_id, source_id)` | Remove a source |
| `client.sources.wait_until_ready(notebook_id)` | Block until all sources processed |

### Artifacts (Generation)

| Method | Returns | Description |
|--------|---------|-------------|
| `client.artifacts.generate_audio(nb_id, audio_format=AudioFormat.DEEP_DIVE)` | `task_id` | Generate Audio Overview (podcast) |
| `client.artifacts.generate_video(nb_id)` | `task_id` | Generate Video Overview |
| `client.artifacts.generate_report(nb_id)` | `task_id` | Generate text report |
| `client.artifacts.generate_slide_deck(nb_id)` | `task_id` | Generate slide deck (PDF) |
| `client.artifacts.generate_mind_map(nb_id)` | `task_id` | Generate mind map (JSON) |
| `client.artifacts.generate_flashcards(nb_id)` | `task_id` | Generate flashcards |
| `client.artifacts.generate_quiz(nb_id)` | `task_id` | Generate quiz |
| `client.artifacts.generate_data_table(nb_id)` | `task_id` | Generate data table (CSV) |

> **IMPORTANT**: `generate_audio()` requires `AudioFormat.DEEP_DIVE` enum, NOT a string like `'deep_dive'`. Using a string causes `AttributeError: 'str' object has no attribute 'value'`.

### Artifacts (Polling & Download)

| Method | Description |
|--------|-------------|
| `client.artifacts.poll_status(nb_id, task_id)` | Check status (1=progress, 2=failed, 3=done) |
| `client.artifacts.wait_for_completion(nb_id, task_id, timeout=120)` | Blocking wait |
| `client.artifacts.list(nb_id)` | List all artifacts |
| `client.artifacts.download_audio(nb_id, path)` | Download audio file |
| `client.artifacts.download_video(nb_id, path)` | Download video file |
| `client.artifacts.download_report(nb_id, path)` | Download report (markdown) |
| `client.artifacts.download_slide_deck(nb_id, path)` | Download slides (PDF) |
| `client.artifacts.download_mind_map(nb_id, path)` | Download mind map (JSON) |
| `client.artifacts.download_flashcards(nb_id, path)` | Download flashcards (JSON) |
| `client.artifacts.download_quiz(nb_id, path)` | Download quiz (JSON) |
| `client.artifacts.download_data_table(nb_id, path)` | Download data table (CSV) |

## Artifact Types

| Type | Output Format | Async | Typical Time |
|------|--------------|-------|-------------|
| `audio` | MP3 | Yes | 2-5 min |
| `video` | MP4 | Yes | 3-8 min |
| `report` | Markdown | Yes | 1-3 min |
| `slide_deck` | PDF | Yes | 2-5 min |
| `mind_map` | JSON | Yes | 1-2 min |
| `flashcards` | JSON | Yes | 1-2 min |
| `quiz` | JSON | Yes | 1-2 min |
| `data_table` | CSV | Yes | 1-2 min |

## Polling Pattern

All artifact generation is async. You MUST poll before downloading:

```python
# Generate (returns immediately)
result = await client.artifacts.generate_audio(nb.id, audio_format=AudioFormat.DEEP_DIVE)
task_id = result.task_id

# Poll until done
while True:
    status = await client.artifacts.poll_status(nb.id, task_id)
    if status.status == 3:      # done — safe to download
        break
    elif status.status == 2:    # failed
        print(f"Error: {status.error}")
        break
    elif status.status == 1:    # in progress
        await asyncio.sleep(30)  # wait 30s between checks

# Now download
await client.artifacts.download_audio(nb.id, '/tmp/output.mp3')
```

Or use the blocking convenience method:

```python
await client.artifacts.wait_for_completion(nb.id, task_id, timeout=300)
await client.artifacts.download_audio(nb.id, '/tmp/output.mp3')
```

## MCP Tool Names vs Python Client Method Names

| MCP Tool Name | Python Client Method | Notes |
|---------------|---------------------|-------|
| `notebook_list` | `client.notebooks.list()` | Returns list of notebook objects |
| `notebook_create` | `client.notebooks.create(title)` | Returns notebook object with `.id` |
| `source_add` (url) | `client.sources.add_url(nb_id, url)` | Must pass notebook_id first |
| `source_add` (text) | `client.sources.add_text(nb_id, text, title)` | Requires title parameter |
| `studio_create` (audio) | `client.artifacts.generate_audio(nb_id, audio_format=AudioFormat.DEEP_DIVE)` | Use enum, not string |
| `studio_create` (video) | `client.artifacts.generate_video(nb_id)` | |
| `studio_create` (report) | `client.artifacts.generate_report(nb_id)` | |
| `studio_create` (slide_deck) | `client.artifacts.generate_slide_deck(nb_id)` | |
| `studio_create` (mind_map) | `client.artifacts.generate_mind_map(nb_id)` | |
| `studio_create` (flashcards) | `client.artifacts.generate_flashcards(nb_id)` | |
| `studio_create` (quiz) | `client.artifacts.generate_quiz(nb_id)` | |
| `studio_create` (data_table) | `client.artifacts.generate_data_table(nb_id)` | |
| `studio_status` | `client.artifacts.poll_status(nb_id, task_id)` | Or `wait_for_completion()` |
| `download_artifact` | `client.artifacts.download_<type>(nb_id, path)` | Separate method per type |
| `refresh_auth` | Re-create client with fresh cookies | No direct equivalent |

## Error Handling

```python
import asyncio
from notebooklm.client import NotebookLMClient
from notebooklm.exceptions import (
    AuthenticationError,
    NotebookNotFoundError,
    ArtifactError,
    ArtifactParseError,
)

async def main():
    try:
        async with await NotebookLMClient.from_storage() as client:
            nb = await client.notebooks.create("Test")
            await client.sources.add_url(nb.id, "https://example.com")
            await client.sources.wait_until_ready(nb.id)

            task = await client.artifacts.generate_audio(
                nb.id, audio_format=AudioFormat.DEEP_DIVE
            )
            await client.artifacts.wait_for_completion(nb.id, task.task_id, timeout=300)
            await client.artifacts.download_audio(nb.id, '/tmp/audio.mp3')

    except AuthenticationError:
        print("Auth failed — extract fresh cookies from Chrome")
    except NotebookNotFoundError:
        print("Notebook not found — check the ID")
    except ArtifactParseError:
        print("Artifact not ready — wait longer before downloading")
    except ArtifactError as e:
        print(f"Artifact generation failed: {e}")
    except asyncio.TimeoutError:
        print("Operation timed out — try increasing timeout")

asyncio.run(main())
```

## Common Pitfalls

1. **Using string instead of enum for audio format**
   - ❌ `audio_format='deep_dive'`
   - ✅ `audio_format=AudioFormat.DEEP_DIVE`

2. **Calling `is_connected()` as a method**
   - ❌ `client.is_connected()` — raises `TypeError`
   - ✅ `client.is_connected` — it's a property

3. **Downloading before artifact is ready**
   - Always poll `status == 3` (done) before downloading
   - Downloading too early raises `ArtifactParseError`

4. **Wrong cookie format**
   - ❌ `{"SID": "value", "HSID": "value"}` (flat dict)
   - ✅ `{"cookies": [{"name": "SID", "value": "value", "domain": ".google.com", ...}]}`

5. **Not waiting for sources to process**
   - After `add_url()`, call `wait_until_ready()` before generating artifacts

6. **Stale cookies**
   - Google sessions expire quickly. If auth fails, re-extract cookies from Chrome with `browser_cookie3`

## File Paths Reference

| File | Path |
|------|------|
| Chrome cookies DB | `/root/.notebooklm/profiles/default/browser_profile/Default/Cookies` |
| Storage state | `/root/.notebooklm/profiles/default/storage_state.json` |
| MCP state (if also used) | `/root/.local/share/notebooklm-mcp/browser_state/state.json` |
| Quickstart script | `/root/notebooklm-mcp/skills/python-client/scripts/notebooklm_quickstart.py` |
| This skill | `/root/notebooklm-mcp/skills/python-client/SKILL.md` |
