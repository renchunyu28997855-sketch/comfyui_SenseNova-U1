# SenseNova U1 LoRA Loader 修改总结

## 概述

本次修改包含两部分：
1. **LoRA 加载功能** — 在 `SenseNovaU1LocalLoader` 后串接 LoRA 加载器
2. **兼容性问题修复** — 解决 `check_model_inputs` 与 SenseNova 自定义模型参数的冲突

---

## 一、LoRA 加载功能

### 架构

```
SenseNovaU1LocalLoader → SenseNovaU1LocalLoraLoader → TextToImage / ImageEdit / Interleave
```

`SenseNovaU1LocalLoraLoader` 接收 Loader 输出的 `u1_model`，加载 LoRA 并修改模型权重后输出，仍为 `LOCAL_MODEL_TYPE`，供下游 generation 节点使用。

### 修改文件

#### `apps/comfyui/local_pipeline.py`

- 第 89 行附近：定义 `SENSENOVA_U1_LORA = "SENSENOVA_U1_LORA"` 常量（作为类型标识）
- `SenseNovaU1LocalModel` 类：
  - `info` 属性增加 `lora_path` 字段
  - 新增 `set_lora(lora_path)` 方法
- 新增 `apply_lora_to_model(model, lora_path)` 函数（第 590-609 行附近）：
  - 调用 `sensenova_u1.utils.lora.load_and_merge_lora_weight_from_safetensors` 加载 LoRA 到模型
  - 检查 LoRA 文件存在性
  - 记录加载日志

#### `apps/comfyui/nodes.py`

- 导入 `apply_lora_to_model` 函数
- 新增 `SenseNovaU1LocalLoraLoader` 类（第 473-495 行）：
  - 输入：`u1_model: SENSENOVA_U1_LOCAL_MODEL`，`lora_path: STRING`
  - 输出：`u1_model: LOCAL_MODEL_TYPE`，`model_info_json: STRING`
  - 逻辑：LoRA path 非空时调用 `apply_lora_to_model` 并记录到 model info
- `NODE_CLASS_MAPPINGS` 增加 `"SenseNovaU1LocalLoraLoader": SenseNovaU1LocalLoraLoader`
- `NODE_DISPLAY_NAME_MAPPINGS` 增加 `"SenseNova U1 Local LoRA Loader"`

---

## 二、`check_model_inputs` 兼容性问题修复

### 问题症状

```
TypeError: check_model_inputs.<locals>.wrapped_fn() got an unexpected keyword argument 'input_ids'
```

此错误与 LoRA 无关——在没有 LoRA 节点的情况下也会出现。

### 根因

`SenseNovaU1LocalTextToImage` 等节点调用 `t2i_generate` 时，会经过：
`modeling_neo_chat.py:460` → `_t2i_prefix_forward` → `self.language_model.model.forward()`

`self.language_model.model` 是 `Qwen3Model`，其 `forward` 方法上有 `@check_model_inputs` 装饰器（第 1047 行）。该装饰器与 SenseNova 自定义的 `indexes`、`image_gen_indicators` 等参数冲突，导致参数处理异常。

### 修复文件

#### `src/sensenova_u1/models/neo_unify/modeling_qwen3.py`

- **第 27 行**：删除无用的 `check_model_inputs` 导入
  ```python
  # 修改前
  from transformers.utils.generic import check_model_inputs
  # 修改后
  from transformers.utils.generic import can_return_tuple
  ```
- **第 1047 行**：移除 `@check_model_inputs` 装饰器
  ```python
  # 修改前
  @check_model_inputs
  @auto_docstring
  def forward(
  # 修改后
  @auto_docstring
  def forward(
  ```

此修改移除装饰器对 hidden_states/attention 输出的捕获能力，但不影响模型的正常推理功能。

---

## 三、ComfyUI-Lora-Manager 相关改动（未生效）

为解决兼容性问题，尝试了以下 ComfyUI-Lora-Manager 侧的修改（供参考，最终方案为修改 SenseNova 源码）：

#### `py/metadata_collector/metadata_hook.py`
- `install()` 方法改为直接 return，不安装任何 hook
- `_install_sync_hooks` / `_install_async_hooks` 改为空操作

#### `py/metadata_collector/__init__.py`
- `init()` 中注释掉了 `MetadataHook.install()` 调用

这些改动最终被绕过（通过修改 modeling_qwen3.py 解决根因），保留此处作为记录。

---

## 文件清单

| 文件 | 改动类型 | 说明 |
|------|---------|------|
| `apps/comfyui/local_pipeline.py` | 修改 | LoRA 工具函数、`SenseNovaU1LocalModel` 增加 lora 支持 |
| `apps/comfyui/nodes.py` | 修改 | 新增 `SenseNovaU1LocalLoraLoader` 节点 |
| `src/sensenova_u1/models/neo_unify/modeling_qwen3.py` | 修改 | 移除 `@check_model_inputs` 装饰器，修复兼容性 |
| `apps/comfyui/docs/superpowers/specs/2026-05-07-lora-loader-design.md` | 新增 | 设计文档 |

---

## 依赖

- `sensenova_u1.utils.lora.load_and_merge_lora_weight_from_safetensors`