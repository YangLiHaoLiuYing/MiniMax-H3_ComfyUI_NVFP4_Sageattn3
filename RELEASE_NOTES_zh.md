# Release Notes — sageattn3 v1.0.0+cp313 Windows

> **社区首个可在 Windows + Python 3.13 + torch 2.13 (cu130) 上直接安装使用的 sageattn3 wheel**，附 MiniMax-H3 Director v3（FP4 加速）工作流。

## 🎯 亮点

- ✅ **cp313 / win_amd64 wheel**，torch 2.13.0+cu130 直接 `pip install` 可用（无需自己编译）
- ✅ 官方及 mengqin 的 Windows wheel 均为 torch 2.9 构建，与 torch 2.13 **ABI 不兼容**（报"找不到指定的程序"）——本仓库补齐了这个空白
- ✅ RTX 5080（sm120）实测：**16.7 TFLOP/s**，精度与标准 attention **完全一致**（余弦相似度 1.0，MSE = 0）
- ✅ 附 8 个 MiniMax-H3 **v3 加速工作流**（UNET attention 走 sageattn3 FP4 内核）
- ✅ 附**完整编译指南**（BUILD.md），任何人可复现

## 📦 安装

```bat
pip install sageattn3-1.0.0-cp313-cp313-win_amd64.whl --no-deps --force-reinstall

python -c "import sageattn3; from sageattn3.api import sdpa; print('OK')"
```

## 🧪 实测数据（RTX 5080 / torch 2.13.0+cu130）

| 指标 | 结果 |
|---|---|
| 输出 shape/dtype | `[2,16,512,128]` fp16 ✅ |
| 余弦相似度 vs 标准 attention | **1.0000** |
| MSE | **0.000000** |
| 速度 | **0.52 ms/次**（B=2,H=16,N=1024,D=128）|
| 算力 | **16.7 TFLOP/s** |

## 📁 文件清单

```
├── dist/sageattn3-1.0.0-cp313-cp313-win_amd64.whl   # 成品 wheel
├── patches/api.cu + api.cu.patch                    # 唯一必要源码修改（删 1 行 include）
├── tools/                                           # setup.py / build_env.py / v3 转换脚本
├── workflows_v3/                                    # 8 个 v3 工作流
├── README.md                                        # 快速上手
└── BUILD.md                                         # 完整编译指南 + FAQ
```

## 🔧 编译要点（详见图谱 BUILD.md）

| 坑 | 解法 |
|---|---|
| MSVC `C3545`（C++20）| 删除 `api.cu` 中 `#include <torch/nn/functional.h>`（补丁见 patches/）|
| `cudafe++ 0xC0000409` 崩溃 | 使用 **CUDA 13.1** 工具链（13.3 有 bug）|
| `LNK1104: python313.lib` | 补导入库到 python_embeded/libs |
| `Python.h` 缺失 | 补 Python 3.13 include 头文件 |

## ⚠️ 已知限制

- 仅支持 **sm120（RTX 50 系）**；RTX 40 系不支持
- `ComfyUI/requirements.txt` 缺失会导致 `/system_stats` 500（MiniMax 打包环境固有，不影响使用）

## 📥 模型权重（不包含）

本发布**不含**模型权重。请自行下载 5 个必需的 MiniMax-H3 模型并放入 `ComfyUI/models/` 对应子目录：

- `minimax_h3_fl2va_pruned_int8_convrot.safetensors` → `models/checkpoints/`
- `minimax_h3_ref2va_pruned_int8_convrot.safetensors` → `models/checkpoints/`
- `qwen3vl_32b_heretic_minimax_h3_nvfp4.safetensors` → `models/clip/`
- `minimax_h3_audio_vae_fp32.safetensors` → `models/vae/`
- `minimax_h3_video_vae_fp16.safetensors` → `models/vae/`

## 📄 许可证

Apache-2.0 — 继承自 [mengqin/SageAttention](https://github.com/mengqin/SageAttention)。见 `LICENSE`。

## ⚠️ 免责声明

本发布为社区预编译 wheel，仅供方便使用，非 NVIDIA / SageAttention 官方发布。风险自负；若自行构建，请对照 `patches/` 中的源码补丁进行验证。

## 🙏 致谢

- [mengqin/SageAttention](https://github.com/mengqin/SageAttention)（sageattention3_blackwell 源码）
- [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes)（`PathchSageAttentionKJ` 节点）
- [NVIDIA/cutlass](https://github.com/NVIDIA/cutlass) v4.0.0
- [SageAttention](https://github.com/thu-ml/SageAttention) 团队
