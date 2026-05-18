# USER PACKAGE KNOWLEDGE BASE

## OVERVIEW

这里是 FNOS 用户空间驱动包模板，负责安装 NVIDIA 用户空间库、`nvidia-smi`、`nvidia-gridd` 和 NVLTS，不编译也不安装内核模块。

## STRUCTURE

```text
package_user_space/
├── manifest              # CI 渲染版本、驱动 URL 和平台
├── cmd/common            # 共享变量、runfile 路径、NVLTS 清理、卸载逻辑
├── cmd/main              # start/status/stop 主入口
├── cmd/write_gridd_conf  # 写入 /etc/nvidia/gridd.conf
├── cmd/uninstall_*       # 卸载生命周期入口
├── cmd/upgrade_*         # 升级生命周期入口
└── config/               # FNOS 应用权限和资源配置
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 校验内核驱动版本 | `cmd/main` | 读取 `/proc/driver/nvidia/version`，必须等于 `EXPECTED_DRIVER_VERSION`。 |
| NVIDIA `.run` 安装参数 | `cmd/main` | 使用 `--no-kernel-modules` 和 `--no-dkms`。 |
| `.run` 文件名 | `cmd/common` | `NVIDIA_RUN_FILE` 由 workflow 的 `this_pack_grid_run` 渲染。 |
| NVLTS 安装 | `cmd/main` | 复制到 `/opt/nvlts`，写 systemd drop-in。 |
| gridd 配置 | `cmd/write_gridd_conf` | 默认 `FeatureType=2`，适配 RTX Virtual Workstation。 |
| 卸载清理 | `cmd/common` | `.run --uninstall` 后清理 `/opt/nvlts` 和 drop-in。 |

## RUNTIME CONTRACT

- 用户空间包必须在内核空间包安装并重启后安装。
- 安装前 `/proc/driver/nvidia/version` 必须能解析到期望驱动版本。
- NVIDIA 安装器只安装用户空间组件：`--no-kernel-modules --no-dkms`。
- `status` 只检查 `/usr/lib/x86_64-linux-gnu/libnvidia-ml.so.<version>` 是否存在。
- 安装后会重启存在的 FNOS 相关服务：`sysinfo_service`、`ai_manager`、`mediasrv`、`resmon_service`。

## CONVENTIONS

- `EXPECTED_DRIVER_VERSION` 和 `NVIDIA_RUN_FILE` 都是 CI 占位符。
- NVLTS artifact 必须包含 `nvlts` 二进制和 `configs` 目录。
- `write_gridd_conf` 使用 heredoc 覆盖 `/etc/nvidia/gridd.conf`，保留 NVIDIA 模板注释。
- 卸载失败通过 `report_error` 写日志并返回非零；清理后会 `systemctl daemon-reload`。

## ANTI-PATTERNS

- 不要让用户空间安装器安装内核模块。
- 不要跳过内核驱动版本校验，否则可能混装不同 NVIDIA 版本。
- 不要把 NVLTS 配置目录路径改到包外不可控位置。
- 不要把缺失的 FNOS 服务当成错误；当前逻辑是记录并跳过。

## VALIDATION

```bash
bash -n package_user_space/cmd/main
bash -n package_user_space/cmd/common
bash -n package_user_space/cmd/write_gridd_conf
bash -n package_user_space/cmd/uninstall_init
bash -n package_user_space/cmd/upgrade_init
```
