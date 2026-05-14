# appstore.driver.gpu.nvidia.ko

这是一个用于 FN NAS / TRIM 应用包体系的 NVIDIA GPU 内核模块包项目。

当前项目从 NVIDIA Linux 驱动安装包中提取内核模块源码和固件，针对指定 FNOS/TRIM 内核版本编译 `*.ko`，并按内核版本分别打出最终应用包。

## 当前版本

- NVIDIA 驱动版本：`580.159.03`
- 应用包版本：`580.159.03-1`
- 当前支持内核：`6.18.18-trim`
- 当前构建架构：`amd64`

## 构建产物

GitHub Actions 会按内核构建目标分别生成最终包：

```text
appstore.driver.gpu.nvidia.ko-580.159.03-1-6.18.18-trim-570-amd64.tgz
appstore.driver.gpu.nvidia.ko-580.159.03-1-6.18.18-trim-587-amd64.tgz
appstore.driver.gpu.nvidia.user-580.159.03-1-x86.tgz
```

每个最终包内包含：

- NVIDIA 内核模块：`app/appstore.driver.gpu.nvidia.ko_<内核版本-架构>/`
- NVIDIA 固件：`app/firmware/`
- 内核空间驱动包元数据和生命周期脚本：`package_kernel_space/`
- 用户空间驱动包元数据和生命周期脚本：`package_user_space/`

两个 package 的 `cmd/common` 分别保存各自生命周期脚本复用的变量、日志函数和错误展示函数；它们会随对应 package 一起打包，不依赖另一个 package。

## Workflow 说明

### `test_release.yml`

主入口 workflow，负责整体编排：

- 定义项目名、包版本、NVIDIA 驱动下载地址
- 调用驱动源码准备 workflow
- 调用 `kernel_space.yml` 完成内核模块编译和 `package_kernel_space` 打包
- 调用 `user_space.yml` 完成 `package_user_space` 打包
- 可选创建 GitHub prerelease 并上传产物

关键变量集中在这里维护：

```yaml
proj_name: "appstore.driver.gpu.nvidia.ko"
this_pack_version: "580.159.03-1"
this_pack_nvidia_driver_version: "580.159.03"
this_pack_nvidia_driver_url: "https://www.nvidia.com/en-us/drivers/details/267577/"
this_pack_grid_url: "https://cn.download.nvidia.com/XFree86/Linux-x86_64/580.159.03/NVIDIA-Linux-x86_64-580.159.03.run"
this_pack_grid_run: "NVIDIA-Linux-x86_64-580.159.03-grid.run"
```

### `nvidia-grid-kernel-src.yml`

负责准备 NVIDIA 驱动源码和固件：

- 下载并缓存 NVIDIA `.run` 文件
- 执行 `--extract-only --target drvpkg`
- 将 `drvpkg/kernel` 打包为 `nvidia-grid-kernel-src`
- 将 `drvpkg/firmware` 作为目录 artifact 上传为 `nvidia-grid-firmware`
- 将 NVIDIA `.run` 安装包上传为 `nvidia-grid-runfile`

### `kernel_space.yml`

负责内核空间驱动包的编译和打包。

当前 matrix 包含：

- `6.18.18-trim-570-amd64`
- `6.18.18-trim-587-amd64`

该 workflow 会：

- 下载 `nvidia-grid-kernel-src`
- 解出 `kernel/`
- 在对应内核头文件容器中执行 `make -j"$(nproc)"`
- 收集编译出的 `*.ko`
- 下载 `nvidia-grid-firmware`
- 替换 `package_kernel_space/manifest`
- 生成 `app.tgz`
- 按内核版本分别打出最终 `.tgz`

### `user_space.yml`

负责用户空间驱动包的打包。

该 workflow 会：

- 下载 `nvidia-grid-runfile`
- 将 NVIDIA `.run` 安装包放入 `app/`
- 替换 `package_user_space/manifest`
- 生成 `app.tgz`
- 打出用户空间驱动包：

```text
appstore.driver.gpu.nvidia.user-580.159.03-1-x86.tgz
```

## 安装逻辑

安装入口为：

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

运行时会根据：

- `uname -r`
- `uname -v` 中的 build number
- `uname -m` 对应的架构

选择对应的模块目录。

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

模块会安装到：

```text
/usr/lib/modules_trim/$(uname -r)/nvidia-gpu-kernel-grid/
```

然后切换 alternatives：

```text
/usr/lib/modules_trim/$(uname -r)/alternatives/nvidia-gpu -> ../nvidia-gpu-kernel-grid
```

系统默认存在：

```text
/lib/modules/$(uname -r)/updates/trim/alternatives -> /usr/lib/modules_trim/$(uname -r)/alternatives
```

因此切换 `/usr/lib/modules_trim/.../alternatives/nvidia-gpu` 后，`/lib/modules/.../updates/trim/alternatives/nvidia-gpu` 也会同步指向新的模块目录。

## 状态检查

`package_kernel_space/cmd/main status` 会读取：

```text
/usr/lib/modules_trim/$(uname -r)/alternatives/nvidia-gpu/nvidia.ko
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

- `0`：版本符合预期
- `3`：未安装、模块版本不符合预期，或对应版本 firmware 缺失

## 停止、卸载和升级

`package_kernel_space/cmd/main stop` 不恢复 alternatives，只记录日志。

恢复逻辑放在：

- `package_kernel_space/cmd/uninstall_init`
- `package_kernel_space/cmd/upgrade_init`

这两个脚本会恢复默认 proprietary 模块：

```text
/usr/lib/modules_trim/$(uname -r)/alternatives/nvidia-gpu -> ../nvidia-gpu-proprietary
```

并移除本项目安装的模块目录：

```text
/usr/lib/modules_trim/$(uname -r)/nvidia-gpu-kernel-grid/
```

然后执行：

```bash
depmod
update-initramfs -u
```

## 用户空间驱动包

用户空间驱动包目录为：

```text
package_user_space/
```

安装入口为：

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

`package_user_space/cmd/main status` 会检查用户空间驱动库是否存在：

```text
/usr/lib/x86_64-linux-gnu/libnvidia-ml.so.580.159.03
```

存在时返回 `0`，不存在时返回 `3`。

`package_user_space/cmd/uninstall_init` 和 `package_user_space/cmd/upgrade_init` 会调用包内 NVIDIA `.run` 安装器执行静默卸载，命令等价于：

```bash
./NVIDIA-Linux-x86_64-580.159.03-grid.run \
  --uninstall \
  --silent \
  --no-runlevel-check \
  --ui=none
```

## 错误展示

根据飞牛应用中心脚本规范，启动、卸载或升级过程中发生错误时，脚本会把明确失败原因写入：

```text
${TRIM_TEMP_LOGFILE}
```

这样应用中心可以直接展示具体错误，例如内核版本不支持、模块目录缺失、firmware 缺失、驱动版本不匹配、`depmod` 或 `update-initramfs` 执行失败等。失败时脚本返回错误码 `1`；如果没有写入 `TRIM_TEMP_LOGFILE`，应用中心通常只能显示“原因未知”的通用错误。

## 更新 NVIDIA 驱动时需要同步修改

更新驱动版本时，至少需要检查并修改：

1. `.github/workflows/test_release.yml`
   - `this_pack_version`
   - `this_pack_nvidia_driver_version`
   - `this_pack_nvidia_driver_url`
   - `this_pack_grid_url`
   - `this_pack_grid_run`

2. `package_kernel_space/cmd/main` 和 `package_user_space/cmd/main`
   - `EXPECTED_DRIVER_VERSION`

3. 如新增内核或架构
   - 在 `kernel_space.yml` 的 matrix 中加入对应目标
   - 在 `test_release.yml` 的 release 上传矩阵中加入对应最终包目标
   - 同步维护矩阵中的 `manifest_platform`

`package_kernel_space/manifest` 是模板文件，打包时会由 `test_release.yml` 替换：

- `this_pack_manifest_version`
- `this_pack_nvidia_driver_version`
- `this_pack_nvidia_driver_url`
- `this_pack_manifest_platform`
- `this_pack_manifest_kernel`

根据应用中心文档，`arch` 字段已废弃；当前只使用 `platform` 字段。`platform` 不支持多个值，当前 amd64 包声明为 `x86`。

## 注意事项

- 本项目会切换系统 NVIDIA GPU 内核模块 alternatives，并安装 NVIDIA firmware。它与飞牛官方应用中心提供的 NVIDIA 驱动应用存在冲突，不建议同时安装或同时启用。
- 当前 workflow 只构建 `6.18.18-trim-570-amd64` 和 `6.18.18-trim-587-amd64`。
- `main` 脚本中包含 `427` 的选择逻辑，但当前还没有对应的 `427-amd64` 构建产物。
- firmware 作为目录 artifact 直接恢复到最终包，不再单独压缩成 tgz。

## 图标与品牌素材说明

本项目如使用 NVIDIA 名称、徽标或相关品牌素材，仅用于标识本应用包与 NVIDIA GPU 驱动相关。NVIDIA 徽标和品牌素材的使用应遵守 NVIDIA 官方《徽标和品牌指南》：

https://www.nvidia.cn/about-nvidia/legal-info/logo-brand-usage/

根据该页面说明，NVIDIA 的徽标和其他品牌元素属于 NVIDIA 的品牌资产，未经 NVIDIA 明确书面授权不得使用；使用 NVIDIA 徽标也可能被理解为存在合作伙伴关系或获得 NVIDIA 品牌背书。因此，本项目不声明与 NVIDIA 存在合作、赞助、认证或背书关系。
