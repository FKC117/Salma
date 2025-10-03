# Let's generate the requested markdown file with the full report inside docs/chat_sandbox_fixes.md

content = """# 🔎 Chat Sandbox & Rendering Debug Report

This document describes issues found in the chat + sandbox integration and provides targeted fixes.  
Covers image rendering, markdown escaping, and LLM code formatting/indentation problems.

---

## What’s breaking (and exactly where)

### 1) Images are generated but never actually shown in the chat
- The sandbox emits **special markers** for images:
  - `__SANDBOX_IMAGE_BASE64__...` (base64 inline)
  - `__SANDBOX_IMAGE_FILE__...` (file paths)
- `SandboxResultProcessor` parses these correctly.  
- But **chat rendering** differs across files:
  - Some paths wrap output in `<pre>` (escapes `<img>`).
  - Other paths use `<div style="white-space:pre-wrap">` (lets HTML render).  
- `_process_execution_output` only replaces **base64 markers**; file-path markers are left raw.

**Result:**  
Base64 images sometimes render, file-path ones don’t. If wrapped in `<pre>`, nothing renders at all.

---

### 2) You sometimes expect frontend to load images “via API”
- In one path, when a `sandbox_result_id` exists, you show “Images will be loaded via API.”  
- In another, you inline HTML via `_process_execution_output`.

**Result:**  
Inconsistent behavior. If frontend doesn’t actually fetch those images, charts never appear.

---

### 3) “Indentation errors” from LLM formatting/markdown
- LLM sometimes outputs inline like `` `python import …` `` or mixes headings/tables with code.  
- `CodeExtractionService` has heuristics to reject markdown/HTML, but one-liners still slip through.  
- Sandbox has auto-fixers for indentation, but malformed snippets still cause syntax errors.

**Result:**  
Indentation/syntax errors despite the auto-fixer.

---

## Quick, surgical fixes

### ✅ Images in chat
1. **Use `<div style="white-space:pre-wrap">` everywhere.**  
   Replace `<pre>` wrappers so `<img>` HTML can render.

2. **Support file-path markers in `_process_execution_output`.**  
   - Detect `__SANDBOX_IMAGE_FILE__...`.
   - Convert path → base64 → `<img>` inline.

3. **Remove “Images will be loaded via API” placeholders.**  
   Inline images directly until API fetch path is implemented.

---

### ✅ Reduce “indentation errors”
4. **Normalize extracted code.**  
   - Strip leading `python ` tokens.
   - Wrap snippets in triple backticks if missing:
     ```python
     ```python
     <code>
     ```
     ```

5. **Keep auto-fixer but feed it cleaner code.**  
   (You already run `_fix_indentation_advanced` in the executor.)

---

### ✅ Optional: pick one image flow
- **Inline base64 rendering**: fastest and works now.
- **Structured SandboxResult + frontend fetch**: keep for history, but don’t rely on it in chat yet.

---

## Tiny diffs you can apply

### A) In `chat_service.py`
```diff
- <pre class="mb-0">{self._process_execution_output(result['output'])}</pre>
+ <div class="mb-0" style="white-space:pre-wrap">
+   {self._process_execution_output(result['output'])}
+ </div>


