# ComfyUI Nodes Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply 4 refactors to ComfyUI custom nodes: remove think_end hardcode, merge LoRA loader, use PATH type for directories, use relative src path.

**Architecture:** Changes are confined to 3 files: `modeling_neo_chat.py` (think fix), `local_pipeline.py` (default path), `nodes.py` (node refactor). No new files created.

**Tech Stack:** Python, ComfyUI custom nodes, transformers

---

## File Map

| File | Responsibility |
|------|---------------|
| `apps/comfyui/src/sensenova_u1/models/neo_unify/modeling_neo_chat.py` | Think mode — remove hardcoded token and duplicate init |
| `apps/comfyui/local_pipeline.py` | `default_source_path()` — use relative path to plugin `src/` |
| `apps/comfyui/nodes.py` | All node INPUT_TYPES changes, delete LoRA loader, update MAPPINGS |

---

## Task 1: Remove hardcoded `think_end_token_id` in think mode

**Files:**
- Modify: `apps/comfyui/src/sensenova_u1/models/neo_unify/modeling_neo_chat.py:525-532`

**Context (lines 510-534):**
```python
        prefix_outputs,
        past_key_values,
        t_idx,
        IMG_START_TOKEN,
        max_think_tokens=1024,
    ):
        template = get_conv_template(self.template)
        eos_token_id = tokenizer.convert_tokens_to_ids(template.sep.strip())
        think_end_token_id = tokenizer.convert_tokens_to_ids('
</think>

')
        think_token_ids = []
        next_token = torch.argmax(prefix_outputs.logits[:, -1, :], dim=-1)

        from transformers.utils import logging as hf_logging
        logger = hf_logging.get_logger(__name__)

        # Hardcode think_end token ID since tokenizer may not recognize ''
        # ''
        think_end_token_id = 151668

        template = get_conv_template(self.template)
        eos_token_id = tokenizer.convert_tokens_to_ids(template.sep.strip())
        think_token_ids = []
        next_token = torch.argmax(prefix_outputs.logits[:, -1, :], dim=-1)

        logger.info(f"[think] start: eos={eos_token_id}, think_end={think_end_token_id}, max={max_think_tokens}")
```

- [ ] **Step 1: Remove hardcoded override and duplicate init**

Delete lines 525-532 (the comment, hardcoded assignment, and the 4 duplicate lines: `template = ...`, `eos_token_id = ...`, `think_token_ids = []`, `next_token = ...`).

After deletion, the code should be:

```python
        template = get_conv_template(self.template)
        eos_token_id = tokenizer.convert_tokens_to_ids(template.sep.strip())
        think_end_token_id = tokenizer.convert_tokens_to_ids('
</think>

')
        think_token_ids = []
        next_token = torch.argmax(prefix_outputs.logits[:, -1, :], dim=-1)

        from transformers.utils import logging as hf_logging
        logger = hf_logging.get_logger(__name__)

        logger.info(f"[think] start: eos={eos_token_id}, think_end={think_end_token_id}, max={max_think_tokens}")
```

Run: verify the file compiles — `python -m py_compile apps/comfyui/src/sensenova_u1/models/neo_unify/modeling_neo_chat.py`

---

## Task 2: Update `default_source_path()` to use relative path

**Files:**
- Modify: `apps/comfyui/local_pipeline.py:429-436`

**Current code:**
```python
def default_source_path() -> str:
    env_path = os.environ.get("SENSENOVA_U1_SRC", "")
    if env_path:
        return env_path
    repo_src = Path(__file__).resolve().parents[2] / "src"
    if repo_src.is_dir():
        return str(repo_src)
    return DEFAULT_SOURCE_PATH
```

- [ ] **Step 1: Replace `default_source_path()` body**

Replace `repo_src = Path(__file__).resolve().parents[2] / "src"` with relative path from the plugin directory:

```python
def default_source_path() -> str:
    env_path = os.environ.get("SENSENOVA_U1_SRC", "")
    if env_path:
        return env_path
    # Use src/ inside the plugin directory (relative path from local_pipeline.py)
    plugin_src = Path(__file__).resolve().parent / "src"
    if plugin_src.is_dir():
        return str(plugin_src)
    return ""
```

Note: `DEFAULT_SOURCE_PATH` constant at line 94 is no longer referenced; it can stay for backward compat but is not used.

Run: `python -c "from apps.comfyui.local_pipeline import default_source_path; print(default_source_path())"`

---

## Task 3: Change `sensenova_u1_src` to hidden field

**Files:**
- Modify: `apps/comfyui/nodes.py:379-385`

**Updated approach (per user clarification):**
- `sensenova_u1_src` is now `hidden=True` — not shown in UI
- The `load()` method uses `default_source_path()` directly instead of the parameter value

**Steps taken:**
1. Changed `sensenova_u1_src` type to `"STRING"` with `"hidden": True`
2. In `load()`, replaced `sensenova_u1_src=sensenova_u1_src` with `sensenova_u1_src=default_source_path()` so the hidden field value is ignored and the code always uses the computed plugin-internal `src` path

Result: `sensenova_u1_src` hidden in UI; load() uses `default_source_path()` pointing to `apps/comfyui/src`

---

## Task 4: Add `lora_path` field to `SenseNovaU1LocalLoader` (dropdown) + model_path dropdown

**Files:**
- Modify: `apps/comfyui/nodes.py:368-399` (INPUT_TYPES), `nodes.py:425-462` (load method and IS_CHANGED)

**Updated approach (per user clarification):**
- `model_path`: Changed from STRING to dropdown using `folder_paths.get_filename_list("checkpoints")`
- `lora_path`: Changed from `["PATH"]` to dropdown using `folder_paths.get_filename_list("loras")` filtered for `.safetensors`
- LoRA path resolution: Added `folder_paths.get_full_path("loras", lora_path)` to resolve dropdown filename to full path

**Steps taken:**
1. Added module-level `CHECKPOINT_OPTIONS` and `LORA_OPTIONS` from `folder_paths` (with `try/except` fallback)
2. `model_path` INPUT_TYPES changed to `(CHECKPOINT_OPTIONS, {"default": ...})` — dropdown from `models/checkpoints`
3. `lora_path` INPUT_TYPES changed to `(LORA_OPTIONS, {"default": ""})` — dropdown from `models/loras` filtered `.safetensors`
4. `load()` method: added path resolution for `lora_path` via `folder_paths.get_full_path("loras", lora_path)` before calling `apply_lora_to_model`

---

## Task 5: Delete `SenseNovaU1LocalLoraLoader` node

**Files:**
- Modify: `apps/comfyui/nodes.py` — remove class, remove from MAPPINGS

- [ ] **Step 1: Delete `SenseNovaU1LocalLoraLoader` class**

Delete the class definition (lines 465-487):
```python
class SenseNovaU1LocalLoraLoader:
    CATEGORY = f"{CATEGORY}/Local"
    RETURN_TYPES = (LOCAL_MODEL_TYPE, "STRING")
    RETURN_NAMES = ("u1_model", "model_info_json")
    FUNCTION = "load"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "u1_model": (LOCAL_MODEL_TYPE,),
                "lora_path": (
                    "STRING",
                    {"default": "", "tooltip": "Path to LoRA safetensors file."},
                ),
            }
        }

    def load(self, u1_model: SenseNovaU1LocalModel, lora_path: str):
        if lora_path.strip():
            apply_lora_to_model(u1_model.model, lora_path)
            u1_model.set_lora(lora_path)
        return u1_model, json.dumps(u1_model.info, ensure_ascii=False)
```

- [ ] **Step 2: Remove from `NODE_CLASS_MAPPINGS`**

Remove line:
```python
    "SenseNovaU1LocalLoraLoader": SenseNovaU1LocalLoraLoader,
```

- [ ] **Step 3: Remove from `NODE_DISPLAY_NAME_MAPPINGS`**

Remove line:
```python
    "SenseNovaU1LocalLoraLoader": "SenseNova U1 Local LoRA Loader",
```

- [ ] **Step 4: Remove `apply_lora_to_model` import from nodes.py if no longer used**

Check if `apply_lora_to_model` is still imported (line 36/70) and used elsewhere in nodes.py. It is used in `SenseNovaU1LocalLoader.load()` after Task 4, so keep the import.

Run: `python -c "from apps.comfyui.nodes import NODE_CLASS_MAPPINGS; print(len(NODE_CLASS_MAPPINGS))"` → should print `10`

---

## Task 6: Verify and test

- [ ] **Step 1: Verify node count**

Run: `python -c "from apps.comfyui.nodes import NODE_CLASS_MAPPINGS; print('Nodes:', len(NODE_CLASS_MAPPINGS))"`
Expected: `10` nodes, no `SenseNovaU1LocalLoraLoader`

- [ ] **Step 2: Verify `sensenova_u1_src` is hidden**

Run: `python -c "from apps.comfyui.nodes import SenseNovaU1LocalLoader; cfg = SenseNovaU1LocalLoader.INPUT_TYPES()['required']['sensenova_u1_src']; print('hidden:', cfg[1].get('hidden'))"`
Expected: `True`

- [ ] **Step 3: Verify `model_path` is dropdown list**

Run: `python -c "from apps.comfyui.nodes import SenseNovaU1LocalLoader; cfg = SenseNovaU1LocalLoader.INPUT_TYPES()['required']['model_path']; print('is list:', isinstance(cfg[0], list))"`
Expected: `True`

- [ ] **Step 4: Verify `lora_path` is dropdown list**

Run: `python -c "from apps.comfyui.nodes import SenseNovaU1LocalLoader; cfg = SenseNovaU1LocalLoader.INPUT_TYPES()['required']['lora_path']; print('is list:', isinstance(cfg[0], list))"`
Expected: `True`

- [ ] **Step 5: Verify `load()` uses `default_source_path()`**

Run: `grep -n "sensenova_u1_src=default_source_path" apps/comfyui/nodes.py`
Expected: line found in `load()` method

- [ ] **Step 6: Verify `default_source_path` returns plugin src**

Run: `python -c "from apps.comfyui.local_pipeline import default_source_path; print(default_source_path())"`
Expected: path containing `apps/comfyui/src`

---

## Implementation Order

1. Task 1 — fix `modeling_neo_chat.py`
2. Task 2 — fix `local_pipeline.py`
3. Task 3 — PATH type for `sensenova_u1_src`
4. Task 4 — add `lora_path` to Loader
5. Task 5 — delete LoRA Loader node
6. Task 6 — verify

## Spec Coverage Check

| Spec Section | Task |
|-------------|-------|
| Change 1: Remove hardcode | Task 1 |
| Change 2: Merge LoRA Loader | Tasks 4, 5 |
| Change 3: PATH type | Tasks 3, 4 |
| Change 4: Relative path | Task 2 |

All spec sections covered. No placeholder steps.
