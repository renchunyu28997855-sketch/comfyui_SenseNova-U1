# ComfyUI Nodes Refactor Design

**Date:** 2026-05-07
**Status:** Draft

## Overview

对 `apps/comfyui` 中的 ComfyUI 自定义节点进行4项改进：
1. 移除 think mode 硬编码
2. 合并 LoRA Loader 到 Model Loader
3. 路径字段改为文件夹选择器
4. 使用相对路径作为默认 src 目录

---

## Change 1: Remove Hardcoded `think_end_token_id`

### File
`apps/comfyui/src/sensenova_u1/models/neo_unify/modeling_neo_chat.py`

### Changes
- **删除** 第525-527行的硬编码：
  ```python
  # Hardcode think_end token ID since tokenizer may not recognize ''
  # ''
  think_end_token_id = 151668
  ```
- **删除** 第529-532行重复的初始化代码（`template = ...`, `eos_token_id = ...`, `think_token_ids = []`, `next_token = ...`）
- 保留第518行 tokenizer 获取方式：
  ```python
  think_end_token_id = tokenizer.convert_tokens_to_ids('
</think>

')
  ```

### Why
第518行已经通过 tokenizer 获取正确的 `think_end_token_id`，第527行的硬编码覆盖会导致 tokenizer 无法识别该 token 时使用硬编码值，两种方式同时存在且后者覆盖前者是不一致的行为。

---

## Change 2: Merge LoRA Loader into Model Loader

### Files
- `apps/comfyui/nodes.py`
- `apps/comfyui/local_pipeline.py`

### Changes

#### 2.1 删除 `SenseNovaU1LocalLoraLoader` 节点
- 从 `NODE_CLASS_MAPPINGS` 中移除 `"SenseNovaU1LocalLoraLoader": SenseNovaU1LocalLoraLoader`
- 从 `NODE_DISPLAY_NAME_MAPPINGS` 中移除对应条目
- 删除 `SenseNovaU1LocalLoraLoader` 类定义（约第465-487行）

#### 2.2 在 `SenseNovaU1LocalLoader` 中新增 LoRA 字段

**INPUT_TYPES 新增字段：**
```python
"lora_path": (
    ["PATH"],
    {
        "default": "",
        "tooltip": "Path to LoRA safetensors file. Leave empty to skip.",
    },
),
```

**load() 方法更新：**
在模型加载完成后，检查 `lora_path` 是否非空：
```python
def load(self, model_path: str, ..., lora_path: str = ""):
    # ... existing model loading ...
    if lora_path.strip():
        apply_lora_to_model(model, lora_path)
        model.set_lora(lora_path)
    return model, json.dumps(model.info, ensure_ascii=False)
```

**IS_CHANGED 更新：**
在 cache key 中加入 `lora_path`。

#### 2.3 保留 `apply_lora_to_model` 和 `set_lora`
这两个函数已在 `local_pipeline.py` 中实现，无需修改。

---

## Change 3: Field Types for Directory/File Selection

### Files
- `apps/comfyui/nodes.py`

### Changes

#### 3.1 `sensenova_u1_src` — 隐藏字段

改为 `hidden=True`，不显示在 UI 中，代码直接指向插件内 `src` 目录：

```python
"sensenova_u1_src": (
    "STRING",
    {
        "default": "",  # 实际路径在 load() 中硬编码
        "hidden": True,
    },
),
```

#### 3.2 `model_path` — ComfyUI checkpoints 目录选择

使用 `folder_paths.get_filename_list("checkpoints")` 动态获取下拉选项：
```python
"model_path": (
    (list(folder_paths.get_filename_list("checkpoints")), {"default": "models/SenseNova-U1-8B-MoT"}),
    # 或者保持 STRING 类型让用户手动输入 HF model id
)
```

#### 3.3 `lora_path` — ComfyUI loras 目录，筛选 .safetensors

使用 `folder_paths.get_filename_list("loras")` 获取下拉选项，过滤 `.safetensors`：
```python
# 动态获取所有 lora 文件
_all_loras = folder_paths.get_filename_list("loras")
# 过滤只保留 .safetensors
_lora_options = [f for f in _all_loras if f.endswith(".safetensors")]

"lora_path": (
    (_lora_options, {"default": ""}),
    {"tooltip": "Select a LoRA file from models/loras."},
)
```

**注意:** 由于 `folder_paths` 依赖 ComfyUI 运行时环境，需要在 `INPUT_TYPES` 中使用懒加载模式避免模块导入错误。

---

## Change 4: Relative Path for Default `sensenova_u1_src`

### Files
- `apps/comfyui/local_pipeline.py`

### Changes

修改 `default_source_path()` 函数：
- 优先使用环境变量 `SENSENOVA_U1_SRC`
- 其次使用相对于插件目录的 `../../src`（即 `apps/comfyui/src`）
- 不再使用 `Path(__file__).resolve().parents[2] / "src"` 这种绝对路径方式

```python
def default_source_path() -> str:
    env_path = os.environ.get("SENSENOVA_U1_SRC", "")
    if env_path:
        return env_path
    # Use relative path from ComfyUI custom_nodes directory
    plugin_src = Path(__file__).resolve().parent / "src"
    if plugin_src.is_dir():
        return str(plugin_src)
    return ""
```

**注意:** `sensenova_u1_src` 的 `INPUT_TYPES` 默认值也需要更新为 `default_source_path()` 返回的相对路径 `../../src`。

### 文件结构确认
```
apps/comfyui/
├── src/                          # <-- 相对路径 ../../src 指向这里
│   └── sensenova_u1/
│       ├── models/
│       │   └── neo_unify/
│       │       └── modeling_neo_chat.py
│       └── ...
├── nodes.py
├── local_pipeline.py
└── ...
```

---

## Summary of `NODE_CLASS_MAPPINGS` Changes

| 操作 | 节点名 |
|------|--------|
| 保留 | SenseNovaChat |
| 保留 | SenseNovaImageGenerate |
| 保留 | SenseNovaPromptBuilder |
| 保留 | SenseNovaVisionURL |
| 保留 | SenseNovaVisionImage |
| 修改 | SenseNovaU1LocalLoader (新增 lora_path) |
| **删除** | **SenseNovaU1LocalLoraLoader** |
| 保留 | SenseNovaU1LocalTextToImage |
| 保留 | SenseNovaU1LocalImageEdit |
| 保留 | SenseNovaU1LocalInterleave |
| 保留 | SenseNovaInterleavePreview |

**节点总数变化:** 11 → 10

---

## Implementation Order

1. Change 1: 修复 `modeling_neo_chat.py`（删除硬编码和重复代码）
2. Change 4: 修改 `local_pipeline.py` 的 `default_source_path()`
3. Change 3: 将 `sensenova_u1_src` 改为 `["PATH"]` 类型
4. Change 2: 合并 LoRA Loader 到 Model Loader
5. 更新 `__init__.py`（如需要）
6. 测试验证

---

## Files to Modify

| File | Changes |
|------|---------|
| `apps/comfyui/src/sensenova_u1/models/neo_unify/modeling_neo_chat.py` | 删除硬编码和重复代码 |
| `apps/comfyui/local_pipeline.py` | 修改 `default_source_path()` |
| `apps/comfyui/nodes.py` | PATH 类型、合并 LoRA、删除节点 |
