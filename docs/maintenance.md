# 维护文档

本文面向项目维护者，说明仓库结构、GitHub Actions 构建流程、包内脚本行为、版本升级时需要同步修改的位置，以及 NVIDIA 品牌素材使用说明。

普通用户安装和使用请阅读：[usage.md](usage.md)

## 项目结构

```text
.github/workflows/
  test_release.yml
  nvidia-grid-kernel-src.yml
  kernel_space.yml
  user_space.yml
  nvlts.yml
  static_checks.yml

package_kernel_space/
  manifest
  cmd/
    common
    main
    uninstall_init
    upgrade_init

package_user_space/
  manifest
  cmd/
    common
    main
    uninstall_init
    upgrade_init
    write_gridd_conf

docs/
  usage.md
  maintenance.md
  usage/
```

两个 package 的 `cmd/common` 分别保存各自生命周期脚本复用的变量、日志函数和错误展示函数。它们会随对应 package 一起打包，不依赖另一个 package。

## 当前版本

- NVIDIA GRID 客户机驱动版本：`580.159.03`
- 应用包版本：`580.159.03-2`
- vGPU 分支：GRID 19.5
- 宿主机 vGPU KVM 驱动示例：`580.159.01`
- 当前支持内核：`6.18.18-trim`
- 当前构建架构：`amd64`
- 应用中心 `platform`：`x86`

## 构建产物

GitHub Actions 会生成以下最终包：

```text
appstore.driver.gpu.nvidia.ko-580.159.03-2-6.18.18-trim-427-amd64.tgz.fpk
appstore.driver.gpu.nvidia.ko-580.159.03-2-6.18.18-trim-570-amd64.tgz.fpk
appstore.driver.gpu.nvidia.ko-580.159.03-2-6.18.18-trim-587-amd64.tgz.fpk
appstore.driver.gpu.nvidia.user-580.159.03-2-x86.tgz.fpk
```

内核空间和用户空间复用 workflow 上传到 GitHub Actions 的中间 artifact 仍是 `.tgz`。`test_release.yml` 在上传 GitHub Release 资产前，会先把下载到 `release-assets/` 的 `.tgz` 文件重命名为 `.tgz.fpk`，再执行 `gh release upload`。因此用户应从 Release 下载 `.tgz.fpk` 安装包；维护者调试 artifact 时才会直接看到 `.tgz`。

内核空间包包含：

- NVIDIA 内核模块：`app/appstore.driver.gpu.nvidia.ko_<内核版本-build-架构>/`
- NVIDIA firmware：`app/firmware/`
- 内核空间驱动包元数据和生命周期脚本：`package_kernel_space/`

用户空间包包含：

- NVIDIA `.run` 安装器：`app/NVIDIA-Linux-x86_64-580.159.03-grid.run`
- NVLTS 文件：`app/nvlts/`
- 用户空间驱动包元数据和生命周期脚本：`package_user_space/`

## Workflow 说明

### `test_release.yml`

主入口 workflow，负责整体编排：

- 定义项目名、包版本、NVIDIA 驱动下载地址、NVLTS 版本
- 调用 `nvidia-grid-kernel-src.yml` 准备 NVIDIA 源码、firmware 和 `.run` 安装器
- 调用 `nvlts.yml` 准备 NVLTS artifact
- 调用 `kernel_space.yml` 编译内核模块并打包 `package_kernel_space`
- 调用 `user_space.yml` 打包 `package_user_space`
- 可选创建 GitHub prerelease，并在上传前将 `.tgz` 产物重命名为 `.tgz.fpk`

关键变量集中维护在 `env`：

```yaml
proj_name: "appstore.driver.gpu.nvidia.grid"
kernel_module_package_name: "appstore.driver.gpu.nvidia.ko"
this_pack_version: "580.159.03-2"
this_pack_nvidia_driver_version: "580.159.03"
this_pack_nvidia_driver_url: "https://www.nvidia.com/en-us/drivers/details/267577/"
this_pack_grid_url: "https://alist.homelabproject.cc/d/foxipan/vGPU/19.5/NVIDIA-GRID-Linux-KVM-580.159.01-580.159.03-582.53/Guest_Drivers/NVIDIA-Linux-x86_64-580.159.03-grid.run"
this_pack_grid_run: "NVIDIA-Linux-x86_64-580.159.03-grid.run"
this_pack_nvlts_version: ""
```

### `nvidia-grid-kernel-src.yml`

负责准备 NVIDIA 驱动源码、firmware 和 `.run` 安装器：

- 下载并缓存 NVIDIA `.run` 文件
- 执行 `--extract-only --target drvpkg`
- 在独立的 `Patch NVIDIA kernel binary` step 中使用 `python3 scripts/patch-nvidia-grid-kernel-binary.py` 尝试 patch `drvpkg/kernel/nvidia/nv-kernel.o_binary`
- 在独立的 `Pack NVIDIA kernel source` step 中将 `drvpkg/kernel` 打包为 `nvidia-grid-kernel-src`
- 将 `drvpkg/firmware` 作为目录 artifact 上传为 `nvidia-grid-firmware`
- 将 NVIDIA `.run` 安装包上传为 `nvidia-grid-runfile`

patch 逻辑会按规则逐条匹配；命中的 pattern 会全部替换，未命中的 pattern 会按名称输出 GitHub Actions warning，但不会阻塞构建。脚本级失败同样会输出 warning，并继续使用当前 `drvpkg/kernel` 打包 artifact。

firmware 作为目录 artifact 直接恢复到最终包，不再单独压缩成 tgz。

### `nvlts.yml`

负责准备 NVLTS 服务文件：

- 默认从 `https://git.collinwebdesigns.de/vgpu/nvlts` 解析最新 release
- 下载 `nvlts_<version>_linux_amd64.tar.gz`
- 使用 cache 避免重复下载
- 解包并上传为 `nvlts` artifact
- `user_space.yml` 会将该 artifact 恢复到 `app/nvlts/` 并打入用户空间驱动包

### `kernel_space.yml`

负责内核空间驱动包的编译和打包。

当前 matrix 包含：

- `6.18.18-trim-427-amd64`
- `6.18.18-trim-570-amd64`
- `6.18.18-trim-587-amd64`

执行流程：

- 下载 `nvidia-grid-kernel-src`
- 解出 `kernel/`，该 artifact 在 patch pattern 命中时包含已 patch 的 kernel source，未命中或脚本级失败时保持当前 kernel source
- 在对应内核头文件容器中执行 `make -j"$(nproc)"`
- 收集编译出的 `*.ko`
- 下载 `nvidia-grid-firmware`
- 替换 `package_kernel_space/manifest`
- 生成 `app.tgz`
- 按内核版本分别打出 `.tgz` artifact，发布 Release 前由 `test_release.yml` 改名为 `.tgz.fpk`

### `user_space.yml`

负责用户空间驱动包的打包：

- 下载 `nvidia-grid-runfile`
- 将 NVIDIA `.run` 安装包放入 `app/`
- 下载 `nvlts` artifact 到 `app/nvlts/`
- 替换 `package_user_space/manifest`
- 生成 `app.tgz`
- 打出用户空间驱动包 artifact：

```text
appstore.driver.gpu.nvidia.user-580.159.03-2-x86.tgz
```

发布 Release 前，`test_release.yml` 会将该 artifact 改名为：

```text
appstore.driver.gpu.nvidia.user-580.159.03-2-x86.tgz.fpk
```

### `static_checks.yml`

负责静态检查：

- 校验 README、文档、`CLAUDE.md`、manifest 和 patch 脚本可以按 UTF-8 读取
- 检查明显乱码标记
- 校验文档中的应用包版本与 `test_release.yml` 的 `this_pack_version` 一致
- 对 `scripts/patch-nvidia-grid-kernel-binary.py` 执行 `python3 -m py_compile`
- 对 `package_kernel_space/cmd` 和 `package_user_space/cmd` 下的 shell 脚本执行 `bash -n`

## 内核空间驱动包

安装入口：

```text
package_kernel_space/cmd/main
```

`start` 执行顺序：

1. 安装 firmware
2. 安装 NVIDIA 内核模块
3. 切换模块 alternatives
4. 执行 `depmod`
5. 写入 `/etc/modprobe.d/blacklist-nouveau.conf` 禁用 nouveau
6. 执行 `update-initramfs -u`

### Firmware 安装

包内 firmware 来源：

```text
${TRIM_APPDEST}/app/firmware/
```

安装到系统目录：

```text
/usr/lib/firmware/nvidia/580.159.03/
```

脚本会复制 firmware 目录下的全部文件，不硬编码具体固件文件名。

### 内核模块选择

运行时会根据以下信息选择对应模块目录：

- `uname -r`
- `uname -v` 中的 build number
- `uname -m` 对应的架构

当前 `6.18.18-trim` 的选择逻辑：

```text
build < 570        -> 6.18.18-trim-427-<arch>
570 <= build < 587 -> 6.18.18-trim-570-<arch>
build >= 587       -> 6.18.18-trim-587-<arch>
```

模块包目录格式：

```text
${TRIM_APPDEST}/app/appstore.driver.gpu.nvidia.ko_<内核版本-build-架构>/
```

例如：

```text
${TRIM_APPDEST}/app/appstore.driver.gpu.nvidia.ko_6.18.18-trim-587-amd64/
```

### 模块安装位置

不同 FNOS/TRIM 内核构建的模块根目录不完全一致。脚本会优先读取系统现有链接：

```text
/lib/modules/$(uname -r)/updates/trim/alternatives
```

如果该链接存在，会跟随它解析出实际模块根目录。例如不同系统上可能是：

```text
/usr/lib/modules_trim/$(uname -r)/alternatives
/usr/trim/modules/$(uname -r)/alternatives
```

如果系统链接不存在或无法解析，脚本会按内核版本和 build number 做 fallback：`6.18.18` 及以上且 build number 大于 `542` 时使用 `/usr/lib/modules_trim/$(uname -r)`，否则使用 `/usr/trim/modules/$(uname -r)`。

模块会安装到解析出的模块根目录下：

```text
<模块根目录>/nvidia-gpu-kernel-grid/
```

然后切换 alternatives：

```text
<模块根目录>/alternatives/nvidia-gpu -> ../nvidia-gpu-kernel-grid
```

因此无论 `/lib/modules/$(uname -r)/updates/trim/alternatives` 指向 `/usr/lib/modules_trim` 还是 `/usr/trim/modules`，`modprobe nvidia` 最终都会通过系统原有 alternatives 链接加载当前包安装的模块。

### 状态检查

`package_kernel_space/cmd/main status` 会读取：

```text
<模块根目录>/alternatives/nvidia-gpu/nvidia.ko
```

并通过 `modinfo` 检查模块版本是否等于：

```bash
EXPECTED_DRIVER_VERSION="580.159.03"
```

同时还会检查对应版本的 firmware 目录是否存在，并确认目录下至少有一个固件文件：

```text
/usr/lib/firmware/nvidia/580.159.03/
```

返回值：

- `0`：版本符合预期，firmware 存在
- `3`：未安装、模块版本不符合预期，或对应版本 firmware 缺失

### 停止、卸载和升级

`package_kernel_space/cmd/main stop` 不恢复 alternatives，只记录日志。

恢复逻辑放在公共函数 `restore_default_module_package`，由以下脚本调用：

- `package_kernel_space/cmd/uninstall_init`
- `package_kernel_space/cmd/upgrade_init`

这两个脚本会恢复默认 proprietary 模块：

```text
<模块根目录>/alternatives/nvidia-gpu -> ../nvidia-gpu-proprietary
```

并移除本项目安装的模块目录：

```text
<模块根目录>/nvidia-gpu-kernel-grid/
```

然后执行：

```bash
depmod
update-initramfs -u
```

## 用户空间驱动包

安装入口：

```text
package_user_space/cmd/main
```

`start` 会先检查：

```text
/proc/driver/nvidia/version
```

确认当前内核空间 NVIDIA 驱动版本为：

```text
580.159.03
```

版本匹配后，执行 NVIDIA `.run` 安装包的静默安装。安装命令等价于：

```bash
./NVIDIA-Linux-x86_64-580.159.03-grid.run \
  --silent \
  --no-kernel-modules \
  --no-dkms \
  --disable-nouveau \
  --no-x-check \
  --no-nouveau-check \
  --no-questions \
  --ui=none
```

该安装流程不会安装 NVIDIA 内核模块，也不会启用 DKMS；它要求 `package_kernel_space` 已经安装并启用了匹配版本的内核空间驱动。

用户空间驱动安装成功后会安装 NVLTS：

```text
/opt/nvlts/nvlts
/opt/nvlts/configs/
/etc/systemd/system/nvidia-gridd.service.d/nvlts.conf
```

`package_user_space/cmd/write_gridd_conf` 会写入 `/etc/nvidia/gridd.conf`，内容为 vGPU Licensing Daemon 配置模板。

随后执行：

```bash
systemctl daemon-reload
systemctl enable nvidia-gridd
systemctl restart nvidia-gridd
```

用户空间驱动安装成功后还会重启以下服务，使系统组件重新加载 NVIDIA 用户空间库：

```bash
systemctl restart sysinfo_service.service
systemctl restart ai_manager.service
systemctl restart mediasrv.service
systemctl restart resmon_service.service
```

### 状态检查

`package_user_space/cmd/main status` 会检查用户空间驱动库是否存在：

```text
/usr/lib/x86_64-linux-gnu/libnvidia-ml.so.580.159.03
```

存在时返回 `0`，不存在时返回 `3`。

### 卸载和升级

`package_user_space/cmd/uninstall_init` 和 `package_user_space/cmd/upgrade_init` 会调用 `common` 中的统一卸载流程。

卸载 NVIDIA 用户空间驱动的命令等价于：

```bash
./NVIDIA-Linux-x86_64-580.159.03-grid.run \
  --uninstall \
  --silent \
  --no-runlevel-check \
  --ui=none
```

同时会清理 NVLTS 相关文件和 systemd drop-in：

```text
/opt/nvlts/
/etc/systemd/system/nvidia-gridd.service.d/nvlts.conf
```

## 错误展示

根据飞牛应用中心脚本规范，启动、卸载或升级过程中发生错误时，脚本会把明确失败原因写入：

```text
${TRIM_TEMP_LOGFILE}
```

这样应用中心可以直接展示具体错误，例如内核版本不支持、模块目录缺失、firmware 缺失、驱动版本不匹配、`depmod` 或 `update-initramfs` 执行失败等。失败时脚本返回错误码 `1`。

`report_error` 同时会把错误输出到标准输出并写入 `LOG_FILE`，便于命令行调试和应用中心展示。

## Manifest 说明

`package_kernel_space/manifest` 和 `package_user_space/manifest` 是模板文件，打包时由 workflow 替换占位符：

- `this_pack_manifest_version`
- `this_pack_nvidia_driver_version`
- `this_pack_nvidia_driver_url`
- `this_pack_manifest_platform`
- `this_pack_manifest_kernel`，仅内核空间包使用

根据应用中心文档，`arch` 字段已废弃；当前只使用 `platform` 字段。`platform` 不支持多个值，当前 amd64 包声明为 `x86`。

## 更新 NVIDIA 驱动时需要同步修改

更新驱动版本时，至少需要检查并修改：

1. `.github/workflows/test_release.yml`
   - `this_pack_version`
   - `this_pack_nvidia_driver_version`
   - `this_pack_nvidia_driver_url`
   - `this_pack_grid_url`
   - `this_pack_grid_run`
   - `this_pack_nvlts_version`，如需要固定 NVLTS 版本

2. `scripts/patch-nvidia-grid-kernel-binary.py`
   - 升级 `this_pack_grid_run` 或 NVIDIA 驱动版本时，建议重新检查 hex pattern 是否还能命中
   - pattern 未命中不会阻塞构建，但会按 pattern 名称输出 warning，需要在 workflow 日志中确认实际 patch 情况

3. `package_kernel_space/cmd/common` 和 `package_user_space/cmd/common`
   - `EXPECTED_DRIVER_VERSION` 的模板替换结果需要保持一致

4. 如新增内核或架构
   - 在 `kernel_space.yml` 的 matrix 中加入对应目标
   - 在 `test_release.yml` 的 release 上传矩阵中加入对应最终包目标
   - 确认 release 上传流程仍先下载 `.tgz` artifact，再改名并上传 `.tgz.fpk`
   - 同步维护矩阵中的 `manifest_platform`

5. 如调整包名
   - `test_release.yml` 的 `proj_name` 和 `kernel_module_package_name`
   - `kernel_space.yml` 的 `kernel_module_package_name`
   - `package_kernel_space/cmd/common` 中的 `PROJ_NAME`
   - README 和用户文档中的下载包名

## 维护注意事项

- `appstore.driver.gpu.nvidia.grid` 是仓库和 release 名称。
- `appstore.driver.gpu.nvidia.ko` 仍用于内核空间应用包名和内核模块目录前缀。
- `appstore.driver.gpu.nvidia.user` 用于用户空间应用包名。
- 内核空间和用户空间驱动版本必须一致。
- 宿主机 vGPU KVM 驱动和客户机 GRID 驱动必须来自匹配的 NVIDIA vGPU 版本组合。
- NVIDIA kernel binary patch 的 pattern 未命中不会阻塞构建，但会按 pattern 名称输出 warning；脚本级失败也只会输出 warning 并继续构建。维护发布包时需要检查 workflow 日志，确认实际 patch 情况。
- 本项目与飞牛官方应用中心 NVIDIA 驱动存在冲突，不应同时安装或启用。

## 图标与品牌素材说明

本项目如使用 NVIDIA 名称、徽标或相关品牌素材，仅用于标识本应用包与 NVIDIA GPU 驱动相关。NVIDIA 徽标和品牌素材的使用应遵守 NVIDIA 官方《徽标和品牌指南》：

https://www.nvidia.cn/about-nvidia/legal-info/logo-brand-usage/

根据该页面说明，NVIDIA 的徽标和其他品牌元素属于 NVIDIA 的品牌资产，未经 NVIDIA 明确书面授权不得使用；使用 NVIDIA 徽标也可能被理解为存在合作伙伴关系或获得 NVIDIA 品牌背书。因此，本项目不声明与 NVIDIA 存在合作、赞助、认证或背书关系。
