"""编译 sageattn3 cp313 wheel 的辅助脚本。
在调用 pip wheel 之前，手动注入 MSVC/SDK 环境变量（模拟 vcvars64.bat 的效果），
因为 torch 的 cpp_extension 在 VS18 下检测 Hostx64 cl 有 bug。
使用 VS2022 Build Tools (MSVC 14.44) —— CuTe 验证过的编译器版本。
"""
import os
import sys

MSVC_VER = "14.44.35207"
VS_ROOT = r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"
MSVC = os.path.join(VS_ROOT, r"VC\Tools\MSVC", MSVC_VER)
SDK_VER = "10.0.26100.0"
SDK = r"C:\Program Files (x86)\Windows Kits\10"
CUDA = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1"

# ninja 位置（python_embeded 的 Scripts）
PY_BASE = r"D:\AI\ComfyUI\MiniMax-H3_NVFP4\python_embeded"
NINJA = os.path.join(PY_BASE, "Scripts")

# ---- PATH ----
path_parts = [
    os.path.join(MSVC, r"bin\Hostx64\x64"),   # cl.exe
    os.path.join(MSVC, r"bin\Hostx64\arm64"),
    os.path.join(SDK, r"bin", SDK_VER, "x64"),
    os.path.join(CUDA, "bin"),
    NINJA,                                     # ninja.exe
]
os.environ["PATH"] = ";".join(path_parts) + ";" + os.environ.get("PATH", "")

# ---- INCLUDE ----
os.environ["INCLUDE"] = ";".join([
    os.path.join(MSVC, "include"),
    os.path.join(MSVC, "atlmfc", "include"),
    os.path.join(SDK, "Include", SDK_VER, "ucrt"),
    os.path.join(SDK, "Include", SDK_VER, "um"),
    os.path.join(SDK, "Include", SDK_VER, "shared"),
    os.path.join(SDK, "Include", SDK_VER, "winrt"),
    os.path.join(SDK, "Include", SDK_VER, "cppwinrt"),
    os.path.join(CUDA, "include"),
])

# ---- LIB ----
os.environ["LIB"] = ";".join([
    os.path.join(MSVC, "lib", "x64"),
    os.path.join(MSVC, "atlmfc", "lib", "x64"),
    os.path.join(SDK, "Lib", SDK_VER, "ucrt", "x64"),
    os.path.join(SDK, "Lib", SDK_VER, "um", "x64"),
    os.path.join(CUDA, "lib", "x64"),
])

# ---- torch / build env ----
os.environ["CUDA_HOME"] = CUDA
os.environ["TORCH_CUDA_ARCH_LIST"] = "12.0"
os.environ["FAHOPPER_FORCE_BUILD"] = "TRUE"
os.environ["DISTUTILS_USE_SDK"] = "1"
os.environ["MSSdk"] = "1"
os.environ["_GLIBCXX_USE_CXX11_ABI"] = "0"

# 确认关键工具
for tool in ["cl.exe", "ninja.exe", "nvcc.exe"]:
    found = False
    for p in os.environ["PATH"].split(";"):
        if os.path.exists(os.path.join(p, tool)):
            found = True
            print(f"[OK] {tool} -> {os.path.join(p, tool)}")
            break
    if not found:
        print(f"[WARN] {tool} not found in PATH!")

print("[INFO] INCLUDE/LIB/PATH 已注入，开始编译...")
print("[INFO] 编译命令将使用 ninja + Hostx64 cl")

# 切换到源码目录并调用 pip wheel
os.chdir(r"C:\Users\Yanglihao\WorkBuddy\2026-08-19-05-45-46\sageattn3_build\SageAttention-mengqin\sageattention3_blackwell")

import subprocess
cmd = [
    os.path.join(PY_BASE, "python.exe"),
    "-m", "pip", "wheel", ".",
    "-w", r"C:\Users\Yanglihao\WorkBuddy\2026-08-19-05-45-46\sageattn3_build\dist",
    "--no-build-isolation",
]
print(f"[INFO] 运行: {' '.join(cmd)}")
proc = subprocess.run(cmd)
print(f"[INFO] 编译进程退出码: {proc.returncode}")
sys.exit(proc.returncode)
