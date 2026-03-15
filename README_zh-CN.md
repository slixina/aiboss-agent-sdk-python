# AI Boss Agent SDK (中文版)

[AI Boss](https://aiboss.fun) 的官方 Python SDK 和命令行工具 (CLI)。

[English](./README.md) | [简体中文](./README_zh-CN.md)

---

## 🚀 简介

AI Boss 允许你通过运行 AI Agent 来利用闲置计算资源赚取收益。Agent 会自动从网络领取并执行经过验证的任务（如网页抓取、网络诊断等）。

**核心特性：**
- **安全沙箱**: 内置防 RCE (远程代码执行) 机制；仅允许访问白名单域名。
- **一键接入**: 一行命令即可加入网络。
- **被动收入**: 后台运行，自动赚取积分。

## 📋 前置要求

- **Python 3.9** 或更高版本。
- 一个 [AI Boss Dashboard](https://aiboss.fun) 账号（用于获取 Enrollment Code）。

## 📦 安装指南

### 方法 1: 使用 pip 安装 (推荐)

```bash
pip install aiboss-agent-sdk
```

### 方法 2: 源码安装

```bash
git clone https://github.com/slixina/aiboss-agent-sdk-python.git
cd aiboss-agent-sdk-python
pip install .
```

## ⚡ 快速开始

### 1. 获取注册码 (Enrollment Code)

1. 登录 [AI Boss Dashboard](https://aiboss.fun/dashboard)。
2. 复制你的 **Enrollment Code** (即你的邀请码)。

### 2. 注册 Agent

在终端运行以下命令，将 `<YOUR_CODE>` 替换为你复制的代码：

```bash
# 基础注册
aiboss enroll --code <YOUR_CODE>

# 可选：指定自定义名称
aiboss enroll --code <YOUR_CODE> --name "My Worker Agent"
```

此操作将：
- 向 AI Boss 网络进行身份验证。
- 生成唯一的 Agent ID 和安全 API 密钥。
- 将凭证保存到 `~/.aiboss/config.json`。

### 3. 启动 Agent

启动 Agent 开始处理任务：

```bash
aiboss start
```

你应该会看到类似以下的输出：
```
[INFO] Agent started. ID: xxxxx-xxxx-xxxx
[INFO] Connected to AI Boss Network (v0.1.0)
[INFO] Waiting for tasks...
[INFO] Task received: scrape (google.com) ...
[SUCCESS] Task completed. Reward: 0.5 CP.
```

### 4. 查看状态

打开一个新的终端窗口查看 Agent 的收入和状态：

```bash
aiboss status
```

## ⚙️ 配置说明

SDK 将配置信息存储在 `~/.aiboss/config.json` 文件中。虽然可以手动编辑，但不建议这样做。

**默认能力 (Capabilities):**
默认情况下，Agent 启用所有支持的能力：
- `scrape`: 网页抓取 (仅限白名单域名：Google, Twitter, GitHub)。
- `ping`: 网络连通性测试。
- `math`: 计算型工作量证明 (PoW)。

## 🛡️ 安全性

我们非常重视安全性。
- **无 RCE**: SDK 不支持任意代码执行。它仅运行预定义的、安全的执行器。
- **沙箱**: 网络访问严格限制在白名单域名内。
- **审计**: 使用 Python 的 `sys.audit` 钩子监控系统调用。

## ❓ 常见问题 (Troubleshooting)

**Q: `command not found: aiboss`**
A: 确保你的 Python 脚本目录在系统 PATH 中。如果你通过 `pip` 安装，通常位于 `~/.local/bin` (Linux/Mac) 或 `%APPDATA%\Python\Scripts` (Windows)。

**Q: `Connection refused` 或 `401 Unauthorized`**
A: 检查网络连接。如果是 401 错误，可能是你的 Enrollment Code 无效或已过期。请尝试重新注册。

**Q: Python 版本错误**
A: 运行 `python --version` 检查版本。你需要 Python 3.9+。

## 🤝 贡献代码

欢迎提交 PR！详情请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 📄 许可证

MIT License. 详见 [LICENSE](LICENSE) 文件。
