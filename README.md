<div align="center">

## ✨ nonebot-plugin-ncqrcode ✨
[![LICENSE](https://img.shields.io/github/license/Misty02600/nonebot-plugin-ncqrcode.svg)](./LICENSE)
[![python](https://img.shields.io/badge/python-3.11+-blue.svg?logo=python&logoColor=white)](https://www.python.org)
![Adapters](https://img.shields.io/badge/Adapters-OneBot%20v11-blue)
<br/>

[![uv](https://img.shields.io/badge/package%20manager-uv-black?logo=uv)](https://github.com/astral-sh/uv)
[![ruff](https://img.shields.io/badge/code%20style-ruff-black?logo=ruff)](https://github.com/astral-sh/ruff)

</div>

本项目的 Just recipes 需要 Just 1.56 或更高版本；Windows 下还需要 PowerShell 7，并通过 `pwsh` 命令调用。直接运行对应的 `uv`、`gh` 等命令不受 PowerShell 要求影响。

## 🛠️ 开发与模板更新

- `just sync`：同步全部开发依赖组。
- `just lint`：只检查 Ruff lint 和格式，不修改文件；`just format` 才会应用修复和格式化。
- `just test`、`just check`：运行 pytest 和 BasedPyright。
- `just update-hooks`：更新 prek hook revisions，并保留七天 cooldown。
- `just update-template`：只在干净工作树中运行 Copier 更新，并自动进入完整收尾验证。
- `just finish-template-update`：解决 Copier 冲突或接管 Renovate PR 后，检查 `.rej`、刷新本地 lock，并重跑 hooks 与全部质量检查。

Hosted Renovate 仍是常规模板升级入口。手工命令用于本地复现、冲突处理和恢复，不要编辑 `.copier-answers.yml` 或手工指定模板版本。

## 🚀 发布

待发布的源码通过 CI 后，在 `main` 分支运行 `just bump`。确认后，Commitizen 会创建版本提交和 annotated tag，Just 会将当前提交及其可达的 annotated tags 整体原子推送到 `origin`，由版本 tag 触发远端 release workflow。

## 📖 介绍

TODO：按插件已经实现的功能填写用途、适用场景和限制。

## 💿 安装

<details open>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-ncqrcode --upgrade
使用 **pypi** 源安装

    nb plugin install nonebot-plugin-ncqrcode --upgrade -i "https://pypi.org/simple"
使用**清华源**安装

    nb plugin install nonebot-plugin-ncqrcode --upgrade -i "https://pypi.tuna.tsinghua.edu.cn/simple"


</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details open>
<summary>uv</summary>

    uv add nonebot-plugin-ncqrcode
安装仓库 main 分支

    uv add git+https://github.com/Misty02600/nonebot-plugin-ncqrcode@main
</details>

<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-ncqrcode
安装仓库 main 分支

    pdm add git+https://github.com/Misty02600/nonebot-plugin-ncqrcode@main
</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-ncqrcode
安装仓库 main 分支

    poetry add git+https://github.com/Misty02600/nonebot-plugin-ncqrcode@main
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_ncqrcode"]

</details>

<details>
<summary>使用 nbr 安装(使用 uv 管理依赖可用)</summary>

[nbr](https://github.com/fllesser/nbr) 是一个基于 uv 的 nb-cli，可以方便地管理 nonebot2

    nbr plugin install nonebot-plugin-ncqrcode
使用 **pypi** 源安装

    nbr plugin install nonebot-plugin-ncqrcode -i "https://pypi.org/simple"
使用**清华源**安装

    nbr plugin install nonebot-plugin-ncqrcode -i "https://pypi.tuna.tsinghua.edu.cn/simple"

</details>


## ⚙️ 配置

TODO：按插件实际读取的配置模型列出配置项、是否必填、默认值和作用；没有配置项时删除本节。只有代码实际依赖相应组件时，才说明 localstore 等存储方案。

## 🎉 使用

TODO：按插件实际注册的命令、事件或公开接口说明用法和权限边界；没有命令接口时改为对应的使用方式。

### 🎨 效果图

TODO：按实际效果补充截图；不需要时删除本节。
