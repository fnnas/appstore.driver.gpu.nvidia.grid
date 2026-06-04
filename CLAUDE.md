# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 交流和文档语言

除非用户明确要求使用其他语言，面向用户的说明、总结、计划、代码审查意见和新增/修改的项目文档都必须使用中文。用户要求保留的固定英文模板或上游工具/API 的原文名称可以保持英文。

## 项目定位

这个仓库用于构建面向 FNOS / 飞牛 NAS vGPU 场景的 NVIDIA GRID 驱动应用包。仓库会产出两个必须保持版本一致的应用包：

- `appstore.driver.gpu.nvidia.ko`：内核空间驱动包，负责安装 NVIDIA kernel module 和 firmware。
- `appstore.driver.gpu.nvidia.user`：用户空间驱动包，负责安装 NVIDIA 用户空间库、`nvidia-smi`、`nvidia-gridd` 和 NVLTS。

当前支持的驱动组合包括 GRID 19.5 / `580.159.03` / `580.159.03-3`，以及 GRID 16.14 / `535.309.01` / `535.309.01-1`。支持 FNOS/TRIM 内核 `6.18.18-trim`。应用包版本中的 `-1`、`-2` 是同一 NVIDIA 驱动版本下的应用包发布修订号，不代表 NVIDIA 驱动版本变化。

## 常用命令

这个仓库没有 package manager 配置，也没有常规本地测试框架。权威静态检查来自 `.github/workflows/static_checks.yml`。在 Windows/Git Bash 环境中，如果 `python3` 不在 `PATH` 上，可以改用 `python`；如果未限定路径的 `find` 解析成 Windows `FIND.EXE`，请改用 `/usr/bin/find`。

本地运行 UTF-8 和乱码标记检查：

```bash
python3 - <<'PY'
from pathlib import Path

paths = [
    Path("readme.md"),
    Path("docs/usage.md"),
    Path("docs/maintenance.md"),
    Path("CLAUDE.md"),
    Path("package_kernel_space/manifest"),
    Path("package_user_space/manifest"),
    Path("scripts/patch-nvidia-grid-kernel-binary.py"),
]

failed = False
for path in paths:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        print(f"{path}: invalid UTF-8: {exc}")
        failed = True
        continue
    if "?" * 3 in text or "\ufffd" in text:
        print(f"{path}: possible mojibake marker found")
        failed = True

raise SystemExit(1 if failed else 0)
PY
```

本地运行应用包版本一致性检查：

```bash
python3 - <<'PY'
import re
from pathlib import Path

workflow = Path(".github/workflows/test_release.yml").read_text(encoding="utf-8")
version_pairs = {
    (this_pack_nvidia_driver_version, this_pack_version)
    for this_pack_version, this_pack_nvidia_driver_version in re.findall(
        r'^\s+- this_pack_version: "([^"]+)"\n\s+this_pack_nvidia_driver_version: "([^"]+)"',
        workflow,
        flags=re.M,
    )
}
expected_packages = {}
for this_pack_nvidia_driver_version, this_pack_version in version_pairs:
    previous = expected_packages.setdefault(this_pack_nvidia_driver_version, this_pack_version)
    if previous != this_pack_version:
        print(f"{this_pack_nvidia_driver_version}: multiple package versions found: {previous}, {this_pack_version}")
        raise SystemExit(1)
paths = [
    Path("readme.md"),
    Path("docs/usage.md"),
    Path("docs/maintenance.md"),
    Path("CLAUDE.md"),
    Path(".github/workflows/test_release.yml"),
]

failed = False
for path in paths:
    text = path.read_text(encoding="utf-8")
    for this_pack_nvidia_driver_version, this_pack_version in sorted(expected_packages.items()):
        version_pattern = re.compile(rf'{re.escape(this_pack_nvidia_driver_version)}-\d+(?![\d.])')
        for match in sorted(set(version_pattern.findall(text))):
            if match != this_pack_version:
                print(f"{path}: package version {match} does not match {this_pack_nvidia_driver_version} package version {this_pack_version}")
                failed = True
raise SystemExit(1 if failed else 0)
PY
```

本地运行 Python patch 脚本语法检查：

```bash
python3 -m py_compile scripts/patch-nvidia-grid-kernel-binary.py
```

本地运行全部包生命周期脚本的 shell 语法检查：

```bash
find package_kernel_space/cmd package_user_space/cmd -maxdepth 1 -type f -print0 |
  while IFS= read -r -d '' file; do
    first_line="$(head -n 1 "$file")"
    if [ "$first_line" = "#!/bin/bash" ] || [ "$first_line" = "#!/bin/sh" ]; then
      echo "bash -n $file"
      bash -n "$file"
    fi
  done
```

迭代单个生命周期脚本时可直接检查目标文件：

```bash
bash -n package_kernel_space/cmd/main
bash -n package_user_space/cmd/main
bash -n package_user_space/cmd/write_gridd_conf
```

构建和发布打包由 GitHub Actions 编排，不是由仓库内的本地构建脚本完成。入口 workflow 是 `.github/workflows/test_release.yml`：`make_release=false` 时只构建 `.tgz` artifacts，不创建 release；`make_release=true` 时会创建按北京时间命名的 prerelease，例如 tag `2026.05.26-20-03-42`、title `fnnas.appstore.driver.gpu.nvidia.grid 2026.05.26 20:03:42`，将待上传产物从 `.tgz` 改名为 `.tgz.fpk`，再把当前矩阵中所有驱动版本的资产上传到同一个 GitHub Release。

## 高层架构

这个仓库的核心是 GitHub Actions artifact 流水线，加上两套 FNOS 应用包目录。

`.github/workflows/test_release.yml` 是总入口。它集中维护项目名、包名和驱动版本矩阵，矩阵中包含应用包版本、NVIDIA 驱动版本、GRID runfile 下载地址和文件名，以及可选的 NVLTS 版本。它依次调用复用 workflow 来准备 NVIDIA GRID 安装器、为 `580.159.03-3` 准备 NVLTS、构建内核空间包、打包用户空间包，并在需要时创建一个时间戳 release，把下载到 `release-assets/` 的 `.tgz` artifact 改名为 `.tgz.fpk` 后上传。

`.github/workflows/nvidia-grid-kernel-src.yml` 下载 NVIDIA GRID `.run` 安装器，将其解包到 `drvpkg`，通过 `python3 scripts/patch-nvidia-grid-kernel-binary.py` 尝试修改 `drvpkg/kernel/nvidia/nv-kernel.o_binary`，再按驱动版本发布三个 artifact：`nvidia-grid-kernel-src-<driver>` 保存 kernel source，`nvidia-grid-firmware-<driver>` 保存 firmware，`nvidia-grid-runfile-<driver>` 保存原始 `.run` 文件。patch 逻辑是 pattern 命中多少就替换多少；未命中的 pattern 会按名称输出 warning；脚本级失败也只输出 warning 并继续构建。

`.github/workflows/kernel_space.yml` 在 FNOS 内核头文件容器中编译 NVIDIA 内核模块。当前 matrix 覆盖 `6.18.18-trim-427-amd64`、`6.18.18-trim-570-amd64`、`6.18.18-trim-587-amd64` 和 `6.18.18-trim-717-amd64`。每个目标都会在解包出的 NVIDIA `kernel/` 目录中执行 `make -j"$(nproc)"`，把生成的 `*.ko` 复制到 `app/app/appstore.driver.gpu.nvidia.ko_<kernel-name>/`，恢复 firmware 到 `app/app/firmware/`，替换 manifest 和脚本占位符，生成 `app.tgz`，最后上传 `.tgz` 内核空间驱动包 artifact；Release 上传前由 `test_release.yml` 改名为 `.tgz.fpk`。

`.github/workflows/user_space.yml` 负责用户空间包。它把当前驱动版本对应的 NVIDIA GRID runfile 恢复到 `app/app/`，并仅在 `enable_nvlts=true` 时把 `nvlts-<driver>` 恢复到 `app/app/nvlts/`、验证 `nvlts` 二进制和 `configs` 目录存在。随后替换 manifest 和脚本占位符，生成 `app.tgz`，最后上传 `appstore.driver.gpu.nvidia.user-<version>-x86.tgz` artifact；Release 上传前由 `test_release.yml` 改名为 `appstore.driver.gpu.nvidia.user-<version>-x86.tgz.fpk`。

`package_kernel_space/` 保存内核空间 FNOS 应用的 manifest、配置和生命周期脚本。`cmd/main start` 会安装 firmware，根据 `uname -r`、`uname -v` 中的 build number 和系统架构选择包内模块目录，把模块安装到解析出的 TRIM 模块根目录，切换 `alternatives/nvidia-gpu` 到 `../nvidia-gpu-kernel-grid`，执行 `depmod`，禁用 nouveau，并执行 `update-initramfs -u`。`cmd/main status` 检查链接到的 `nvidia.ko` 版本和 firmware 目录。`cmd/uninstall_init` 与 `cmd/upgrade_init` 调用 `restore_default_module_package`，仅当 alternatives 仍指向 `../nvidia-gpu-kernel-grid` 时恢复到已有 `../nvidia-gpu-proprietary`，再删除 GRID 模块目录并按需执行 `depmod` 和 `update-initramfs -u`。

`package_user_space/` 保存用户空间 FNOS 应用的 manifest、配置和生命周期脚本。`cmd/main start` 会先检查 `/proc/driver/nvidia/version` 是否匹配 `EXPECTED_DRIVER_VERSION`，再以 `--no-kernel-modules` 和 `--no-dkms` 方式运行 NVIDIA 安装器。`ENABLE_NVLTS=true` 时会安装 NVLTS 到 `/opt/nvlts`，通过 `cmd/write_gridd_conf` 写入 `/etc/nvidia/gridd.conf`，安装 `nvidia-gridd` systemd drop-in，启用并重启 `nvidia-gridd`；当前只有 `580.159.03-3` 启用。最后在相关 FNOS 服务存在时重启它们。`cmd/main status` 检查 `/usr/lib/x86_64-linux-gnu/libnvidia-ml.so.<version>`。用户空间包的卸载和升级入口都会执行 `.run --uninstall` 流程，并仅在启用 NVLTS 时清理 NVLTS 文件和 systemd drop-in。

`app/` 是 CI 打包 `app.tgz` 时使用的暂存目录。仓库中只提交 `.gitkeep` 来保留 `app/app` 和 `app/ui` 目录；NVIDIA 安装器、firmware、kernel modules、NVLTS 文件和最终 tarball 都是 CI 产物，不是源码文件。

## 版本和兼容性维护点

更新 NVIDIA 驱动或应用包版本时，至少要同步检查这些位置：

- `.github/workflows/test_release.yml`：`this_pack_nvidia_driver_version` 是 NVIDIA 驱动版本，例如 `580.159.03`；`this_pack_version` 是应用包版本，例如 `580.159.03-3`。同一 NVIDIA 驱动版本下只发包修订时，只递增 `-1`、`-2`、`-3` 这类应用包修订号；升级 NVIDIA 驱动时才同步改变前面的驱动版本号。
- `.github/workflows/test_release.yml`：还要同步维护 `this_pack_nvidia_driver_page_url`、`this_pack_grid_download_url`、`this_pack_grid_run`，以及需要固定 NVLTS 版本时的 `this_pack_nvlts_version`。新增驱动版本时，需要同步维护准备驱动包、内核空间打包、用户空间打包、创建 release、上传 asset 和校验 asset 的 matrix。
- `scripts/patch-nvidia-grid-kernel-binary.py`：升级 NVIDIA GRID runfile 时需要复核 patch rules 是否仍适配。pattern 未命中会按名称输出 warning 且不阻塞构建，检查构建日志时要确认实际命中和替换情况。
- `package_kernel_space/cmd/common` 和 `package_user_space/cmd/common`：`EXPECTED_DRIVER_VERSION` 占位符由 CI 替换，必须和 workflow 输入保持一致。
- `package_user_space/cmd/common`：`NVIDIA_RUN_FILE` 由 `this_pack_grid_run` 替换。
- `package_kernel_space/manifest` 和 `package_user_space/manifest`：占位符名称要和 workflow 中的 `sed` 替换逻辑保持一致。
- 新增内核构建目标时，需要同步修改 `.github/workflows/kernel_space.yml` 的 matrix、`.github/workflows/test_release.yml` 的 release 上传 matrix，以及 `package_kernel_space/cmd/main` 中的运行时选择逻辑。release 上传流程应继续保持先下载 `.tgz` artifact，再改名并上传 `.tgz.fpk`。

内核空间和用户空间驱动版本必须一致。客户机 GRID 驱动还必须与 `readme.md` 和 `docs/usage.md` 中记录的宿主机 vGPU KVM 驱动分支匹配。本项目与飞牛官方应用中心 NVIDIA 驱动冲突，不应同时安装或启用。
