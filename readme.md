# appstore.driver.gpu.nvidia.grid

这是一个面向 FNOS / 飞牛 NAS vGPU 场景的 NVIDIA GRID 驱动应用包项目。

项目提供两个应用包：

- `appstore.driver.gpu.nvidia.ko`：内核空间驱动包，负责安装 NVIDIA kernel module 和 firmware。
- `appstore.driver.gpu.nvidia.user`：用户空间驱动包，负责安装 NVIDIA 用户空间库、`nvidia-smi`、`nvidia-gridd` 和 NVLTS。

Release 下载文件名分别以 `nvidia.ko-` 和 `nvidia.user-` 开头；上述 `appstore.driver.gpu.*` 名称是安装后使用的 FNOS 应用标识。

## 当前支持版本

| vGPU 分支 | 宿主机 vGPU KVM 驱动 | 客户机 GRID 驱动 | 应用包版本 |
| --- | --- | --- | --- |
| GRID 19.5 | `580.159.01` | `580.159.03` | `580.159.03-3` |
| GRID 16.14 | `535.309.01` | `535.309.01` | `535.309.01-1` |

- 已构建内核包：`6.18.18-trim`、`6.18.18.c788-trim`、`6.18.18.c877-trim`、`6.18.18.c938-trim`、`6.18.18.c952-trim`、`6.18.18.c1032-trim`
- chroot 源码包：每个驱动版本额外提供一个 `chroot-amd64` 包，用于本机编译当前内核模块
- 支持架构：`x86`

## 文档入口

- 新手安装和使用教程：[docs/usage.md](docs/usage.md)
- 项目维护和构建说明：[docs/maintenance.md](docs/maintenance.md)

## 下载哪个包

每次安装至少需要下载两个包：

1. 一个内核空间驱动包。优先根据 FNOS 内核版本选择预构建包；没有匹配的预构建包时可选择同驱动版本的 `chroot-amd64` 源码包。
2. 一个同版本用户空间驱动包，例如 `nvidia.user-580.159.03-3-x86.tgz.fpk`。

内核驱动包选择规则：先确认 `uname -r`。旧 `6.18.18-trim` 因为同一内核名下存在多组 build，需要再按 build number 选择 `427`、`570`、`587` 或 `717` 包。其他带构建号的完整内核名直接按 `uname -r` 选择，例如 `6.18.18.c1032-trim` 选择 `6.18.18.c1032-trim-amd64` 包。没有对应预构建包时，可改用 `chroot-amd64` 源码包。

当前已构建内核包选择规则：

| 当前内核版本         | 当前内核 build number | 应选择的内核驱动包                                                               |
|----------------|-------------------|-------------------------------------------------------------------------|
| `6.18.18-trim` | `#427` 到 `#569`   | `nvidia.ko-580.159.03-3-6.18.18-trim-427-amd64.tgz.fpk` |
| `6.18.18-trim` | `#570` 到 `#586`   | `nvidia.ko-580.159.03-3-6.18.18-trim-570-amd64.tgz.fpk` |
| `6.18.18-trim` | `#587` 到 `#716`   | `nvidia.ko-580.159.03-3-6.18.18-trim-587-amd64.tgz.fpk` |
| `6.18.18-trim` | `#717` 到 `#787`   | `nvidia.ko-580.159.03-3-6.18.18-trim-717-amd64.tgz.fpk` |
| `6.18.18.c788-trim` | `#788`        | `nvidia.ko-580.159.03-3-6.18.18.c788-trim-amd64.tgz.fpk` |
| `6.18.18.c877-trim` | `#877`        | `nvidia.ko-580.159.03-3-6.18.18.c877-trim-amd64.tgz.fpk` |
| `6.18.18.c938-trim` | `#938`        | `nvidia.ko-580.159.03-3-6.18.18.c938-trim-amd64.tgz.fpk` |
| `6.18.18.c952-trim` | `#952`        | `nvidia.ko-580.159.03-3-6.18.18.c952-trim-amd64.tgz.fpk` |
| `6.18.18.c1032-trim` | `#1032`      | `nvidia.ko-580.159.03-3-6.18.18.c1032-trim-amd64.tgz.fpk` |

源码兜底包不包含任何预构建 `.ko`，安装时会在隔离的 chroot 中联网安装最小编译依赖，并把针对当前内核构建的模块写入既有模块目录后继续原安装流程：

```text
nvidia.ko-580.159.03-3-chroot-amd64.tgz.fpk
```

应优先使用匹配的预构建包。chroot 编译要求系统有可用的当前内核头文件、网络连接和足够磁盘空间，耗时也明显更长。

如果使用 GRID 16.14 / `535.309.01` 版本，包名中的应用包版本需要同步换成 `535.309.01-1`，例如：

```text
nvidia.ko-535.309.01-1-6.18.18-trim-427-amd64.tgz.fpk
nvidia.ko-535.309.01-1-6.18.18.c788-trim-amd64.tgz.fpk
nvidia.ko-535.309.01-1-6.18.18.c877-trim-amd64.tgz.fpk
nvidia.ko-535.309.01-1-6.18.18.c938-trim-amd64.tgz.fpk
nvidia.ko-535.309.01-1-6.18.18.c952-trim-amd64.tgz.fpk
nvidia.ko-535.309.01-1-6.18.18.c1032-trim-amd64.tgz.fpk
nvidia.ko-535.309.01-1-chroot-amd64.tgz.fpk
nvidia.user-535.309.01-1-x86.tgz.fpk
```

安装前在 FNOS 控制台或 SSH 中执行：

```bash
uname -a
```

根据输出中的内核版本选择对应内核包；只有 `uname -r` 为 `6.18.18-trim` 时，才需要再根据 `#473`、`#570`、`#587`、`#717` 等 build number 选择分组包。

## 安装顺序

正确顺序是：

1. 给 FNOS 虚拟机打快照。
2. 安装内核空间驱动包 `appstore.driver.gpu.nvidia.ko`。
3. 重启 FNOS。
4. 确认 `/proc/driver/nvidia/version` 显示已安装的驱动版本，例如 `580.159.03` 或 `535.309.01`。
5. 安装用户空间驱动包 `appstore.driver.gpu.nvidia.user`。
6. 用 `nvidia-smi` 和系统资源管理器确认 GPU 正常工作。

详细截图教程见：[docs/usage.md](docs/usage.md)

## 重要提醒

- 宿主机 vGPU KVM 驱动和 FNOS 客户机 GRID 驱动必须来自匹配的 NVIDIA vGPU 驱动版本组合。
- 本项目驱动与飞牛官方应用中心的 NVIDIA 驱动冲突，不要同时安装或启用。
- 内核空间驱动和用户空间驱动版本必须一致，不能混装 `580.159.03` 和 `535.309.01`。
- chroot 编译失败或中断后会保留 `/tmp/appstore.driver.gpu.nvidia.ko-chroot-build.failed`，避免启动时反复编译；重启、手动删除该文件、更新或卸载内核包后才会允许重试。
- 安装会修改内核模块 alternatives、firmware、nouveau blacklist、initramfs 和 NVIDIA 用户空间库，安装前请务必创建虚拟机快照。

## Release

发布包在 GitHub Releases 中下载：

```text
https://github.com/fnnas/appstore.driver.gpu.nvidia.grid/releases
```

GitHub Release 中的安装包会以 `.tgz.fpk` 扩展名发布，可直接用于 FNOS 本地安装。只有下载 GitHub Actions artifact 或历史 `.tgz` 产物时，才需要手动改名为 `.tgz.fpk`。
