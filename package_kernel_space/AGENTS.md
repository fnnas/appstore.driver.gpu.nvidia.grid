# KERNEL PACKAGE KNOWLEDGE BASE

## OVERVIEW

这里是 FNOS 内核空间驱动包模板，负责安装 NVIDIA kernel modules 和 firmware，并接管 FNOS/TRIM 的 NVIDIA module alternatives。

## STRUCTURE

```text
package_kernel_space/
├── manifest          # CI 渲染版本、驱动 URL、平台和内核包名
├── cmd/common        # 共享变量、日志、模块根目录解析、保守恢复 alternatives
├── cmd/main          # start/status/stop 主入口
├── cmd/uninstall_*   # 卸载生命周期入口
├── cmd/upgrade_*     # 升级生命周期入口
└── config/           # FNOS 应用权限和资源配置
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 运行时选择内核模块目录 | `cmd/main` | `kernel_package_version()` 按 `uname -r`、build number、架构选择。 |
| 解析 TRIM 模块根目录 | `cmd/common` | 优先跟随 `/lib/modules/.../updates/trim/alternatives`，再按版本/build fallback。 |
| 安装 firmware | `cmd/main` | 来源 `${TRIM_APPDEST}/app/firmware`，目标 `/usr/lib/firmware/nvidia/<version>`。 |
| 切换 alternatives | `cmd/main`、`cmd/common` | 安装切到 `../nvidia-gpu-kernel-grid`；卸载/升级仅在当前仍指向 GRID 时恢复到已有 `../nvidia-gpu-proprietary`。 |
| 禁用 nouveau | `cmd/common` | 写 `/etc/modprobe.d/blacklist-nouveau.conf`。 |
| 渲染 manifest 和版本 | `.github/workflows/kernel_space.yml` | 替换 manifest 和 `cmd/common` 中的占位符。 |

## RUNTIME CONTRACT

- 当前支持内核版本接受 `6.18.18-trim`；`#788` 起接受 `6.18.18.c<N>-trim`，运行时统一映射到 `6.18.18-trim-<build>-<arch>` 包内模块目录。
- build `< 570` 使用 `6.18.18-trim-427-<arch>`。
- build `570 <= x < 587` 使用 `6.18.18-trim-570-<arch>`。
- build `587 <= x < 717` 使用 `6.18.18-trim-587-<arch>`。
- build `717 <= x < 788` 使用 `6.18.18-trim-717-<arch>`。
- build `>= 788` 使用 `6.18.18-trim-717-<arch>`，运行时内核版本可能是 `6.18.18.c<N>-trim`。
- `nvidia.ko` 中读到的 module version 必须等于 `EXPECTED_DRIVER_VERSION`。

## CONVENTIONS

- `EXPECTED_DRIVER_VERSION="this_pack_nvidia_driver_version"` 是 CI 占位符。
- `PROJ_NAME="appstore.driver.gpu.nvidia.ko"` 参与包内模块目录命名。
- `kernel_space.yml` 上传 `.tgz` artifact，`test_release.yml` 发布 Release 前改名为 `.tgz.fpk`。
- 所有错误既写 `LOG_FILE`，也在 `TRIM_TEMP_LOGFILE` 存在时写给 FNOS UI。
- `status` 成功返回 `0`，未就绪返回 `3`。

## ANTI-PATTERNS

- 不要新增内核构建目标而不更新 `cmd/main` 的 build number 选择逻辑。
- 不要删除卸载/升级阶段的 `restore_default_module_package`，否则可能把系统 alternatives 留在 GRID 模块上。
- 不要在卸载/升级阶段强制创建 alternatives 目录或覆盖非 GRID 目标；只能撤销本包仍在接管的状态。
- 不要跳过 `depmod` 或 `update-initramfs -u`。
- 不要硬编码 firmware 文件名；workflow 恢复的是完整 firmware 目录。

## VALIDATION

```bash
bash -n package_kernel_space/cmd/main
bash -n package_kernel_space/cmd/common
bash -n package_kernel_space/cmd/uninstall_init
bash -n package_kernel_space/cmd/upgrade_init
```
