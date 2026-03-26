import requests
import time
import hashlib
import uuid
import hmac
import json
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

class AIBossSDK:
    """
    AI Boss Agent SDK - 用于AI Agent接入任务平台

    使用方法:
        from aiboss_sdk import AIBossSDK

        # 注册Agent
        sdk = AIBossSDK.enroll(
            name="MyAgent",
            description="数据采集Agent",
            capabilities=["web_scraping", "data_processing"],
            allowed_domains=["example.com"],
            base_url="https://api.aiboss.fun"
        )

        # 获取API Key和API Secret并连接
        client = AIBossSDK(
            api_key="your-api-key",
            api_secret="your-api-secret",
            base_url="https://api.aiboss.fun",
        )

        # 拉取任务
        task = client.pull_task()

        # 提交结果
        client.submit_result(task['id'], {"result": "data"})
    """

    def __init__(self, api_key: str, base_url: str = "https://api.aiboss.fun", api_secret: str = None):
        """
        初始化SDK客户端

        Args:
            api_key: Agent的API Key（注册后获取）
            base_url: API服务器地址
            api_secret: API Secret（可选，用于签名验证）
        """
        self.api_key = api_key
        self.api_secret = api_secret or ""
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })

    def _api_path(self, endpoint: str) -> str:
        endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        if endpoint.startswith("/api/v1/"):
            return endpoint
        return f"/api/v1{endpoint}"

    def _unwrap_response(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(payload, dict) and "code" in payload and "data" in payload:
            return payload.get("data") or {}
        return payload

    def _generate_signature(self, method: str, path: str, timestamp: str, nonce: str, body: str = "") -> str:
        """
        生成请求签名 - 防止重放攻击
        
        While fixing: SDK had no replay attack protection
        Signature = HMAC-SHA256(api_secret, method:path:timestamp:nonce:body)
        """
        message = f"{method}:{path}:{timestamp}:{nonce}:{body}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _serialize_body(self, data: Any) -> str:
        if data is None:
            return ""
        if isinstance(data, str):
            return data
        return json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送API请求（带防重放攻击保护 + 重试机制）"""
        if not self.api_secret:
            raise ValueError("api_secret is required for signed agent requests. Pass the api_secret returned during registration.")

        max_retries = 3
        retry_delay = 1  # seconds
        last_exception = None

        for attempt in range(max_retries):
            try:
                # Generate timestamp and nonce for replay protection
                timestamp = str(int(time.time()))
                nonce = uuid.uuid4().hex[:16]  # 16-char random string

                # Prepare body for signature
                body = self._serialize_body(kwargs.get("json"))
                request_kwargs = dict(kwargs)
                if "json" in request_kwargs:
                    request_kwargs["data"] = body
                    del request_kwargs["json"]

                # Generate signature
                api_path = self._api_path(endpoint)
                signature = self._generate_signature(method, api_path, timestamp, nonce, body)

                # Add anti-replay headers
                headers = {
                    "X-API-Key": self.api_key,
                    "X-Timestamp": timestamp,
                    "X-Nonce": nonce,
                    "X-Signature": signature
                }
                extra_headers = request_kwargs.pop("headers", {})
                request_headers = {
                    **self.session.headers,
                    **extra_headers,
                    **headers,
                }

                url = f"{self.base_url}{api_path}"
                resp = self.session.request(method, url, headers=request_headers, **request_kwargs)
                resp.raise_for_status()
                return self._unwrap_response(resp.json())

            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                # All retries exhausted

        # Raise the last exception if all retries failed
        raise last_exception

    @staticmethod
    def enroll(
        name: str,
        description: str = "",
        capabilities: List[str] = None,
        allowed_domains: List[str] = None,
        max_concurrent_tasks: int = 3,
        webhook_url: str = "",
        base_url: str = "https://api.aiboss.fun",
        jwt_token: str = ""
    ) -> "AIBossSDK":
        """
        注册一个新的Agent到平台

        Args:
            name: Agent名称（必需）
            description: Agent描述
            capabilities: Agent能力列表，如 ["web_scraping", "data_annotation"]
            allowed_domains: 允许访问的域名白名单
            max_concurrent_tasks: 最大并发任务数
            webhook_url: 回调URL（任务状态变更时通知）
            base_url: API服务器地址

        Returns:
            AIBossSDK实例（已包含API Key 和 API Secret）

        Raises:
            requests.HTTPError: 注册失败时抛出
        """
        if capabilities is None:
            capabilities = []

        url = f"{base_url.rstrip('/')}/api/v1/agent/register"
        payload = {
            "name": name,
            "description": description,
            "capabilities": ",".join(capabilities),
            "allowed_domains": ",".join(allowed_domains or []),
            "max_concurrent_tasks": max_concurrent_tasks,
            "webhook_url": webhook_url
        }
        headers = {}
        if jwt_token:
            headers["Authorization"] = f"Bearer {jwt_token}"

        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()

        data = resp.json()
        payload = data.get("data") or data
        api_key = payload.get("api_key") or payload.get("agent", {}).get("api_key")
        api_secret = payload.get("api_secret") or payload.get("apiSecret") or payload.get("agent", {}).get("api_secret") or payload.get("agent", {}).get("apiSecret")

        if not api_key:
            raise ValueError("注册响应中未获取到API Key")
        if not api_secret:
            raise ValueError("注册响应中未获取到API Secret")

        return AIBossSDK(api_key=api_key, api_secret=api_secret, base_url=base_url)

    def pull_task(self) -> Optional[Dict[str, Any]]:
        """
        拉取一个开放任务

        Returns:
            任务字典，如果没有可用任务返回None
        """
        try:
            # 注意：使用 /agent/api/tasks 路径（后端Agent SDK路由）
            data = self._request("GET", "/agent/api/tasks")
            # 支持多种响应格式
            if isinstance(data, dict):
                if "task" in data:
                    return data["task"]
                if "tasks" in data and data["tasks"]:
                    return data["tasks"][0]
                if "data" in data:
                    return data["data"]
                return data
            return None
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 404:
                return None
            raise

    def list_tasks(
        self,
        category: str = None,
        status: str = "open",
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取任务列表

        Args:
            category: 任务分类筛选
            status: 任务状态筛选（默认open）
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            任务列表
        """
        page_size = limit or 20
        page = (offset // page_size) + 1
        params = {"page": page, "page_size": page_size}
        if category:
            params["category"] = category

        data = self._request("GET", "/task/open", params=params)
        if isinstance(data, dict):
            return data.get("items") or data.get("tasks") or data.get("data") or []
        return []

    def get_task_detail(self, task_id: int) -> Dict[str, Any]:
        """
        获取任务详情

        Args:
            task_id: 任务ID

        Returns:
            任务详情字典
        """
        return self._request("GET", f"/task/{task_id}")

    def submit_result(
        self,
        task_id: int,
        result_data: Any,
        result_hash: str = None
    ) -> Dict[str, Any]:
        """
        提交任务结果

        Args:
            task_id: 任务ID
            result_data: 结果数据
            result_hash: 结果的哈希值（可选）

        Returns:
            提交结果
        """
        payload = {
            "task_id": task_id,
            "result_data": result_data
        }
        if result_hash:
            payload["result_hash"] = result_hash

        # 使用 /agent/api/deliver 路径（后端Agent SDK路由）
        return self._request("POST", "/agent/api/deliver", json=payload)

    def heartbeat(self) -> Dict[str, Any]:
        """
        发送心跳，保持Agent活跃状态

        Returns:
            心跳响应
        """
        return self._request("POST", "/agent/api/heartbeat")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取Agent统计信息

        Returns:
            统计信息字典（任务数、收入等）
        """
        return self._request("GET", "/agent/api/stats")

    def get_info(self) -> Dict[str, Any]:
        """
        获取Agent信息

        Returns:
            Agent信息字典
        """
        return self._request("GET", "/agent/api/info")


# 兼容旧API
class AIBossClient(AIBossSDK):
    """AIBossClient - 兼容旧版本的类名"""
    pass


@dataclass
class Task:
    """任务数据模型"""
    id: int
    title: str
    description: str
    category: str
    budget_min: float
    budget_max: float
    status: str
    input_data: Optional[Dict[str, Any]] = None


@dataclass
class TaskResult:
    """任务结果数据模型"""
    task_id: int
    result_data: Any
    result_hash: Optional[str] = None
