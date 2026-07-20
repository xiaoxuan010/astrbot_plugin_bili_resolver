# Source-Aware Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add source-aware conditional custom templates while preserving all existing `${变量}` templates.

**Architecture:** Classify the original event before URL normalization and pass the immutable source string through the existing resolver calls. Render a deliberately small, line-oriented conditional language before the existing placeholder and image-component renderer.

**Tech Stack:** Python 3.10+, AstrBot message events/components, pytest, JSON configuration.

## Global Constraints

- Preserve `${标题}` and every existing placeholder.
- Support only `{% if source == "value" %}`, `{% elif source == "value" %}`, `{% else %}`, and `{% endif %}` on standalone lines.
- Valid source values are exactly `card`, `url`, `bvid`, and `text`.
- Pass source through function arguments; never store per-message source in module globals.
- Invalid conditional syntax logs the error and falls back to the original video format.

---

### Task 1: Message source classification and propagation

**Files:**
- Create: `tests/test_message_source.py`
- Modify: `main.py`
- Modify: `analysis_bilibili.py`

**Interfaces:**
- Produces: `_classify_message_source(text: str, card_url: str = "") -> str`
- Produces: `bili_keyword(..., source: str = "text")`
- Consumes: `video_detail(..., source=source)`

- [ ] **Step 1: Write a failing source-classifier test**

```python
from astrbot_plugin_bili_resolver import main

def test_source_classifier_api_exists():
    assert hasattr(main, "_classify_message_source")
```

- [ ] **Step 2: Run the test and verify RED**

Run from `D:\Project\2026\AstrBot`:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; .\.venv\Scripts\python.exe -m pytest data\plugins\astrbot_plugin_bili_resolver\tests\test_message_source.py -q
```

Expected: one assertion failure because `_classify_message_source` is absent.

- [ ] **Step 3: Implement the classifier API**

```python
BARE_BVID_PATTERN = re.compile(r"BV[A-Za-z0-9]{10}", re.I)
BILI_URL_SOURCE_PATTERN = re.compile(
    r"(?:b23\.tv|bili(?:22|23|33|2233)\.cn|(?:[\w-]+\.)?bilibili\.com)(?:[/:?]|$)",
    re.I,
)

def _classify_message_source(text: str, card_url: str = "") -> str:
    if card_url:
        return "card"
    if BILI_URL_SOURCE_PATTERN.search(text):
        return "url"
    if BARE_BVID_PATTERN.fullmatch(text.strip()):
        return "bvid"
    return "text"
```

- [ ] **Step 4: Add behavior tests and verify GREEN**

Add separate assertions for card, full URL, short URL, bare BV, descriptive BV text, and URL containing BV. Run the Task 1 command and expect all tests to pass.

- [ ] **Step 5: Add propagation tests and implementation**

Use signature inspection to require `source` on `bili_keyword`, then change:

```python
async def bili_keyword(group_id, text, session, source: str = "text"):
    ...
    msg, vurl = await video_detail(..., source=source)
```

In `on_message`, compute `source = _classify_message_source(original_text, json_url)` before replacing or expanding `text`, then call `bili_keyword(..., source=source)`. Pass `source="text"` from the search command because its original trigger is command text.

- [ ] **Step 6: Run Task 1 tests and commit**

Expected: all source tests pass.

```powershell
git add main.py analysis_bilibili.py tests/test_message_source.py
git commit -m "feat: 识别并传递 B 站消息来源"
```

### Task 2: Restricted conditional rendering and fallback

**Files:**
- Create: `tests/test_conditional_template.py`
- Modify: `analysis_bilibili.py`
- Modify: `_conf_schema.json`
- Modify: `README.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Produces: `TemplateSyntaxError(ValueError)`
- Produces: `_render_conditionals(template: str, source: str) -> str`
- Changes: `_apply_template(template, data, cover_url, source="text") -> list`

- [ ] **Step 1: Write a failing renderer API test**

```python
from astrbot_plugin_bili_resolver import analysis_bilibili

def test_conditional_renderer_api_exists():
    assert hasattr(analysis_bilibili, "_render_conditionals")
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; .\.venv\Scripts\python.exe -m pytest data\plugins\astrbot_plugin_bili_resolver\tests\test_conditional_template.py -q
```

Expected: one assertion failure because `_render_conditionals` is absent.

- [ ] **Step 3: Implement the line-oriented parser**

Implement a state machine that recognizes standalone control lines, selects one branch, rejects nested blocks, unknown source values, malformed ordering, duplicate `else`, and missing `endif`, and returns templates without control tags unchanged byte-for-byte.

- [ ] **Step 4: Add parser behavior tests and verify GREEN**

Test every source branch, legacy templates, two sequential conditional blocks, malformed tags, nested blocks, and missing `endif`. Expected: all renderer tests pass.

- [ ] **Step 5: Integrate placeholder/image rendering and fallback**

Call `_render_conditionals` at the start of `_apply_template`. Pass `kwargs.get("source", "text")` from `video_detail`. Catch `TemplateSyntaxError` around custom rendering, log the exact error, and continue into the existing original-format code path.

- [ ] **Step 6: Add integration tests**

Verify `${封面}` in an unselected branch produces no cover URL, a selected cover branch produces an image element, and variable substitution occurs after branch selection.

- [ ] **Step 7: Update configuration and documentation**

Document the four source values, standalone control-line rule, recommended template, syntax-error fallback, and backward compatibility in `_conf_schema.json`, `README.md`, and `CHANGELOG.md`.

- [ ] **Step 8: Run the full verification suite and commit**

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; .\.venv\Scripts\python.exe -m pytest data\plugins\astrbot_plugin_bili_resolver\tests -q
.\.venv\Scripts\python.exe -m compileall -q data\plugins\astrbot_plugin_bili_resolver
git diff --check
```

Expected: all tests pass, compilation exits 0, and `git diff --check` exits 0.

```powershell
git add analysis_bilibili.py _conf_schema.json README.md CHANGELOG.md tests/test_conditional_template.py docs/superpowers/plans/2026-07-21-source-aware-template.md
git commit -m "feat: 支持来源感知条件模板"
```
