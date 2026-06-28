export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

export interface ApiClientOptions extends RequestInit {
  body?: any;
}

export const apiClient = {
  async fetch<T = any>(path: string, options: ApiClientOptions = {}): Promise<T> {
    const url = `${API_BASE_URL}${path.startsWith('/') ? '' : '/'}${path}`;
    
    const headers = new Headers(options.headers);
    let body = options.body;
    
    if (body && typeof body === 'object' && !(body instanceof FormData)) {
      if (!headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json');
      }
      body = JSON.stringify(body);
    }
    
    const response = await fetch(url, {
      ...options,
      headers,
      body,
    });
    
    if (!response.ok) {
      const errText = await response.text().catch(() => 'Unknown error');
      throw new Error(`HTTP error! status: ${response.status}, message: ${errText}`);
    }
    
    return response.json() as Promise<T>;
  },
  
  async get<T = any>(path: string, options?: Omit<ApiClientOptions, 'body' | 'method'>): Promise<T> {
    return this.fetch<T>(path, { ...options, method: 'GET' });
  },
  
  async post<T = any>(path: string, body?: any, options?: Omit<ApiClientOptions, 'body' | 'method'>): Promise<T> {
    return this.fetch<T>(path, { ...options, method: 'POST', body });
  }
};
