# PROJECT KNOWLEDGE BASE

**Generated:** 2026-05-18

## OVERVIEW

本仓库构建面向 FNOS / 飞牛 NAS vGPU 场景的 NVIDIA GRID 驱动应用包。产物分为内核空间包 `appstore.driver.gpu.nvidia.ko` 和用户空间包 `appstore.driver.gpu.nvidia.user`，两者驱动版本必须一致。

## STRUCTURE

```text
./
├── .github/workflows/      # GitHub Actions 构建、打包、发布和静态检查入口
├── package_kernel_space/   # FNOS 内核空间应用包模板和生命周期脚本
├── package_user_space/     # FNOS 用户空间应用包模板、NVLTS 和 gridd 配置脚本
├── scripts/                # NVIDIA GRID kernel binary patch 脚本
├── docs/                   # 用户安装教程和维护文档
└── app/                    # CI 打包暂存目录，只提交 .gitkeep
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 调整驱动版本、包版本、GRID runfile 或 NVLTS | `.github/workflows/test_release.yml` | 驱动版本清单使用 `this_pack_version`、`this_pack_nvidia_driver_version`、`this_pack_grid_download_url`、`this_pack_grid_run`。 |
| 修改内核模块构建目标 | `.github/workflows/kernel_space.yml`、`.github/workflows/test_release.yml`、`package_kernel_space/cmd/main` | matrix、release 上传 matrix、运行时选择逻辑必须同步。 |
| 修改用户空间打包流程 | `.github/workflows/user_space.yml`、`package_user_space/cmd/common` | `.run` 文件名由 `this_pack_grid_run` 渲染。 |
| 修改 FNOS 内核空间安装行为 | `package_kernel_space/cmd/main`、`package_kernel_space/cmd/common` | 涉及 firmware、alternatives、`depmod`、nouveau blacklist、initramfs。 |
| 修改 FNOS 用户空间安装行为 | `package_user_space/cmd/main`、`package_user_space/cmd/common`、`package_user_space/cmd/write_gridd_conf` | 先校验内核驱动版本，再安装用户空间驱动；NVLTS 仅 580 包启用。 |
| 修改 NVIDIA binary patch 规则 | `scripts/patch-nvidia-grid-kernel-binary.py` | pattern 未命中只 warning，不阻塞 CI。 |
| 修改用户文档 | `readme.md`、`docs/usage.md`、`docs/maintenance.md` | 版本号必须和 workflow 保持一致。 |

## CURRENT VERSION CONTRACT

- 当前支持 GRID 19.5：宿主机示例 `580.159.01`，客户机 `580.159.03`，应用包版本 `580.159.03-3`。
- 当前支持 GRID 16.14：宿主机示例 `535.309.01`，客户机 `535.309.01`，应用包版本 `535.309.01-1`。
- 支持内核：`6.18.18-trim`。
- 当前内核包分组：`427`、`570`、`587`。

同一 NVIDIA 驱动版本下只发包修订时，只递增应用包版本后缀，例如 `-2` 到 `-3`。升级 NVIDIA 驱动时才同步改变前面的驱动版本号。

## CONVENTIONS

- 面向用户的说明、计划、总结、代码审查意见和新增/修改项目文档使用中文。
- `package_kernel_space/cmd/common` 和 `package_user_space/cmd/common` 中的 `EXPECTED_DRIVER_VERSION` 是 CI 渲染占位符，不要手工写死发布值。
- manifest 占位符名称必须和 workflow 中 `sed` 替换逻辑保持一致。
- `app/app` 和 `app/ui` 是 CI 打包暂存目录；源码中只保留 `.gitkeep`。
- GitHub Actions 中间 artifact 使用 `.tgz`，GitHub Release 上传前必须改名为 `.tgz.fpk`。
- 本仓库没有 package manager 配置，也没有常规本地测试框架；以 `.github/workflows/static_checks.yml` 为静态检查权威来源。
- shell 生命周期脚本没有 `.sh` 后缀；按 shebang 和 `bash -n` 识别，不要只搜索 `*.sh`。

## ANTI-PATTERNS

- 不要只改 README 或 docs 中的版本号而不改 `.github/workflows/test_release.yml`。
- 不要让内核空间包和用户空间包的 NVIDIA 驱动版本不一致。
- 不要把 NVIDIA `.run`、firmware、kernel modules、NVLTS 文件或最终 `.tgz` / `.tgz.fpk` 产物提交进源码。
- 不要把本项目驱动和飞牛官方应用中心 NVIDIA 驱动描述为可共存；它们冲突。
- 不要把 patch pattern 未命中当成 CI 硬失败；当前设计是输出 warning 并继续构建。
- 不要把 `downloads/`、`drvpkg/`、`kernel/`、`release-assets/`、`*.tgz`、`*.run`、`package_*/app.tgz` 当作源码维护。
- 不要把 `.idea/`、`.opencode/`、`.sisyphus/`、`.DS_Store`、`Thumbs.db` 写入项目知识库。

## COMMANDS

```bash
# UTF-8、乱码标记、版本一致性、Python 语法、shell 语法的权威 CI 定义
cat .github/workflows/static_checks.yml

# Python patch 脚本语法检查
python3 -m py_compile scripts/patch-nvidia-grid-kernel-binary.py

# 单个生命周期脚本语法检查
bash -n package_kernel_space/cmd/main
bash -n package_user_space/cmd/main
bash -n package_user_space/cmd/write_gridd_conf
```

Windows/Git Bash 环境中，如果 `python3` 不存在可改用 `python`；如果 `find` 被解析成 Windows `FIND.EXE`，使用 `/usr/bin/find`。

## NOTES

- GitHub Actions 是构建和发布入口，本地没有等价的一键构建脚本。
- `make_release=false` 只构建 `.tgz` artifacts；`make_release=true` 会创建 prerelease，并在上传前把 `.tgz` 改名为 `.tgz.fpk`。
- `gh release upload --clobber` 会覆盖同名 release asset，开启 `make_release=true` 前先确认版本号和产物名。
- 用户安装顺序是内核空间包、重启、确认 `/proc/driver/nvidia/version`、再安装用户空间包。
- GitHub Release 资产应直接使用 `.tgz.fpk` 扩展名；只有调试 Actions artifact 或历史 `.tgz` 产物时才需要手动改名。
