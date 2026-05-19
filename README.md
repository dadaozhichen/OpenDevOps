# Devops Analyzer

扫描项目源码 → Tree-sitter 提取代码块 → 大模型分析 → 生成 `README.md`。

## 安装

```bash
pip install devops-analyzer

# 或从源码安装（会自动拉取 tree-sitter grammar 并编译原生扩展，需 git + C++ 编译器）
git clone https://github.com/dadaozhichen/OpenDevOps.git
cd OpenDevOps
pip install -e .

# 使用智谱 AI 时额外安装
pip install zhipuai
```

从 PyPI 安装的 **wheel** 已包含编译好的 `scan_native` 与 `tree_sitter_native`，可直接 `devops config` / `devops <项目路径>`。

**Python 3.13**：会自动安装 `tree-sitter>=0.22`（带 Windows 等平台预编译 wheel）；3.12 及以下仍使用 `tree-sitter 0.21.x`。

### Windows 说明

| 安装方式 | 要求 |
|----------|------|
| `pip install devops-analyzer`（PyPI wheel） | 推荐 |
| `pip install -e .`（源码） | 需 **Git**、**Microsoft C++ Build Tools**（[下载](https://visualstudio.microsoft.com/visual-cpp-build-tools/)），用于编译本项目的 C++ 扩展 |

## 首次使用：配置模型 API

**必须先配置你自己的 API Key**，再分析项目：

```bash
devops config
```

按提示选择提供商、输入 API Key 和模型名称。配置保存在 `~/.devops/config.json`（仅当前用户可读）。

查看当前配置（Key 脱敏显示）：

```bash
devops config --show
```

## 支持的模型提供商

| 提供商 | `provider` 值 | 默认模型 | 说明 |
|--------|---------------|----------|------|
| OpenAI | `openai` | `gpt-4o-mini` | 官方或自定义 Base URL |
| 智谱 AI | `zhipuai` | `glm-4-flash` | 需 `pip install zhipuai` |
| DeepSeek | `deepseek` | `deepseek-chat` | OpenAI 兼容协议 |
| Moonshot | `moonshot` | `moonshot-v1-8k` | OpenAI 兼容协议 |

也可用环境变量覆盖（优先级低于配置文件）：

```bash
export DEVOPS_PROVIDER=openai
export DEVOPS_API_KEY=sk-...
export DEVOPS_MODEL=gpt-4o-mini
export DEVOPS_BASE_URL=https://api.openai.com/v1   # 可选
```

## 分析项目

```bash
devops /path/to/your/project

# 或显式子命令
devops analyze /path/to/your/project

# 指定输出文件
devops /path/to/project -o README.md

# 临时覆盖模型（不改配置文件）
devops /path/to/project --provider deepseek --model deepseek-chat
```

## 命令一览

```bash
devops config              # 交互式配置 API
devops config --show       # 查看配置
devops <项目路径>          # 分析并生成 README.md
devops analyze <项目路径>
devops --help
devops --version
```
