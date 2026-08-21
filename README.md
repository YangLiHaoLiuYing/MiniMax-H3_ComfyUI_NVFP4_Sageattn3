# sageattn3 cp313 Windows Wheel + MiniMax-H3 v3 Acceleration

**The first community-built sageattn3 wheel that works directly on Windows + Python 3.13 + torch 2.13 (cu130)**, plus ready-made MiniMax-H3 Director v3 workflows with sageattn3 FP4-accelerated attention.

- Target hardware: **RTX 50 series (sm120, Blackwell)** — tested on RTX 5080
- Kernel: sageattn3 FP4-quantized Flash Attention (`sageattn3_blackwell`)
- Accuracy: **cosine similarity 1.0 / MSE = 0** vs standard attention
- Speed: **16.7 TFLOP/s** on RTX 5080 (0.52 ms/call, B=2,H=16,N=1024,D=128)

> 中文版见 [README_zh.md](README_zh.md) · 编译指南 [BUILD.md](BUILD.md) / [BUILD_zh.md](BUILD_zh.md)

---

## File Structure

```
sageattn3-v3-release/
├── README.md                        # This file (EN)
├── README_zh.md                     # README (中文)
├── BUILD.md                         # Full build guide (EN)
├── BUILD_zh.md                      # Build guide (中文)
├── LICENSE                          # Apache-2.0 (same as upstream)
├── dist/
│   └── sageattn3-1.0.0-cp313-cp313-win_amd64.whl   # Ready-built wheel (pip install)
├── patches/
│   ├── api.cu                       # Modified api.cu (unnecessary include removed)
│   ├── api.cu.bak                   # Original api.cu (patch base)
│   └── api.cu.patch                 # Unified diff (1-line removal; git apply / patch -p1)
├── tools/
│   ├── setup.py                     # Build config (C++20 — critical)
│   ├── build_env.py                 # Env injection script (MSVC/SDK/CUDA vars)
│   ├── make_v3_workflow.py          # Single-workflow v3 converter
│   └── make_v3_workflows.py         # Batch v3 converter (all 8 examples)
└── workflows_v3/
    ├── minimax_h3_director_加速版.json              # All-in-one workflow
    ├── minimax_h3_director_t2v_v3.json              # Text-to-video
    ├── minimax_h3_director_external_groups_i2v_v3.json  # Image-to-video (groups)
    ├── minimax_h3_director_r2v_v3.json              # Reference-image-to-video
    ├── minimax_h3_director_external_groups_r2v_v3.json
    ├── minimax_h3_director_v2v_v3.json              # Video-to-video
    ├── minimax_h3_director_rv2v_v3.json             # Reference-video-to-video
    └── minimax_h3_director_fl2v_v3.json             # FL image-to-video
```

## Models (NOT included — download separately)

The MiniMax H3 model files are **not part of this repo** (licensing + size). The workflows reference these files — obtain them from MiniMax's official channel / HuggingFace and place them under `<ComfyUI>/models/`:

| File | Node | Folder |
|---|---|---|
| `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | UNETLoader | `models/checkpoints/` (or `models/unet/`) |
| `minimax_h3_ref2va_pruned_int8_convrot.safetensors` | UNETLoader | `models/checkpoints/` (or `models/unet/`) |
| `qwen3vl_32b_heretic_minimax_h3_nvfp4.safetensors` | CLIPLoader | `models/clip/` |
| `minimax_h3_audio_vae_fp32.safetensors` | VAELoader | `models/vae/` |
| `minimax_h3_video_vae_fp16.safetensors` | VAELoader | `models/vae/` |

If your downloaded files have different names, just update the corresponding loader node in the workflow.

## Quick Start (binary only, no compilation)

```bat
:: 1) Install the wheel into your ComfyUI environment (python_embeded works too)
D:\AI\ComfyUI\xxx\python_embeded\python.exe -m pip install dist\sageattn3-1.0.0-cp313-cp313-win_amd64.whl --force-reinstall

:: 2) Verify import
D:\AI\ComfyUI\xxx\python_embeded\python.exe -c "import sageattn3; print('OK')"

:: 3) Copy workflows from workflows_v3\ into
::    <ComfyUI>/user/default/workflows/  then open ComfyUI and use them
```

How the v3 workflows work: **KJNodes `PathchSageAttentionKJ`** (with `sageattn3`) replaces H3's native `MiniMaxH3MemoryEfficientSageAttentionPatch`, routing the UNET attention through sageattn3's FP4 kernel:

```
UNETLoader → PathchSageAttentionKJ(sageattn3) → MiniMaxH3Director
```

## Why Build It Yourself (community gap)

The official sageattn3 and mengqin releases ship Linux wheels only; mengqin's Windows wheel is built against `cu130torch291` (torch 2.9.1), which is **ABI-incompatible with torch 2.13 (cu130)** — installing it fails with `The specified procedure could not be found`. This repo provides a **cp313 wheel that works with torch 2.13** plus a fully reproducible build process.

## Key Technical Points (build pitfalls)

| Problem | Root cause | Fix |
|---|---|---|
| `error C3545` (MSVC) | CUTLASS v3.9.2+ CuTe templates trigger an MSVC bug under C++20 | See [BUILD.md](BUILD.md): **remove `#include <torch/nn/functional.h>` from api.cu** (the torch C++ API headers it pulls in deep-instantiate CuTe templates; after removal C3545 no longer appears) |
| `cudafe++ crash 0xC0000409` | CUDA 13.3 nvcc frontend crashes on large template files | **Use the CUDA 13.1 toolkit** (can be installed alongside 13.3) |
| `LNK1104: python313.lib` | ComfyUI python_embeded is a slim build without import libs | Copy `python313.lib` from any Python 3.13 install into `python_embeded/libs/` |
| `Python.h` missing | python_embeded has no dev headers | Copy the full Python 3.13 `include/` into `python_embeded/include/` |

## Test Results (RTX 5080)

```
torch: 2.13.0+cu130 | CUDA: 13.1 (build) | GPU: RTX 5080
sdpa output: torch.Size([2, 16, 512, 128]) fp16
cosine similarity vs standard attention: 1.0000
MSE: 0.000000
speed: 0.52 ms/call = 16.7 TFLOP/s (B=2,H=16,N=1024,D=128)
```

## Known Limitations

- **sm120 (RTX 50 series) only**; RTX 40 series (sm89) is not supported
- Missing `ComfyUI/requirements.txt` makes `/system_stats` return 500 (a MiniMax packaging quirk; does not affect nodes or workflow execution)
- Full generation should be verified by running inside ComfyUI (requires loading the MiniMax H3 model)

## Acknowledgements

- [mengqin/SageAttention](https://github.com/mengqin/SageAttention) (sageattention3_blackwell source & releases)
- [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes) (`PathchSageAttentionKJ` node)
- [NVIDIA/cutlass](https://github.com/NVIDIA/cutlass) (v4.0.0)
- The [SageAttention](https://github.com/thu-ml/SageAttention) team
