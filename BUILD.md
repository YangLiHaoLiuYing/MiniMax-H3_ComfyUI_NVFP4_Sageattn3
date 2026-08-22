# Build Guide: sageattn3 cp313 Windows Wheel

Build `sageattn3-1.0.0-cp313-cp313-win_amd64.whl` from source (compatible with torch 2.13 / cu130).

> 中文版见 [BUILD_zh.md](BUILD_zh.md)

## Requirements

| Component | Version | Notes |
|---|---|---|
| Windows | 10/11 x64 | |
| Visual Studio Build Tools | 2022 or 18 (MSVC 14.4x+) | must include "Desktop development with C++" |
| CUDA Toolkit | **13.1** | critical! CUDA 13.3 crashes cudafe++ |
| Python | 3.13.x | must match the target environment |
| PyTorch | 2.13.0+cu130 | target runtime (e.g. ComfyUI python_embeded) |
| CUTLASS | v4.0.0 | cloned automatically by setup.py |

## Steps

### 1. Get the source

```bat
git clone https://github.com/mengqin/SageAttention.git
cd SageAttention/sageattention3_blackwell
```

### 2. Apply the one critical patch (the only required source change)

Remove one line from `sageattn3/blackwell/api.cu` (see `patches/api.cu.patch`):

```diff
 #include <torch/python.h>
-#include <torch/nn/functional.h>
 #include <ATen/cuda/CUDAContext.h>
```

> **Why**: `torch/nn/functional.h` pulls in torch C++ API headers that deep-instantiate CUTLASS CuTe templates, triggering MSVC `C3545` under C++20. api.cu only uses `at::Tensor` / `torch::IntArrayRef`, so removing it has zero functional impact.

```bat
:: Apply the patch (from the **sageattn3** source repo root; works with git apply or patch -p1)
git apply patches\api.cu.patch
:: …or simply copy the pre-patched file from this repo
copy patches\api.cu sageattn3\blackwell\api.cu
```

### 3. Configure setup.py

Keep the defaults (this repo's `tools/setup.py` is the exact working config):
- Both nvcc and host use **C++20** (`-std=c++20` + `/std:c++20`)
- Key flags: `/Zc:preprocessor`, `/Zc:twoPhase-`, `/bigobj`, `/MD`

> Do **not** switch to C++17. Full C++17 conflicts with torch 2.13 headers (bit-field default member initializers etc. are C++20); and mixing nvcc C++17 + host C++20 crashes cudafe++.

### 4. Prepare the build environment (slim python_embeded)

ComfyUI's `python_embeded` is a slim Python. Before building, add:

```bat
:: a) Python dev headers (missing Python.h)
xcopy /E /I C:\path\to\full_python313\include  D:\AI\ComfyUI\xxx\python_embeded\include

:: b) Import library (missing python313.lib → LNK1104)
copy C:\path\to\full_python313\libs\python313.lib  D:\AI\ComfyUI\xxx\python_embeded\libs\
```

### 5. Inject the environment and build

Use `tools/build_env.py` (injects MSVC/SDK/CUDA INCLUDE/LIB/PATH and points to **CUDA v13.1**):

```bat
D:\AI\ComfyUI\xxx\python_embeded\python.exe build_env.py
:: Output lands in dist\sageattn3-1.0.0-cp313-cp313-win_amd64.whl
```

Or set the env vars manually and run:

```bat
D:\AI\ComfyUI\xxx\python_embeded\python.exe -m pip wheel . -w dist --no-build-isolation
```

> The `CUDA` path in `build_env.py` must point to `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1`. CUDA 13.1 and 13.3 can coexist.

### 6. Install & verify

```bat
D:\AI\ComfyUI\xxx\python_embeded\python.exe -m pip install dist\sageattn3-1.0.0-cp313-cp313-win_amd64.whl --no-deps --force-reinstall

D:\AI\ComfyUI\xxx\python_embeded\python.exe -c "import sageattn3; from sageattn3.api import sdpa; print('OK')"
```

GPU smoke test (requires RTX 50 series):

```python
import torch
from sageattn3.api import sdpa
q = torch.randn(2, 16, 512, 128, device="cuda", dtype=torch.float16)
out = sdpa(q, q, q)
torch.cuda.synchronize()
print(out.shape, torch.isfinite(out).all())  # torch.Size([2,16,512,128]) True
```

## FAQ

| Symptom | Cause & fix |
|---|---|
| `error C3545: Ints requires a non-type template argument` | api.cu still includes `torch/nn/functional.h` → apply the patch |
| `cudafe++.exe died with exit code 0xC0000409` | using CUDA 13.3 → switch to 13.1 |
| `LNK1104: cannot open file 'python313.lib'` | add `python313.lib` to python_embeded/libs |
| `fatal error: Python.h: No such file` | add the Python include headers |
| `C3545` inside CUTLASS headers | mixed CUTLASS 3.9.2/4.x files → use a clean full v4.0.0, don't mix versions |
| mengqin's official wheel fails with "procedure could not be found" | ABI mismatch (torch 2.9 vs 2.13) → use this repo's wheel |

## Why This Combination Works (summary)

1. **The real C3545 trigger** is not the CUTLASS version — it's the torch C++ API headers pulled in by `torch/nn/functional.h` deep-instantiating CuTe's `CompactLambda::seq` templates, where MSVC fails to deduce the parameter pack under C++20. Removing that include changes the instantiation path, so C3545 disappears even under C++20.
2. **cudafe++ crash**: a CUDA 13.3 frontend bug on large template files; gone with 13.1.
3. **Everything else**: environment injection (`build_env.py`) + filling the gaps in python_embeded (include/libs).

## Converting Workflows to v3

Once the wheel works, swap H3's `MiniMaxH3MemoryEfficientSageAttentionPatch` for KJNodes' `PathchSageAttentionKJ(sageattn3)` so UNET attention runs through the FP4 kernel:

```bat
python tools\make_v3_workflows.py <Director example_workflows dir> <output dir>
```

> The `<Director example_workflows dir>` is `example_workflows/` shipped inside [AIMixer/ComfyUI_MiniMaxH3_Director](https://github.com/AIMixer/ComfyUI_MiniMaxH3_Director) (the node is based on ComfyUI official MiniMax H3 support, PR #15224 / #15228). Our 8 v3 workflows are derived from those bundled examples.

Rules: remove every patch node on the chain (H3 patch / old KJ), create a `PathchSageAttentionKJ` node (`widgets_values=["sageattn3"]`), and rewire `UNET → KJ → Director`. 8 ready-made v3 workflows are in `workflows_v3/`.
