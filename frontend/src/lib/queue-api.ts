/**
 * Queue Management API Client
 * HTTP client for queue management operations
 */

import {
  Ticket,
  Service,
  Counter,
  QueueState,
  CounterState,
  CreateServiceRequest,
  CreateCounterRequest,
  CreateTicketRequest,
  CallNextTicketRequest,
  CompleteTicketRequest,
  CancelTicketRequest,
  DailyStatistics
} from '@/types/queue';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/queue';

class QueueApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  // Service Management
  async createService(data: CreateServiceRequest): Promise<Service> {
    return this.request('/services', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getServices(): Promise<Service[]> {
    return this.request('/services');
  }

  async getService(serviceId: string): Promise<Service> {
    return this.request(`/services/${serviceId}`);
  }

  // Counter Management
  async createCounter(data: CreateCounterRequest): Promise<Counter> {
    return this.request('/counters', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getCounters(): Promise<Counter[]> {
    return this.request('/counters');
  }

  async getCounter(counterId: string): Promise<Counter> {
    return this.request(`/counters/${counterId}`);
  }

  async getCounterState(counterId: string): Promise<CounterState> {
    return this.request(`/counters/${counterId}/state`);
  }

  async callNextTicket(counterId: string, data: CallNextTicketRequest): Promise<Ticket | null> {
    return this.request(`/counters/${counterId}/call-next`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Ticket Management
  async createTicket(data: CreateTicketRequest): Promise<Ticket> {
    return this.request('/tickets', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getTicket(ticketId: string): Promise<Ticket> {
    return this.request(`/tickets/${ticketId}`);
  }

  async startService(ticketId: string): Promise<Ticket> {
    return this.request(`/tickets/${ticketId}/start`, {
      method: 'POST',
    });
  }

  async completeService(ticketId: string, data: CompleteTicketRequest): Promise<Ticket> {
    return this.request(`/tickets/${ticketId}/complete`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async cancelTicket(ticketId: string, data: CancelTicketRequest): Promise<Ticket> {
    return this.request(`/tickets/${ticketId}/cancel`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Queue Management
  async getQueueState(serviceId?: string): Promise<QueueState> {
    const params = serviceId ? `?service_id=${serviceId}` : '';
    return this.request(`/queue/state${params}`);
  }

  async getWaitingList(serviceId?: string, limit: number = 50): Promise<Ticket[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
    });
    if (serviceId) {
      params.append('service_id', serviceId);
    }
    return this.request(`/queue/waiting?${params}`);
  }

  // Statistics
  async getDailyStatistics(date?: string, serviceId?: string): Promise<DailyStatistics[]> {
    const params = new URLSearchParams();
    if (date) {
      params.append('date', date);
    }
    if (serviceId) {
      params.append('service_id', serviceId);
    }
    const paramString = params.toString();
    return this.request(`/statistics/daily${paramString ? `?${paramString}` : ''}`);
  }

  async getPerformanceMetrics(period: string = 'today', serviceId?: string): Promise<unknown> {
    const params = new URLSearchParams({ period });
    if (serviceId) {
      params.append('service_id', serviceId);
    }
    return this.request(`/statistics/performance?${params}`);
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; database: string; timestamp: string }> {
    return this.request('/health');
  }
}

// Singleton instance
export const queueApi = new QueueApiClient();

// Export class for testing
export { QueueApiClient };