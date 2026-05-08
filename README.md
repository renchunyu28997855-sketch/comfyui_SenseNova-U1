# SenseNova-U1 for ComfyUI

ComfyUI custom nodes for SenseNova-U1 API and local inference.

## Nodes

- `SenseNova Image Generate`: calls the U1-Fast image API.
- `SenseNova Chat`, `SenseNova Vision URL`, `SenseNova Vision Image`: utility API nodes.
- `SenseNova Prompt Builder`: rewrites raw ideas into image-generation prompts.
- `SenseNova U1 Local Loader`: loads a local or HuggingFace SenseNova-U1 checkpoint.
- `SenseNova U1 Local Text to Image`: runs local `t2i_generate`.
- `SenseNova U1 Local Image Edit`: runs local `it2i_generate`.
- `SenseNova U1 Local Interleave`: runs local `interleave_gen`.
- `SenseNova Interleave Preview`: renders ordered interleaved text / image results.

## Install

From the SenseNova-U1 repository:

```bash
python apps/comfyui/install.py --comfyui /path/to/ComfyUI
```

By default this creates:

```text
/path/to/ComfyUI/custom_nodes/ComfyUI-SenseNova-U1 -> /path/to/SenseNova-U1/apps/comfyui
```

Install the lightweight ComfyUI app dependencies in the Python environment used by ComfyUI:

```bash
python -m pip install -r apps/comfyui/requirements.txt
```

For local inference, make sure the SenseNova-U1 runtime dependencies are also installed in the
same environment. When using this app from the main SenseNova-U1 checkout, the loader can discover
`src/` automatically. You can override it if needed:

```bash
python -m pip install -e .
export SENSENOVA_U1_SRC="/path/to/SenseNova-U1/src"
```

Restart ComfyUI after installation.

## Model and LoRA Storage / 模型和LoRA存储

For local inference, place files as follows:

| File Type / 文件类型 | Location / 存储位置 |
|---------------------|-------------------|
| Main model (checkpoints) / 主模型 | `checkpoints/` |
| LoRA models / LoRA模型 | `loras/` |

## API Key Configuration / API密钥配置

For remote API usage, create an `api_key.txt` file in the project root and write your API key into it:

```
# api_key.txt
your-api-token-here
```

Alternatively, set environment variables or use `.env`:

```bash
export SN_API_KEY="your-api-token"
export SN_BASE_URL="https://token.sensenova.cn/v1"
```

Tokens are not exposed as node inputs, so they are not saved into ComfyUI workflows.

## Workflows / 工作流

Example workflows live in `workflows/`:

- `api_u1_fast_t2i.json`: API U1-Fast text-to-image.
- `local_t2i.json`: local SenseNova-U1 text-to-image.
- `local_editing.json`: local SenseNova-U1 image editing.
- `local_interleave.json`: local SenseNova-U1 interleaved generation.

Drag a workflow JSON into ComfyUI, then update `model_path`, `device`, `device_map`, and prompt
settings as needed. For a smoke test, set `num_steps` to `1` or `2` before returning to the
recommended `50`.

## Notes On Samplers / 采样器说明

Local U1 generation uses the sampling loop implemented by `t2i_generate`, `it2i_generate`, and
`interleave_gen`. It does not directly plug into ComfyUI's `KSampler` / latent model interface.
You can still reuse ComfyUI image IO and post-processing nodes around these U1 nodes.

---

# SenseNova-U1 for ComfyUI

ComfyUI 自定义节点，用于 SenseNova-U1 API 和本地推理。

## 节点说明

- `SenseNova Image Generate`：调用 U1-Fast 图片生成 API。
- `SenseNova Chat`、`SenseNova Vision URL`、`SenseNova Vision Image`：实用 API 节点。
- `SenseNova Prompt Builder`：将原始想法改写为图片生成提示词。
- `SenseNova U1 Local Loader`：加载本地或 HuggingFace 的 SenseNova-U1 检查点。
- `SenseNova U1 Local Text to Image`：运行本地 `t2i_generate`。
- `SenseNova U1 Local Image Edit`：运行本地 `it2i_generate`。
- `SenseNova U1 Local Interleave`：运行本地 `interleave_gen`。
- `SenseNova Interleave Preview`：渲染有序的交错文本/图片结果。

## 安装

从 SenseNova-U1 仓库：

```bash
python apps/comfyui/install.py --comfyui /path/to/ComfyUI
```

默认创建以下链接：

```text
/path/to/ComfyUI/custom_nodes/ComfyUI-SenseNova-U1 -> /path/to/SenseNova-U1/apps/comfyui
```

在 ComfyUI 使用的 Python 环境中安装轻量级 ComfyUI 应用依赖：

```bash
python -m pip install -r apps/comfyui/requirements.txt
```

如需本地推理，请确保在同一环境中安装 SenseNova-U1 运行时依赖。从主 SenseNova-U1 仓库使用时，加载器可自动发现 `src/`。如有需要可手动指定：

```bash
python -m pip install -e .
export SENSENOVA_U1_SRC="/path/to/SenseNova-U1/src"
```

安装后请重启 ComfyUI。

## 模型和LoRA存储

本地推理时，请按以下方式放置文件：

| 文件类型 | 存储位置 |
|---------|---------|
| 主模型 (checkpoints) | `checkpoints/` |
| LoRA模型 | `loras/` |

## API密钥配置

远程 API 使用时，请在项目根目录创建 `api_key.txt` 文件，并将您的 API 密钥写入其中：

```
# api_key.txt
your-api-token-here
```

或者设置环境变量或使用 `.env` 文件：

```bash
export SN_API_KEY="your-api-token"
export SN_BASE_URL="https://token.sensenova.cn/v1"
```

令牌不会作为节点输入暴露，因此不会保存到 ComfyUI 工作流中。

## 工作流

示例工作流位于 `workflows/` 目录：

- `api_u1_fast_t2i.json`：API U1-Fast 文生图。
- `local_t2i.json`：本地 SenseNova-U1 文生图。
- `local_editing.json`：本地 SenseNova-U1 图片编辑。
- `local_interleave.json`：本地 SenseNova-U1 交错生成。

将工作流 JSON 拖入 ComfyUI，然后根据需要更新 `model_path`、`device`、`device_map` 和提示词设置。
首次测试时，可将 `num_steps` 设置为 `1` 或 `2`，确认正常后再改为推荐的 `50`。

## 采样器说明

本地 U1 生成使用由 `t2i_generate`、`it2i_generate` 和 `interleave_gen` 实现的采样循环。
它不直接接入 ComfyUI 的 `KSampler` / 潜空间模型接口，但您仍可围绕这些 U1 节点复用 ComfyUI 的图片 IO 和后处理节点。
