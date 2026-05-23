# Devops Analyzer

**[English](#english)** · **[中文](#中文)**

---

<a id="english"></a>

## English

Scan project source → Tree-sitter code blocks → LLM analysis → `README.md`.

### Install

```bash
# Recommended: PyPI prebuilt wheel (native extensions built in Release CI; no MSVC on Windows)
pip install devops-analyzer

# Or from source (fetches tree-sitter grammars and compiles locally; needs git + C++ toolchain)
git clone https://github.com/dadaozhichen/OpenDevOps.git
cd OpenDevOps
pip install -e .

# Optional: Zhipu AI
pip install zhipuai
```

On tag push, GitHub Actions **prebuilds** `scan_native` and `tree_sitter_native` on Linux / macOS / Windows for **Python 3.9–3.13** and uploads wheels.  
`pip install devops-analyzer` prefers those wheels, so you usually **do not need to compile C++ locally**.

Prebuilt `.whl` files are also on [GitHub Releases](https://github.com/dadaozhichen/OpenDevOps/releases):

```bash
pip install devops_analyzer-0.1.7-cp311-cp311-win_amd64.whl
```

**Supported Python**: `>=3.9` (see `requires-python` in `pyproject.toml`).  
**tree-sitter**: `0.21.x` for 3.9–3.12; `>=0.22` for 3.13+ (PyPI environment markers).

#### Windows

| Method | Requirements |
|--------|----------------|
| `pip install devops-analyzer` (PyPI / Release wheel) | Recommended; **no MSVC** |
| `pip install -e .` or `pip install .` (sdist / source) | **Git**, **Microsoft C++ Build Tools** ([download](https://visualstudio.microsoft.com/visual-cpp-build-tools/)) |

If pip builds from source (e.g. no wheel for your Python version), force binaries only:

```bash
pip install devops-analyzer --only-binary devops-analyzer
```

### First run: configure model API

Configure your API key before analyzing a project:

```bash
devops config
```

Follow the prompts for provider, API key, and model. Config is stored in `~/.devops/config.json` (user-readable only).

Show current config (masked API key):

```bash
devops config --show
```

### Supported providers

| Provider | `provider` | Default model | Notes |
|----------|------------|---------------|-------|
| OpenAI | `openai` | `gpt-4o-mini` | Official or custom base URL |
| Zhipu AI | `zhipuai` | `glm-4-flash` | `pip install zhipuai` |
| DeepSeek | `deepseek` | `deepseek-chat` | OpenAI-compatible API |
| Moonshot | `moonshot` | `moonshot-v1-8k` | OpenAI-compatible API |

Environment variables (lower priority than config file):

```bash
export DEVOPS_PROVIDER=openai
export DEVOPS_API_KEY=sk-...
export DEVOPS_MODEL=gpt-4o-mini
export DEVOPS_BASE_URL=https://api.openai.com/v1   # optional
```

### Analyze a project

```bash
devops /path/to/your/project

# explicit subcommand
devops analyze /path/to/your/project

# custom output file
devops /path/to/project -o README.md

# override model without editing config
devops /path/to/project --provider deepseek --model deepseek-chat

# English README (default is Chinese)
devops /path/to/project --lang en
```

### Commands

```bash
devops config              # interactive API setup
devops config --show       # show config
devops <project-path>      # analyze and write README.md
devops analyze <project-path>
devops --help
devops --version
```

---

<a id="中文"></a>

## 中文

扫描项目源码 → Tree-sitter 提取代码块 → 大模型分析 → 生成 `README.md`。

### 安装

```bash
# 推荐：安装 PyPI 预编译 wheel（Release CI 已编译原生扩展，Windows 一般无需 MSVC）
pip install devops-analyzer

# 或从源码安装（会自动拉取 tree-sitter grammar 并本地编译，需 git + C++ 编译器）
git clone https://github.com/dadaozhichen/OpenDevOps.git
cd OpenDevOps
pip install -e .

# 使用智谱 AI 时额外安装
pip install zhipuai
```

打 tag 发布时，GitHub Actions 会在 **Linux / macOS / Windows** 上为 **Python 3.9–3.13** **预编译** `scan_native` 与 `tree_sitter_native` 并上传 wheel。  
因此 `pip install devops-analyzer` 会优先安装这些 wheel，**通常不需要在本机编译 C++**。

也可从 [GitHub Releases](https://github.com/dadaozhichen/OpenDevOps/releases) 下载对应平台的 `.whl` 手动安装：

```bash
pip install devops_analyzer-0.1.7-cp311-cp311-win_amd64.whl
```

**支持的 Python**：`>=3.9`（见 `pyproject.toml` 中 `requires-python`）。  
**tree-sitter**：3.9–3.12 使用 `0.21.x`；3.13 及以上使用 `>=0.22`（由 PyPI 环境标记自动选择）。

#### Windows

| 安装方式 | 要求 |
|----------|------|
| `pip install devops-analyzer`（PyPI / Release 预编译 wheel） | 推荐，**无需**安装 MSVC |
| `pip install -e .` 或 `pip install .`（sdist / 源码） | 需 **Git**、**Microsoft C++ Build Tools**（[下载](https://visualstudio.microsoft.com/visual-cpp-build-tools/)） |

若 pip 误从源码包编译（例如没有对应 Python 版本的 wheel），可强制只装二进制包：

```bash
pip install devops-analyzer --only-binary devops-analyzer
```

### 首次使用：配置模型 API

分析项目前请先配置 API Key：

```bash
devops config
```

按提示选择提供商、输入 API Key 和模型名称。配置保存在 `~/.devops/config.json`（仅当前用户可读）。

查看当前配置（API Key 脱敏显示）：

```bash
devops config --show
```

### 支持的模型提供商

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

### 分析项目

```bash
devops /path/to/your/project

# 或显式子命令
devops analyze /path/to/your/project

# 指定输出文件
devops /path/to/project -o README.md

# 临时覆盖模型（不改配置文件）
devops /path/to/project --provider deepseek --model deepseek-chat

# 生成英文 README（默认中文）
devops /path/to/project --lang en
```

### 命令一览

```bash
devops config              # 交互式配置 API
devops config --show       # 查看配置
devops <项目路径>          # 分析并生成 README.md
devops analyze <项目路径>
devops --help
devops --version
```
