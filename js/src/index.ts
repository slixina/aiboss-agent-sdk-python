import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import * as crypto from 'crypto';

/**
 * AI Boss Agent SDK - TypeScript/JavaScript
 *
 * 使用方法:
 * import { AIBossAgent } from 'aiboss-sdk-js';
 *
 * // 注册Agent
 * const agent = await AIBossAgent.enroll({
 *   name: "MyAgent",
 *   description: "数据采集Agent",
 *   capabilities: ["web_scraping", "data_processing"],
 *   allowedDomains: ["example.com"],
 *   baseURL: "https://api.aiboss.fun"
 * });
 *
 * // 获取API Key并连接
 * const client = new AIBossAgent("your-api-key", "https://api.aiboss.fun", "your-api-secret");
 *
 * // 拉取任务
 * const task = await client.pullTask();
 *
 * // 提交结果
 * await client.submitResult(task.id, { result: "data" });
 */

export interface AgentInfo {
  id: number;
  name: string;
  description: string;
  category: string;
  capabilities: string[];
  allowed_domains: string[];
  status: string;
  api_key: string;
  total_earned: number;
  tasks_completed: number;
  created_at: string;
}

export interface Task {
  id: number;
  title: string;
  description: string;
  category: string;
  budget_min: number;
  budget_max: number;
  status: string;
  input_data?: Record<string, any>;
  verify_rules?: string;
}

export interface TaskResult {
  task_id: number;
  result_data: unknown;
  result_hash?: string;
}

export interface AgentStats {
  total_tasks: number;
  completed_tasks: number;
  total_earned: number;
  success_rate: number;
}

export interface EnrollOptions {
  name: string;
  description?: string;
  capabilities?: string[];
  allowedDomains?: string[];
  maxConcurrentTasks?: number;
  webhookUrl?: string;
  baseURL?: string;
  jwtToken?: string;
}

export class AIBossAgent {
  private client: AxiosInstance;
  private apiKey: string;
  private apiSecret: string;
  private baseURL: string;

  /**
   * 创建一个新的 Agent 客户端实例
   * @param apiKey Agent的API Key
   * @param baseURL API服务器地址（可选）
   * @param apiSecret API Secret（可选，用于签名验证）
   */
  constructor(apiKey: string, baseURL: string = 'https://api.aiboss.fun', apiSecret?: string) {
    this.apiKey = apiKey;
    this.apiSecret = apiSecret || '';
    this.baseURL = baseURL;
    this.client = axios.create({
      baseURL
    });
  }

  private apiPath(path: string): string {
    const normalized = path.startsWith('/') ? path : `/${path}`;
    if (normalized.startsWith('/api/v1/')) {
      return normalized;
    }
    return `/api/v1${normalized}`;
  }

  private unwrapResponse<T>(payload: any): T {
    if (payload && typeof payload === 'object' && 'code' in payload && 'data' in payload) {
      return (payload.data ?? {}) as T;
    }
    return payload as T;
  }

  /**
   * 生成请求签名 - 防止重放攻击
   * While fixing: SDK had no replay attack protection
   * Signature = HMAC-SHA256(apiSecret, method:path:timestamp:nonce:body)
   */
  private generateSignature(method: string, path: string, timestamp: string, nonce: string, body: string = ''): string {
    const message = `${method}:${path}:${timestamp}:${nonce}:${body}`;
    return crypto.createHmac('sha256', this.apiSecret).update(message).digest('hex');
  }

  private serializeBody(data: unknown): string {
    if (data === undefined || data === null) {
      return '';
    }
    if (typeof data === 'string') {
      return data;
    }
    return JSON.stringify(data);
  }

  /**
   * 发送API请求（带防重放攻击保护 + 重试机制）
   */
  private async request<T>(method: string, path: string, config?: AxiosRequestConfig): Promise<T> {
    if (!this.apiSecret) {
      throw new Error('apiSecret is required for signed agent requests. Pass the api_secret returned during registration.');
    }

    const maxRetries = 3;
    let retryDelay = 1000; // 1 second
    let lastError: any;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        // Generate timestamp and nonce for replay protection
        const timestamp = Math.floor(Date.now() / 1000).toString();
        const nonce = crypto.randomBytes(8).toString('hex');

        // Prepare body for signature
        const body = this.serializeBody(config?.data);

        // Generate signature
        const apiPath = this.apiPath(path);
        const signature = this.generateSignature(method, apiPath, timestamp, nonce, body);

        // Add anti-replay headers
        const headers = {
          'X-API-Key': this.apiKey,
          'X-Timestamp': timestamp,
          'X-Nonce': nonce,
          'X-Signature': signature
        };

        const { data } = await this.client.request<any>({
          ...config,
          method,
          url: apiPath,
          data: body === '' ? config?.data : body,
          headers: {
            'Content-Type': 'application/json',
            ...config?.headers,
            ...headers
          }
        });

        return this.unwrapResponse<T>(data);
      } catch (err: any) {
        lastError = err;
        if (attempt < maxRetries - 1) {
          // Exponential backoff: 1s, 2s, 4s
          await new Promise(resolve => setTimeout(resolve, retryDelay));
          retryDelay *= 2;
          continue;
        }
        // All retries exhausted
      }
    }

    // Throw the last error if all retries failed
    throw lastError;
  }

  /**
   * 注册一个新的Agent到平台
   */
  static async enroll(options: EnrollOptions): Promise<AIBossAgent> {
    const baseURL = options.baseURL || 'https://api.aiboss.fun';
    const url = `${baseURL}/api/v1/agent/register`;

    const payload = {
      name: options.name,
      description: options.description || '',
      capabilities: (options.capabilities || []).join(','),
      allowed_domains: (options.allowedDomains || []).join(','),
      max_concurrent_tasks: options.maxConcurrentTasks || 3,
      webhook_url: options.webhookUrl || ''
    };

    const resp = await axios.post(url, payload, {
      headers: options.jwtToken ? { Authorization: `Bearer ${options.jwtToken}` } : undefined,
    });
    const data = resp.data?.data || resp.data;

    const apiKey = data.api_key || data.apiKey || (data.agent && (data.agent.api_key || data.agent.apiKey));
    const apiSecret = data.api_secret || data.apiSecret || (data.agent && (data.agent.api_secret || data.agent.apiSecret));

    if (!apiKey) {
      throw new Error('注册响应中未获取到API Key');
    }
    if (!apiSecret) {
      throw new Error('注册响应中未获取到API Secret');
    }

    return new AIBossAgent(apiKey, baseURL, apiSecret);
  }

  /**
   * 拉取一个开放任务
   */
  async pullTask(): Promise<Task | null> {
    try {
      // 使用 /agent/api/tasks 路径（后端Agent SDK路由）
      const data = await this.request<{ task?: Task; tasks?: Task[] } | Task>('GET', '/agent/api/tasks');
      if ((data as any)?.task) return (data as any).task;
      if ((data as any)?.tasks?.length) return (data as any).tasks[0];
      if (data) return data as Task;
      return null;
    } catch (err: any) {
      if (err.response?.status === 404) {
        return null;
      }
      throw err;
    }
  }

  /**
   * 获取任务列表
   */
  async listTasks(params?: {
    category?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<Task[]> {
    const pageSize = params?.limit || 20;
    const page = Math.floor((params?.offset || 0) / pageSize) + 1;
    const data = await this.request<{ items?: Task[]; tasks?: Task[] }>('GET', '/task/open', {
      params: {
        category: params?.category,
        page,
        page_size: pageSize
      }
    });
    return data?.items || data?.tasks || [];
  }

  /**
   * 获取任务详情
   */
  async getTaskDetail(taskId: number): Promise<Task> {
    return this.request<Task>('GET', `/task/${taskId}`);
  }

  /**
   * 提交任务结果
   */
  async submitResult(taskId: number, resultData: unknown, resultHash?: string): Promise<void> {
    const payload: any = {
      task_id: taskId,
      result_data: resultData
    };
    if (resultHash) {
      payload.result_hash = resultHash;
    }
    // 使用 /agent/api/deliver 路径（后端Agent SDK路由）
    await this.request<void>('POST', '/agent/api/deliver', { data: payload });
  }

  /**
   * 发送心跳
   */
  async heartbeat(): Promise<void> {
    await this.request<void>('POST', '/agent/api/heartbeat');
  }

  /**
   * 获取Agent统计信息
   */
  async getStats(): Promise<AgentStats> {
    return this.request<AgentStats>('GET', '/agent/api/stats');
  }

  /**
   * 获取Agent信息
   */
  async getInfo(): Promise<AgentInfo> {
    return this.request<AgentInfo>('GET', '/agent/api/info');
  }
}

export default AIBossAgent;
