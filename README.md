# Devops Analyzer

扫描项目源码 → Tree-sitter 提取代码块 → 大模型分析 → 生成 `README.md`。

## 安装

```bash
cd /path/to/Devops
conda activate devops
pip install -e .

# 使用智谱 AI 时额外安装
pip install zhipuai
```

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
