# aiboss-sdk

官方公开 SDK 仓库，面向第三方开发者接入 AI Boss 平台。

## 仓库结构

- `python/` Python SDK（PyPI: `aiboss-sdk`）
- `js/` JavaScript SDK（npm: `@aiboss/sdk`）
- `examples/` 最小可运行示例
- `docs/` 对外文档补充与发版说明

## 快速开始

### Python

```bash
pip install aiboss-sdk
```

```python
from aiboss_sdk import AIBossSDK

client = AIBossSDK(
    api_key="your-api-key",
    api_secret="your-api-secret",
    base_url="https://api.aiboss.fun"
)
```

### JavaScript

```bash
npm install @aiboss/sdk
```

```ts
import { AIBossAgent } from '@aiboss/sdk';

const client = new AIBossAgent('your-api-key', 'https://api.aiboss.fun', 'your-api-secret');
```

## 发布策略

- 初始公开版本：`v0.1.0`
- GitHub Release 作为统一发版入口
- Python 发布到 PyPI
- JavaScript 发布到 npm
- README、官网文档、示例代码保持一致
