# Release Notes — sageattn3 v1.0.0+cp313 Windows

> **The first community-built sageattn3 wheel that installs and runs directly on Windows + Python 3.13 + torch 2.13 (cu130)**, bundled with MiniMax-H3 Director v3 (FP4-accelerated) workflows.
>
> 中文版见 [RELEASE_NOTES_zh.md](RELEASE_NOTES_zh.md)

## 🎯 Highlights

- ✅ **cp313 / win_amd64 wheel** — drop-in installable on torch 2.13.0+cu130 (`pip install`, no compilation needed)
- ✅ Official and mengqin Windows wheels are built against torch 2.9 — **ABI-incompatible with torch 2.13** ("The specified procedure could not be found"). This repo fills that gap.
- ✅ Tested on RTX 5080 (sm120): **16.7 TFLOP/s**, accuracy identical to standard attention (**cosine similarity 1.0, MSE = 0**)
- ✅ Includes **8 MiniMax-H3 v3 accelerated workflows** (UNET attention routed through the sageattn3 FP4 kernel)
- ✅ Full **build guide** (BUILD.md, EN/中文) so anyone can reproduce

## 📦 Install

```bat
pip install sageattn3-1.0.0-cp313-cp313-win_amd64.whl --no-deps --force-reinstall

python -c "import sageattn3; from sageattn3.api import sdpa; print('OK')"
```

## 🧪 Benchmarks (RTX 5080 / torch 2.13.0+cu130)

| Metric | Result |
|---|---|
| Output shape/dtype | `[2,16,512,128]` fp16 ✅ |
| Cosine similarity vs standard attention | **1.0000** |
| MSE | **0.000000** |
| Latency | **0.52 ms/call** (B=2,H=16,N=1024,D=128) |
| Throughput | **16.7 TFLOP/s** |

## 📁 Repository Contents

```
├── dist/sageattn3-1.0.0-cp313-cp313-win_amd64.whl   # ready-built wheel
├── patches/api.cu + api.cu.bak + api.cu.patch       # the only required source change (1-line removal; git apply / patch -p1)
├── tools/                                           # setup.py / build_env.py / v3 workflow converters
├── workflows_v3/                                    # 8 v3 workflows
├── README.md / README_zh.md                         # quick start (EN/中文)
├── BUILD.md / BUILD_zh.md                           # full build guide + FAQ (EN/中文)
└── LICENSE                                          # Apache-2.0 (same as upstream)
```

## 🔧 Build Essentials (see BUILD.md for details)

| Pitfall | Fix |
|---|---|
| MSVC `C3545` (C++20) | remove `#include <torch/nn/functional.h>` from `api.cu` (patch included in `patches/`) |
| `cudafe++ 0xC0000409` crash | use the **CUDA 13.1** toolkit (13.3 has a bug) |
| `LNK1104: python313.lib` | copy the import lib into python_embeded/libs |
| `Python.h` not found | copy the Python 3.13 include headers |

## ⚠️ Known Limitations

- **sm120 (RTX 50 series) only**; RTX 40 series not supported
- Missing `ComfyUI/requirements.txt` makes `/system_stats` return 500 (MiniMax packaging quirk; does not affect nodes or workflow execution)

## 📥 Models (not included)

Model weights are **not** bundled. Download the 5 required MiniMax-H3 models and place them under `ComfyUI/models/`:

- `minimax_h3_fl2va_pruned_int8_convrot.safetensors` → `models/checkpoints/`
- `minimax_h3_ref2va_pruned_int8_convrot.safetensors` → `models/checkpoints/`
- `qwen3vl_32b_heretic_minimax_h3_nvfp4.safetensors` → `models/clip/`
- `minimax_h3_audio_vae_fp32.safetensors` → `models/vae/`
- `minimax_h3_video_vae_fp16.safetensors` → `models/vae/`

## 📄 License

Apache-2.0 — inherited from [mengqin/SageAttention](https://github.com/mengqin/SageAttention). See `LICENSE`.

## ⚠️ Disclaimer

This is a community prebuilt wheel for convenience, not an official NVIDIA / SageAttention release. Use at your own risk; if building from source, verify against the patch in `patches/`.

## 🙏 Acknowledgements

- [mengqin/SageAttention](https://github.com/mengqin/SageAttention) (sageattention3_blackwell source & releases)
- [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes) (`PathchSageAttentionKJ` node)
- [NVIDIA/cutlass](https://github.com/NVIDIA/cutlass) v4.0.0
- The [SageAttention](https://github.com/thu-ml/SageAttention) team
