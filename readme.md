# appstore.driver.gpu.nvidia.grid

这是一个面向 FNOS / 飞牛 NAS vGPU 场景的 NVIDIA GRID 驱动应用包项目。

项目提供两个应用包：

- `appstore.driver.gpu.nvidia.ko`：内核空间驱动包，负责安装 NVIDIA kernel module 和 firmware。
- `appstore.driver.gpu.nvidia.user`：用户空间驱动包，负责安装 NVIDIA 用户空间库、`nvidia-smi`、`nvidia-gridd` 和 NVLTS。

## 当前版本

- vGPU 分支：GRID 19.5
- 宿主机 vGPU KVM 驱动：`580.159.01`
- 客户机 GRID 驱动：`580.159.03`
- 应用包版本：`580.159.03-2`
- 支持内核：`6.18.18-trim`
- 支持架构：`x86`

## 文档入口

- 新手安装和使用教程：[docs/usage.md](docs/usage.md)
- 项目维护和构建说明：[docs/maintenance.md](docs/maintenance.md)

## 下载哪个包

每次安装至少需要下载两个包：

1. 一个内核空间驱动包，根据 FNOS 内核版本和 build number 选择。
2. 一个用户空间驱动包，固定选择 `appstore.driver.gpu.nvidia.user-580.159.03-2-x86.tgz`。

内核驱动包选择规则：先确认内核版本，例如 `6.18.18-trim`；再根据同一内核版本下的 build number 选择对应包。后续如果支持新的 FNOS/TRIM 内核版本，会增加新的内核版本分组。

当前 `6.18.18-trim` 内核选择规则：

| 当前内核版本         | 当前内核 build number | 应选择的内核驱动包                                                               |
|----------------|-------------------|-------------------------------------------------------------------------|
| `6.18.18-trim` | `#427` 到 `#569`   | `appstore.driver.gpu.nvidia.ko-580.159.03-2-6.18.18-trim-427-amd64.tgz` |
| `6.18.18-trim` | `#570` 到 `#586`   | `appstore.driver.gpu.nvidia.ko-580.159.03-2-6.18.18-trim-570-amd64.tgz` |
| `6.18.18-trim` | `#587` 及以上        | `appstore.driver.gpu.nvidia.ko-580.159.03-2-6.18.18-trim-587-amd64.tgz` |

安装前在 FNOS 控制台或 SSH 中执行：

```bash
uname -a
```

根据输出中的内核版本和 `#473`、`#570`、`#587` 等 build number 选择对应内核包。

## 安装顺序

正确顺序是：

1. 给 FNOS 虚拟机打快照。
2. 安装内核空间驱动包 `appstore.driver.gpu.nvidia.ko`。
3. 重启 FNOS。
4. 确认 `/proc/driver/nvidia/version` 显示 `580.159.03`。
5. 安装用户空间驱动包 `appstore.driver.gpu.nvidia.user`。
6. 用 `nvidia-smi` 和系统资源管理器确认 GPU 正常工作。

详细截图教程见：[docs/usage.md](docs/usage.md)

## 重要提醒

- 宿主机 vGPU KVM 驱动和 FNOS 客户机 GRID 驱动必须来自匹配的 NVIDIA vGPU 驱动版本组合。本文当前组合属于 GRID 19.5。
- 本项目驱动与飞牛官方应用中心的 NVIDIA 驱动冲突，不要同时安装或启用。
- 内核空间驱动和用户空间驱动版本必须一致，当前均为 `580.159.03`。
- 安装会修改内核模块 alternatives、firmware、nouveau blacklist、initramfs 和 NVIDIA 用户空间库，安装前请务必创建虚拟机快照。

## Release

发布包在 GitHub Releases 中下载：

```text
https://github.com/fnnas/appstore.driver.gpu.nvidia.grid/releases
```

FNOS 本地安装时通常需要把下载到的 `.tgz` 文件改名为 `.tgz.fpk`。
