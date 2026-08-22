# 编译指南：sageattn3 cp313 Windows wheel

从源码编译 `sageattn3-1.0.0-cp313-cp313-win_amd64.whl`（torch 2.13 / cu130 兼容）。

## 环境要求

| 组件 | 版本 | 说明 |
|---|---|---|
| Windows | 10/11 x64 | |
| Visual Studio Build Tools | 2022 或 18（MSVC 14.4x+）| 需含 C++ 桌面开发组件 |
| CUDA Toolkit | **13.1** | 关键！13.3 会导致 cudafe++ 崩溃 |
| Python | 3.13.x | 与目标环境一致 |
| PyTorch | 2.13.0+cu130 | 目标运行环境（ComfyUI python_embeded） |
| CUTLASS | v4.0.0 | 源码内自动 clone |

## 步骤

### 1. 准备源码

```bat
git clone https://github.com/mengqin/SageAttention.git
cd SageAttention/sageattention3_blackwell
```

### 2. 应用关键补丁（唯一必须的源码修改）

`sageattn3/blackwell/api.cu` 中删除一行（见 `patches/api.cu.patch`）：

```diff
 #include <torch/python.h>
-#include <torch/nn/functional.h>
 #include <ATen/cuda/CUDAContext.h>
```

> **为什么**：`torch/nn/functional.h` 引入的 torch C++ API 头文件会深度实例化 CUTLASS CuTe 模板，在 C++20 下触发 MSVC `C3545` 编译错误。api.cu 只用 `at::Tensor`/`torch::IntArrayRef`，删掉完全不影响功能。

```bat
:: 应用补丁（在 **sageattn3** 源码仓库根目录执行，git apply 或 patch -p1 均可）
git apply patches\api.cu.patch
:: 或直接复制本仓库修改好的文件
copy patches\api.cu sageattn3\blackwell\api.cu
```

### 3. 配置 setup.py

保持默认（本仓库 `tools/setup.py` 即最终成功配置）：
- nvcc 与 host 均为 **C++20**（`-std=c++20` + `/std:c++20`）
- 关键编译 flag：`/Zc:preprocessor`、`/Zc:twoPhase-`、`/bigobj`、`/MD`

> 注意：不要改成 C++17。全 C++17 会与 torch 2.13 头文件（位域默认初始化等 C++20 特性）冲突；且 nvcc C++17 + host C++20 的混配会导致 cudafe++ 崩溃。

### 4. 准备编译环境（python_embeded 精简版）

ComfyUI 的 `python_embeded` 是精简 Python，编译前需补齐：

```bat
:: a) Python 开发头文件（缺 Python.h）
xcopy /E /I C:\path\to\full_python313\include  D:\AI\ComfyUI\xxx\python_embeded\include

:: b) 导入库（缺 python313.lib → LNK1104）
copy C:\path\to\full_python313\libs\python313.lib  D:\AI\ComfyUI\xxx\python_embeded\libs\
```

### 5. 注入环境并编译

使用 `tools/build_env.py`（自动注入 MSVC/SDK/CUDA 的 INCLUDE/LIB/PATH，并指向 **CUDA v13.1**）：

```bat
D:\AI\ComfyUI\xxx\python_embeded\python.exe build_env.py
:: 产物输出到 dist\sageattn3-1.0.0-cp313-cp313-win_amd64.whl
```

或手动设置环境变量后直接：

```bat
D:\AI\ComfyUI\xxx\python_embeded\python.exe -m pip wheel . -w dist --no-build-isolation
```

> `build_env.py` 中的 `CUDA` 路径需指向 `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1`。CUDA 13.1 与 13.3 可并存安装，互不影响。

### 6. 安装与验证

```bat
D:\AI\ComfyUI\xxx\python_embeded\python.exe -m pip install dist\sageattn3-1.0.0-cp313-cp313-win_amd64.whl --no-deps --force-reinstall

D:\AI\ComfyUI\xxx\python_embeded\python.exe -c "import sageattn3; from sageattn3.api import sdpa; print('OK')"
```

GPU 冒烟测试（需 RTX 50 系）：

```python
import torch
from sageattn3.api import sdpa
q = torch.randn(2, 16, 512, 128, device="cuda", dtype=torch.float16)
out = sdpa(q, q, q)
torch.cuda.synchronize()
print(out.shape, torch.isfinite(out).all())  # torch.Size([2,16,512,128]) True
```

## 常见问题

| 症状 | 原因与处理 |
|---|---|
| `error C3545: Ints requires a non-type template argument` | api.cu 未删 `torch/nn/functional.h` → 应用补丁 |
| `cudafe++.exe died with exit code 0xC0000409` | 用了 CUDA 13.3 → 换 13.1 |
| `LNK1104: cannot open file 'python313.lib'` | 补 `python313.lib` 到 python_embeded/libs |
| `fatal error: Python.h: No such file` | 补 Python include 头文件 |
| `C3545` 出现在 CUTLASS 头文件里 | 混用了 CUTLASS 3.9.2/4.x 的文件 → 用干净 v4.0.0 完整版，不要混搭 |
| 安装 mengqin 官方 wheel 报"找不到指定的程序" | ABI 不兼容（torch 2.9 vs 2.13）→ 用本仓库 wheel |

## 为什么这套组合能成功（原理简述）

1. **C3545 的真正触发点**：不是 CUTLASS 版本，而是 `torch/nn/functional.h` 引入的头文件深度实例化 CuTe 的 `CompactLambda::seq` 模板，MSVC 在 C++20 下对参数包推导失败。删掉该 include 后实例化路径改变，C++20 下不再触发。
2. **cudafe++ 崩溃**：CUDA 13.3 前端处理大型模板文件的 bug，换 13.1 即消失。
3. **其余**：环境注入（build_env.py）+ python_embeded 补齐（include/libs）。

## v3 工作流转换

拿到可用 wheel 后，把 H3 的 `MiniMaxH3MemoryEfficientSageAttentionPatch` 换成 KJNodes 的 `PathchSageAttentionKJ(sageattn3)` 即可让 UNET attention 走 FP4 内核：

```bat
python tools\make_v3_workflows.py <Director 的 example_workflows 目录> <输出目录>
```

> `<Director 的 example_workflows 目录>` 即 [AIMixer/ComfyUI_MiniMaxH3_Director](https://github.com/AIMixer/ComfyUI_MiniMaxH3_Director) 节点自带的 `example_workflows/`（该节点基于 ComfyUI 官方 MiniMax H3 支持，PR #15224 / #15228）。我们的 8 个 v3 工作流即派生自这些内置示例。

转换规则：删除链路上所有 patch 节点（H3 patch / 旧 KJ），新建 `PathchSageAttentionKJ`（`widgets_values=["sageattn3"]`），重连 `UNET → KJ → Director`。8 个成品工作流见 `workflows_v3/`。
