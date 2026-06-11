export interface MediaIntegrationClientOptions {
  baseUrl: string;
  token: string;
  fetchImpl?: typeof fetch;
}

export class MediaIntegrationError extends Error {
  readonly code: string;
  readonly correlationId?: string;
  readonly retryable: boolean;
  readonly statusCode: number;

  constructor(
    code: string,
    message: string,
    options: { correlationId?: string; retryable?: boolean; statusCode?: number } = {},
  ) {
    super(message);
    this.name = "MediaIntegrationError";
    this.code = code;
    this.correlationId = options.correlationId;
    this.retryable = options.retryable ?? false;
    this.statusCode = options.statusCode ?? 400;
  }
}

export class MediaIntegrationClient {
  private readonly baseUrl: string;
  private readonly token: string;
  private readonly fetchImpl: typeof fetch;

  constructor(options: MediaIntegrationClientOptions) {
    let root = options.baseUrl.replace(/\/$/, "");
    if (!root.endsWith("/media-integration/v1")) {
      root = `${root}/media-integration/v1`;
    }
    this.baseUrl = root;
    this.token = options.token;
    this.fetchImpl = options.fetchImpl ?? fetch;
  }

  private idempotencyHeaders(key?: string): Record<string, string> {
    return { "Idempotency-Key": key ?? crypto.randomUUID() };
  }

  private async parseError(response: Response): Promise<never> {
    let body: unknown;
    try {
      body = await response.json();
    } catch {
      throw new MediaIntegrationError("http_error", response.statusText, { statusCode: response.status });
    }
    const envelope = body as { error?: { code?: string; message?: string; correlation_id?: string; retryable?: boolean }; detail?: { error?: { code?: string; message?: string } } };
    const err = envelope.error ?? envelope.detail?.error;
    if (err?.code) {
      throw new MediaIntegrationError(err.code, err.message ?? "Request failed", {
        correlationId: (err as { correlation_id?: string }).correlation_id,
        retryable: (err as { retryable?: boolean }).retryable,
        statusCode: response.status,
      });
    }
    throw new MediaIntegrationError("http_error", JSON.stringify(body), { statusCode: response.status });
  }

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set("Authorization", `Bearer ${this.token}`);
    headers.set("Accept", "application/json");
    if (init.body && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    const response = await this.fetchImpl(`${this.baseUrl}${path}`, { ...init, headers });
    if (!response.ok) {
      await this.parseError(response);
    }
    return (await response.json()) as T;
  }

  listRequests(params: Record<string, string | number | undefined> = {}): Promise<{ items: unknown[]; total: number }> {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined) qs.set(k, String(v));
    }
    const q = qs.toString();
    return this.request(`/requests${q ? `?${q}` : ""}`);
  }

  getRequest(requestId: string): Promise<Record<string, unknown>> {
    return this.request(`/requests/${requestId}`);
  }

  claim(requestId: string, idempotencyKey?: string): Promise<Record<string, unknown>> {
    return this.request(`/requests/${requestId}/claim`, {
      method: "POST",
      headers: this.idempotencyHeaders(idempotencyKey),
    });
  }

  heartbeat(
    requestId: string,
    body: { progress_percent: number; external_job_ref?: string; progress_message?: string },
    idempotencyKey?: string,
  ): Promise<Record<string, unknown>> {
    return this.request(`/requests/${requestId}/heartbeat`, {
      method: "POST",
      headers: this.idempotencyHeaders(idempotencyKey),
      body: JSON.stringify(body),
    });
  }

  fail(
    requestId: string,
    body: { failure_code: string; failure_message: string; retryable?: boolean },
    idempotencyKey?: string,
  ): Promise<Record<string, unknown>> {
    return this.request(`/requests/${requestId}/fail`, {
      method: "POST",
      headers: this.idempotencyHeaders(idempotencyKey),
      body: JSON.stringify(body),
    });
  }

  createUpload(
    requestId: string,
    body: { file_name: string; mime_type: string; size_bytes: number; sha256: string },
    idempotencyKey?: string,
  ): Promise<Record<string, unknown>> {
    return this.request(`/requests/${requestId}/uploads`, {
      method: "POST",
      headers: this.idempotencyHeaders(idempotencyKey),
      body: JSON.stringify(body),
    });
  }

  submitAsset(
    requestId: string,
    body: {
      upload_id: string;
      mime_type: string;
      sha256: string;
      external_asset_ref?: string;
      variant_key?: string;
      width?: number;
      height?: number;
      duration_seconds?: number;
      metadata?: Record<string, unknown>;
    },
    idempotencyKey?: string,
  ): Promise<Record<string, unknown>> {
    return this.request(`/requests/${requestId}/assets`, {
      method: "POST",
      headers: this.idempotencyHeaders(idempotencyKey),
      body: JSON.stringify(body),
    });
  }

  complete(requestId: string, idempotencyKey?: string): Promise<Record<string, unknown>> {
    return this.request(`/requests/${requestId}/complete`, {
      method: "POST",
      headers: this.idempotencyHeaders(idempotencyKey),
    });
  }
}
