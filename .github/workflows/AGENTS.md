# WORKFLOW KNOWLEDGE BASE

## OVERVIEW

这里是仓库的构建、打包、发布和静态检查编排层。所有版本变量从 `test_release.yml` 汇总后传入复用 workflow。

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 总入口和版本变量 | `test_release.yml` | `proj_name`、包名、驱动版本、runfile URL、NVLTS 版本都在 `env`。 |
| 准备 NVIDIA GRID 安装器 | `nvidia-grid-kernel-src.yml` | 下载 `.run`、解包 `drvpkg`、执行 binary patch、上传源码/firmware/runfile artifact。 |
| 准备 NVLTS | `nvlts.yml` | 未指定版本时从 GitLab API 解析最新 release。 |
| 编译内核模块 | `kernel_space.yml` | matrix 使用 FNOS 内核头文件容器。 |
| 打包用户空间包 | `user_space.yml` | 恢复 `.run` 和 `nvlts` artifact 后生成用户空间 `.tgz`。 |
| 静态检查 | `static_checks.yml` | 文档 UTF-8、版本一致性、Python 语法、shell 语法。 |

## ARTIFACT FLOW

```text
test_release.yml
├── nvidia-grid-kernel-src.yml
│   ├── nvidia-grid-kernel-src  -> kernel_space.yml
│   ├── nvidia-grid-firmware    -> kernel_space.yml
│   └── nvidia-grid-runfile     -> user_space.yml
├── nvlts.yml
│   └── nvlts                  -> user_space.yml
├── kernel_space.yml            -> appstore.driver.gpu.nvidia.ko-<version>-<kernel>.tgz
└── user_space.yml              -> appstore.driver.gpu.nvidia.user-<version>-x86.tgz
```

## CONVENTIONS

- `this_pack_version` 是应用包版本，例如 `580.159.03-2`。
- `this_pack_nvidia_driver_version` 是 NVIDIA 驱动版本，例如 `580.159.03`。
- `this_pack_grid_run` 必须和下载 URL 最终文件名、用户空间 `cmd/common` 渲染结果一致。
- 内核空间包 release 上传 matrix 必须覆盖 `kernel_space.yml` 的全部 matrix。
- `manifest_platform` 当前为应用中心 `x86`，内核构建架构当前为 `amd64`。

## ANTI-PATTERNS

- 新增内核 matrix 后不要漏改 `test_release.yml` 的 release asset matrix。
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
