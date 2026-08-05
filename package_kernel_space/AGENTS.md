# KERNEL PACKAGE KNOWLEDGE BASE

## OVERVIEW

这里是 FNOS 内核空间驱动包模板，负责安装 NVIDIA kernel modules 和 firmware，并接管 FNOS/TRIM 的 NVIDIA module alternatives。

## STRUCTURE

```text
package_kernel_space/
├── manifest          # CI 渲染版本、驱动 URL、平台和内核包名
├── cmd/common        # 共享变量、日志、模块根目录解析、保守恢复 alternatives
├── cmd/main          # start/status/stop 主入口
├── cmd/build_module_chroot # 独立的本机 overlay/chroot 编译脚本
├── cmd/uninstall_*   # 卸载生命周期入口
├── cmd/upgrade_*     # 升级生命周期入口
└── config/           # FNOS 应用权限和资源配置
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 运行时选择内核模块目录 | `cmd/main` | 旧 `6.18.18-trim` 按 build number 分组；其他内核按 `<uname -r>-<arch>` 包内目录。 |
| 解析 TRIM 模块根目录 | `cmd/common` | 优先跟随 `/lib/modules/.../updates/trim/alternatives`，再按版本/build fallback。 |
| 安装 firmware | `cmd/main` | 来源 `${TRIM_APPDEST}/app/firmware`，目标 `/usr/lib/firmware/nvidia/<version>`。 |
| chroot 源码构建 | `cmd/main`、`cmd/build_module_chroot` | 预构建 `nvidia.ko` 缺失且包内有源码时编译，产物仍写入 `source_module_dir`。 |
| 切换 alternatives | `cmd/main`、`cmd/common` | 安装切到 `../nvidia-gpu-kernel-grid`；卸载/升级仅在当前仍指向 GRID 时恢复到已有 `../nvidia-gpu-proprietary`。 |
| 禁用 nouveau | `cmd/common` | 写 `/etc/modprobe.d/blacklist-nouveau.conf`。 |
| 渲染 manifest 和版本 | `.github/workflows/kernel_space.yml` | 替换 manifest 和 `cmd/common` 中的占位符。 |

## RUNTIME CONTRACT

- 旧 `6.18.18-trim` 仍按 build number 分组，兼容既有 `427`、`570`、`587`、`717` 包。
- 其他内核版本直接映射到 `<uname -r>-<arch>` 包内模块目录；目录不存在时安装阶段报错退出。
- build `< 570` 使用 `6.18.18-trim-427-<arch>`。
- build `570 <= x < 587` 使用 `6.18.18-trim-570-<arch>`。
- build `587 <= x < 717` 使用 `6.18.18-trim-587-<arch>`。
- build `>= 717` 使用 `6.18.18-trim-717-<arch>`。
- 例如 `6.18.18.c788-trim` 使用 `6.18.18.c788-trim-<arch>`，`6.18.18.c877-trim` 使用 `6.18.18.c877-trim-<arch>`，`6.18.18.c938-trim` 使用 `6.18.18.c938-trim-<arch>`，`6.18.18.c952-trim` 使用 `6.18.18.c952-trim-<arch>`。
- `nvidia.ko` 中读到的 module version 必须等于 `EXPECTED_DRIVER_VERSION`。
- 包内源码固定为 `app/nvidia-kernel-source/kernel`；没有预构建模块且没有源码时继续进入既有安装检查并失败。
- chroot 失败锁为 `/tmp/appstore.driver.gpu.nvidia.ko-chroot-build.failed`，失败或中断时保留，成功、更新和卸载时清除。

## CONVENTIONS

- `EXPECTED_DRIVER_VERSION="this_pack_nvidia_driver_version"` 是 CI 占位符。
- `PROJ_NAME="appstore.driver.gpu.nvidia.ko"` 参与包内模块目录命名。
- `kernel_space.yml` 上传 `nvidia.ko-<version>-<target>.tgz` artifact，`test_release.yml` 发布 Release 前改名为 `.tgz.fpk`；FNOS `appname` 和包内模块目录前缀仍使用 `appstore.driver.gpu.nvidia.ko`。
- 所有错误既写 `LOG_FILE`，也在 `TRIM_TEMP_LOGFILE` 存在时写给 FNOS UI。
- chroot 构建输出通过 `run_with_user_visible_log` 同时写控制台、`LOG_FILE` 和 FNOS UI 日志。
- `status` 成功返回 `0`，未就绪返回 `3`。

## ANTI-PATTERNS

- 不要新增内核构建目标而不更新 workflow matrix 和 release asset matrix；只有旧 `6.18.18-trim` 的同名 build 分组需要改运行时逻辑。
- 不要删除卸载/升级阶段的 `restore_default_module_package`，否则可能把系统 alternatives 留在 GRID 模块上。
- 不要在卸载/升级阶段强制创建 alternatives 目录或覆盖非 GRID 目标；只能撤销本包仍在接管的状态。
- 不要跳过 `depmod` 或 `update-initramfs -u`。
- 不要硬编码 firmware 文件名；workflow 恢复的是完整 firmware 目录。
- 不要让 `chroot-amd64` 包携带任何预构建 `.ko`，也不要把 chroot 编译脚本耦合到模块安装逻辑。

## VALIDATION

```bash
bash -n package_kernel_space/cmd/main
bash -n package_kernel_space/cmd/common
bash -n package_kernel_space/cmd/build_module_chroot
bash -n package_kernel_space/cmd/uninstall_init
bash -n package_kernel_space/cmd/upgrade_init
```
