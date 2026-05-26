# appstore.driver.gpu.nvidia.grid

这是一个面向 FNOS / 飞牛 NAS vGPU 场景的 NVIDIA GRID 驱动应用包项目。

项目提供两个应用包：

- `appstore.driver.gpu.nvidia.ko`：内核空间驱动包，负责安装 NVIDIA kernel module 和 firmware。
- `appstore.driver.gpu.nvidia.user`：用户空间驱动包，负责安装 NVIDIA 用户空间库、`nvidia-smi`、`nvidia-gridd` 和 NVLTS。

## 当前支持版本

| vGPU 分支 | 宿主机 vGPU KVM 驱动 | 客户机 GRID 驱动 | 应用包版本 |
| --- | --- | --- | --- |
| GRID 19.5 | `580.159.01` | `580.159.03` | `580.159.03-3` |
| GRID 16.14 | `535.309.01` | `535.309.01` | `535.309.01-1` |

- 支持内核：`6.18.18-trim`
- 支持架构：`x86`

## 文档入口

- 新手安装和使用教程：[docs/usage.md](docs/usage.md)
- 项目维护和构建说明：[docs/maintenance.md](docs/maintenance.md)

## 下载哪个包

每次安装至少需要下载两个包：

1. 一个内核空间驱动包，根据 FNOS 内核版本和 build number 选择。
2. 一个同版本用户空间驱动包，例如 `appstore.driver.gpu.nvidia.user-580.159.03-3-x86.tgz.fpk`。

内核驱动包选择规则：先确认内核版本，例如 `6.18.18-trim`；再根据同一内核版本下的 build number 选择对应包。后续如果支持新的 FNOS/TRIM 内核版本，会增加新的内核版本分组。

当前 `6.18.18-trim` 内核选择规则：

| 当前内核版本         | 当前内核 build number | 应选择的内核驱动包                                                               |
|----------------|-------------------|-------------------------------------------------------------------------|
| `6.18.18-trim` | `#427` 到 `#569`   | `appstore.driver.gpu.nvidia.ko-580.159.03-3-6.18.18-trim-427-amd64.tgz.fpk` |
| `6.18.18-trim` | `#570` 到 `#586`   | `appstore.driver.gpu.nvidia.ko-580.159.03-3-6.18.18-trim-570-amd64.tgz.fpk` |
| `6.18.18-trim` | `#587` 及以上        | `appstore.driver.gpu.nvidia.ko-580.159.03-3-6.18.18-trim-587-amd64.tgz.fpk` |

如果使用 GRID 16.14 / `535.309.01` 版本，包名中的应用包版本需要同步换成 `535.309.01-1`，例如：

```text
appstore.driver.gpu.nvidia.ko-535.309.01-1-6.18.18-trim-427-amd64.tgz.fpk
appstore.driver.gpu.nvidia.user-535.309.01-1-x86.tgz.fpk
```

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
4. 确认 `/proc/driver/nvidia/version` 显示已安装的驱动版本，例如 `580.159.03` 或 `535.309.01`。
5. 安装用户空间驱动包 `appstore.driver.gpu.nvidia.user`。
6. 用 `nvidia-smi` 和系统资源管理器确认 GPU 正常工作。

详细截图教程见：[docs/usage.md](docs/usage.md)

## 重要提醒

- 宿主机 vGPU KVM 驱动和 FNOS 客户机 GRID 驱动必须来自匹配的 NVIDIA vGPU 驱动版本组合。
- 本项目驱动与飞牛官方应用中心的 NVIDIA 驱动冲突，不要同时安装或启用。
- 内核空间驱动和用户空间驱动版本必须一致，不能混装 `580.159.03` 和 `535.309.01`。
- 安装会修改内核模块 alternatives、firmware、nouveau blacklist、initramfs 和 NVIDIA 用户空间库，安装前请务必创建虚拟机快照。

## Release

发布包在 GitHub Releases 中下载：

```text
https://github.com/fnnas/appstore.driver.gpu.nvidia.grid/releases
```

GitHub Release 中的安装包会以 `.tgz.fpk` 扩展名发布，可直接用于 FNOS 本地安装。只有下载 GitHub Actions artifact 或历史 `.tgz` 产物时，才需要手动改名为 `.tgz.fpk`。
