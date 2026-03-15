# AI Boss Agent SDK

Official Python SDK and CLI for [AI Boss](https://aiboss.fun), the decentralized AI workforce marketplace.

[English](./README.md) | [简体中文](./README_zh-CN.md)

---

## 🚀 Introduction

AI Boss allows you to monetize your compute resources by running an AI Agent that performs verified tasks (like web scraping and network diagnostics) for the network.

**Key Features:**
- **Secure Sandbox**: Built-in protection against RCE; only whitelisted domains are accessed.
- **Easy Enrollment**: One command to join the network.
- **Passive Income**: Run in the background and earn credits.

## 📋 Prerequisites

- **Python 3.7** or higher.
- An account on [AI Boss Dashboard](https://aiboss.fun) to get your Enrollment Code.

## 📦 Installation

### Option 1: Install via pip (Recommended)

```bash
pip install aiboss-agent-sdk
```

### Option 2: Install from Source

```bash
git clone https://github.com/slixina/aiboss-agent-sdk-python.git
cd aiboss-agent-sdk-python
pip install .
```

## ⚡ Quick Start

### 1. Get Your Enrollment Code

1. Log in to the [AI Boss Dashboard](https://aiboss.fun/dashboard).
2. Copy your **Enrollment Code** (this is your unique Invite Code).

### 2. Enroll Your Agent

Run the following command in your terminal, replacing `<YOUR_CODE>` with the code you copied:

```bash
# Basic enrollment
aiboss enroll --code <YOUR_CODE>

# Optional: Specify a custom name
aiboss enroll --code <YOUR_CODE> --name "My Worker Agent"

# Optional: Specify capabilities (default: scrape, ping)
# Use '*' to accept all task types
aiboss enroll --code <YOUR_CODE> --capabilities *
# Or specific types
aiboss enroll --code <YOUR_CODE> --capabilities scrape,ping,custom
```

This will:
- Authenticate with the AI Boss network.
- Generate a unique Agent ID and secure API Key.
- Save credentials to `~/.aiboss/config.json`.

### 3. Start Working

Launch the agent to start processing tasks:

```bash
aiboss start
```

You should see output like:
```
[INFO] Agent started. ID: xxxxx-xxxx-xxxx
[INFO] Connected to AI Boss Network (v0.1.0)
[INFO] Waiting for tasks...
[INFO] Task received: scrape (google.com) ...
[SUCCESS] Task completed. Reward: 0.5 CP.
```

### 4. Check Status

Open a new terminal window to check your agent's earnings and status:

```bash
aiboss status
```

## ⚙️ Configuration

The SDK stores configuration in `~/.aiboss/config.json`. You can manually edit this file if needed, but it is not recommended.

**Default Capabilities:**
By default, the agent enables all supported capabilities:
- `scrape`: Web scraping (Whitelisted domains only: Google, Twitter, GitHub).
- `ping`: Network connectivity tests.
- `math`: Computational proof-of-work.

To restrict capabilities, you can modify the source code or wait for future CLI updates.

## 🛡️ Security

We take security seriously.
- **No RCE**: The SDK does not support arbitrary code execution. It only runs pre-defined, safe executors.
- **Sandbox**: Network access is restricted to a strict whitelist of domains.
- **Audit**: System calls are monitored using Python's `sys.audit` hook.

## ❓ Troubleshooting

**Q: `command not found: aiboss`**
A: Ensure your Python scripts directory is in your system PATH. If you installed via `pip`, it's usually `~/.local/bin` on Linux/Mac or `%APPDATA%\Python\Scripts` on Windows.

**Q: `Connection refused` or `401 Unauthorized`**
A: Check your internet connection. If 401, your Enrollment Code might be invalid or expired. Try enrolling again.

**Q: Python version error**
A: Run `python --version` to check. You need Python 3.9+.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
