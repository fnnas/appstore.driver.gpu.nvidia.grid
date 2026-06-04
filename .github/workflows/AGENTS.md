# WORKFLOW KNOWLEDGE BASE

## OVERVIEW

这里是仓库的构建、打包、发布和静态检查编排层。所有版本变量从 `test_release.yml` 汇总后传入复用 workflow。

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 总入口和版本变量 | `test_release.yml` | 包名在 `env`，驱动版本、runfile URL、NVLTS 版本在 `plan_build` 的驱动列表。 |
| 准备 NVIDIA GRID 安装器 | `nvidia-grid-kernel-src.yml` | 下载 `.run`、解包 `drvpkg`、执行 binary patch、上传源码/firmware/runfile artifact。 |
| 准备 NVLTS | `nvlts.yml` | 未指定版本时从 GitLab API 解析最新 release。 |
| 编译内核模块 | `kernel_space.yml` | matrix 使用 FNOS 内核头文件容器。 |
| 打包用户空间包 | `user_space.yml` | 恢复 `.run` 和 `nvlts` artifact 后生成用户空间 `.tgz`。 |
| 静态检查 | `static_checks.yml` | 文档 UTF-8、版本一致性、Python 语法、shell 语法。 |

## ARTIFACT FLOW

```text
test_release.yml
├── plan_build
│   ├── driver_matrix
│   ├── nvlts_matrix
│   ├── user_matrix
│   └── release_assets_matrix
├── nvidia-grid-kernel-src.yml
│   ├── nvidia-grid-kernel-src-<driver>  -> kernel_space.yml
│   ├── nvidia-grid-firmware-<driver>    -> kernel_space.yml
│   └── nvidia-grid-runfile-<driver>     -> user_space.yml
├── nvlts.yml
│   └── nvlts-580.159.03       -> user_space.yml for 580 only
├── kernel_space.yml            -> appstore.driver.gpu.nvidia.ko-<version>-<kernel>.tgz
└── user_space.yml              -> appstore.driver.gpu.nvidia.user-<version>-x86.tgz
```

## CONVENTIONS

- `this_pack_version` 是应用包版本，例如 `580.159.03-3`。
- `this_pack_nvidia_driver_version` 是 NVIDIA 驱动版本，例如 `580.159.03`。
- `this_pack_grid_run` 必须和下载 URL 最终文件名、用户空间 `cmd/common` 渲染结果一致。
- `workflow_dispatch` 的 `build_580` / `build_535` 控制本次构建哪些 NVIDIA 驱动版本；两者不能同时为 `false`。
- `plan_build` 统一生成构建和 release 上传 matrix，新增驱动版本时优先改这里，不要在各 job 重复硬编码矩阵。
- 多个驱动版本并行构建时，源码、firmware、runfile artifact 名称必须带驱动版本后缀。
- NVLTS 当前仅 `580.159.03-3` 用户空间包启用，535 用户空间包不下载、不打包、不安装 NVLTS。
- `prune_ccache` 只按本次勾选的驱动版本清理内核 ccache；不要把未勾选版本纳入删除正则。
- `plan_build` 的 kernels 列表必须覆盖 `kernel_space.yml` 的全部内核 matrix。
- `manifest_platform` 当前为应用中心 `x86`，内核构建架构当前为 `amd64`。

## ANTI-PATTERNS

- 新增内核 matrix 后不要漏改 `test_release.yml` 的 `plan_build` kernels 列表、校验正则和 ccache 清理正则。
- 不要把 `nvidia-grid-kernel-src.yml` 中 patch 失败改成硬失败，除非同时更新维护文档和发布策略。
- 不要绕过 `static_checks.yml` 的版本一致性逻辑更新文档版本。
- 不要把下载出的 NVIDIA runfile 或 NVLTS 内容作为源码提交。

## VALIDATION

```bash
python3 -m py_compile scripts/patch-nvidia-grid-kernel-binary.py

find package_kernel_space/cmd package_user_space/cmd -maxdepth 1 -type f -print0 |
  while IFS= read -r -d '' file; do
    first_line="$(head -n 1 "$file")"
    if [ "$first_line" = "#!/bin/bash" ] || [ "$first_line" = "#!/bin/sh" ]; then
      bash -n "$file"
    fi
  done
```
