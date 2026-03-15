import requests
import time
import platform
import json
import hmac
import hashlib
import random
import string
from urllib.parse import urlparse
from typing import Dict, Any, Optional, List
from .config import get_api_url, get_agent_id, get_agent_secret, save_config

class AibossClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or get_api_url()
        self.agent_id = get_agent_id()
        self.secret = get_agent_secret()
        self.session = requests.Session()
        self.version = "0.1.2"

    def _generate_nonce(self, length: int = 16) -> str:
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def _sign_request(self, method: str, url: str, body: Dict[str, Any] = None) -> Dict[str, str]:
        """Generate HMAC headers."""
        if not self.agent_id or not self.secret:
            return {}
            
        timestamp = str(int(time.time() * 1000))
        nonce = self._generate_nonce()
        
        # Consistent body stringify to match Node.js JSON.stringify
        body_str = ""
        if body:
            body_str = json.dumps(body, separators=(',', ':'))
            
        # Parse path from URL
        parsed = urlparse(url)
        path = parsed.path
        if parsed.query:
             path += "?" + parsed.query
             
        # Signature: METHOD + PATH + TIMESTAMP + NONCE + BODY
        data_to_sign = f"{method.upper()}{path}{timestamp}{nonce}{body_str}"
        
        signature = hmac.new(
            self.secret.encode('utf-8'),
            data_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return {
            "X-Agent-ID": self.agent_id,
            "X-Timestamp": timestamp,
            "X-Nonce": nonce,
            "X-Signature": signature,
            "Content-Type": "application/json"
        }

    def enroll(self, enrollment_code: str, name: str, capabilities: List[str]) -> Dict[str, Any]:
        """Enroll a new agent."""
        payload = {
            "enrollment_code": enrollment_code,
            "name": name,
            "capabilities": capabilities,
            "version": self.version
        }
        
        try:
            url = f"{self.base_url}/agents/enroll"
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if 'agent_id' in data and 'api_key' in data:
                self.agent_id = data['agent_id']
                self.secret = data['api_key']
                # Save to config
                save_config(self.base_url, self.agent_id, self.secret)
                return data
            else:
                raise ValueError("Invalid enrollment response: missing agent_id or api_key")
                
        except requests.exceptions.RequestException as e:
            print(f"Error enrolling agent: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Server response: {e.response.text}")
            raise

    def sync(self, status: str = "idle") -> Dict[str, Any]:
        """Sync with server: Heartbeat + Get Task."""
        if not self.agent_id:
            # Cannot sync if not enrolled
            return {"command": "sleep", "duration": 10}

        url = f"{self.base_url}/agents/sync"
        payload = {
            "status": status,
            "version": self.version
        }
        
        headers = self._sign_request("POST", url, payload)
        
        try:
            # Send raw JSON string to ensure body matches signature calculation (no spaces)
            data_str = json.dumps(payload, separators=(',', ':'))
            response = self.session.post(url, data=data_str, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Propagate exception to let runner handle backoff
            # print(f"Error syncing: {e}")
            raise

    def submit_task(self, task_id: str, output: Dict[str, Any], execution_time_ms: int, success: bool = True) -> Dict[str, Any]:
        """Submit task result."""
        if not self.agent_id:
            raise ValueError("Agent ID not configured.")
            
        url = f"{self.base_url}/tasks/{task_id}/submit"
        
        # Construct payload matching Backend DTO: { agentId, result, success }
        # execution_time_ms is included in result for analytics
        payload = {
            "agentId": self.agent_id,
            "result": {
                **output,
                "execution_time_ms": execution_time_ms
            },
            "success": success
        }
        
        headers = self._sign_request("POST", url, payload)
        
        try:
            # Send raw JSON string to ensure body matches signature calculation (no spaces)
            data_str = json.dumps(payload, separators=(',', ':'))
            response = self.session.post(url, data=data_str, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error submitting task: {e}")
            raise

    def get_paycheck(self) -> Optional[Dict[str, Any]]:
        """Get agent paycheck data (earnings, rank, etc)."""
        if not self.agent_id:
            return None
            
        url = f"{self.base_url}/viral/paycheck/{self.agent_id}"
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.RequestException:
            return None
